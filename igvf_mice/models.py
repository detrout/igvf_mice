from django.contrib import admin
from django.core.exceptions import ValidationError
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
    uuid = models.UUIDField(null=True, blank=True)
    url = models.URLField(
        unique=True,
        help_text="URL to obtain information about the accessioned data item",
    )

    def __str__(self):
        return "{}:{}".format(self.namespace.prefix, self.name)

    @property
    def path(self):
        """Return just the path portion of the url

        This will match IGVF DACC (and ENCODE) @id fields.
        """
        parts = parse.urlsplit(self.url)
        return parts.path

    @admin.display
    def link(self) -> str:
        """Formatted <a href=> for use in pages"""
        return format_html(
            '<a href="{url}">{url}</a>',
            url=self.url,
        )


class Source(models.Model):
    """Entities that produce products used by the project"""

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Name of company or organization providing items",
    )
    homepage = models.URLField(
        null=True, help_text="Home page containing more information about the source"
    )
    igvf_id = models.CharField(
        max_length=255, null=True, help_text="id used by igvf to refer to this source"
    )

    def __str__(self):
        return str(self.name)

    @admin.display
    def link(self):
        """Formatted <a href=> for use in pages"""
        return format_html(
            '<a href="{homepage}">{homepage}</a>',
            homepage=self.homepage,
        )


class LibraryConstructionKit(models.Model):
    """Reference to describe a library construction kit used to make libraries.

    References models:`igvf_mice.Source` to describe who is providing the kit
    """

    name = models.CharField(max_length=255, unique=True, help_text="The product name")
    version = models.CharField(
        max_length=50, help_text="description of the kit version"
    )
    source = models.ForeignKey(
        Source, on_delete=models.PROTECT, help_text="Who is the kit provider"
    )

    def __str__(self):
        return str("{} {}".format(self.name, self.version))


class LibraryBarcode(models.Model):
    """Map adapter types to the multiplex sequence

    Library kits have many different kinds of bar code possible, and
    usually use some kind of short name to reference the genome
    sequence for the barcode.

    This links the :model:`igvf_mice.LibraryConstructionKit` part identifier
    to a name and sequence.
    """

    class Meta:
        ordering = ["kit", "code", "barcode_type"]

    kit = models.ForeignKey(LibraryConstructionKit, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, null=True)
    code = models.CharField(max_length=6, null=False)
    sequence = models.CharField(max_length=16, blank=True, null=True)
    # should be an enum, but need to check with others
    barcode_type = models.CharField(max_length=2, null=True)

    @admin.display
    @property
    def kit_name(self):
        """Helper property to quickly access the kit name property in the admin pages"""
        return self.kit.name

    def __str__(self):
        name = [self.kit_name, self.code, self.sequence]
        if self.barcode_type is not None:
            name.append(self.barcode_type)
        return " ".join(name)


class StrainType(models.TextChoices):
    CC_FOUNDER = ("FO", "CC Founder")
    CC_CROSS = ("CR", "CC Cross")


# This is representing a genetic background
# so like ENCODE model organism or cell line donors
class MouseStrain(models.Model):
    """A particular strain or genetic background of mice

    We order :model:`igvf_mouse.Mouse` from MouseStrains.
    """

    name = models.CharField(max_length=50, unique=True, help_text="Name of mouse type")
    strain_type = models.CharField(
        max_length=2,
        choices=StrainType.choices,
        default=StrainType.CC_FOUNDER,
        help_text="code representing strain type",
    )
    code = models.CharField(
        max_length=50, unique=True, help_text="short mouse strain code"
    )
    jax_catalog_number = models.CharField(
        max_length=255, help_text="order number for the mouse strain type"
    )
    url = models.URLField(null=True, help_text="Information page for mouse")
    # price = models.DecimalField(max_digits=5, decimal_places=2)
    # status = models.EnumField()
    # RMS = what is this, why is it a list of numbers?
    # ordered, do we need a many to many with different order dates?
    # communication with ULAR
    # availability
    notes = models.TextField(
        null=True, help_text="extended information about the mouse strain"
    )
    source = models.ForeignKey(
        "Source", on_delete=models.PROTECT, help_text="source providing the mouse"
    )

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
    """An individual mouse

    A :model:`igvf_mice.Mouse` is a specific mouse of type
    :model:`igvf_mice.MouseStrain` that is then dissected into
    :model:`igvf_mice.Tissue`
    """

    class Meta:
        verbose_name_plural = "mice"

    def __str__(self):
        return self.name

    name = models.CharField(max_length=50, unique=True, help_text="individual mouse id")
    strain = models.ForeignKey(
        MouseStrain, on_delete=models.PROTECT, help_text="strain type for mouse"
    )
    sex = models.CharField(
        max_length=1,
        choices=SexEnum.choices,
        default=SexEnum.UNKNOWN,
        help_text="sex of mouse, if known",
    )
    weight_g = models.FloatField(null=True, verbose_name="weight (grams)")
    date_of_birth = models.DateField(null=True, help_text="Date mouse was born")
    date_obtained = models.DateField(null=True, help_text="Date mouse was received")
    harvest_date = models.DateField(
        null=True, help_text="Date of dissection started"
    )
    estrus_cycle = models.CharField(
        max_length=2,
        choices=EstrusCycle.choices,
        default=None,
        null=True,
        blank=True,
        help_text="State of estrus cycle if applicable",
    )
    # should this be a list of users instead?
    operator = models.CharField(
        max_length=50,
        blank=True,
        help_text="Identifying information for person or team doing the dissection",
    )
    notes = models.TextField(blank=True, help_text="extended information about mouse")
    sample_box = models.CharField(
        max_length=10, blank=True, help_text="storage identifier"
    )
    accession = models.ManyToManyField(
        Accession, help_text="external IDs assigned to this mouse"
    )

    @property
    def age_days(self):
        """Calculated age, dissection date - date of birth"""
        return self.harvest_date - self.date_of_birth

    @property
    def source(self):
        """Helper to return mouse strain source"""
        return self.strain.source


