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

import json
import os
from lxml import html

from arc_utilities import save_file, save_meta


def archive_group_files(s, group_name):
    file_dir = os.path.join(os.curdir, group_name, 'files')
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    metadata = {'.': {'fileType': 'dir', 'description': '', 'author': '', 'date': '', 'children': {}}}

    for file in yield_walk_files(s, group_name):
        update_file_meta(metadata, file)

        file_path = os.path.join(file_dir, *file['parentDir'], file['name'])
        if file['fileType'] == 'data':
            if not os.path.isfile(file_path):
                print(f'Archiving file: {file_path}')
                save_file(s, file_path, file['url'])
        elif file['fileType'] == 'dir':
            print(f'Archiving directory: {file_path}')
            if not os.path.exists(file_path):
                os.makedirs(file_path)

    save_meta(group_name, 'files-meta', metadata)


def update_file_meta(metadata, file):
    parent_meta = metadata['.']
    for file_dir in file['parentDir']:
        parent_meta = parent_meta['children'][file_dir]

    if file['fileType'] == 'data':
        meta = {
            'fileType': 'data',
            'description': file['description'],
            'author': file['author'],
            'date': file['date'],
            'mime': file['mime'],
            'size': file['size'],
        }

        parent_meta['children'][file['name']] = meta
    elif file['fileType'] == 'dir':
        meta = {
            'fileType': 'dir',
            'description': file['description'],
            'author': file['author'],
            'date': file['date'],
            'children': {},
        }
        parent_meta['children'][file['name']] = meta


def first_or_empty(l):
    return l[0] if l else ''


def yield_walk_files(s, group_name, url_path='.', parent_dir=None):
    if parent_dir is None:
        parent_dir = []

    url = f'https://groups.yahoo.com/neo/groups/{group_name}/files/{url_path}/'
    resp = s.get(url)

    tree = html.fromstring(resp.text)

    for el in tree.xpath('//*[@data-file]'):
        data = json.loads('{%s}' % el.attrib['data-file'].encode('utf-8').decode('unicode-escape'))
        if data['fileType'] == 'f':
            yield {
                'fileType': 'data',
                'name': el.xpath('.//a/text()')[0],
                'description': first_or_empty(el.xpath('.//span/text()')),
                'parentDir': parent_dir,
                'author': first_or_empty(el.xpath('.//*[@class="yg-list-auth"]/text()')),  # author of the file
                'date': first_or_empty(el.xpath('.//*[@class="yg-list-date"]/text()')),  # upload date

                'url': el.xpath('.//@href')[0],
                'mime': data['mime'],
                'size': float(data['size']),
            }
        elif data['fileType'] == 'd':
            name = el.xpath('.//a/text()')[0]
            yield {
                'fileType': 'dir',
                'name': name,
                'description': first_or_empty(el.xpath('.//span/text()')),
                'parentDir': parent_dir,
                'author': first_or_empty(el.xpath('.//*[@class="yg-list-auth"]/text()')),  # author of the file
                'date': first_or_empty(el.xpath('.//*[@class="yg-list-date"]/text()')),  # upload date
            }
            yield from yield_walk_files(s, group_name, data['filePath'], [*parent_dir, name])
        else:
            raise NotImplementedError("Unknown fileType %s, data was %s" % (
                data['fileType'], json.dumps(data),
            ))
    return
