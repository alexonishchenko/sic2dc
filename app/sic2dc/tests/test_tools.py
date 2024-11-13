import pytest

from sic2dc.src.tools import (
    dict_path,
    get_subdict_by_path,
    indented_to_dict,
    paths_to_dict,
    paths_by_path_ptrns,
    remove_key_nokey,
)


@pytest.mark.parametrize(
    "paths, result",
    [
        ([('k1',), ('k1', 'k2'), ('k1', 'k2', 'k3'), ('k1', 'k4')], {'k1': {'k2': {'k3': {}}, 'k4': {}}}),
        ([('k1',), ('k1', 'k2'), ('k3',), ('k3', 'k4')], {'k1': {'k2': {}}, 'k3': {'k4': {}}}),
    ],
)
def test_paths_to_dict(paths: list[tuple], result: dict):
    assert paths_to_dict(paths) == result


@pytest.mark.parametrize(
    "config, indent_char, indent, comments, result",
    [
        ('arista_short_str', ' ', 3, ['^\\s*!.*$'], 'arista_short_dict'),
    ],
)
def test_indented_to_dict(config: str, indent_char: str, indent: int, comments: list[str], result, request):
    config = request.getfixturevalue(config)
    result = request.getfixturevalue(result)
    assert indented_to_dict(config, indent_char, indent, comments) == result


def test_remove_key_nokey():
    d1 = {
        'interface e1': {
            'switchport': {},
            'ip address 1.1.1.1/32': {},
            'lldp': {
                'enable': {},
            },
            'no switchport': {},
        },
        'interface e2': {
            'shutdown': {},
            'no shutdown': {},
        },
    }
    d2 = {
        'interface e1': {
            'ip address 1.1.1.1/32': {},
            'lldp': {
                'enable': {},
            },
        },
        'interface e2': {},
    }

    remove_key_nokey(d1)

    assert d1 == d2


def test_get_subdict_by_path():
    d1 = {
        'interface e1': {
            'switchport': {},
            'ip address 1.1.1.1/32': {},
            'lldp': {
                'enable': {},
            },
            'no switchport': {},
        },
        'interface e2': {
            'shutdown': {},
            'no shutdown': {},
        },
    }

    path = ['interface e1', 'lldp']

    d2 = {'enable': {}}

    assert get_subdict_by_path(d1, path) == d2


def test_dict_path():
    d1 = {
        'k1': {
            'k2': {
                'k3': {},
            },
            'k5': {},
        },
        'k4': {},
    }

    paths = [['k1', 'k2', 'k3'], ['k1', 'k5'], ['k4']]
    assert dict_path(d1) == paths


EXAMPLE_DICT = {
    'interface e1': {
        'no shutdown': {},
        'switchport mode access': {},
        'switchport access vlan 1': {},
        'switchport': {},
    },
    'interface e2': {
        'no shutdown': {},
        'switchport mode access': {},
        'switchport access vlan 2': {},
        'switchport': {},
    },
    'interface e3': {
        'no shutdown': {},
        'switchport mode access': {},
        'switchport access vlan 3': {},
        'switchport': {},
    },
    'router bgp 6666': {'router-id 1': {}},
}


@pytest.mark.parametrize(
    "d, path, result",
    [
        (
            EXAMPLE_DICT,
            ['interface e*', 'switchport access vlan *'],
            [
                ['interface e1', 'switchport access vlan 1'],
                ['interface e2', 'switchport access vlan 2'],
                ['interface e3', 'switchport access vlan 3'],
            ],
        ),
        (
            EXAMPLE_DICT,
            ['interface e*'],
            [
                ['interface e1'],
                ['interface e3'],
                ['interface e2'],
            ],
        ),
        (
            EXAMPLE_DICT,
            ['router bgp 6666'],
            [['router bgp 6666']],
        ),
    ],
)
def test_paths_by_path_ptrns(d: dict, path: list[str], result: list[str]):
    assert sorted(paths_by_path_ptrns(d, path)) == sorted(result)
