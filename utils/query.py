from __future__ import unicode_literals

from utils.exceptions import OpTypeNotDefinedException
from utils.format import str_to_date


MAX_LIMIT = 1000


def get_page_by_skip(data, skip, limit, op_type):
    limit = min(MAX_LIMIT, limit)
    if op_type == "latest":
        data = data.order_by("-created_at")
    elif op_type == "more":
        data = data.order_by("created_at")
    else:
        pass

    return data[skip: (skip + limit)]


def get_page_by_date_threshold(data, date_threshold, limit, op_type):
    if isinstance(date_threshold, basestring):
        date_threshold = str_to_date(date_threshold)
    if op_type == "latest":
        data = data.filter(date_threshold__gt=date_threshold).order_by("-created_at")
    elif op_type == "more":
        data = data.filter(date_threshold__lt=date_threshold).order_by("created_at")
    else:
        raise OpTypeNotDefinedException(op_type)

    return data[0:limit]


def model_to_dict(model):
    return model.dict_description()


def queries_to_serializable_array(queries):
    return map(model_to_dict, queries)


class MetaVisible(type):

    @property
    def visible(cls):
        if hasattr(cls, "objects"):
            return cls.objects.filter(deleted=False)
        else:
            return None

