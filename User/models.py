# coding=utf-8
from __future__ import unicode_literals
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager, AbstractUser
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import smart_str

from utils.mixins import HasPublicID

# Create your models here.


def profile_avatar(instance, filename, *args, **kwargs):
    current = timezone.now()
    ext = filename.split('.')[-1]
    random_file_name = str(uuid.uuid4()).replace('-', '')
    new_file_name = "{0}/{1}/{2}/{3}/{4}.{5}".format(
        'profile_avatar',
        current.year,
        current.month,
        current.day,
        random_file_name,
        ext
    )
    return new_file_name


class MyUserManager(UserManager):

    def _create_user(self, phone_num, password, **extra_fields):
        now = timezone.now()
        if not phone_num or not password:
            raise ValueError("Phone number and password must be set to create a user")
        user = self.model(phone_num=phone_num, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, phone_num, password=None, **extra_fields):
        return self._create_user(phone_num, password, **extra_fields)

    def create_superuser(self, phone_num, password, **extra_fields):
        return self._create_user(phone_num, password, **extra_fields)


class User(AbstractUser, HasPublicID):
    REQUIRED_FIELDS = []
    USERNAME_FIELD = "phone_num"

    objects = MyUserManager()

    phone_num = models.CharField(max_length=20, verbose_name=u"手机号(用户名)", db_index=True, unique=True)
    avatar = models.ImageField(upload_to=profile_avatar, verbose_name="头像")
    gender = models.CharField(max_length=1, choices=(
        ('m', u'男'),
        ('f', u'女'),
    ), verbose_name=u'性别')
    signature = models.CharField(max_length=1000, verbose_name=u"签名", default='说点什么吧')

    follows = models.ManyToManyField("self", through="UserRelation", related_name="fans", symmetrical=False)

    fans_num = models.IntegerField(default=0, verbose_name=u"粉丝数量")
    follows_num = models.IntegerField(default=0, verbose_name=u"关注数量")
    status_num = models.IntegerField(default=0, verbose_name=u"动态数量")
    comment_num = models.IntegerField(default=0, verbose_name="评论数量")

    created_at = models.DateTimeField(auto_now_add=True)

    device_token = models.CharField(max_length=255, verbose_name='设备的token')

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def dict_description(self):
        result = dict(
            id=self.public_id,
            phone_num=self.phone_num,
            avatar=self.avatar.url,
            signature=self.signature,
            fans_num=self.fans_num,
            follows_num=self.follows_num,
            status_num=self.status_num,
            comment_num=self.comment_num
        )
        if hasattr(self, "is_fan"):
            result.update(is_fan=self.is_fan)
        if hasattr(self, "is_follow"):
            result.update(is_follow=self.is_follow)
        return result

    def logout(self, commit=True):
        self.device_token = ""
        if commit:
            self.save()

    @property
    def online(self):
        return self.device_token != ""


class UserRelation(models.Model):

    source_user = models.ForeignKey(User, related_name='follows_relation')
    target_user = models.ForeignKey(User, related_name='fans_relation')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", )
        unique_together = ("source_user", "target_user")


@receiver(post_delete, sender=UserRelation)
def auto_decrease_relation_numbers(sender, instance, **kwargs):
    source = instance.source_user
    target = instance.target_user
    source.follows_num -= 1
    target.fans_num -= 1
    source.save()
    target.save()


@receiver(post_save, sender=UserRelation)
def auto_increase_relation_numbers(sender, instance, created, **kwargs):
    if not created:
        return
    source = instance.source_user
    target = instance.target_user
    source.follows_num += 1
    target.fans_num += 1
    source.save()
    target.save()


class AuthenticationManager(models.Manager):

    def already_sent(self, phone, seconds=60):
        """ Check if a valid authentication code has already sent to the given phone
         number in `seconds`

         :param phone phone number
         :param seconds time threshold
        """
        if AuthenticationCode.objects.filter(phone_num=phone, is_active=True).exists():
            record = AuthenticationCode.objects.filter(phone_num=phone, is_active=True).first()
            if (timezone.now() - record.created_at).total_seconds() > seconds:
                AuthenticationCode.objects.filter(phone_num=phone).update(is_active=False)
                return False
            else:
                return True
        else:
            return False

    def check_code(self, code, phone, seconds=60*5):
        """ Check the code
         :param code authentication code
         :param phone phone number
         :param seconds expire time
         :return boolean
        """
        record = AuthenticationCode.objects.filter(phone_num=phone, code=code, is_active=True).first()
        if record is None:
            return False
        elif (timezone.now() - record.created_at).total_seconds() > seconds:
            return False
        else:
            return True

    def deactivate(self, code, phone):
        """ Deactivate a code
         :param code authentication code
         :param phone corresponding phone number
         :return True on success
        """
        try:
            record = AuthenticationCode.objects.get(phone_num=phone, code=code)
            record.is_active = False
            record.save()
            return True
        except ObjectDoesNotExist:
            return False


class AuthenticationCode(models.Model):
    phone_num = models.CharField(max_length=20, verbose_name=u'手机号码')
    code = models.CharField(max_length=6, verbose_name=u'验证码')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    objects = AuthenticationManager()

    def __str__(self):
        return smart_str(self.code)

    class Meta:
        ordering = ['-created_at']