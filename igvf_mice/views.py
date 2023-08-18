from rest_framework import viewsets
from rest_framework import permissions
from igvf_mice.models import (
    Accession,
    Source,
    LibraryConstructionKit,
    LibraryBarcode,
    MouseStrain,
    Mouse,
    Subpool,
    SequencingRun,
    SubpoolInRun,
    SubpoolInRunFile,
)
from igvf_mice.serializers import (
    AccessionSerializer,
    SourceSerializer,
    LibraryConstructionKitSerializer,
    LibraryBarcodeSerializer,
    MouseStrainSerializer,
    MouseSerializer,
    IgvfRodentDonorSerializer,
    IgvfSequenceFileSerializer,
)


class AccessionViewSet(viewsets.ModelViewSet):
    queryset = Accession.objects.all()
    serializer_class = AccessionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LibraryConstructionKitViewSet(viewsets.ModelViewSet):
    queryset = LibraryConstructionKit.objects.all()
    serializer_class = LibraryConstructionKitSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LibraryBarcodeViewSet(viewsets.ModelViewSet):
    queryset = LibraryBarcode.objects.all()
    serializer_class = LibraryBarcodeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class MouseStrainViewSet(viewsets.ModelViewSet):
    queryset = MouseStrain.objects.all()
    serializer_class = MouseStrainSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class MouseViewSet(viewsets.ModelViewSet):
    queryset = Mouse.objects.all()
    serializer_class = MouseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class IgvfRodentDonorViewSet(viewsets.ModelViewSet):
    serializer_class = IgvfRodentDonorSerializer

    def get_queryset(self):
        return Mouse.objects.all()

class IgvfSequenceFileViewSet(viewsets.ModelViewSet):
    serializer_class = IgvfSequenceFileSerializer

    def get_queryset(self):
        return Subpool.objects.all()
