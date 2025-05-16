import datetime
from io import StringIO
import pandas
from django.test import TestCase

from .. import models
from ..io.load_sheet import (
    load_accessions,
    load_mice,
    load_protocols,
    load_tissues,
    load_splitseq_samples,
    load_splitseq_ont_samples,
)
from ..io.converters import (
    str_or_none,
    uci_tz_or_none,
)


def get_test_protocols_sheet():
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
    return protocols


def get_test_mice_sheet():
    dob_aug16 = datetime.datetime(2022, 8, 16)#, tzinfo=los_angeles)
    dob_jun20 = datetime.datetime(2023, 6, 20)#, tzinfo=los_angeles)

    start_016 = datetime.datetime(2022, 10, 27, 9, 1)#, tzinfo=los_angeles)
    start_017 = datetime.datetime(2022, 10, 27, 11, 44)#, tzinfo=los_angeles)
    start_144 = datetime.datetime(2023, 8, 28, 11, 15)#, tzinfo=los_angeles)
    finish_144 = datetime.datetime(2023, 8, 28, 11, 33)#, tzinfo=los_angeles)

    mice = pandas.DataFrame({
            "Mouse Name": ["016_B6J_10F", "017_B6J_10M", "144_B6129S1F1J_10F"],
            "Dissection ID": ["16", "17", "144"],
            "Strain code": ["B6J", "B6J", "B6129S1F1J"],
            "Sex": ["M", "F", "F"],
            "Weight (g)": [21.1, 26.3, 19.9],
            "DOB": [dob_aug16, dob_aug16, dob_jun20],
            "Dissection start time": [start_016, start_017, start_144],
            "Dissection finish time": [None, None, finish_144],
            "Timepoint": [10] * 3,
            "Timepoint unit": ["weeks"] * 3,
            "estrus_cycle": ["D", "NA", "DP"],
            "Operator": ["T1", "T2", "T1"],
            "Comments": ["", "", ""],
            "Housing number": [14669, 14670, None],
        }
    )

    return mice


def get_test_tissue_sheet():
    start_016 = datetime.datetime(2022, 10, 27, 9, 1)#, tzinfo=los_angeles)
    start_aug28 = datetime.datetime(2023, 8, 28, 11, 15)
    start_268 = datetime.datetime(2024, 2, 21, 9, 38)
    finish_aug28 = datetime.datetime(2023, 8, 28, 11, 33)
    finish_268 = datetime.datetime(2024, 2, 21, 9, 57)

    tissues = pandas.DataFrame({
        "Mouse_Tissue ID": [
            "016_B6J_10F_01",
            "016_B6J_10F_02",
            "017_B6J_10M_01",
            "017_B6J_10M_02",
            "144_B6129S1F1J_10F_01",
            "144_B6129S1F1J_10F_03",
            "268_CC001_10F_01",
        ],
        "Mouse name": [
            "016_B6J_10F",
            "016_B6J_10F",
            "017_B6J_10M",
            "017_B6J_10M",
            "144_B6129S1F1J_10F",
            "144_B6129S1F1J_10F",
            "268_CC001_10F",
        ],
        "tissue": [
            "Hypothalamus/Pituitary",
            "Cerebellum",
            "Hypothalamus/Pituitary",
            "Cerebellum",
            "Hypothalamus/Pituitary",
            "Cortex/Hippocampus left",
            "Diencephelon/Pituitary",
        ],
        "tissue_id": [
            ["UBERON:0001898","UBERON:0000007"],
            ["UBERON:0002037"],
            ["UBERON:0001898","UBERON:0000007"],
            ["UBERON:0002037"],
            ["UBERON:0001898","UBERON:0000007"],
            ["NTR:0000646","NTR:0000750"],
            ["UBERON:0001894", "UBERON:0000007"],
        ],
        "Genotype": ["B6J", "B6J", "B6J", "B6J", "B6129S1F1J", "B6129S1F1J", "CC001"],
        "Tube label": ["016-01", "016-02", "017-01", "017-02", "144-01", "144-02", "268-01"],
        "tube weight (g)": [1.046, 1.046, 1.041, 1.041, 1.043, 1.037, 1.031],
        "tube+tissue weight (g)": [1.118, None, 1.126, None, 1.132, 1.181, 1.103],
        "Dissection start": [
            start_016,
            start_016,
            start_016,
            start_016,
            start_aug28,
            start_aug28,
            start_268,
        ],
        "Dissection end": [None, None, None, None, finish_aug28, finish_aug28, finish_268],
        "Body weight (g)": [21.1, 21.1, 26.3, 26.3, 19.9, 19.9, 18.7],
        "Dissector": ["AA", "AA", "BB", None, "CC", "CC", "HH"],
        "comment": ["comment", None, None, "", "comment", None, None]
    })
    return tissues


