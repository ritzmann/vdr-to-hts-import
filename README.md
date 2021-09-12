Import VDR recordings to HTS Tvheadend
======================================

Iterate through a directory hierarchy and identify all  directories that contain a `info` file in VDR format.

Search each directory that contains a `info` file for `.ts` files and import them into HTS Tvheadend.
The information contained in `info` is used for the import.

VDR info file format
----------------

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

Tvheadend config format
-----------------------

A comprehensive example of a Tvheadend entry for import:

    {
        "enabled": true,
        "start": 1510693200,
        "start_extra": 0,
        "stop": 1510696800,
        "stop_extra": 0,
        "channel": "c21ce739589fe95431a87819c5551dec",
        "channelname": "4Music",
        "title": {
            "eng": "8 Out of 10 Cats Best Bits" 
        },
        "subtitle": {
            "eng": "S17, E11. Compilation edition with Jimmy Carr, team captains Sean Lock and Jon Richardson, and guests including Jo Brand, David O'Doherty, Katherine Ryan, Jerry Springer, and Roisin Conaty." 
        },
        "description": {
            "eng": "S17, E11. Compilation edition with Jimmy Carr, team captains Sean Lock and Jon Richardson, and guests including Jo Brand, David O'Doherty, Katherine Ryan, Jerry Springer, and Roisin Conaty." 
        },
        "pri": 2,
        "retention": 0,
        "removal": 0,
        "playposition": 0,
        "playcount": 0,
        "config_name": "9fd12d0886d1e62684a33493c13c2cab",
        "creator": "192.168.0.128",
        "errorcode": 0,
        "errors": 1,
        "data_errors": 0,
        "dvb_eid": 0,
        "noresched": true,
        "norerecord": false,
        "fileremoved": 0,
        "autorec": "bac31816545721d1f9d43651b49979ea",
        "timerec": "",
        "parent": "",
        "child": "",
        "content_type": 3,
        "broadcast": 0,
        "comment": "Auto recording: Created from EPG query",
        "files": [
            {
                "filename": "/mnt/3tb/video-files/8 Out of 10 Cats Best Bits/8 Out of 10 Cats Best Bits.mkv",
                "info": [
                    {
                        "type": "MPEG2VIDEO",
                        "width": 704,
                        "height": 576,
                        "duration": 3600,
                        "aspect_num": 16,
                        "aspect_den": 9
                    },
                    {
                        "type": "MPEG2AUDIO",
                        "language": "nar",
                        "audio_type": 0,
                        "audio_version": 2
                    },
                    {
                        "type": "MPEG2AUDIO",
                        "language": "eng",
                        "audio_type": 0,
                        "audio_version": 2
                    },
                    {
                        "type": "DVBSUB",
                        "language": "eng",
                        "composition_id": 2,
                        "ancillary_id": 2
                    },
                    {
                        "type": "TEXTSUB",
                        "language": "eng",
                        "composition_id": 0,
                        "ancillary_id": 0
                    }
                ],
                "start": 1510693080,
                "stop": 1510695949
            },
            {
                "filename": "/mnt/3tb/video-files/8 Out of 10 Cats Best Bits/8 Out of 10 Cats Best Bits-2.mkv",
                "info": [
                    {
                        "type": "MPEG2VIDEO",
                        "width": 704,
                        "height": 576,
                        "duration": 3600,
                        "aspect_num": 16,
                        "aspect_den": 9
                    },
                    {
                        "type": "MPEG2AUDIO",
                        "language": "nar",
                        "audio_type": 0,
                        "audio_version": 2
                    },
                    {
                        "type": "MPEG2AUDIO",
                        "language": "eng",
                        "audio_type": 0,
                        "audio_version": 2
                    },
                    {
                        "type": "DVBSUB",
                        "language": "eng",
                        "composition_id": 2,
                        "ancillary_id": 2
                    },
                    {
                        "type": "TEXTSUB",
                        "language": "eng",
                        "composition_id": 0,
                        "ancillary_id": 0
                    }
                ],
                "start": 1510696049,
                "stop": 1510697100
            }
        ]
    }