from django.contrib import admin

from .models import (
    AccessionNamespace,
    Accession,
    Source,
    LibraryConstructionKit,
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


class AccessionNamespaceOptions(admin.ModelAdmin):
    model = AccessionNamespace

    list_display = ("name", "prefix", "link")


class AccessionOptions(admin.ModelAdmin):
    model = Accession

    search_fields = ["name"]

    list_display = ("name", "link")


class SourceOptions(admin.ModelAdmin):
    model = Source
    list_display = ("name",)


class LibraryConstructionKitOptions(admin.ModelAdmin):
    model = LibraryConstructionKit
    list_display = ("name", "version", "source")


class LibraryBarcodeOptions(admin.ModelAdmin):
    model = LibraryBarcode
    list_display = ("kit", "name", "code", "sequence")


class MouseStrainOptions(admin.ModelAdmin):
    model = MouseStrain
    list_display = ("name", "strain_type", "jax_catalog_number", "notes")


class MouseOptions(admin.ModelAdmin):
    model = Mouse
    list_display = ("name", "strain", "sex", "date_of_birth", "sample_box")
    list_filter = ("strain", "sex")
    ordering = ("-name",)
    autocomplete_fields = ["accession",]



class OntologyTermOptions(admin.ModelAdmin):
    model = OntologyTerm
    list_display = ("name", "curie_link")


class TissueOptions(admin.ModelAdmin):
    model = Tissue
    list_display = (
        "name",
        "mouse",
        #"timepoint",
        #"timepoint_units",
    )
    filter_horizontal = ["ontology_term","accession"]
    autocomplete_fields = ["accession",]


class FixedSampleOptions(admin.ModelAdmin):
    model = FixedSample

    list_display = (
        "name",
        "tube_label",
        "fixation_name",
        "fixation_date",
    )
    ordering = ("-name",)
    filter_horizontal = ["tissue",]


class SplitSeqPlateOptions(admin.ModelAdmin):
    model = SplitSeqPlate

    list_display = ("name", "total_nuclei", "aliquots_small_used", "aliquots_small_remaining", "aliquots_large_used", "aliquots_large_remaining")


class SplitSeqWellOptions(admin.ModelAdmin):
    model = SplitSeqWell

    filter_horizontal = ["biosample", "barcode"]


class SubpoolOptions(admin.ModelAdmin):
    model = Subpool

    list_display = ("name", "plate", "nuclei", "cdna_pcr_rounds", "cdna_ng_per_ul_in_25ul", "cdna_average_bp_length", "index", "library_ng_per_ul", "library_average_bp_length")
    list_filter = ("plate",)

    fields = (
        ("name", "plate"),
        "nuclei",
        ("cdna_pcr_rounds", "cdna_ng_per_ul_in_25ul"),
        ("bioanalyzer_date", "cdna_average_bp_length"),
        ("library_ng_per_ul", "library_average_bp_length"),
        ("index_pcr_number", "index"),
        ("barcode"),
    )
    filter_horizontal = ["barcode",]


class PlatformOptions(admin.ModelAdmin):
    model = Platform


class SubpoolInRunInline(admin.StackedInline):
    model = SubpoolInRun

    search_fields = "subpool"
    fieldsets = (
        (None, {"fields": (("subpool", "run_date"), ("raw_reads", "status"))}),
        (None, {
            "classes": ("wide",),
            "fields": ("pattern",),
        }),
    )


class SequencingRunOptions(admin.ModelAdmin):
    model = SequencingRun

    list_display = ("name", "platform", "plate")
    list_filter = ("platform", "plate")

    inlines = [SubpoolInRunInline,]

    filter_horizontal = ["accession",]


class SubpoolInRunOptions(admin.ModelAdmin):
    model = SubpoolInRun


class SubpoolInRunFileOptions(admin.ModelAdmin):
    model = SubpoolInRunFile

    list_display = ("filename", "md5sum")

    filter_horizontal = ["accession",]


class MeasurementSetOptions(admin.ModelAdmin):
    model = MeasurementSet

    filter_horizontal = ["accession"]


admin.site.register(AccessionNamespace, AccessionNamespaceOptions)
admin.site.register(Accession, AccessionOptions)
admin.site.register(Source, SourceOptions)
admin.site.register(LibraryConstructionKit, LibraryConstructionKitOptions)
admin.site.register(LibraryBarcode, LibraryBarcodeOptions)
admin.site.register(MouseStrain, MouseStrainOptions)
admin.site.register(Mouse, MouseOptions)
admin.site.register(OntologyTerm, OntologyTermOptions)
admin.site.register(Tissue, TissueOptions)
admin.site.register(FixedSample, FixedSampleOptions)
admin.site.register(SplitSeqPlate, SplitSeqPlateOptions)
admin.site.register(SplitSeqWell, SplitSeqWellOptions)
admin.site.register(Subpool, SubpoolOptions)
admin.site.register(Platform, PlatformOptions)
admin.site.register(SequencingRun, SequencingRunOptions)
admin.site.register(SubpoolInRun, SubpoolInRunOptions)
admin.site.register(SubpoolInRunFile, SubpoolInRunFileOptions)
admin.site.register(MeasurementSet, MeasurementSetOptions)
