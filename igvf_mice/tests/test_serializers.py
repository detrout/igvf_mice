from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from igvf_mice import models
from igvf_mice import serializers
# Will need to test aliases on Mouse serializer
#        self.assertEqual(male_mouse.aliases, [f"ali-mortazavi:{male_mouse.name}"])


class TestSerializers(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_user")

    def create_object(self, url, payload, expected_status):
        response = self.client.post(url, payload)
        if response.status_code == status.HTTP_201_CREATED:
            payload = response.json()
        else:
            print(response.content)
        self.assertEqual(response.status_code, expected_status)

        return payload

    def create_source(self, expected_status=status.HTTP_201_CREATED):
        payload = {
            "name": "test-source",
            "display_name": "test source",
            "homepage": "https://example.com/source",
            "igvf_id": "/source/test_source"
        }

        url = reverse("source-list")
        return self.create_object(url, payload, expected_status)

    def create_library_construction_reagent(self, expected_status=status.HTTP_201_CREATED):
        source = self.create_source(expected_status=expected_status)
        payload = {
            "name": "parse-wt",
            "display_name": "Parse WT",
            "version": "v2",
            "source": source.get("@id")
        }

        url = reverse("libraryconstructionreagent-list")
        return self.create_object(url, payload, expected_status)

        return payload

    def create_udi_library_barcode(self, expected_status=status.HTTP_201_CREATED):
        reagent = self.create_library_construction_reagent(expected_status=expected_status)
        payload = {
            "name": "UDI_Plate_WT_1",
            "code": "UDI01",
            "i7_sequence": "CAGATCAC",
            "i5_sequence": "CTTCACAT",
            "well_position": "A1",
            "reagent": reagent.get("@id"),
        }

        url = reverse("librarybarcode-list")
        return self.create_object(url, payload, expected_status)

    def create_mouse_strain(self, expected_status=status.HTTP_201_CREATED):
        source = self.create_source()
        payload = {
            "name": "B6J",
            "display_name": "C57BL/6J",
            "igvf_id": "C57BL/6J (B6)",
            "strain_type": "FO",
            "jax_catalog_number": "000664",
            "see_also": "https://www.jax.org/strain/000664",
            "source": source.get("@id"),
        }

        url = reverse("mousestrain-list")
        return self.create_object(url, payload, expected_status)

    def create_mouse(self, expected_status=status.HTTP_201_CREATED):
        mouse_strain = self.create_mouse_strain()
        payload = {
            "name": "016_B6J_10F",
            "sex": "F",
            "estrus_cycle": "D",
            "weight_g": 21.1,
            "date_of_birth": "2022-08-16",
            "harvest_date": "2022-10-27",
            "timepoint_description": "10 weeks",
            "life_stage": "A",
            "housing_number": 400802,
            "strain": mouse_strain.get("@id"),
        }

        url = reverse("mouse-list")
        return self.create_object(url, payload, expected_status)

    def create_ontology_term_lung(self, expected_status=status.HTTP_201_CREATED):
        payload = {
            "curie": "UBERON:0002048",
            "name": "lung",
        }

        url = reverse("ontologyterm-list")
        return self.create_object(url, payload, expected_status)

    def create_tissue_lung(self, expected_status=status.HTTP_201_CREATED):
        mouse = self.create_mouse()
        lung = self.create_ontology_term_lung()

        payload = {
            "name": "016_B6J_10F_07",
            "mouse": mouse["@id"],
            "dissection_time": "2023-10-27T11:15:30",
            "description": "lung",
            "ontology_term": [lung["@id"]],
            "tube_label": "016-07",
            "total_weight_g": 1.031,
        }
        tissue = serializers.TissueSerializer(data=payload)
        if not tissue.is_valid():
            print(tissue.errors)

        url = reverse("tissue-list")
        return self.create_object(url, payload, expected_status)

    def create_fixed_sample_lung(self, expected_status=status.HTTP_201_CREATED):
        lung = self.create_tissue_lung()

        payload = {
            "name": lung["name"],
            "tube_label": "016-17",
            "fixation_name": "IGVF_FIX_30",
            "fixation_date": "2023-10-28",
            "starting_nuclei": 100000,
            "fixed_nuclei": 67000,
            "aliquots_made": 1,
            "aliquot_volume_ul": 50,
            "tissue": [lung["@id"]],
        }

        url = reverse("fixedsample-list")
        return self.create_object(url, payload, expected_status)


    def test_source(self):
        self.failUnlessRaises(
            models.Source.DoesNotExist,
            models.Source.objects.get,
            name="test-source"
        )

        self.assertEqual(models.Source.objects.count(), 0)
        self.client.force_authenticate(user=None)
        payload = self.create_source(status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        payload = self.create_source(status.HTTP_201_CREATED)

        s = models.Source.objects.get(name=payload["name"])
        self.assertEqual(s.homepage, payload["homepage"])
        self.assertEqual(s.igvf_id, payload["igvf_id"])
        self.assertIn("@id", payload)

    def test_create_library_reagent(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_library_construction_reagent()

        reagent = models.LibraryConstructionReagent.objects.get(name=payload["name"])
        self.assertEqual(reagent.name, payload["name"])
        self.assertIn("@id", payload)

    def test_create_library_barcode(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_udi_library_barcode()

        barcode = models.LibraryBarcode.objects.get(name=payload["name"])
        self.assertEqual(barcode.name, payload["name"])
        self.assertEqual(barcode.code, payload["code"])
        self.assertEqual(barcode.i7_sequence, payload["i7_sequence"])
        self.assertIn("@id", payload)

    def test_create_mouse_strain_serializer(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_mouse_strain()

        mouse_strain = models.MouseStrain.objects.get(name="B6J")
        self.assertEqual(mouse_strain.name, payload["name"])
        self.assertEqual(mouse_strain.see_also, payload["see_also"])
        self.assertIn("@id", payload)

    def test_create_mouse_serializer(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_mouse()

        mouse = models.Mouse.objects.get(name=payload["name"])
        self.assertEqual(mouse.name, payload["name"])
        self.assertEqual(mouse.weight_g, payload["weight_g"])
        self.assertEqual(mouse.age_days, 72)

    def test_tissue_serializer(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_tissue_lung()

        tissue = models.Tissue.objects.get(name=payload["name"])
        self.assertEqual(tissue.description, payload["description"])
        self.assertEqual(tissue.tube_label, "016-07")
        self.assertIn("@id", payload)

    def test_fixed_sample_serializer(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_fixed_sample_lung()

        name = payload["name"]
        fixed_sample = models.FixedSample.objects.get(name=name)

        self.assertEqual(fixed_sample.name, name)
        self.assertEqual(fixed_sample.tissue.first().name, name)
        self.assertIn("@id", payload)

