from pathlib import Path

import ast
import json
import logging

from collections import defaultdict
from copy import deepcopy
from deepdiff import DeepDiff

from sic2dc.src.base_cures import CuresMixin
from sic2dc.src.base_dump import DumpMixin
from sic2dc.src.base_filters import FiltersMixin

from sic2dc.src.schema import CfgCmprCure, CfgCmprFilter, CfgCmprSettings
from sic2dc.src.tools import get_subdict_by_path, indented_to_dict, remove_key_nokey


logger = logging.getLogger()


class ConfigCompareBase(CuresMixin, FiltersMixin, DumpMixin):
    """
    Base Config Compare class reads two input files, cures them and transforms them into nested dicts.
    The dicts can be changed with the help of input filters. And then dicts are compared.
    Filters are transformed into list of objects of class CfgCmprFilter
        (filter actions examples are cp21, cp12, del1, del2, upd1,upd2).
    Cures are transformed into list of objects of class CfgCmprCure


    When ConfigCompareBase object is created it has 'diff_dict' property. 'diff_dict' keys are tuple paths to
        differing config  parts. Example

    diff_dict:
        {
            ('interface Port-Channel1',): {
                'add': {'switchport trunk allowed vlan 11': {}},
                'del': {'switchport trunk allowed vlan 11,13': {}},
            }
            ('interface Ethernet5', 'lldp'): {
                'del': {'enable': {}},
            }
        }


    ConfigCompareBase.dump() returns and/or prints out text (color) difference.
    """

    def __init__(
        self, f1: str, f2: str, settings: CfgCmprSettings, filters: list[dict] = None, cures: list[dict] = None
    ):
        """
        1. Create cc object: read files, apply cures and create d1 and d2.
        2. Apply filters to dicts
        3. Run comparison
        """
        settings: CfgCmprSettings
        cures: list[CfgCmprCure]
        filters: list[CfgCmprFilter]

        # set method list to help find filters
        self.method_list = [
            attribute
            for attribute in dir(self.__class__)
            if callable(getattr(self.__class__, attribute)) and attribute.startswith('__') is False
        ]

        cures = cures if cures else list()
        filters = filters if filters else list()

        # initial sets
        self.cures = [CfgCmprCure(**cure) for cure in cures]
        self.filters = [CfgCmprFilter(**filter) for filter in filters]
        self.settings = CfgCmprSettings(**settings)

        self.f1 = str(Path(f1).absolute())
        self.f2 = str(Path(f2).absolute())

        # files read
        with open(self.f1, 'r') as f:
            self.c1 = f.read()
        with open(self.f2, 'r') as f:
            self.c2 = f.read()

        self.c1_uncured = deepcopy(self.c1)
        self.c2_uncured = deepcopy(self.c2)

        # apply cures to text configs
        self.apply_cures()

        # set dicts from files
        no_cmd = self.settings.no_cmd if self.settings.no_cmd and self.settings.ignore_cmd_nocmd else ''
        self.d1 = indented_to_dict(
            self.c1, **self.settings.model_dump(include=['indent', 'indent_char', 'comments']), no_cmd=no_cmd
        )
        self.d2 = indented_to_dict(
            self.c2, **self.settings.model_dump(include=['indent', 'indent_char', 'comments']), no_cmd=no_cmd
        )

        self.d1_unfiltered = deepcopy(self.d1)
        self.d2_unfiltered = deepcopy(self.d2)

        # apply filters to dicts
        self.apply_filters()

        # run comparison
        self.compare()

    def apply_cures(self):
        """
        Apply cures
        """
        for i, cure in enumerate(self.cures):
            action = cure.action
            if action and action in self.method_list:
                action_method = getattr(self, action)
                action_method(cure)
            else:
                logger.error(f"Wrong cure {i}: {cure.model_dump()}")

    def apply_filters(self):
        """
        Apply filters.
        """
        for i, filter in enumerate(self.filters):
            action = filter.action
            if action and action in self.method_list:
                action_method = getattr(self, action)
                action_method(filter)
            else:
                logger.error(f"Wrong filter {i}: {filter.model_dump()}")

    def compare(self):
        """
        Compare prepared dicts using deepdiff and set diff_dict - subdicts to be added and to be removed from d2
        """
        dif = DeepDiff(self.d1, self.d2)

        dif_add = [
            tuple(ast.literal_eval(p.replace("root", "").replace('"', '').replace('][', ', ')))
            for p in dif.get('dictionary_item_added', [])
        ] + [
            tuple(
                ast.literal_eval(
                    p.replace("root", "")
                    .replace('"', '')
                    .replace('][', ', ')
                    .replace(']', f",'{list(v['new_value'])[0]}']")
                )
            )
            for p, v in dif.get('values_changed', dict()).items()
        ]
        dif_del = [
            tuple(ast.literal_eval(p.replace("root", "").replace('"', '').replace('][', ', ')))
            for p in dif.get('dictionary_item_removed', [])
        ] + [
            tuple(
                ast.literal_eval(
                    p.replace("root", "")
                    .replace('"', '')
                    .replace('][', ', ')
                    .replace(']', f",'{list(v['old_value'])[0]}']")
                )
            )
            for p, v in dif.get('values_changed', {}).items()
        ]

        diff_dict = defaultdict(dict)

        for path in set(dif_add + dif_del):
            result_path = path[:-1]
            key = tuple(result_path)
            if not key in diff_dict:
                diff_dict[key]['add'] = dict()
                diff_dict[key]['del'] = dict()
            if path in dif_add:
                diff_dict[key]['add'][path[-1]] = get_subdict_by_path(self.d2, path)
            if path in dif_del:
                diff_dict[key]['del'][path[-1]] = get_subdict_by_path(self.d1, path)

        pass

        self.diff_dict = dict(diff_dict)


def sic2dc(
    f1: str,
    f2: str,
    settings: dict,
    filters: list[dict] | None = None,
    cures: list[dict] | None = None,
    color: bool = False,
) -> dict:
    """
    Creates ConfigCompareBase object and compares f1 and f2.
    Returns ConfigCompareBase.diff_dict and ConfigCompareBase.dump() lines as dict
    Returns dict:
        'diff_dict': dict
        'diff_lines': str
    """

    # dirty hack: transform filters and cures from e.g. AnsibleBaseYAMLObject into native python objects.
    cures = json.loads(json.dumps(cures)) if cures else list()
    filters = json.loads(json.dumps(filters)) if filters else list()
    settings = json.loads(json.dumps(settings))

    # init cc object
    cc = ConfigCompareBase(f1, f2, settings, filters=filters, cures=cures)

    # return diff_dict and text diff form.
    return {'diff_dict': cc.diff_dict, 'diff_lines': cc.dump(quiet=True, color=color)}
