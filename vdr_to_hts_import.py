#!/usr/bin/python3

# This script has the purpose to import old TVHeadend recordings in a new TVHeadend installation. It scans a folder
# with TVHeadend recordings and sets for each file a recording timer in TVHeadend. This is adapted from the following
# script:
# https://tvheadend.org/boards/5/topics/28252?r=29113#message-29113 by user ullix tv.
# The folder is expected to be in untouched format. My recordings have a filenamescheme of "name-YYYY-MM-DDHH-MM.ts"
# because I had %F%R in the recording String. Looks ugly but helps now. Getting the time string with filedate2num has
# to be adapted. Variables have to be adapted to personal situation.
import datetime
import json
import logging
import os
import subprocess
import time

import requests

# Input variables
recdir = "/v"
api_url = "http://localhost:9981/api/dvr/entry/create"
user = 'user'
password = 'password'
config_template = {
    "enabled": True,
    "start": 1000,
    "stop": 2000,
    "channelname": "Imported",
    "title": {
        "ger": "my title"
    },
    "comment": "added by tvh_rec_import.py",
    "files": [
        {
            "filename": "/full/path/to/videofile.ts"
        }
    ]
}


class InfoError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Info:
    """
    The format of an info file is described in http://www.vdr-wiki.de/wiki/index.php/Info like this:

    C = Kanal-ID, verweist im Format Quelle-NID-TID-SID auf die Einträge in der channels.conf
    E = EventID StartZeit Dauer TableID, wie in epg.data
    T = Titel
    S = Kurztext
    D = Beschreibung
    G = Genre
    R = Altersbeschränkung
    X = Technische Details
        Stream: 1 = MPEG2-Video, 2 = MPEG2 Audio, 3 = Untertitel, 4 = AC3-Audio, 5 = H.264-Video, 6 = HEAAC-Audio
        Typ:
            bei Video: 01 = 05 = 4:3, 02 = 03 = 06 = 07 = 16:9, 04 = 08 = >16:9, 09 = 0D = HD 4:3, 0A = 0B = 0E = 0F = HD 16:9, 0C = 10 = HD >16:9
            bei Audio: 01 = Mono?, 03 = Stereo, 05 = Dolby Digital
        Sprache
        Beschreibung
    V = VPS Zeit (time_t)
    F = Framerate
    L = Lebensdauer
    P = Priorität
    @ = (AUX) Zusätzliche Beschreibungsfeld, welches von der timers.conf übernommen wurde.

    Example:

    C S19.2E-1-1011-11100 Das Erste HD
    E 40747 1303617600 4500 4E 1C
    T Flutsch und weg
    S Spielfilm Großbritannien / USA 2006 (Flushed Away) - Kinderprogramm
    D Die Ratte Roddy lebt als verwöhntes Haustier bei einer wohlhabenden Londoner Familie. Als er in die Kanalisation gespült wird, kommt er einem Komplott des fiesen Kröterichs Toad auf die Spur und muss sich als Held und Lebensretter beweisen.
    X 5 0B deu HD-Video
    X 2 03 deu stereo
    X 4 44 deu Dolby Digital 5.1
    X 2 03 deu ohne Audiodeskription
    V 1303617600
    F 50
    P 50
    L 99
    @ <epgsearch><channel>1 - Das Erste HD</channel><update>0</update><eventid>40747</eventid><bstart>600</bstart><bstop>900</bstop></epgsearch>

    Read each line into a dict with the first character as the key. Since we are not interested in the key X that may
    occur multiple times, we store only one of the X lines.
    """
    def __init__(self, filename):
        self.filename = filename
        self.info = {}

    def get_channel_name(self):
        """
        Return the channel name with the channel ID removed
        """
        channel = self._get('C')
        if channel is None:
            raise InfoError('no channel in info file')
        return channel[channel.index(' ') + 1:]

    def get_description(self):
        """
        Return the description of the show
        """
        description = self._get('D')
        if description is None:
            raise InfoError('no description in info file')
        return description

    def get_short_description(self):
        """
        Return the short description of the show
        """
        short_description = self._get('S')
        if short_description is None:
            raise InfoError('no short description in info file')
        return short_description

    def get_start_date_time(self):
        """
        Return the EPG start date and time
        """
        event = self._get('E')
        if event is None:
            raise InfoError('no EPG event in info file')

        event_items = event.split()
        if len(event_items) != 4:
            raise InfoError('expected 4 EPG event items but got %i' % len(event_items))

        try:
            start_date_time = int(event_items[1])
        except ValueError:
            raise InfoError('EPG start date time is wrong format')

        return start_date_time

    def get_title(self):
        """
        Return the title of the show
        """
        title = self._get('T')
        if title is None:
            raise InfoError('no title in info file')
        return title

    def _get(self, key):
        if not self.info:
            self._load_info()
        return self.info.get(key)

    def _load_info(self):
        with open(self.filename) as file:
            for line in file:
                key = line[0]
                value = line[2:]
                self.info[key] = value


# Functions
def filedate2num(filepath):
    """Convert filename that ends with 'YYYY-MM-DDHH-MM.ts' to Unix timestamp; use cdate, i.e. last inode change time
    not creation, on error"""

    try:
        dt = int(time.mktime(datetime.datetime.strptime(filepath[-18:-3], "%Y-%m-%d%H-%M").timetuple()))
    except IOError:
        logging.info("ERROR in filestr2num: file name '%s' doesn't end with 'YYYY-MM-DDHH-MM.ts'. "
                     "Use Inode Change Time instead." % filepath)
        dt = int(os.stat(filepath).st_ctime)
    return dt


def video_duration(video_file_path):
    """Get video duration in sec from a ffprobe call, using json output"""

    # command is:  ffprobe -loglevel quiet -print_format json -show_format /full/path/to/videofile
    command = ["ffprobe", "-loglevel", "quiet", "-print_format", "json", "-show_format", video_file_path]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    js = json.loads(out)
    return int(float(js['format']['duration']) + 1.)


def import_record(filepath, config, url):
    """Creates a json file with the information from video file and sends a recording timer to the server."""
    video_start = filedate2num(filepath)
    config['files'][0]['filename'] = filepath[8:]
    config['title']['ger'] = filepath.split("/")[-1][:-3]
    config['start'] = video_start
    config['stop'] = video_start + video_duration(filepath)
    logging.info("New File Info: \n", json.dumps(config, sort_keys=True, indent=4))
    response = requests.post(url, auth=(user, password), json=config)
    logging.info("Server Answer:", response.text)


def main():
    """Iterating through recordings folder"""
    directories = os.listdir(recdir)
    for folder in directories:
        for root, dirs, files in os.walk(os.path.join(recdir, folder)):
            # change to:
            # if 'info' in files:
            #     import_record(...)
            #
            for filename in files:
                if filename[-3:] == '.ts':
                    import_record(os.path.join(root, filename), config_template, api_url)


if __name__ == "__main__":
    main()
