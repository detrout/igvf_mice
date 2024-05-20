"""Parse the complex plate layout spreadsheet tab
"""

from collections import namedtuple
import functools
import pandas
import re

from django.db import transaction

from .. import models
from .converters import (
    normalize_plate_name,
    parse_mouse_tissue,
    get_strain_from_mouse_tissue,
)

WellContent = namedtuple("well_content", ["genotype", "tissue_id"])


class ValidationError(ValueError):
    """Validators failed on a layout.
    """
    pass


def is_plate_name(name):
    return not pandas.isnull(name) and name.startswith("IGVF_")


class PlateLayoutParser:
    def __init__(self):
        self.plate_label = 1
        self.column_label = 1
        self.well_row_label_column = 1
        self.well_row_id_column = 2
        self.well_start_column = 3
        self.well_end_column = self.well_start_column + 11
        self.well_column_range = slice(self.well_start_column, self.well_end_column)

        # for the pooled wells
        self._pooled_well_re = re.compile("^([A-H]+)_(?P<sex>[MF])[0-9]_([0-9])+$")
        self._well_id_re = re.compile("^[A-H]1?[\d]$")

        # Used for validation rules
        self._mouse_strains = {x.name for x in models.MouseStrain.objects.all()}
        self._sex_re = re.compile("^(Tissue[0-9]_)?(?P<sex>[MF])(_rep[0-9]+)?$")

    def find_plate_start(self, sheet):
        """Search for the start of a plate layout block
        """
        for plate_id_row in sheet[sheet[self.plate_label].apply(is_plate_name)].index:
            plate_name = normalize_plate_name(sheet.iloc[plate_id_row][self.plate_label])
            if plate_name.endswith("XX"):
                continue

            column_header = [str(x) for x in range(1,13)]
            for i in range(plate_id_row, plate_id_row + 4):
                current_header = [str(x) for x in sheet.loc[i, self.well_column_range]]
                if current_header == column_header:
                    yield (plate_name, i-1)

    def get_block_column_ids(self, sheet, block_row_start):
        label_start_row = block_row_start + 1

        for cell in sheet.iloc[label_start_row, self.well_start_column:]:
            if pandas.notnull(cell):
                yield cell
            else:
                break

    def get_block_column_labels(self, sheet, block_row_start):
        id_start_row = block_row_start

        for cell in sheet.iloc[id_start_row, self.well_start_column:]:
            if pandas.notnull(cell):
                yield cell
            else:
                break

    def get_block_simple_column_end(self, sheet, block_row_start):
        """Some plates have mixed genotype wells which are hard to validate
        """
        data_start_row = block_row_start + 2

        for col_offset in range(self.well_start_column, sheet.shape[1]):
            cell = sheet.iloc[data_start_row, col_offset]
            if pandas.isnull(cell) or self._pooled_well_re.match(cell):
                return col_offset

        return sheet.shape[1]

    def get_block_row_ids(self, sheet, block_row_start):
        label_start_row = block_row_start + 2

        started = False
        for i, row in sheet.iloc[label_start_row:].iterrows():
            # once we see a A..H label we're in a block and should be ready to abort
            if pandas.notnull(row[self.well_row_id_column]):
                started = True

            if pandas.notnull(row[self.well_row_id_column]) and pandas.notnull(row[self.well_start_column]):
                yield row[self.well_row_id_column]
            # if we've seen the start of the row ids, and we hit a blank we should stop
            elif started:
                break

    def get_block_row_labels(self, sheet, block_row_start):
        label_start_row = block_row_start + 2

        started = False
        for i, row in sheet.iloc[label_start_row:].iterrows():
            # once we see a A..H label we're in a block and should be ready to abort
            if pandas.notnull(row[self.well_row_id_column]):
                started = True

            if pandas.notnull(row[self.well_row_label_column]) and pandas.notnull(row[self.well_start_column]):
                yield row[self.well_row_label_column]
            # if we've seen the start of the row ids, and we hit a blank we should stop
            elif started:
                break

    def get_merged_well_contents(self, plate_name, sheet, block_row_start):
        """Return the well content lists for well containing multiple tissues"""
        well_end_column = self.get_block_simple_column_end(sheet, block_row_start)
        well_range = range(self.well_start_column, well_end_column)

        column_labels = list(self.get_block_column_labels(sheet, block_row_start))
        column_validators = list(self.get_validation_label_rules(plate_name, column_labels))

        row_labels = list(self.get_block_row_labels(sheet, block_row_start))
        row_validators = list(self.get_validation_label_rules(plate_name, row_labels))

        validation_errors = 0
        well_contents = {}
        row_offset = 0
        for start in self.get_merged_well_definition_start(sheet, block_row_start):
            # the well ids like A9..B12 are 3 lines down from the start
            well_ids = []
            for cell in sheet.iloc[start+3][well_range]:
                if pandas.notnull(cell) and self._well_id_re.match(cell):
                    row = cell[0]
                    column = cell[1:]
                    well_ids.append((row, column))
                else:
                    print(f"Well id {cell} failed validation on 0-based line {start+3}")
                    return

            for pooled_row in [start, start+1]:
                current_sheet_slice = sheet.iloc[pooled_row][well_range]
                for col_offset, (well_id, cell) in enumerate(zip(well_ids, current_sheet_slice)):
                    # Really could use some validation rules here...
                    if callable(row_validators[row_offset]):
                        if not row_validators[row_offset](cell):
                            validation_errors += 1
                            print(f"Failed row_validator[{row_offset},{col_offset}]({cell}) rule {row_validators[row_offset]}")
                    if callable(column_validators[col_offset]):
                        if not column_validators[col_offset](cell):
                            validation_errors += 1
                            print(f"Failed column_validator[{row_offset},{col_offset}]({cell}) rule {row_validators[row_offset]}")
                    strain = get_strain_from_mouse_tissue(cell)

                    well_contents.setdefault(well_id, []).append(WellContent(strain, cell))
                row_offset += 1

        if validation_errors > 0:
            raise ValidationError(f"there were {validation_errors} reading the block at {block_row_start}")

        return well_contents

    def get_merged_well_definition_start(self, sheet, block_row_start):
        """Return the sheet locations where we can find the contents of merged wells.
        """
        detail_start_row = block_row_start + len(list(self.get_block_row_ids(sheet, block_row_start)))
        maximum_search_length = 30
        detail_max_row = min(detail_start_row + maximum_search_length, sheet.shape[0])
        detail_range = range(detail_start_row, detail_max_row)

        merged_well_ids = set(self.get_merged_well_ids(sheet, block_row_start))
        if len(merged_well_ids) == 0:
            return

        definition_start = detail_start_row
        for row_index in detail_range:
            cell = sheet.iloc[row_index][self.well_start_column]
            if pandas.notnull(cell) and cell in merged_well_ids:
                yield definition_start - 2
            definition_start += 1

    def get_merged_well_ids(self, sheet, block_row_start):
        """Extract the ids used to refer to the tissue ids that were pooled
        """
        pooled_start_row = block_row_start + 2
        pooled_start_column = self.get_block_simple_column_end(sheet, block_row_start)

        for row_index, row in sheet.iloc[pooled_start_row:,pooled_start_column:].iterrows():
            saw_data = False
            for col_offset, cell in enumerate(row):
                if pandas.notnull(cell):
                    if self._pooled_well_re.match(cell):
                        saw_data = True
                        yield cell
                else:
                    continue
            if not saw_data:
                break

    @staticmethod
    def _validate_sex(value, expected_sex, overrides=None):
        try:
            tissue = parse_mouse_tissue(value)
            sex = tissue.mouse_sex[-1]
        except ValueError:
            return False
        return sex == expected_sex

    @staticmethod
    def _validate_strain(value, expected_strain, overrides=None):
        try:
            tissue = parse_mouse_tissue(value)
            strain = tissue.mouse_strain
        except ValueError:
            return False

        if overrides is not None:
            expected_strain = overrides.get(value, expected_strain)

        return strain == expected_strain

    def get_validation_label_rules(self, plate_name, labels):
        tissue_overrides = {
            "IGVF_003": {"092_CASTJ_10F_03": "CASTJ"},
            "IGVF_005": {"092_CASTJ_10F_01": "CASTJ"},
            "IGVF_006": {"092_CASTJ_10F_01": "CASTJ"},
            "IGVF_007": {"092_CASTJ_10F_01": "CASTJ"},
            "IGVF_011": {"092_CASTJ_10F_03": "CASTJ"},
        }.get(plate_name)

        for l in labels:
            sex = self._sex_re.match(l)
            if sex:
                yield functools.partial(PlateLayoutParser._validate_sex, expected_sex=sex.group("sex"))
            elif l in self._mouse_strains:
                yield functools.partial(PlateLayoutParser._validate_strain, expected_strain=l, overrides=tissue_overrides)
            else:
                yield None

    def get_well_contents_from_block(self, plate_name, sheet, plate_start):
        column_ids = list(self.get_block_column_ids(sheet, plate_start))
        column_labels = list(self.get_block_column_labels(sheet, plate_start))
        column_validators = list(self.get_validation_label_rules(plate_name, column_labels))
        column_end = self.get_block_simple_column_end(sheet, plate_start)

        row_ids = list(self.get_block_row_ids(sheet, plate_start))
        row_labels = list(self.get_block_row_labels(sheet, plate_start))
        row_validators = list(self.get_validation_label_rules(plate_name, row_labels))

        data_row_start = plate_start + 2
        data_row_range = slice(data_row_start, data_row_start + len(row_ids))
        column_range = slice(self.well_start_column, column_end)

        validation_errors = 0
        well_contents = {}
        for row_offset, (i, row) in enumerate(sheet.iloc[data_row_range, column_range].iterrows()):
            for col_offset, cell in enumerate(row):
                if len(row_validators) > 0 and callable(row_validators[row_offset]):
                    if not row_validators[row_offset](cell):
                        print(f"Failed row_validator[{row_offset},{col_offset}]({cell})")
                        validation_errors += 1
                if len(column_validators) > 0 and callable(column_validators[col_offset]):
                    if not column_validators[col_offset](cell):
                        print(f"Failed column_validator[{row_offset},{col_offset}]({cell})")
                        validation_errors += 1
                strain = get_strain_from_mouse_tissue(cell)

                row_id = str(row_ids[row_offset])
                col_id = str(column_ids[col_offset])
                well_contents[row_id, col_id] = [WellContent(strain, cell)]

        well_contents.update(self.get_merged_well_contents(plate_name, sheet, plate_start))

        if validation_errors > 0:
            raise ValidationError(f"there were {validation_errors} reading the block at {block_row_start}")

        return well_contents

    def parse_plates(self, sheet):
        for plate_name, plate_start in self.find_plate_start(sheet):
            contents = self.get_well_contents_from_block(plate_name, sheet, plate_start)
            yield plate_name, contents


    def _get_or_create_plate(self, plate_name):
        try:
            plate_record = models.SplitSeqPlate.objects.get(name=plate_name)
        except models.SplitSeqPlate.DoesNotExist:
            plate_record = models.SplitSeqPlate(
                name=plate_name,
                size=models.PlateSizeEnum.size_96,
                pool_location=None,
                date_performed=None,
            )
            plate_record.save()
        return plate_record

    def _get_or_create_well(self, well_id, plate, barcodes, biosamples):
        try:
            well = models.SplitSeqWell.objects.get(
                plate=plate,
                row=well_id[0],
                column=well_id[1],
            )
        except models.SplitSeqWell.DoesNotExist:
            well = models.SplitSeqWell(
                plate=plate,
                row=well_id[0],
                column=well_id[1],
            )
            well.save()
            well.biosample.set(biosamples)
            well.barcode.set(barcodes)
            well.save()


    def _guess_barcode_reagent_from_plate(self, plate_name, plate_contents):
        wt_mega_2_reagent = models.LibraryConstructionReagent.objects.get(name="wt-mega-v2")
        wt_regular_2_reagent = models.LibraryConstructionReagent.objects.get(name="wt-v2")
        if len(plate_contents) == 48:
            return wt_regular_2_reagent
        elif len(plate_contents) == 96:
            return wt_mega_2_reagent
        else:
            raise RuntimeError("Unrecognized plate {} size {}".format(
                plate_name, len(plate_contents)))

    def import_plates(self, sheet):
        biosample_table = {x.name: x for x in models.FixedSample.objects.all()}
        with transaction.atomic():
            for plate_name, plate_contents in self.parse_plates(sheet):
                plate = self._get_or_create_plate(plate_name)

                biosamples = []
                for well_id in plate_contents:
                    well_contents = plate_contents[well_id]

                    biosamples.extend([biosample_table[item.tissue_id] for item in well_contents])
                    reagent = self._guess_barcode_reagent_from_plate(plate_name, plate_contents)
                    barcodes = models.LibraryBarcode.objects.filter(
                        reagent=reagent,
                        code="{}{}".format(well_id[0], well_id[1]),
                    )

                    assert len(barcodes) > 0, "We should find bar codes to attach to a well"

                    well = self._get_or_create_well(well_id, plate, barcodes, biosamples)
