import jwt

from django.conf import settings


class JWTUtil(object):
    SECRET = settings.SECRET_KEY

    @classmethod
    def jwt_encode(cls, user_id, device_id):
        """
        Encode jwt header information
        :param user_id:         identifier for the user
        :param device_id:       identifier for the device
        :return:
        """
        return jwt.encode({"user_id": user_id,
                           "device_id": device_id},
                          cls.SECRET)

    @classmethod
    def jwt_decode(cls, token):
        try:
            return jwt.decode(token, cls.SECRET)
        except jwt.InvalidTokenError:
            return None
