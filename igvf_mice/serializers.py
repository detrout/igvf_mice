import os

from django.conf import settings
from rest_framework import serializers
from igvf_mice.models import (
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
    Tissue,
    FixedSample,
    SplitSeqPlate,
    SplitSeqWell,
    Subpool,
    Stranded,
    Platform,
    SequencingRun,
    SubpoolInRun,
    SubpoolInRunFile,
    MeasurementSet,
)


class AccessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Accession
        fields = ["@id", "name", "see_also"]


class SourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Source
        fields = [
            "@id",
            "name",
            "display_name",
            "homepage",
            "igvf_id",
        ]


class LibraryConstructionKitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LibraryConstructionKit
        fields = "__all__"


class LibraryBarcodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LibraryBarcode
        fields = "__all__"


class PlatformSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Platform
        fields = "__all__"


class SequencingRunChildSerializer(serializers.HyperlinkedModelSerializer):
    """Simple SequencingRun serialiizer.

    This version does not link to the SplitSeqPlate objects.

    See below for SequencingRunRootSerializer that does link to the
    SplitSeqPlate, but it needs to be declared after SplitSeqPlate.
    """
    class Meta:
        model = SequencingRun
        fields = [
            "@id",
            "name",
            "run_date",
            "stranded",
            "platform",
            "plate",
        ]

    platform = PlatformSerializer()
    stranded = serializers.ChoiceField(choices=Stranded.choices)


class MouseStrainSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MouseStrain
        fields = "__all__"

    strain_type = serializers.ChoiceField(choices=StrainType.choices)


class MouseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Mouse
        fields = "__all__"

    accession = AccessionSerializer(many=True)
    sex = serializers.ChoiceField(choices=SexEnum.choices)
    estrus_cycle = serializers.ChoiceField(EstrusCycle.choices)


class OntologyTermSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OntologyTerm
        fields = "__all__"


class TissueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tissue
        fields = "__all__"

    accession = AccessionSerializer(many=True)


class FixedSampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FixedSample
        fields = "__all__"


class SplitSeqPlateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SplitSeqPlate
        fields = [
            "@id",
            "name",
            "size",
            "pool_location",
            "date_performed",
            "barcoded_cell_counter",
            "volume_of_nuclei",
            "sequencing_runs",
        ]

    sequencing_runs = SequencingRunChildSerializer(source="sequencingrun_set", many=True)


class SplitSeqWellSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SplitSeqWell
        fields = "__all__"


class SequencingRunRootSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SequencingRun
        fields = [
            "@id",
            "name",
            "run_date",
            "stranded",
            "platform",
            "plate",
        ]

    platform = PlatformSerializer()
    plate = SplitSeqPlateSerializer()


class SubpoolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Subpool
        fields = [
            "@id",
            "name",
            "nuclei",
            "selection_type",
            "cdna_ng_per_ul_in_25ul",
            "bioanalyzer_date",
            "cdna_average_bp_length",
            "index_pcr_number",
            "index",
            "library_ng_per_ul",
            "library_average_bp_length",
            "plate",
            "barcode",
            "subpool_runs",
        ]

    barcode = LibraryBarcodeSerializer(many=True)
    subpool_runs = serializers.StringRelatedField(source="subpoolrun_set")


class SubpoolInRunSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubpoolInRun
        fields = "__all__"


class MeasurementSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MeasurementSet
        fields = "__all__"

    accession = AccessionSerializer(many=True)
    subpool_in_run = SubpoolInRunSerializer(source="subpoolinrun_set", many=True)


class IgvfLabInfoMixin:
    """Every IGVF object for submission needs award and lab
    """
    def get_award(self, obj):
        return "/awards/{}/".format(settings.AWARD)

    def get_lab(self, obj):
        return "/labs/{}".format(settings.LAB_ALIAS)


class IgvfRodentDonorSerializer(serializers.HyperlinkedModelSerializer, IgvfLabInfoMixin):
    class Meta:
        model = Mouse
        fields = [
            "@id",
            "accession",
            "aliases",
            "award",
            "lab",
            "taxa",
            "sex",
            "strain",
            "source",
            "product_id",
            "strain_background",
            "individual_rodent",
            "rodent_identifier",
        ]

    accession = AccessionSerializer(many=True)
    aliases = serializers.SerializerMethodField()
    award = serializers.SerializerMethodField()
    lab = serializers.SerializerMethodField()
    taxa = serializers.SerializerMethodField()
    sex = serializers.CharField()
    strain = serializers.CharField(source='strain.code')
    url = serializers.URLField(source='strain.url')
    source = serializers.CharField(source='strain.source.igvf_id')
    product_id = serializers.CharField(source='strain.jax_catalog_number')
    strain_background = serializers.CharField(source='strain.name')
    individual_rodent = serializers.SerializerMethodField()
    rodent_identifier = serializers.CharField(source='name')

    def get_aliases(self, obj):
        return ["{}:{}".format(settings.LAB_ALIAS, obj.name)]

    def get_taxa(self, obj):
        return "Mus musculus"

    def get_individual_rodent(self, obj):
        return 1


