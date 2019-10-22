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

import mechanize
import requests


def login_session(username, password, save_and_load_cookies=True):
    s = requests.Session()
    user_agent = 'Mozilla/4.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0'
    s.headers['User-Agent'] = user_agent

    # load cookies from file if we can
    cookie_file = 'PRIVATE_DATA_DO_NOT_SHARE.cookies'
    if save_and_load_cookies:
        if os.path.isfile(cookie_file):
            s.cookies = mechanize.MozillaCookieJar()
            s.cookies.load(cookie_file)
            return s

    # if not loading cookies from file, get them by logging in
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', user_agent)]
    br.set_cookiejar(mechanize.MozillaCookieJar())

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

    # Give sign in cookies to the session
    s.cookies = br.cookiejar

    if save_and_load_cookies:
        br.cookiejar.save(cookie_file)

    br.close()
    return s


def save_file(s, file_path, url, referer=''):
    resp = s.get(url, headers={'referer': referer})

    with open(file_path, "wb") as writeFile:
        writeFile.write(resp.content)


def save_meta(group_name, name, metadata):
    with open(os.path.join(os.curdir, group_name, f'{name}.json'), 'w') as writeFile:
        json.dump(metadata, writeFile, indent=2)


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
