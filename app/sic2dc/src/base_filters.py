from copy import deepcopy

from sic2dc.src.schema import CfgCmprFilter, When

from sic2dc.src.tools import get_subdict_by_path, paths_by_path_ptrns


def _apply_whens(path_patterns: list[str], whens: list[When] = None, d1: dict = None, d2: dict = None) -> list[str]:
    """
    Actually main filters logic.
    Returns all paths filtered by 'path_patterns' and then all 'whens' are applied.
    """
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


class FiltersMixin:
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
