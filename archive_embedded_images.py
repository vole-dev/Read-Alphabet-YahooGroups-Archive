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
import urllib
import uuid

from bs4 import BeautifulSoup

from arc_utilities import retrieve_url, log, load_meta, save_meta, save_file


def archive_embedded_images(s, group_name):
    meta = load_meta(group_name, 'embedded_images') or {'parsed_messages': {}, 'imgs': {}}
    imgs = set()

    message_dir = os.path.join(os.curdir, group_name, 'messages')
    parsed_messages = set(meta['parsed_messages'])
    for filename in os.listdir(message_dir):
        if filename in parsed_messages:
            continue
        with open(os.path.join(message_dir, filename), 'r', encoding='utf-8') as readFile:
            log(f'Parsing message in {filename} for embedded images', group_name)
            message_json = json.load(readFile)
            imgs.update(parse_message_embedded_imgs(message_json['messageBody']))

            parsed_messages.add(filename)
    meta['parsed_messages'] = list(parsed_messages)

    for img in imgs:
        if img not in meta['imgs']:
            img_extension = img.split('?')[0].split('.')[-1]
            meta['imgs'][img] = str(uuid.uuid4()) + f'.{img_extension}'

    save_meta(group_name, 'embedded_images', meta)

    embedded_img_dir = os.path.join(os.curdir, group_name, 'embedded_img')
    if not os.path.exists(embedded_img_dir):
        os.makedirs(embedded_img_dir)

    for img in meta['imgs']:
        img_file = meta['imgs'][img]
        if os.path.isfile(os.path.join(embedded_img_dir, img_file)):
            continue

        log(f'Archiving embedded image {img} to file {img_file}', group_name)
        if not save_file(s, os.path.join(embedded_img_dir, img_file), img):
            log(f'ERROR: Unable to save file', group_name)


def parse_message_embedded_imgs(msg):
    soup = BeautifulSoup(msg, 'html5lib')
    img_srcs = map(lambda x: x.attrs.get('src', None), soup.findAll('img'))
    img_srcs_non_none = filter(None, img_srcs)

    banned_substrings = ['data:', 'cid:', 'adserver.yahoo.com', 'yimg.com%2Fa%2F', 'ads.x10.com', 'geo.yahoo.com']
    imgs = filter(lambda x: not any(ban_str in x for ban_str in banned_substrings), img_srcs_non_none)

    # deal with ec.yimg.com redirection
    redir_imgs = map(lambda img: redirect_ecyimg(img), imgs)

    return redir_imgs


def redirect_ecyimg(url):
    if not url.startswith('https://ec.yimg.com/ec?'):
        return url
    redirected_url = urllib.parse.parse_qs(url.split('?')[1])['url'][0]
    print(f'redir: {redirected_url}')
    return redirected_url
