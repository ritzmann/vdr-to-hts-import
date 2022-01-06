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
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from requests.auth import HTTPDigestAuth

import vdr_to_hts_import
from vdr_to_hts_import import Config, DirWalker, Importer, Info, InfoError, UnicodeEscapeHeuristic


def test_dir_walker_walk(mocker):
    mocker.patch('pathlib.Path.iterdir', return_value=[Path('dir1'), Path('dir2'), Path('dir3')])
    mocker.patch('pathlib.Path.is_dir', return_value=True)
    file_list = ['file1', 'file2.ts', 'info']
    mocker.patch('os.walk', return_value=[['root1', [], file_list]])
    importer_mock = mocker.patch('vdr_to_hts_import.Importer')

    DirWalker.walk('top')

    importer_mock.assert_has_calls([
        mocker.call.import_record(Path('root1'), file_list),
        mocker.call.import_record(Path('root1'), file_list),
        mocker.call.import_record(Path('root1'), file_list)
    ])


def test_importer_import_record(mocker):
    mocker.patch('vdr_to_hts_import.Config.create_from_info', return_value={
        "enabled": True,
        "title": {"fin": "title1"},
        "comment": "added by vdr_to_hts_import.py",
        "files": [{"filename": "root/concat.ts"}],
        "channelname": "channel1",
        "subtitle": {"fin": "subtitle1"},
        "description": {"fin": "description 1"},
        "start": 1231,
        "stop": 1996
    })
    response_mock = mocker.patch('requests.post', return_value=Mock())
    response_mock.text = 'response1'

    Importer.import_record('root', ['file1', 'file1.ts', 'info', 'file2.ts', 'a.ts', '.ts', 'a'])

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    config = {
        "enabled": True,
        "title": {"fin": "title1"},
        "comment": "added by vdr_to_hts_import.py",
        "files": [{"filename": "root/concat.ts"}],
        "channelname": "channel1",
        "subtitle": {"fin": "subtitle1"},
        "description": {"fin": "description 1"},
        "start": 1231,
        "stop": 1996
    }
    response_mock.assert_called_once_with(vdr_to_hts_import.api_url,
                                          auth=HTTPDigestAuth(vdr_to_hts_import.user, vdr_to_hts_import.password),
                                          headers=headers,
                                          data="conf={}".format(json.dumps(config)))


def test_importer_import_record_no_ts_files(mocker):
    mocker.patch.multiple('vdr_to_hts_import.Info',
                          get_channel_name=Mock(return_value='channel1'),
                          get_title=Mock(return_value='title1'),
                          get_start_date_time=Mock(return_value=1231),
                          get_duration=Mock(return_value=765))

    with pytest.raises(InfoError) as exc_info:
        Importer.import_record(Path('root'), ['file1', 'info'])
    assert 'found info file but no .ts files in directory root' == str(exc_info.value)


def test_config_single_ts_file(mocker):
    mocker.patch.multiple('vdr_to_hts_import.Info',
                          get_channel_name=Mock(return_value='channel1'),
                          get_description=Mock(return_value='description 1'),
                          get_subtitle=Mock(return_value='subtitle1'),
                          get_title=Mock(return_value='title1'),
                          get_start_date_time=Mock(return_value=1231),
                          get_duration=Mock(return_value=768))
    open_mock = mocker.mock_open()
    mocker.patch('subprocess.run')
    config = Config(Path('root'), ['file1.ts', 'info'])

    with patch('builtins.open', open_mock):
        assert {
           'channelname': 'channel1',
           'comment': 'added by vdr_to_hts_import.py',
           'description': {'fin': 'description 1'},
           'enabled': True,
           'files': [{'filename': 'root/file1.ts'}],
           'start': 1231,
           'stop': 1231 + 768,
           'subtitle': {'fin': 'subtitle1'},
           'title': {'fin': 'title1'}
        } == config.create_from_info()


def test_config_multiple_ts_files(mocker):
    mocker.patch.multiple('vdr_to_hts_import.Info',
                          get_channel_name=Mock(return_value='channel1'),
                          get_description=Mock(return_value='description 1'),
                          get_subtitle=Mock(return_value='subtitle1'),
                          get_title=Mock(return_value='title1'),
                          get_start_date_time=Mock(return_value=1231),
                          get_duration=Mock(return_value=768))
    open_mock = mocker.mock_open()
    mocker.patch('subprocess.run')
    config = Config(Path('root'), ['file1.ts', 'info', 'file2.ts'])

    with patch('builtins.open', open_mock):
        assert {
           'channelname': 'channel1',
           'comment': 'added by vdr_to_hts_import.py',
           'description': {'fin': 'description 1'},
           'enabled': True,
           'files': [{'filename': 'root/concat.ts'}],
           'start': 1231,
           'stop': 1231 + 768,
           'subtitle': {'fin': 'subtitle1'},
           'title': {'fin': 'title1'}
        } == config.create_from_info()


