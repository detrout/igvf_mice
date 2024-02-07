import datetime
import functools
from io import StringIO
import pandas
import zoneinfo
from django.test import TestCase

from .. import models
from ..io.read_sheet import (
    import_accessions,
    import_mice,
    import_protocols,
    import_tissues,
    is_plate_name,
    WellContent,
    PlateLayoutParser,
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

    def test_import_tissues(self):
        mice = get_test_mice_sheet()
        import_mice(mice)
        self.assertEqual(models.Tissue.objects.count(), 0)

        tissues = get_test_tissue_sheet()

        first = tissues[tissues["Mouse_Tissue ID"] == "016_B6J_10F_01"]
        import_tissues(first)
        self.assertEqual(models.Tissue.objects.count(), 1)

        import_tissues(tissues)
        self.assertEqual(models.Tissue.objects.count(), 6)

        for tissue_i, row in enumerate(models.Tissue.objects.all()):
            dissection_start_time = uci_tz_or_none(tissues.iloc[tissue_i]["Dissection start"])
            dissection_end_time = uci_tz_or_none(tissues.iloc[tissue_i]["Dissection end"])

            self.assertEqual(row.name, tissues.iloc[tissue_i]["Mouse_Tissue ID"])
            self.assertEqual(row.mouse.name, tissues.iloc[tissue_i]["Mouse name"])
            self.assertEqual(row.dissection_start_time, dissection_start_time)
            self.assertEqual(row.dissection_end_time, dissection_end_time)
            self.assertEqual(row.tube_label, tissues.iloc[tissue_i]["Tube label"])
            self.assertEqual(row.mouse.strain.name, tissues.iloc[tissue_i]["Genotype"])
            self.assertEqual(row.mouse.weight_g, tissues.iloc[tissue_i]["Body weight (g)"])


igvf_003_csv = """,IGVF_003,,,,,,,,,,,,,,,
,,,Tissue1_F_rep1,Tissue1_M_rep1,Tissue1_F_rep2,Tissue1_M_rep2,Tissue1_F_rep3,Tissue1_M_rep3,Tissue1_F_rep4,Tissue1_M_rep4,Tissue2_F_1/3,Tissue2_M_1/3,Tissue2_F_2/4,Tissue2_M_2/4,,
,,,1,2,3,4,5,6,7,8,9,10,11,12,,
,B6J,A,016_B6J_10F_03,017_B6J_10M_03,018_B6J_10F_03,019_B6J_10M_03,020_B6J_10F_03,021_B6J_10M_03,024_B6J_10F_03,025_B6J_10M_03,AB_F1_06,AB_M1_06,AB_F2_06,AB_M2_06,,
,NODJ,B,066_NODJ_10F_03,067_NODJ_10M_03,068_NODJ_10F_03,069_NODJ_10M_03,070_NODJ_10F_03,071_NODJ_10M_03,072_NODJ_10F_03,073_NODJ_10M_03,AB_F3_06,AB_M3_06,AB_F4_06,AB_M4_06,,
,AJ,C,026_AJ_10F_03,029_AJ_10M_03,028_AJ_10F_03,031_AJ_10M_03,030_AJ_10F_03,033_AJ_10M_03,032_AJ_10F_03,035_AJ_10M_03,CD_F1_06,CD_M1_06,CD_F2_06,CD_M2_06,,
,PWKJ,D,076_PWKJ_10F_03,077_PWKJ_10M_03,078_PWKJ_10F_03,079_PWKJ_10M_03,080_PWKJ_10F_03,081_PWKJ_10M_03,084_PWKJ_10F_03,085_PWKJ_10M_03,CD_F3_06,CD_M3_06,CD_F4_06,CD_M4_06,,
,129S1J,E,036_129S1J_10F_03,037_129S1J_10M_03,038_129S1J_10F_03,041_129S1J_10M_03,040_129S1J_10F_03,043_129S1J_10M_03,044_129S1J_10F_03,045_129S1J_10M_03,EF_F1_06,EF_M1_06,EF_F2_06,EF_M2_06,,
,CASTJ,F,086_CASTJ_10F_03,087_CASTJ_10M_03,088_CASTJ_10F_03,089_CASTJ_10M_03,090_CASTJ_10F_03,091_CASTJ_10M_03,094_CASTJ_10F_03,093_CASTJ_10M_03,EF_F3_06,EF_M3_06,EF_F4_06,EF_M4_06,,
,WSBJ,G,058_WSBJ_10F_03,057_WSBJ_10M_03,060_WSBJ_10F_03,059_WSBJ_10M_03,062_WSBJ_10F_03,061_WSBJ_10M_03,096_WSBJ_10F_03,063_WSBJ_10M_03,GH_F1_06,GH_M1_06,GH_F2_06,GH_M2_06,,
,NZOJ,H,092_CASTJ_10F_03,047_NZOJ_10M_03,048_NZOJ_10F_03,049_NZOJ_10M_03,050_NZOJ_10F_03,051_NZOJ_10M_03,052_NZOJ_10F_03,053_NZOJ_10M_03,GH_F3_06,GH_M3_06,GH_F4_06,GH_M4_06,,
,,,,,,,,,,,,,,,,
,,,Tissue1_F_rep1,Tissue1_M_rep1,Tissue1_F_rep2,Tissue1_M_rep2,Tissue1_F_rep3,Tissue1_M_rep3,Tissue1_F_rep4,Tissue1_M_rep4,,,,,,
,,A,016_B6J_10F_06,017_B6J_10M_06,018_B6J_10F_06,019_B6J_10M_06,020_B6J_10F_06,021_B6J_10M_06,024_B6J_10F_06,025_B6J_10M_06,,,,,,
,,B,066_NODJ_10F_06,067_NODJ_10M_06,068_NODJ_10F_06,069_NODJ_10M_06,070_NODJ_10F_06,071_NODJ_10M_06,072_NODJ_10F_06,073_NODJ_10M_06,,,,,,
,,,AB_F1_06,AB_M1_06,AB_F2_06,AB_M2_06,AB_F3_06,AB_M3_06,AB_F4_06,AB_M4_06,,,,,,
,,,A9,A10,A11,A12,B9,B10,B11,B12,,,,,,
,,,,,,,,,,,,,,,,
,,C,026_AJ_10F_06,029_AJ_10M_06,028_AJ_10F_06,031_AJ_10M_06,030_AJ_10F_06,033_AJ_10M_06,032_AJ_10F_06,035_AJ_10M_06,,,,,,
,,D,076_PWKJ_10F_06,077_PWKJ_10M_06,078_PWKJ_10F_06,079_PWKJ_10M_06,080_PWKJ_10F_06,081_PWKJ_10M_06,084_PWKJ_10F_06,085_PWKJ_10M_06,,,,,,
,,,CD_F1_06,CD_M1_06,CD_F2_06,CD_M2_06,CD_F3_06,CD_M3_06,CD_F4_06,CD_M4_06,,,,,,
,,,C9,C10,C11,C12,D9,D10,D11,D12,,,,,,
,,,,,,,,,,,,,,,,
,,E,036_129S1J_10F_06,037_129S1J_10M_06,038_129S1J_10F_06,041_129S1J_10M_06,040_129S1J_10F_06,043_129S1J_10M_06,044_129S1J_10F_06,045_129S1J_10M_06,,,,,,
,,F,086_CASTJ_10F_06,087_CASTJ_10M_06,088_CASTJ_10F_06,089_CASTJ_10M_06,090_CASTJ_10F_06,091_CASTJ_10M_06,094_CASTJ_10F_06,093_CASTJ_10M_06,,,,,,
,,,EF_F1_06,EF_M1_06,EF_F2_06,EF_M2_06,EF_F3_06,EF_M3_06,EF_F4_06,EF_M4_06,,,,,,
,,,E9,E10,E11,E12,F9,F10,F11,F12,,,,,,
,,,,,,,,,,,,,,,,
,,G,058_WSBJ_10F_06,057_WSBJ_10M_06,060_WSBJ_10F_06,059_WSBJ_10M_06,062_WSBJ_10F_06,061_WSBJ_10M_06,096_WSBJ_10F_06,063_WSBJ_10M_06,,,,,,
,,H,046_NZOJ_10F_06,047_NZOJ_10M_06,048_NZOJ_10F_06,049_NZOJ_10M_06,050_NZOJ_10F_06,051_NZOJ_10M_06,052_NZOJ_10F_06,053_NZOJ_10M_06,,,,,,
,,,GH_F1_06,GH_M1_06,GH_F2_06,GH_M2_06,GH_F3_06,GH_M3_06,GH_F4_06,GH_M4_06,,,,,,
,,,G9,G10,G11,G12,H9,H10,H11,H12,,,,,,
,,,,,,,,,,,,,,,,
"""
igvf_003_row_start = 1

igvf_005_csv = """,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,IGVF_005,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,Tissue1_F_rep1,Tissue1_M_rep1,Tissue1_F_rep2,Tissue1_M_rep2,Tissue1_F_rep3,Tissue1_M_rep3,Tissue1_F_rep4,Tissue1_M_rep4,Tissue2_F_1/3,Tissue2_M_1/3,Tissue2_F_2/4,Tissue2_M_2/4,,
,,,1,2,3,4,5,6,7,8,9,10,11,12,,
,B6J,A,016_B6J_10F_05,017_B6J_10M_05,018_B6J_10F_05,019_B6J_10M_05,020_B6J_10F_05,021_B6J_10M_05,024_B6J_10F_05,025_B6J_10M_05,AB_F1_01,AB_M1_01,AB_F2_01,AB_M2_01,,
,NODJ,B,066_NODJ_10F_05,067_NODJ_10M_05,068_NODJ_10F_05,069_NODJ_10M_05,070_NODJ_10F_05,071_NODJ_10M_05,072_NODJ_10F_05,073_NODJ_10M_05,AB_F3_01,AB_M3_01,AB_F4_01,AB_M4_01,,
,AJ,C,026_AJ_10F_05,029_AJ_10M_05,028_AJ_10F_05,031_AJ_10M_05,030_AJ_10F_05,033_AJ_10M_05,032_AJ_10F_05,035_AJ_10M_05,CD_F1_01,CD_M1_01,CD_F2_01,CD_M2_01,,
,PWKJ,D,076_PWKJ_10F_05,077_PWKJ_10M_05,078_PWKJ_10F_05,079_PWKJ_10M_05,080_PWKJ_10F_05,081_PWKJ_10M_05,084_PWKJ_10F_05,085_PWKJ_10M_05,CD_F3_01,CD_M3_01,CD_F4_01,CD_M4_01,,
,129S1J,E,036_129S1J_10F_05,037_129S1J_10M_05,038_129S1J_10F_05,041_129S1J_10M_05,040_129S1J_10F_05,043_129S1J_10M_05,044_129S1J_10F_05,045_129S1J_10M_05,EF_F1_01,EF_M1_01,EF_F2_01,EF_M2_01,,
,CASTJ,F,086_CASTJ_10F_05,087_CASTJ_10M_05,088_CASTJ_10F_05,089_CASTJ_10M_05,090_CASTJ_10F_05,091_CASTJ_10M_05,094_CASTJ_10F_05,093_CASTJ_10M_05,EF_F3_01,EF_M3_01,EF_F4_01,EF_M4_01,,
,WSBJ,G,058_WSBJ_10F_05,057_WSBJ_10M_05,060_WSBJ_10F_05,059_WSBJ_10M_05,062_WSBJ_10F_05,061_WSBJ_10M_05,096_WSBJ_10F_05,063_WSBJ_10M_05,GH_F1_01,GH_M1_01,GH_F2_01,GH_M2_01,,
,NZOJ,H,046_NZOJ_10F_05,047_NZOJ_10M_05,048_NZOJ_10F_05,049_NZOJ_10M_05,050_NZOJ_10F_05,051_NZOJ_10M_05,052_NZOJ_10F_05,053_NZOJ_10M_05,GH_F3_01,GH_M3_01,GH_F4_01,GH_M4_01,,
,,,,,,,,,,,,,,,,
,,,Tissue1_F_rep1,Tissue1_M_rep1,Tissue1_F_rep2,Tissue1_M_rep2,Tissue1_F_rep3,Tissue1_M_rep3,Tissue1_F_rep4,Tissue1_M_rep4,,,,,,
,,A,016_B6J_10F_01,017_B6J_10M_01,018_B6J_10F_01,019_B6J_10M_01,020_B6J_10F_01,021_B6J_10M_01,024_B6J_10F_01,025_B6J_10M_01,,,,,,
,,B,066_NODJ_10F_01,067_NODJ_10M_01,068_NODJ_10F_01,069_NODJ_10M_01,070_NODJ_10F_01,071_NODJ_10M_01,072_NODJ_10F_01,073_NODJ_10M_01,,,,,,
,,,AB_F1_01,AB_M1_01,AB_F2_01,AB_M2_01,AB_F3_01,AB_M3_01,AB_F4_01,AB_M4_01,,,,,,
,,,A9,A10,A11,A12,B9,B10,B11,B12,,,,,,
,,,,,,,,,,,,,,,,
,,C,026_AJ_10F_01,029_AJ_10M_01,028_AJ_10F_01,031_AJ_10M_01,030_AJ_10F_01,033_AJ_10M_01,032_AJ_10F_01,035_AJ_10M_01,,,,,,
,,D,076_PWKJ_10F_01,077_PWKJ_10M_01,078_PWKJ_10F_01,079_PWKJ_10M_01,080_PWKJ_10F_01,081_PWKJ_10M_01,084_PWKJ_10F_01,085_PWKJ_10M_01,,,,,,
,,,CD_F1_01,CD_M1_01,CD_F2_01,CD_M2_01,CD_F3_01,CD_M3_01,CD_F4_01,CD_M4_01,,,,,,
,,,C9,C10,C11,C12,D9,D10,D11,D12,,,,,,
,,,,,,,,,,,,,,,,
,,E,036_129S1J_10F_01,037_129S1J_10M_01,038_129S1J_10F_01,041_129S1J_10M_01,040_129S1J_10F_01,043_129S1J_10M_01,044_129S1J_10F_01,045_129S1J_10M_01,,,,,,
,,F,086_CASTJ_10F_01,087_CASTJ_10M_01,088_CASTJ_10F_01,089_CASTJ_10M_01,090_CASTJ_10F_01,091_CASTJ_10M_01,094_CASTJ_10F_01,093_CASTJ_10M_01,,,,,,
,,,EF_F1_01,EF_M1_01,EF_F2_01,EF_M2_01,EF_F3_01,EF_M3_01,EF_F4_01,EF_M4_01,,,,,,
,,,E9,E10,E11,E12,F9,F10,F11,F12,,,,,,
,,,,,,,,,,,,,,,,
,,G,058_WSBJ_10F_01,057_WSBJ_10M_01,060_WSBJ_10F_01,059_WSBJ_10M_01,062_WSBJ_10F_01,061_WSBJ_10M_01,096_WSBJ_10F_01,063_WSBJ_10M_01,,,,,,
,,H,092_CASTJ_10F_01,047_NZOJ_10M_01,048_NZOJ_10F_01,049_NZOJ_10M_01,050_NZOJ_10F_01,051_NZOJ_10M_01,052_NZOJ_10F_01,053_NZOJ_10M_01,,,,,,
,,,GH_F1_01,GH_M1_01,GH_F2_01,GH_M2_01,GH_F3_01,GH_M3_01,GH_F4_01,GH_M4_01,,,,,,
,,,G9,G10,G11,G12,H9,H10,H11,H12,,,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
"""
igvf_005_row_start = 7

igvf_b01_csv = """,,,,,,,,,,,,,,,,
,IGVF_B01,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,F,M,F,M,F,M,F,M,F,M,F,M,,
,,,1,2,3,4,5,6,7,8,9,10,11,12,,
,B6J Rep 1,A,118_B6J_10F_21,117_B6J_10M_21,118_B6J_10F_21,117_B6J_10M_21,118_B6J_10F_21,117_B6J_10M_21,118_B6J_10F_21,117_B6J_10M_21,118_B6J_10F_21,117_B6J_10M_21,118_B6J_10F_21,117_B6J_10M_21,,
,CASTJ Rep 1,B,106_CASTJ_10F_21,105_CASTJ_10M_21,106_CASTJ_10F_21,105_CASTJ_10M_21,106_CASTJ_10F_21,105_CASTJ_10M_21,106_CASTJ_10F_21,105_CASTJ_10M_21,106_CASTJ_10F_21,105_CASTJ_10M_21,106_CASTJ_10F_21,105_CASTJ_10M_21,,
,B6J Rep 2,C,120_B6J_10F_21,119_B6J_10M_21,120_B6J_10F_21,119_B6J_10M_21,120_B6J_10F_21,119_B6J_10M_21,120_B6J_10F_21,119_B6J_10M_21,120_B6J_10F_21,119_B6J_10M_21,120_B6J_10F_21,119_B6J_10M_21,,
,CASTJ Rep 2,D,108_CASTJ_10F_21,107_CASTJ_10M_21,108_CASTJ_10F_21,107_CASTJ_10M_21,108_CASTJ_10F_21,107_CASTJ_10M_21,108_CASTJ_10F_21,107_CASTJ_10M_21,108_CASTJ_10F_21,107_CASTJ_10M_21,108_CASTJ_10F_21,107_CASTJ_10M_21,,
,,E,,,,,,,,,,,,,,
,,F,,,,,,,,,,,,,,
,,G,,,,,,,,,,,,,,
,,H,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,,nuclei stock volume (uL),buffer volume (uL),total volume (uL) - need 90 ul,,,,,,,,,,
,,,118_B6J_10F_21,15,87.2,102.2,A1,A3,A5,A7,A9,A11,,,,
,,,117_B6J_10M_21,15,113.2,128.2,A2,A4,A6,A8,A10,A12,,,,
,,,106_CASTJ_10F_21,15,82.4,97.4,B1,B3,B5,B7,B9,B11,,,,
,,,105_CASTJ_10M_21,15,125.3,140.3,B2,B4,B6,B8,B10,B12,,,,
,,,120_B6J_10F_21,15,70,85,C1,C3,C5,C7,C9,C11,,,,
,,,119_B6J_10M_21,15,74.5,89.5,C2,C4,C6,C8,C10,C12,,,,
,,,108_CASTJ_10F_21,15,87.8,102.8,D1,D3,D5,D7,D9,D11,,,,
,,,107_CASTJ_10M_21,15,122.1,137.1,D2,D4,D6,D8,D10,D12,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
"""
igvf_b01_row_start = 3

igvf_012_csv = """,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,IGVF_012,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,Mixed,Mixed,Mixed,Mixed,Mixed,Mixed,Mixed,Mixed,Mixed,Mixed,Mixed,Mixed,,
,,,1,2,3,4,5,6,7,8,9,10,11,12,,
,,A,016_B6J_10F_08,016_B6J_10F_08,016_B6J_10F_08,016_B6J_10F_08,022_B6J_10F_16,022_B6J_10F_16,022_B6J_10F_16,022_B6J_10F_16,029_AJ_10M_06,029_AJ_10M_06,029_AJ_10M_06,029_AJ_10M_06,,
,,B,031_AJ_10M_06,031_AJ_10M_06,031_AJ_10M_06,031_AJ_10M_06,047_NZOJ_10M_08,047_NZOJ_10M_08,047_NZOJ_10M_08,047_NZOJ_10M_08,122_B6J_10F_16,122_B6J_10F_16,122_B6J_10F_16,122_B6J_10F_16,,
,,C,046_NZOJ_10F_03,046_NZOJ_10F_03,046_NZOJ_10F_03,046_NZOJ_10F_03,058_WSBJ_10F_06,058_WSBJ_10F_06,058_WSBJ_10F_06,058_WSBJ_10F_06,076_PWKJ_10F_08,076_PWKJ_10F_08,076_PWKJ_10F_08,076_PWKJ_10F_08,,
,,D,057_WSBJ_10M_06,057_WSBJ_10M_06,057_WSBJ_10M_06,057_WSBJ_10M_06,046_NZOJ_10F_01,046_NZOJ_10F_01,046_NZOJ_10F_01,046_NZOJ_10F_01,062_WSBJ_10F_06,062_WSBJ_10F_06,062_WSBJ_10F_06,062_WSBJ_10F_06,,
,,,,,,,,,,,,,,,,

"""
igvf_012_row_start = 4

igvf_015_csv = """,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
,IGVF_015,,,,,,,,,,,,,,,
,,,Hypothalamus/Pituitary,Cortex/Hippocampus left,Liver,Heart,Adrenal,F Gonads + M Gonads left,Kidney left,Gastrocnemius left,PBMCs,Hypothalamus/Pituitary,Cortex/Hippocampus left,Adrenal,,
,,,1,2,3,4,5,6,7,8,9,10,11,12,,
,Tissue_M_rep1,A,239_TREM2_10F_01,239_TREM2_10F_03,239_TREM2_10F_05,239_TREM2_10F_06,239_TREM2_10F_08,239_TREM2_10F_26,239_TREM2_10F_31,239_TREM2_10F_33,239_TREM2_10F_20,239_TREM2_10F_01,239_TREM2_10F_03,239_TREM2_10F_08,,
,Tissue_F_rep1,B,240_TREM2_10M_01,240_TREM2_10M_03,240_TREM2_10M_05,240_TREM2_10M_06,240_TREM2_10M_08,240_TREM2_10M_25,240_TREM2_10M_31,240_TREM2_10M_33,240_TREM2_10M_20,240_TREM2_10M_01,240_TREM2_10M_03,240_TREM2_10M_08,,
,Tissue_M_rep2,C,241_TREM2_10F_01,241_TREM2_10F_03,241_TREM2_10F_05,241_TREM2_10F_06,241_TREM2_10F_08,241_TREM2_10F_26,241_TREM2_10F_31,241_TREM2_10F_33,241_TREM2_10F_20,241_TREM2_10F_01,241_TREM2_10F_03,241_TREM2_10F_08,,
,Tissue_F_rep2,D,242_TREM2_10M_01,242_TREM2_10M_03,242_TREM2_10M_05,242_TREM2_10M_06,242_TREM2_10M_08,242_TREM2_10M_25,242_TREM2_10M_31,242_TREM2_10M_33,242_TREM2_10M_20,242_TREM2_10M_01,242_TREM2_10M_03,242_TREM2_10M_08,,
,Tissue_M_rep3,E,243_TREM2_10F_01,243_TREM2_10F_03,243_TREM2_10F_05,243_TREM2_10F_06,243_TREM2_10F_08,243_TREM2_10F_26,243_TREM2_10F_31,243_TREM2_10F_33,243_TREM2_10F_20,243_TREM2_10F_01,243_TREM2_10F_03,243_TREM2_10F_08,,
,Tissue_F_rep3,F,244_TREM2_10M_01,244_TREM2_10M_03,244_TREM2_10M_05,244_TREM2_10M_06,244_TREM2_10M_08,244_TREM2_10M_25,244_TREM2_10M_31,244_TREM2_10M_33,248_TREM2_10M_20,244_TREM2_10M_01,244_TREM2_10M_03,244_TREM2_10M_08,,
,Tissue_M_rep4,G,245_TREM2_10F_01,245_TREM2_10F_03,245_TREM2_10F_05,245_TREM2_10F_06,245_TREM2_10F_08,245_TREM2_10F_26,245_TREM2_10F_31,245_TREM2_10F_33,247_TREM2_10F_20,245_TREM2_10F_01,245_TREM2_10F_03,245_TREM2_10F_08,,
,Tissue_F_rep4,H,248_TREM2_10M_01,248_TREM2_10M_03,248_TREM2_10M_05,248_TREM2_10M_06,248_TREM2_10M_08,248_TREM2_10M_25,248_TREM2_10M_31,248_TREM2_10M_33,250_TREM2_10M_20,248_TREM2_10M_01,248_TREM2_10M_03,248_TREM2_10M_08,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,
"""
igvf_015_row_start = 3

igvf_0xx_1_csv = """,,,,,,,,,,,,,,,,
,IGVF_0XX,,,,,,,,,,,,,,,
,,,Tissue1_F_rep1 / rep3,Tissue1_F_rep1/ rep3,Tissue1_F_rep1 / rep3,Tissue1_M_rep1 / rep3,Tissue1_M_rep1 / rep3,Tissue1_M_rep1 / rep3,Tissue1_F_rep2 / rep4,Tissue1_F_rep2 / rep4,Tissue1_F_rep2 / rep4,Tissue1_M_rep2 / rep4,Tissue1_M_rep2 / rep4,Tissue1_M_rep2 / rep4,,
,,,1,2,3,4,5,6,7,8,9,10,11,12,,
,B6NZOF1J,A,B6NZOF1J_F_rep1_1,B6NZOF1J_F_rep1_2,B6NZOF1J_F_rep1_3,B6NZOF1J_M_rep1_1,B6NZOF1J_M_rep1_2,B6NZOF1J_M_rep1_3,B6NZOF1J_F_rep2_1,B6NZOF1J_F_rep2_2,B6NZOF1J_F_rep2_3,B6NZOF1J_M_rep2_1,B6NZOF1J_M_rep2_2,B6NZOF1J_M_rep2_3,,
,,B,B6NZOF1J_F_rep3_1,B6NZOF1J_F_rep3_2,B6NZOF1J_F_rep3_3,B6NZOF1J_M_rep3_1,B6NZOF1J_M_rep3_2,B6NZOF1J_M_rep3_3,B6NZOF1J_F_rep4_1,B6NZOF1J_F_rep4_2,B6NZOF1J_F_rep4_3,B6NZOF1J_M_rep4_1,B6NZOF1J_M_rep4_2,B6NZOF1J_M_rep4_3,,
,B6AF1J,C,B6AF1J_F_rep1_1,B6AF1J_F_rep1_2,B6AF1J_F_rep1_3,B6AF1J_M_rep1_1,B6AF1J_M_rep1_2,B6AF1J_M_rep1_3,B6AF1J_F_rep2_1,B6AF1J_F_rep2_2,B6AF1J_F_rep2_3,B6AF1J_M_rep2_1,B6AF1J_M_rep2_2,B6AF1J_M_rep2_3,,
,,D,B6AF1J_F_rep3_1,B6AF1J_F_rep3_2,B6AF1J_F_rep3_3,B6AF1J_M_rep3_1,B6AF1J_M_rep3_2,B6AF1J_M_rep3_3,B6AF1J_F_rep4_1,B6AF1J_F_rep4_2,B6AF1J_F_rep4_3,B6AF1J_M_rep4_1,B6AF1J_M_rep4_2,B6AF1J_M_rep4_3,,
,,,,,,,,,,,,,,,,
1.1Billion per P3 200cycles kit x2-3,,,,,,,,,,,,,,,,
1.6 Billion reads per strain,,,,,,,,,,,,,,,,
"~160,000 cells per kit",,,,,,,,,,,,,,,,
"~80,000 cells per strain",,,,,,,,,,,,,,,,
~1000 cells/uL x 15uL x 3wells x 8reps = 360k ,,,,,,,,,,,,,,,,
2 strains,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,

"""
igvf_0xx_1_row_start = 3


def read_layout(csv):
    """Have pandas parse a Python text literal containing CSV data"""
    stream = StringIO(csv)
    return pandas.read_csv(stream, header=None)


def validate_plate_column_ids(plate_column_ids):
    expected_column_ids = set(range(1,13))
    for column_id in plate_column_ids:
        assert column_id in expected_column_ids, f"{column_id} {type(column_id)} not in expected_column_ids"


def validate_plate_row_ids(plate_row_labels):
    expected_row_labels = set(("A", "B", "C", "D", "E", "F", "G", "H"))
    for row_label in plate_row_labels:
        assert row_label in expected_row_labels, f"{row_label} not in expected labels"


class TestPlateLayoutParser(TestCase):
    fixtures = ["source", "mousestrain"]

    def test_is_plate_name(self):
        parser = PlateLayoutParser()
        self.assertEqual(is_plate_name(None), False)
        self.assertEqual(is_plate_name("Foo"), False)
        self.assertEqual(is_plate_name("IGVF_123"), True)
        self.assertEqual(is_plate_name("IGVF_0XX"), True)

    def test_find_plate_start_one_large_plate(self):
        layout = read_layout(igvf_003_csv)
        starts = list(PlateLayoutParser().find_plate_start(layout))

        self.assertEqual(len(starts), 1)
        known_good = [("IGVF_003", igvf_003_row_start),]
        for actual, expected in zip(starts, known_good):
            self.assertEqual(actual[0], expected[0])
            self.assertEqual(actual[1], expected[1])

    def test_find_plate_start_two_large_plates(self):
        layouts = read_layout("".join([igvf_003_csv, igvf_005_csv]))

        starts = list(PlateLayoutParser().find_plate_start(layouts))

        known_good = [("IGVF_003", igvf_003_row_start), ("IGVF_005", 39)]
        self.assertEqual(len(starts), 2)
        for actual, expected in zip(starts, known_good):
            self.assertEqual(actual[0], expected[0])
            self.assertEqual(actual[1], expected[1])

    def test_find_plate_start_with_b01(self):
        layouts = read_layout("".join([igvf_003_csv, igvf_b01_csv, igvf_005_csv]))

        starts = list(PlateLayoutParser().find_plate_start(layouts))

        known_good = [("IGVF_003", igvf_003_row_start), ("IGVF_B01", 36), ("IGVF_005", 66)]
        self.assertEqual(len(starts), len(known_good))
        for actual, expected in zip(starts, known_good):
            self.assertEqual(actual[0], expected[0])
            self.assertEqual(actual[1], expected[1])

    def test_find_plate_start_with_012(self):
        layouts = read_layout("".join([igvf_003_csv, igvf_012_csv, igvf_005_csv]))

        starts = list(PlateLayoutParser().find_plate_start(layouts))

        known_good = [("IGVF_003", igvf_003_row_start), ("IGVF_012", 37), ("IGVF_005", 50)]
        self.assertEqual(len(starts), len(known_good))
        for actual, expected in zip(starts, known_good):
            self.assertEqual(actual[0], expected[0])
            self.assertEqual(actual[1], expected[1])

    def test_find_plate_start_with_incomplete(self):
        layouts = read_layout("".join([igvf_003_csv, igvf_012_csv, igvf_0xx_1_csv]))

        starts = list(PlateLayoutParser().find_plate_start(layouts))

        known_good = [("IGVF_003", igvf_003_row_start), ("IGVF_012", 37)]
        self.assertEqual(len(starts), len(known_good))
        for actual, expected in zip(starts, known_good):
            self.assertEqual(actual[0], expected[0])
            self.assertEqual(actual[1], expected[1])

    def test_find_plate_start_with_015_incomplete(self):
        layouts = read_layout("".join([igvf_003_csv, igvf_012_csv, igvf_015_csv, igvf_0xx_1_csv]))

        starts = list(PlateLayoutParser().find_plate_start(layouts))

        known_good = [("IGVF_003", igvf_003_row_start), ("IGVF_012", 37), ("IGVF_015", 47)]
        self.assertEqual(len(starts), len(known_good))
        for actual, expected in zip(starts, known_good):
            self.assertEqual(actual[0], expected[0])
            self.assertEqual(actual[1], expected[1])

    def test_get_block_column_ids_tissue_block(self):
        layouts = read_layout(igvf_003_csv)

        column_ids = list(PlateLayoutParser().get_block_column_ids(layouts, igvf_003_row_start))
        expected = [str(x) for x in range(1, 13)]
        self.assertEqual(column_ids, expected)

    def test_get_block_column_labels_tissue_block(self):
        layouts = read_layout(igvf_003_csv)

        column_labels = list(PlateLayoutParser().get_block_column_labels(layouts, igvf_003_row_start))
        expected = [
            "Tissue1_F_rep1",
            "Tissue1_M_rep1",
            "Tissue1_F_rep2",
            "Tissue1_M_rep2",
            "Tissue1_F_rep3",
            "Tissue1_M_rep3",
            "Tissue1_F_rep4",
            "Tissue1_M_rep4",
            "Tissue2_F_1/3",
            "Tissue2_M_1/3",
            "Tissue2_F_2/4",
            "Tissue2_M_2/4"
        ]
        self.assertEqual(column_labels, expected)

    def test_get_block_column_labels_sex_tissue_block(self):
        layouts = read_layout(igvf_b01_csv)

        column_labels = list(PlateLayoutParser().get_block_column_labels(layouts, igvf_b01_row_start))
        expected = ["F", "M", "F", "M", "F", "M", "F", "M", "F", "M", "F", "M"]
        self.assertEqual(column_labels, expected)

    def test_get_block_column_labels_mixed_tissue_block(self):
        layouts = read_layout(igvf_012_csv)

        column_labels = list(PlateLayoutParser().get_block_column_labels(layouts, igvf_012_row_start))
        expected = ["Mixed"] * 12
        self.assertEqual(column_labels, expected)


    def test_get_block_complex_column_start(self):
        layouts = read_layout(igvf_003_csv)

        well_end = PlateLayoutParser().get_block_simple_column_end(layouts, igvf_003_row_start)
        self.assertEqual(well_end, 11)

    def test_get_block_row_ids_full_block(self):
        layouts = read_layout(igvf_003_csv)

        row_ids = list(PlateLayoutParser().get_block_row_ids(layouts, igvf_003_row_start))
        self.assertEqual(row_ids, ["A", "B", "C", "D", "E", "F", "G", "H"])

    def test_get_block_row_ids_b01_half_block(self):
        # This one the list of labels continues past the available data
        layouts = read_layout(igvf_b01_csv)

        row_ids = list(PlateLayoutParser().get_block_row_ids(layouts, igvf_b01_row_start))
        self.assertEqual(row_ids, ["A", "B", "C", "D"])

    def test_get_block_row_ids_half_block(self):
        layouts = read_layout(igvf_012_csv)

        row_ids = list(PlateLayoutParser().get_block_row_ids(layouts, igvf_012_row_start))
        self.assertEqual(row_ids, ["A", "B", "C", "D"])

    def test_get_block_row_labels_full_block(self):
        layouts = read_layout(igvf_003_csv)

        row_labels = list(PlateLayoutParser().get_block_row_labels(layouts, igvf_003_row_start))
        expected = ["B6J", "NODJ", "AJ", "PWKJ", "129S1J", "CASTJ", "WSBJ", "NZOJ"]
        self.assertEqual(row_labels, expected)

    def test_get_block_row_labels_b01_half_block(self):
        # This one the list of labels continues past the available data
        layouts = read_layout(igvf_b01_csv)

        row_labels = list(PlateLayoutParser().get_block_row_labels(layouts, igvf_b01_row_start))
        expected = ["B6J Rep 1", "CASTJ Rep 1", "B6J Rep 2", "CASTJ Rep 2"]
        self.assertEqual(row_labels, expected)

    def test_get_block_row_labels_half_block(self):
        layouts = read_layout(igvf_012_csv)

        row_labels = list(PlateLayoutParser().get_block_row_labels(layouts, igvf_012_row_start))
        self.assertEqual(row_labels, [])

    def test_get_simple_block_column_end(self):
        layouts = read_layout(igvf_012_csv)

        column_end = PlateLayoutParser().get_block_simple_column_end(layouts, igvf_012_row_start)
        self.assertEqual(column_end, 15)

    def test_get_merged_well_contents(self):
        layouts = read_layout(igvf_003_csv)

        parser = PlateLayoutParser()
        wells = parser.get_merged_well_contents("IGVF_003", layouts, igvf_003_row_start)

        self.assertEqual(wells["A", "9"], [WellContent("B6J", "016_B6J_10F_06"), WellContent("NODJ", "066_NODJ_10F_06")])
        self.assertEqual(wells["B", "12"], [WellContent("B6J", "025_B6J_10M_06"), WellContent("NODJ", "073_NODJ_10M_06")])

        self.assertEqual(wells["C", "9"], [WellContent("AJ", "026_AJ_10F_06"), WellContent("PWKJ", "076_PWKJ_10F_06")])
        self.assertEqual(wells["D", "12"], [WellContent("AJ", "035_AJ_10M_06"), WellContent("PWKJ", "085_PWKJ_10M_06")])

        self.assertEqual(wells["E", "9"], [WellContent("129S1J", "036_129S1J_10F_06"), WellContent("CASTJ", "086_CASTJ_10F_06")])
        self.assertEqual(wells["F", "12"], [WellContent("129S1J", "045_129S1J_10M_06"), WellContent("CASTJ", "093_CASTJ_10M_06")])

        self.assertEqual(wells["G", "9"], [WellContent("WSBJ", "058_WSBJ_10F_06"), WellContent("NZOJ", "046_NZOJ_10F_06")])
        self.assertEqual(wells["H", "12"], [WellContent("WSBJ", "063_WSBJ_10M_06"), WellContent("NZOJ", "053_NZOJ_10M_06")])

    def test_get_validation_label_rules_sex(self):
        labels = ["Tissue1_F_rep1", "Tissue2_M_rep3", "F", "M"]
        data = ["016_B6J_10F_03", "017_B6J_10M_03", "018_B6J_10F_03", "019_B6J_10M_03"]

        for rule, value in zip(PlateLayoutParser().get_validation_label_rules("IGVF_003", labels), data):
            self.assertTrue(callable(rule))
            self.assertTrue(rule(value))

        data = ["016_B6J_10M_03", "017_B6J_10F_03", "018_B6J_10M_03", "019_B6J_10F_03"]
        for rule, value in zip(PlateLayoutParser().get_validation_label_rules("IGVF_003", labels), data):
            self.assertFalse(rule(value))

    def test_get_validation_label_rules_complex_cells(self):
        labels = ["Tissue2_M_rep3/4", "Tissue1_AB_1"]
        data = ["016_B6J_10F_03", "Foo_F1_26"]

        for rule, value in zip(PlateLayoutParser().get_validation_label_rules("IGVF_003", labels), data):
            self.assertFalse(callable(rule))

    def test_get_validation_label_rules_genotype(self):
        labels = ["B6J", "NODJ", "AJ", "CC003"]
        data = ["016_B6J_10F_20", "066_NODJ_10F_20", "026_AJ_10F_20", "076_CC003_10F_20"]

        for rule, value in zip(PlateLayoutParser().get_validation_label_rules("IGVF_003", labels), data):
            self.assertTrue(callable(rule))
            self.assertTrue(rule(value))

        wrong_data = ["AB_F1_03", "AB_M1_03", "AB_F2_03", "AB_M2_03"]

        for rule, value in zip(PlateLayoutParser().get_validation_label_rules("IGVF_003", labels), wrong_data):
            self.assertTrue(callable(rule))
            self.assertFalse(rule(value))

    def test_get_validation_label_rule_genotype_override(self):
        labels = ["NZOJ"]
        data = ["092_CASTJ_10F_03"]

        rules = list(PlateLayoutParser().get_validation_label_rules("IGVF_003", labels))
        self.assertTrue(rules[0](data[0]))

    def test_validate_strain_092_CASTJ_10F_03(self):
        override = {"092_CASTJ_10F_03": "CASTJ"}
        rule = functools.partial(PlateLayoutParser._validate_strain, expected_strain="NZOJ", overrides=override)

        tissue_name = list(override.keys())[0]
        self.assertTrue(rule(tissue_name))

    def test_get_well_contents_from_igvf_003(self):
        layouts = read_layout(igvf_003_csv)

        well_contents = PlateLayoutParser().get_well_contents_from_block("IGVF_003", layouts, igvf_003_row_start)

        self.assertEqual(len(well_contents), 96)
        self.assertEqual(well_contents["A", "1"], [WellContent("B6J", "016_B6J_10F_03")])
        self.assertEqual(well_contents["A", "8"], [WellContent("B6J", "025_B6J_10M_03")])
        self.assertEqual(well_contents["A", "9"], [WellContent("B6J", "016_B6J_10F_06"), WellContent("NODJ", "066_NODJ_10F_06")])
        self.assertEqual(well_contents["H", "1"], [WellContent("CASTJ", "092_CASTJ_10F_03")])
        self.assertEqual(well_contents["H", "8"], [WellContent("NZOJ", "053_NZOJ_10M_03")])
        self.assertEqual(well_contents["H", "12"], [WellContent("WSBJ", "063_WSBJ_10M_06"), WellContent("NZOJ", "053_NZOJ_10M_06")])

    def test_get_well_contents_from_igvf_b01(self):
        layouts = read_layout(igvf_b01_csv)

        well_contents = PlateLayoutParser().get_well_contents_from_block("IGVF_b01", layouts, igvf_b01_row_start)

        self.assertEqual(len(well_contents), 48)
        self.assertEqual(well_contents["A", "1"], [WellContent("B6J", "118_B6J_10F_21")])
        self.assertEqual(well_contents["A", "12"], [WellContent("B6J", "117_B6J_10M_21")])
        self.assertEqual(well_contents["D", "1"], [WellContent("CASTJ", "108_CASTJ_10F_21")])
        self.assertEqual(well_contents["D", "12"], [WellContent("CASTJ", "107_CASTJ_10M_21")])

    def test_get_well_contents_from_igvf_12(self):
        layouts = read_layout(igvf_012_csv)

        well_contents = PlateLayoutParser().get_well_contents_from_block("IGVF_012", layouts, igvf_012_row_start)

        self.assertEqual(len(well_contents), 48)
        self.assertEqual(well_contents["A", "1"], [WellContent("B6J", "016_B6J_10F_08")])
        self.assertEqual(well_contents["A", "12"], [WellContent("AJ", "029_AJ_10M_06")])
        self.assertEqual(well_contents["D", "1"], [WellContent("WSBJ", "057_WSBJ_10M_06")])
        self.assertEqual(well_contents["D", "12"], [WellContent("WSBJ", "062_WSBJ_10F_06")])

    def test_get_merged_well_definition_start_003(self):
        layouts = read_layout(igvf_003_csv)

        parser = PlateLayoutParser()
        starts = list(parser.get_merged_well_definition_start(layouts, igvf_003_row_start))

        expected = [13, 18, 23, 28]
        self.assertEqual(starts, expected)

    def test_get_merged_well_definition_start_b01(self):
        csvs = StringIO(igvf_b01_csv)
        layouts = pandas.read_csv(csvs, header=None)

        parser = PlateLayoutParser()
        starts = list(parser.get_merged_well_definition_start(layouts, igvf_b01_row_start))
        self.assertEqual(starts, [])

    def test_get_merged_well_ids_003(self):
        layouts = read_layout(igvf_003_csv)

        parser = PlateLayoutParser()
        merged_well_ids = list(parser.get_merged_well_ids(layouts, igvf_003_row_start))

        expected = [
            "AB_F1_06", "AB_M1_06", "AB_F2_06", "AB_M2_06",
            "AB_F3_06", "AB_M3_06", "AB_F4_06", "AB_M4_06",
            "CD_F1_06", "CD_M1_06", "CD_F2_06", "CD_M2_06",
            "CD_F3_06", "CD_M3_06", "CD_F4_06", "CD_M4_06",
            "EF_F1_06", "EF_M1_06", "EF_F2_06", "EF_M2_06",
            "EF_F3_06", "EF_M3_06", "EF_F4_06", "EF_M4_06",
            "GH_F1_06", "GH_M1_06", "GH_F2_06", "GH_M2_06",
            "GH_F3_06", "GH_M3_06", "GH_F4_06", "GH_M4_06",
        ]
        self.assertEqual(merged_well_ids, expected)

    def test_parse_plate(self):
        layouts = read_layout(
            "".join([igvf_003_csv, igvf_005_csv, igvf_b01_csv, igvf_012_csv, igvf_0xx_1_csv, igvf_015_csv]))

        parser = PlateLayoutParser()

        # will only test subset of expected well contents... there's a lot of them.
        expected = [
            ("IGVF_003", {
                ("A", "1"): [WellContent("B6J", "016_B6J_10F_03")],
                ("A", "8"): [WellContent("B6J", "025_B6J_10M_03")],
                ("A", "9"): [WellContent("B6J", "016_B6J_10F_06"), WellContent("NODJ", "066_NODJ_10F_06")],
                ("H", "1"): [WellContent("CASTJ", "092_CASTJ_10F_03")],
                ("H", "8"): [WellContent("NZOJ", "053_NZOJ_10M_03")],
                ("H", "12"): [WellContent("WSBJ", "063_WSBJ_10M_06"), WellContent("NZOJ", "053_NZOJ_10M_06")],
            }),
            ("IGVF_005", {
                ("A", "1"): [WellContent("B6J", "016_B6J_10F_05")],
                ("A", "8"): [WellContent("B6J", "025_B6J_10M_05")],
                ("A", "9"): [WellContent("B6J", "016_B6J_10F_01"), WellContent("NODJ", "066_NODJ_10F_01")],
                ("H", "1"): [WellContent("NZOJ", "046_NZOJ_10F_05")],
                ("H", "8"): [WellContent("NZOJ", "053_NZOJ_10M_05")],
                ("H", "12"): [WellContent("WSBJ", "063_WSBJ_10M_01"), WellContent("NZOJ", "053_NZOJ_10M_01")],
            }),
            ("IGVF_B01", {
                ("A", "1"): [WellContent("B6J", "118_B6J_10F_21")],
                ("A", "12"): [WellContent("B6J", "117_B6J_10M_21")],
                ("D", "1"): [WellContent("CASTJ", "108_CASTJ_10F_21")],
                ("D", "12"): [WellContent("CASTJ", "107_CASTJ_10M_21")],
            }),
            ("IGVF_012", {
                ("A", "1"): [WellContent("B6J", "016_B6J_10F_08")],
                ("A", "8"): [WellContent("B6J", "022_B6J_10F_16")],
                ("D", "1"): [WellContent("WSBJ", "057_WSBJ_10M_06")],
                ("D", "12"): [WellContent("WSBJ", "062_WSBJ_10F_06")],
            }),
            ("IGVF_015", {
                ("A", "1"): [WellContent("TREM2", "239_TREM2_10F_01")],
                ("A", "12"): [WellContent("TREM2", "239_TREM2_10F_08")],
                ("H", "1"): [WellContent("TREM2", "248_TREM2_10M_01")],
                ("H", "12"): [WellContent("TREM2", "248_TREM2_10M_08")],
            }),
        ]
        for expected_plate, actual_plate in zip(expected, parser.parse_plates(layouts)):
            expected_name, expected_wells = expected_plate
            actual_name, actual_wells = actual_plate

            self.assertEqual(expected_name, actual_name)

            for key in expected_wells:
                self.assertEqual(expected_wells[key], actual_wells[key])
