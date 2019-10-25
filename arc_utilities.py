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
import time
from http.cookiejar import MozillaCookieJar

import requests
from bs4 import BeautifulSoup


def login_session(username, password, save_and_load_cookies=True):
    s = requests.Session()
    s.headers['User-Agent'] = 'Mozilla/4.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'
    s.cookies = MozillaCookieJar()

    # load cookies from file if we can
    cookie_file = 'PRIVATE_DATA_DO_NOT_SHARE.cookies'
    if save_and_load_cookies:
        if os.path.isfile(cookie_file):
            s.cookies.load(cookie_file)
            return s

    # if not loading cookies from file, get them by logging in

    # Open login page
    resp = s.get('https://login.yahoo.com/')
    if resp.status_code != 200:
        print('Error. Login page returned with status code %s' % resp.status_code)
        return None

    # Submit username
    time.sleep(0.1)
    soup = BeautifulSoup(resp.text, "html5lib")
    post_data = {'username': username}
    set_post_param(post_data, soup, 'acrumb')
    set_post_param(post_data, soup, 'sessionIndex')
    set_post_param(post_data, soup, 'passwd')
    set_post_param(post_data, soup, 'signin')
    set_post_param(post_data, soup, 'persistent')

    resp = s.post(resp.url, data=post_data)
    if resp.status_code != 200:
        print('Error. Username POST message returned with status code %s' % resp.status_code)
        return None
    if 'messages.ERROR_INVALID_IDENTIFIER' in resp.text:
        print("Error. Username not accepted. 'Sorry, we don't recognize this account' message from Yahoo.")
        return None
    if 'messages.ERROR_INVALID_USERNAME' in resp.text:
        print("Error. Username not accepted. 'Sorry, we don't recognize this email' message from Yahoo.")
        return None

    # Submit password
    time.sleep(0.1)
    soup = BeautifulSoup(resp.text, "html5lib")
    post_data = {'password': password}
    set_post_param(post_data, soup, 'browser-fp-data')
    set_post_param(post_data, soup, 'crumb')
    set_post_param(post_data, soup, 'acrumb')
    set_post_param(post_data, soup, 'sessionIndex')
    set_post_param(post_data, soup, 'displayName')
    set_post_param(post_data, soup, 'username')
    set_post_param(post_data, soup, 'passwordContext')
    set_post_param(post_data, soup, 'verifyPassword')

    resp = s.post(resp.url, data=post_data)
    if resp.status_code != 200:
        print('Error. Password POST message returned with status code %s' % resp.status_code)
        return None
    if 'messages.ERROR_INVALID_PASSWORD' in resp.text:
        print("Error. Password not accepted. 'Invalid password' message from Yahoo.")
        return None

    if save_and_load_cookies:
        s.cookies.save(cookie_file)

    return s


def set_post_param(post_data, soup, param):
    post_data[param] = soup.find(attrs={'name': param}).attrs.get('value', None)


def save_file(s, file_path, url, referer=''):
    resp = s.get(url, headers={'referer': referer})

    with open(file_path, "wb") as writeFile:
        writeFile.write(resp.content)


def save_meta(group_name, name, metadata):
    with open(os.path.join(os.curdir, group_name, f'{name}.json'), 'w', encoding='utf-8') as writeFile:
        json.dump(metadata, writeFile, indent=2)


def load_meta(group_name, name):
    meta_path = os.path.join(os.curdir, group_name, f'{name}.json')
    metadata = None

    if os.path.isfile(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as readFile:
            metadata = json.load(readFile)

    return metadata


def retrieve_url(s, url, group_name, params=None):
    failed = False
    resp = s.get(url, params=params)
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


def retrieve_json(s, url, group_name, params=None):
    resp, failure = retrieve_url(s, url, group_name, params=params)

    if failure:
        return None

    try:
        data_json = json.loads(resp.text)['ygData']
    except ValueError as valueError:
        if 'mbr-login-greeting' in resp.text:
            # the user needs to be signed in to Yahoo
            print("Error. Yahoo login is not working")
            sys.exit()
        else:
            raise valueError

    return data_json


def photo_info_url(photo_info):
    quality_rank = {'tn': 1, 'sn': 2, 'hr': 3, 'or': 4}
    best_rank = 0
    best_url = ""
    for info in photo_info:
        rank = quality_rank[info['photoType']]
        if rank > best_rank:
            best_rank = rank
            best_url = info['displayURL']
    return best_url


writeLogFile = True


def set_no_logging():
    global writeLogFile
    writeLogFile = False


def log(msg, group_name):
    print(msg)
    if writeLogFile:
        log_f = open(group_name + ".txt", "a")
        log_f.write("\n" + msg)
        log_f.close()
