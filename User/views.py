from django.shortcuts import render
from django.contrib import auth

from User.jwt_utils import JWTUtil
from User.sms import create_random_code, send_sms
from utils.decorators import *
from .models import *
from User.forms import UserRegisterForm, PasswordResetForm
# Create your views here.


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


@json_view
@login_first
def logout(request):
    request.user.logout()


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


@json_view
def register(request):
    data = request.data
    form = UserRegisterForm(data, request.FILES)
    if form.is_valid():
        user = form.save()
        jwt_token = JWTUtil.jwt_encode(user.id, user.device_token)
        result = user.dict_description()
        result.update(jwt_token=jwt_token)
        return result
    else:
        return form.generate_error_report()


@json_view
def reset_password(request):
    data = request.data
    form = PasswordResetForm(data)
    if form.is_valid():
        form.save()
    else:
        return JsonResponse(form.generate_error_report())


@json_view
@login_first
def info(request):
    data = request.data
    if "user_id" in data:
        pass


