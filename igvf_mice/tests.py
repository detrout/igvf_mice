from django.test import TestCase

from .models import (
    AccessionNamespace,
    Accession,
    Source,

)


class TestAccession(TestCase):
    def setUp(self):
        self.igvf = AccessionNamespace.objects.create(name="IGVF", accession_prefix="igvf")
        self.igvf_test = AccessionNamespace.objects.create(name="IGVF test", accession_prefix="igvf_test")

    def test_accession(self):
        test016_B6J_10F = Accession.objects.create(
            namespace=self.igvf_test,
            name="TSTDO36427294",
            url="https://api.sandbox.igvf.org/rodent-donors/TSTDO36427294/")

        self.assertEqual(str(test016_B6J_10F), "igvf_test:TSTDO36427294")
        self.assertEqual(test016_B6J_10F.path, "/rodent-donors/TSTDO36427294/")
