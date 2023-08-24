from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from igvf_mice.models import (
    Source,
)
# Will need to test aliases on Mouse serializer
#        self.assertEqual(male_mouse.aliases, [f"ali-mortazavi:{male_mouse.name}"])


class TestSerializers(APITestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_user")

    def test_source(self):
        name = "test-source"
        display_name = "test source"
        homepage = "https://example.com/source"
        igvf_id = "/source/test_source"

        self.failUnlessRaises(Source.DoesNotExist, Source.objects.get, name=name)

        url = reverse("source-list")
        payload = {
            "name": name,
            "display_name": display_name,
            "homepage": homepage,
            "igvf_id": igvf_id,
        }
        self.client.force_authenticate(user=None)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        s = Source.objects.get(name=name)
        self.assertEqual(s.homepage, homepage)
        self.assertEqual(s.igvf_id, igvf_id)