class IgvfSubpoolInRunFileSerializer(serializers.HyperlinkedModelSerializer, IgvfLabInfoMixin):
    class Meta:
        model = SubpoolInRunFile
        fields = [
            "award",
            "lab",
            "md5sum",
            "file_format",
            "flowcell_id",
            "lane",
            "submitted_file_name",
            "illumina_read_type",
        ]

    award = serializers.SerializerMethodField()
    lab = serializers.SerializerMethodField()
    md5sum = serializers.CharField()
    file_format = serializers.SerializerMethodField()
    # file_set
    # content_type
    flowcell_id = serializers.CharField()
    lane = serializers.IntegerField()
    # sequencing_run
    submitted_file_name = serializers.CharField(source="filename")
    illumina_read_type = serializers.CharField(source="read", required=False)

    def get_file_format(self, obj):
        filename = obj.filename
        file_type = None

        while file_type is None and len(filename) > 0:
            filename, suffix = os.path.splitext(filename)
            if suffix in (".gz", ".bz2"):
                pass
            elif suffix in (".fastq",):
                file_type = "fastq"
            elif suffix in (".bam",):
                file_type = "bam"

        return file_type


class IgvfSubpoolInRunSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubpoolInRun
        fields = [
            "files",
            #"sequencing_run",
            #"platform",
        ]

    files = IgvfSubpoolInRunFileSerializer(source="subpoolinrunfile_set", many=True)
    #sequencing_run = serializers.CharField(source="sequencing_run.name")
    #platform = serializers.CharField(source="sequencing_run.platform.igvf_id")
    
    #files = serializers.ListField(
    #    IgvfSubpoolInRunFileSerializer(source="subpoolinrunfile_set")
    #)


#class IgvfSequenceFileSerializer(serializers.HyperlinkedModelSerializer):
#    class Meta:
#        model = Subpool
#        fields = [
#            "name",
#            "subpoolinrun",
#        ]
#        #depth = 3
#
#    name = serializers.CharField()
#    subpoolinrun = IgvfSubpoolInRunSerializer(source="subpoolinrun_set", many=True)

class IgvfSequenceFileSerializer(serializers.HyperlinkedModelSerializer, IgvfLabInfoMixin):
    class Meta:
        model = SubpoolInRunFile
        fields = [
            "accession",
            #"aliases",
            "award",
            "lab",
            "md5sum",
            #"file_format",
            #"file_set",
            "flowcell_id",
            "lane",
            #"sequencing_run",
            "submitted_file_name",
            "illumina_read_type",
            "sequencing_platform",
            #"seqspec",
        ]

    accession = AccessionSerializer(many=True)
    #aliases = serializers.ListField(child=serializers.CharField())
    award = serializers.SerializerMethodField()
    lab = serializers.SerializerMethodField()
    md5sum = serializers.CharField()
    #file_format = serializers.CharField()
    #file_set = serializers.CharField()
    flowcell_id = serializers.CharField()
    lane = serializers.IntegerField()
    #sequencing_run = serializers.IntegerField()
    submitted_file_name = serializers.CharField(source="filename")
    illumina_read_type = serializers.CharField(source="read", allow_null=True)
    # this is slow.
    sequencing_platform = serializers.CharField(source="sequencing_run.platform.igvf_id")
    #seqspec = serializers.CharField()


class IgvfSeqSpecSequenceRegionSerializer(serializers.Serializer):
    class Meta:
        fields = []

    object_type = serializers.CharField(default="!Region", read_only=True)
    region_id = serializers.CharField(read_only=True)
    region_type = serializers.CharField(default="fastq", read_only=True)
    name = serializers.CharField(default="Read 1 sequence fastq", read_only=True)
    sequence_type = serializers.CharField(default="random", read_only=True)


class IgvfSeqSpecListSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubpoolInRunFile
        fields = [
            "id",
            "md5sum",
            "filename",
            "flowcell_id",
            "lane",
            "read",
        ]


class IgvfSeqSpecDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubpoolInRunFile
        fields = [
            "object_type",
            "seqspec_version",
            "assay",
            "sequencer",
            "doi",
            "publication_date",
            "name",
            "description",
            "modalities",
            "lib_struct",
        ]

    object_type = serializers.CharField(default="!Assay", read_only=True)
    seqspec_version = serializers.CharField(default="0.0.0", read_only=True)
    assay = serializers.SerializerMethodField(read_only=True)
    sequencer = serializers.SerializerMethodField(read_only=True)
    doi = serializers.CharField(default="", read_only=True)
    publication_date = serializers.CharField(default="", read_only=True)
    name = serializers.SerializerMethodField(read_only=True)
    description = serializers.SerializerMethodField(read_only=True)
    modalities = serializers.SerializerMethodField(read_only=True)
    lib_struct = serializers.CharField(default="", read_only=True)

    def get_assay(self, obj):
        if obj.sequencing_run.platform.family == "illumina":
            return "Wt-Mega-v2"
        else:
            raise NotImplementedError("Need to implement other seqspecs")

    def get_sequencer(self, obj):
        if obj.sequencing_run.platform.family == "illumina":
            return "Illumina"
        else:
            raise NotImplementedError("Need to implement other seqspecs")

    def get_name(self, obj):
        if obj.sequencing_run.platform.family == "illumina":
            return "WT Mega v2"
        else:
            raise NotImplementedError("Need to implement other seqspecs")

    def get_description(self, obj):
        if obj.sequencing_run.platform.family == "illumina":
            return "split-pool ligation-based transcriptome sequencing"
        else:
            raise NotImplementedError("Need to implement other seqspecs")

    def get_modalities(self, obj):
        if obj.sequencing_run.platform.family == "illumina":
            return ["rna"]
        else:
            raise NotImplementedError("Need to implement other seqspecs")
