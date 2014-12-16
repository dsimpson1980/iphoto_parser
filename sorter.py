#!/usr/env/python

import os
import subprocess
import logging

"""script to split iphoto database into directory structure by file metadata
dates; year, month, day

Overwrites files in directory of they exist

"""


def parse_timestamp(timestamp_str):
    import time
    import collections

    fields = ['year', 'month', 'day']
    TimeTuple = collections.namedtuple('TimeTuple', fields)
    t = time.strptime(timestamp_str, '%Y:%m:%d %H:%M:%S')
    return TimeTuple(t.tm_year, t.tm_mon, t.tm_mday)


def get_metadata(filepath):
    from PIL import Image
    import ExifTags

    img = Image.open(filepath)
    if img._getexif():
        exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items()
                if k in ExifTags.TAGS}
        return exif
    return None


def parse_cmdline():
    import argparse

    arg_parser = argparse.ArgumentParser(description='Parser for iphoto splitter')
    arg_parser.add_argument('libpath', help='path to iphoto db')
    arg_parser.add_argument('export_dir', help='base directory to export files')
    arg_parser.add_argument('--filter-by-model', default=False,
                            action='store_true')
    arg_parser.add_argument('--log-level', help='level of logging',
                            default='ERROR')
    args = arg_parser.parse_args()
    args.libpath = os.path.join(args.libpath, 'Masters')
    if not os.path.exists(args.export_dir):
        os.makedirs(args.export_dir)
    return args


def parse_files(args):
    os.path.walk(args.source_path, move_files, args)


def move_files(args, dirname, filenames):
    import re
    import fnmatch

    includes = ['*.jpg', '*.jpeg', '*.mpg', '*.mpeg']
    includes += [x.upper() for x in includes]
    includes = r'|'.join([fnmatch.translate(x) for x in includes])
    filenames = [f for f in filenames if re.match(includes, f)]

    for filename in filenames:
        filepath = os.path.join(dirname, filename)
        metadata = get_metadata(filepath)
        if not metadata:
            continue
        datetime = metadata.get('DateTime', '')
        timestamp = None if datetime == '' else parse_timestamp(datetime)
        timestamp_dir = '' if timestamp is None else os.path.join(
            str(timestamp.year), str(timestamp.month), str(timestamp.day))
        model = metadata.get('Model', '') if args.filter_by_model else ''
        file_dir = os.path.join(args.export_dir, model, timestamp_dir)
        if not os.path.exists(file_dir):
            logging.info('Created directory %s', file_dir)
            os.makedirs(file_dir)
        new_filepath = os.path.join(file_dir, filename)
        subprocess.call(['cp', filepath, new_filepath])
        logging.info('Copied %s', filepath)


def main():
    args = parse_cmdline()
    logging.basicConfig(datefmt='%y-%m-%d', level=args.log_level)
    parse_files(args.libpath)

if __name__ == '__main__':
    main()