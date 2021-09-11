import pytest

from vdr_to_hts_import import Info, InfoError


def test_get_channel_name():
    info = Info('test')
    info.info['C'] = 'some-id channel1'

    assert 'channel1' == info.get_channel_name()


def test_get_channel_name_with_multiple_spaces():
    info = Info('test')
    info.info['C'] = 'some-id name of channel 1'

    assert 'name of channel 1' == info.get_channel_name()


def test_get_channel_name_no_id():
    info = Info('test')
    info.info['C'] = 'channel1'

    with pytest.raises(ValueError) as exc_info:
        info.get_channel_name()
    assert 'substring not found' == str(exc_info.value)


def test_get_channel_name_no_channel():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_channel_name()
    assert 'no channel in info file' == str(exc_info.value)


def test_get_description():
    info = Info('test')
    info.info['D'] = 'description1'

    assert 'description1' == info.get_description()


def test_get_description_with_multiple_spaces():
    info = Info('test')
    info.info['D'] = 'description with spaces'

    assert 'description with spaces' == info.get_description()


def test_get_description_no_description():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_description()
    assert 'no description in info file' == str(exc_info.value)


def test_get_short_description():
    info = Info('test')
    info.info['S'] = 'shortdescription1'

    assert 'shortdescription1' == info.get_short_description()


def test_get_short_description_with_multiple_spaces():
    info = Info('test')
    info.info['S'] = 'short description with spaces'

    assert 'short description with spaces' == info.get_short_description()


def test_get_short_description_no_short_description():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_short_description()
    assert 'no short description in info file' == str(exc_info.value)


def test_get_title():
    info = Info('test')
    info.info['T'] = 'title1'

    assert 'title1' == info.get_title()


def test_get_title_with_multiple_spaces():
    info = Info('test')
    info.info['T'] = 'title with spaces'

    assert 'title with spaces' == info.get_title()


def test_get_title_no_title():
    info = Info('test')
    # Need at least one entry so that Info does not try to load data from a file
    info.info['Y'] = 'value'

    with pytest.raises(InfoError) as exc_info:
        info.get_title()
    assert 'no title in info file' == str(exc_info.value)
