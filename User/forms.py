from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from User.models import User, AuthenticationCode


class UserRegisterForm(forms.ModelForm):

    auth_code = forms.CharField(max_length=6)

    class Meta:
        model = User

    def clean_phone_num(self):
        phone_num = self.cleaned_data['phone_num']
        if User.objects.filter(phone_num=phone_num).exists():
            raise forms.ValidationError('user exists')
        return phone_num

    def clean_password(self):
        password = self.cleaned_data['password']
        p_len = len(password)
        if p_len < settings.PASSWORD_LEN_MIN or p_len > settings.PASSWORD_LEN_MAX:
            raise forms.ValidationError('password length')
        return password

    def clean_device_token(self):
        token = self.cleaned_data['device_token']
        # TODO: validate the token
        return token

    def clean(self):
        super(UserRegisterForm, self).clean()
        if 'phone_num' not in self.cleaned_data or 'password' not in self.cleaned_data:
            return
        auth_code = self.cleaned_data['auth_code']
        phone_num = self.cleaned_data['phone_num']
        if not AuthenticationCode.objects.check_code(code=auth_code, phone=phone_num):
            self.add_error('auth_code', forms.ValidationError('invalid code'))

    def save(self, commit=True):
        # TODO: Raise an error if commit equals False
        create_param = self.cleaned_data
        del create_param['auth_code']
        user = User.objects.create(**self.cleaned_data)
        user.set_password(self.cleaned_data['password'])
        AuthenticationCode.objects.deactivate(code=self.cleaned_data['auth_code'], phone=self.cleaned_data['phone_num'])
        return user

    def generate_error_report(self):
        err = self.errors
        if 'phone_num' in err:
            return 'user exists'
        elif 'password' in err:
            return 'password length'
        elif 'auth_code' in err:
            return 'invalid code'
        else:
            return 'unknown'


class PasswordResetForm(UserRegisterForm):

    class Meta:
        model = User

    def __init__(self, data=None, files=None, **kwargs):
        super(PasswordResetForm, self).__init__(data=data, files=files, **kwargs)
        self._user = None

    def clean_phone_num(self):
        phone_num = self.cleaned_data['phone_num']
        try:
            self._user = User.objects.get(phone_num=phone_num)
        except ObjectDoesNotExist:
            raise forms.ValidationError('user not found')
        return phone_num

    def save(self, commit=True):
        user = self._user
        user.set_password(self.cleaned_data['password'])
        AuthenticationCode.objects.deactivate(code=self.cleaned_code, phone=self.cleaned_data['phone_num'])

        if commit:
            user.save()
        return user

    def generate_error_report(self):
        report = super(PasswordResetForm, self).generate_error_report()
        if report == "user exists":
            return "user not found"
        else:
            return report
