# coding=utf-8
from __future__ import unicode_literals
import json

from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from Message.signal import send_notification
from utils.mixins import HasPublicID
from utils.format import date_to_string

# Create your models here.


class Message(models.Model, HasPublicID):
    target = models.ForeignKey("User.User", verbose_name="消息发送的目标", related_name="+")
    source = models.ForeignKey("User.User", verbose_name="产生消息的用户", related_name="+")

    created_at = models.DateTimeField(auto_now_add=True)
    checked = models.BooleanField(default=False)
    flag = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    operation_at = models.DateTimeField(default=timezone.now)
    message_body = models.CharField(max_length=255, verbose_name="消息")
    namespace = models.CharField(max_length=255, verbose_name="消息的namespace")
    message_type = models.CharField(max_length=255, verbose_name="消息类型")

    related_status = models.ForeignKey("Status.Status", related_name="+")
    related_comment = models.ForeignKey("Status.Comment", related_name="+")

    class Meta:
        verbose_name = "消息"
        verbose_name_plural = "消息"

    def dict_description(self):
        result = dict(
            id=self.public_id,
            message_type=self.message_type,
            created_at=date_to_string(self.created_at),
            checked=self.checked,
            flag=self.flag,
            read=self.read,
            message_body=json.load(self.message_body),
            user=self.source.dict_description(),
            reserved=""
        )
        if self.related_status:
            result.update(status=self.related_status.dict_description())
        if self.related_comment:
            result.update(comment=self.related_comment.dict_description())
        return result


@receiver(send_notification)
def send_notification_handler(sender, message_type, namespace, message_body, source, target, **kwargs):
    create_param = dict(
        message_type=message_type,
        namespace=namespace,
        message_body=message_body,
        source=source,
        target=target,
        related_status=kwargs.get("status"),
        related_comment=kwargs.get("comment")
    )
    Message.objects.create(**create_param)
