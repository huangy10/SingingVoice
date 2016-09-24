from __future__ import unicode_literals

from django import forms
from django.contrib.gis.geos import Point
from Status.models import Status, Comment


class StatusNewForm(forms.ModelForm):

    def __init__(self, data=None, files=None, **kwargs):
        loc = data['loc']
        loc_des = loc['des']
        loc_point = Point(x=float(loc['lon']), y=float(loc['lat']))
        data.update(dict(loc_des=loc_des, location=loc_point))
        super(StatusNewForm, self).__init__(data, files, **kwargs)

    class Meta:
        model = Status

    def generate_error_report(self):
        return self.errors.items()[0][0]


class CommentNewForm(forms.ModelForm):

    class Meta:
        model = Comment

    def generate_error_report(self):
        return self.errors.items()[0][0]
