from pathlib import Path

import ast
import logging
import re

from collections import defaultdict
from copy import deepcopy
from deepdiff import DeepDiff

from sic2dc.src.schema import CfgCmprCure, CfgCmprFilter, CfgCmprSettings, When
from sic2dc.src.tools import get_subdict_by_path, indented_to_dict, paths_by_path_ptrns, remove_key_nokey


logger = logging.getLogger()


def _apply_whens(path_patterns: list[str], whens: list[When] = None, d1: dict = None, d2: dict = None) -> list[str]:
    d1 = d1 if d1 else dict()
    d2 = d2 if d2 else dict()
    path_patterns = path_patterns if path_patterns else []

    paths1 = paths_by_path_ptrns(d1, path_patterns)
    result = paths1
    banned_in_result = deepcopy(result)

    if whens:
        # d1 whens
        flag_use_banned = False
        for path in paths1:
            whens_results = list()
            subdict1 = get_subdict_by_path(d1, path)
            for when in whens:
                if when.has_children:
                    flag_use_banned = True
                    paths_with_children = paths_by_path_ptrns(subdict1, when.has_children)
                    if paths_with_children and path in banned_in_result:
                        whens_results.append(True)
                    else:
                        whens_results.append(False)
                if when.doesnt_have_chidren:
                    flag_use_banned = True
                    paths_with_children = paths_by_path_ptrns(subdict1, when.doesnt_have_chidren)
                    if not paths_with_children and path in banned_in_result:
                        whens_results.append(True)
                    else:
                        whens_results.append(False)

            if all(whens_results):
                banned_in_result.remove(path)

        if flag_use_banned:
            result = [r for r in result if r not in banned_in_result]
        banned_in_result = deepcopy(result)

        # d2 whens
        flag_use_banned = False
        for when in whens:
            if when.absent_in_destination:
                flag_use_banned = True
                paths2 = paths_by_path_ptrns(d2, path_patterns)
                paths_absent_in_d2 = [p for p in result if p not in paths2]
                for p in paths_absent_in_d2:
                    banned_in_result.remove(p)

        if flag_use_banned:
            result = [r for r in result if r not in banned_in_result]

        return result
    else:
        return result


class CuresMixin:
    c1: str
    c2: str
    settings: CfgCmprSettings

    def enter_exit(self, cure: CfgCmprCure):
        """
        Adds indentation by pattern.
        kwargs (yaml format):
        enter_exits:
          - enter: <str>
            exit: <str>

        Example b4com bgp address families:
        enter_exits:
          - enter: ' address-family \S+\s.*$'
            exit: ' exit-address-family$'
        router bgp 123
         ...
         address-family ipv4 unicast
         network 10.10.176.1/32
         max-paths ebgp 4
         neighbor 10.10.2.0 activate
         neighbor 10.10.2.2 activate
         neighbor 10.10.2.4 activate
         exit-address-family
         address-family l2vpn evpn
         neighbor 10.10.10.1 activate
         neighbor 10.10.10.2 activate
         neighbor 10.10.10.3 activate
         exit-address-family
         ...
        ->
        router bgp 123
         ...
         address-family l2vpn evpn
          neighbor 10.10.10.1 activate
          neighbor 10.10.10.2 activate
          neighbor 10.10.10.3 activate
          exit-address-family
         address-family ipv4 unicast
          network 10.10.176.1/32
          max-paths ebgp 4
          neighbor 10.10.2.0 activate
          neighbor 10.10.2.2 activate
          neighbor 10.10.2.4 activate
          exit-address-family
         ...
        """
        enter_exits = cure.kwargs.get('enter_exits', list())
        for config in [self.c1, self.c2]:
            enter_exit_level = 0
            result_config_lines = list()
            for line in config.splitlines():
                add_indent = str(enter_exit_level*(self.settings.indent_char*self.settings.indent))
                result_line = f"{add_indent}{line}"
                result_config_lines.append(result_line)
                for enter_exit in enter_exits:
                    if re.match(enter_exit['enter'], line):
                        enter_exit_level += 1
                    if re.match(enter_exit['exit'], line):
                        enter_exit_level -= 1
            config = '\n'.join(result_config_lines)


