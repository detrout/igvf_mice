from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
    AccessionNamespace,
    Accession,
    Source,
    LibraryConstructionKit,
    LibraryBarcode,
    StrainType,
    MouseStrain,
    SexEnum,
    EstrusCycle,
    Mouse,
    OntologyTerm,
    AgeUnitsEnum,
    LifeStageEnum,
    require_3_underscores,
    Tissue,
    FixedSample,
    PlateSizeEnum,
    SplitSeqPlate,
    SplitSeqWell,
    Subpool,
    Platform,
    Stranded,
    SequencingRun,
    RunStatus,
    SubpoolInRun,
    SubpoolInRunFile,
    MeasurementSet,
)


class TestModels(TestCase):
    def setUp(self):
        self.accession_namespace_igvf = AccessionNamespace.objects.create(
            name="IGVF", accession_prefix="igvf"
        )
        self.accession_namespace_igvf.save()
        self.accession_namespace_igvf_test = AccessionNamespace.objects.create(
            name="IGVF test", accession_prefix="igvf_test"
        )
        self.accession_namespace_igvf_test.save()
        self.source_fake = Source.objects.create(
            name="fake source",
            homepage="https://example.edu",
            igvf_id="/sources/example",
        )
        self.source_fake.save()
        self.library_construction_kit_fake = LibraryConstructionKit.objects.create(
            name="a kit", version="3.14", source=self.source_fake
        )
        self.library_construction_kit_fake.save()
        self.library_barcode_fake_t = LibraryBarcode(
            kit=self.library_construction_kit_fake,
            name="pb123",
            code="1",
            sequence="GTCTAGGT",
            barcode_type="T",
        )
        self.library_barcode_fake_t.save()
        self.library_barcode_fake_r = LibraryBarcode(
            kit=self.library_construction_kit_fake,
            name="pb222",
            code="2",
            sequence="AGCTTAAC",
            barcode_type="R",
        )
        self.library_barcode_fake_r.save()
        self.library_barcode_fake_illumina = LibraryBarcode(
            kit=self.library_construction_kit_fake,
            name="I7",
            code="I7",
            sequence="TTCATGT",
        )
        self.library_barcode_fake_illumina.save()
        self.mouse_strain_fake = MouseStrain.objects.create(
            name="CASTJ/human glial cells",
            strain_type=StrainType.CC_FOUNDER,
            code="BR",
            jax_catalog_number="[redacted]",
            url="https://www.wikidata.org/wiki/Q1500726",
            notes="tries to escape",
            source=self.source_fake,
        )
        self.mouse_strain_fake.save()
        self.mouse_male_fake = Mouse.objects.create(
            name="Brain",
            strain=self.mouse_strain_fake,
            sex=SexEnum.MALE,
            weight_g=21.3,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            harvest_date="1998-11-14",
            # estrus_cycle=None,
            operator="WB",
            notes="very fake mouse",
            sample_box="791.45/75",
        )
        self.mouse_male_fake.save()
        self.mouse_female_fake = Mouse.objects.create(
            name="Dot",
            strain=self.mouse_strain_fake,
            sex=SexEnum.FEMALE,
            weight_g=20.1,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            harvest_date="1998-11-14",
            estrus_cycle=EstrusCycle.ANESTRUS,
            operator="WB",
            notes="very fake mouse",
            sample_box="891.45/75",
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
            dissection_time="2023-08-11T17:07-08:00",
            timepoint_description="10 weeks",
            life_stage=LifeStageEnum.POST_NATAL,
            tube_label="016-30",
            tube_weight_g=1.23,
            total_weight_g=1.5,
            dissector="WB",
            dissection_notes="levitated for 5 minutes",
        )
        self.tissue_tail.ontology_term.set([self.ontology_term_tail])
        self.tissue_tail.save()

        self.fixed_sample_tail = FixedSample(
            name="108_CASTJ_10M_21",
            tube_label="108_21",
            fixation_name="imaginary test",
            fixation_date="2023-1-1",
            starting_nuclei=17,
            nuclei_into_fixation=4,
            fixed_nuclei=3,
            aliquots_made=2,
            aliquot_volume_ul=150,
        )
        self.fixed_sample_tail.save()
        self.fixed_sample_tail.tissue.set([self.tissue_tail])
        self.fixed_sample_tail.save()
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
            cdna_ng_per_ul_in_25ul=22.0,
            bioanalyzer_date="2023-1-1",
            index_pcr_number=11,
            index=2,
            library_ng_per_ul=30.0,
            library_average_bp_length=410,
        )
        self.subpool_fake.save()
        self.subpool_fake.barcode.set([self.library_barcode_fake_illumina])
        self.subpool_fake.save()
        self.platform = Platform.objects.create(
            name="novaseq2000",
            igvf_id="/platform-terms/EFO_0010963/",
            display_name="Novaseq 2000",
            family="illumina",
            source=self.source_fake,
        )
        self.sequencing_run_fake = SequencingRun.objects.create(
            name="next02",
            run_date="1991-08-25",
            platform=self.platform,
            plate=self.plate_fake,
            stranded=Stranded.REVERSE,
        )
        self.subpool_run = SubpoolInRun.objects.create(
            subpool=self.subpool_fake,
            sequencing_run=self.sequencing_run_fake,
            status=RunStatus.PASS,
            # measurement_set=
        )

    def test_accession(self):
        test016_B6J_10F = Accession.objects.create(
            namespace=self.accession_namespace_igvf_test,
            name="TSTDO36427294",
            url="https://api.sandbox.igvf.org/rodent-donors/TSTDO36427294/",
        )

        test016_B6J_10F.clean_fields()
        self.assertEqual(str(test016_B6J_10F), "igvf_test:TSTDO36427294")
        self.assertEqual(test016_B6J_10F.path, "/rodent-donors/TSTDO36427294/")

    def test_source(self):
        name = "Illumina"
        homepage = "https://www.illumina.com"
        source = Source.objects.create(
            name=name, homepage=homepage, igvf_id="/sources/illumina/"
        )

        source.clean_fields()
        self.assertEqual(source.name, name)
        self.assertEqual(source.link(), f'<a href="{homepage}">{homepage}</a>')

    def test_library_construction_kit(self):
        name = "b kit"
        version = "2.7.1"

        kit = LibraryConstructionKit(
            name=name,
            version=version,
            source=self.source_fake,
        )

        kit.clean_fields()
        self.assertEqual(str(kit), f"{name} {version}")

    def test_library_barcode(self):
        kit = self.library_construction_kit_fake
        name = "library name"
        code = "A123"
        sequence = "GATTACA"
        barcode_type = "R"
        barcode = LibraryBarcode(
            kit=kit,
            name=name,
            code=code,
            sequence=sequence,
            barcode_type=barcode_type,
        )

        barcode.clean_fields()
        self.assertEqual(barcode.kit_name, kit.name)
        self.assertEqual(str(barcode), f"{kit.name} {code} {sequence} {barcode_type}")

    def test_mouse_strain(self):
        strain = MouseStrain(
            name="brain",
            strain_type=StrainType.CC_FOUNDER,
            code="BR",
            jax_catalog_number="[redacted]",
            url="https://www.wikidata.org/wiki/Q1500726",
            notes="suffers from delusions of grandeur",
            source=self.source_fake,
        )

        strain.clean_fields()
        self.assertEqual(str(strain), strain.name)

    def test_mouse(self):
        male_mouse = Mouse(
            name="B1",
            strain=self.mouse_strain_fake,
            sex=SexEnum.MALE,
            weight_g=21.3,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            harvest_date="1998-11-14",
            # estrus_cycle=None,
            operator="WB",
            notes="very fake mouse",
            sample_box="791.45/75",
        )

        male_mouse.clean_fields()
        self.assertIsInstance(male_mouse.date_of_birth, date)
        self.assertEqual(male_mouse.age_days.days, 1162)
        self.assertEqual(male_mouse.source, self.mouse_strain_fake.source)

        female_mouse = Mouse(
            name="C1",
            strain=self.mouse_strain_fake,
            sex=SexEnum.FEMALE,
            weight_g=19.5,
            date_of_birth="1995-9-9",
            date_obtained="1995-9-9",
            harvest_date="1998-11-14",
            estrus_cycle=EstrusCycle.ANESTRUS,
            operator="DOT",
            notes="very fake mouse",
            sample_box="Tower",
        )

        female_mouse.clean_fields()
        self.assertIsInstance(female_mouse.date_of_birth, date)
        self.assertEqual(female_mouse.age_days.days, 1162)
        self.assertEqual(female_mouse.source, self.mouse_strain_fake.source)

    def test_ontology_term(self):
        curie = "UBERON:0001385"
        name = "tibialis anterior"
        term = OntologyTerm.objects.create(
            curie=curie,
            name=name,
            description="A muscle that originates in the upper two-thirds of the lateral surface of the tibia",
        )

        term.clean_fields()
        self.assertEqual(str(term), f"{curie} ({name})")
        url = "https://data.igvf.org/sample-terms/UBERON_0001385"
        self.assertEqual(term.url, url)
        self.assertEqual(term.link(), f'<a href="{url}">{curie}</a>')

    def test_validate_3_underscores(self):
        self.assertRaises(ValidationError, require_3_underscores, "a_b_c")
        require_3_underscores("a_b_c_d")

    def test_tissue(self):
        tissue = Tissue.objects.create(
            mouse=self.mouse_female_fake,
            name="016_B6J_10F_30",
            description="tail",
            dissection_time="2023-08-11T17:07-08:00",
            timepoint_description="10 weeks",
            life_stage=LifeStageEnum.POST_NATAL,
            tube_label="016-30",
            tube_weight_g=1.23,
            total_weight_g=1.5,
            dissector="WB",
            dissection_notes="levitated for 5 minutes",
        )
        tissue.ontology_term.set([self.ontology_term_tail])

        tissue.clean_fields()
        self.assertAlmostEqual(tissue.weight_g, 0.27)
        self.assertAlmostEqual(tissue.weight_mg, 270)
        self.assertEqual(tissue.ontology_names, "tail")
        self.assertEqual(str(tissue), f"{tissue.name} {tissue.description}")

        tissue.ontology_term.set([self.ontology_term_tail, self.ontology_term_pbmc])
        tissue.clean_fields()
        self.assertEqual(
            tissue.ontology_names, "peripheral blood mononuclear cell, tail"
        )

    def test_fixed_sample(self):
        name = "107_CASTJ_10F_21"
        fixed_sample = FixedSample.objects.create(
            name=name,
            tube_label="107_21",
            fixation_name="imaginary test",
            fixation_date="2023-1-1",
            starting_nuclei=17,
            nuclei_into_fixation=4,
            fixed_nuclei=3,
            aliquots_made=2,
            aliquot_volume_ul=150,
        )
        fixed_sample.save()
        fixed_sample.tissue.set([self.tissue_tail])

        self.assertEqual(str(fixed_sample), name)

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
        well_single = SplitSeqWell.objects.create(
            plate=self.plate_fake,
            row="A",
            column="2",
        )
        well_single.save()
        well_single.biosample.set([self.fixed_sample_tail])
        well_single.barcode.set(
            [self.library_barcode_fake_r, self.library_barcode_fake_t]
        )

        self.assertEqual(str(well_single), f"{self.plate_fake.name} A2")

    def test_subpool(self):
        subpool = Subpool.objects.create(
            name="002_13A",
            plate=self.plate_fake,
            nuclei=67000,
            selection_type="NO",
            cdna_pcr_rounds="5 + 7",
            cdna_ng_per_ul_in_25ul=22.0,
            bioanalyzer_date="2023-1-1",
            index_pcr_number=11,
            index=1,
            library_ng_per_ul=25.0,
            library_average_bp_length=430,
        )
        subpool.save()
        subpool.barcode.set([self.library_barcode_fake_illumina])
        subpool.save()

        self.assertEqual(subpool.plate_name(), self.plate_fake.name)
        self.assertEqual(str(subpool), subpool.name)

    def test_platform(self):
        name = "novaseq6000"
        display_name = "Novaseq 6000"

        platform = Platform.objects.create(
            name=name,
            igvf_id="/platform-terms/EFO_0008637/",
            display_name=display_name,
            family="illumina",
            source=self.source_fake,
        )

        self.assertEqual(str(platform), display_name)

    def test_sequencing_run(self):
        name = "next01"
        run = SequencingRun.objects.create(
            name=name,
            run_date="1066-10-14",
            platform=self.platform,
            plate=self.plate_fake,
            stranded=Stranded.REVERSE,
        )

        self.assertEqual(str(run), name)
        self.assertEqual(run.platform_name, self.platform.name)
        self.assertEqual(run.plate_name, self.plate_fake.name)

    def test_subpool_in_run(self):
        subpool_run = SubpoolInRun.objects.create(
            subpool=self.subpool_fake,
            sequencing_run=self.sequencing_run_fake,
            status=RunStatus.PASS,
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
        subpool_run_file_r1 = SubpoolInRunFile.objects.create(
            subpool_run=self.subpool_run,
            md5sum="68b329da9893e34099c7d8ad5cb9c940",
            filename=filename_r1,
            flowcell_id="AAC0JNKHV",
            lane=1,
            read="R1",
        )

        self.assertEqual(str(subpool_run_file_r1), filename_r1)
