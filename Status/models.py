# coding=utf-8
from __future__ import unicode_literals
import uuid

from django.contrib.gis.db import models
from django.db.models import Count, Sum, Case, When, IntegerField, Value
from django.utils import timezone

from utils.mixins import HasPublicID
from utils.format import date_to_string
from utils.decorators import classproperty
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


class StatusManager(models.GeoManager):

    def make_full_annotation(self, user):
        return self.select_related("user").annotate(like_num=Count("liked_by"))\
            .annotate(comment_num=Count('comments'))\
            .annotate(
            liked=Sum(Case(When(liked_by=user, then=Value(1)), default=Value(0), output_field=IntegerField()))
        )


class Status(models.Model, HasPublicID):

    user = models.ForeignKey("User.User", related_name="status", verbose_name='作者')
    cover = models.ImageField(upload_to=status_image, verbose_name="动态封面图")
    voice = models.FileField(upload_to=status_voice, verbose_name="动态声音")
    location = models.PointField(verbose_name="动态地点")
    created_at = models.DateTimeField(auto_now_add=True)
    loc_des = models.CharField(max_length=255, verbose_name="地点描述", db_index=True)

    liked_by = models.ManyToManyField("User.User", related_name="liked_status", verbose_name="点赞")

    deleted = models.BooleanField(default=False, verbose_name='动态是否被删除')
    deleted_at = models.DateTimeField(default=timezone.now, verbose_name='动态被删除的日期')

    objects = StatusManager()

    @classproperty
    def visible(cls):
        return cls.objects.filter(deleted=False)

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
        if hasattr(self, "comment_num"):
            result.update(comment_num=self.comment_num)
        return result

    def delete(self, using=None, keep_parents=False, commit=False):
        if commit:
            super(Status, self).delete(using=using, keep_parents=keep_parents)
        else:
            self.deleted = True
            self.deleted_at = timezone.now()
            self.save()


class CommentManger(models.Manager):

    def make_full_annotation(self, user):
        return self.select_related("user", "status").annotate(like_num=Count("liked_by"))\
            .annotate(
            liked=Sum(Case(When(liked_by=user, then=Value(1)), default=Value(0), output_field=IntegerField()))
        )


class Comment(models.Model, HasPublicID):

    user = models.ForeignKey("User.User", verbose_name="用户")
    status = models.ForeignKey(Status, verbose_name="动态", related_name="comments")
    image = models.ImageField(upload_to=status_image, verbose_name="评论图片")
    created_at = models.DateTimeField(auto_now_add=True)

    liked_by = models.ManyToManyField("User.User", related_name="liked_comments", verbose_name="点赞")

    deleted = models.BooleanField(default=False, verbose_name="是否被删除")
    deleted_at = models.DateTimeField(default=timezone.now, verbose_name='删除日期')

    objects = CommentManger()

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

    def delete(self, using=None, keep_parents=False, commit=False):
        if commit:
            super(Comment, self).delete(using=using, keep_parents=keep_parents)
        else:
            self.deleted = True
            self.deleted_at = timezone.now()
            self.save()

