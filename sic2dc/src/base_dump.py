import logging
import re

from sic2dc.src.schema import KEY_ADD, KEY_DEL

logger = logging.getLogger()


MAP_COLOR = {
    True: {
        KEY_ADD: '\u001b[32m+ ',
        KEY_DEL: '\u001b[31m- ',
    },
    False: {
        KEY_ADD: '+ ',
        KEY_DEL: '- ',
    },
}


def dump_dict(d: dict, indent: int = 0, indent_str: str = ' ', color: bool = False) -> list:
    result = list()

    for k, v in d.items():
        line = k
        color_end = '\033\u001b[0m' if color else ''
        for key in [KEY_ADD, KEY_DEL]:
            line = re.sub(f'^{key}', MAP_COLOR[color][key], line) + color_end
        result.append(indent * indent_str + line)
        if v:
            result.extend(dump_dict(v, indent + 1, indent_str, color))

    return result


class DumpMixin:
    diff_dict: dict

    def dump(self, quiet: bool = True, color: bool = False):
        """
        Dump diff in text form.
        """
        result = dump_dict(self.diff_dict, 0, self.settings.indent_char * self.settings.indent, color)

        if not quiet:
            print('\n'.join(result))
        return result
