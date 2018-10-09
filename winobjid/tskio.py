import os
# Following template from https://github.com/log2timeline/dfvfs/blob/master/dfvfs/file_io/tsk_file_io.py


class FileInfo(object):
    def __init__(self, fullname, attribute):
        self.fullname = fullname
        self.filename = attribute.info.fs_file.name.name
        self.id = attribute.info.id
        self.type = attribute.info.type
        self.size = attribute.info.size
        self.attribute_name = attribute.info.name


class TskFileIo(object):
    """Class that implements a file-like object using pytsk3."""
    def __init__(self, tsk_file, tsk_file_info):
        """Initializes the file-like object.
        Args:
            tsk_file (File): the tsk File object
            tsk_file_info (FileInfo): The file info representing the tsk_file.
                                      This contains the attribute to read from.
        """
        self.tsk_file = tsk_file
        self.tsk_file_info = tsk_file_info
        self._current_offset = 0

    def read(self, size=None):
        """Implement the read functionality.
        Args:
            size: The size to read.
        Returns:
            bytes
        """

        if self._current_offset < 0:
            raise IOError(u'Invalid current offset value less than zero.')

        if self._current_offset >= self.tsk_file_info.size:
            return b''

        if size is None or self._current_offset + size > self.tsk_file_info.size:
            size = self.tsk_file_info.size - self._current_offset

        data = self.tsk_file.read_random(
            self._current_offset,
            size,
            self.tsk_file_info.type,
            self.tsk_file_info.id
        )

        self._current_offset += len(data)

        return data

    def seek(self, offset, whence=os.SEEK_SET):
        """Seeks an offset within the file-like object.
        Args:
            offset: The offset to seek.
            whence: Optional value that indicates whether offset is an absolute or relative position within the file.
        """
        if whence == os.SEEK_CUR:
            offset += self._current_offset

        elif whence == os.SEEK_END:
            offset += self.tsk_file_info.size
        elif whence != os.SEEK_SET:
            raise IOError(u'Unsupported whence.')

        if offset < 0:
            raise IOError(u'Invalid offset value less than zero.')

        self._current_offset = offset

    def get_offset(self):
        """Get the current offset.
        Returns:
            file offset
        """
        return self._current_offset

    def get_size(self):
        """Get the file's size.
        Returns:
            file size
        """
        return self.tsk_file_info.size

    def tell(self):
        """Alias for get_offset()
        Returns:
            file offset
        """
        return self.get_offset()
