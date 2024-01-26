import pandas

from .. import models
from .converters import (
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
    loaded_tissues = {x.name: x for x in models.Tissues.objects.all()}

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
