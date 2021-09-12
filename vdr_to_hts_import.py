#!/usr/bin/python3
#
# This file is part of vdr-to-hts-import,
# Copyright (C) 2021-present Fabian Ritzmann
#
# vdr-to-hts-import is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# vdr-to-hts-import is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vdr-to-hts-import.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
import os

import requests


top_directory = '/v'
api_url = "http://localhost:9981/api/dvr/entry/create"
user = 'user'
password = 'password'


class InfoError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Info:
    """
    Read each line into a dict with the first character as the key. Since we are not interested in the key X that may
    occur multiple times, we store only one of the X lines.
    """
    def __init__(self, directory):
        self.filepath = os.path.join(directory, 'info')
        self.info = {}

    def get_channel_name(self):
        """
        Return the channel name with the channel ID removed
        """
        channel = self._get('C')
        if channel is None:
            raise InfoError('no channel in info file ' + self.filepath)
        return channel[channel.index(' ') + 1:]

    def get_description(self):
        """
        Return the description of the show
        """
        description = self._get('D')
        if description is None:
            raise InfoError('no description in info file ' + self.filepath)
        return description

    def get_duration(self):
        """
        Return the EPG duration
        """
        event = self._get('E')
        if event is None:
            raise InfoError('no EPG event in info file ' + self.filepath)

        event_items = event.split()
        if len(event_items) < 4:
            raise InfoError('expected at least 4 EPG event items but got %i in info file %s' %
                            (len(event_items), self.filepath))

        try:
            duration = int(event_items[2])
        except ValueError:
            raise InfoError('EPG duration is wrong format in info file ' + self.filepath)

        return duration

    def get_short_description(self):
        """
        Return the short description of the show
        """
        short_description = self._get('S')
        if short_description is None:
            raise InfoError('no short description in info file ' + self.filepath)
        return short_description

    def get_start_date_time(self):
        """
        Return the EPG start date and time
        """
        event = self._get('E')
        if event is None:
            raise InfoError('no EPG event in info file ' + self.filepath)

        event_items = event.split()
        if len(event_items) < 4:
            raise InfoError('expected at least 4 EPG event items but got %i in info file %s' %
                            (len(event_items), self.filepath))

        try:
            start_date_time = int(event_items[1])
        except ValueError:
            raise InfoError('EPG start date time is wrong format in info file ' + self.filepath)

        return start_date_time

    def get_title(self):
        """
        Return the title of the show
        """
        title = self._get('T')
        if title is None:
            raise InfoError('no title in info file ' + self.filepath)
        return title

    def _get(self, key):
        if not self.info:
            self._load_info()
        return self.info.get(key)

    def _load_info(self):
        with open(self.filepath) as file:
            for line in file:
                key = line[0]
                value = line[2:]
                self.info[key] = value


class Importer:
    def __init__(self, directory):
        self.directory = directory
        self.config = {
            "enabled": True,
            "title": {},
            "comment": "added by vdr_to_hts_import.py",
            "files": []
        }

    def import_record(self, files):
        info = Info(self.directory)

        for file in files:
            if '.ts' == file[-3:]:
                self.config['files'].append({'filename': str(os.path.join(self.directory, file))})
        if len(self.config['files']) < 1:
            raise InfoError('found info file but no .ts files in directory ' + self.directory)

        self.config['channelname'] = info.get_channel_name()
        self.config['title']['fin'] = info.get_title()
        start_date_time = info.get_start_date_time()
        self.config['start'] = start_date_time
        self.config['stop'] = start_date_time + info.get_duration()

        logging.info("new file info:\n{}".format(json.dumps(self.config, sort_keys=True, indent=4)))

        response = requests.post(api_url, auth=(user, password), json=self.config)
        logging.info("server response:\n{}".format(response.text))


class DirWalker:
    @staticmethod
    def walk():
        directories = os.listdir(top_directory)
        for folder in directories:
            for root, _, files in os.walk(os.path.join(top_directory, folder)):
                if 'info' in files:
                    importer = Importer(root)
                    importer.import_record(files)


def main():
    logging.basicConfig(filename='vdr_to_hts_import.log', level=logging.INFO, format='%(asctime)s %(message)s')

    dir_walker = DirWalker()
    dir_walker.walk()


if __name__ == "__main__":
    main()
