#!/usr/bin/env python
# -*- coding: utf-8 -*-
# BASC Imageboard Archiver Utilities
from __future__ import absolute_import
from __future__ import print_function
import codecs
import json
import jsonmerge
import os
import re
import time

import requests


def mkdirs(path):
    """Make directory, if it doesn't exist."""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:  # folder exists, due to multithreading
        pass


def download_file(local_filename, url, clobber=False):
    """Download the given file. Clobber overwrites file if exists."""
    dir_name = os.path.dirname(local_filename)
    mkdirs(dir_name)

    if clobber or not os.path.exists(local_filename):
        i = requests.get(url)

        # if not exists
        if i.status_code == 404:
            print('Failed to download file:', local_filename, url)
            return False

        # write out in 1MB chunks
        chunk_size_in_bytes = 1024*1024  # 1MB
        with open(local_filename, 'wb') as local_file:
            for chunk in i.iter_content(chunk_size=chunk_size_in_bytes):
                local_file.write(chunk)

    return True

def download_json(local_filename, url, clobber=False):
    """Download the given JSON file, and pretty-print before we output it."""
    if download_file(local_filename, url, clobber):
        # read original json
        original_data = json.loads(open(local_filename).read())

        # write reformatted json
        with open(local_filename, 'w') as json_file:
            json_file.write(json.dumps(original_data, sort_keys=True, indent=2, separators=(',', ': ')))

        # merge/save the previous json to save deleted comments
        local_filename_merged = os.path.splitext(local_filename)[0] + '.merged.json'
        if not os.path.exists(local_filename_merged):
            print(local_filename_merged + " doesn't exist: CREATING!")
            with open(local_filename_merged, 'w+') as temp_f:
                temp_f.write('{"posts":[]}')
        previous_json = {}
        with open(local_filename_merged, 'r+') as old_json_file:
            previous_json = json.loads(old_json_file.read())
        with open(local_filename_merged, 'w+') as merge_json_file:
            merged_json = jsonmerge.merge(original_data, previous_json, {
                'properties': {
                    'posts': {
                        'mergeStrategy': 'arrayMergeByIndex'
                    }
                }
            })
            merge_json_file.write(json.dumps(merged_json, sort_keys=True, indent=2, separators=(',', ': ')))

def file_replace(local_filename, pattern, replacement):
    """Regex replace in the given file."""
    # can't use fileinput lib here because utf-8
    temp_new_filename = '{}-temporary'.format(local_filename)
    with codecs.open(local_filename, 'r', encoding='utf-8') as fi:
        with codecs.open(temp_new_filename, 'w', encoding='utf-8') as fo:
            for line in fi:
                fo.write(re.sub(pattern, replacement, line))
    os.remove(local_filename)
    os.rename(temp_new_filename, local_filename)


def timestamp():
    """Return a timestamp for right now."""
    now = time.time()
    localtime = time.localtime(now)
    return time.strftime('%Y-%m-%d %H:%M:%S', localtime)
