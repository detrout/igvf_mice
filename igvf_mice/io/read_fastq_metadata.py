"""Reading from the fastq metadata file"""
import logging

import pandas
from Bio.Seq import Seq

from .converters import convert_plate_id_to_name, normalize_plate_name, str_or_none
from ..models import Subpool


logger = logging.getLogger(__name__)


def is_subpool_exome(subpool_name):
    if subpool_name is None:
        return False

    try:
        subpool = Subpool.objects.get(name=subpool_name)
    except Subpool.DoesNotExist:
        raise Subpool.DoesNotExist("Subpool {} does not exist".format(subpool_name))

    for protocol in subpool.protocols.all():
        if protocol.name == "cdna_exome_capture":
            return True

    return False


def fastq_metadata_row_to_subpool_name(row):
    if pandas.isnull(row.subpool_name):
        # Can we infer the subpool name
        if pandas.isnull(row.plate_id):
            # Need a plate id to find the subpool
            return None
        elif pandas.isnull(row.barcode_id):
            return None
        else:
            plate_name = convert_plate_id_to_name(row.plate_id)
            candidates = Subpool.objects.filter(
                plate__name=plate_name,
                barcode__code=row.barcode_id)
            if candidates.count() == 0:
                logger.warn("Nothing matched {} {}".format(
                    plate_name, row.barcode_id))
                assert False
            elif candidates.count() == 1:
                return candidates.first().name
            else:
                logger.warn("Too many subpools {} matched {} {}".format(
                    candidates, plate_name, row.barcode_id))
                assert False

        return None
    else:
        return "{}_{}".format(row.plate_id, row.subpool_name)


def get_subpool_from_fastq_row(row):
    plate_name = normalize_plate_name(row.experiment)
    subpool_name = fastq_metadata_row_to_subpool_name(row)

    if is_subpool_exome(subpool_name):
        row.protocol = "E"

    # if subpool_name in ["003_13A", "004_13A", "005_13A", "007_13A", "008B_13A", "009_13A", "010_13A", "011_13A"]:
    #    plate_name = "IGVF_EX1"
    # elif subpool_name in ["016_13A","017_13A","018_13A","019_13A","020_13A","021_13A","022_13A","023_13A"]:
    #    plate_name = "IGVF_EX2"

    query = {
        "plate__name": plate_name,
    }

    if pandas.notnull(subpool_name):
        query["name"] = subpool_name
    if pandas.notnull(row.barcode_id) and len(row.barcode_id) > 0:
        query["index"] = str_or_none(row.barcode_id)

    # these are labeled as having X nuclei but actually have fewer nuclei.
    # Not that you can tell that from the filename
    # nuclei_dont_match = {"013_67N", "014_13H"}
    # if pandas.notnull(row.nuclei) and subpool_name not in nuclei_dont_match:
    #    query["nuclei"] = int(row.nuclei)*1000
    if pandas.isnull(row.protocol) or row.protocol == "":
        query["selection_type"] = "NO"
    elif row.protocol == "E":
        query["selection_type"] = "EX"

    subpools = Subpool.objects.filter(**query)

    if len(subpools) == 0:
        print("Nothing found for {} {}".format(query, row.filename))
    elif len(subpools) > 1:
        print("Multiple hits for {}: {} {}".format(query, subpools, row.filename))
        assert False
    else:
        return subpools[0]


def check_fastq_barcode_is_equal(i7_sequence, i5_rc_sequence, barcode):
    if pandas.isnull(i5_rc_sequence):
        return i7_sequence == barcode

    sequences = barcode.split("+")
    if len(sequences) != 2:
        print(
            "Warning: database says dual index, file says single index: {} {} {}".format(
                i7_sequence, i5_rc_sequence, barcode
            )
        )
        return False

    i7, i5 = sequences
    # barcodes in the fastq file are reverse complimented.
    i5 = Seq(i5).reverse_complement()
    return i7_sequence == i7 and i5_rc_sequence == i5
