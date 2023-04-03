from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.utils.html import format_html

from urllib import parse

import numpy


class AccessionNamespace(models.Model):
    """Describe a potential source of accession ids."""

    name = models.CharField(
        max_length=255, unique=True, help_text="name usually used for the entity."
    )
    homepage = models.URLField(null=True, help_text="home page URL for entity")
    accession_prefix = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        help_text="identifying prefix added to accessions when being displayed in lists",
    )

    def __str__(self):
        return self.name

    @property
    def prefix(self):
        if self.accession_prefix is not None:
            return self.accession_prefix
        else:
            return self.name.replace(" ", "_")

    @admin.display
    def link(self):
        return format_html(
            '<a href="{homepage}">{homepage}</a>',
            homepage=self.homepage,
        )


class Accession(models.Model):
    """An accession ID name and what url it expands to

    Refers to :model:`igvf_mice.AccessionNamespace` to define valid
    namespaces
    """
    namespace = models.ForeignKey(AccessionNamespace, on_delete=models.PROTECT)
    name = models.CharField(max_length=255, help_text="Accession ID")
    url = models.URLField(unique=True, help_text="URL to obtain information about the accessioned data item")

    def __str__(self):
        return "{}:{}".format(self.namespace.prefix, self.name)

    @property
    def path(self):
        parts = parse.urlsplit(self.url)
        return parts.path

    @admin.display
    def link(self):
        return format_html(
            '<a href="{url}">{url}</a>',
            url=self.url,
        )


class Source(models.Model):
    """Entities that produce products used by the project
    """

    name = models.CharField(max_length=255, unique=True, help_text="Name of company or organization providing items")
    homepage = models.URLField(null=True, help_text="Home page containing more information about the source")
    igvf_id = models.CharField(max_length=255, null=True, help_text="id used by igvf to refer to this source")

    def __str__(self):
        return str(self.name)

    @admin.display
    def link(self):
        return format_html(
            '<a href="{homepage}">{homepage}</a>',
            url=self.url,
        )


class LibraryConstructionKit(models.Model):
    """Reference to describe a library construction kit used to make libraries.

    References models:`igvf_mice.Source` to describe who is providing the kit 
    """
    name = models.CharField(max_length=255, unique=True, help_text="The products name")
    version = models.CharField(max_length=50, help_text="description of the kit version")
    source = models.ForeignKey(Source, on_delete=models.PROTECT)

    def __str__(self):
        return str("{} {}".format(self.name, self.version))


class LibraryBarcode(models.Model):
    """Map adapter types to the multiplex sequence"""

    kit = models.ForeignKey(LibraryConstructionKit, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, null=True)
    code = models.CharField(max_length=6, null=False)
    sequence = models.CharField(max_length=16, blank=True, null=True)
    # should be an enum, but need to check with others
    barcode_type = models.CharField(max_length=2, null=True)

    @admin.display
    @property
    def kit_name(self):
        return self.kit.name

    def __str__(self):
        return "{} {} {}".format(self.kit_name, self.code, self.sequence)


class StrainType(models.TextChoices):
    CC_FOUNDER = ("FO", "CC Founder")
    CC_CROSS = ("CR", "CC Cross")