# What if we made django-bioontology?
# How do we track prefixes?
class OntologyTerm(models.Model):
    """Ontology terms captured by the IGVF DACC.

    They import terms from many other sources like UBERON or OBI, but
    they also sometimes define their own term ids for attributes not
    in the public ontologies. We need to be able to link our samples
    to DACC terms.

    :model:`igvf_mice.Tissue` objects are annotated with the
    OntologyTerms.
    """

    # The term IDs are typically CURIEs
    # https://www.w3.org/TR/2010/NOTE-curie-20101216/
    # And we should have some way of validating the prefix
    # and maybe rewriting them to be URLs.
    curie = models.CharField(
        max_length=255, primary_key=True, help_text="short ID used by IGVF DACC"
    )
    name = models.CharField(max_length=255, help_text="short human readable label")
    description = models.TextField(null=True, help_text="longer description for term")

    def __str__(self):
        return "{} ({})".format(self.curie, self.name)

    @property
    def url(self):
        safe_curie = self.curie.replace(":", "_")
        return parse.urljoin("https://data.igvf.org/sample-terms/", safe_curie)

    @admin.display
    def link(self):
        """Formatted <a href=> for display in pages"""
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


def require_3_underscores(value):
    if isinstance(value, str):
        underscores = 0
        for c in value:
            if c == "_":
                underscores += 1

        if underscores != 3:
            raise ValidationError("Wrong number of underscores {}. Expected 3".format(underscores))

# this is closest to being a tissue specific biosample object
class Tissue(models.Model):
    """Track a tissue or tissues dissected from a mouse as one unit

    Usually it's a single tissue but occasionally it's easier to
    dissect several tissues together.

    A :model:`igvf_mice.Mouse` is dissected into several
    :model:`igvf_mice.Tissue` objects after, the Tissue objects are
    disassociated into :model:`igvf_mice.FixedSample`
    """

    # This is heavily inspired by Samples - 8 founders tab
    # this might need to split into tissue & extract?
    class Meta:
        ordering = ["name"]

    mouse = models.ForeignKey(Mouse, on_delete=models.PROTECT)
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="human friendly unique identifier for tissue",
        validators=[require_3_underscores],
    )
    # this should be a friendly name of whats in represented by ontology many to many
    description = models.CharField(
        max_length=75, help_text="description of type or types of tissue"
    )
    # should be many to many, as one dissection may have multiple tissues
    ontology_term = models.ManyToManyField(
        OntologyTerm,
        help_text="Links to ontology terms that describe this tissue or set of tissues",
    )
    dissection_time = models.DateTimeField(
        default=timezone.now, help_text="when did disection happen"
    )
    timepoint_description = models.CharField(
        max_length=20,
        null=True,
        help_text="Description of intended time point to group by"
    )
    life_stage = models.CharField(
        max_length=2,
        choices=LifeStageEnum.choices,
        default=LifeStageEnum.POST_NATAL,
        help_text="broad life stage of mouse",
    )
    # We have the age on the mouse object.
    # But in the spreadsheet this was used to group samples
    # age = models.FloatField()
    # age_units = models.CharField(
    #    max_length=1, choices=AgeUnitsEnum.choices, default=AgeUnitsEnum.WEEK
    # )
    # tissue_weight = models.FloatField()
    tube_label = models.CharField(
        max_length=50, help_text="human identifier for tube containing sample"
    )
    tube_weight_g = models.FloatField(null=True, verbose_name="tube weight (grams)")
    total_weight_g = models.FloatField(null=True, verbose_name="total weight (grams)")
    dissector = models.CharField(
        max_length=40, null=True, help_text="Identifier for person doing disection"
    )
    dissection_notes = models.TextField(
        null=True, help_text="Qualitative information about diesections"
    )
    accession = models.ManyToManyField(
        Accession, help_text="Accession IDs assigned to this sample"
    )

    @property
    def weight_g(self):
        """Calculate weight of tissue from final and initial tube weights"""
        if not (self.tube_weight_g is None or self.total_weight_g is None):
            return self.total_weight_g - self.tube_weight_g

    @property
    def weight_mg(self):
        """Convert weight calculated in grams to miligrams rounded to 3 decimals"""
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
        """Comma separated list of ontology term names"""
        return ", ".join((x.name for x in self.ontology_term.all()))

    def __str__(self):
        return "{} {}".format(self.name, self.description)


