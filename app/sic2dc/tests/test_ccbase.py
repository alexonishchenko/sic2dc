from pathlib import Path
import pytest

from ruamel.yaml import YAML

from .example_input import EXAMPLE_FILTERS_ARISTA, EXAMPLE_SETTINGS_ARISTA
from sic2dc.src.config_compare import ConfigCompareBase

def from_yaml(s: str) -> dict:
    yaml = YAML(typ="safe")
    return yaml.load(s)


def test_cc_base():
    f1 = Path(__file__).parent / 'configs/arista_desired.cfg'
    f2 = Path(__file__).parent / 'configs/arista_oper.cfg'
    settings = from_yaml(EXAMPLE_SETTINGS_ARISTA)
    filters = from_yaml(EXAMPLE_FILTERS_ARISTA)
    cc = ConfigCompareBase(str(f1.absolute()), str(f2.absolute()), settings, filters)

    assert not cc.diff_dict


def test_cc_diff_vlan():
    f1 = Path(__file__).parent / 'configs/arista_desired_vlan_add.cfg'
    f2 = Path(__file__).parent / 'configs/arista_oper.cfg'
    settings = from_yaml(EXAMPLE_SETTINGS_ARISTA)
    filters = from_yaml(EXAMPLE_FILTERS_ARISTA)
    cc = ConfigCompareBase(str(f1.absolute()), str(f2.absolute()), settings, filters)

    assert cc.diff_dict

    vlan_add_diff = {
        'add': {'switchport trunk allowed vlan 11': {}}, 'del': {'switchport trunk allowed vlan 11,13': {}}
    }

    assert cc.diff_dict[('interface Port-Channel1',)] == vlan_add_diff
