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
        else:
            record = models.Mouse.objects.get(pk=name)

        # import accession skips if submitted_accessions.get is None
        import_accessions(submitted_accessions.get(name), record)

    print("Currently have {} mice loaded".format(models.Mouse.objects.count()))
    assert not failed, "Check warning messages"
    
