import datetime
from io import StringIO
import pandas
from django.test import TestCase

from .. import models
from ..io.read_sheet import (
    import_accessions,
    import_mice,
    import_protocols,
    import_tissues,
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

    mice = pandas.DataFrame(
        {
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
    finish_aug28 = datetime.datetime(2023, 8, 28, 11, 33)

    tissues = pandas.DataFrame({
        "Mouse_Tissue ID": [
            "016_B6J_10F_01",
            "016_B6J_10F_02",
            "017_B6J_10M_01",
            "017_B6J_10M_02",
            "144_B6129S1F1J_10F_01",
            "144_B6129S1F1J_10F_03"
        ],
        "Mouse name": [
            "016_B6J_10F",
            "016_B6J_10F",
            "017_B6J_10M",
            "017_B6J_10M",
            "144_B6129S1F1J_10F",
            "144_B6129S1F1J_10F"
        ],
        "tissue": [
            "Hypothalamus/Pituitary",
            "Cerebellum",
            "Hypothalamus/Pituitary",
            "Cerebellum",
            "Hypothalamus/Pituitary",
            "Cortex/Hippocampus left",
        ],
        "tissue_id": [
            ["UBERON:0001898","UBERON:0000007"],
            ["UBERON:0002037"],
            ["UBERON:0001898","UBERON:0000007"],
            ["UBERON:0002037"],
            ["UBERON:0001898","UBERON:0000007"],
            ["NTR:0000646","NTR:0000750"],
        ],
        "Genotype": ["B6J", "B6J", "B6J", "B6J", "B6129S1F1J", "B6129S1F1J"],
        "Tube label": ["016-01", "016-02", "017-01", "017-02", "144-01", "144-02"],
        "tube weight (g)": [1.046, 1.046, 1.041, 1.041, 1.043, 1.037],
        "tube+tissue weight (g)": [1.118, None, 1.126, None, 1.132, 1.181],
        "Dissection start": [
            start_016,
            start_016,
            start_016,
            start_016,
            start_aug28,
            start_aug28
        ],
        "Dissection end": [None, None, None, None, finish_aug28, finish_aug28],
        "Body weight (g)": [21.1, 21.1, 26.3, 26.3, 19.9, 19.9],
        "Dissector": ["AA", "AA", "BB", None, "CC", "CC"],
        "comment": ["comment", None, None, "", "comment", None]
    })
    return tissues



def get_test_ont_sequencing_sheet():
    ont_csv = """Experiment,Tissue,Sample ID,cDNA Build Date,[cDNA] (ng/uL),Average Length (bp),bp to calculate for loading,Tube ID,Library Build Date,Library Molarity (fmol),cDNA Input (ng),cDNA Volume (uL),H2O Vol. to make up 47uL (uL),[Library] (ng/uL),Loading Molarity (fmol),Loading Input (ng),Total Loading Vol. (uL),Sample Loading Vol. (uL),H2O Vol. to add (uL),Sequencing Date,Kit,ONT Instrument,Flow Cell Type,Flow Cell Chemistry,Flow Cell ID,Position,# of Pores Dectected,Run Length,Raw Reads (M),Estimated Bases (Gb),Estimated N50 (bp),Run Size (GB),MinKNOW Version,Raw Data Type,Convert to raw data? ,# of uncoverted files,# of unconverted reads,final raw data format,# raw reads,raw data file size,raw data checksum (md5sum),Basecaller,Basecaller Version,Bascalling Mode,Basecalling Config,min Q-score (default 10),Passed bases,Passed Reads,fastq.gz file size,checksum (md5sum) .fastq.gz,Trimmed File,Trimmed Reads,checksum (md5sum) .fastq.gz.1,Notes
IGVF003,Main: Cortex + Hippocampus,igvf003_8A_lig-ss_1,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT001,GF - 12/06/22,200.0,150.0,1.15384615384615,45.8461538461539,2.34,10.0,8.0,12.0,3.41880341880342,8.58119658119658,GF - 12/06/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU11962,X1,1469.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
Founders,Multiplexed: Heart,igvf003_8A_lig-ss_2,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT001,GF - 12/07/22,200.0,150.0,1.15384615384615,45.8461538461539,2.34,10.0,8.0,12.0,3.41880341880342,8.58119658119658,GF - 12/07/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU06485,X2,1017.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_3,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT001,GF - 12/07/22,200.0,150.0,1.15384615384615,45.8461538461539,2.34,10.0,8.0,12.0,3.41880341880342,8.58119658119658,GF - 12/07/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU06411,X3,1149.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_4,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT001,GF - 12/07/22,200.0,150.0,1.15384615384615,45.8461538461539,2.34,10.0,8.0,12.0,3.41880341880342,8.58119658119658,GF - 12/07/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU11624,X4,313.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_5,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT002,GF - 12/08/22,200.0,150.0,1.15384615384615,45.8461538461539,3.82,10.0,8.0,12.0,2.09424083769634,9.90575916230367,GF - 12/08/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU05901,X1,1472.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_6,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT002,GF - 12/08/22,200.0,150.0,1.15384615384615,45.8461538461539,3.82,10.0,8.0,12.0,2.09424083769634,9.90575916230367,GF - 12/08/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU06482,X4,1444.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_7,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT002,GF - 12/08/22,200.0,150.0,1.15384615384615,45.8461538461539,3.82,10.0,8.0,12.0,2.09424083769634,9.90575916230367,GF - 12/08/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU06496,X5,1403.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_8,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT002,GF - 12/08/22,200.0,150.0,1.15384615384615,45.8461538461539,3.82,10.0,8.0,12.0,2.09424083769634,9.90575916230367,GF - 12/09/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU06476,X2,1423.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_9,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT002,GF - 12/08/22,200.0,150.0,1.15384615384615,45.8461538461539,3.82,10.0,8.0,12.0,2.09424083769634,9.90575916230367,GF - 12/09/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU11470,X3,1262.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_10,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT003,JS - 12/13/22,200.0,150.0,1.15384615384615,45.8461538461539,6.1,10.0,8.0,12.0,1.31147540983607,10.6885245901639,JS - 12/13/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAV21462,X4,1558.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_8A_lig-ss_11,HL/ER - 12/02/22,130.0,1150.0,1250.0,ONT003,JS - 12/13/22,200.0,150.0,1.15384615384615,45.8461538461539,6.1,10.0,8.0,12.0,1.31147540983607,10.6885245901639,JS - 12/13/22,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAU06484,X5,1399.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_13A-gc_lig-ss_qc_1,GF - 05/18/23,48.2,1144.0,1244.0,ONT018,GF - 05/22/23,200.0,149.0,3.09128630705394,43.9087136929461,2.9,10.0,7.5,12.0,2.58620689655172,9.41379310344828,GF - 06/06/23,SQK-LSK114-XL,MinION,FLO-MIN114,R10.4.1,FAW82381,MIN24672,1080.0,48 hours,15.1,15.19,1130,280.0,23.04.5,fast5,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvf003_13A-gc_lig-ss_p2_1,GF - 05/18/23,48.2,1144.0,1244.0,ONT018,GF - 05/22/23,200.0,149.0,3.09128630705394,43.9087136929461,2.9,20.0,15.0,32.0,5.17241379310345,26.8275862068966,GF - 06/08/23,SQK-LSK114-XL,P2 Solo,FLO-PRO114M,R10.4.1,PAO03808,P2S-00617-B,6809.0,93 hours,92.85,95.44,1180,1540.0,22.07.9,fast5,1.0,2.0,8000.0,pod5,92839059.0,933G,3d76177a266b86aa588e49c4109c08cd,dorado,0.5.0,Super Accurate,dna_r10.4.1_e8.2_400bps_sup@v4.1.0,10.0,,82558734.0,72G,1034404a43366a41b6840ad95b6ac439,,,,
,,igvf003_13A-gc_lig-ss_p2_2,GF - 05/18/23,48.2,1144.0,1244.0,ONT018,GF - 05/22/23,200.0,149.0,3.09128630705394,43.9087136929461,2.9,20.0,15.0,32.0,5.17241379310345,26.8275862068966,GF - 06/13/23,SQK-LSK114-XL,P2 Solo,FLO-PRO114M,R10.4.1,PAO03105,P2S-00617-A,7562.0,,,,,,,fast5,1.0,1.0,4000.0,pod5,74638001.0,780G,3b287a1aa3d119946de71b319c3ad70d,dorado,0.5.0,Super Accurate,dna_r10.4.1_e8.2_400bps_sup@v4.1.0,10.0,,65732603.0,57G,54b785ed64da5b40bef87077858c3819,,,,
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
IGVFB01,Main: Left Cortex,igvfB01_13G-gc_lig-ss_1,PM 04/04/23,43.2,1473.0,1573.0,ONT012,GF - 04/07/23,200.0,192.0,4.44444444444444,42.5555555555556,3.82,12.0,12.0,12.0,3.1413612565445,8.8586387434555,GF - 04/07/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW43925,X1,1285.0,,,,1020,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
Bridge,,igvfB01_13G-gc_lig-ss_2,PM 04/04/23,43.2,1473.0,1573.0,ONT012,GF - 04/07/23,200.0,192.0,4.44444444444444,42.5555555555556,3.82,12.0,12.0,12.0,3.1413612565445,8.8586387434555,GF - 04/13/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39250,X1,1398.0,,,,976,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_3,PM 04/04/23,43.2,1473.0,1573.0,ONT012,GF - 04/07/23,200.0,192.0,4.44444444444444,42.5555555555556,3.82,12.0,12.0,12.0,3.1413612565445,8.8586387434555,GF - 04/15/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39152,X1,1360.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_4,PM 04/04/23,43.2,1473.0,1573.0,ONT014,GF - 04/17/23,200.0,192.0,4.44444444444444,42.5555555555556,3.06,12.0,12.0,12.0,3.92156862745098,8.07843137254902,GF - 04/17/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW41308,X5,1463.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_5,PM 04/04/23,43.2,1473.0,1573.0,ONT014,GF - 04/17/23,200.0,192.0,4.44444444444444,42.5555555555556,3.06,12.0,12.0,12.0,3.92156862745098,8.07843137254902,GF - 04/17/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW43869,X1,1135.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_6,PM 04/04/23,43.2,1473.0,1573.0,ONT014,GF - 04/17/23,200.0,192.0,4.44444444444444,42.5555555555556,3.06,12.0,12.0,12.0,3.92156862745098,8.07843137254902,GF - 04/17/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39263,X3,1128.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_7,PM 04/04/23,43.2,1473.0,1573.0,ONT016,GF - 04/19/23,200.0,192.0,4.44444444444444,42.5555555555556,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,GF - 04/19/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39182,X4,1155.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_8,PM 04/04/23,43.2,1473.0,1573.0,ONT016,GF - 04/19/23,200.0,192.0,4.44444444444444,42.5555555555556,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,PM - 04/24/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW43761,X1,,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_9,PM 04/04/23,43.2,1473.0,1573.0,ONT016,GF - 04/19/23,200.0,192.0,4.44444444444444,42.5555555555556,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,PM - 04/24/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39890,X2,,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_10,PM 04/04/23,43.2,1473.0,1573.0,ONT016,GF - 04/19/23,200.0,192.0,4.44444444444444,42.5555555555556,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,PM - 04/24/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW43852,X3,,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13G-gc_lig-ss_11,PM 04/04/23,35.5,1091.0,1191.0,ONT021,GF - 05/22/23,200.0,142.0,4.0,43.0,3.38,20.0,14.5,32.0,4.28994082840237,27.7100591715976,GF - 05/19/23,SQK-LSK114,P2 Solo,FLO-PRO114M,R10.4.1,PAO05399,P2S-00617-A,,116 hours,119.09,107.59,,,,fast5,1.0,3.0,12000.0,pod5,119068058.0,1.1 T,7c8c8a63a52f1dacf0e93cac94ac5c0f,dorado,0.5.0,Super Accurate,dna_r10.4.1_e8.2_400bps_sup@v4.1.0,10.0,,105591654.0,78 G,7425dfe4ef2e843d7ea29d648f72a2cd,,,,
,,igvfB01_13H_lig-ss_1,PM 04/04/23,41.3,1447.0,1547.0,ONT013,GF - 04/07/23,200.0,188.0,4.55205811138015,42.4479418886199,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,GF - 04/07/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW41173,X2,1417.0,,,,1070,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_2,PM 04/04/23,41.3,1447.0,1547.0,ONT013,GF - 04/07/23,200.0,188.0,4.55205811138015,42.4479418886199,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,GF - 04/13/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39190,X2,1174.0,,,,1040,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_3,PM 04/04/23,41.3,1447.0,1547.0,ONT013,GF - 04/07/23,200.0,188.0,4.55205811138015,42.4479418886199,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,GF - 04/15/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW54715,X2,1340.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_4,PM 04/04/23,41.3,1447.0,1547.0,ONT013,GF - 04/07/23,200.0,188.0,4.55205811138015,42.4479418886199,4.48,12.0,12.0,12.0,2.67857142857143,9.32142857142857,GF - 04/15/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39215,X3,1216.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_5,PM 04/04/23,41.3,1447.0,1547.0,ONT015,GF - 04/17/23,200.0,188.0,4.55205811138015,42.4479418886199,4.86,12.0,12.0,12.0,2.46913580246914,9.53086419753086,GF - 04/17/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39354,X4,1341.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_6,PM 04/04/23,41.3,1447.0,1547.0,ONT015,GF - 04/17/23,200.0,188.0,4.55205811138015,42.4479418886199,4.86,12.0,12.0,12.0,2.46913580246914,9.53086419753086,GF - 04/17/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW41239,X5,1308.0,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_7,PM 04/04/23,41.3,1447.0,1547.0,ONT015,GF - 04/17/23,200.0,188.0,4.55205811138015,42.4479418886199,4.86,12.0,12.0,12.0,2.46913580246914,9.53086419753086,GF - 04/17/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW43926,MIN24338,,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_8,PM 04/04/23,41.3,1447.0,1547.0,ONT015,GF - 04/17/23,200.0,188.0,4.55205811138015,42.4479418886199,4.86,12.0,12.0,12.0,2.46913580246914,9.53086419753086,PM - 04/24/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39324,X4,,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_9,PM 04/04/23,41.3,1447.0,1547.0,ONT015,GF - 04/17/23,200.0,188.0,4.55205811138015,42.4479418886199,4.86,12.0,12.0,12.0,2.46913580246914,9.53086419753086,PM - 04/24/23,SQK-LSK114woma,GridION,FLO-MIN114,R10.4.1,FAW39355,X5,,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,igvfB01_13H_lig-ss_10,PM 04/04/23,41.3,1447.0,1547.0,ONT017,GF - 04/19/23,200.0,188.0,4.55205811138015,42.4479418886199,5.8,12.0,12.0,12.0,2.06896551724138,9.93103448275862,PM - 04/24/23,SQK-LSK114,GridION,FLO-MIN114,R10.4.1,FAW39859,MIN24338,,,,,,,,,0.0,,,,,,,Guppy,,Super Accurate,,,,,,,,,,
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
"""
    return pandas.read_csv(StringIO(ont_csv))


class TestReadSheet(TestCase):
    fixtures = ["source", "mousestrain", "ontologyterm"]

    def test_import_protocol(self):
        self.assertEqual(models.ProtocolLink.objects.count(), 0)

        protocols = get_test_protocols_sheet()

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
            self.assertEqual(row.timepoint, mice.iloc[mouse_i]["Timepoint"])
            self.assertEqual(row.timepoint_unit, mice.iloc[mouse_i]["Timepoint unit"])
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
