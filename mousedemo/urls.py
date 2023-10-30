"""mousedemo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from igvf_mice import views

router = routers.DefaultRouter()
router.register(r"accession", views.AccessionViewSet)
router.register(r"source", views.SourceViewSet)
router.register(r"library-construction-reagent", views.LibraryConstructionReagentViewSet)
router.register(r"library-barcode", views.LibraryBarcodeViewSet)
router.register(r"mouse-strain", views.MouseStrainViewSet)
router.register(r"mouse", views.MouseViewSet)
router.register(r"ontology-term", views.OntologyTermViewSet)
router.register(r"tissue", views.TissueViewSet)
router.register(r"fixed-sample", views.FixedSampleViewSet)
router.register(r"split-seq-plate", views.SplitSeqPlateViewSet)
router.register(r"split-seq-well", views.SplitSeqWellViewSet)
router.register(r"platform", views.PlatformViewSet)
router.register(r"subpool", views.SubpoolViewSet)
router.register(r"sequencing-run", views.SequencingRunViewSet)
router.register(r"subpool-in-run", views.SubpoolInRunViewSet)
router.register(r"subpool-in-run-file", views.SubpoolInRunFileViewSet)
router.register(r"measurement-set", views.MeasurementSetViewSet)

router.register(
    r"igvf/rodent-donor",
    views.IgvfRodentDonorViewSet,
    basename="igvf-rodent-donor",
)
router.register(
    r"igvf/sequence-file",
    views.IgvfSequenceFileViewSet,
    basename="igvf-sequence-file",
)


urlpatterns = [
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
