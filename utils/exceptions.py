from __future__ import unicode_literals


class DeclarativeException(Exception):

    def as_response(self):
        raise NotImplementedError


class UserNotFoundException(DeclarativeException):

    def as_response(self):
        return "user not found"


class StatusNotFoundException(DeclarativeException):

    def as_response(self):
        return "status not found"


class CommentNotFoundException(DeclarativeException):

    def as_response(self):
        return "comment not found"
