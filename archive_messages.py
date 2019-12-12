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

from arc_utilities import retrieve_url, log


def archive_group_messages(s, group_name):
    message_dir = os.path.join(os.curdir, group_name, 'messages')
    if not os.path.exists(message_dir):
        os.makedirs(message_dir)

    for msg_number in yield_walk_messages(s, group_name):
        archive_message(s, group_name, msg_number)
    return


def archive_message(s, group_name, msg_number):
    message_dir = os.path.join(os.curdir, group_name, 'messages')
    if os.path.isfile(os.path.join(message_dir, str(msg_number) + ".json")):
        return  # skip messages that have already been downloaded

    print("Archiving message " + str(msg_number))
    resp, failed = retrieve_url(s, f'https://groups.yahoo.com/api/v1/groups/{group_name}/messages/{msg_number}',
                                group_name)

    if failed:
        return False

    resp_raw, failed = retrieve_url(s, f'https://groups.yahoo.com/api/v1/groups/{group_name}/messages/{msg_number}/raw',
                                    group_name)

    if failed:
        return False

    try:
        msg_json = json.loads(resp.text)['ygData']
        msg_raw_json = json.loads(resp_raw.text)['ygData']
    except ValueError as valueError:
        if 'mbr-login-greeting' in resp.text:
            # the user needs to be signed in to Yahoo
            print("Error. Yahoo login is not working")
            sys.exit()
        else:
            raise valueError

    msg_json['rawEmail'] = msg_raw_json['rawEmail']

    with open(os.path.join(message_dir, str(msg_number) + ".json"), "w", encoding='utf-8') as writeFile:
        json.dump(msg_json, writeFile, indent=2)
    return True


def yield_walk_messages(s, group_name):
    url_base = f'https://groups.yahoo.com/api/v1/groups/{group_name}/messages?start=%s&count=1000&sortOrder=asc&direction=1'

    first_message = 1
    while True:
        resp, failure = retrieve_url(s, url_base % first_message, group_name)

        if failure:
            log(f'FAILURE. Unable to obtain message list from %s' % url_base % first_message, group_name)
            return

        try:
            message_list = json.loads(resp.text)['ygData']['messages']
        except ValueError as valueError:
            if 'mbr-login-greeting' in resp.text:
                # the user needs to be signed in to Yahoo
                print("Error. Yahoo login is not working")
                sys.exit()
            else:
                raise valueError

        if not message_list or message_list[0]['messageId'] < first_message:
            # Once first_message passes the end message, the api will always return the last message
            break
        else:
            first_message = message_list[-1]['messageId'] + 1

        for message in message_list:
            yield message['messageId']

    return
