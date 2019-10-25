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

import os  # required for checking if a file exists locally
import sys  # required to cancel script if blocked by Yahoo
import time  # required to log the date and time of run
import traceback

from arc_utilities import login_session, log, set_no_logging
from archive_attachments import archive_group_attachments
from archive_files import archive_group_files
from archive_info import archive_group_info
from archive_messages import archive_group_messages
from archive_photos import archive_group_photos
from archive_polls import archive_group_polls
from archive_topics import archive_group_topics


def login_and_archive(group_name, action, username, password):
    s = login_session(username, password)
    if not s:
        return
    archive_group(s, group_name, action)


def archive_group(s, group_name, mode):
    log("\nArchiving group '" + group_name + "', mode: " + mode + " , on " + time.strftime("%c"), group_name)
    start_time = time.time()
    do_all = mode == "all"

    valid_mode = False

    if mode == "messages" or do_all:
        valid_mode = True
        try_archive(s, group_name, archive_group_messages, 'message')
        try_archive(s, group_name, archive_group_topics, 'topic')
    if mode == "files" or do_all:
        valid_mode = True
        try_archive(s, group_name, archive_group_files, 'file')
    if mode == "attachments" or do_all:
        valid_mode = True
        try_archive(s, group_name, archive_group_attachments, 'attachment')
    if mode == "photos" or do_all:
        valid_mode = True
        try_archive(s, group_name, archive_group_photos, 'photo')
    if mode == "info" or do_all:
        valid_mode = True
        try_archive(s, group_name, archive_group_info, 'info')
    if mode == "polls" or do_all:
        valid_mode = True
        try_archive(s, group_name, archive_group_polls, 'poll')

    if not valid_mode:
        print(f'You have specified an invalid mode ({mode}).')
        sys.exit()

    log("Time taken is " + str(time.time() - start_time) + " seconds", group_name)
    return


def try_archive(s, group_name, archiving_fun, archive_type):
    try:
        archiving_fun(s, group_name)
    except:
        e = traceback.format_exc()
        log(f'Failure. {archive_type} archive exception: {e}', group_name)
    else:
        log(f'Success. {archive_type} archive finished', group_name)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if "nologs" in sys.argv:
        print("Logging mode OFF")
        set_no_logging()
        sys.argv.remove("nologs")
    if len(sys.argv) >= 5:
        login_and_archive(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print('This script requires parameters to run:')
        print('python archive_group.py <groupName> <action> <username> <password> [nologs]')
        print('Available actions are: all, messages, files, attachments, photos, info')
