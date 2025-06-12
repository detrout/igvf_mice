from django.test import TestCase
import pandas
from ..io.read_fastq_metadata import (
    is_subpool_exome,
    fastq_metadata_row_to_subpool_name,
    get_subpool_from_fastq_row,
    check_fastq_barcode_is_equal,
)


class TestReadFastqMetadata(TestCase):
    fixtures = [
        "source",
        "mousestrain",
        "ontologyterm",
        "librarybarcode",
        "library_construction_reagent",
        "test_protocols",
        "test_splitseqplates",
        "test_subpools",
    ]

    def test_is_subpool_exome(self):
        self.assertEqual(is_subpool_exome("003_13A"), True)
        self.assertEqual(is_subpool_exome("003_67A"), False)
        self.assertEqual(is_subpool_exome("016_13A"), True)

    def test_fastq_metadata_row_to_subpool_name_nanopore(self):
        fastqs = pandas.DataFrame({
            "experiment": ["igvf_003"],
            "run_name": ["nanopore_p2/igvf003_13A-gc_lig-ss_p2_2"],
            "plate_id": ["003"],
            "filename": ["igvf_003/nanopore_p2/igvf003_13A-gc_lig-ss_p2_2/igvf003_13A-gc_lig-ss_p2_2_3s.fastq.gz"],
            "file_type": ["fastq"],
            "compression": ["gz"],
            "lane": [None],
            "read": [None],
            "fragment": [None],
            "protocol": ["E"],
            "subpool_name": ["13A"],
            "sequencer": ["promethion"],
            "sequencer_run": ["edaf3b6838fc248dd1b06c4a1b7df46a447615bf"],
            "flowcell_id": ["PAO03105"],
            "barcode_id": [None],
            "barcode": [None],
            "read_length": [None],
            "size": [4461245769],
            "ctime": ["2023-06-13"],
            "exists": [False],
            "md5sum": ["7e9832c3a33438b20b954ef8dbc1c300"],
        })

        self.assertEqual(
            fastq_metadata_row_to_subpool_name(fastqs.iloc[0]),
            "003_13A"
        )

    # Adding tests for 004_13A/004_67A since they have colliding illumina barcodes
    def test_fastq_metadata_row_to_subpool_004_13A(self):
        fastqs = pandas.DataFrame({
            "experiment": ["igvf_004"],
            "run_name": ["nextseq"],
            "plate_id": ["004"],
            "filename": ["igvf_004/nextseq/004_13A_R1.fastq.gz"],
            "file_type": ["fastq"],
            "compression": ["gz"],
            "lane": [None],
            "read": ["R1"],
            "fragment": [None],
            "protocol": [None],
            "subpool_name": ["13A"],
            "sequencer": ["VH0582"],
            "sequencer_run": ["1"],
            "flowcell_id": ["AAATJF3HV"],
            "barcode_id": ["2"],
            "barcode": ["ACTTGA"],
            "read_length": ["140"],
            "size": [None],
            "ctime": ["2023-06-13"],
            "exists": [True],
            "md5sum": ["e3032740ef0d720818f582027f8e43ab"],
        })

        self.assertEqual(
            fastq_metadata_row_to_subpool_name(fastqs.iloc[0]),
            "004_13A"
        )

    def test_fastq_metadata_row_to_subpool_004_67A(self):
        fastqs = pandas.DataFrame({
            "experiment": ["igvf_004"],
            "run_name": ["nextseq"],
            "plate_id": ["004"],
            "filename": ["igvf_004/nextseq/004_67A_R1.fastq.gz"],
            "file_type": ["fastq"],
            "compression": ["gz"],
            "lane": [None],
            "read": ["R1"],
            "fragment": [None],
            "protocol": [None],
            "subpool_name": ["67A"],
            "sequencer": ["VH0582"],
            "sequencer_run": ["1"],
            "flowcell_id": ["AAATJF3HV"],
            "barcode_id": ["2"],
            "barcode": ["ACTTGA"],
            "read_length": ["140"],
            "size": [None],
            "ctime": ["2023-06-13"],
            "exists": [True],
            "md5sum": ["b37eb5352cdc612eaa64099ff61fb255"],
        })

        self.assertEqual(
            fastq_metadata_row_to_subpool_name(fastqs.iloc[0]),
            "004_67A"
        )

    def test_fastq_metadata_row_to_subpool_004_67A_nova(self):
        fastqs = pandas.DataFrame({
            "experiment": ["igvf_004"],
            "run_name": ["nova2"],
            "plate_id": ["004"],
            "filename": ["igvf_004/nova2/Sublibrary_2_S1_L004_R2_001.fastq.gz"],
            "file_type": ["fastq"],
            "compression": ["gz"],
            "lane": ["L004"],
            "read": ["R2"],
            "fragment": ["001"],
            "protocol": [None],
            "subpool_name": [None],
            "sequencer": ["A00850"],
            "sequencer_run": ["254"],
            "flowcell_id": ["HTGM5DSX5"],
            "barcode_id": ["2"],
            "barcode": ["ACTTGA"],
            "read_length": ["86"],
            "size": [None],
            "ctime": ["2023-06-13"],
            "exists": [True],
            "md5sum": ["310343ca4eeaee652e4b23b1a4d117cf"],
        })

        self.assertEqual(
            fastq_metadata_row_to_subpool_name(fastqs.iloc[0]),
            "004_67A"
        )

    def test_fastq_metadata_row_to_subpool_name_nova_008b(self):
        fastqs = pandas.DataFrame({
            "experiment": ["igvf_008b"],
            "run_name": ["nova1"],
            "plate_id": ["008b"],
            "filename": ['igvf_008b/nova1/Sublibrary_2_S1_L003_R1_001.fastq.gz'],
            "file_type": ["fastq"],
            "compression": ["gz"],
            "lane": ["L003"],
            "read": ["R1"],
            "fragment": ["1"],
            "protocol": [None],
            "subpool_name": [None],
            "sequencer": ["A00850"],
            "sequencer_run": ["278"],
            "flowcell_id": ["H5VF5DSX7"],
            "barcode_id": ["2"],
            "barcode": ["ACTTGA"],
            "read_length": ["140"],
            "size": [None],
            "ctime": ["2024-01-16 15:33:25.692465"],
            "exists": [True],
            "md5sum": ["c0f9661d21c2b0c3f73ff5b46c75888e"],
        })

        self.assertEqual(
            fastq_metadata_row_to_subpool_name(fastqs.iloc[0]), "008B_13A")

    def test_check_fastq_barcode_is_equal(self):
        self.assertTrue(check_fastq_barcode_is_equal("ACTTGA", None, "ACTTGA"))
        self.assertFalse(check_fastq_barcode_is_equal("ACTTGA", None, "CTTGTA"))
        self.assertTrue(
            check_fastq_barcode_is_equal("GTGAAACT", "AGTCTGTA", "GTGAAACT+TACAGACT")
        )
        self.assertFalse(
            check_fastq_barcode_is_equal("GTGAAACT", "AGTCTGTA", "ACTTGATC+TTTGGGTG")
        )
        self.assertFalse(check_fastq_barcode_is_equal("GTGAAACT", "AGTCTGTA", "CTTGTA"))
