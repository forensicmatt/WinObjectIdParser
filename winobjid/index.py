import struct
import logging
import binascii
from winobjid.objid import ObjectId
from winobjid.utils import NtfsReference


class InvalidIndexPageHeader(Exception):
    def __init__(self, message):
        super(InvalidIndexPageHeader, self).__init__(message)


class InvalidEntryFlag(Exception):
    def __init__(self, message):
        super(InvalidEntryFlag, self).__init__(message)


class IndexOEntry(object):
    def __init__(self, buf, offset=None, recover=False):
        self._offset = offset
        self._recovered = recover
        logging.debug("Index Entry at Offset: {}".format(self._offset))
        flag = struct.unpack("<H", buf[12:14])[0]
        if flag == 2:
            self._buffer = buf[0:88]
        elif flag in [0, 1]:
            data_offset = struct.unpack("<H", buf[0:2])[0]
            data_size = struct.unpack("<H", buf[2:4])[0]
            self._buffer = buf[0:data_offset+data_size]
        elif flag == 3:
            # This seems to be the end of the last page flag.
            self._buffer = buf[0:88]
        else:
            raise(
                InvalidEntryFlag(
                    "Invalid entry flag of {} at offset {}.".format(
                        flag, self._offset
                    )
                )
            )

    def is_last_entry(self):
        if self.flags in [2, 3]:
            return True
        return False

    def get_offset(self):
        return self._offset

    def is_valid(self):
        """Check if valid record. This is useful for unallocated parsing.
        """
        if self.flags == 2:
            if self._buffer[0:8] == "\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00":
                # This is a end record
                return True
        else:
            if self.flags in [0, 1]:
                if self.data_offset == 32:
                    if self.data_size == 56:
                        if self.entry_size == 88:
                            if self.key_size == 16:
                                return True
        return False

    def is_empty(self):
        if self._buffer[14:] == b"\x00"*74:
            return True
        return False

    @property
    def data_offset(self):
        """This should be 32 [0x20]"""
        return struct.unpack("<H", self._buffer[0:2])[0]

    @property
    def data_size(self):
        """This should be 56 [0x38]"""
        return struct.unpack("<H", self._buffer[2:4])[0]

    @property
    def padding1(self):
        return struct.unpack("<I", self._buffer[4:8])[0]

    @property
    def entry_size(self):
        """This should be 88 [0x58]"""
        if self.flags in [0, 1, 3]:
            entry_size = struct.unpack("<H", self._buffer[8:10])[0]
        else:
            entry_size = 88

        return entry_size

    @property
    def key_size(self):
        """This should be 16 [0x10]"""
        return struct.unpack("<H", self._buffer[10:12])[0]

    @property
    def flags(self):
        """1 = Entry has subnodes; 2 = Last Entry
        3 appears to be the last index in the file?
        """
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
            "recovered": self._recovered,
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
        # relative to offset 24
        return struct.unpack("<I", self._buffer[24:28])[0]

    @property
    def index_entry_size(self):
        """The size of the allocated entries block from the beginning
        of the index page.
        This value + 8 seems to point to the start of the end entry with
        a flag of 2 (the end entry has a flag of 2, but seems to be a
        have duplicate values of the last record).
        """
        return struct.unpack("<I", self._buffer[28:32])[0]

    @property
    def allocated_index_entry_size(self):
        """The size allocated for entries.
        This value + 24 + index_entry_offset will equal the size complete
        size of the INDX page.
        """
        return struct.unpack("<I", self._buffer[32:36])[0]

    @property
    def leaf_node(self):
        """1 appears to indicate the last allocated page of the file.
        """
        return struct.unpack("<B", self._buffer[36:37])[0]

    @property
    def update_sequence(self):
        return binascii.b2a_hex(
            self._buffer[40:42]
        )

    def as_dict(self):
        return {
            "signature": self.signature.hex(),
            "update_sequence_offset": self.update_sequence_offset,
            "update_sequence_size": self.update_sequence_size,
            "logfile_sequence_number": self.logfile_sequence_number,
            "vcn": self.vcn,
            "index_entry_offset": self.index_entry_offset,
            "index_entry_size": self.index_entry_size,
            "allocated_index_entry_size": self.allocated_index_entry_size,
            "leaf_node": self.leaf_node
        }


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

    def is_valid(self):
        if self.header.signature == b"INDX":
            return True
        return False

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

        while True:
            entry = IndexOEntry(
                self._index_block_buf[pointer:],
                offset=self._offset + pointer
            )
            if entry.is_last_entry():
                break

            pointer += entry.entry_size

            yield entry

    def iter_unalloc_entries(self):
        pointer = self.header.index_entry_size
        if not self.header.leaf_node:
            pointer += 8

        while True:
            if len(self._index_block_buf[pointer:]) > 88:
                entry = IndexOEntry(
                    self._index_block_buf[pointer:],
                    recover=True,
                    offset=self._offset + pointer
                )

                if entry.is_empty():
                    break

                if entry.flags == 3:
                    break

                pointer += 88
                yield entry
            else:
                break


class ObjectIndexFile(object):
    def __init__(self, file_handle):
        self._file_handle = file_handle
        self._offset = 0
        self._file_handle.seek(0, 2)
        self._file_size = self._file_handle.tell()
        self._file_handle.seek(0, 0)

    def iter_index_pages(self):
        while True:
            try:
                index = IndexPage(
                    self._file_handle,
                    offset=self._offset
                )
            except InvalidIndexPageHeader as error:
                logging.error("{}".format(error))
                break
            except Exception as error:
                logging.error("{}".format(error))
                break

            logging.info("{}".format(index.header.as_dict()))
            self._offset += index.get_page_size()

            yield index

            if self._offset >= self._file_size:
                break

            self._file_handle.seek(
                self._offset
            )
