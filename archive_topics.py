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

from arc_utilities import log, save_meta, load_meta, retrieve_json


def archive_group_topics(s, group_name):
    topic_data = load_meta(group_name, 'topics-meta') or {}

    num_archived = 0
    for topic in yield_walk_topics(s, group_name):
        record_id = topic['recordId']
        saved_topic = topic_data.get(str(record_id), None)
        if not saved_topic or topic['lastPosted'] != saved_topic['lastPosted']:
            print(f'Archiving topic {record_id}')
            num_archived += 1
            topic['message_ids'] = get_topic_message_ids(s, group_name, record_id)
        else:
            topic['message_ids'] = saved_topic['message_ids']
            if topic != saved_topic:
                print(f'Archiving topic {record_id}')
                num_archived += 1

        topic_data[record_id] = topic

        if num_archived == 100:
            num_archived = 0
            print("Saving partial topics archive to disk")
            save_meta(group_name, 'topics-meta', topic_data)

    save_meta(group_name, 'topics-meta', topic_data)
    return


def yield_walk_topics(s, group_name):
    url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/topics'
    params = {
        'count': 100,
        'sortOrder': 'asc',
        'direction': 1,
    }

    first_topic = 1
    while first_topic != 0:
        params['startTopicId'] = first_topic
        topics_json = retrieve_json(s, url, group_name, params=params)

        if not topics_json:
            log(f'FAILURE. Unable to obtain topic list from {url} with {params=}', group_name)
            return

        topic_list = topics_json['topicRecords']

        for topic in topic_list:
            yield topic

        first_topic = topic_list[-1]['nextTopic']

    return


def get_topic_message_ids(s, group_name, topic_record_id):
    topic_url = f'https://groups.yahoo.com/api/v1/groups/{group_name}/topics/{topic_record_id}'
    topic_json = retrieve_json(s, topic_url, group_name)

    if not topic_json:
        log(f'FAILURE. Unable to obtain topic from {topic_url}', group_name)
        return None

    messages = topic_json['messages']
    message_ids = map(lambda msg: msg['msgId'], messages)
    return list(message_ids)