# This is representing a genetic background
# so like ENCODE model organism or cell line donors
class MouseStrain(models.Model):
    name = models.CharField(max_length=50, unique=True)
    strain_type = models.CharField(
        max_length=2, choices=StrainType.choices, default=StrainType.CC_FOUNDER
    )
    code = models.CharField(max_length=50, unique=True)
    jax_catalog_number = models.CharField(max_length=255)
    url = models.URLField(null=True)
    # price = models.DecimalField(max_digits=5, decimal_places=2)
    # status = models.EnumField()
    # RMS = what is this, why is it a list of numbers?
    # ordered, do we need a many to many with different order dates?
    # communication with ULAR
    # availability
    notes = models.TextField(null=True)
    source = models.ForeignKey("Source", on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class SexEnum(models.TextChoices):
    MALE = ("M", "male")
    FEMALE = ("F", "female")
    UNKNOWN = ("U", "unknown")
    OTHER = ("O", "other")


class EstrusCycle(models.TextChoices):
    UNKNOWN = ("U", "Unknown")
    ANESTRUS = ("A", "Anestrus")
    ANESTRUS_PROESTRUS = ("AP", "Anestrus>Proestrus")
    PROESTRUS = ("P", "Proestrus")
    PROESTRUS_ESTRUS = ("PE", "Proestrus>Estrus")
    ESTRUS = ("E", "Estrus")
    ESTRUS_METESTRUS = ("EM", "Estrus>Metestrus")
    METESTRUS = ("M", "Metestrus")
    METESTRUS_DIESTRUS = ("MD", "Metestrus>Diestrus")
    DIESTRUS = ("D", "Diestrus")
    DIESTRUS_PROESTRUS = ("DP", "Diestrus>Proestrus")


# this represents an individual donor
class Mouse(models.Model):
    class Meta:
        verbose_name_plural = "mice"

    def __str__(self):
        return self.name

    name = models.CharField(max_length=50, unique=True)
    strain = models.ForeignKey(MouseStrain, on_delete=models.PROTECT)
    sex = models.CharField(
        max_length=1, choices=SexEnum.choices, default=SexEnum.UNKNOWN
    )
    weight_g = models.FloatField(null=True, verbose_name="weight (grams)")
    date_of_birth = models.DateField(null=True)
    date_obtained = models.DateField(null=True)
    harvest_start_time = models.DateTimeField(null=True)
    harvest_end_time = models.DateTimeField(null=True)
    estrus_cycle = models.CharField(
        max_length=2, choices=EstrusCycle.choices, default=None, null=True
    )
    # should this be a list of users instead?
    operator = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    sample_box = models.CharField(max_length=10, blank=True)
    accession = models.ManyToManyField(Accession)

    @property
    def age_days(self):
        return self.harvest_start_time.date() - self.date_of_birth

    @property
    def source(self):
        return self.strain.source


# What if we made django-bioontology?
# How do we track prefixes?
class OntologyTerm(models.Model):
    # The term IDs are typically CURIEs
    # https://www.w3.org/TR/2010/NOTE-curie-20101216/
    # And we should have some way of validating the prefix
    # and maybe rewriting them to be URLs.
    curie = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True)

    def __str__(self):
        return "{} ({})".format(self.curie, self.name)

    @property
    def url(self):
        safe_curie = self.curie.replace(":", "_")
        return parse.urljoin("https://data.igvf.org/sample-terms/", safe_curie)

    @admin.display
    def curie_link(self):
        return format_html(
            '<a href="{url}">{curie}</a>',
            url=self.url,
            curie=self.curie,
        )


class AgeUnitsEnum(models.TextChoices):
    DAY = ("d", "day")
    WEEK = ("w", "week")
    MONTH = ("m", "month")
    YEAR = ("y", "year")


class LifeStageEnum(models.TextChoices):
    EMBRYONIC = ("EM", "embryonic")
    POST_NATAL = ("PN", "post-natal")
    ADULT = ("A", "adult")


