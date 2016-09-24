from __future__ import unicode_literals


from django.views.decorators import http
from django.db.models import Count, Sum, IntegerField, Case, When, Value
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from Status.models import *
from User.models import User
from utils.decorators import json_view, may_make_exception, login_first, load_object_by_id
from utils.query import get_page_by_skip, get_page_by_date_threshold, queries_to_serializable_array
from Status.forms import StatusNewForm, CommentNewForm


# Create your views here.


@http.require_GET
@json_view
@login_first
@load_object_by_id(User, get_current_user_if_fail=True)
def status_list(request, user):
    result = get_page_by_date_threshold(
        Status.visible.make_full_annotation(user).filter(user=user),
        **request.JSON
    )
    return queries_to_serializable_array(result)


@http.require_POST
@json_view
@login_first
def new_status(request):
    form = StatusNewForm(request.JSON, request.FILES)
    if form.is_valid():
        status = form.save()
        return status.dict_description()
    else:
        return form.generate_error_report()


@http.require_GET
@json_view
@login_first
@load_object_by_id(Status)
def comment_list(request, status):
    result = get_page_by_date_threshold(
        Comment.visible.make_full_annotation(request.user).filter(status=status),
        **request.JSON
    )
    return queries_to_serializable_array(result)


@http.require_POST
@json_view
@login_first
@load_object_by_id(Status)
def new_comment(request, status):
    data = request.JSON
    data.update(status=status, user=request.user)
    form = CommentNewForm(data, request.FILES)
    if form.is_valid():
        comment = form.save()
        return comment.dict_description()
    else:
        return form.generate_error_report()


@http.require_GET
@json_view
@login_first
def world(request):
    data = request.JSON
    loc = data['loc']
    lat = float(loc['lat'])
    lon = float(loc['lon'])
    range_ = float(data['range'])
    limit = int(data['limit'])
    pt = Point(x=lon, y=lat)
    result = Status.visible.make_full_annotation(request.user)\
        .order_by('-like_num', '-comment_num')\
        .filter(location__distance_lte=(pt, D(m=range_)))[0:limit]
    return queries_to_serializable_array(get_page_by_skip(result, 0, limit, None))


@http.require_POST
@json_view
@login_first
@load_object_by_id(Status)
def delete_status(request, status):
    if status.user_id != request.user.id:
        return "no permission"
    else:
        status.delete()


@http.require_POST
@json_view
@login_first
@load_object_by_id(Comment)
def delete_comment(request, comment):
    if comment.user != request.user.id:
        return "no permission"
    else:
        comment.delete()
