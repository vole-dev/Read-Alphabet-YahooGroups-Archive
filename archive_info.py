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

from arc_utilities import retrieve_url, log, photo_info_url, save_file


def archive_group_info(s, group_name):
    info_path = os.path.join(os.curdir, group_name, 'info')
    if not os.path.exists(info_path):
        os.makedirs(info_path)

    info_url = f'https://groups.yahoo.com/api/v1/groups/{group_name}'
    resp, failure = retrieve_url(s, info_url, group_name)

    if failure:
        log(f'FAILURE. Unable to obtain info from {info_url}', group_name)
        return

    try:
        info_json = json.loads(resp.text)['ygData']
    except ValueError as valueError:
        if 'mbr-login-greeting' in resp.text:
            # the user needs to be signed in to Yahoo
            print("Error. Yahoo login is not working")
            sys.exit()
        else:
            raise valueError

    with open(os.path.join(info_path, 'info.json'), 'w', encoding='utf-8') as writeFile:
        json.dump(info_json, writeFile, indent=2)

    statistics_url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/statistics'
    resp, failure = retrieve_url(s, statistics_url, group_name)

    if failure:
        log(f'FAILURE. Unable to obtain info from {statistics_url}', group_name)
        return

    try:
        statistics_json = json.loads(resp.text)['ygData']
    except ValueError as valueError:
        if 'mbr-login-greeting' in resp.text:
            # the user needs to be signed in to Yahoo
            print("Error. Yahoo login is not working")
            sys.exit()
        else:
            raise valueError

    with open(os.path.join(info_path, 'statistics.json'), 'w', encoding='utf-8') as writeFile:
        json.dump(statistics_json, writeFile, indent=2)

    # download group photo
    group_photo_url = photo_info_url(statistics_json['groupHomePage']['photoInfo'])
    if group_photo_url:
        group_photo_filename = group_photo_url.split('?')[0].split('.')
        group_photo_ext = "" if len(group_photo_filename) < 2 else '.' + group_photo_filename[-1]
        save_file(s, os.path.join(info_path, f'groupPhoto{group_photo_ext}'), group_photo_url)

    # download group cover photo
    cover_photo_url = photo_info_url(statistics_json['groupCoverPhoto']['photoInfo'])
    if cover_photo_url:
        cover_photo_filename = cover_photo_url.split('?')[0].split('.')
        cover_photo_ext = "" if len(cover_photo_filename) < 2 else '.' + cover_photo_filename[-1]
        save_file(s, os.path.join(info_path, f'coverPhoto{cover_photo_ext}'), cover_photo_url)
