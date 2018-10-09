import struct
import logging
import binascii
from winobjid.objid import ObjectId
from winobjid.utils import NtfsReference


class InvalidIndexPageHeader(Exception):
    def __init__(self, message):
        super(InvalidIndexPageHeader, self).__init__(message)


class IndexOEntry(object):
    def __init__(self, buf, offset=None):
        self._offset = offset
        logging.debug("Index Entry at Offset: {}".format(self._offset))
        offset = struct.unpack("<H", buf[0:2])[0]
        size = struct.unpack("<H", buf[2:4])[0]
        self._buffer = buf[0:offset+size]

    def get_offset(self):
        return self._offset

    @property
    def data_offset(self):
        """This should be 32"""
        return struct.unpack("<H", self._buffer[0:2])[0]

    @property
    def data_size(self):
        """This should be 56"""
        return struct.unpack("<H", self._buffer[2:4])[0]

    @property
    def entry_size(self):
        """This should be 88"""
        return struct.unpack("<H", self._buffer[8:10])[0]

    @property
    def key_size(self):
        """This should be 16"""
        return struct.unpack("<H", self._buffer[10:12])[0]

    @property
    def flags(self):
        """1 = Entry has subnodes; 2 = Last Entry"""
        return struct.unpack("<H", self._buffer[12:14])[0]

    @property
    def object_id(self):
        return ObjectId(self._buffer[16:32])

    @property
    def mft_reference(self):
        return NtfsReference(
            self._buffer[32:40]
        )

    @property
    def birth_volume(self):
        return ObjectId(self._buffer[40:56])

    @property
    def birth_object(self):
        return ObjectId(self._buffer[56:72])

    @property
    def birth_domain(self):
        return ObjectId(self._buffer[72:88])

    def as_dict(self):
        return {
            "offset": self._offset,
            "flags": self.flags,
            "object_id": self.object_id.as_dict(),
            "mft_reference": self.mft_reference.as_dict(),
            "birth_volume": self.birth_volume.as_dict(),
            "birth_object": self.birth_object.as_dict(),
            "birth_domain": self.birth_domain.as_dict()
        }


class IndexHeader(object):
    def __init__(self, buf):
        update_seq_off = struct.unpack("<H", buf[4:6])[0]
        update_seq_size = struct.unpack("<H", buf[6:8])[0]
        self._buffer = bytearray(buf[0:update_seq_off+update_seq_size*2])

    def block_size(self):
        """The block size of the index will be the update sequence size - 1 * 512.
        The update sequence array gets applied every 512 bytes (the first 2 bytes is the value)
        """
        return (self.update_sequence_size - 1) * 512

    def get_fixup_array(self):
        """Return the update sequence array as a list of 2 bytes each.
        """
        so = self.update_sequence_offset
        eo = self.update_sequence_offset+(self.update_sequence_size*2)
        raw_buf = self._buffer[so:eo]
        return [raw_buf[i:i + 2] for i in range(0, len(raw_buf), 2)]

    @property
    def signature(self):
        return bytes(self._buffer[0:4])

    @property
    def update_sequence_offset(self):
        return struct.unpack("<H", self._buffer[4:6])[0]

    @property
    def update_sequence_size(self):
        return struct.unpack("<H", self._buffer[6:8])[0]

    @property
    def logfile_sequence_number(self):
        return struct.unpack("<Q", self._buffer[8:16])[0]

    @property
    def vcn(self):
        return struct.unpack("<Q", self._buffer[16:24])[0]

    @property
    def index_entry_offset(self):
        return struct.unpack("<I", self._buffer[24:28])[0]

    @property
    def index_entry_size(self):
        return struct.unpack("<I", self._buffer[28:32])[0]

    @property
    def allocated_index_entry_size(self):
        return struct.unpack("<I", self._buffer[32:36])[0]

    @property
    def leaf_node(self):
        return struct.unpack("<B", self._buffer[36:37])[0]

    @property
    def update_sequence(self):
        return binascii.b2a_hex(
            self._buffer[40:42]
        )


class IndexPage(object):
    def __init__(self, file_handle, offset):
        self._offset = offset
        logging.debug("Parsing Index Page at offset: {}".format(self._offset))
        raw_buffer = file_handle.read(64)

        if not bytes(raw_buffer[0:4]) == b"INDX":
            raise(
                InvalidIndexPageHeader(
                    "Invalid Page Header Signature [{}] at offset: {}".format(
                        bytes(raw_buffer[0:4]),
                        self._offset
                    )
                )
            )

        self.header = IndexHeader(
            raw_buffer
        )
        block_size = self.header.block_size()
        self._index_block_buf = bytearray(
            raw_buffer + file_handle.read(
                block_size - 64
            )
        )
        self._fix_raw_block()

    def get_page_size(self):
        return self.header.block_size()

    def _fix_raw_block(self):
        """Apply the update sequence array to their respected offsets.
        """
        fix_up_array = self.header.get_fixup_array()

        # first item in array is the update sequence value
        for i in range(self.header.update_sequence_size-1):
            v1 = fix_up_array[i+1][0]
            v2 = fix_up_array[i + 1][1]
            self._index_block_buf[(i*512)+510] = v1
            self._index_block_buf[(i*512)+511] = v2

    def iter_entries(self):
        pointer = self.header.index_entry_offset + 24
        entry = IndexOEntry(
            self._index_block_buf[pointer:],
            offset=self._offset+pointer
        )
        pointer += entry.entry_size

        while True:
            yield entry

            if pointer >= self.header.index_entry_size:
                break

            entry = IndexOEntry(
                self._index_block_buf[pointer:],
                offset=self._offset+pointer
            )
            pointer += entry.entry_size


class ObjectIndexFile(object):
    def __init__(self, file_handle):
        self._file_handle = file_handle
        self._offset = 0
        self._file_handle.seek(0, 2)
        self._file_size = self._file_handle.tell()
        self._file_handle.seek(0, 0)

    def iter_index_pages(self):
        index = IndexPage(
            self._file_handle,
            offset=self._offset
        )
        self._offset += index.get_page_size()

        while True:
            yield index

            if self._offset == self._file_size:
                break

            self._file_handle.seek(
                self._offset
            )

            try:
                index = IndexPage(
                    self._file_handle,
                    offset=self._offset
                )
            except InvalidIndexPageHeader as error:
                logging.error(error)
                break

            self._offset += index.get_page_size()
