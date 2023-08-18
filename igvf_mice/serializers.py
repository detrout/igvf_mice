import os

from django.conf import settings
from rest_framework import serializers
from igvf_mice.models import (
    Accession,
    Source,
    LibraryConstructionKit,
    LibraryBarcode,
    MouseStrain,
    Mouse,
    SplitSeqPlate,
    Subpool,
    SubpoolInRun,
    SubpoolInRunFile,
)


class AccessionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Accession
        fields = ["name", "url"]


class SourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Source
        fields = "__all__"


class LibraryConstructionKitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LibraryConstructionKit
        fields = "__all__"


class LibraryBarcodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LibraryBarcode
        fields = "__all__"


class MouseStrainSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MouseStrain
        fields = "__all__"


class MouseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Mouse
        fields = "__all__"


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
            "accession",
            "aliases",
            "award",
            "lab",
            "taxa",
            "sex",
            "strain",
            "url",
            "source",
            "product_id",
            "strain_background",
            "individual_rodent",
            "rodent_identifier",
        ]

    accession = serializers.StringRelatedField(many=True)
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

    def get_aliases(self):
        return ["{}:{}".format(settings.LAB_ALIAS, self.name)]

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


class IgvfSequenceFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Subpool
        fields = [
            "name",
            "subpoolinrun",
        ]
        #depth = 3

    name = serializers.CharField()
    subpoolinrun = IgvfSubpoolInRunSerializer(source="subpoolinrun_set", many=True)

#class IgvfSequenceFileSerializerByFile(serializers.HyperlinkedModelSerializer, IgvfLabInfoMixin):
#    class Meta:
#        model = SubpoolInRunFile
#        fields = [
#            "accession",
#            #"aliases",
#            "award",
#            "lab",
#            "md5sum",
#            "file_format",
#            #"file_set",
#            "flowcell_id",
#            "lane",
#            #"sequencing_run",
#            "submitted_file_name",
#            "illumina_read_type",
#            #"sequencing_platform",
#            #"seqspec",
#        ]
#
#    accession = serializers.StringRelatedField(many=True)
#    #aliases = serializers.ListField(child=serializers.CharField())
#    award = serializers.SerializerMethodField()
#    lab = serializers.SerializerMethodField()
#    md5sum = serializers.CharField()
#    file_format = serializers.CharField()
#    #file_set = serializers.CharField()
#    flowcell_id = serializers.CharField()
#    lane = serializers.IntegerField()
#    #sequencing_run = serializers.IntegerField()
#    submitted_file_name = serializers.CharField(source="filename")
#    illumina_read_type = serializers.CharField(source="read", allow_null=True)
#    # this is slow.
#    #sequencing_platform = serializers.CharField(source="subpool_run.sequencing_run.platform.igvf_id")
#    #seqspec = serializers.CharField()
#
