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
import subprocess
from pathlib import Path

import requests
from requests.auth import HTTPDigestAuth

top_directory = Path('/v')
api_url = "http://localhost:9981/api/dvr/entry/create"
user = 'user'
password = 'password'


class UnicodeEscapeHeuristic:
    """
    Decode a string based on the following algorithm:
    1. If string contains only 7-bit ASCII characters, decode as unicode-escape
    2. Otherwise, assume it is already UTF-8 encoded
    """
    @staticmethod
    def decode(text):
        if UnicodeEscapeHeuristic._is_ascii(text):
            return bytes(text, 'ascii').decode("unicode-escape")
        else:
            return text

    @staticmethod
    def _is_ascii(text):
        return all(ord(c) < 128 for c in text)


class InfoError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Info:
    """
    Read each VDR info line into a dict with the first character as the key. Since we are not interested in key X that
    may occur multiple times, we store only one of the X lines.
    """
    def __init__(self, directory):
        self.filepath = directory / 'info'
        self.info = {}

    def get_channel_name(self):
        """
        Return the channel name with the channel ID removed
        """
        channel = self._get('C')
        if channel is None:
            raise InfoError('no channel in info file ' + str(self.filepath))
        return channel[channel.index(' ') + 1:]

    def get_description(self):
        """
        Return the description of the show
        """
        description = self._get('D')
        if description is None:
            raise InfoError('no description in info file ' + str(self.filepath))
        return description

    def get_duration(self):
        """
        Return the EPG duration
        """
        event = self._get('E')
        if event is None:
            raise InfoError('no EPG event in info file ' + str(self.filepath))

        event_items = event.split()
        if len(event_items) < 4:
            raise InfoError('expected at least 4 EPG event items but got %i in info file %s' %
                            (len(event_items), self.filepath))

        try:
            duration = int(event_items[2])
        except ValueError:
            raise InfoError('EPG duration is wrong format in info file ' + str(self.filepath))

        return duration

    def get_subtitle(self):
        """
        Return the subtitle of the show
        """
        return self._get('S')

    def get_start_date_time(self):
        """
        Return the EPG start date and time
        """
        event = self._get('E')
        if event is None:
            raise InfoError('no EPG event in info file ' + str(self.filepath))

        event_items = event.split()
        if len(event_items) < 4:
            raise InfoError('expected at least 4 EPG event items but got %i in info file %s' %
                            (len(event_items), self.filepath))

        try:
            start_date_time = int(event_items[1])
        except ValueError:
            raise InfoError('EPG start date time is wrong format in info file ' + str(self.filepath))

        return start_date_time

    def get_title(self):
        """
        Return the title of the show
        """
        title = self._get('T')
        if title is None:
            raise InfoError('no title in info file ' + str(self.filepath))
        return title

    def _get(self, key):
        if not self.info:
            self._load_info()
        return self.info.get(key)

    def _load_info(self):
        try:
            with open(self.filepath) as file:
                for line in file:
                    key = line[0]
                    value = line[2:]
                    if value:
                        value = UnicodeEscapeHeuristic.decode(value)
                    self.info[key] = value.rstrip()
        except Exception as exc:
            logging.error('Failed to process file ' + str(self.filepath), exc_info=exc)
            raise


class Config:
    """
    Create a config dict that can be imported into Tvheadend
    """
    def __init__(self, directory, files):
        self.directory = directory
        self.files = files

    def create_from_info(self):
        config = {
            "enabled": True,
            "title": {},
            "comment": "added by vdr_to_hts_import.py",
            "files": []
        }
        info = Info(self.directory)

        start_date_time = info.get_start_date_time()
        config['start'] = start_date_time

        config['stop'] = start_date_time + info.get_duration()

        self._add_file(config)

        config['channelname'] = info.get_channel_name()

        config['title']['fin'] = info.get_title()

        subtitle = info.get_subtitle()
        if subtitle:
            config['subtitle'] = {"fin": subtitle}

        description = info.get_description()
        if description:
            config['description'] = {"fin": description}

        return config

    def _add_file(self, config):
        """
        Tvheadend allows only one file to be imported. (If you try to import multiple files, it will pick the last file
        in the list.) Concatenate all files into one and import the concatenated file.
        """
        ts_files = []
        for file in self.files:
            if '.ts' == file[-3:]:
                ts_files.append(file)

        number_of_ts_files = len(ts_files)
        if number_of_ts_files < 1:
            raise InfoError('found info file but no .ts files in directory ' + str(self.directory))
        elif number_of_ts_files == 1:
            filename = self.directory / ts_files[0]
        else:
            filename = self._concat_ts_files(ts_files)

        config['files'].append({
            'filename': str(filename)
        })

    def _concat_ts_files(self, files):
        """
        Use ffmpeg to concatenate all .ts files
        """
        filelist_path = Path(self.directory, 'filelist.txt')
        with open(str(filelist_path), 'x') as concat_files:
            for file in files:
                concat_files.write("file '" + str(self.directory / file) + "'\n")
        filename = self.directory / 'concat.ts'
        subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', str(filelist_path), '-c', 'copy', str(filename)],
                       check=True, text=True)
        return filename


class Importer:
    """
    Read a VDR directory and import the files into Tvheadend
    """
    @staticmethod
    def import_record(directory, files):
        config = Config(directory, files)
        config_dict = config.create_from_info()
        logging.info("import config:\n{}".format(json.dumps(config_dict, sort_keys=True, indent=4)))

        # Tvheadend will reject POST requests with any other content type than this:
        # (Took some reading of the source code to find that)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        # Usually you would use `json=` to pass the config data into the POST body but /api/dvr/entry/create expects
        # that the body starts with the string "conf=". Therefore we need to use json.dumps and because requests sets
        # the content type only to a form when you pass a dict into `data=`, we need to explicitly set the content type
        # to a form.
        response = requests.post(api_url,
                                 auth=HTTPDigestAuth(user, password),
                                 headers=headers,
                                 data="conf={}".format(json.dumps(config_dict)))
        logging.info("server response:\n{}".format(response.text))


class DirWalker:
    @staticmethod
    def walk():
        """
        Walk through a directory tree with this structure:
        / top directory / recording title / recording date / recording files
        """
        for recording_dir in top_directory.iterdir():
            if recording_dir.is_dir():
                for root, _, files in os.walk(recording_dir):
                    if 'info' in files:
                        Importer.import_record(Path(root), files)


def main():
    logging.basicConfig(filename='vdr_to_hts_import.log', level=logging.INFO, format='%(asctime)s %(message)s')

    DirWalker.walk()


if __name__ == "__main__":
    main()
