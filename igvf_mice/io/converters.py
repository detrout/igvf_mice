"""Cast pandas values to django database semantics

The way that pandas and django represent missing data needs a bits of
conversion.
"""
from collections import namedtuple
from collections.abc import Sequence
import datetime
import pandas
import zoneinfo

from .. import models
from .validators import validate_mouse_age_sex


def date_or_none(x):
    if pandas.isnull(x):
        return None
    elif x in ("-",):
        return None
    elif isinstance(x, (datetime.datetime, datetime.date)):
        return x.date()
    else:
        return x


def datetime_or_none(x):
    if pandas.isnull(x):
        return None
    elif x in ("-",):
        return None
    elif isinstance(x, datetime.datetime):
        return x
    else:
        return x


def float_or_none(x):
    if pandas.isnull(x):
        return None
    elif x in ("N/A", "-",):
        return None
    else:
        return float(x)

    
def int_or_none(x):
    if x in ("N/A", "#DIV/0!", "#VALUE!", "-"):
        return None
    elif pandas.isnull(x):
        return None
    else:
        return int(x)


def positive_int_or_none(x):
    if x in ("N/A", "#DIV/0!", "#VALUE!", "-"):
        return None
    elif pandas.isnull(x):
        return None
    else:
        x = int(x)
        if x < 0:
            return None
        else:
            return x

    
def int_or_0(x):
    if pandas.isnull(x):
        return 0
    else:
        return int(x)


def str_or_empty(x):
    if pandas.isnull(x):
        return ""
    else:
        return x


def str_or_none(x):
    if pandas.isnull(x):
        return None
    else:
        return x
    

def normalize_barcode_index(value):
    if isinstance(value, str):
        if value.startswith("UDI_WT_"):
            return "UDI{}".format(value[len("UDI_WT_"):])

    return value


def normalize_plate_name(name):
    name = name.upper()

    return name


genotype_to_strain = {
    "129S1/SvImJ": "129S1J",
    "B6129SF1/J": "B6129S1F1J",
    "B6CASTF1/J": "B6CASTF1J",
    "B6NODF1/J": "B6NODF1J",
    "B6PWKF1/J": "B6PWKF1J",
    "B6WSBF1/J": "B6WSBF1J",
    "CAST/EiJ": "CASTJ",
    "C57BL/6J": "B6J",
    "NOD/ShiLtJ": "NODJ",
    "NZO/HlLtJ": "NZOJ",
    "PWK/PhJ": "PWKJ",
    "TREM2R47HNSS_HO": "TREM2",
    "WSB/EiJ": "WSBJ",
}
def normalize_strain(strain):
    """Adapter to convert name
    """
    return genotype_to_strain.get(strain, strain)

strain_to_genotype = {genotype_to_strain[k]: k for k in genotype_to_strain}
def get_genotype_from_mouse_tissue(mouse_tissue):
    fields = parse_mouse_tissue(mouse_tissue)
    strain = fields[1]
    return strain_to_genotype.get(strain, strain)

def normalize_subpool_submission_status(value):
    if pandas.isnull(value):
        return str(models.RunStatusEnum.FAILED)
    elif value in (0, False, "no", "No"):
        return str(models.RunStatusEnum.FAILED)
    elif value in (1, True, "yes", "Yes"):
        return str(models.RunStatusEnum.PASS)


mouse_age_sex_tuple = namedtuple("mouse_age_sex_tuple", ["mouse_age", "mouse_sex"])


mouse_name_tuple = namedtuple(
    "mouse_name_tuple",
    ["mouse_id", "mouse_strain", "mouse_age", "mouse_sex"])


mouse_tissue_tuple = namedtuple(
    "mouse_tissue_tuple",
    ["mouse_id", "mouse_strain", "mouse_age", "mouse_sex", "tissue_id"])


def parse_mouse_age_sex(mouse_age_sex):
    """Parse age/sex combined files like 10F or 6moM"""
    sex = mouse_age_sex[-1]
    age = mouse_age_sex[0:-1]

    if not sex in models.SexEnum.values:
        raise ValueError(
            "Invalid sex value {}. Allowed values {}".format(sex, models.SexEnum.values))

    valid_ages = ("6mo",)
    if not (age in valid_ages or isinstance(int(age), int)):
        raise ValueError("Age must be an integer or in {}".format(valid_ages))

    return mouse_age_sex_tuple(age, sex)