def get_test_splitseq_samples():
    return pandas.DataFrame({
        'tissue_id': ['016_B6J_10F_01',
                      '144_B6129S1F1J_10F_03',
                      '144_B6129S1F1J_10F_01'],
        'tube_label': ['016_01', '144_03', '144_01'],
        'fixation_name': ['IGVF_FIX_003',
                          'IGVF_FIX_013',
                          'IGVF_FIX_012'],
        'fixation_date': ['2023-01-09',
                          '2023-09-15',
                          '2024-03-27'],
        'pooled_from': [['016_B6J_10F_01'],
                        ['144_B6129S1F1J_10F_03'],
                        ['144_B6129S1F1J_10F_01']],
        'weight': [72.0, 144.0, 89.0],
        'isolation_technician': [None, 'PM', 'GF'],
        'fixation_technician': ['PM', 'PM', 'GF'],
        'fixed_count_technician': ['GF', 'PM', 'GF'],
        'volume_ul': [3000.0, 3000.0, 3000.0],
        'before_count1': [None, 68.0, 82.0],
        'before_count2': [None, 62.0, 95.0],
        'before_df1': [None, 11.0, 6.0],
        'before_df2': [None, None, None],
        'nuclei_per_ul_before_fixation': [2920.0, None, None],
        'starting_nuclei': [8.76, 21.45, 15.93],
        'nuclei_into_fixation': [3.504, 5.3625, 3.999999999735],
        'fixed_nuclei': [1.9305, 2.2605, 3.39625],
        'parse_input_ul': [1200.0, 750.0, 753.2956684999999],
        'share_input_ul': [342.465753424658,
                           139.86013986014,
                           188.323917137476],
        'after_count1': [57.0, 73.0, 117.0],
        'after_count2': [60.0, 64.0, 130.0],
        'after_df1': [None, 11.0, 11.0],
        'after_df2': [None, None, None],
        'nuclei_per_ul_after_fixation': [None, None, None],
        'aliquots_made': [2.0, 2.0, 2.0],
        'aliquot_volume_ul': [150.0, 150.0, 125.0],
        'comments': [None,
                     None,
                     'Bits left after dissociation; was mushed into the filter using the tip'],
        'sheet_name': ['Founder Samples into experiment',
                       'F1 Samples into experiment',
                       'F1 Samples into experiment'],
        'line_no': [401, 46, 346]})


def get_test_splitseq_ont_sequencing_sheet():
    return pandas.DataFrame({
        'plate': ['IGVF003', 'IGVF004'],
        'subpool': ['003_13A', '004_8A'],
        'name': ['ONT018', 'ONT004'],
        'sample_id': ['igvf003_13A-gc_lig-ss_qc_1', 'igvf004_8A_lig-ss_1'],
        'cdna_build_date': ['2023-05-18', '2022-12-15'],
        'cdna_volume_ul': [3.091286307, 1.870967742],
        'cdna_ng_per_ul': [48.2, 77.5],
        'average_length': [1144.0, 1113.0],
        'technician': ['GF,JS', 'GF'],
        'passed_qc': [True, True],
        'library_build_date': ['2023-05-22', '2023-01-03'],
        'library_volume_ul': [15.0, 15.0],
        'library_input_ng_per_ul': [2.9, 5.9],
        'sequencing_run_date': ['2023-06-06', '2023-01-03'],
        'sequencing_run_platform': ['minion', 'gridion'],
        'flowcell_kit': ['SQK-LSK114-XL', 'SQK-LSK114'],
        'flowcell_type': ['FLO-MIN114', 'FLO-MIN114'],
        'flowcell_id': ['FAW82381', 'FAV32642'],
        'sequencing_software': ['Guppy', 'Guppy'],
        'comments': [None, None],
    })


