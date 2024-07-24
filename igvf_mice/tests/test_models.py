from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import (
    NucleicAcidEnum,
    Accession,
    Source,
    LibraryConstructionReagent,
    LibraryBarcode,
    StrainType,
    MouseStrain,
    SexEnum,
    EstrusCycle,
    Mouse,
    OntologyTerm,
    LifeStageEnum,
    TimeUnitsEnum,
    require_3_underscores,
    Tissue,
    SampleExtraction,
    ParseFixedSample,
    NucleicAcidExtraction,
    NanoporeLibrary,
    PlateSizeEnum,
    SplitSeqPlate,
    SplitSeqWell,
    Subpool,
    Platform,
    StrandedEnum,
    SequencingRun,
    RunStatusEnum,
    LibraryInRun,
    SequencingFile,
    MeasurementSet,
    reverse_compliment,
)


class TestReverseCompliment(TestCase):
    def test_reverse_complimentc(self):
        query = "ATGCRYSWKMBVDN"
        expected = "NHBVKMWSRYGCAT"
        self.assertEqual(reverse_compliment(query), expected)
        self.assertEqual(reverse_compliment(query.lower()), expected.lower())


class TestModels(TestCase):
    def setUp(self):
        self.source_fake = Source.objects.create(
            name="fake source",
            homepage="https://example.edu",
            igvf_id="/sources/example",
        )
        self.source_fake.save()
        self.library_construction_reagent_fake = LibraryConstructionReagent.objects.create(
            name="a kit", version="3.14", source=self.source_fake
        )
        self.library_construction_reagent_fake.save()
        self.library_barcode_fake_t = LibraryBarcode(
            reagent=self.library_construction_reagent_fake,
            name="pb123",
            code="1",
            i7_sequence="GTCTAGGT",
            barcode_type="T",
        )
        self.library_barcode_fake_t.save()
        self.library_barcode_fake_r = LibraryBarcode(
            reagent=self.library_construction_reagent_fake,
            name="pb222",
            code="2",
            i7_sequence="AGCTTAAC",
            barcode_type="R",
        )
        self.library_barcode_fake_r.save()
        self.library_barcode_fake_illumina = LibraryBarcode(
            reagent=self.library_construction_reagent_fake,
            name="I7",
            code="I7",
            i7_sequence="TTCATGT",
        )
        self.library_barcode_fake_illumina.save()
        self.library_barcode_fake_dual_illumina = LibraryBarcode(
            reagent=self.library_construction_reagent_fake,
            name="UDI03",
            code="UDI03",
            i7_sequence="GATCAGTC",
            i5_sequence="TTGACTCT",
        )
        self.library_barcode_fake_dual_illumina.save()
        self.mouse_strain_fake = MouseStrain.objects.create(
            name="CASTHUMAN",
            display_name="CASTJ/human glial cells",
            igvf_id="CASTJ/human glial cells (CASTHUMAN)",
            strain_type=StrainType.FOUNDER,
            jax_catalog_number="[redacted]",
            see_also="https://www.wikidata.org/wiki/Q1500726",
            notes="tries to escape",
            source=self.source_fake,
        )
        self.mouse_strain_fake.save()
        self.mouse_male_fake = Mouse.objects.create(
            name="Brain",
            dissection=15,
            strain=self.mouse_strain_fake,
            sex=SexEnum.MALE,
            weight_g=21.3,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            dissection_start_time="1998-11-14T09:00:00-07:00",
            dissection_end_time="1998-11-14T10:00:00-07:00",
            timepoint=10,
            timepoint_unit=TimeUnitsEnum.WEEK,
            life_stage=LifeStageEnum.POST_NATAL,
            # estrus_cycle=None,
            operator="WB",
            notes="very fake mouse",
            housing_number="35689",
        )
        self.mouse_male_fake.save()
        self.mouse_female_fake = Mouse.objects.create(
            name="Dot",
            dissection=16,
            strain=self.mouse_strain_fake,
            sex=SexEnum.FEMALE,
            weight_g=20.1,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            dissection_start_time="1998-11-14T10:00:00-07:00",
            dissection_end_time="1998-11-14T11:00:00-07:00",
            timepoint=10,
            timepoint_unit=TimeUnitsEnum.WEEK,
            life_stage=LifeStageEnum.POST_NATAL,
            estrus_cycle=EstrusCycle.ANESTRUS,
            operator="WB",
            notes="very fake mouse",
            housing_number="982735",
        )
        self.mouse_female_fake.save()
        self.ontology_term_tail = OntologyTerm.objects.create(
            curie="UBERON:0002415",
            name="tail",
            description="An external caudal extension of the body.",
        )
        self.ontology_term_tail.save()
        self.ontology_term_pbmc = OntologyTerm.objects.create(
            curie="CL:2000001",
            name="peripheral blood mononuclear cell",
            description="A leukocyte with a single non-segmented nucleus",
        )
        self.ontology_term_pbmc.save()
        self.tissue_tail = Tissue.objects.create(
            mouse=self.mouse_male_fake,
            name="016_B6J_10M_30",
            description="tail",
            dissection_start_time="2023-08-11T17:07-08:00",
            dissection_end_time="2023-08-11T17:15-08:00",
            tube_label="016-30",
            tube_weight_g=1.23,
            total_weight_g=1.5,
            dissector="WB",
            dissection_notes="levitated for 5 minutes",
        )
        self.tissue_tail.ontology_term.set([self.ontology_term_tail])
        self.tissue_tail.save()

        self.sample_extraction_tail = SampleExtraction(
            name="108_CASTJ_10M_21",
            tube_label="108_21",
            #box_name="stuff",
            date="2023-1-1",
            volume_ul=3000,
            count1=50,
            df1=11,
            count2=60,
            parse_input_ul=660,
            share_input_ul=165,
        )
        self.sample_extraction_tail.save()
        self.sample_extraction_tail.tissue.set([self.tissue_tail])
        self.sample_extraction_tail.save()

        self.fixed_sample_tail = ParseFixedSample(
            name="108_CASTJ_10M_21",
            extraction=self.sample_extraction_tail,
            #tube_label="108_21",
            #box_name="stuff",
            volume_ul=3000,
            count1=48,
            df1=11,
            aliquots_made=2,
            aliquot_volume_ul=150,
        )
        self.fixed_sample_tail.save()
        #self.fixed_sample_tail.tissue.set([self.tissue_tail])
        #self.fixed_sample_tail.save()
        self.plate_fake = SplitSeqPlate(
            name="TEST_002",
            size=PlateSizeEnum.size_96,
        )
        self.plate_fake.save()
        self.well_single = SplitSeqWell(
            plate=self.plate_fake,
            row="A",
            column="1",
        )
        self.well_single.save()
        self.well_single.biosample.set([self.fixed_sample_tail])
        self.well_single.barcode.set(
            [self.library_barcode_fake_r, self.library_barcode_fake_t]
        )
        self.subpool_fake = Subpool.objects.create(
            name="002_13B",
            plate=self.plate_fake,
            nuclei=67000,
            selection_type="NO",
            cdna_pcr_rounds="5 + 7",
            cdna_ng_per_ul=22.0,
            cdna_volume=25,
            bioanalyzer_date="2023-1-1",
            index_pcr_number=11,
            index=2,
            library_ng_per_ul=30.0,
            library_average_bp_length=410,
        )
        self.subpool_fake.save()
        self.subpool_fake.barcode.set([self.library_barcode_fake_illumina])
        self.subpool_fake.save()
        self.platform_novaseq = Platform.objects.create(
            name="novaseq2000",
            igvf_id="/platform-terms/EFO_0010963/",
            display_name="Novaseq 2000",
            family="illumina",
        )
        self.platform_gridion = Platform.objects.create(
            name="gridion",
            igvf_id="/platform-terms/EFO_0008633/",
            display_name="ONT GridION",
            family="nanopore",
        )
        self.sequencing_run_fake = SequencingRun.objects.create(
            name="next02",
            run_date="1991-08-25",
            platform=self.platform_novaseq,
            plate=self.plate_fake,
            stranded=StrandedEnum.REVERSE,
        )
        self.subpool_run = LibraryInRun.objects.create(
            subpool=self.subpool_fake,
            sequencing_run=self.sequencing_run_fake,
            status=RunStatusEnum.PASS,
            # measurement_set=
        )

        # ont sequenced subpools
        self.ont_subpool_extraction = NucleicAcidExtraction.objects.create(
            name="ONT003",
            date="2022-08-12",
            # in ONT sequencing this is 150 / input_ng_per_ul.
            volume_ul=1.1538461538461537,
            # this is column M of ONT sequencing IGVF_Splitseq
            input_ng_per_ul=130,
            passed_qc=True,
        )
        self.ont_subpool_extraction.save()
        self.ont_subpool_extraction.tissue.set([self.tissue_tail])
        self.ont_subpool_extraction.save()

        self.ont_subpool_library = NanoporeLibrary.objects.create(
            name="ONT003",
            nucleic_acid=NucleicAcidEnum.rna,
            technician="Jay",
            build_date="2022-08-12",
            # this is [library] (ng/nl) (O) on ONT sequencing
            ng_per_ul=3.82,
            # this is from sample loading vol (S) on ONT sequencing
            volume_ul=2.0942408377,
        )

        self.ont_subpool_library.save()
        self.ont_subpool_library.nucleic_acid_extraction.set([self.ont_subpool_extraction])
        self.ont_subpool_library.save()

    # Test cases some of which depend on the above preseeded object tree
    def test_accession_with_uuid(self):
        test016_B6J_10F = Accession.objects.create(
            accession_prefix="igvftst",
            name="TSTDO36427294",
            uuid="8bd01581-b4e2-499b-8266-5e1d40634888",
            see_also="https://api.sandbox.igvf.org/rodent-donors/TSTDO36427294/",
        )

        test016_B6J_10F.full_clean()
        self.assertEqual(str(test016_B6J_10F), "igvftst:TSTDO36427294")
        self.assertEqual(test016_B6J_10F.path, "/rodent-donors/TSTDO36427294/")

    def test_accession_no_uuid(self):
        test016_B6J_10F = Accession.objects.create(
            accession_prefix="igvftst",
            name="TSTDO36427294",
            see_also="https://api.sandbox.igvf.org/rodent-donors/TSTDO36427294/",
        )

        test016_B6J_10F.full_clean()
        self.assertEqual(str(test016_B6J_10F), "igvftst:TSTDO36427294")
        self.assertEqual(test016_B6J_10F.path, "/rodent-donors/TSTDO36427294/")

    def test_source(self):
        name = "illumina"
        display_name = "Illumina"
        homepage = "https://www.illumina.com"
        source = Source.objects.create(
            name=name,
            display_name=display_name,
            homepage=homepage,
            igvf_id="/sources/illumina/"
        )

        source.full_clean()
        self.assertEqual(source.name, name)
        self.assertEqual(source.link(), f'<a href="{homepage}">{homepage}</a>')

    def test_library_construction_reagent(self):
        name = "b-kit",
        display_name = "B Kit"
        version = "2.7.1"

        reagent = LibraryConstructionReagent(
            name=name,
            display_name=display_name,
            version=version,
            source=self.source_fake,
        )

        reagent.full_clean()
        self.assertEqual(str(reagent), f"{display_name} v{version}")

    def test_library_barcode(self):
        reagent = self.library_construction_reagent_fake
        name = "library name"
        code = "A123"
        sequence = "GATTACA"
        barcode_type = "R"
        barcode = LibraryBarcode(
            reagent=reagent,
            name=name,
            code=code,
            i7_sequence=sequence,
            barcode_type=barcode_type,
        )

        barcode.full_clean()
        self.assertEqual(barcode.reagent_name, reagent.name)
        self.assertEqual(str(barcode), f"{name} {code} {sequence} {barcode_type}")

    def test_library_barcode_fake_dual_illumina_reverse_compliment(self):
        barcode = self.library_barcode_fake_dual_illumina

        self.assertEqual(barcode.code, "UDI03")
        self.assertEqual(barcode.i7_sequence, "GATCAGTC")
        self.assertEqual(barcode.i5_sequence, "TTGACTCT")
        self.assertEqual(barcode.i5_reverse_compliment, "AGAGTCAA")

    def test_mouse_strain(self):
        strain = MouseStrain(
            name="SG1",
            display_name="Super brain 1",
            igvf_id="Super brain 1 (SG1)",
            strain_type=StrainType.FOUNDER,
            jax_catalog_number="[redacted]",
            see_also="https://www.wikidata.org/wiki/Q1500726",
            notes="suffers from delusions of grandeur",
            source=self.source_fake,
        )

        strain.full_clean()
        self.assertEqual(str(strain), strain.name)

    def test_mouse(self):
        male_mouse = Mouse(
            name="SG2",
            dissection=18,
            strain=self.mouse_strain_fake,
            sex=SexEnum.MALE,
            weight_g=21.3,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            dissection_start_time="1998-11-14T09:00:00-07:00",
            dissection_end_time="1998-11-14T10:00:00-07:00",
            timepoint=10,
            timepoint_unit=TimeUnitsEnum.WEEK,
            life_stage=LifeStageEnum.POST_NATAL,
            # estrus_cycle=None,
            operator="WB",
            notes="very fake mouse",
            housing_number="924387",
        )

        male_mouse.full_clean()
        self.assertIsInstance(male_mouse.date_of_birth, date)
        self.assertEqual(male_mouse.age_days, 1162)
        self.assertEqual(male_mouse.source, self.mouse_strain_fake.source)

        female_mouse = Mouse(
            name="C1",
            dissection=19,
            strain=self.mouse_strain_fake,
            sex=SexEnum.FEMALE,
            weight_g=19.5,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            dissection_start_time="1998-11-14T10:00:00-07:00",
            dissection_end_time="1998-11-14T11:00:00-07:00",
            estrus_cycle=EstrusCycle.ANESTRUS,
            timepoint=10,
            timepoint_unit=TimeUnitsEnum.WEEK,
            life_stage=LifeStageEnum.POST_NATAL,
            operator="DOT",
            notes="very fake mouse",
            housing_number="29384",
        )

        female_mouse.full_clean()
        self.assertIsInstance(female_mouse.date_of_birth, date)
        self.assertEqual(female_mouse.age_days, 1162)
        self.assertEqual(female_mouse.source, self.mouse_strain_fake.source)

    def test_genderqueer_mouse(self):
        genderqueer_mouse = Mouse(
            name="B2",
            dissection=20,
            strain=self.mouse_strain_fake,
            sex=SexEnum.MALE,
            weight_g=21.3,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            dissection_start_time="1998-11-14T11:00:00-07:00",
            dissection_end_time="1998-11-14T12:00:00-07:00",
            estrus_cycle=EstrusCycle.PROESTRUS,
            operator="WB",
            notes="very fake mouse",
            housing_number="15358",
        )

        self.assertRaises(ValidationError, genderqueer_mouse.full_clean)

    def test_ontology_term(self):
        curie = "UBERON:0001385"
        name = "tibialis anterior"
        term = OntologyTerm.objects.create(
            curie=curie,
            name=name,
            description="A muscle that originates in the upper two-thirds of"
                        "the lateral surface of the tibia",
        )

        term.full_clean()
        self.assertEqual(str(term), f"{curie} ({name})")
        href = "https://data.igvf.org/sample-terms/UBERON_0001385"
        self.assertEqual(term.igvf_href, href)
        self.assertEqual(term.link(), f'<a href="{href}">{curie}</a>')

    def test_validate_3_underscores(self):
        self.assertRaises(ValidationError, require_3_underscores, "a_b_c")
        require_3_underscores("a_b_c_d")

    def test_tissue(self):
        tissue = Tissue.objects.create(
            mouse=self.mouse_female_fake,
            name="016_B6J_10F_30",
            description="tail",
            dissection_start_time="2023-08-11T17:07-08:00",
            tube_label="016-30",
            tube_weight_g=1.23,
            total_weight_g=1.5,
            dissector="WB",
            dissection_notes="levitated for 5 minutes",
        )
        tissue.ontology_term.set([self.ontology_term_tail])

        tissue.full_clean()
        self.assertAlmostEqual(tissue.weight_g, 0.27)
        self.assertAlmostEqual(tissue.weight_mg, 270)
        self.assertEqual(tissue.ontology_names, "tail")
        self.assertEqual(str(tissue), f"{tissue.name} {tissue.description}")

        tissue.ontology_term.set([self.ontology_term_tail, self.ontology_term_pbmc])
        tissue.full_clean()
        self.assertEqual(
            tissue.ontology_names, "peripheral blood mononuclear cell, tail"
        )

    def test_mouse_tissue_pbmc(self):
        total_cells = 3.25
        tissue = Tissue.objects.create(
            mouse=self.mouse_female_fake,
            name="016_B6J_10F_020",
            description="PBMC",
            tube_label="016_020",
            volume_ul=400,
            input_total_cells=total_cells,
            dissection_notes="Blood contains black holes",
        )
        tissue.ontology_term.set([self.ontology_term_pbmc])
        tissue.full_clean()
        self.assertEqual(tissue.input_total_cells, total_cells)

    def test_sample_extraction(self):
        name = "107_CASTJ_10F_21"
        extraction = SampleExtraction.objects.create(
            name=name,
            tube_label="107_21",
            date="2023-1-1",
            volume_ul=3000,
            count1=109,
            df1=11,
            count2=92,
            parse_input_ul=400,
            share_input_ul=90,
        )
        extraction.save()
        extraction.tissue.set([self.tissue_tail])
        extraction.save()

        self.assertEqual(extraction.nuclei_per_ul, .011055)
        self.assertEqual(extraction.nuclei_per_ml, 11.055)
        self.assertEqual(extraction.total_nuclei, 33.165)
        self.assertAlmostEqual(extraction.nuclei_into_parse, 4.422)
        self.assertAlmostEqual(extraction.nuclei_into_share, 0.99495)

    def test_fixed_sample(self):
        # Data from IGVF_Splitseq ? Samples into experiment
        name = "107_CASTJ_10F_21"
        fixed_sample = ParseFixedSample.objects.create(
            name=name,
            extraction=self.sample_extraction_tail,
            technician="GF",
            # before fixation volume rsb mL (M) converted to ul.
            volume_ul=300,
            # before fixation count 1 (N)
            count1=82,
            # before fixation DF1 (P)
            df1=11,
            # before fixation count 2 (O)
            count2=60,
            # after fixation # aliquots (AO)
            aliquots_made=2,
            # after fixation uL per aliquot (AP)
            aliquot_volume_ul=150,
        )
        fixed_sample.save()
        self.assertEqual(str(fixed_sample), name)
        self.assertAlmostEqual(fixed_sample.fraction_recovered, 0.5867768595)

    def test_split_seq_plate(self):
        plate = SplitSeqPlate.objects.create(
            name="TEST_001",
            size=PlateSizeEnum.size_96,
            pool_location="missing",
            date_performed="2023-02-28",
        )

        self.assertIsNone(plate.total_nuclei)
        plate.barcoded_cell_counter = 1000
        self.assertIsNone(plate.total_nuclei)
        plate.volume_of_nuclei = 1000
        self.assertEqual(plate.total_nuclei, 1000000)

    def test_split_seq_well(self):
        row = "A"
        column = "2"
        well_single = SplitSeqWell.objects.create(
            plate=self.plate_fake,
            row=row,
            column=column,
        )
        well_single.save()
        well_single.biosample.set([self.fixed_sample_tail])
        well_single.barcode.set(
            [self.library_barcode_fake_r, self.library_barcode_fake_t]
        )

        self.assertEqual(str(well_single), f"{self.plate_fake.name} A2")
        self.assertEqual(well_single.well, f"{row}{column}")

    def test_subpool(self):
        subpool = Subpool.objects.create(
            name="002_13A",
            plate=self.plate_fake,
            nuclei=67000,
            selection_type="NO",
            cdna_pcr_rounds="5 + 7",
            cdna_ng_per_ul=22.0,
            cdna_volume=25,
            bioanalyzer_date="2023-1-1",
            index_pcr_number=11,
            index=1,
            library_ng_per_ul=25.0,
            library_average_bp_length=430,
        )
        subpool.save()
        subpool.barcode.set([self.library_barcode_fake_illumina])
        subpool.save()

        subpool.clean()
        self.assertEqual(subpool.plate_name(), self.plate_fake.name)
        self.assertEqual(str(subpool), subpool.name)
        self.assertEqual(subpool.subpool_name, "13A")

    def test_subpool_no_gene_capture(self):
        subpool = Subpool.objects.create(
            name="002_13A",
            plate=self.plate_fake,
            nuclei=67000,
            selection_type="NO",
            cdna_pcr_rounds="5 + 7",
            cdna_ng_per_ul=22.0,
            cdna_volume=25,
            bioanalyzer_date="2023-1-1",
            gene_capture_ng_per_ul=17.5,
            index_pcr_number=11,
            index=1,
            library_ng_per_ul=25.0,
            library_average_bp_length=430,
        )
        self.assertRaises(ValidationError, subpool.clean)
        self.assertEqual(subpool.subpool_name, "13A")

    def test_subpool_was_gene_capture(self):
        subpool = Subpool.objects.create(
            name="002_13A",
            plate=self.plate_fake,
            nuclei=67000,
            selection_type="EX",
            cdna_pcr_rounds="5 + 7",
            cdna_ng_per_ul=22.0,
            cdna_volume=25,
            bioanalyzer_date="2023-1-1",
            gene_capture_ng_per_ul=17.5,
            index_pcr_number=11,
            index=1,
            library_ng_per_ul=25.0,
            library_average_bp_length=430,
        )
        subpool.clean()

    def test_platform(self):
        name = "novaseq6000"
        display_name = "Novaseq 6000"

        platform = Platform.objects.create(
            name=name,
            igvf_id="/platform-terms/EFO_0008637/",
            display_name=display_name,
            family="illumina",
        )

        self.assertEqual(str(platform), display_name)

    def test_sequencing_run(self):
        name = "next01"
        run = SequencingRun.objects.create(
            name=name,
            run_date="1066-10-14",
            platform=self.platform_novaseq,
            plate=self.plate_fake,
            stranded=StrandedEnum.REVERSE,
        )

        self.assertEqual(str(run), name)
        self.assertEqual(run.platform_name, self.platform_novaseq.name)
        self.assertEqual(run.plate_name, self.plate_fake.name)

    def test_subpool_in_run(self):
        subpool_run = LibraryInRun.objects.create(
            subpool=self.subpool_fake,
            sequencing_run=self.sequencing_run_fake,
            status=RunStatusEnum.PASS,
            # measurement_set=
        )

        self.assertEqual(
            str(subpool_run),
            f"{self.subpool_fake.name} {self.sequencing_run_fake.name}",
        )

    def test_measurement_set(self):
        name = "TST12345"
        measurement_set = MeasurementSet.objects.create(name=name)

        self.assertEqual(str(measurement_set), name)

    def test_subpool_in_run_file(self):
        filename_r1 = "next02/002_13B_R1.fastq.gz"
        sequencing_file_r1 = SequencingFile.objects.create(
            sequencing_run=self.sequencing_run_fake,
            library_in_run=self.subpool_run,
            md5sum="68b329da9893e34099c7d8ad5cb9c940",
            filename=filename_r1,
            lane=1,
            read="R1",
        )

        self.assertEqual(str(sequencing_file_r1), filename_r1)

    # testing nanopore tables
    # we've got two kinds of nanopore data, one derived from the splitseq
    # subpools, and one from a fresh isolation from different tissues.

    def test_ont_sample_extraction_from_tissue(self):
        name = "ONT002"
        extraction = NucleicAcidExtraction.objects.create(
            name=name,
            date="2022-08-12",
            # in ONT sequencing this is computed from 150 / input_ng_per_ul.
            # The spreadsheet is visually rounded to 2 digits, and as it's
            # something pipetted there's a limit to how accurately it can be
            # moved
            volume_ul=1.15,
            # this is column M of ONT sequencing IGVF_Splitseq
            input_ng_per_ul=130,
            passed_qc=True,
        )
        extraction.save()
        extraction.tissue.set([self.tissue_tail])
        extraction.save()

        self.assertAlmostEqual(extraction.total, 149.5)

    def test_ont_sample_extraction_from_subpool(self):
        extraction = NucleicAcidExtraction.objects.create(
            name="ONT002",
            date="2022-08-12",
            # in ONT sequencing this is computed from 150 / input_ng_per_ul.
            # this is the actual value of the calculation which has more
            # significant digit than can be used.
            volume_ul=6.8181818181,
            # this is column M of ONT sequencing IGVF_Splitseq
            input_ng_per_ul=22,
            passed_qc=True,
        )
        extraction.save()
        extraction.subpool.set([self.subpool_fake])
        extraction.save()

        # our recorded concentration should match subpool
        # cdna_ng_per_ul or gene_capture_ng_per_ul (for gene capture
        # experiments)
        self.assertAlmostEqual(self.subpool_fake.cdna_ng_per_ul, extraction.input_ng_per_ul)
        self.assertAlmostEqual(extraction.total, 150)

    def test_ont_subpool_library(self):
        name = "ONT002"
        extraction = NucleicAcidExtraction.objects.create(
            name=name,
            date="2022-08-12",
            # in ONT sequencing this is cdna input (ng) (Col L) / input_ng_per_ul. (Col M)
            volume_ul=1.1538461538461537,
            # this is column M of ONT sequencing IGVF_Splitseq
            input_ng_per_ul=130,
            passed_qc=True,
        )
        extraction.save()
        extraction.tissue.set([self.tissue_tail])
        extraction.save()

        library = NanoporeLibrary.objects.create(
            name="ONT002",
            nucleic_acid=NucleicAcidEnum.rna,
            technician="Jay",
            build_date="2022-08-12",
            # this is [library] (ng/nl) (O) on ONT sequencing
            ng_per_ul=3.82,
            # this is from sample loading vol (S) on ONT sequencing
            volume_ul=2.0942408377,
        )
        library.save()
        library.nucleic_acid_extraction.set([extraction])
        library.save()

        self.assertAlmostEqual(library.total, 8)

    def test_ont_subpool_sequencing(self):
        run = SequencingRun.objects.create(
            run_date="2022-12-13",
            platform=self.platform_gridion,
            flowcell_kit="SQK-LSK114-XL",
            flowcell_type="FLO-PRO114M",
            flowcell_id="FAU21462",
            sequencing_software="23.04.05",
        )

        library_in_run = LibraryInRun.objects.create(
            nanopore=self.ont_subpool_library,
            sequencing_run=run,
            status="P",
        )

        pod5 = SequencingFile.objects.create(
            sequencing_run=run,
            library_in_run=library_in_run,
            filename="igvf003_13A-gc_lig-ss_p2_1.pod5",
            md5sum="3d76177a266b86aa588e49c4109c08cd",
        )

        fastq = SequencingFile.objects.create(
            sequencing_run=run,
            library_in_run=library_in_run,
            filename="igvf003_13A-gc_lig-ss_p2_1.fastq.gz",
            md5sum="1034404a43366a41b6840ad95b6ac439",
        )

        # These are more properties associated with generating a nanopore
        # fastq file
        #    basecaller_version="0.5.0",
        #    basecalling_mode="Super Accurate",
        #    basecalling_config="dna_r10.4.1_e8.2_400bps_sup@v4.1.0",
        #    q_score=10,

    def test_methylation_nucleic_acid_extraction(self):
        # These examples are coming from IGVF_methylation
        # Meth_DNA tab
        extraction = NucleicAcidExtraction.objects.create(
            # Tube ID (I)
            name="B02",
            # DNA Ext. Date (H)
            date="2023-08-23",
            # this is inferred from the formula of Avg * 50 = Total
            volume_ul=50,
            # DNA extraction 1 (J)
            concentration1=17.9,
            # DNA extraction 2 (K)
            concentration2=18.3,
            # Made into Lib? Or Disposed (O)
            passed_qc=True,
            # DNA extraction: Notes (N)
            comments="Elute incubation done for 1h instead of 30 min"
        )
        extraction.save()
        extraction.tissue.set([self.tissue_tail])
        extraction.save()

        self.assertAlmostEqual(extraction.average_concentration, 18.1)
        self.assertAlmostEqual(extraction.total, 905)

    def test_methylation_nanopore_library(self):
        # Libraries can be the result of pooling several tubes
        # Several examples taken from Meth_DNA
        # The spreadsheet has the same note applying to several rows.
        tubes = [
            ("B01", "2023-08-23", 50, 18.5, 18.5, True, None),
            ("B02", "2023-08-23", 50, 17.9, 18.3, True, "Elute incubation"),
            ("B03", "2023-08-23", 50, 17.9, 17.7, True, None),
        ]

        extractions = []
        for name, ext_date, volume, c1, c2, qc, note in tubes:
            e = NucleicAcidExtraction.objects.create(
                name=name,
                date=ext_date,
                volume_ul=volume,
                concentration1=c1,
                concentration2=c2,
                passed_qc=qc,
                comments=note,
            )
            e.save()
            e.tissue.set([self.tissue_tail])
            e.save()
            extractions.append(e)

        concentration = sum([e.average_concentration for e in extractions])/len(extractions)
        volume = sum([e.total for e in extractions])

        # This object is coming from Meth_Lib
        library = NanoporeLibrary.objects.create(
            # Tube ID (J)
            name="B01+B02+B03",
            # inferred from spreadsheet
            nucleic_acid=NucleicAcidEnum.dna,
            # Technician (B)
            technician="Yes",
            # Lib Exp Date (A)
            build_date="2023-08-23",
            # the calculated value is in Library (ng/uL) Avg (S)
            ng_per_ul=concentration,
            # the calculated value is in Library (ng/uL)  Total (T)
            volume_ul=volume,
        )
        library.save()
        library.nucleic_acid_extraction.set(extractions)
        library.save()

    def test_ont_methylation_sequencing(self):
        extraction = NucleicAcidExtraction.objects.create(
            name="C01",
            date="2023-08-26",
            volume_ul=50,
            concentration1=39.4,
            concentration2=41.6,
            passed_qc=True,
        )
        extraction.save()
        extraction.tissue.set([self.tissue_tail])
        extraction.save()

        # This object is coming from Meth_Lib
        library = NanoporeLibrary.objects.create(
            # Tube ID (J)
            name="C01",
            # inferred from spreadsheet
            nucleic_acid=NucleicAcidEnum.dna,
            # Technician (B)
            technician="Yes",
            # Lib Exp Date (A)
            build_date="2023-08-22",
            ng_per_ul=46,
            volume_ul=12,
        )
        library.save()
        library.nucleic_acid_extraction.set([extraction])
        library.save()

        run = SequencingRun.objects.create(
            run_date="2023-08-12",
            platform=self.platform_gridion,
            flowcell_kit="SQK-LSK114-XL",
            flowcell_type="FLO-PRO114M",
            flowcell_id="FAU21462",
            sequencing_software="23.04.05",
        )

        library_in_run = LibraryInRun.objects.create(
            nanopore=self.ont_subpool_library,
            sequencing_run=run,
            status="P",
        )

        pod5 = SequencingFile.objects.create(
            sequencing_run=run,
            library_in_run=library_in_run,
            filename="igvfm003_03_lig-dna_p2_2.pod5",
            md5sum="3d76177a266b86aa588e49c4109c08cd",
        )

        fastq = SequencingFile.objects.create(
            sequencing_run=run,
            library_in_run=library_in_run,
            filename="igvf003_13A-gc_lig-ss_p2_1.fastq.gz",
            md5sum="1034404a43366a41b6840ad95b6ac439",
        )
