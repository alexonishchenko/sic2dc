import logging

KEY_ADD = 'sic2dc_add'
KEY_DEL = 'sic2dc_del'


logger = logging.getLogger()


def dump_dict(
    d: dict, indent: int = 0, indent_str: str = ' ', color: bool = False, add_key: str = KEY_ADD, del_key: str = KEY_DEL
) -> list:
    result = list()
    color_end = '\033\u001b[0m' if color else ''
    color_del = '\u001b[31m' if color else ''
    result.extend([color_del + indent * indent_str + '- ' + l + color_end for l in d.get(del_key, dict())])
    color_add = '\u001b[32m' if color else ''
    result.extend([color_add + indent * indent_str + '+ ' + l + color_end for l in d.get(add_key, dict())])

    for k, v in d.items():
        if k in (add_key, del_key):
            continue
        result.append(indent * indent_str + k)
        result.extend(dump_dict(v, indent + 1, indent_str, color, add_key, del_key))

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

        result_dict = dict()

        for path, dif in self.diff_dict.items():
            current_dict = result_dict
            for p in path:
                if p not in current_dict:
                    current_dict[p] = {}
                current_dict = current_dict[p]
            pass
            current_dict[KEY_ADD] = dif.get('add', {})
            current_dict[KEY_DEL] = dif.get('del', {})

        result = dump_dict(result_dict, 0, self.settings.indent_char * self.settings.indent, color, KEY_ADD, KEY_DEL)

        if not quiet:
            print('\n'.join(result))
        return result
