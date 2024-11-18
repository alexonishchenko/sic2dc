from pathlib import Path

from ruamel.yaml import YAML

from sic2dc.src.config_compare import ConfigCompareBase
from sic2dc.src.tools import load_yaml


def test_key_nokey():
    f1 = Path(__file__).parent / 'configs/arista1_short_nokey.cfg'
    f2 = f1

    file_settings = Path(__file__).parent.parent / 'example/settings_arista_dcs.yml'
    file_filters = Path(__file__).parent.parent / 'example/filters_arista_dcs.yml'

    settings = load_yaml(str(file_settings.absolute()))
    filters = load_yaml(str(file_filters.absolute()))

    # check nokey deleted
    cc = ConfigCompareBase(str(f1.absolute()), str(f2.absolute()), settings, filters)
    f_result = Path(__file__).parent / 'configs/arista1_short_nokey.yml'
    assert cc.d1 == load_yaml(str(f_result.absolute()))

    # check nokey not deleted because key added after
    f1 = Path(__file__).parent / 'configs/arista1_short_nokey_after.cfg'
    cc = ConfigCompareBase(str(f1.absolute()), str(f2.absolute()), settings, filters)

    f_result = Path(__file__).parent / 'configs/arista1_short.yml'
    assert cc.d1 == load_yaml(str(f_result.absolute()))
