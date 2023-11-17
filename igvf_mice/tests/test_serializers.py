from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from pathlib import Path
from urllib.parse import urlparse

from igvf_mice import models
from igvf_mice import serializers


def get_pk_from_id(value):
    urlparts = urlparse(value)
    parts = Path(urlparts.path).parts
    return parts[-1]


class TestSerializers(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_user")

    def create_object(self, url, payload, expected_status):
        # Does object already exist?
        # wells don't have a clear primary key, so we
        # can't check for their existence first.
        # Please don't create more than one of the same well.
        if url == "/library-barcode/":
            # special case library barcodes, because I'm using
            # the default primary key
            try:
                library = models.LibraryBarcode.objects.get(name=payload["name"])
                response = self.client.get("{}{}/".format(url, library.id))
                if response.status_code == status.HTTP_200_OK:
                    return response.json()
            except models.LibraryBarcode.DoesNotExist:
                pass
        elif url == "/sequencing-run/":
            try:
                run = models.SequencingRun.objects.get(name=payload["name"])
                response = self.client.get("{}{}/".format(url, run.id))
                if response.status_code == status.HTTP_200_OK:
                    return response.json()
            except models.SequencingRun.DoesNotExist:
                pass

        elif "name" in payload:
            response = self.client.get("{}{}/".format(url, payload["name"]))
            if response.status_code == status.HTTP_200_OK:
                return response.json()

        # If not make it
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

    def create_polyt_a1_library_barcodes(self, expected_status=status.HTTP_201_CREATED):
        reagent = self.create_library_construction_reagent(expected_status=expected_status)
        payload = {
            "name": "pbs_1239",
            "code": "A1",
            "i7_sequence": "CATTCCTA",
            "well_position": "A1",
            "barcode_type": "T",
            "well_position": "A1",
            "reagent": reagent.get("@id"),
        }

        url = reverse("librarybarcode-list")
        return self.create_object(url, payload, expected_status)

    def create_random_a1_library_barcodes(self, expected_status=status.HTTP_201_CREATED):
        reagent = self.create_library_construction_reagent(expected_status=expected_status)
        payload = {
            "name": "pbs_1327",
            "code": "A1",
            "i7_sequence": "CATCATCC",
            "well_position": "A1",
            "barcode_type": "R",
            "well_position": "A1",
            "reagent": reagent.get("@id"),
        }

        url = reverse("librarybarcode-list")
        return self.create_object(url, payload, expected_status)

    def create_udi01_library_barcode(self, expected_status=status.HTTP_201_CREATED):
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

    def create_split_seq_plate(self, expected_status=status.HTTP_201_CREATED):
        payload = {
            "name": "IGVF_TEST_01",
            "pool_location": "In a box",
            "date_performed": "2023-07-01",
        }

        url = reverse("splitseqplate-list")
        return self.create_object(url, payload, expected_status)

    def create_split_seq_wells(self, expected_status=status.HTTP_201_CREATED):
        plate = self.create_split_seq_plate(expected_status=expected_status)
        fixed_sample = self.create_fixed_sample_lung(expected_status=expected_status)
        a1_polyt = self.create_polyt_a1_library_barcodes(expected_status=expected_status)
        a1_random = self.create_random_a1_library_barcodes(expected_status=expected_status)

        payload = {
            "plate": plate["@id"],
            "row": "A",
            "column": "1",
            "biosample": [fixed_sample.get("@id")],
            "barcode": [a1_polyt["@id"], a1_random["@id"]],
        }

        url = reverse("splitseqwell-list")
        return self.create_object(url, payload, expected_status)

    def create_subpool(self, expected_status=status.HTTP_201_CREATED):
        plate = self.create_split_seq_plate(expected_status=expected_status)
        udi01 = self.create_udi01_library_barcode(expected_status=expected_status)

        payload = {
            "name": "003_8A",
            "nuclei": 8000,
            "selection_type": "NO",
            "subcellular_component": "N",
            "cdna_pcr_rounds": "5 + 9",
            "cdna_ng_per_ul": 130.0,
            "cdna_volume": 25.0,
            "bioanalyzer_date": "2022-12-05",
            "cdna_average_bp_length": 1150,
            "index_pcr_number": 12,
            "index":  "UDI01",
            "library_ng_per_ul": 11.8,
            "library_average_bp_length": 443,
            "plate": plate["@id"],
            "barcode": [udi01["@id"]],
        }

        url = reverse("subpool-list")
        return self.create_object(url, payload, expected_status)

    def create_platform(self, expected_status=status.HTTP_201_CREATED):
        payload = {
            "name": "nextseq2000",
            "igvf_id": "/platform-terms/EFO_0010963/",
            "display_name": "Nextseq 2000",
            "family": "illumina",
        }
        url = reverse("platform-list")
        return self.create_object(url, payload, expected_status)

    def create_sequencing_run(self, expected_status=status.HTTP_201_CREATED):
        platform = self.create_platform(expected_status=expected_status)
        subpool = self.create_subpool(expected_status=expected_status)

        payload = {
            "name": "igvf_003/nextseq",
            "run_date": "2010-10-1",
            "platform": platform["@id"],
            "plate": subpool["plate"],
            "stranded": str(models.StrandedEnum.REVERSE),
        }

        url = reverse("sequencingrun-list")
        return self.create_object(url, payload, expected_status)

    def create_subpool_in_run(self, expected_status=status.HTTP_201_CREATED):
        subpool = self.create_subpool(expected_status=expected_status)
        sequencing_run = self.create_sequencing_run(expected_status=expected_status)

        payload = {
            "subpool": subpool["@id"],
            "sequencing_run": sequencing_run["@id"],
            "raw_reads": 1000000,
            "status": str(models.RunStatusEnum.PASS),
        }
        url = reverse("subpoolinrun-list")
        return self.create_object(url, payload, expected_status)

    def create_subpool_in_run_file(self, expected_status=status.HTTP_201_CREATED):
        sequencing_run = self.create_sequencing_run(expected_status)
        subpool_run = self.create_subpool_in_run(expected_status)

        payload = {
            "md5sum": "d41d8cd98f00b204e9800998ecf8427e",
            "filename": "igvf_003/next1/003_67B_R2.fastq.gz",
            "flowcell_id": "AAATMGFHV",
            "read": "R2",
            "sequencing_run": sequencing_run["@id"],
            "subpool_run": subpool_run["@id"],
        }
        url = reverse("subpoolinrunfile-list")
        return self.create_object(url, payload, expected_status)

    def create_measurement_set(self, expected_status=status.HTTP_201_CREATED):
        subpool_in_run = self.create_subpool_in_run(expected_status)

        payload = {
            "name": "subpool_013_13A",
            "subpoolinrun_set": [subpool_in_run["@id"]],
        }

        url = reverse("measurementset-list")
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
        payload = self.create_udi01_library_barcode()

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

        # Can we add an accession?
        # start with no accessions
        self.assertEqual(mouse.accession.count(), 0)
        # create the accession
        accession = {
            "accession_prefix": "igvf",
            "name": "IGVFDO7007WBAX",
            "uuid": "7f506a6b95d24e529e9161f992a6c02c",
            "see_also": "https://api.data.igvf.org/rodent-donors/IGVFDO7007WBAX/",
        }
        accession_url = reverse("accession-list")
        accession = self.create_object(accession_url, accession, status.HTTP_201_CREATED)

        # link the accession to the mouse object
        response = self.client.patch(payload["@id"], {"accession": [accession["@id"]]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # is the accession now in the database
        self.assertEqual(mouse.accession.count(), 1)
        self.assertEqual(mouse.accession.first().name, accession["name"])
        self.assertEqual(mouse.accession.first().see_also, accession["see_also"])

        # does it also show up in the API?
        response = self.client.get(payload["@id"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_mouse = response.json()
        self.assertEqual(len(updated_mouse["accession"]), 1)
        self.assertEqual(updated_mouse["accession"][0], accession)

    def test_tissue_serializer(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_tissue_lung()

        tissue = models.Tissue.objects.get(name=payload["name"])
        self.assertEqual(tissue.description, payload["description"])
        self.assertEqual(tissue.tube_label, "016-07")
        self.assertIn("@id", payload)

        # Can we add an accession?
        # start with no accessions
        self.assertEqual(tissue.accession.count(), 0)
        # create the accession
        accession = {
            "accession_prefix": "igvf",
            "name": "IGVFSM3681WOHF",
            "uuid": "4119b4d9295d42a6bab5c4b6d7d241d3",
            "see_also": "https://api.data.igvf.org/tissues/IGVFSM3681WOHF/",
        }
        accession_url = reverse("accession-list")
        accession = self.create_object(accession_url, accession, status.HTTP_201_CREATED)

        # link the accession to the mouse object
        response = self.client.patch(payload["@id"], {"accession": [accession["@id"]]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # is the accession now in the database
        self.assertEqual(tissue.accession.count(), 1)
        self.assertEqual(tissue.accession.first().name, accession["name"])
        self.assertEqual(tissue.accession.first().see_also, accession["see_also"])

        # does it also show up in the API?
        response = self.client.get(payload["@id"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_tissue = response.json()
        self.assertEqual(len(updated_tissue["accession"]), 1)
        self.assertEqual(updated_tissue["accession"][0], accession)

    def test_fixed_sample_serializer(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_fixed_sample_lung()

        name = payload["name"]
        fixed_sample = models.FixedSample.objects.get(name=name)

        self.assertEqual(fixed_sample.name, name)
        self.assertEqual(fixed_sample.tissue.first().name, name)
        self.assertIn("@id", payload)

    def test_split_seq_plate(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_split_seq_plate()

        name = payload["name"]
        plate = models.SplitSeqPlate.objects.get(name=name)

        self.assertEqual(plate.name, name)
        self.assertEqual(plate.size, 96)  # Default value from models
        self.assertEqual(
            plate.date_performed.isoformat(), payload["date_performed"])

    def test_create_split_seq_well(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_split_seq_wells()

        well = models.SplitSeqWell.objects.get(plate__name="IGVF_TEST_01", row="A", column="1")
        self.assertEqual(well.well, "{}{}".format(payload["row"], payload["column"]))
        self.assertEqual(well.barcode.count(), 2)

    def test_create_subpool(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_subpool()

        subpool = models.Subpool.objects.get(name=payload["name"])
        self.assertEqual(subpool.nuclei, payload["nuclei"])
        self.assertEqual(subpool.selection_type, payload["selection_type"])

    def test_create_platform(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_platform()

        platform = models.Platform.objects.get(name=payload["name"])
        self.assertEqual(platform.igvf_id, payload["igvf_id"])
        self.assertEqual(platform.display_name, payload["display_name"])

    def test_create_sequencing_run(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_sequencing_run()

        run = models.SequencingRun.objects.get(name=payload["name"])
        self.assertEqual(run.plate.name, payload["plate"]["name"])

    def test_create_subpool_in_run(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_subpool_in_run()

        pk = get_pk_from_id(payload["@id"])
        subpool_in_run = models.SubpoolInRun.objects.get(pk=pk)

        self.assertEqual(subpool_in_run.status, str(models.RunStatusEnum.PASS))

    def test_create_subpool_in_run_file(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_subpool_in_run_file()

        pk = get_pk_from_id(payload["@id"])
        subpool_file = models.SubpoolInRunFile.objects.get(pk=pk)

        self.assertEqual(payload["flowcell_id"], subpool_file.flowcell_id)
        self.assertIsNone(subpool_file.lane)
        self.assertEqual(subpool_file.accession.count(), 0)

        # Can we add an accession?
        # start with no accessions
        self.assertEqual(subpool_file.accession.count(), 0)
        # create the accession
        accession = {
            "accession_prefix": "igvf",
            "name": "IGVFFI1667GMRZ",
            "uuid": "c82c421ac32144e0a459bcf60e68eb72",
            "see_also": "https://api.data.igvf.org/sequence-files/IGVFI1667GMRZ/",
        }
        accession_url = reverse("accession-list")
        accession = self.create_object(accession_url, accession, status.HTTP_201_CREATED)

        # link the accession to the mouse object
        response = self.client.patch(payload["@id"], {"accession": [accession["@id"]]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # is the accession now in the database
        self.assertEqual(subpool_file.accession.count(), 1)
        self.assertEqual(subpool_file.accession.first().name, accession["name"])
        self.assertEqual(subpool_file.accession.first().see_also, accession["see_also"])

        # does it also show up in the API?
        response = self.client.get(payload["@id"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_file = response.json()
        self.assertEqual(len(updated_file["accession"]), 1)
        self.assertEqual(updated_file["accession"][0], accession)

    def test_create_measurement_set(self):
        self.client.force_authenticate(user=self.user)
        payload = self.create_measurement_set()

        pk = get_pk_from_id(payload["@id"])
        measurement_set = models.MeasurementSet.objects.get(pk=pk)
        self.assertEqual(measurement_set.subpoolinrun_set.count(), 1)

        # Can we add an accession?
        # start with no accessions
        self.assertEqual(measurement_set.accession.count(), 0)
        # create the accession
        accession = {
            "accession_prefix": "igvf",
            "name": "IGVFDS0128SBCV",
            "uuid": "21aeaee1-beba-4133-ba82-02e7d6d49eaa",
            "see_also": "https://api.data.igvf.org/sequence-files/IGVFDS0128SBCV/",
        }
        accession_url = reverse("accession-list")
        accession = self.create_object(accession_url, accession, status.HTTP_201_CREATED)

        # link the accession to the mouse object
        response = self.client.patch(payload["@id"], {"accession": [accession["@id"]]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # is the accession now in the database
        self.assertEqual(measurement_set.accession.count(), 1)
        self.assertEqual(measurement_set.accession.first().name, accession["name"])
        self.assertEqual(measurement_set.accession.first().see_also, accession["see_also"])

        # does it also show up in the API?
        response = self.client.get(payload["@id"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_measurement = response.json()
        self.assertEqual(len(updated_measurement["accession"]), 1)
        self.assertEqual(updated_measurement["accession"][0], accession)
