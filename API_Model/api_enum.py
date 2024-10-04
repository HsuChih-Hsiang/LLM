from enum import Enum, unique

@unique
class FileType(Enum):
    UNDEFINED = 1
    PDF = 2
    TEXT = 3
    