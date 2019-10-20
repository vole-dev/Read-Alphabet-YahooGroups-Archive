"""
Yahoo-Groups-Archiver Copyright 2015, 2017, 2018 Andrew Ferguson and others

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

import glob  # required to find the most recent message downloaded
import json  # required for reading various JSON attributes from the content
import os  # required for checking if a file exists locally
import shutil  # required for deleting an old folder
import sys  # required to cancel script if blocked by Yahoo
import time  # required to log the date and time of run

import mechanize
import requests  # required for fetching the raw messages
from lxml import html

user_agent = 'Mozilla/4.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'


def login_and_archive(group_name, action, username, password):
    s = login_session(username, password)
    if not s:
        return
    archive_group(s, group_name, action)


def login_session(username, password):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', user_agent)]

    # Open login page
    br.open('https://login.yahoo.com/')

    time.sleep(0.1)
    # Submit username
    br.select_form(nr=0)
    br['username'] = username
    resp = br.submit()
    if 'messages.ERROR_INVALID_IDENTIFIER' in str(resp.get_data()):
        print("Error. Username not accepted. 'Sorry, we don't recognize this account' message from Yahoo.")
        return None
    if 'messages.ERROR_INVALID_USERNAME' in str(resp.get_data()):
        print("Error. Username not accepted. 'Sorry, we don't recognize this email' message from Yahoo.")
        return None

    time.sleep(0.1)
    # Submit password
    br.select_form(nr=0)
    br['password'] = password
    resp = br.submit()
    if 'messages.ERROR_INVALID_PASSWORD' in str(resp.get_data()):
        print("Error. Password not accepted. 'Invalid password' message from Yahoo.")
        return None

    # Create a session with the cookies obtained by signing in
    s = requests.Session()
    s.cookies = br.cookiejar
    s.headers['User-Agent'] = user_agent

    br.close()
    return s


def archive_group(s, group_name, mode="update"):
    log("\nArchiving group '" + group_name + "', mode: " + mode + " , on " + time.strftime("%c"), group_name)
    start_time = time.time()
    msgs_archived = 0

    message_dir = os.path.join(os.curdir, group_name, 'messages')
    if mode == "retry":
        # don't archive any messages we already have
        # but try to archive ones that we don't, and may have
        # already attempted to archive
        min_msg = 1
    elif mode == "update":
        # start archiving at the last+1 message message we archived
        most_recent = 1
        if os.path.exists(message_dir):
            old_dir = os.getcwd()
            os.chdir(message_dir)
            for file in glob.glob("*.json"):
                if int(file[0:-5]) > most_recent:
                    most_recent = int(file[0:-5])
            os.chdir(old_dir)

        min_msg = most_recent
    elif mode == "restart":
        # delete all previous archival attempts and archive everything again
        if os.path.exists(message_dir):
            shutil.rmtree(message_dir)
        min_msg = 1
    elif mode == "files":
        archive_group_files(s, group_name)
        log("files archive finished", group_name)
        return
    elif mode == "attachments":
        archive_group_attachments(s, group_name)
        log("attachment archive finished", group_name)
        return
    else:
        print("You have specified an invalid mode (" + mode + ").")
        print(
            "Valid modes are:\nupdate - add any new messages to the archive\nretry - attempt to get all messages that "
            "are not in the archive\nrestart - delete archive and start from scratch")
        sys.exit()

    if not os.path.exists(message_dir):
        os.makedirs(message_dir)
    max_msg = group_messages_max(s, group_name)
    for x in range(min_msg, max_msg + 1):
        if not os.path.isfile(os.path.join(message_dir, str(x) + ".json")):
            print("Archiving message " + str(x) + " of " + str(max_msg))
            success = archive_message(s, group_name, x)
            if success:
                msgs_archived = msgs_archived + 1

    log("Archive finished, archived " + str(msgs_archived) + ", time taken is " + str(
        time.time() - start_time) + " seconds", group_name)


def group_messages_max(s, group_name):
    resp = s.get(
        'https://groups.yahoo.com/api/v1/groups/' + group_name + '/messages?count=1&sortOrder=desc&direction=-1')
    page_html = resp.text
    try:
        page_json = json.loads(page_html)
    except ValueError as valueError:
        if "Stay signed in" in page_html and "Trouble signing in" in page_html:
            # the user needs to be signed in to Yahoo
            print(
                "Error. The group you are trying to archive is a private group. To archive a private group using this "
                "tool, login to a Yahoo account that has access to the private groups, then extract the data from the "
                "cookies Y and T from the domain yahoo.com . Paste this data into the appropriate variables (cookie_Y "
                "and cookie_T) at the top of this script, and run the script again.")
            sys.exit()
        else:
            raise valueError
    return page_json["ygData"]["totalRecords"]


def archive_message(s, group_name, msg_number):
    resp, failed = retrieve_url(s, f'https://groups.yahoo.com/api/v1/groups/{group_name}/messages/{msg_number}',
                                group_name)

    if failed:
        return False

    resp_raw, failed = retrieve_url(s, f'https://groups.yahoo.com/api/v1/groups/{group_name}/messages/{msg_number}/raw',
                                    group_name)

    if failed:
        return False

    msg_json = json.loads(resp.text)
    msg_raw_json = json.loads(resp_raw.text)
    msg_json['ygData']['rawEmail'] = msg_raw_json['ygData']['rawEmail']

    with open(os.path.join(group_name, 'messages', str(msg_number) + ".json"), "w", encoding='utf-8') as writeFile:
        json.dump(msg_json, writeFile)
    return True


def retrieve_url(s, url, group_name):
    failed = False
    resp = s.get(url)
    if resp.status_code != 200:
        if resp.status_code == 500:
            # we are most likely being blocked by Yahoo
            log("Archive halted - it appears Yahoo has blocked you.", group_name)
            log(
                "Check if you can access the group's homepage from your browser. If you can't, you have been "
                "blocked.",
                group_name)
            log(
                "Don't worry, in a few hours (normally less than 3) you'll be unblocked and you can run this "
                "script again - it'll continue where you left off.",
                group_name)
            sys.exit()
        log("Failed to retrieve url " + url + " due to HTTP status code " + str(resp.status_code),
            group_name)
        failed = True
    return resp, failed


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


def save_file(s, file_path, url, referer=''):
    resp = s.get(url, headers={'referer': referer})

    with open(file_path, "wb") as writeFile:
        writeFile.write(resp.content)


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


def save_meta(group_name, name, metadata):
    with open(os.path.join(os.curdir, group_name, f'{name}.json'), 'w') as writeFile:
        json.dump(metadata, writeFile, indent=2)


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


def first_or_empty(l):
    return l[0] if l else ''


def log(msg, group_name):
    print(msg)
    if writeLogFile:
        log_f = open(group_name + ".txt", "a")
        log_f.write("\n" + msg)
        log_f.close()


writeLogFile = True
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if "nologs" in sys.argv:
        print("Logging mode OFF")
        writeLogFile = False
        sys.argv.remove("nologs")
    if len(sys.argv) >= 5:
        login_and_archive(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print('This script requires parameters to run:')
        print('python archive_group.py <groupName> <action> <username> <password> [nologs]')
        print('Available actions are: update, retry, restart, files, attachments')
