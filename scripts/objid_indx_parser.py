import sys
sys.path.append("..")
import re
import json
import pytsk3
import logging
import argparse
from winobjid.index import ObjectIndexFile
from winobjid.logical import Volume


VALID_DEBUG_LEVELS = ["ERROR", "WARN", "INFO", "DEBUG"]
__VERSION__ = "0.0.1"


def set_debug_level(debug_level):
    if debug_level in VALID_DEBUG_LEVELS:
        logging.basicConfig(
            level=getattr(logging, debug_level)
        )
    else:
        raise (Exception("{} is not a valid debug level.".format(debug_level)))


def get_arguments():
    usage = u"""Parse the $O Index. The file can be found at \\$Extend\\$ObjId:$O.
    version: {}
    """.format(__VERSION__)

    arguments = argparse.ArgumentParser(
        description=usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    arguments.add_argument(
        "-s", "--source",
        dest="source",
        action="store",
        required=True,
        help="The $O Index or a logical volume (logical volume: \\\\.\\C:)."
    )
    arguments.add_argument(
        "-o", "--output_template",
        dest="output_template",
        action="store",
        required=False,
        default=None,
        help="Output template format."
    )
    arguments.add_argument(
        "--debug",
        dest="debug",
        action="store",
        default="ERROR",
        choices=VALID_DEBUG_LEVELS,
        help="Debug level [default=ERROR]"
    )

    return arguments


def parse_logical(options):
    out_template = None
    if options.output_template:
        out_template = options.output_template

    tsk_img = pytsk3.Img_Info(
        options.source
    )
    volume = Volume(
        tsk_img
    )
    file_io = volume.get_obj_file()
    if file_io:
        obj_id_file = ObjectIndexFile(
            file_io
        )
        for index_page in obj_id_file.iter_index_pages():
            for entry in index_page.iter_entries():
                if out_template:
                    print(
                        out_template.format(
                            **entry.as_dict()
                        )
                    )
                else:
                    print(
                        json.dumps(entry.as_dict())
                    )


def parse_file(options):
    out_template = None
    if options.output_template:
        out_template = options.output_template

    with open(options.source, 'rb') as fh:
        obj_id_file = ObjectIndexFile(
            fh
        )

        for index_page in obj_id_file.iter_index_pages():
            for entry in index_page.iter_entries():
                if out_template:
                    print(
                        out_template.format(
                            **entry.as_dict()
                        )
                    )
                else:
                    print(
                        json.dumps(entry.as_dict())
                    )


def main():
    arguments = get_arguments()
    options = arguments.parse_args()

    set_debug_level(
        options.debug
    )

    if re.match('\\\\\\\.\\\[a-zA-Z]:', options.source):
        parse_logical(options)
    else:
        parse_file(options)


if __name__ == "__main__":
    main()
