import pandas
import numpy

from .. import models
from .converters import (
    date_or_none,
    float_or_nan,
    float_or_none,
    normalize_strain,
    int_or_none,
    int_or_0,
    str_or_empty,
    uci_tz_or_none,
)


def load_accessions(submitted_accessions, record):
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


def load_protocols(sheet):
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


def load_mice(mice, submitted_accessions=None):
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
    current_mice = {x.name for x in models.Mouse.objects.all()}
    failed = 0
    added = 0

    for i, row in mice.iterrows():
        name = row["Mouse Name"]
        if name not in current_mice:
            housing_number = None if pandas.isnull(row["Housing number"]) else row["Housing number"]
            record = models.Mouse(
                # should i use liz's disection id?
                name=name,
                dissection=int_or_none(row["Mouse ID"]),
                strain=mouse_strains[row["Strain code"]],
                sex=row["Sex"],
                weight_g=row["Weight (g)"],
                date_of_birth=row["DOB"].date() if pandas.notnull(row["DOB"]) else None,
                dissection_start_time=uci_tz_or_none(row["Dissection start time"]),
                dissection_end_time=uci_tz_or_none(row["Dissection finish time"]),
                timepoint=row["Timepoint"],
                timepoint_unit=row["Timepoint unit"],
                life_stage=models.LifeStageEnum.ADULT,
                light_status=row["Light status"],
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
        load_accessions(submitted_accessions.get(name), record)

    print("Currently have {} mice loaded".format(models.Mouse.objects.count()))
    assert not failed, "Check warning messages"

    return added


def load_tissues(tissue_sheets, submitted_tissues=None):
    if submitted_tissues is None:
        submitted_tissues = {}

    loaded_mice = {x.name: x for x in models.Mouse.objects.all()}
    ontology_map = {x.curie: x for x in models.OntologyTerm.objects.all()}

    tissue_sheets = tissue_sheets.copy()
    tissue_sheets.columns = [x.lower() for x in tissue_sheets.columns]
    added = 0
    failed = 0
    for i, row in tissue_sheets.iterrows():
        tissue_name = row["mouse_tissue id"]
        mouse_name = row["mouse name"]
        try:
            mouse = loaded_mice[mouse_name]
        except KeyError:
            print("row {}, {} was not found".format(i+2, mouse_name))
            failed += 1
            continue

        mouse_tissue = row["mouse_tissue id"]

        genotype = normalize_strain(row["genotype"])

        # this is the "label swap" on spreadsheet rows 602-605.
        if mouse_name == "092_CASTJ_10F":
            genotype = "CASTJ"
        # this is the other half the swap on spreadsheet rows 1522-1525
        elif mouse_name == "046_NZOJ_10F":
            genotype = 'NZOJ'

        if mouse.strain.name != genotype:
            print(f"{tissue_name} Mouse strain {mouse.strain.name} != {genotype}")
            failed += 1
            continue

        tissue_terms = []
        for term_curie in row["tissue_id"]:
            tissue_terms.append(ontology_map[term_curie])

        record = models.Tissue(
            mouse=mouse,
            name=mouse_tissue,
            description=row["tissue"],
            tube_label=row["tube label"],
            dissector=str_or_empty(row["dissector"]),
            dissection_notes=str_or_empty(row["comment"]),
        )

        if pandas.notnull(row["dissection start"]):
            record.dissection_start_time = uci_tz_or_none(row["dissection start"])

        if pandas.notnull(row["dissection end"]):
            record.dissection_end_time = uci_tz_or_none(row["dissection end"])

        tube_weight_label = "tube weight (g)"
        if pandas.notnull(row[tube_weight_label]):
            record.tube_weight_g = float_or_nan(row[tube_weight_label])

        total_weight_label = "tube+tissue weight (g)"
        if pandas.notnull(row[total_weight_label]):
            record.total_weight_g = float_or_nan(row[total_weight_label])

        if pandas.notnull(row.get("volume (mL)")):
            record.volume_ul = float_or_nan(row["volume (mL)"]) * 1000

        if pandas.notnull(row.get("cells before fixation (x 10^6)")):
            record.input_total

        record.save()
        record.ontology_term.set(tissue_terms)
        record.save()
        added += 1

        load_accessions(submitted_tissues.get(tissue_name), record)

    if failed > 0:
        raise ValidationError(f"Check warning messages. {failed} records failed")

    return added


def load_splitseq_samples(fixed_samples):
    """Import splitseq SampleExtraction and ParseFixedSample records

    In the spreadsheet these are one row, but because the cell/nuclei
    extraction can be fed into the nanopore path they need to be separated.
    """
    current_extraction = {x.name for x in models.SampleExtraction.objects.all()}
    current_tissues = {x.name for x in models.ParseFixedSample.objects.all()}

    added = 0
    for i, row in fixed_samples.iterrows():
        if not row["tissue_id"] in current_extraction:
            try:
                pooled_tissues = []
                for pooled_id in row["pooled_from"]:
                    pooled_tissues.append(models.Tissue.objects.get(name=pooled_id))
            except models.Tissue.DoesNotExist as e:
                raise models.Tissue.DoesNotExist("Tissue {} does not exist".format(pooled_id))

            if not row["weight"] is None:
                tissue_weight = sum([int_or_0(x.weight_mg) for x in pooled_tissues])
                if not numpy.isclose(tissue_weight, row["weight"]):
                    print(
                        "Sum of tissue weights from {pooled_from} {total_weight}"
                        " doesn't match {weight}. {sheet}:{line_no}".format(
                            pooled_from=",".join([x.name for x in pooled_tissues]),
                            total_weight=tissue_weight,
                            weight=row["weight"],
                            sheet=row["sheet_name"],
                            line_no=row["line_no"],
                    ))

            extraction_record = models.SampleExtraction(
                name=row["tissue_id"],
                tube_label=row["tube_label"],
                date=date_or_none(row["fixation_date"]),
                technician=row.get("isolation_technician"),
                volume_ul=row["volume_ul"],
                count1=row["before_count1"],
                df1=row["before_df1"],
                count2=row["before_count2"],
                df2=row["before_df2"],
                input_nuclei_per_ul=row["nuclei_per_ul_before_fixation"],
                parse_input_ul=row["parse_input_ul"],
                share_input_ul=row["share_input_ul"],
            )
            extraction_record.save()
            extraction_record.tissue.set(pooled_tissues)
            extraction_record.save()

            sample_record = models.ParseFixedSample(
                name=row["tissue_id"],
                extraction=extraction_record,
                count1=row["after_count1"],
                df1=row["after_df1"],
                count2=row["after_count2"],
                df2=row["after_df2"],
                input_nuclei_per_ul=row["nuclei_per_ul_after_fixation"],

                aliquots_made=int_or_none(row["aliquots_made"]),
                aliquot_volume_ul=float_or_none(row["aliquot_volume_ul"]),
                comments=row["comments"],
            )
            sample_record.save()
            added += 1

    return added


def get_or_create_splitseq_ont_nucleic_acid_extraction(row, subpool):
    name = row["name"]
    try:
        extraction = models.NucleicAcidExtraction.objects.get(name=name)
    except models.NucleicAcidExtraction.DoesNotExist:
        extraction = models.NucleicAcidExtraction(
            name=row["name"],
            date=row["cdna_build_date"],
            technician=row["technician"],
            volume_ul=row["cdna_volume_ul"],
            input_ng_per_ul=row["cdna_ng_per_ul"],
            passed_qc=row["passed_qc"],
        )
        extraction.save()
        extraction.subpool.set([subpool])
    # we're not handling the case where there could be multiple extractions pooled
    # like ONT020&026, this pretends the merged samples are one pool
    return [extraction]


def get_or_create_splitseq_ont_library(row, extractions):
    name = row["name"]
    try:
        library = models.NanoporeLibrary.objects.get(name=name)
    except models.NanoporeLibrary.DoesNotExist:
        library = models.NanoporeLibrary.objects.create(
            name=row["name"],
            nucleic_acid=models.NucleicAcidEnum.cdna,
            build_date=row["library_build_date"],
            ng_per_ul=row["library_input_ng_per_ul"],
            volume_ul=row["library_volume_ul"],
        )
        library.nucleic_acid_extraction.set(extractions)
        library.save()
    return library


def get_or_create_ont_splitseq_sequencing_run(row):
    name = row["sample_id"]
    try:
        run = models.SequencingRun.objects.get(name=name)
    except models.SequencingRun.DoesNotExist:
        plate = models.SplitSeqPlate.objects.get(pk=row["plate"])
        platform = models.Platform.objects.get(
            name=row["sequencing_run_platform"])

        run = models.SequencingRun.objects.create(
            # name is supposed to be the directory
            # where the file is?
            name=row["sample_id"],
            run_date=row["sequencing_run_date"],
            platform=platform,
            plate=plate,
            stranded="U",
            sequencer=row["sequencing_run_platform"],
            flowcell_kit=row["flowcell_kit"],
            flowcell_type=row["flowcell_type"],
            flowcell_id=row["flowcell_id"],
            sequencing_software=row["sequencing_software"],
        )
    return run


def load_splitseq_ont_samples(samples):
    for i, row in samples.iterrows():
        subpool = models.Subpool.objects.get(pk=row["subpool"])

        extraction = get_or_create_splitseq_ont_nucleic_acid_extraction(
            row, subpool)
        library = get_or_create_splitseq_ont_library(row, extraction)
        run = get_or_create_ont_splitseq_sequencing_run(row)

        try:
            libraryinrun = models.LibraryInRun.objects.get(
                subpool=subpool,
                nanopore=library,
                sequencing_run=run
            )
        except models.LibraryInRun.DoesNotExist:
            libraryinrun = models.LibraryInRun.objects.create(
                subpool=subpool,
                nanopore=library,
                sequencing_run=run
            )
            libraryinrun.save()
