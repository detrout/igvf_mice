from django.contrib import admin

from .models import (
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
    Sublibrary,
)


class SourceOptions(admin.ModelAdmin):
    model = Source
    list_display = ("name",)


class LibraryConstructionKitOptions(admin.ModelAdmin):
    model = LibraryConstructionKit
    list_display = ("name", "version", "source")


class LibraryBarcodeOptions(admin.ModelAdmin):
    model = LibraryBarcode
    list_display = ("kit", "code", "sequence")


class MouseStrainOptions(admin.ModelAdmin):
    model = MouseStrain
    list_display = ("name", "strain_type")


class MouseOptions(admin.ModelAdmin):
    model = Mouse
    list_display = ("name", "strain", "sex")


class OntologyTermOptions(admin.ModelAdmin):
    model = OntologyTerm
    list_options = ("term_name", "term_uri")


class TissueOptions(admin.ModelAdmin):
    model = Tissue
    list_options = (
        "mouse__name",
        "mouse_tissue_id",
        #"timepoint",
        #"timepoint_units",
    )


class FixedSampleOptions(admin.ModelAdmin):
    model = FixedSample


class SplitSeqPlateOptions(admin.ModelAdmin):
    model = SplitSeqPlate


class SublibraryOptions(admin.ModelAdmin):
    model = Sublibrary


admin.site.register(Source, SourceOptions)
admin.site.register(LibraryConstructionKit, LibraryConstructionKitOptions)
admin.site.register(LibraryBarcode, LibraryBarcodeOptions)
admin.site.register(MouseStrain, MouseStrainOptions)
admin.site.register(Mouse, MouseOptions)
admin.site.register(OntologyTerm, OntologyTermOptions)
admin.site.register(Tissue, TissueOptions)
admin.site.register(FixedSample, FixedSampleOptions)
admin.site.register(SplitSeqPlate, SplitSeqPlateOptions)
admin.site.register(Sublibrary, SublibraryOptions)
