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
)


class TestModels(TestCase):
    def setUp(self):
        self.accession_namespace_igvf = AccessionNamespace.objects.create(
            name="IGVF", accession_prefix="igvf"
        )
        self.accession_namespace_igvf_test = AccessionNamespace.objects.create(
            name="IGVF test", accession_prefix="igvf_test"
        )
        self.source_fake = Source.objects.create(
            name="fake source",
            homepage="https://example.edu",
            igvf_id="/sources/example",
        )
        self.library_construction_kit_fake = LibraryConstructionKit.objects.create(
            name="a kit", version="3.14", source=self.source_fake
        )
        self.mouse_strain_fake = MouseStrain.objects.create(
            name="CASTJ/human glial cells",
            strain_type=StrainType.CC_FOUNDER,
            code="BR",
            jax_catalog_number="[redacted]",
            url="https://www.wikidata.org/wiki/Q1500726",
            notes="tries to escape",
            source=self.source_fake,
        )
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
        self.ontology_term_tail = OntologyTerm.objects.create(
            curie="UBERON:0002415",
            name="tail",
            description="An external caudal extension of the body.",
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
            mouse=self.mouse_male_fake,
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