class FixedSample(models.Model):
    """Samples whose cells/nuclei have that have been disassociated

    The next step for a :model:`igvf_mice.Tissue` sample is for it to
    be disassociated, fixed, and placed into various aliquots sized
    for being placed into :model:`igvf_mice.SplitSeqWell` associated with
    a :model:`igvf_mice.SplitSeqPlate`.
    """

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
    """a plate of wells used to start labeling nuclei.

    A plate contains many :model:`igvf_mice.SplitSeqWell` objects that
    are linked to :model:`igvf_mice.FixedSample` objects.

    We track when and by whom a plate was built, and then how many
    aliquots were made from this reaction.

    Aliquots are normally produced containing 8,000 or 67,000 cells
    which are tracked here as small or large aliquots. To allow for
    some variation, the size threshold used is 10,000 cells.

    The aliquots are then labeled with the illumina multiplexing
    adapters and turned into :model:`igvf_mice.Subpool`

    """

    # ideally the UI for this would look like a plate.
    # with 96 wells to start with
    name = models.CharField(
        max_length=20, unique=True, help_text="Human friendly name for this plate run"
    )
    size = models.SmallIntegerField(
        default=PlateSizeEnum.size_96,
        choices=PlateSizeEnum.choices,
        help_text="In case they ever use a different sized plate",
    )
    # this could turn into a list of locations?
    pool_location = models.CharField(
        max_length=50,
        null=True,
        help_text="Information to help find any remaining pooled sample",
    )
    date_performed = models.DateField(default=timezone.now, null=True)
    barcoded_cell_counter = models.IntegerField(null=True)
    volume_of_nuclei = models.IntegerField(null=True)

    def __str__(self):
        return self.name

    @property
    def total_nuclei(self):
        """Compute the number of nuclei from the cell count and volume"""
        if self.barcoded_cell_counter is None or self.volume_of_nuclei is None:
            return None
        else:
            return self.barcoded_cell_counter * self.volume_of_nuclei



#   H (96 well plate)
#   P (384 well plate)
well_rows = [
    ("{}".format(chr(x)), "{}".format(chr(x))) for x in range(ord("A"), ord("I"))
]

# [ 1, 24 ] for 384 well plate
# [ 1, 12 ] for 96 well plate
well_columns = [("{}".format(x), "{}".format(x)) for x in range(1, 13)]


class SplitSeqWell(models.Model):
    """A well that samples are placed into that will be labeled

    A :model:`igvf_mice.SplitSeqWell` contains
    :model:`igvf_mice.FixedSample` that will be labeled with a known
    barcode and then two rounds of random barcode.

    Eventually all the wells will poured into a pool will be stored in
    aliquots which is represented by the
    model:`igvf_mice.SplitSeqPlate`

    """

    plate = models.ForeignKey("SplitSeqPlate", on_delete=models.PROTECT)
    row = models.CharField(max_length=2, choices=well_rows)
    column = models.CharField(max_length=2, choices=well_columns)

    # what sequence tells us what the the starting sample?
    # Sina had index7, index5 fields
    # should we be tracking the parse protocol here?

    biosample = models.ManyToManyField(FixedSample)

    barcode_filter = models.Q(barcode_type="R") | models.Q(barcode_type="T")
    barcode = models.ManyToManyField(
        LibraryBarcode,
        limit_choices_to=barcode_filter,
    )

    def __str__(self):
        return "{} {}{}".format(self.plate.name, self.row, self.column)


class SublibrarySelectionType(models.TextChoices):
    no_selection = ("NO", "No selection done")
    exome_capture = ("EX", "Exome capture")


