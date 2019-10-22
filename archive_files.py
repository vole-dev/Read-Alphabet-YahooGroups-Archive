"""
Yahoo-Groups-Archiver Copyright 2015, 2017-2019 Andrew Ferguson and others

YahooGroups-Archiver, a simple python script that allows for all
messages in a public Yahoo Group to be archived.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
from urllib.parse import unquote

from arc_utilities import save_file, save_meta, retrieve_json, log


def archive_group_files(s, group_name):
    file_dir = os.path.join(os.curdir, group_name, 'files')
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    metadata = {'dirEntries': {}}

    for file in yield_walk_files(s, group_name):
        update_file_meta(metadata, file)

        file_path = os.path.join(file_dir, *file['parent_dirs'], file['fileName'])
        if file['type'] == 0:
            # file handling
            if not os.path.isfile(file_path):
                print(f'Archiving file: {file_path}')
                save_file(s, file_path, file['downloadURL'])
        elif file['type'] == 1:
            # dir handing
            print(f'Archiving directory: {file_path}')
            if not os.path.exists(file_path):
                os.makedirs(file_path)

    save_meta(group_name, 'files-meta', metadata)


def update_file_meta(metadata, file):
    parent_meta = metadata
    for file_dir in file['parent_dirs']:
        parent_meta = parent_meta['dirEntries'][file_dir]

    if file['type'] == 1:
        file['dirEntries'] = {}

    parent_meta['dirEntries'][file['fileName']] = file


def yield_walk_files(s, group_name, path_uri=''):
    url = f'https://groups.yahoo.com/api/v2/groups/{group_name}/files'
    params = {'sort': 'FILENAME', 'order': 'ASC'}
    if path_uri:
        params['sfpath'] = unquote(path_uri)
    folder_json = retrieve_json(s, url, group_name, params=params)

    if not folder_json:
        log(f'FAILURE. Unable to obtain data from {url}', group_name)
        return

    for entry in folder_json['dirEntries']:
        entry['parent_dirs'] = list(map(lambda crumb: crumb['dirDisplayName'], folder_json['breadCrumb']))
        yield entry

        if entry['type'] == 1:
            # type == 1 for directories
            yield from yield_walk_files(s, group_name, entry['pathURI'])
        elif entry['type'] != 0:
            raise NotImplementedError('Unknown file entry type %s' % entry['type'])
