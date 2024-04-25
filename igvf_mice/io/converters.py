"""Cast pandas values to django database semantics

The way that pandas and django represent missing data needs a bits of
conversion.
"""
from collections import namedtuple
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


def normalize_strain(strain):
    replacements = {
        "F1/J": "F1J",
        "B6129SF1J": "B6129S1F1J",
    }
    for current, desired in replacements.items():
        strain = strain.replace(current, desired)

    return strain

    return strain


def normalize_subpool_submission_status(value):
    if pandas.isnull(value):
        return str(models.RunStatusEnum.FAILED)
    elif value in (0, False, "no", "No"):
        return str(models.RunStatusEnum.FAILED)
    elif value in (1, True, "yes", "Yes"):
        return str(models.RunStatusEnum.PASS)

mouse_name_tuple = namedtuple(
    "mouse_name_tuple",
    ["mouse_id", "mouse_strain", "mouse_age", "mouse_sex"])


mouse_tissue_tuple = namedtuple(
    "mouse_tissue_tuple",
    ["mouse_id", "mouse_strain", "mouse_age", "mouse_sex", "tissue_id"])


def parse_mouse_name(mouse_name):
    mouse_id_end = mouse_name.find("_")
    mouse_age_sex_start = mouse_name.rfind("_") + 1
    
    mouse_id = mouse_name[0:mouse_id_end]
    mouse_strain = normalize_strain(mouse_name[mouse_id_end+1:mouse_age_sex_start-1])
    mouse_age_sex = mouse_name[mouse_age_sex_start:]
    validate_mouse_age_sex(mouse_age_sex)
    return mouse_name_tuple(mouse_id, mouse_strain, mouse_age_sex)


def parse_mouse_tissue(mouse_tissue):
    fields = mouse_tissue.split("_")
    
    mouse_id = fields.pop(0)
    mouse_strain = fields.pop(0)
    if mouse_strain in ("TREM2R47HNSS",):
        mouse_strain = "_".join([mouse_strain, fields.pop(0)])
    mouse_strain = normalize_strain(mouse_strain)
    mouse_age_sex = fields.pop(0)
    validate_mouse_age_sex(mouse_age_sex)
    tissue_id = fields.pop(0)
    assert len(fields) == 0
    
    return mouse_tissue_tuple(mouse_id, mouse_strain, mouse_age_sex, tissue_id)


def get_genotype_from_mouse_tissue(mouse_tissue):
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
