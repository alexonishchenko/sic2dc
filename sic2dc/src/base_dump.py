import logging
import re

from ruamel.yaml import YAML
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.compat import StringIO

from sic2dc.src.tools import get_subdict_by_path


def pathlist2dict(l: list[str], value: dict | None = None) -> dict:
    current = value
    for p in l[::-1]:
        current = {p: current}
    return current


class NonAliasingRTRepresenter(RoundTripRepresenter):
    def ignore_aliases(self, data):
        return True


class StrYaml(YAML):
    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        self.Representer = NonAliasingRTRepresenter
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()


logger = logging.getLogger()


def dump_action(action_dict: dict, path: list[str], symbol: str, color: bool = False) -> list[str]:
    """
    Dump single path action (add/del) to text.
    """
    if not action_dict:
        return []

    if path:
        path_dict = pathlist2dict(path)
        subpath_dict = get_subdict_by_path(path_dict, path[:-1])
        subpath_dict[path[-1]] = action_dict
    else:
        path_dict = action_dict

    yaml = StrYaml(typ=['rt'])
    e = yaml.emitter
    e.MAX_SIMPLE_KEY_LENGTH = 1024
    s = yaml.dump(path_dict).split('\n')

    s_formatted = list(map(lambda x: re.sub('^[- ] ', f"  ", x), s))
    color_end = '\033\u001b[0m' if color else ''
    s_no_nones = list(map(lambda x: re.sub(r'\:( None| \{\})?$', color_end, x), s_formatted))

    result = list()

    for i, line in enumerate([snn for snn in s_no_nones if snn]):
        if i >= len(path):
            result.append(re.sub(r'(^\s*)', f"{symbol} " + r"\1", line))
        else:
            result.append(line)

    return result


class DumpMixin:
    diff_dict: dict

    def dump(self, quiet: bool = True, color: bool = False):
        """
        Dump diff in text form.
        """
        result = list()
        char_add = '\u001b[32m' if color else ''
        char_add += '+'
        char_del = '\u001b[31m' if color else ''
        char_del += '-'
        for k, v in self.diff_dict.items():
            lines_add = dump_action(v['add'], k, char_add, color)
            lines_del = dump_action(v['del'], k, char_del, color)
            if lines_add:
                lines_del = lines_del[len(k) :]
            result.extend(lines_add + lines_del)
        if not quiet:
            print('\n'.join(result))
        return result
