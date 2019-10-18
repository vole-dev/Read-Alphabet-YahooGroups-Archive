#!/usr/local/bin/python
'''
Yahoo-Groups-Archiver, HTML Archive Script Copyright 2019 Robert Lancaster and others

YahooGroups-Archiver, a simple python script that allows for all
messages in a public Yahoo Group to be archived.

The HTML Archive Script allows you to take the downloaded json documents
and turn them into html-based yearly archives of emails.
Note that the archive-group.py script must be run first.

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
'''
import email
from email import policy
import html.parser
import json
import os
import sys
from datetime import datetime
from natsort import natsorted, ns
import cgi


def archiveYahooMessage(file, archiveFile, messageYear, format):
    with open(archiveFile, 'a', encoding='utf-8') as f:
        if f.tell() == 0:
            f.write("<style>pre {white-space: pre-wrap;}</style>\n");
        tmessage = loadYahooMessage(file, format)
        f.write(tmessage)
    print('Yahoo Message: ' + file + ' archived to: archive-' + str(messageYear) + '.html')

def loadYahooMessage(file, format):
    f1 = open(file, 'r', encoding='utf-8')
    fileContents=f1.read()
    f1.close()
    jsonDoc = json.loads(fileContents)
    emailMessageID = jsonDoc['ygData']['msgId']
    emailMessageSender = html.unescape(jsonDoc['ygData']['from'])
    emailMessageTimeStamp = jsonDoc['ygData']['postDate']
    emailMessageDateTime = datetime.fromtimestamp(float(emailMessageTimeStamp)).strftime('%Y-%m-%d %H:%M:%S')
    emailMessageSubject = html.unescape(jsonDoc['ygData'].get('subject', ''))
    emailMessageString = html.unescape(jsonDoc['ygData']['rawEmail'])
    message = email.message_from_string(emailMessageString, policy=policy.default)
    messageBody = getEmailBody(message)
    
    messageText = '-----------------------------------------------------------------------------------<br>' + "\n"
    messageText += 'Post ID:' + str(emailMessageID) + '<br>' + "\n"
    messageText += 'Sender:' + cgi.escape(emailMessageSender) + '<br>' + "\n"
    messageText += 'Post Date/Time:' + cgi.escape(emailMessageDateTime) + '<br>' + "\n"
    messageText += 'Subject:' + cgi.escape(emailMessageSubject) + '<br>' + "\n"
    messageText += 'Message:' + '<br><br>' + "\n"
    messageText += messageBody
    messageText += '<br><br><br><br><br>' + "\n"
    return messageText
    
def getYahooMessageYear(file):
    f1 = open(file, 'r', encoding='utf-8')
    fileContents=f1.read()
    f1.close()
    jsonDoc = json.loads(fileContents)
    emailMessageTimeStamp = jsonDoc['ygData']['postDate']
    return datetime.fromtimestamp(float(emailMessageTimeStamp)).year

# Thank you to the help in this forum for the bulk of this function
# https://stackoverflow.com/questions/17874360/python-how-to-parse-the-body-from-a-raw-email-given-that-raw-email-does-not
def getEmailBody(message):
    body = ''
    if message.is_multipart():
        for part in message.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))

            # skip any text/plain (txt) attachments
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body += '<pre>'
                body += cgi.escape(part.get_content())
                body += '</pre>'
                break
    # not multipart - i.e. plain text, no attachments, keeping fingers crossed
    else:
        ctype = message.get_content_type()
        if ctype != 'text/html':
            body += '<pre>'
            body += cgi.escape(message.get_content())
             body += '</pre>'
        else:
             body += message.get_content()
    return body

## This is where the script starts

if len(sys.argv) < 2:
     sys.exit('You need to specify your group name')

groupName = sys.argv[1]
oldDir = os.getcwd()
if os.path.exists(groupName):
    archiveDir = os.path.abspath(groupName + '-archive')
    if not os.path.exists(archiveDir):
         os.makedirs(archiveDir)
    os.chdir(groupName)
    for file in natsorted(os.listdir(os.getcwd())):
         messageYear = getYahooMessageYear(file)
         archiveFile = archiveDir + '/archive-' + str(messageYear) + '.html'
         archiveYahooMessage(file, archiveFile, messageYear, 'utf-8')
else:
     sys.exit('Please run archive-group.py first')

os.chdir(oldDir)
print('Complete')


