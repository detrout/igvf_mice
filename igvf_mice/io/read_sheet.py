from collections.abc import Mapping
import pandas

from .. import models
from .converters import normalize_strain


class StrainCode(Mapping):
    def __getitem__(self, key):
        overrides = {
            "B6129SF1J": "B6129S1F1J",
            "B6AF1": "B6AF1J",
        }
        key = overrides.get(key, key)

        try:
            x = models.MouseStrain.objects.get(name=key)
            return x.display_name
        except models.MouseStrain.DoesNotExist:
            raise KeyError("{} was not found".format(key))

    def __len__(self):
        return models.MouseStrain.objects.count()

    def __iter__(self):
        for strain in models.MouseStrain.objects.all():
            return strain.name


class StrainName(Mapping):
    def __getitem__(self, key):
        overrides = {"B6129SF1J": "B6129S1F1/J"}
        key = overrides.get(key, key)

        try:
            x = models.MouseStrain.objects.get(display_name=key)
            return x.name
        except models.MouseStrain.DoesNotExist:
            raise KeyError("{} was not found".format(key))

    def __len__(self):
        return models.MouseStrain.objects.count()

    def __iter__(self):
        for strain in models.MouseStrain.objects.all():
            return strain.display_name


strain_code_to_name = StrainCode()
strain_name_to_code = StrainName()


def normalize_mice_name(name):
    if pandas.isnull(name):
        return name

    if name == "056_WSBJ_10F->PWKJ_9F":
        name = "056_PWKJ_9F"

    if not name[-1] in ("M", "F"):
        raise ValueError(f"Unrecognized sex field in {name}")

    name_fields = name.split("_")

    if len(name_fields) > 3:
        # deal with TREM2R47HNSS_HO
        if name_fields[1].startswith("TREM2R47"):
            name_fields = [name_fields[0], "_".join(name_fields[1:-1]), name_fields[-1]]

    name_fields[1] = normalize_strain(name_fields[1])

    if not name_fields[1] in strain_code_to_name:
        raise ValueError(f"strain background {name_fields[1]} in {name} not recognized")

    return "_".join(name_fields)


def normalize_mice_strain_name(x):
    if pandas.isnull(x):
        return x
    elif x in strain_name_to_code:
        return x
    elif x in strain_code_to_name:
        return strain_code_to_name[x]
    else:
        raise ValueError(f"Unrecognized strain name {x}")