# this is closest to being a tissue specific biosample object
class Tissue(models.Model):
    # This is heavily inspired by Samples - 8 founders tab
    # this might need to split into tissue & extract?

    mouse = models.ForeignKey(Mouse, on_delete=models.PROTECT)
    name = models.CharField(max_length=50, unique=True)
    # this should be a friendly name of whats in represented by ontology many to many
    description = models.CharField(max_length=75)
    # should be many to many, as one dissection may have multiple tissues
    ontology_term = models.ManyToManyField(OntologyTerm)
    dissection_time = models.DateTimeField(default=timezone.now)
    life_stage = models.CharField(
        max_length=2, choices=LifeStageEnum.choices, default=LifeStageEnum.POST_NATAL
    )
    # We have the age on the mouse object.
    # But in the spreadsheet this was used to group samples
    # age = models.FloatField()
    # age_units = models.CharField(
    #    max_length=1, choices=AgeUnitsEnum.choices, default=AgeUnitsEnum.WEEK
    # )
    # tissue_weight = models.FloatField()
    tube_label = models.CharField(max_length=50)
    tube_weight_g = models.FloatField(null=True, verbose_name="tube weight (grams)")
    total_weight_g = models.FloatField(null=True, verbose_name="total weight (grams)")
    dissector = models.CharField(max_length=10, null=True)
    dissection_notes = models.TextField(null=True)
    accession = models.ManyToManyField(Accession)

    @property
    def weight_g(self):
        if not (self.tube_weight_g is None or self.total_weight_g is None):
            return self.total_weight_g - self.tube_weight_g

    @property
    def weight_mg(self):
        precision = 3
        weight = self.weight_g
        if weight is None:
            return weight
        else:
            # the total weights in grams frequently lead to slight numeric
            # instability like 231.99999999999997.
            return numpy.round(weight * 1000, precision)

    @property
    def ontology_names(self):
        return ", ".join((x.name for x in self.ontology_term.all()))

    def __str__(self):
        return "{} {}".format(self.name, self.description)


class FixedSample(models.Model):
    name = models.CharField(max_length=50, unique=True)
    tube_label = models.CharField(max_length=20, unique=True)
    fixation_name = models.CharField(max_length=20)
    fixation_date = models.DateField(null=True)
    tissue = models.ManyToManyField("Tissue")
    starting_nuclei = models.FloatField(null=True)
    nuclei_into_fixation = models.FloatField(null=True)
    fixed_nuclei = models.FloatField(null=True)
    aliquots_made = models.IntegerField(null=True)
    aliquot_volume_ul = models.FloatField(null=True)

    def __str__(self):
        return self.name


class PlateSizeEnum(models.TextChoices):
    size_96 = (96, "96")
    size_384 = (384, "384")


class SplitSeqPlate(models.Model):
    # ideally the UI for this would look like a plate.
    # with 96 wells to start with
    name = models.CharField(max_length=20, unique=True)
    size = models.SmallIntegerField(
        default=PlateSizeEnum.size_96, choices=PlateSizeEnum.choices
    )
    # this could turn into a list of locations?
    pool_location = models.CharField(max_length=50, null=True)
    date_performed = models.DateTimeField(default=timezone.now, null=True)
    barcoded_cell_counter = models.IntegerField(null=True)
    volume_of_nuclei = models.IntegerField(null=True)
    aliquots_small_made = models.IntegerField(null=True)
    aliquots_large_made = models.IntegerField(null=True)

    def __str__(self):
        return self.name

    @property
    def total_nuclei(self):
        if self.barcoded_cell_counter is None or self.volume_of_nuclei is None:
            return None
        else:
            return self.barcoded_cell_counter * self.volume_of_nuclei

    @property
    def aliquots_small_used(self):
        return len(self.sublibrary_set.filter(nuclei__lt=10000))

    @property
    def aliquots_large_used(self):
        return len(self.sublibrary_set.filter(nuclei__gt=10000))

    @property
    def aliquots_small_remaining(self):
        return self.aliquots_small_made - self.aliquots_small_used

    def aliquots_large_remaining(self):
        return self.aliquots_large_made - self.aliquots_large_used


#   H (96 well plate)
#   P (384 well plate)
well_rows = [
    ("{}".format(chr(x)), "{}".format(chr(x))) for x in range(ord("A"), ord("I"))
]

# [ 1, 24 ] for 384 well plate
# [ 1, 12 ] for 96 well plate
well_columns = [("{}".format(x), "{}".format(x)) for x in range(1, 13)]


class SplitSeqWell(models.Model):
    plate = models.ForeignKey("SplitSeqPlate", on_delete=models.PROTECT)
    row = models.CharField(max_length=2, choices=well_rows)
    column = models.CharField(max_length=2, choices=well_columns)

    # what sequence tells us what the the starting sample?
    # Sina had index7, index5 fields
    # should we be tracking the parse protocol here?

    biosample = models.ManyToManyField(FixedSample)
    barcode = models.ManyToManyField(
        LibraryBarcode,
        limit_choices_to={"barcode_type": ["T", "R"]},
    )

    def __str__(self):
        return "{} {}{}".format(self.plate.name, self.row, self.column)


