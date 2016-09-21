from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest

from .models import User
from jwt_utils import JWTUtil


class MyJWTAuthorizationMiddleware(object):

    def process_request(self, request):
        if request.user.is_superuser:
            return
        if not hasattr(request, '_cached_user') or not hasattr(request, '_cached_device'):
            user, device = self.get_user(request)
            request._cached_user = user or AnonymousUser()
        request.user = request._cached_user

    def get_user(self, request):
        header = request.META.get("HTTP_AUTHORIZATION")
        # print header
        if header is None:
            return None
        data = JWTUtil.jwt_decode(header)
        if data is None:
            return None
        user_id = data['user_id']
        token = data['device_token']
        try:
            user = User.objects.get(pk=user_id)
            if user.device_token is not None and user.device_token != token:
                return None
        except ObjectDoesNotExist:
            return None

        return user

