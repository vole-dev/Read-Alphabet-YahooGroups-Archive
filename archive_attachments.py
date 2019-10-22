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

from arc_utilities import save_file, save_meta


def archive_group_attachments(s, group_name):
    att_dir = os.path.join(os.curdir, group_name, 'attachments')
    if not os.path.exists(att_dir):
        os.makedirs(att_dir)

    metadata = {}

    for att in yield_walk_attachments(s, group_name):
        update_attachment_meta(metadata, att)

        if att['attType'] == 'file':
            file_path = os.path.join(att_dir, str(att['attachmentId']), att['filename'])
            if not os.path.isfile(file_path):
                print(f'Archiving attachment: {file_path}')
                if att['type'] == 'photo':
                    url = att['photoInfo']['displayURL']
                elif att['type'] == 'file':
                    url = att['link']
                else:
                    raise ValueError('unsupported attachment type: %s' % att['type'])
                url = f'{url}?download=1'
                attachment_id = att['attachmentId']
                referer = f'https://groups.yahoo.com/neo/groups/{group_name}/attachments/{attachment_id}'

                # Sometimes yahoo responds that it won't serve files if you're not coming from a Yahoo Groups page
                # Getting the attachment page, saving the cookies, and using the page as a referer MIGHT help prevent
                # that. I do not know for sure
                s.get(referer)

                save_file(s, file_path, url, referer=referer)
        elif att['attType'] == 'group':
            att_path = os.path.join(att_dir, str(att['attachmentId']))
            if not os.path.exists(att_path):
                os.makedirs(att_path)

    save_meta(group_name, 'attachments-meta', metadata)


def update_attachment_meta(metadata, att):
    if att['attType'] == 'group':
        metadata[att['attachmentId']] = att
        metadata[att['attachmentId']]['files'] = []
    elif att['attType'] == 'file':
        metadata[att['attachmentId']]['files'].append(att)


def yield_walk_attachments(s, group_name):
    url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/attachments'
    resp = s.get(url)

    att_list_json = json.loads(resp.text)

    for att in att_list_json['ygData']['attachments']:
        attachment_id = att['attachmentId']
        yield {
            'attType': 'group',
            'groupId': att['groupId'],
            'attachmentId': attachment_id,
            'msgTitle': att['title'],
            'author': att['creatorNickname'],
            'modificationDate': att['modificationDate'],
            'total': att['total'],
            'referenceId': att['referenceId'],
        }

        att_url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/attachments/{attachment_id}'
        resp = s.get(att_url)
        att_json = json.loads(resp.text)['ygData']

        for file in att_json['files']:
            yield_data = {
                'attType': 'file',
                'attachmentId': file['attachmentId'],
                'fileId': file['fileId'],
                'title': file['title'],
                'size': file['size'],
                'filename': file['filename'],
                'fileType': file['fileType'],
                'type': file['type'],
            }

            if file['type'] == 'photo':
                # The last photoInfo seems to hold the original image, but this might be wrong
                # has 5 fields: displayURL, height, width, size, photoType
                photo_info = file['photoInfo'][-1]
                yield_data['photoInfo'] = photo_info
            elif file['type'] == 'file':
                yield_data['link'] = file['link']

            yield yield_data
    return
