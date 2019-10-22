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

from arc_utilities import login_session, log, set_no_logging
from archive_attachments import archive_group_attachments
from archive_files import archive_group_files
from archive_info import archive_group_info
from archive_messages import archive_group_messages
from archive_photos import archive_group_photos
from archive_polls import archive_group_polls


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
        archive_group_messages(s, group_name)
        log("message archive finished", group_name)
    if mode == "files" or do_all:
        valid_mode = True
        archive_group_files(s, group_name)
        log("files archive finished", group_name)
    if mode == "attachments" or do_all:
        valid_mode = True
        archive_group_attachments(s, group_name)
        log("attachment archive finished", group_name)
    if mode == "photos" or do_all:
        valid_mode = True
        archive_group_photos(s, group_name)
        log("photo archive finished", group_name)
    if mode == "info" or do_all:
        valid_mode = True
        archive_group_info(s, group_name)
        log("info archive finished", group_name)
    if mode == "polls" or do_all:
        valid_mode = True
        archive_group_polls(s, group_name)
        log("poll archive finished", group_name)

    if not valid_mode:
        print("You have specified an invalid mode (" + mode + ").")
        sys.exit()

    log("Time taken is " + str(time.time() - start_time) + " seconds", group_name)
    return


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
