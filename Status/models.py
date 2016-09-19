# coding=utf-8
from __future__ import unicode_literals
import uuid

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.utils import timezone

from utils.mixins import HasPublicID
from utils.format import date_to_string
# Create your models here.


def status_image(instance, filename, *args, **kwargs):
    current = timezone.now()
    ext = filename.split('.')[-1]
    random_file_name = str(uuid.uuid4()).replace('-', '')
    new_file_name = "{0}/{1}/{2}/{3}/{4}.{5}".format(
        'status',
        current.year,
        current.month,
        current.day,
        random_file_name,
        ext
    )
    return new_file_name


def status_voice(instance, filename, *args, **kwargs):
    current = timezone.now()
    ext = filename.split('.')[-1]
    random_file_name = str(uuid.uuid4()).replace('-', '')
    new_file_name = "{0}/{1}/{2}/{3}/{4}.{5}".format(
        'voice',
        current.year,
        current.month,
        current.day,
        random_file_name,
        ext
    )
    return new_file_name


class Status(models.Model, HasPublicID):

    user = models.ForeignKey("User.User", related_name="status", verbose_name='作者')
    cover = models.ImageField(upload_to=status_image, verbose_name="动态封面图")
    voice = models.FileField(upload_to=status_voice, verbose_name="动态声音")
    location = models.PointField(verbose_name="动态地点")
    created_at = models.DateTimeField(auto_now_add=True)
    loc_des = models.CharField(max_length=255, verbose_name="地点描述", db_index=True)

    liked_by = models.ManyToManyField("User.User", related_name="liked_status", verbose_name="点赞")

    objects = models.GeoManager()

    @property
    def latitude(self):
        return self.location.y

    @property
    def longitude(self):
        return self.location.x

    class Meta:
        verbose_name = "动态"
        verbose_name_plural = "动态"

    def dict_description(self):
        result = dict(
            id=self.public_id,
            cover=self.cover.url,
            voice=self.voice.url,
            user=self.user.dict_description(),
            loc=dict(
                lat=self.latitude,
                lon=self.longitude,
                des=self.loc_des
            ),
            created_at=date_to_string(self.created_at)
        )
        if hasattr(self, "liked"):
            result.update(liked=self.liked)
        if hasattr(self, "like_num"):
            result.update(like_num=self.like_num)
        return result


class Comment(models.Model, HasPublicID):
    user = models.ForeignKey("User.User", verbose_name="用户")
    status = models.ForeignKey(Status, verbose_name="动态")
    image = models.ImageField(upload_to=status_image, verbose_name="评论图片")
    created_at = models.DateTimeField(auto_now_add=True)

    liked_by = models.ManyToManyField("User.User", related_name="liked_comments", verbose_name="点赞")

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"

    def dict_description(self):
        result = dict(
            id=self.public_id,
            image=self.image.url,
            created_at=date_to_string(self.created_at),
            user=self.user.dict_description(),
            status=self.status.dict_description()
        )
        if hasattr(self, 'liked'):
            result.update(liked=self.liked)
        if hasattr(self, 'like_num'):
            result.update(like_num=self.like_num)

        return result

