import datetime
import pandas
import zoneinfo
from django.test import TestCase

from .. import models
from ..io.read_sheet import (
    import_accessions,
    import_mice,
    import_protocols,
)
from ..io.converters import (
    str_or_none,
    uci_tz_or_none,
)


class TestReadSheet(TestCase):
    fixtures = ["source", "mousestrain"]

    def test_import_protocol(self):
        self.assertEqual(models.ProtocolLink.objects.count(), 0)
        protocols = pandas.DataFrame(
            {
                "Protocol": ["splitseq_100k", "splitseq_1M_v2"],
                "Protocols.io version": [1, 1],
                "Link": [
                    "https://www.protocols.io/view/evercode-wt-v2-2-1-eq2lyj9relx9/v1",
                    "https://www.protocols.io/view/evercode-wt-mega-v2-2-1-8epv5xxrng1b/v1",
                ],
                "Description": [
                    "Parse Bio snRNA-seq for 100,000 cells or nuclei using v2 reagents",
                    "Parse Bio snRNA-seq for 1M cells or nuclei using v2 reagents",
                ],
            }
        )

        first = protocols[protocols["Protocol"] == "splitseq_100k"]
        self.assertEqual(first.shape[0], 1)

        import_protocols(first)
        self.assertEqual(models.ProtocolLink.objects.count(), 1)

        import_protocols(protocols)
        self.assertEqual(models.ProtocolLink.objects.count(), 2)

        for i, row in enumerate(models.ProtocolLink.objects.all()):
            self.assertEqual(row.name, protocols.iloc[i]["Protocol"])
            self.assertEqual(row.version, protocols.iloc[i]["Protocols.io version"])
            self.assertEqual(row.see_also, protocols.iloc[i]["Link"])
            self.assertEqual(row.description, protocols.iloc[i]["Description"])

    def test_import_mice(self):
        self.assertEqual(models.Mouse.objects.count(), 0)

        los_angeles = zoneinfo.ZoneInfo("America/Los_Angeles")
        dob_aug16 = datetime.datetime(2022, 8, 16)#, tzinfo=los_angeles)
        dob_jun20 = datetime.datetime(2023, 6, 20)#, tzinfo=los_angeles)

        start_016 = datetime.datetime(2022, 10, 27, 9, 1)#, tzinfo=los_angeles)
        start_017 = datetime.datetime(2022, 10, 27, 11, 44)#, tzinfo=los_angeles)
        start_144 = datetime.datetime(2023, 8, 28, 11, 15)#, tzinfo=los_angeles)
        finish_144 = datetime.datetime(2023, 8, 28, 11, 33)#, tzinfo=los_angeles)

        mice = pandas.DataFrame(
            {
                "Mouse Name": ["016_B6J_10F", "017_B6J_10M", "144_B6129S1F1J_10F"],
                "Strain code": ["B6J", "B6J", "B6129S1F1J"],
                "Sex": ["M", "F", "F"],
                "Weight (g)": [21.1, 26.3, 19.9],
                "DOB": [dob_aug16, dob_aug16, dob_jun20],
                "Dissection start time": [start_016, start_017, start_144],
                "Dissection finish time": [None, None, finish_144],
                "Timepoint": ["10 weeks"] * 3,
                "estrus_cycle": ["D", "NA", "DP"],
                "Operator": ["T1", "T2", "T1"],
                "Comments": ["", "", ""],
                "Housing number": [14669, 14670, None],
            }
        )

        submitted = {
            "016_B6J_10F": [
                {
                    "accession_prefix": "igvftst",
                    "name": "TSTDO32293389",
                    "uuid": "5adf9704-60ab-41da-bdb6-ac8a3b156fb3",
                    "see_also": "https://api.sandbox.igvf.org/rodent-donors/TSTDO32293389/",
                },
                {
                    "accession_prefix": "igvf",
                    "name": "IGVFDO7007WBAX",
                    "uuid": "7f506a6b-95d2-4e52-9e91-61f992a6c02c",
                    "see_also": "https://api.data.igvf.org/rodent-donors/IGVFDO7007WBAX/",
                },
            ],
            "017_B6J_10M": [
                {
                    "accession_prefix": "igvf",
                    "name": "IGVFDO4725SNCJ",
                    "uuid": "b022e300-8ef9-4f7e-a145-a818c70b9965",
                    "see_also": "https://api.data.igvf.org/rodent-donors/IGVFDO4725SNCJ/",
                }
            ],
        }

        first = mice[mice["Mouse Name"] == "016_B6J_10F"]
        added = import_mice(first)

        self.assertEqual(models.Mouse.objects.count(), 1)
        self.assertEqual(added, 1)

        record = models.Mouse.objects.get(name="016_B6J_10F")
        self.assertEqual(record.accession.count(), 0)
        import_accessions(submitted["016_B6J_10F"], record)
        self.assertEqual(record.accession.count(), 2)

        added = import_mice(mice, submitted)
        self.assertEqual(added, 2)

        for mouse_i, row in enumerate(models.Mouse.objects.all()):
            dissection_start_time = uci_tz_or_none(mice.iloc[mouse_i]["Dissection start time"])
            dissection_end_time = uci_tz_or_none(mice.iloc[mouse_i]["Dissection finish time"])

            self.assertEqual(row.name, mice.iloc[mouse_i]["Mouse Name"])
            self.assertEqual(row.strain.name, mice.iloc[mouse_i]["Strain code"])
            self.assertEqual(row.sex, mice.iloc[mouse_i]["Sex"])
            self.assertEqual(row.weight_g, mice.iloc[mouse_i]["Weight (g)"])
            self.assertEqual(row.date_of_birth, mice.iloc[mouse_i]["DOB"])
            self.assertEqual(row.dissection_start_time, dissection_start_time)
            self.assertEqual(row.dissection_end_time, dissection_end_time)
            self.assertEqual(row.timepoint_description, mice.iloc[mouse_i]["Timepoint"])
            self.assertEqual(row.estrus_cycle, mice.iloc[mouse_i]["estrus_cycle"])
            self.assertEqual(row.operator, mice.iloc[mouse_i]["Operator"])
            self.assertEqual(row.notes, mice.iloc[mouse_i]["Comments"])
            self.assertEqual(row.housing_number, str_or_none(mice.iloc[mouse_i]["Housing number"]))

            submitted_accessions = {x["name"]: x for x in submitted.get(row.name, [])}

            # the order of the accessions is not preserved.
            for accession in row.accession.all():
                expected = submitted_accessions[accession.name]
                self.assertEqual(accession.accession_prefix, expected["accession_prefix"])
                self.assertEqual(accession.name, expected["name"])
                self.assertEqual(str(accession.uuid), expected["uuid"])
                self.assertEqual(accession.see_also, expected["see_also"])

        added = import_mice(mice, submitted)
        self.assertEqual(added, 0)
