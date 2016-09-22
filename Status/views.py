from django.views.decorators import http
from django.db.models import Count, Sum, IntegerField, Case, When, Value

from Status.models import *
from User.models import User
from utils.decorators import json_view, may_make_exception, login_first, load_object_by_id
from utils.query import get_page_by_skip, get_page_by_date_threshold, queries_to_serializable_array
from Status.forms import StatusNewForm


# Create your views here.


@http.require_GET
@json_view
@login_first
@load_object_by_id(User, get_current_user_if_fail=True)
def status_list(request, user):
    result = get_page_by_date_threshold(
        Status.objects.filter(user=user)
        .annotate(like_num=Count("liked_by"))
        .annotate(comment_num=Count("comments"))
        .annotate(liked=Sum(Case(When(liked_by=user, then=Value(1)), default=Value(0), output_field=IntegerField()))),
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
        Comment.objects.filter(status=status)
        .annotate(like_num=Count("liked_by"))
        .annotate(liked=Sum(Case(When(liked_by=request.user, then=Value(1)), default=Value(0), output_field=IntegerField()))),
        **request.JSON
    )
    return queries_to_serializable_array(result)