class Subpool(models.Model):
    """aloquots of cells that have had an illumina multiplexing barcode added.

    :model:`igvf_mice.Subpool` objects are made after one of the 16
    available illumina multiplex barcodes are added to the aliquots stored from
    when the :model:`igvf_mice.SplitSeqPlate` was built.

    Subpools can be sequenced via multiple
    :model:`igvf_mice.SequencingRun` producing several
    :model:`igvf_mice.SubpoolInRun` objects linking
    :model:`igvf_mice.SubpoolInRunFile` items to their source subpools
    and runs.
    """

    name = models.CharField(max_length=50, unique=True)
    plate = models.ForeignKey("SplitSeqPlate", on_delete=models.PROTECT)
    nuclei = models.IntegerField()
    selection_type = models.CharField(
        max_length=2,
        choices=SublibrarySelectionType.choices,
        default=SublibrarySelectionType.no_selection
    )
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

    accession = models.ManyToManyField(Accession)
    # Where should QC & production run information go?

    # given what we know about the split seq barcodes and the sequencing
    # information can generate a seqspec record?
    @admin.display
    def plate_name(self):
        """Helper to return the SplitSeqPlate name in admin pages"""
        return self.plate.name

    def __str__(self):
        return self.name


class Platform(models.Model):
    """List of possible sequencing platforms"""

    name = models.CharField(
        max_length=20, unique=True, help_text="short unique code for the sequencer"
    )
    igvf_id = models.CharField(
        max_length=255, null=True, help_text="id used by igvf to refer to this platform"
    )
    display_name = models.CharField(
        max_length=100, help_text="friendly name for the sequencer"
    )
    family = models.CharField(
        max_length=100,
        help_text="term to group sufficiently similar platforms. Such as treating the different Illumina machines",
    )
    source = models.ForeignKey(
        Source,
        on_delete=models.PROTECT,
        help_text="Describe who the source is for the sequencing platform.",
        null=True
    )

    def __str__(self):
        return self.display_name


class Stranded(models.TextChoices):
    FORWARD = ("F", "Forward")
    REVERSE = ("R", "Reverse")
    UNSTRANDED = ("U", "Unstranded")


class SequencingRun(models.Model):
    """Record information about a sequencer run.

    One :model:`igvf_mice.SplitSeqPlate` will be run run on several
    different SequencingRuns, to take advantage of different
    sequencing :model:`igvf_mice.Platform` strengths and weakeness, as
    well as trying to meet coverage requirements for our experiments.

    we group experiments by :model:`igvf_mice.SplitSeqPlate` so we
    link to that table here.

    """

    name = models.CharField(max_length=50, unique=True)
    run_date = models.DateField(null=True)
    platform = models.ForeignKey(Platform, on_delete=models.PROTECT)
    plate = models.ForeignKey(SplitSeqPlate, on_delete=models.PROTECT)
    stranded = models.CharField(
        max_length=1, choices=Stranded.choices, default=Stranded.REVERSE
    )

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
    """Link Subpools to Sequencing runs

    Since a sequencing run can contain many subpools, this table links
    :model:`igvf_mice.Subpool` to the :model:`igvf_mice.SequencingRun`
    it was run on.

    The result of a sequencing run is a collection of files which are
    tracked as model:`igvf_mice.SubpoolInRunFile`.

    Individual subpools may not perform well on a run so we have a
    status field.

    Eventually all of the subpools from with the same logical set of
    barcodes are submitted to the DACC as a
    :model:`igvf_mice.MeasurementSet`.

    """

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
    """Describes a file produced by a SequencingRun

    Since the :model:`igvf_mice.Subpool` objects are described by an Illumina barcode the
    resulting fastq files will usually be demultiplexed by the Subpool id.

    For Illumina style reads there were usually be paired ends, and
    there may be multiple lanes or fragments that need to be grouped together.

    Eventually the files will be uploaded to a repository and receive
    :model:`igvf_mice.Accession` IDs.

    """

    subpool_run = models.ForeignKey(SubpoolInRun, on_delete=models.PROTECT)
    md5sum = models.CharField(max_length=32, null=True, blank=False)
    filename = models.CharField(max_length=255, null=False, blank=False)
    flowcell_id = models.CharField(max_length=100, null=False, blank=False)
    lane = models.IntegerField(null=True)
    read = models.CharField(max_length=4, null=True, blank=False)
    accession = models.ManyToManyField(Accession)

    def __str__(self):
        return self.filename


class MeasurementSet(models.Model):
    """Describes a set of files that can be processed together.

    a measurement_set is an concept by the IGVF DACC to group a set of
    sequence_data files that were submitted and can be processed
    together. It links the files to the source biosample objects.

    For us, a :model:`igvf_mice.MeasurementSet` is a one to many
    relationship for :model:`igvf_mice.SubpoolInRun` objects.

    """

    name = models.CharField(max_length=50, unique=True)
    accession = models.ManyToManyField(Accession)

    def __str__(self):
        return self.name
