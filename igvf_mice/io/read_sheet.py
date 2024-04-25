import pandas

from .. import models
from .converters import (
    normalize_strain,
    int_or_none,
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
                dissection=int_or_none(row["Dissection ID"]),
                strain=mouse_strains[row["Strain code"]],
                sex=row["Sex"],
                weight_g=row["Weight (g)"],
                date_of_birth=row["DOB"].date() if pandas.notnull(row["DOB"]) else None,
                dissection_start_time=uci_tz_or_none(row["Dissection start time"]),
                dissection_end_time=uci_tz_or_none(row["Dissection finish time"]),
                timepoint=row["Timepoint"],
                timepoint_unit=row["Timepoint unit"],
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

        if not pandas.isnull(row["dissection start"]):
            record.dissection_start_time = uci_tz_or_none(row["dissection start"])

        if not pandas.isnull(row["dissection end"]):
            record.dissection_end_time = uci_tz_or_none(row["dissection end"])

        tube_weight_label = "tube weight (g)"
        if not pandas.isnull(row[tube_weight_label]):
            record.tube_weight_g = float(row[tube_weight_label])

        total_weight_label = "tube+tissue weight (g)"
        if not pandas.isnull(row[total_weight_label]):
            record.total_weight_g = float(row[total_weight_label])

        record.save()
        record.ontology_term.set(tissue_terms)
        record.save()
        added += 1

        import_accessions(submitted_tissues.get(tissue_name), record)

    if failed > 0:
        raise ValidationError(f"Check warning messages. {failed} records failed")
    return added
