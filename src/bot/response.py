from enum import Enum


class ResponseType(Enum):
    TEXT = 1
    IMAGE = 2
    TEXT_AND_IMAGE = 3


class Response:
    def __init__(self, text=None, image=None, type=ResponseType.TEXT):
        self.text = text
        self.image = image
        self.type = type