class FiltersMixin():
    d1: dict
    d2: dict

    @staticmethod
    def cp_single_path(d1: dict, d2: dict, path: list[str]) -> None:
        """
        Filter heper. Copy a path from d1 to d2.
        """
        subd1 = get_subdict_by_path(d1, path)
        subd2 = get_subdict_by_path(d2, path[:-1])
        subd2[path[-1]] = subd1
        pass

    def cp(self, d1: dict, d2: dict, path: list[str], whens: list[When]) -> None:
        """
        Filter helper. Copy from d1 to d2. d1 can be self.d1 or self.d2 and vice versa for d2.
        """
        paths_whens = _apply_whens(path, whens, d1, d2)

        pass
        for p in paths_whens:
            self.cp_single_path(d1, d2, p)

    def cp21(self, filter: CfgCmprFilter):
        """
        Filter. Copy from self.d2 to self.d1.
        """
        self.cp(self.d2, self.d1, filter.path, filter.when)

    def cp12(self, filter: CfgCmprFilter):
        """
        Filter. Copy from self.d2 to self.d2.
        """
        self.cp(self.d1, self.d2, filter.path, filter.when)

    @staticmethod
    def del_path(d: dict, path: list[str], whens: list[When]):
        """
        Filter. Del path in dict.
        """
        paths_whens = _apply_whens(path, whens, d)

        for p in paths_whens:
            subdict = get_subdict_by_path(d, p[:-1])
            subdict.pop(p[-1])

    def del1(self, filter: CfgCmprFilter):
        """
        Filter. Del in self.d1.
        """
        self.del_path(self.d1, filter.path, filter.when)

    def del2(self, filter: CfgCmprFilter):
        """
        Filter. Del in self.d2.
        """
        self.del_path(self.d2, filter.path, filter.when)

    @staticmethod
    def upd_path(d: dict, path: list[str], whens: list[When], data: dict):
        """
        Filter helper. Update dict at path with another dict.
        """
        paths_whens = _apply_whens(path, whens, d)
        for p in paths_whens:
            subdict = get_subdict_by_path(d, p)
            subdict.update(data)

    def upd1(self, filter: CfgCmprFilter):
        """
        Filter. Update self.d1 at path with data dict.
        """
        self.upd_path(self.d1, filter.path, filter.when, dict(filter.data))

    def upd2(self, filter: CfgCmprFilter):
        """
        Filter. Update self.d2 at path with data dict.
        """
        self.upd_path(self.d2, filter.path, filter.when, dict(filter.data))


class ConfigCompareBase(CuresMixin, FiltersMixin):
    """
    Base Config Compare class reads two input files, cures them and transforms them into nested dicts.
    The dicts can be changed with the help of input filters. And then dicts are compared.
    Filters are objects of class CfgCmprFilter (filter actions examples are cp21, cp12, del1, del2, upd1,upd2).
    """
    def __init__(self, f1: str, f2: str, settings: CfgCmprSettings, filters: list[dict] = None, cures: list[dict] = None):
        """
        1. Create cc object: read files, apply cures and create d1 and d2. 
        2. Apply filters to dicts
        3. Run comparison
        """
        settings: CfgCmprSettings
        cures: list[CfgCmprCure]
        filters: list[CfgCmprFilter]

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
        self.d1 = indented_to_dict(self.c1, **self.settings.model_dump(include=['indent', 'indent_char', 'comments']))
        self.d2 = indented_to_dict(self.c2, **self.settings.model_dump(include=['indent', 'indent_char', 'comments']))

        self.d1_unfiltered = deepcopy(self.d1)
        self.d2_unfiltered = deepcopy(self.d2)
        
        # set method list to help find filters
        self.method_list = [
            attribute
            for attribute in dir(self.__class__)
            if callable(getattr(self.__class__, attribute)) and attribute.startswith('__') is False
        ]

        # apply filters to dicts
        self.apply_filters()

        # apply cmd no cmd
        if self.settings.ignore_cmd_nocmd:
            remove_key_nokey(self.d1)
            remove_key_nokey(self.d2)

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
        ]
        dif_del = [
            tuple(ast.literal_eval(p.replace("root", "").replace('"', '').replace('][', ', ')))
            for p in dif.get('dictionary_item_removed', [])
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

