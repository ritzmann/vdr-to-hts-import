import pytest

from vdr_to_hts_import import Info


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
