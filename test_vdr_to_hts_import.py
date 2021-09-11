# This file is part of vdr_to_hts_import,
# Copyright (C) 2021-present Fabian Ritzmann
#
# vdr_to_hts_import is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# vdr_to_hts_import is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vdr_to_hts_import.  If not, see <https://www.gnu.org/licenses/>.

from unittest.mock import Mock

import pytest

import vdr_to_hts_import
from vdr_to_hts_import import DirWalker, Importer, Info, InfoError


def test_dir_walker_walk(mocker):
    mocker.patch('os.listdir', return_value=['dir1', 'dir2', 'dir3'])
    file_list = ['file1', 'file2.ts', 'info']
    mocker.patch('os.walk', return_value=[['root1', [], file_list]])
    importer_mock = mocker.patch('vdr_to_hts_import.Importer')
    dir_walker = DirWalker()

    dir_walker.walk()

    importer_mock.assert_has_calls([
        mocker.call('root1'),
        mocker.call().import_record(file_list),
        mocker.call('root1'),
        mocker.call().import_record(file_list),
        mocker.call('root1'),
        mocker.call().import_record(file_list)
    ])


def test_importer_import_record(mocker):
    mocker.patch.multiple('vdr_to_hts_import.Info',
                          get_channel_name=Mock(return_value='channel1'),
                          get_title=Mock(return_value='title1'),
                          get_start_date_time=Mock(return_value=1231),
                          get_duration=Mock(return_value=765))
    response_mock = mocker.patch('requests.post', return_value=Mock())
    response_mock.text = 'response1'
    importer = Importer('root')

    importer.import_record(['file1', 'file1.ts', 'info', 'file2.ts'])

    config = {
        "enabled": True,
        "title": {
            "fin": "title1"
        },
        "comment": "added by vdr_to_hts_import.py",
        "files": [
            {"filename": "root/file1.ts"},
            {"filename": "root/file2.ts"}
        ],
        "channelname": "channel1",
        "start": 1231,
        "stop": 1231 + 765,
    }
    response_mock.assert_called_once_with(vdr_to_hts_import.api_url,
                                          auth=(vdr_to_hts_import.user, vdr_to_hts_import.password),
                                          json=config)


def test_importer_import_record_no_ts_files(mocker):
    mocker.patch.multiple('vdr_to_hts_import.Info',
                          get_channel_name=Mock(return_value='channel1'),
                          get_title=Mock(return_value='title1'),
                          get_start_date_time=Mock(return_value=1231),
                          get_duration=Mock(return_value=765))
    importer = Importer('root')

    with pytest.raises(InfoError) as exc_info:
        importer.import_record(['file1', 'info'])
    assert 'found info file but no .ts files in directory root' == str(exc_info.value)


def test_info_get_channel_name():
    info = Info('test')
    info.info['C'] = 'some-id channel1'

    assert 'channel1' == info.get_channel_name()


def test_info_get_channel_name_with_multiple_spaces():
    info = Info('test')
    info.info['C'] = 'some-id name of channel 1'

    assert 'name of channel 1' == info.get_channel_name()


def test_info_get_channel_name_no_id():
    info = Info('test')
    info.info['C'] = 'channel1'

    with pytest.raises(ValueError) as exc_info:
        info.get_channel_name()
    assert 'substring not found' == str(exc_info.value)


def test_info_get_channel_name_no_channel():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_channel_name()
    assert 'no channel in info file' == str(exc_info.value)


def test_info_get_description():
    info = Info('test')
    info.info['D'] = 'description1'

    assert 'description1' == info.get_description()


def test_info_get_description_with_multiple_spaces():
    info = Info('test')
    info.info['D'] = 'description with spaces'

    assert 'description with spaces' == info.get_description()


def test_info_get_description_no_description():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_description()
    assert 'no description in info file' == str(exc_info.value)


def test_info_get_duration():
    info = Info('test')
    info.info['E'] = 'eventid 12312 234 tableid'

    assert 234 == info.get_duration()


def test_info_get_duration_wrong_number_event_items():
    info = Info('test')
    info.info['E'] = 'eventid 12312 tableid'

    with pytest.raises(InfoError) as exc_info:
        info.get_duration()
    assert 'expected 4 EPG event items but got 3' == str(exc_info.value)


def test_info_get_duration_invalid_format():
    info = Info('test')
    info.info['E'] = 'eventid 12312 23a4i tableid'

    with pytest.raises(InfoError) as exc_info:
        info.get_duration()
    assert 'EPG duration is wrong format' == str(exc_info.value)


def test_info_get_duration_no_duration():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_duration()
    assert 'no EPG event in info file' == str(exc_info.value)


def test_info_get_short_description():
    info = Info('test')
    info.info['S'] = 'shortdescription1'

    assert 'shortdescription1' == info.get_short_description()


def test_info_get_short_description_with_multiple_spaces():
    info = Info('test')
    info.info['S'] = 'short description with spaces'

    assert 'short description with spaces' == info.get_short_description()


def test_info_get_short_description_no_short_description():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_short_description()
    assert 'no short description in info file' == str(exc_info.value)


def test_info_get_start_date_time():
    info = Info('test')
    info.info['E'] = 'eventid 12312 234 tableid'

    assert 12312 == info.get_start_date_time()


def test_info_get_start_date_time_wrong_number_event_items():
    info = Info('test')
    info.info['E'] = 'eventid 12312 tableid'

    with pytest.raises(InfoError) as exc_info:
        info.get_start_date_time()
    assert 'expected 4 EPG event items but got 3' == str(exc_info.value)


def test_info_get_start_date_time_invalid_format():
    info = Info('test')
    info.info['E'] = 'eventid 12a312c 234 tableid'

    with pytest.raises(InfoError) as exc_info:
        info.get_start_date_time()
    assert 'EPG start date time is wrong format' == str(exc_info.value)


def test_info_get_start_date_time_no_start_date_time():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_start_date_time()
    assert 'no EPG event in info file' == str(exc_info.value)


def test_info_get_title():
    info = Info('test')
    info.info['T'] = 'title1'

    assert 'title1' == info.get_title()


def test_info_get_title_with_multiple_spaces():
    info = Info('test')
    info.info['T'] = 'title with spaces'

    assert 'title with spaces' == info.get_title()


def test_info_get_title_no_title():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_title()
    assert 'no title in info file' == str(exc_info.value)
