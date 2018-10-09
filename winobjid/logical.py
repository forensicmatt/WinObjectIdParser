import pytsk3
from winobjid.tskio import FileInfo, TskFileIo


class Volume(object):
    """A class to process the logical volume."""
    def __init__(self, file_io):
        """Create LogicalEnumerator

        Params:
            file_io (FileIO): I file like object representing a volume.
            description (unicode): description of the volume
            temp_location (unicode): The location to extract files to
            cleanup (bool): Remove the temp folder after processesing
            output_template (unicode): The output template.
            dump_db (bool): True = Dump all database tables.
        """
        self.file_io = file_io
        self.tsk_fs = pytsk3.FS_Info(
            self.file_io
        )

    def get_obj_file(self):
        tsk_file = self.tsk_fs.open(
            "/$Extend/$ObjId"
        )
        for attr in tsk_file:
            if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_NTFS_IDXALLOC:
                if attr.info.name:
                    if attr.info.name == b"$O":
                        file_info = FileInfo(
                            "/$Extend/$ObjId", attr
                        )
                        return TskFileIo(
                            tsk_file, file_info
                        )
