# YahooGroups-Archiver

#### A simple python script that archives all messages from a public Yahoo Group

YahooGroups-Archiver allows you to make a backup copy of all the messages in a private group.

Messages are downloaded in a JSON format, with one .json file per message.

Works with Python 3.

## Usage
**`python archive_group.py <groupName> <action> <username> <password> [nologs]`**
where *`<groupName>`* is the name of the group you wish to archive (e.g: hypercard),
*`<username>`* and *`<password>`* match an account that can access the group's content

**Action**
* *`update`* - the default., Archive all new messages since the last time the script was run
* *`files`* - Download all files from the group, any previously downloaded file will not be downloaded again
* *`attachments`* - Download all attachments, any previously downloaded attachments will not be downloaded again
* *`photos`* - Download all photos, will not download photos that are from attachments
* *`info`* - Downloads general info about the group, like the description and cover photo

By default a log file called <groupname>.txt is created and stores information such as what messages could not be received. This is entirely for the benefit of the user: it's not needed at all by the script during any re-runs (although re-runs will append new information to the log file). If you don't want a log file to be created or added to, add the `nologs` keyword when you call the script.

## Note
Yahoo attempts to block connections that it deems to be "spamming", and so after around 15,000 messages have been downloaded it is highly likely that Yahoo will block you. This is OK, the script will automatically stop, and Yahoo should unblock you after around two hours. Running the script again once you have been unblocked will just continue where it left off. (Unless you run with the *`restart`* *[option]*, of course!

## Credits
Thanks to the [Archive Team](http://archiveteam.org/) for making [information about the Yahoo Groups API](http://www.archiveteam.org/index.php?title=Yahoo!_Groups) available.
