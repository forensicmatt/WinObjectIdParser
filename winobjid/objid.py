import struct
import datetime
from winobjid.utils import FileTime


class ObjectId(object):
    """Represents a raw Object ID (UUID)
    """
    def __init__(self, buf):
        self._buffer = buf

    @property
    def timestamp(self):
        # http://computerforensics.parsonage.co.uk/downloads/TheMeaningofLIFE.pdf
        # The file ObjectID is a time based version which means it is created using a system time.
        # The time is a 60 bit time value, a count of 100 nanosecond intervals of UTC since midnight
        # at the start of 15th October 1582.

        # Get le uint64
        le_timestamp = struct.unpack("<Q", self._buffer[0:8])[0]

        # remove first 4 bits used for version
        le_timestamp = le_timestamp - (le_timestamp & 0xf000000000000000)

        # see http://computerforensics.parsonage.co.uk/downloads/TheMeaningofLIFE.pdf
        le_timestamp = le_timestamp - 5748192000000000

        dt_object = datetime.datetime(1601, 1, 1) + datetime.timedelta(
            microseconds=le_timestamp / 10
        )

        # filetime is 100 nanosecond resolution
        nanoseconds = str(le_timestamp % 10000000).zfill(7) + '00'

        filetime = FileTime.from_dt_object(
            dt_object, nanoseconds=nanoseconds
        )

        return filetime

    @property
    def timestamp_uint64(self):
        le_timestamp = struct.unpack("<Q", self._buffer[0:8])[0]
        le_timestamp = le_timestamp - (le_timestamp & 0xf000000000000000)
        return le_timestamp

    @property
    def version(self):
        high_order = struct.unpack(">H", self._buffer[6:8])[0]
        return high_order & 0x000f

    @property
    def variant(self):
        field = struct.unpack(">H", self._buffer[8:10])[0]
        return field >> 14

    @property
    def sequence(self):
        field = struct.unpack(">H", self._buffer[8:10])[0]
        return field & 0x3FFF

    @property
    def mac(self):
        return self._buffer[10:16].hex()

    def as_dict(self):
        return {
            "uuid": str(self),
            "hex": self._buffer.hex(),
            "timestamp": str(self.timestamp),
            "timestamp_uint64": self.timestamp_uint64,
            "version": self.version,
            "variant": self.variant,
            "sequence": self.sequence,
            "mac": self.mac
        }

    def __str__(self):
        return "{:08x}-{:04x}-{:04x}-{:02x}{:02x}-{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(
            struct.unpack("<L", self._buffer[0:4])[0],
            struct.unpack("<H", self._buffer[4:6])[0],
            struct.unpack("<H", self._buffer[6:8])[0],
            struct.unpack("<B", self._buffer[8:9])[0],
            struct.unpack("<B", self._buffer[9:10])[0],
            struct.unpack("<B", self._buffer[10:11])[0],
            struct.unpack("<B", self._buffer[11:12])[0],
            struct.unpack("<B", self._buffer[12:13])[0],
            struct.unpack("<B", self._buffer[13:14])[0],
            struct.unpack("<B", self._buffer[14:15])[0],
            struct.unpack("<B", self._buffer[15:16])[0]
        )
