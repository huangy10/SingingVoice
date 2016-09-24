# coding=utf-8
import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from utils.exceptions import DeclarativeException
from utils.tools import camel_to_under_dash


def combine_two_decorators(dec1, dec2):
    return lambda x: dec1(dec2(x))


def login_first(method):
    """ 这个装饰器和django自带的不同，如果发现当前用户没有登陆，会返回一个Json告知
    """
    def wrapper(request, *args, **kwargs):
        if request.user is None or not request.user.is_authenticated():
            return JsonResponse(dict(code='1402'))
        else:
            return method(request, *args, **kwargs)
    return wrapper


def as_json(view):
    """ 将view返回的参数打包成json响应
    """
    def wrapper(request, *args, **kwargs):
        result = view(request, *args, **kwargs)
        if result is None:
            return JsonResponse(dict(code='0'))
        elif isinstance(result, tuple):
            return JsonResponse(dict(code=result[0], payload=result[1]))
        elif isinstance(result, basestring):
            return JsonResponse(dict(code=result))
        elif isinstance(result, int):
            return JsonResponse(dict(code=str(result)))
        else:
            return JsonResponse(dict(code='0', payload=result))
    return wrapper


def json_request(view):
    """ 尝试将请求的body转成JSON格式
    """
    def wrapper(request, *args, **kwargs):
        if request.method != "POST":
            setattr(request, "JSON", request.GET)
            return view(request, *args, **kwargs)
        try:
            data = json.loads(request.body)
        except ValueError:
            data = request.POST
        setattr(request, 'JSON', data)
        return view(request, *args, **kwargs)

    return wrapper


def may_make_exception(view):
    """ Notice: when using with json_view, this decorator must be placed as the inner one
    """

    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except DeclarativeException as e:
            return e.as_response()

    return wrapper


def load_object_by_id(model, id_field=None, get_current_user_if_fail=False, null_instead_of_exception=False):
    model_name = camel_to_under_dash(model.__name__)
    if id_field is None:
        id_field = "%s_id" % model_name

    def wrapper(view):
        def _wrapper(request, *args, **kwargs):
            data = request.data
            if id_field in data:
                try:
                    obj = model.objects.get(public_id=data[id_field])
                except ObjectDoesNotExist:
                    if not null_instead_of_exception:
                        raise model.not_found_exception
                    else:
                        obj = None
            elif model.__name__ == "User" and get_current_user_if_fail:
                obj = request.user
            else:
                obj = None
            kwargs.update({model_name: obj})
            return view(request, *args, **kwargs)
        return _wrapper

    return wrapper


json_view = combine_two_decorators(as_json, json_request)


class ClassPropertyDescriptor(object):

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)
