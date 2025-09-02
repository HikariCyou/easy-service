def clean_dict(d: dict):
    return {k: v for k, v in d.items() if not (isinstance(v, str) and v.strip() == "")}
