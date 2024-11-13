# sic2dc
Simple indented config to dict compare.


# Summary
This is another configuration diff tool. It transforms indented configs into nested dictionaries, applies 'filters' to both dictionaries and then compares them. Applying filters helps skipping hidden/default lines or parts of the configuration which we are not interested in comparing.
Before transforing into dicts the configs can be cured (e.g. indentation may be added).
Also sic2dc can ignore "command" / "no command" in the same configuration section.


# Why
When comparing desired to operstate configurations one can face some difficulties that can be overcome by sic2dc.
 - desired state sections may be sorted in a way that doesn't match operstate but after applying it will give the same result.
 - device OS may sort sections in some odd way which is not always possible to replicate in desired state.
 - desired state config may have default lines which will be hidden in operstate configuration.
 - device OS can add lines to operstate config
 - device OS can alter incomming lines with unique values
 - desired state config may consist of multiple parts (e.g. arista configlets) which may override sections from each other
 - configuration syntax may need some treatment before comparison.


# Install

    pip install sic2dc

# Usage

## cli
```bash
# help
sic2dc  -h
usage: sic2dc [-h] -c1 -c2 -s [-f] [-c] [-g]

Simple indented config to dict compare.

options:
  -h, --help           show this help message and exit
  -c1, --config-1  relative path to the first config.
  -c2, --config-2  relative path to the second config.
  -s, --settings   relative path to settings yaml.
  -f, --filters    relative path to filters list yaml.
  -c, --cures      relative path to cures list yaml.
  -g, --no-color   disable color.
```

## cli example
```bash
sic2dc -c1 intended/sw1.cfg -c2 oper/sw1.cfg -s sic2dc/settings_arista_dcs.yml
```

```diff        
interface Port-Channel1
-   no shutdown
interface Ethernet1
+   no switchport
+ snmp-server engineID local 123
+ system l1
+   unsupported speed action error
+   unsupported error-correction action error
+ interface Ethernet3
+   shutdown
+   no switchport
- errdisable recovery interval 300
- router bfd
-   multihop interval 300 min-rx 300 multiplier 3
interface Port-Channel2
-   no shutdown
router bgp 66666
-   bgp default ipv4-unicast
```

The following options are required: c1, c2, settings. If no filters or cures are passed the configs are transformed and compared as they are. Filters and cures are yaml files with lists at the top level. Settings is a yaml with a dict.

## python
```python
from sic2dc import sic2dc
f1 = 'path_to_c1'
f2 = 'path_to_c2'
settings = {
    'indent_char': ' ',
    'indent': 3,
    'comments': ['^\s*[\!\#].*?$', '^\s*$'],
}

filters = []
cures = []

result = sic2dc(f1, f2, settings, filters=filters, cures=cures, color=True)

result['diff_dict']
result['diff_lines']
```        
## ansible filter
```python
"""filter_plugins file"""
from sic2dc import sic2dc
class FilterModule(object):
    def filters(self):
        return {'sic2dc': sic2dc}
```
```yaml
# playbook
# settings, filters and cures can be set as ansible vars of a host.
- set_fact:
    cfg_diff: "{{ f1 | sic2dc(f2, settings, filters, cures, False) }}"
- debug:
    msg: "{{ cfg_diff['diff_lines'] | join('\n') }}"
  when: cfg_diff['diff_dict']
- fail:
  when: cfg_diff['diff_dict']
```

# Concepts
## dicts
When a config is transformed into dict the lines of the config are trimmed and become dict keys.
```python
router bgp 1234    # spaces in the end of line
  router-id 1234
# transforms into
{'router bgp 1234': {'router-id 1234': {}}}
```

## path
Since we compare nested dicts **path** is used to define config parts of interest. Path is a list of regex patterns.
<br>path examples
```python
path = ['interface [Ee]thernet \S+'] # all ethernet interfaces
path = ['router bgp \d+', 'address-family .*'] # all address-families in 'router bgp' section. 
```
## whens
When applying filters **whens** are used to select more specific sections. Imagine we want to select all unused interfaces that exist in operstate and do not exist in desired state. So they should be 'shutdown' and they should be absent in destination.

