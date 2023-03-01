import re


def to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def camel_to_snake_case_deep(d):
    if isinstance(d, list):
        return [
            camel_to_snake_case_deep(i) if isinstance(i, (dict, list)) else i for i in d
        ]
    return {
        to_snake(a): camel_to_snake_case_deep(b) if isinstance(b, (dict, list)) else b
        for a, b in d.items()
    }


def kaspadBlockToModel(block: object):
    return {
        "header": camel_to_snake_case_deep(block["header"]),
        "transactions": None,
        "verbose_data": camel_to_snake_case_deep(block["verboseData"]),
    }
