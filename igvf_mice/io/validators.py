import pandas
import re

def validate_alias(alias):
    alias_pattern = re.compile("^(?:j-michael-cherry|ali-mortazavi|barbara-wold|lior-pachter|grant-macgregor|kim-green|mark-craven|qiongshi-lu|audrey-gasch|robert-steiner|jesse-engreitz|thomas-quertermous|anshul-kundaje|michael-bassik|will-greenleaf|marlene-rabinovitch|lars-steinmetz|jay-shendure|nadav-ahituv|martin-kircher|danwei-huangfu|michael-beer|anna-katerina-hadjantonakis|christina-leslie|alexander-rudensky|laura-donlin|hannah-carter|bing-ren|kyle-gaulton|maike-sander|charles-gersbach|gregory-crawford|tim-reddy|ansuman-satpathy|andrew-allen|gary-hon|nikhil-munshi|w-lee-kraus|lea-starita|doug-fowler|luca-pinello|guillaume-lettre|benhur-lee|daniel-bauer|richard-sherwood|benjamin-kleinstiver|marc-vidal|david-hill|frederick-roth|mikko-taipale|anne-carpenter|hyejung-won|karen-mohlke|michael-love|jason-buenrostro|bradley-bernstein|hilary-finucane|chongyuan-luo|noah-zaitlen|kathrin-plath|roy-wollman|jason-ernst|zhiping-weng|manuel-garber|xihong-lin|alan-boyle|ryan-mills|jie-liu|maureen-sartor|joshua-welch|stephen-montgomery|alexis-battle|livnat-jerby|jonathan-pritchard|predrag-radivojac|sean-mooney|harinder-singh|nidhi-sahni|jishnu-das|hao-wu|sreeram-kannan|hongjun-song|alkes-price|soumya-raychaudhuri|shamil-sunyaev|len-pennacchio|axel-visel|jill-moore|ting-wang|feng-yue|igvf|igvf-dacc):[a-zA-Z\\d_$.+!*,()'-]+(?:\\s[a-zA-Z\\d_$.+!*,()'-]+)*$")
    
    if alias_pattern.match(alias) is None:
        raise ValueError("Invalid alias")
    else:
        return True


def validate_mouse_age_sex(value):
    sex = value[-1]
    age = value[0:-1]

    if sex not in ("M", "F"):
        raise ValueError("Invalid sex value")

    valid_ages = ("6mo",)
    if not (age in valid_ages or isinstance(int(age), int)):
        raise ValueError("Age must be an integer or in {}".format(valid_ages))

    return True


def validate_splitseq_cap_label(cap_label, sample_id, line_no=None):
    if not (pandas.isnull(cap_label) or pandas.isnull(sample_id)):
        sample_fields = sample_id.split("_")
        predicted_label = "_".join([sample_fields[0], sample_fields[-1]])
        if predicted_label != cap_label:
            if line_no is not None:
                line_err = f" line {line_no}"
            else:
                line_err = ""
            print(f"{cap_label} should equal {predicted_label}{line_err}")
            return False
        else:
            return True