class Subpool(models.Model):
    """aloquots of cells from the pooled barcoded plate of samples

    A Cellular subpool
    """

    name = models.CharField(max_length=50, unique=True)
    plate = models.ForeignKey("SplitSeqPlate", on_delete=models.PROTECT)
    nuclei = models.IntegerField()
    cdna_pcr_rounds = models.CharField(max_length=50, null=True)
    cdna_ng_per_ul_in_25ul = models.FloatField(null=True)

    bioanalyzer_date = models.DateField(null=True)
    cdna_average_bp_length = models.IntegerField(null=True)
    index_pcr_number = models.IntegerField(null=True)
    index = models.IntegerField(null=True)

    barcode = models.ManyToManyField(
        LibraryBarcode,
        limit_choices_to={"barcode_type": None},
    )

    library_ng_per_ul = models.FloatField(null=True)
    library_average_bp_length = models.IntegerField(null=True)

    # Where should QC & production run information go?

    # given what we know about the split seq barcodes and the sequencing
    # information can generate a seqspec record?
    @admin.display
    def plate_name(self):
        return self.plate.name

    def __str__(self):
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=20, unique=True)
    display_name = models.CharField(max_length=100)
    family = models.CharField(max_length=100)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)

    def __str__(self):
        if self.display_name is not None:
            return self.display_name
        else:
            return self.name


class Stranded(models.TextChoices):
    FORWARD = ("F", "Forward")
    REVERSE = ("R", "Reverse")
    UNSTRANDED = ("U", "Unstranded")


class SequencingRun(models.Model):
    name = models.CharField(max_length=50, unique=True)
    run_date = models.DateField(null=True)
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT)
    plate = models.ForeignKey(SplitSeqPlate, on_delete=models.PROTECT)
    stranded = models.CharField(
        max_length=1, choices=Stranded.choices, default=Stranded.REVERSE
    )
    accession = models.ManyToManyField(Accession)

    def __str__(self):
        return self.name

    @admin.display
    @property
    def platform_name(self):
        return self.platform.name

    @admin.display
    @property
    def plate_name(self):
        return self.plate.name


class RunStatus(models.TextChoices):
    PASS = ("P", "Pass")
    CAUTION = ("C", "Caution")
    FAILED = ("F", "Failed")


class SubpoolInRun(models.Model):
    subpool = models.ForeignKey(
        Subpool,
        on_delete=models.PROTECT,
    )
    sequencing_run = models.ForeignKey(SequencingRun, on_delete=models.PROTECT)
    raw_reads = models.IntegerField(null=True)
    status = models.CharField(max_length=1, choices=RunStatus.choices, null=True)
    measurement_set = models.ForeignKey(
        "MeasurementSet", on_delete=models.PROTECT, null=True
    )

    def __str__(self):
        return "{} {}".format(self.subpool.name, self.sequencing_run.name)


class SubpoolInRunFile(models.Model):
    subpool_run = models.ForeignKey(SubpoolInRun, on_delete=models.PROTECT)
    md5sum = models.CharField(max_length=32, null=True, blank=False)
    filename = models.CharField(max_length=255, null=True, blank=False)
    # lane = models.CharField(max_length=10, null=True, blank=False)
    lane = models.IntegerField(null=True)
    # fragment = models.CharField(max_length=10, null=True, blank=False)
    fragment = models.IntegerField(null=True)
    read = models.CharField(max_length=4, null=True, blank=False)
    accession = models.ManyToManyField(Accession)

    def __str__(self):
        return self.filename


class MeasurementSet(models.Model):
    name = models.CharField(max_length=50, unique=True)
    accession = models.ManyToManyField(Accession)

    def __str__(self):
        return self.name
