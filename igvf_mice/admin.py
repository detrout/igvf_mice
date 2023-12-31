from django.contrib import admin

from .models import (
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


class AccessionOptions(admin.ModelAdmin):
    model = Accession

    search_fields = ["name"]

    list_display = ("name", "link")


class SourceOptions(admin.ModelAdmin):
    model = Source
    list_display = ("name",)


class LibraryConstructionReagentOptions(admin.ModelAdmin):
    model = LibraryConstructionReagent
    list_display = ("name", "version", "source")


class LibraryBarcodeOptions(admin.ModelAdmin):
    model = LibraryBarcode
    list_display = ("reagent", "name", "code", "i7_sequence", "i5_sequence")
    search_fields = ("code", "i7_sequence", "i5_sequence")


class MouseStrainOptions(admin.ModelAdmin):
    model = MouseStrain
    list_display = ("name", "strain_type", "jax_catalog_number", "notes")


class MouseOptions(admin.ModelAdmin):
    model = Mouse
    list_display = ("name", "strain", "sex", "date_of_birth", "housing_number")
    list_filter = ("strain", "sex")
    ordering = ("-name",)
    fields = (
        ("name", "strain"),
        ("housing_number", "date_obtained"),
        ("weight_g", "sex", "estrus_cycle"),
        ("date_of_birth", "harvest_date"),
        ("timepoint_description", "life_stage"),
        ("operator"),
        ("notes"),
        ("accession"),
    )

    autocomplete_fields = ["accession",]


class OntologyTermOptions(admin.ModelAdmin):
    model = OntologyTerm
    list_display = ("name", "link")
    search_fields = ("name",)


class TissueOptions(admin.ModelAdmin):
    model = Tissue
    list_display = (
        "name",
        "mouse",
        #"timepoint",
        #"timepoint_units",
    )
    fields = (
        ("name", "mouse"),
        "dissection_time",
        "description",
        "ontology_term",
        ("tube_label", "tube_weight_g", "total_weight_g"),
        "dissector",
        "dissection_notes",
        "accession",
    )
    #filter_horizontal = ["ontology_term",]
    autocomplete_fields = ["ontology_term", "accession",]


class FixedSampleOptions(admin.ModelAdmin):
    model = FixedSample

    search_fields = ("name",)
    list_display = (
        "name",
        "tube_label",
        "fixation_name",
        "fixation_date",
    )
    ordering = ("-name",)

    fields = (
        ("name", "tube_label"),
        ("fixation_name", "fixation_date"),
        ("starting_nuclei", "nuclei_into_fixation", "fixed_nuclei"),
        ("aliquots_made", "aliquot_volume_ul"),
        "tissue",
    )

    filter_horizontal = ["tissue",]


class SplitSeqWellInline(admin.StackedInline):
    model = SplitSeqWell

    autocomplete_fields = ["biosample", "barcode"]
    #filter_horizontal = [
    #    "biosample",
    #    "barcode"
    #]

    fields = (
        ("row", "column"),
        ("biosample", "barcode",),
    )


class SplitSeqPlateOptions(admin.ModelAdmin):
    model = SplitSeqPlate

    list_display = (
        "name",
        "total_nuclei",
    )

    fields = (
        ("name", "pool_location"),
        ("date_performed", "barcoded_cell_counter", "volume_of_nuclei"),
    )

    inlines = [SplitSeqWellInline,]


class SplitSeqWellOptions(admin.ModelAdmin):
    model = SplitSeqWell

    fields = (
        ("plate", "row", "column"),
        "biosample",
        "barcode",
    )

    list_filter = ["plate__name"]
    filter_horizontal = ["biosample", "barcode"]


class SubpoolOptions(admin.ModelAdmin):
    model = Subpool

    list_display = ("name", "plate", "nuclei", "cdna_pcr_rounds", "cdna_ng_per_ul", "cdna_volume", "cdna_average_bp_length", "index", "library_ng_per_ul", "library_average_bp_length")
    list_filter = ("plate",)

    fields = (
        ("name", "plate"),
        "nuclei",
        ("cdna_pcr_rounds", "cdna_ng_per_ul", "cdna_volume"),
        ("bioanalyzer_date", "cdna_average_bp_length"),
        ("library_ng_per_ul", "library_average_bp_length"),
        ("index_pcr_number", "index"),
        ("barcode"),
        ("accession"),
    )
    filter_horizontal = ["barcode",]
    autocomplete_fields = ["accession",]


class PlatformOptions(admin.ModelAdmin):
    model = Platform


class SubpoolInRunInline(admin.StackedInline):
    model = SubpoolInRun

    search_fields = "subpool"
    fields = (
        ("subpool", "status", "measurement_set"),
    )


class SequencingRunOptions(admin.ModelAdmin):
    model = SequencingRun

    list_display = ("name", "platform", "plate")
    list_filter = ("platform", "plate")

    fields = (
        ("name", "plate"),
        ("platform", "run_date", "stranded"),
    )
    inlines = [SubpoolInRunInline,]


class SubpoolInRunOptions(admin.ModelAdmin):
    model = SubpoolInRun

    list_filter = ("subpool__plate",)
    list_display = ("subpool", "status", "measurement_set")


class SubpoolInRunFileOptions(admin.ModelAdmin):
    model = SubpoolInRunFile

    list_display = ("filename", "md5sum", "subpool_run")
    list_filter = ("subpool_run__sequencing_run",)

    autocomplete_fields = ["accession",]


class MeasurementSetOptions(admin.ModelAdmin):
    model = MeasurementSet

    filter_horizontal = ["accession"]


admin.site.register(Accession, AccessionOptions)
admin.site.register(Source, SourceOptions)
admin.site.register(LibraryConstructionReagent, LibraryConstructionReagentOptions)
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
