def attribute_status_fill(field):
    if field in ["UNK", "NI", "NASK", "NA", "ND"]:
        return field
    elif field is not None:
        return "VAL"
    else:
        return None


def values_strip_missing(field):
    if field in ["UNK", "NI", "NASK", "NA", "ND"]:
        return None
    else:
        return field
