import re

from ruamel.yaml import YAML


def load_yaml(filename: str) -> list | dict:
    with open(filename, 'r') as f:
        yaml = YAML(typ="safe")
        return yaml.load(f)


def paths_to_dict(paths: list[tuple], no_cmd: str = '') -> dict:
    """
    Turn list of paths into dict.
    Example:
    [('k1',),('k1', 'k2'), ('k1', 'k2', 'k3'), ('k1', 'k4')]
    ->
    {
        k1: {
            k2: {
                k3: {},
            },
            k4: {},
        },
    }
    """
    result = dict()
    for path in paths:
        current = result
        for p in path:
            if no_cmd:
                if M := re.match(f'^{no_cmd}(.*$)', p):
                    p_wo_no = str(M.groups()[0])
                    if p_wo_no in current:
                        current.pop(p_wo_no)
                        continue
                else:
                    no_p = f"{no_cmd}{p}"
                    if no_p in current:
                        current.pop(no_p)
            if p in current:
                current = current[p]
            else:
                current[p] = dict()
    return result


def indented_to_dict(
    config: str, indent_char: str = " ", indent: int = 3, comments: list[str] = None, no_cmd: str = ''
):
    """
    Create nested dict from indentet config.
    Example:
    interface e1
      switchport access vlan 1
      switchport mode access
      lldp
        enable
    ->
    {
        'interface e1': {
            'switchport access vlan 1': {},
            'switchport mode access': {},
            'lldp': {
                'enable': {},
            },
        },
    }
    """
    comments = comments if comments else list()
    indented_lines = []
    paths = ['!FOOBAR']
    for i, line in enumerate(config.splitlines()):
        if any(re.match(comment, line) for comment in comments):
            continue
        name = line.lstrip(indent_char).rstrip()
        level = (len(line) - len(name)) // indent
        indented_lines.append((i, level, name))
        paths.append([p for p in paths[-1][:level]] + [name])
    paths = paths[1:]

    return paths_to_dict(paths, no_cmd)


def remove_key_nokey(d: dict, no: str = "no "):
    """
    Recursively eliminate 'key' 'no key' same level pairs from nested dict.
    Example:
    {
        'interface e1': {
            'switchport': {},
            'lldp': {
                'enable': {},
            },
            'no switchport': {},
        },
    }
    ->
    {
        'interface e1': {
            'lldp': {
                'enable': {},
            },
        },
    }
    """
    keys = list(d)
    for k in keys:
        nokey = f"{no}{k}"
        if k in keys and nokey in keys:
            if keys.index(nokey) > keys.index(k):
                d.pop(k)
                d.pop(nokey)
            elif keys.index(k) > keys.index(nokey):
                d.pop(nokey)
    for k in list(d):
        remove_key_nokey(d[k])


def get_subdict_by_path(d: dict, path: list = None):
    """
    Follow the path and return subdict.
    Example in yaml:
    path: [k1, k2]
    k1:
      k2:
       k3: {}
       k4: {}
      k5: {}
      k6: {}
    ->
    k3: {}
    k4: {}
    """
    result = d
    for p in path:
        if p in result:
            result = result[p]
        else:
            result[p] = dict()
            result = result[p]
    return result


def dict_path(d: dict, path: list = None):
    """
    Recursively transform a dict into list of paths.
    Example (yaml):
    k1:
      k2:
        k3: {}
      k5': {}
    k4: {}
    ->
    [['k1', 'k2', 'k3'], ['k1', 'k5'], ['k4']]
    """
    if path is None:
        path = []

    if not isinstance(d, dict) or d == dict():
        return [path]

    result = []

    for k, v in d.items():
        dp_k = dict_path(v, path + [k])
        result.extend(dp_k)

    return result


def paths_by_path_ptrns(d: dict, path: list[str] = None) -> list:
    """
    Transform a dict into paths list (see dict_path) and filter by list of paths patterns.
    Returns filtered list of paths(lists).
    Example yaml:
    path: ['k1', 'k2', 'the*']
    k1:
      k2:
        k3: {}
        the_key: {}
      k5': {}
    k4: {}
    ->
    [['k1', 'k2', 'the_key']]
    """

    path = path if path else list()
    result = dict_path(d)

    # apply path pattern filter
    for i, ptrn in enumerate(path):
        result = [r for r in result if len(r) > i and re.match(ptrn, r[i])]

    # trim by path pattern length
    result = [r[: len(path)] for r in result]

    return [list(t) for t in set([tuple(r) for r in result])]
