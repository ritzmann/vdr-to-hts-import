import pytest

import vdr_to_hts_import
from vdr_to_hts_import import DirWalker, Info, InfoError


def test_dir_walker(mocker):
    mocker.patch('os.listdir', return_value=['dir1', 'dir2', 'dir3'])
    mocker.patch('os.walk', return_value=[['root1', [], ['file1', 'file2.ts']]])
    import_record_mock = mocker.patch('vdr_to_hts_import.import_record')
    dir_walker = DirWalker()

    dir_walker.walk()

    import_record_mock.assert_has_calls([
        mocker.call('root1/file2.ts', vdr_to_hts_import.config_template, vdr_to_hts_import.api_url),
        mocker.call('root1/file2.ts', vdr_to_hts_import.config_template, vdr_to_hts_import.api_url),
        mocker.call('root1/file2.ts', vdr_to_hts_import.config_template, vdr_to_hts_import.api_url)
    ])


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