class TestReadSheet(TestCase):
    fixtures = ["source", "mousestrain", "ontologyterm", "platform"]

    def test_load_protocol(self):
        self.assertEqual(models.ProtocolLink.objects.count(), 0)

        protocols = get_test_protocols_sheet()

        first = protocols[protocols["Protocol"] == "splitseq_100k"]
        self.assertEqual(first.shape[0], 1)

        load_protocols(first)
        self.assertEqual(models.ProtocolLink.objects.count(), 1)

        load_protocols(protocols)
        self.assertEqual(models.ProtocolLink.objects.count(), 2)

        for i, row in enumerate(models.ProtocolLink.objects.all()):
            self.assertEqual(row.name, protocols.iloc[i]["Protocol"])
            self.assertEqual(row.version, protocols.iloc[i]["Protocols.io version"])
            self.assertEqual(row.see_also, protocols.iloc[i]["Link"])
            self.assertEqual(row.description, protocols.iloc[i]["Description"])

    def test_load_mice(self):
        self.assertEqual(models.Mouse.objects.count(), 0)

        mice = get_test_mice_sheet()

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
        added = load_mice(first)

        self.assertEqual(models.Mouse.objects.count(), 1)
        self.assertEqual(added, 1)

        record = models.Mouse.objects.get(name="016_B6J_10F")
        self.assertEqual(record.accession.count(), 0)
        load_accessions(submitted["016_B6J_10F"], record)
        self.assertEqual(record.accession.count(), 2)

        added = load_mice(mice, submitted)
        # expected is whatever else wasn't added in the first call
        self.assertEqual(added, mice.shape[0]-1)

        for mouse_i, row in enumerate(models.Mouse.objects.all()):
            dissection_start_time = uci_tz_or_none(mice.iloc[mouse_i]["Dissection start time"])
            dissection_end_time = uci_tz_or_none(mice.iloc[mouse_i]["Dissection finish time"])

            self.assertEqual(row.name, mice.iloc[mouse_i]["Mouse Name"])
            self.assertEqual(row.strain.name, mice.iloc[mouse_i]["Strain code"])
            self.assertEqual(row.sex, mice.iloc[mouse_i]["Sex"])
            self.assertEqual(row.weight_g, mice.iloc[mouse_i]["Weight (g)"])
            self.assertEqual(row.date_of_birth, mice.iloc[mouse_i]["DOB"].date())
            self.assertEqual(row.dissection_start_time, dissection_start_time)
            self.assertEqual(row.dissection_end_time, dissection_end_time)
            self.assertEqual(row.timepoint, mice.iloc[mouse_i]["Timepoint"])
            self.assertEqual(
                row.timepoint_unit, mice.iloc[mouse_i]["Timepoint unit"])
            self.assertEqual(
                row.estrus_cycle, mice.iloc[mouse_i]["estrus_cycle"])
            self.assertEqual(row.operator, mice.iloc[mouse_i]["Operator"])
            self.assertEqual(row.notes, mice.iloc[mouse_i]["Comments"])
            self.assertEqual(
                row.housing_number,
                str_or_none(mice.iloc[mouse_i]["Housing number"])
            )

            submitted_accessions = {x["name"]: x for x in submitted.get(row.name, [])}

            # the order of the accessions is not preserved.
            for accession in row.accession.all():
                expected = submitted_accessions[accession.name]
                self.assertEqual(
                    accession.accession_prefix,
                    expected["accession_prefix"]
                )
                self.assertEqual(accession.name, expected["name"])
                self.assertEqual(str(accession.uuid), expected["uuid"])
                self.assertEqual(accession.see_also, expected["see_also"])

        added = load_mice(mice, submitted)
        self.assertEqual(added, 0)

    def test_load_tissues(self):
        mice = get_test_mice_sheet()
        load_mice(mice)
        self.assertEqual(models.Tissue.objects.count(), 0)

        tissues = get_test_tissue_sheet()

        first = tissues[tissues["Mouse_Tissue ID"] == "016_B6J_10F_01"]
        load_tissues(first)
        self.assertEqual(models.Tissue.objects.count(), 1)

        load_tissues(tissues)
        self.assertEqual(models.Tissue.objects.count(), tissues.shape[0])

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

    def test_load_splitseq_samples(self):
        mice = get_test_mice_sheet()
        load_mice(mice)

        tissues = get_test_tissue_sheet()
        load_tissues(tissues)

        self.assertEqual(models.SampleExtraction.objects.count(), 0)
        self.assertEqual(models.ParseFixedSample.objects.count(), 0)

        samples = get_test_splitseq_samples()
        load_splitseq_samples(samples)

        self.assertEqual(models.SampleExtraction.objects.count(), 3)
        self.assertEqual(models.ParseFixedSample.objects.count(), 3)

    def test_load_splitseq_ont_samples(self):
        mice = get_test_mice_sheet()
        load_mice(mice)

        tissues = get_test_tissue_sheet()
        load_tissues(tissues)

        # Create plates
        igvf003 = models.SplitSeqPlate(
            name="IGVF003",
        )
        igvf003.save()
        subpool_003_13a = models.Subpool.objects.create(
            name="003_13A",
            plate=igvf003,
            nuclei=13000,
            selection_type="EX",
        )
        subpool_003_13a.save()
        igvf004 = models.SplitSeqPlate(
            name="IGVF004",
        )
        igvf004.save()
        subpool_004_8a = models.Subpool.objects.create(
            name="004_8A",
            plate=igvf004,
            nuclei=8000,
            selection_type="NO",
        )
        subpool_004_8a.save()

        ont = get_test_splitseq_ont_sequencing_sheet()
        load_splitseq_ont_samples(ont)
