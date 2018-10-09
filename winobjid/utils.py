import struct
import datetime


class FileTime(datetime.datetime):
    """datetime.datetime object is immutable, so we will create a class to inherit
    datetime.datetime so we can set a custom nanosecond.
    """
    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)

    @staticmethod
    def from_dt_object(dt_object, nanoseconds=0):
        ft = FileTime(
            dt_object.year,
            dt_object.month,
            dt_object.day,
            dt_object.hour,
            dt_object.minute,
            dt_object.second,
            dt_object.microsecond
        )
        ft.nanoseconds = nanoseconds
        return ft

    def __str__(self):
        return "{0.year}-{0.month:02}-{0.day:02} {0.hour:02}:{0.minute:02}:{0.second:02}.{0.nanoseconds}".format(self)


class NtfsReference(object):
    def __init__(self, buf):
        self._buffer = buf

    @property
    def reference(self):
        return struct.unpack("<Q", self._buffer[0:8])[0]

    @property
    def entry(self):
        return struct.unpack("<IH", self._buffer[0:6])[0]

    @property
    def sequence(self):
        return struct.unpack("<H", self._buffer[6:8])[0]

    def as_dict(self):
        return {
            "reference": self.reference,
            "entry": self.entry,
            "sequence": self.sequence
        }
