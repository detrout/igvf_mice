import os
from urllib.parse import urlsplit

from django.conf import settings
from rest_framework import serializers
from igvf_mice.models import (
    Accession,
    Source,
    LibraryConstructionReagent,
    LibraryBarcode,
    StrainType,
    MouseStrain,
    SexEnum,
    EstrusCycle,
    Mouse,
    OntologyTerm,
    LifeStageEnum,
    Tissue,
    FixedSample,
    SplitSeqPlate,
    SplitSeqWell,
    SublibrarySelectionTypeEnum,
    SubcellularComponentEnum,
    Subpool,
    StrandedEnum,
    Platform,
    SequencingRun,
    SubpoolInRun,
    SubpoolInRunFile,
    MeasurementSet,
)


def expand_field(value, field_model, field_serializer, request, pkname="name"):
    if value is None:
        return None

    if isinstance(value, list):
        data = [expand_field(x, field_model, field_serializer, request, pkname) for x in value]
    elif isinstance(value, str):
        urlpath = urlsplit(value).path
        parts = [x for x in urlpath.split("/") if len(x) > 0]
        object_name = parts[-1]
        obj = field_model.objects.get(**{pkname: object_name})
        # ceral is a pun for serialized
        context = {"request": request}
        cereal = field_serializer(obj, context=context)
        data = cereal.data
    else:
        print("Unrecognized type {type(value)}")
        return None

    return data


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


class LibraryConstructionReagentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LibraryConstructionReagent
        fields = [
            "@id",
            "name",
            "display_name",
            "version",
            "source",
        ]


class LibraryBarcodeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LibraryBarcode
        fields = [
            "@id",
            "name",
            "code",
            "i7_sequence",
            "i5_sequence",
            "barcode_type",
            "well_position",
            "reagent",
        ]


class PlatformSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Platform
        fields = [
            "@id",
            "name",
            "display_name",
            "igvf_id",
            "family"
        ]


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
    stranded = serializers.ChoiceField(choices=StrandedEnum.choices)


class MouseStrainSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MouseStrain
        fields = [
            "@id",
            "name",
            "display_name",
            "igvf_id",
            "strain_type",
            "jax_catalog_number",
            "see_also",
            "notes",
            "source",
        ]

    strain_type = serializers.ChoiceField(choices=StrainType.choices)


class MouseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Mouse
        fields = [
            "@id",
            "name",
            "strain",
            "sex",
            "weight_g",
            "date_of_birth",
            "date_obtained",
            "age_days",
            "harvest_date",
            "timepoint_description",
            "life_stage",
            "estrus_cycle",
            "operator",
            "notes",
            "housing_number",
            "accession",
        ]
        extra_kwargs = {"accession": {"required": False, "allow_empty": True}}

    sex = serializers.ChoiceField(choices=SexEnum.choices)
    estrus_cycle = serializers.ChoiceField(choices=EstrusCycle.choices)
    life_stage = serializers.ChoiceField(choices=LifeStageEnum.choices)

    def to_representation(self, value):
        data = super().to_representation(value)
        request = self.context.get("request")

        if "accession" in data:
            data["accession"] = expand_field(data["accession"], Accession, AccessionSerializer, request)
        return data


class OntologyTermSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OntologyTerm
        fields = [
            "@id",
            "curie",
            "name",
            "description",
        ]


class TissueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tissue
        fields = [
            "@id",
            "name",
            "mouse",
            "description",
            "ontology_term",
            "fixedsample_set",
            "dissection_time",
            "tube_label",
            "tube_weight_g",
            "total_weight_g",
            "weight_mg",
            "dissector",
            "dissection_notes",
            "accession"
        ]
        extra_kwargs = {"accession": {"required": False, "allow_empty": True}}

    def to_representation(self, value):
        data = super().to_representation(value)
        request = self.context.get("request")

        if "mouse" in data:
            data["mouse"] = expand_field(data["mouse"], Mouse, MouseSerializer, request)
        if "accession" in data:
            data["accession"] = expand_field(data["accession"], Accession, AccessionSerializer, request)
        return data


class FixedSampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FixedSample
        fields = [
            "@id",
            "name",
            "tube_label",
            "fixation_name",
            "fixation_date",
            "tissue",
            "starting_nuclei",
            "nuclei_into_fixation",
            "fixed_nuclei",
            "aliquots_made",
            "aliquot_volume_ul",
            "splitseqwell_set",
        ]

    def to_representation(self, value):
        data = super().to_representation(value)
        request = self.context.get("request")

        if "tissue" in data:
            data["tissue"] = expand_field(data["tissue"], Tissue, TissueSerializer, request)
        return data


class MinimalSplitSeqWellSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SplitSeqWell
        fields = [
            "@id",
            "well",
        ]

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
            "wells",
        ]

    sequencing_runs = SequencingRunChildSerializer(source="sequencingrun_set", many=True, required=False)
    wells = MinimalSplitSeqWellSerializer(source="splitseqwell_set", many=True, required=False)


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

    def to_representation(self, value):
        data = super().to_representation(value)
        request = self.context.get("request")

        if "plate" in data:
            data["plate"] = expand_field(data["plate"], SplitSeqPlate, SplitSeqPlateSerializer, request)
        return data


class SubpoolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Subpool
        fields = [
            "@id",
            "name",
            "nuclei",
            "selection_type",
            "subcellular_component",
            "cdna_ng_per_ul",
            "cdna_volume",
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

    selection_type = serializers.ChoiceField(
        choices=SublibrarySelectionTypeEnum.choices)
    subcellular_component = serializers.ChoiceField(
        choices=SubcellularComponentEnum.choices)
    subpool_runs = serializers.StringRelatedField(source="subpoolrun_set", required=False)

    def to_representation(self, value):
        data = super().to_representation(value)
        request = self.context.get("request")

        if "barcode" in data:
            data["barcode"] = expand_field(data["barcode"], LibraryBarcode, LibraryBarcodeSerializer, request, "id")
        return data


class SubpoolInRunSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubpoolInRun
        fields = [
            "@id",
            "subpool",
            "sequencing_run",
            "raw_reads",
            "status",
            "measurement_set",
        ]


class SubpoolInRunFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SubpoolInRunFile
        fields = [
            "@id",
            "md5sum",
            "filename",
            "flowcell_id",
            "lane",
            "read",
            "sequencing_run",
            "subpool_run",
            "accession",
        ]
        extra_kwargs = {"accession": {"required": False, "allow_empty": True}}

    def to_representation(self, value):
        data = super().to_representation(value)
        request = self.context.get("request")

        if "accession" in data:
            data["accession"] = expand_field(data["accession"], Accession, AccessionSerializer, request)
        return data


class MeasurementSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MeasurementSet
        fields = [
            "@id",
            "name",
            "accession",
            "subpoolinrun_set",
        ]
        extra_kwargs = {"accession": {"required": False, "allow_empty": True}}

    def to_representation(self, value):
        data = super().to_representation(value)
        request = self.context.get("request")

        if "accession" in data:
            data["accession"] = expand_field(data["accession"], Accession, AccessionSerializer, request)
        if "subpoolinrun_set" in data:
            data["subpoolinrun_set"] = expand_field(data["subpoolinrun_set"], SubpoolInRun, SubpoolInRunSerializer, request, pkname="id")
        return data


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

    accession = AccessionSerializer(many=True, required=False)
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

    accession = AccessionSerializer(many=True, required=False)
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


class PipelineBiosampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FixedSample
        fields = [
            "@id",
            "tissue_name",
            "dissection_time",
            "tissue_weight_g",
            "tissue_description",
            "ontology_terms",
            "mouse_name",
            "genotype",
        ]

    tissue_name = serializers.CharField(source="tissue.name", read_only=True)
    dissection_time = serializers.DateTimeField(read_only=True)
    tissue_weight_g = serializers.DecimalField(source="tissue.weight_g", max_digits=8, decimal_places=3, min_value=0)
    tissue_description = serializers.CharField(source="tissue.description", read_only=True)
    ontology_terms = serializers.ListField(read_only=True)

    mouse_name = serializers.CharField(source="mouse.name", read_only=True)
    genotype = serializers.CharField(source="mouse.strain.name", read_only=True)


class PipelineMouseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Mouse
        fields = [
            "@id",
            "name",
            "estrus_cycle",
            "date_of_birth",
            "harvest_date",
            "age_days",
            "timepoint_description",
            "sex",
            "body_weight_g",
            "notes",
            "genotype",
        ]

    estrus_cycle = serializers.CharField(source="get_estrus_cycle_display")
    sex = serializers.CharField(source="get_sex_display")
    body_weight_g = serializers.DecimalField(source="weight_g", max_digits=8, decimal_places=3, min_value=0)
    genotype = serializers.CharField(source="strain.name")


class PipelineTissueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tissue
        fields = [
            "@id",
            "name",
            "mouse",
            "description",
            "ontology_term",
            "fixedsample_set",
            "dissection_time",
            "tube_label",
            "tube_weight_g",
            "total_weight_g",
            "weight_mg",
            "dissector",
            "dissection_notes",
            "accession"
        ]

    mouse = PipelineMouseSerializer()
    ontology_term = OntologyTermSerializer(many=True)
    accession = AccessionSerializer(many=True)


class PipelineFixedSampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FixedSample
        fields = [
            "tissue"
        ]

    tissue = PipelineTissueSerializer(many=True)


class PipelineSampleMetadataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SplitSeqWell
        fields = [
            "plate_name",
            "well",
            "row",
            "column",
            "biosample",
            "barcode",
        ]

    plate_name = serializers.CharField(source="plate.name", read_only=True)
    well = serializers.CharField(read_only=True)
    barcode = LibraryBarcodeSerializer(many=True)
    biosample = PipelineFixedSampleSerializer(many=True)
