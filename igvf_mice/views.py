from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework import permissions
from igvf_mice.models import (
    Accession,
    Source,
    LibraryConstructionReagent,
    LibraryBarcode,
    MouseStrain,
    Mouse,
    OntologyTerm,
    Tissue,
    FixedSample,
    SplitSeqPlate,
    SplitSeqWell,
    Subpool,
    Platform,
    SequencingRun,
    SubpoolInRun,
    SubpoolInRunFile,
    MeasurementSet,
)
from igvf_mice.serializers import (
    AccessionSerializer,
    SourceSerializer,
    LibraryConstructionReagentSerializer,
    LibraryBarcodeSerializer,
    MouseStrainSerializer,
    MouseSerializer,
    OntologyTermSerializer,
    TissueSerializer,
    FixedSampleSerializer,
    SplitSeqPlateSerializer,
    SplitSeqWellSerializer,
    SubpoolSerializer,
    PlatformSerializer,
    SequencingRunRootSerializer,
    SubpoolInRunSerializer,
    SubpoolInRunFileSerializer,
    MeasurementSetSerializer,
    IgvfRodentDonorSerializer,
    IgvfSequenceFileSerializer,
    IgvfSeqSpecListSerializer,
    IgvfSeqSpecDetailSerializer,
    PipelineSampleMetadataSerializer,
)


class AccessionViewSet(viewsets.ModelViewSet):
    queryset = Accession.objects.all()
    serializer_class = AccessionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LibraryConstructionReagentViewSet(viewsets.ModelViewSet):
    queryset = LibraryConstructionReagent.objects.all()
    serializer_class = LibraryConstructionReagentSerializer
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
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("strain",)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class OntologyTermViewSet(viewsets.ModelViewSet):
    queryset = OntologyTerm.objects.all()
    serializer_class = OntologyTermSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TissueViewSet(viewsets.ModelViewSet):
    queryset = Tissue.objects.all()
    serializer_class = TissueSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("mouse", "ontology_term",)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class FixedSampleViewSet(viewsets.ModelViewSet):
    queryset = FixedSample.objects.all()
    serializer_class = FixedSampleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SplitSeqPlateViewSet(viewsets.ModelViewSet):
    queryset = SplitSeqPlate.objects.all()
    serializer_class = SplitSeqPlateSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SplitSeqWellViewSet(viewsets.ModelViewSet):
    queryset = SplitSeqWell.objects.all()
    serializer_class = SplitSeqWellSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("plate",)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SubpoolViewSet(viewsets.ModelViewSet):
    queryset = Subpool.objects.all()
    serializer_class = SubpoolSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("plate",)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SequencingRunViewSet(viewsets.ModelViewSet):
    queryset = SequencingRun.objects.all()
    serializer_class = SequencingRunRootSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SubpoolInRunViewSet(viewsets.ModelViewSet):
    queryset = SubpoolInRun.objects.all()
    serializer_class = SubpoolInRunSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("subpool", "measurement_set", "sequencing_run",)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SubpoolInRunFileViewSet(viewsets.ModelViewSet):
    queryset = SubpoolInRunFile.objects.all()
    serializer_class = SubpoolInRunFileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class MeasurementSetViewSet(viewsets.ModelViewSet):
    queryset = MeasurementSet.objects.all()
    serializer_class = MeasurementSetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class IgvfRodentDonorViewSet(viewsets.ModelViewSet):
    serializer_class = IgvfRodentDonorSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Mouse.objects.all()


class IgvfSequenceFileViewSet(viewsets.ModelViewSet):
    serializer_class = IgvfSequenceFileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return SubpoolInRunFile.objects.all()


class PipelineSampleMetadataViewSet(viewsets.ModelViewSet):
    queryset = SplitSeqWell.objects.order_by("plate", "row", "column")
    serializer_class = PipelineSampleMetadataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("plate__name",)
