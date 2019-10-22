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
import sys

from arc_utilities import photo_info_url, save_file, save_meta, retrieve_url, log


def archive_group_photos(s, group_name):
    photo_dir = os.path.join(os.curdir, group_name, 'photos')
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)

    metadata = {}

    for photo in yield_walk_photos(s, group_name):
        photo_id = photo['photoId']
        metadata[photo_id] = photo

        photo_filename = photo['photoFilename'].split('.')
        file_ext = "" if len(photo_filename) < 2 else '.' + photo_filename[-1]
        file_path = os.path.join(photo_dir, str(photo['photoId']) + file_ext)
        if not os.path.isfile(file_path):
            print(f'Archiving photo: {photo_id}')
            url = photo_info_url(photo['photoInfo']) + '?download=1'
            save_file(s, file_path, url)

    save_meta(group_name, 'photos-meta', metadata)


def yield_walk_photos(s, group_name):
    url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/photos'
    resp, failure = retrieve_url(s, url, group_name)

    if failure:
        log(f'Unable to obtain photo list from {url}', group_name)
        return

    try:
        photo_list_json = json.loads(resp.text)
    except ValueError as valueError:
        if 'mbr-login-greeting' in resp.text:
            # the user needs to be signed in to Yahoo
            print("Error. Yahoo login is not working")
            sys.exit()
        else:
            raise valueError

    for photo in photo_list_json['ygData']:
        source = photo['source']
        if source == 'MAIL':
            continue  # Do not download attachments as a photo
        yield photo
    return