def test_info_get_channel_name(mocker):
    open_mock = mocker.mock_open(read_data='C some-id channel1\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'channel1' == info.get_channel_name()


def test_info_get_channel_name_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='C some-id name of channel 1\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'name of channel 1' == info.get_channel_name()


def test_info_get_channel_name_no_id(mocker):
    open_mock = mocker.mock_open(read_data='C channel1\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(ValueError) as exc_info:
            info.get_channel_name()
        assert 'substring not found' == str(exc_info.value)


def test_info_get_channel_name_no_channel(mocker):
    open_mock = mocker.mock_open(read_data='Y channel1\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_channel_name()
        assert 'no channel in info file test/info' == str(exc_info.value)


def test_info_get_channel_name_open_exception(mocker):
    open_mock = mocker.mock_open()
    open_mock.side_effect = IOError('test message')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(IOError) as exc_info:
            info.get_channel_name()
        assert 'test message' == str(exc_info.value)


def test_info_get_description(mocker):
    open_mock = mocker.mock_open(read_data='D description1\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'description1' == info.get_description()


def test_info_get_description_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='D description with spaces\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'description with spaces' == info.get_description()


def test_info_get_description_no_description(mocker):
    open_mock = mocker.mock_open(read_data='Y no description\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_description()
        assert 'no description in info file test/info' == str(exc_info.value)


def test_info_get_duration(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 234 == info.get_duration()


def test_info_get_duration_additional_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid FF\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 234 == info.get_duration()


def test_info_get_duration_wrong_number_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 tableid\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_duration()
        assert 'expected at least 4 EPG event items but got 3 in info file test/info' == str(exc_info.value)


def test_info_get_duration_invalid_format(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 23a4i tableid\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_duration()
        assert 'EPG duration is wrong format in info file test/info' == str(exc_info.value)


def test_info_get_duration_no_duration(mocker):
    open_mock = mocker.mock_open(read_data='Y no event\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_duration()
        assert 'no EPG event in info file test/info' == str(exc_info.value)


def test_info_get_subtitle(mocker):
    open_mock = mocker.mock_open(read_data='S subtitle1\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'subtitle1' == info.get_subtitle()


def test_info_get_subtitle_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='S subtitle with spaces\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'subtitle with spaces' == info.get_subtitle()


def test_info_get_subtitle_no_subtitle(mocker):
    open_mock = mocker.mock_open(read_data='Y no text\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        subtitle = info.get_subtitle()

    assert subtitle is None


def test_info_get_start_date_time(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 12312 == info.get_start_date_time()


def test_info_get_start_date_time_additional_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 234 tableid FF\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 12312 == info.get_start_date_time()


def test_info_get_start_date_time_wrong_number_event_items(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12312 tableid\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_start_date_time()
        assert 'expected at least 4 EPG event items but got 3 in info file test/info' == str(exc_info.value)


def test_info_get_start_date_time_invalid_format(mocker):
    open_mock = mocker.mock_open(read_data='E eventid 12a312c 234 tableid\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_start_date_time()
        assert 'EPG start date time is wrong format in info file test/info' == str(exc_info.value)


def test_info_get_start_date_time_no_start_date_time(mocker):
    open_mock = mocker.mock_open(read_data='Y no event\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_start_date_time()
        assert 'no EPG event in info file test/info' == str(exc_info.value)


def test_info_get_title(mocker):
    open_mock = mocker.mock_open(read_data='T title1\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'title1' == info.get_title()


def test_info_get_title_unicode_escape(mocker):
    open_mock = mocker.mock_open(read_data='T s\\u00f6me Finnish title\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'söme Finnish title' == info.get_title()


def test_info_get_title_utf_8(mocker):
    open_mock = mocker.mock_open(read_data='T söme Finnish title\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'söme Finnish title' == info.get_title()


def test_info_get_title_with_multiple_spaces(mocker):
    open_mock = mocker.mock_open(read_data='T title with spaces\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        assert 'title with spaces' == info.get_title()


def test_info_get_title_no_title(mocker):
    open_mock = mocker.mock_open(read_data='Y no title\n')
    info = Info(Path('test'))

    with patch('builtins.open', open_mock):
        with pytest.raises(InfoError) as exc_info:
            info.get_title()
        assert 'no title in info file test/info' == str(exc_info.value)


def test_unicode_ascii():
    assert 'test' == UnicodeEscapeHeuristic.decode('test')


def test_unicode_url_encoded():
    assert 'söme' == UnicodeEscapeHeuristic.decode('s\\u00f6me')


def test_unicode_utf_8():
    assert 'söme' == UnicodeEscapeHeuristic.decode('söme')
