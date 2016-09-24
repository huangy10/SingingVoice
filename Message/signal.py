from __future__ import unicode_literals


from django.dispatch import Signal


send_notification = Signal(
    providing_args=["message_type", "namespace", "message_body", "source", "target"]
)
