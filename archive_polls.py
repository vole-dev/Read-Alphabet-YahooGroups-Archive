"""
Yahoo-Groups-Archiver Copyright 2015, 2017-2019

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

from arc_utilities import retrieve_url, log


def archive_group_polls(s, group_name):
    poll_dir = os.path.join(os.curdir, group_name, 'polls')
    if not os.path.exists(poll_dir):
        os.makedirs(poll_dir)

    for poll_id in yield_walk_polls(s, group_name):
        archive_poll(s, group_name, poll_id)


def archive_poll(s, group_name, poll_id):
    poll_dir = os.path.join(os.curdir, group_name, 'polls')
    poll_path = os.path.join(poll_dir, f'{poll_id}.json')
    if os.path.isfile(poll_path):
        return

    print(f'Archiving poll {poll_id}')
    url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/polls/{poll_id}'
    resp, failure = retrieve_url(s, url, group_name)

    if failure:
        log(f'FAILURE. Unable to obtain poll data from {url}', group_name)
        return

    try:
        poll_json = json.loads(resp.text)['ygData']
    except ValueError as valueError:
        if 'mbr-login-greeting' in resp.text:
            # the user needs to be signed in to Yahoo
            print("Error. Yahoo login is not working")
            sys.exit()
        else:
            raise valueError

    del poll_json['viewerNickname']

    for selection in poll_json['selections']:
        for response in selection['responses']:
            del response['nickname']
            del response['email']

    with open(poll_path, 'w', encoding='utf-8') as writeFile:
        json.dump(poll_json, writeFile)


def yield_walk_polls(s, group_name):
    url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/polls'
    resp, failure = retrieve_url(s, url, group_name)

    if failure:
        log(f'FAILURE. Unable to obtain poll list from {url}', group_name)
        return

    try:
        polls_json = json.loads(resp.text)['ygData']
    except ValueError as valueError:
        if 'mbr-login-greeting' in resp.text:
            # the user needs to be signed in to Yahoo
            print("Error. Yahoo login is not working")
            sys.exit()
        else:
            raise valueError

    for poll in polls_json:
        yield poll['surveyId']
