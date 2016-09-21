# coding=utf-8
import json

from django.http import JsonResponse
from utils.exceptions import DeclarativeException

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
            return view(request, *args, **kwargs)
        try:
            data = json.loads(request.body)
        except ValueError:
            data = request.POST
        setattr(request, 'JSON', data)
        return view(request, *args, **kwargs)

    return wrapper


def may_make_exception(view):

    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except DeclarativeException as e:
            return e.as_response()

    return wrapper


json_view = combine_two_decorators(as_json, json_request)