def join_mouse_age_sex(value):
    if isinstance(value, mouse_age_sex_tuple):
        mouse_age = str(value.mouse_age)
        mouse_sex = str(value.mouse_sex)
    elif isinstance(value, Sequence) and len(value) == 2:
        mouse_age = str(value[0])
        mouse_sex = str(value[1])
    else:
        raise ValueError("Value {} not compatible with mouse_age_sex_tuple".format(value))

    # TODO: Could probably add validators here too
    return mouse_age + mouse_sex


def parse_mouse_name(mouse_name):
    mouse_id_end = mouse_name.find("_")
    mouse_age_sex_start = mouse_name.rfind("_") + 1

    mouse_id = mouse_name[0:mouse_id_end]
    mouse_strain = normalize_strain(mouse_name[mouse_id_end+1:mouse_age_sex_start-1])
    mouse_age, mouse_sex = parse_mouse_age_sex(mouse_name[mouse_age_sex_start:])
    return mouse_name_tuple(mouse_id, mouse_strain, mouse_age, mouse_sex)


def join_mouse_name(value):
    if isinstance(value, mouse_name_tuple):
        mouse_id = value.mouse_id
        mouse_strain = value.mouse_strain
        mouse_age = value.mouse_age
        mouse_sex = value.mouse_sex
    elif isinstance(value, mouse_tissue_tuple):
        mouse_id = value.mouse_id
        mouse_strain = value.mouse_strain
        mouse_age = value.mouse_age
        mouse_sex = value.mouse_sex
    elif isinstance(value, Sequence) and len(value) == 4:
        mouse_id = value[0]
        mouse_strain = value[1]
        mouse_age = value[2]
        mouse_sex = value[3]
    else:
        raise ValueError("{} does not look like a parsed mouse_name".format(value))

    #mouse_strain = reverse_normalize_strain(mouse_strain)
    mouse_age_sex = join_mouse_age_sex((mouse_age, mouse_sex))
    return "_".join([mouse_id, mouse_strain, mouse_age_sex])


def parse_mouse_tissue(mouse_tissue):
    fields = mouse_tissue.split("_")

    mouse_id = fields.pop(0)
    mouse_strain = fields.pop(0)
    mouse_strain = normalize_strain(mouse_strain)
    mouse_age_sex = fields.pop(0)
    mouse_age, mouse_sex = parse_mouse_age_sex(mouse_age_sex)
    validate_mouse_age_sex(mouse_age_sex)
    tissue_id = fields.pop(0)
    assert len(fields) == 0

    return mouse_tissue_tuple(
        mouse_id, mouse_strain, mouse_age, mouse_sex, tissue_id)


def join_mouse_tissue(value):
    """Covert a set of mouse tissue attributes into a formatted string
    """
    if isinstance(value, mouse_tissue_tuple):
        mouse_id = value.mouse_id
        mouse_strain = value.mouse_strain
        mouse_age = value.mouse_age
        mouse_sex = value.mouse_sex
        mouse_tissue = value.tissue_id
    elif isinstance(value, Sequence) and len(value) == 5:
        mouse_id = value[0]
        mouse_strain = value[1]
        mouse_age = value[2]
        mouse_sex = value[3]
        mouse_tissue = value[4]
    else:
        raise ValueError(
            "{} does not look like a parsed mouse_name".format(value))

    mouse_strain = reverse_normalize_strain(mouse_strain)
    mouse_age_sex = join_mouse_age_sex((mouse_age, mouse_sex))
    return "_".join([mouse_id, mouse_strain, mouse_age_sex, mouse_tissue])


def get_strain_from_mouse_tissue(mouse_tissue):
    fields = parse_mouse_tissue(mouse_tissue)

    return fields[1]


def uci_tz_or_none(value):
    los_angeles_tz = zoneinfo.ZoneInfo("America/Los_Angeles")

    if pandas.isnull(value):
        return None
    elif isinstance(value, pandas.Timestamp):
        return value.tz_localize("America/Los_Angeles")
    elif isinstance(value, datetime.datetime):
        return value.astimezone(los_angeles_tz)
