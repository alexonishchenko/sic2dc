import re

from sic2dc.src.schema import CfgCmprCure, CfgCmprSettings


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
          - enter: ' address-family \\S+\\s.*$'
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
        for attr in ['c1', 'c2']:
            config = getattr(self, attr)
            enter_exit_level = 0
            result_config_lines = list()
            for line in config.split('\n'):
                add_indent = str(enter_exit_level * (self.settings.indent_char * self.settings.indent))
                result_line = f"{add_indent}{line}"
                result_config_lines.append(result_line)
                for enter_exit in enter_exits:
                    if re.match(enter_exit['enter'], line):
                        enter_exit_level += 1
                    if re.match(enter_exit['exit'], line):
                        enter_exit_level -= 1
            setattr(self, attr, '\n'.join(result_config_lines))
