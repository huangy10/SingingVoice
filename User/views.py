from django.contrib import auth
from django.views.decorators import http
from django.db.models import Sum, IntegerField, Case, When, Value

from User.jwt_utils import JWTUtil
from User.sms import create_random_code, send_sms
from utils.decorators import *
from User.models import *
from User.forms import UserRegisterForm, PasswordResetForm
from utils.query import get_page_by_date_threshold, get_page_by_skip, queries_to_serializable_array
# Create your views here.


@http.require_POST
@json_view
def login(request):
    data = request.JSON
    phone_num = data['phone_num']
    password = data['password']
    device_token = data['device_token']

    user = auth.authenticate(phone_num=phone_num, password=password)

    if user is None:
        if not User.objects.filter(phone_num=phone_num).exists():
            return "phone number not found"
        else:
            return "password invalid"
    else:
        user.device_token = device_token
        user.save()
        jwt_token = JWTUtil.jwt_encode(user.id, device_token)
        result = user.dict_description()
        result.update(jwt_token=jwt_token)
        return result


@http.require_POST
@json_view
@login_first
def logout(request):
    request.user.logout()


@http.require_POST
@json_view
def send_code(request):
    data = request.JSON
    phone_num = data['phone_num']
    if AuthenticationCode.objects.already_sent(phone_num):
        return "already sent"
    else:
        code = create_random_code()
        if send_sms(code, phone_num):
            AuthenticationCode.objects.create(phone_num=phone_num, code=code)
            return
        else:
            return "error"


@http.require_POST
@json_view
def register(request):
    data = request.JSON
    form = UserRegisterForm(data, request.FILES)
    if form.is_valid():
        user = form.save()
        jwt_token = JWTUtil.jwt_encode(user.id, user.device_token)
        result = user.dict_description()
        result.update(jwt_token=jwt_token)
        return result
    else:
        return form.generate_error_report()


@http.require_POST
@json_view
def reset_password(request):
    data = request.JSON
    form = PasswordResetForm(data)
    if form.is_valid():
        form.save()
    else:
        return JsonResponse(form.generate_error_report())


@http.require_http_methods(['GET', 'POST'])
@json_view
@login_first
@may_make_exception
@load_object_by_id(User, get_current_user_if_fail=True)
def info(request, user):
    if request.method == "GET":
        return user.dict_description()
    elif request.method == "POST":
        data = request.data
        user.update(name=data.get('name'), avatar=request.FILES.get('avatar'), signature=data.get('signature'))


@http.require_GET
@json_view
@load_object_by_id(User, get_current_user_if_fail=True)
def fans(request, user):
    # TODO: check if is_follow can be read as a Boolean Field
    result = get_page_by_skip(
        data=User.objects.filter(follows=user).annotate(
            is_follow=Sum(Case(When(fans=user, then=Value(1)), default=Value(0), output_field=IntegerField()))
        ),
        **request.JSON
    )
    return queries_to_serializable_array(result)


@http.require_GET
@json_view
@load_object_by_id(User, get_current_user_if_fail=True)
def follows(request, user):
    result = get_page_by_skip(data=User.objects.filter(fans=user), **request.JSON)
    for user in result:
        setattr(user, 'is_follow', True)
    return queries_to_serializable_array(result)