```yaml
path: [^interface (Ethernet|Management).*]
when:
  - has_children: ['^shutdown$']
  - absent_in_destination: True
```
## examples
See [examples](https://github.com/alexonishchenko/sic2dc/tree/main/sic2dc/example) for filters/cures/settings examples

# Settings
Settings configure the following parameters (example for b4com switches).

```yaml
# enable/disable deleting of command/no command from both configs
ignore_cmd_nocmd: True

# indent char
indent_char: ' '

# number of indent_chars on single indentation level
indent: 1

# list of patterns for comment lines. they will be deleted from both configs.
comments:
  - '^\s*[\!\#].*?$'
  - '^\s*$'
  - '^\s*exit\s*$'
  - '^end\s*$'
```



# Filters
Filters mostly copy, delete or change sections in c1 and c2. A filter is defined by the following fileds:
 - **action** - str value e.g cp21, cp12, upd1, upd2, del1, del2
 - **when** - list of when conditions ('has_children', 'doesnt_have_chidren', 'absent_in_destination')
 - **path** - path to set config parts of interest.
 - **data** - dict of data used by filter (in udpate filters)


### cp21. Copy from c2 to c1
```yaml
# arista.desiredstate: copy unused interfaces from operstate
- action: cp21
  path: [^interface (Ethernet|Management).*]
  when:
    - has_children: ['^shutdown$']
    - absent_in_destination: True
```
### cp12. Copy from c1 to c2
Does the opposite.

### upd2. Update c2 with data
```yaml
# arista.operstate: add swprt mode access if swprt access vlan
#   in operstate config this is hidden
- action: upd2
  path: [^interface Eth.*]
  data:
    switchport mode access: {}
  when:
    - has_children: [switchport access vlan.*]
```
### upd1. Update c1 with data
Same as upd2

### del1. Delete section in c1
```yaml
# arista.desiredstate: delete errdisable default value
- action: del1
  path: [^errdisable recovery interval 300]
```

### del2. Delete section in c2
```yaml
# arista.operstate: delete snmp engine id
- action: del2
  path: ['snmp-server engineID .*']
```


# Cures
Cures are defined by **action** and its **kwargs**. They are applied to configs prior to dict transformation.
Currently the only cure supported is "enter_exit". It adds indentation by pattern.

## enter_exit
Find 'enter' pattern, add a single level of indentation to all following lines until 'exit' pattern is met.

```yaml
- action: enter_exit
  kwargs:
    enter_exits:
      - enter: ' address-family \S+\s.*$'
        exit: ' exit-address-family$'
```

The cure above transform example

        router bgp 1234
         address-family l2vpn evpn
         neighbor 10.10.10.7 activate
         neighbor 10.10.10.8 activate
         exit-address-family
        ->
        router bgp 1234
         address-family l2vpn evpn
          neighbor 10.10.10.7 activate
          neighbor 10.10.10.8 activate
          exit-address-family

# Api notes
## sic2dc

```python
def sic2dc(
        f1: str,
        f2: str,
        settings: dict,
        filters: list[dict] | None = None,
        cures: list[dict] | None = None,
        color: bool = False) -> dict:
    """
    Creates ConfigCompareBase object and compares f1 and f2.
    Returns ConfigCompareBase.diff_dict and ConfigCompareBase.dump() lines as dict
    Returns dict:
        'diff_dict': dict
        'diff_lines': str
    """
```

## ConfigCompareBase

```python
class ConfigCompareBase(...):
    def __init__(self, f1: str, f2: str, settings: CfgCmprSettings,
                 filters: list[dict] = None, cures: list[dict] = None):
        """
        1. Create cc object: read files, apply cures and create d1 and d2. 
        2. Apply filters to dicts
        3. Run comparison
        """

cc = ConfigCompareBase(...)

# uncured c1 and c2:
cc.c1_uncured
cc.c2_uncured

# cured c1 and c2
cc.c1
cc.c2

# unfiltered d1 and d2
cc.d1_unfiltered
cc.d2_unfiltered

# filtered d1 and d2
cc.d1
cc.d2

# dump
bw_diff_text = cc.dump(quiet=True, color=False)
color_diff_text = cc.dump(quiet=True, color=True)

# printout color diff
cc.dump(color=True)
```
