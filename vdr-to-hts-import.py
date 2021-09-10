#!/usr/bin/python3
# -*- coding: UTF-8 -*-

# This script has the purpose to import old TVHeadend recordings in a new TVHeadend installation. It scans a folder
# with TVHeadend recordings and sets for each file a recording timer in TVHeadend. This is adapted from the following
# script:
# https://tvheadend.org/boards/5/topics/28252?r=29113#message-29113 by user ullix tv.
# The folder is expected to be in untouched format. My recordings have a filenamescheme of "name-YYYY-MM-DDHH-MM.ts"
# because I had %F%R in the recording String. Looks ugly but helps now. Getting the time string with filedate2num has
# to be adapted. Variables have to be adapted to personal situation.
import datetime
import json
import os
import requests
import subprocess
import time

# Input variables
recdir = "/v"
api_url = "http://star.ritzmann.online:9981/api/dvr/entry/create"
user = 'user'
password = 'password'
mask = {
    "enabled": True,
    "start": 1000,
    "stop":  2000,
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


# Functions
def filedate2num(filepath):
    """Convert filename that ends with 'YYYY-MM-DDHH-MM.ts' to Unix timestamp; use cdate, i.e. last inode change time
    not creation, on error"""

    try:
        dt = int(time.mktime(datetime.datetime.strptime(filepath[-18:-3], "%Y-%m-%d%H-%M").timetuple()))
    except IOError:
        print("ERROR in filestr2num: file name '%s' doesn't end with 'YYYY-MM-DDHH-MM.ts'. "
              "Use Inode Change Time instead." % filepath)
        dt = int(os.stat(filepath).st_ctime)
    return dt


def video_duration(video_file_path):
    """Get video duration in sec from a ffprobe call, using json output"""

    # command is:  ffprobe -loglevel quiet -print_format json -show_format /full/path/to/videofile
    command = ["ffprobe", "-loglevel", "quiet", "-print_format", "json", "-show_format",  video_file_path]
    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = pipe.communicate()
    js = json.loads(out)
    return int(float(js['format']['duration']) + 1.)


def import_record(filepath, new_mask, url):
    """Creates a json file with the information from video file and sends a recording timer to the server."""
    video_start = filedate2num(filepath)
    new_mask['files'][0]['filename'] = filepath[8:]
    new_mask['title']['ger'] = filepath.split("/")[-1][:-3]
    new_mask['start'] = video_start
    new_mask['stop'] = video_start + video_duration(filepath)
    print("New File Info: \n", json.dumps(new_mask, sort_keys=True, indent=4))
    response = requests.post(url, auth=(user, password), json=new_mask)
    print("Server Answer:", response.text)


def main():
    """Iterating through recordings folder"""
    directories = os.listdir(recdir)
    for folder in directories:
        for root, dirs, files in os.walk(os.path.join(recdir, folder)):
            for filename in files:
                if filename[-3:] == '.ts':
                    import_record(os.path.join(root, filename), mask, api_url)


if __name__ == "__main__":
    main()
