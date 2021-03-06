# coding=utf-8
from __future__ import unicode_literals
import uuid

from django.db import models


class HasPublicID(object):

    public_id = models.CharField(max_length=40, verbose_name=u"对外id", default=uuid.uuid4, unique=True, db_index=True)

