def merge_dicts(d1, d2):
    for k in d2:
        d1[k] = d2[k]
    return d1
