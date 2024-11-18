from pathlib import Path

from ruamel.yaml import YAML

from sic2dc.src.config_compare import ConfigCompareBase, sic2dc
from sic2dc.src.tools import load_yaml


def test_cc_base():
    f1 = Path(__file__).parent / 'configs/arista_desired.cfg'
    f2 = Path(__file__).parent / 'configs/arista_oper.cfg'
    file_settings = Path(__file__).parent.parent / 'example/settings_arista_dcs.yml'
    file_filters = Path(__file__).parent.parent / 'example/filters_arista_dcs.yml'

    settings = load_yaml(str(file_settings.absolute()))
    filters = load_yaml(str(file_filters.absolute()))

    cc = ConfigCompareBase(str(f1.absolute()), str(f2.absolute()), settings, filters)

    assert not cc.diff_dict


def test_cc_diff_vlan():
    f1 = Path(__file__).parent / 'configs/arista_desired_vlan_add.cfg'
    f2 = Path(__file__).parent / 'configs/arista_oper.cfg'

    file_settings = Path(__file__).parent.parent / 'example/settings_arista_dcs.yml'
    file_filters = Path(__file__).parent.parent / 'example/filters_arista_dcs.yml'

    settings = load_yaml(str(file_settings.absolute()))
    filters = load_yaml(str(file_filters.absolute()))

    cc = ConfigCompareBase(str(f1.absolute()), str(f2.absolute()), settings, filters)

    assert cc.diff_dict

    vlan_add_diff = {
        'add': {'switchport trunk allowed vlan 11': {}},
        'del': {'switchport trunk allowed vlan 11,13': {}},
    }

    assert cc.diff_dict[('interface Port-Channel1',)] == vlan_add_diff


def test_cc_base_cure():
    f1 = Path(__file__).parent / 'configs/b4com4100_address_families.cfg'
    f2 = Path(__file__).parent / 'configs/b4com4100_address_families_cured.cfg'

    file_settings = Path(__file__).parent.parent / 'example/settings_b4com4100.yml'
    file_cures = Path(__file__).parent.parent / 'example/cures_b4com4100.yml'

    settings = load_yaml(str(file_settings.absolute()))
    cures = load_yaml(str(file_cures.absolute()))

    cc = ConfigCompareBase(str(f1.absolute()), str(f2.absolute()), settings, [], cures)

    assert cc.c1 == cc.c2_uncured


def test_sic2dc():
    f1 = Path(__file__).parent / 'configs/arista_desired.cfg'
    f2 = Path(__file__).parent / 'configs/arista_oper.cfg'
    file_settings = Path(__file__).parent.parent / 'example/settings_arista_dcs.yml'
    file_filters = Path(__file__).parent.parent / 'example/filters_arista_dcs.yml'

    settings = load_yaml(str(file_settings.absolute()))
    filters = load_yaml(str(file_filters.absolute()))

    result = sic2dc(str(f1.absolute()), str(f2.absolute()), settings, filters)

    assert not result['diff_dict'] and not result['diff_lines']


def test_sic2dc_diff_vlan():
    f1 = Path(__file__).parent / 'configs/arista_desired_vlan_add.cfg'
    f2 = Path(__file__).parent / 'configs/arista_oper.cfg'

    file_settings = Path(__file__).parent.parent / 'example/settings_arista_dcs.yml'
    file_filters = Path(__file__).parent.parent / 'example/filters_arista_dcs.yml'

    settings = load_yaml(str(file_settings.absolute()))
    filters = load_yaml(str(file_filters.absolute()))

    result = sic2dc(str(f1.absolute()), str(f2.absolute()), settings, filters)

    vlan_add_diff = {
        'add': {'switchport trunk allowed vlan 11': {}},
        'del': {'switchport trunk allowed vlan 11,13': {}},
    }
    vlan_add_diff_lines = [
        'interface Port-Channel1',
        '+   switchport trunk allowed vlan 11',
        '-   switchport trunk allowed vlan 11,13',
    ]

    assert result['diff_dict'][('interface Port-Channel1',)] == vlan_add_diff
    assert result['diff_lines'] == vlan_add_diff_lines
