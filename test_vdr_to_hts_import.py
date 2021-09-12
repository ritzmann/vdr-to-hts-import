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

from unittest.mock import Mock, patch

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

    importer.import_record(['file1', 'file1.ts', 'info', 'file2.ts', 'a.ts', '.ts', 'a'])

    config = {
        "enabled": True,
        "title": {
            "fin": "title1"
        },
        "comment": "added by vdr_to_hts_import.py",
        "files": [
            {"filename": "root/file1.ts"},
            {"filename": "root/file2.ts"},
            {"filename": "root/a.ts"},
            {"filename": "root/.ts"},
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


def test_info_get_channel_name(mocker):
    open_mock = mocker.mock_open(read_data='C some-id channel1\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'channel1' == info.get_channel_name()


def test_info_get_channel_name_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='C some-id name of channel 1\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'name of channel 1' == info.get_channel_name()


def test_info_get_channel_name_no_id(mocker):
    open_mock = mocker.mock_open(read_data='C channel1\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(ValueError) as exc_info:
            info.get_channel_name()
        assert 'substring not found' == str(exc_info.value)


def test_info_get_channel_name_no_channel(mocker):
    open_mock = mocker.mock_open(read_data='Y channel1\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_channel_name()
        assert 'no channel in info file test/info' == str(exc_info.value)


def test_info_get_description(mocker):
    open_mock = mocker.mock_open(read_data='D description1\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'description1' == info.get_description()


def test_info_get_description_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='D description with spaces\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'description with spaces' == info.get_description()


def test_info_get_description_no_description(mocker):
    open_mock = mocker.mock_open(read_data='Y no description\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_description()
        assert 'no description in info file test/info' == str(exc_info.value)


def test_info_get_duration(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 234 == info.get_duration()


def test_info_get_duration_additional_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid FF\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 234 == info.get_duration()


def test_info_get_duration_wrong_number_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 tableid\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_duration()
        assert 'expected at least 4 EPG event items but got 3 in info file test/info' == str(exc_info.value)


def test_info_get_duration_invalid_format(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 23a4i tableid\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_duration()
        assert 'EPG duration is wrong format in info file test/info' == str(exc_info.value)


def test_info_get_duration_no_duration(mocker):
    open_mock = mocker.mock_open(read_data='Y no event\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_duration()
        assert 'no EPG event in info file test/info' == str(exc_info.value)


def test_info_get_subtitle(mocker):
    open_mock = mocker.mock_open(read_data='S subtitle1\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'subtitle1' == info.get_subtitle()


def test_info_get_subtitle_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='S subtitle with spaces\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'subtitle with spaces' == info.get_subtitle()


def test_info_get_subtitle_no_subtitle(mocker):
    open_mock = mocker.mock_open(read_data='Y no text\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_subtitle()
        assert 'no subtitle in info file test/info' == str(exc_info.value)


def test_info_get_start_date_time(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 12312 == info.get_start_date_time()


def test_info_get_start_date_time_additional_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid FF\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 12312 == info.get_start_date_time()


def test_info_get_start_date_time_wrong_number_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 tableid\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_start_date_time()
        assert 'expected at least 4 EPG event items but got 3 in info file test/info' == str(exc_info.value)


def test_info_get_start_date_time_invalid_format(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12a312c 234 tableid\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_start_date_time()
        assert 'EPG start date time is wrong format in info file test/info' == str(exc_info.value)


def test_info_get_start_date_time_no_start_date_time(mocker):
    open_mock = mocker.mock_open(read_data='Y no event\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_start_date_time()
        assert 'no EPG event in info file test/info' == str(exc_info.value)


def test_info_get_title(mocker):
    open_mock = mocker.mock_open(read_data='T title1\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'title1' == info.get_title()


def test_info_get_title_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='T title with spaces\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        assert 'title with spaces' == info.get_title()


def test_info_get_title_no_title(mocker):
    open_mock = mocker.mock_open(read_data='Y no title\n')
    info = Info('test')

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_title()
        assert 'no title in info file test/info' == str(exc_info.value)
