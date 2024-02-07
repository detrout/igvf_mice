from collections import namedtuple
import functools
import pandas
import re

from .. import models
from .converters import (
    normalize_plate_name,
    parse_mouse_tissue,
    get_genotype_from_mouse_tissue,
    str_or_empty,
    uci_tz_or_none,
)

def import_accessions(submitted_accessions, record):
    if submitted_accessions is None:
        return

    current_accessions = list(record.accession.all())
    current_accession_ids = {x.name for x in current_accessions}
    count = 0

    for accession_record in submitted_accessions:
        if accession_record["name"] not in current_accession_ids:
            accession = models.Accession(
                accession_prefix=accession_record["accession_prefix"],
                name=accession_record["name"],
                uuid=accession_record["uuid"],
                see_also=accession_record["see_also"],
            )
            accession.save()
            current_accessions.append(accession)
            current_accession_ids.add(accession.name)
            count += 1

    if count > 0:
        record.accession.set(current_accessions)
        record.save()

    
def import_protocols(sheet):
    current_protocols = {x.name for x in models.ProtocolLink.objects.all()}

    for i, row in sheet.iterrows():
        if row["Protocol"] not in current_protocols:
            record = models.ProtocolLink(
                name=row["Protocol"],
                version=int(row["Protocols.io version"]),
                see_also=row["Link"],
                description=row["Description"]
            )
            record.save()


def import_mice(mice, submitted_accessions=None):
    if submitted_accessions is None:
        submitted_accessions = {}

    required_columns = {
        "Mouse Name",
        "Strain code",
        "Housing number",
        "Sex",
        "Weight (g)",
        "DOB",
        "Dissection start time",
        "Dissection finish time",
        "Timepoint",
        "estrus_cycle",
    }

    missing_columns = required_columns.difference(mice.columns)
    if len(missing_columns) > 0:
        raise KeyError(f"Missing column names {missing_columns}")

    mouse_strains = {x.name: x for x in models.MouseStrain.objects.all()}
    current_mice  = {x.name for x in models.Mouse.objects.all()}
    failed = 0
    added = 0

    for i, row in mice.iterrows():
        name = row["Mouse Name"]
        if name not in current_mice:
            housing_number = None if pandas.isnull(row["Housing number"]) else row["Housing number"]        
            record = models.Mouse(
                # should i use liz's disection id?
                name=name,
                strain=mouse_strains[row["Strain code"]],
                sex=row["Sex"],
                weight_g=row["Weight (g)"],
                date_of_birth=row["DOB"].date() if not pandas.isnull(row["DOB"]) else None,
                dissection_start_time=uci_tz_or_none(row["Dissection start time"]),
                dissection_end_time=uci_tz_or_none(row["Dissection finish time"]),
                timepoint_description=row["Timepoint"],
                life_stage=models.LifeStageEnum.ADULT,
                estrus_cycle=row["estrus_cycle"],
                operator=str_or_empty(row["Operator"]),
                notes=str_or_empty(row["Comments"]),
                housing_number=housing_number,
            )
            record.save()
            added += 1
        else:
            record = models.Mouse.objects.get(pk=name)

        # import accession skips if submitted_accessions.get is None
        import_accessions(submitted_accessions.get(name), record)

    print("Currently have {} mice loaded".format(models.Mouse.objects.count()))
    assert not failed, "Check warning messages"
    
    return added


def import_tissues(tissue_sheets, submitted_tissues=None):
    if submitted_tissues is None:
        submitted_tissues = {}

    los_angeles_tz = zoneinfo.ZoneInfo("America/Los_Angeles")

    loaded_mice = {x.name: x for x in models.Mouse.objects.all()}
    loaded_tissues = {x.name: x for x in models.Tissue.objects.all()}

    failed = False
    for i, row in tissue_sheets.iterrows():
        mouse_name = row["Mouse name"]
        try:
            mouse = loaded_mice[mouse_name]
        except KeyError:
            print("row {}, {} was not found".format(i+2, mouse_name))
            failed = True
            continue

        mouse_tissue = row["Mouse_Tissue ID"]

        genotype = row["Genotype"]

        validate_tissue_genotype(mouse.strain.name, genotype)

        tissue_terms = []
        for term_curie, term_name in tissue_dissection_to_ontology_map[row["Tissue"]]:
            tissue_terms.append(ontology_map[term_curie])

        if pandas.isnull(row["Approx. sac time"]):
            sac_time = datetime.time(0,0,0)
        else:
            sac_time = datetime.time(
                row["Approx. sac time"].hour,
                row["Approx. sac time"].minute,
                row["Approx. sac time"].second,
            )

        record = models.Tissue(
            mouse=mouse,
            name = mouse_tissue,
            description = row["Tissue"],
            #dissection_time=dissection,
            #age=age,
            #age_units=age_units,
            tube_label=row["Tube label"],
            dissector=str_or_empty(row["Dissector"]),
            dissection_notes=str_or_empty(row["Comment"]),
        )

        if not pandas.isnull(row["Dissection date"]):
            record.dissection = datetime.combine(row["Dissection date"], sac_time).astimezone(los_angeles_tz)

        tube_weight_label = "tube weight (g)"
        if not pandas.isnull(row[tube_weight_label]):
            record.tube_weight_g = float(row[tube_weight_label])

        total_weight_label = "tube+tissue weight (g)"
        if not pandas.isnull(row[total_weight_label]):
            record.total_weight_g = float(row[total_weight_label])

        record.save()
        record.ontology_term.set(tissue_terms)
        record.save()

        import_accessions(submitted_accessions.get(row["Mouse_Tissue ID"]), record)

    assert not failed, "Check warning messages."

WellContent = namedtuple("well_content", ["genotype", "tissue_id"])


class ValidationError(ValueError):
    """Validators failed on a layout.
    """
    pass


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
        for plate_id_row in sheet[sheet[self.plate_label].apply(self.is_plate_name)].index:
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

        for col_offset in range(self.well_start_column, 255):
            cell = sheet.iloc[data_start_row, col_offset]
            if pandas.isnull(cell) or self._pooled_well_re.match(cell):
                return col_offset

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
                    genotype = get_genotype_from_mouse_tissue(cell)

                    well_contents.setdefault(well_id, []).append(WellContent(genotype, cell))
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
            sex = tissue.mouse_age_sex[-1]
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
                genotype = get_genotype_from_mouse_tissue(cell)

                row_id = str(row_ids[row_offset])
                col_id = str(column_ids[col_offset])
                well_contents[row_id, col_id] = [WellContent(genotype, cell)]

        well_contents.update(self.get_merged_well_contents(plate_name, sheet, plate_start))

        if validation_errors > 0:
            raise ValidationError(f"there were {validation_errors} reading the block at {block_row_start}")

        return well_contents

    def parse_plates(self, sheet):
        for plate_name, plate_start in self.find_plate_start(sheet):
            contents = self.get_well_contents_from_block(plate_name, sheet, plate_start)
            yield plate_name, contents

    def is_plate_name(self, name):
        return not pandas.isnull(name) and name.startswith("IGVF_")
