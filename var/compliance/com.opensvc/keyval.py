#!/usr/bin/env python

data = {
  "default_prefix": "OSVC_COMP_GROUP_",
  "example_kwargs": {
    "path": "/etc/ssh/sshd_config",
  },
  "example_value": """
{
  "keys": [
    {
      "key": "PermitRootLogin",
      "op": "=",
      "value": "yes"
    },
    {
      "key": "PermitRootLogin",
      "op": "reset",
      "value": ""
    }
  ]
}

""",
  "description": """* Setup and verify keys in "key value" formatted configuration file.
* Example files: sshd_config, ssh_config, ntp.conf, ...
""",
  "form_definition": """
Desc: |
  A rule to set a list of parameters in simple keyword/value configuration file format. Current values can be checked as set or unset, strictly equal, or superior/inferior to their target value. By default, this object appends keyword/values not found, potentially creating duplicates. The 'reset' operator can be used to avoid such duplicates.
Outputs:
  -
    Dest: compliance variable
    Type: json
    Format: list of dict
    Class: keyval
Inputs:
  -
    Id: key
    Label: Key
    DisplayModeTrim: 64
    DisplayModeLabel: key
    LabelCss: action16
    Mandatory: Yes
    Type: string
    Help:
  -
    Id: op
    Label: Comparison operator
    DisplayModeLabel: op
    LabelCss: action16
    Mandatory: Yes
    Type: string
    Default: "="
    Candidates:
      - reset
      - unset
      - "="
      - ">"
      - ">="
      - "<"
      - "<="
      - "IN"
    Help: The comparison operator to use to check the parameter current value. The 'reset' operator can be used to avoid duplicate occurence of the same keyword (insert a key reset after the last key set to mark any additional key found in the original file to be removed). The IN operator verifies the current value is one of the target list member. On fix, if the check is in error, it sets the first target list member. A "IN" operator value must be a JSON formatted list.
  -
    Id: value
    Label: Value
    DisplayModeLabel: value
    LabelCss: action16
    Mandatory: Yes
    Type: string or integer
    Help: The configuration file parameter target value.
""",
}


import os
import sys
import json

sys.path.append(os.path.dirname(__file__))

from comp import *
from keyval_parser import Parser, ParserError

class KeyVal(CompObject):
    def __init__(self, prefix=None, path=None, separator=" "):
        CompObject.__init__(self, prefix=prefix, data=data)
        self.cf = path
        self.separator = separator

    def init(self):
        self.nocf = False
        self.file_keys = {}

        if self.cf:
            self.file_keys[self.cf] = {
                "target_n_key": {},
                "keys": [],
            }

        for rule in self.get_rules():
            if self.cf and "key" in rule:
                self.file_keys[self.cf]["keys"] += [rule]
                continue
            if "path" not in rule:
                continue
            if "keys" not in rule or not isinstance(rule["keys"], list):
                continue
            path = rule["path"]
            separator = rule.get("separator", self.separator)
            if path not in self.file_keys:
                self.file_keys[path] = {
                    "separator": separator,
                    "target_n_key": {},
                    "keys": rule["keys"],
                }
            else:
                self.file_keys[path]["keys"] += rule["keys"]

        for path, data in self.file_keys.items():
            for i, key in enumerate(data["keys"]):
                if data["keys"][i]['op'] == 'IN':
                    data["keys"][i]['value'] = json.loads(data["keys"][i]['value'])
                if 'op' in key and 'key' in key and key['op'] not in ("unset", "reset"):
                    if key['key'] not in data["target_n_key"]:
                        data["target_n_key"][key['key']] = 1
                    else:
                        data["target_n_key"][key['key']] += 1
            try:
                data["conf"] = Parser(path, separator=data.get("separator", self.separator), obj=self)
            except ParserError as e:
                perror(e)
                raise ComplianceError()


    def fixable(self):
        return RET_OK

    def _check_key(self, path, data, keyname, target, op, value, instance=0, verbose=True):
        r = RET_OK
        if op == "reset":
            if value is not None:
                current_n_key = len(value)
                target_n_key = data["target_n_key"][keyname] if keyname in data["target_n_key"] else 0
                if current_n_key > target_n_key:
                    if verbose:
                        perror("%s: %s is set %d times, should be set %d times"%(path, keyname, current_n_key, target_n_key))
                    return RET_ERR
                else:
                    if verbose:
                        pinfo("%s: %s is set %d times, on target"%(path, keyname, current_n_key))
                    return RET_OK
            else:
                return RET_OK
        elif op == "unset":
            if value is not None:
                if is_string(target) and target.strip() == "":
                    if verbose:
                        perror("%s: %s is set, should not be"% (path, keyname))
                    return RET_ERR
                target_found = False
                for i, val in enumerate(value):
                    if target == val:
                        target_found = True
                        break

                if target_found:
                    if verbose:
                        perror("%s: %s[%d] is set to value %s, should not be"%(path, keyname, i, target))
                    return RET_ERR
                else:
                    if verbose:
                        pinfo("%s: %s is not set to value %s, on target"%(path, keyname, target))
                    return RET_OK
            else:
                if is_string(target) and target.strip() != "":
                    if verbose:
                        pinfo("%s: %s=%s is not set, on target"%(path, keyname, target))
                else:
                    if verbose:
                        pinfo("%s: %s is not set, on target"%(path, keyname))
                return RET_OK

        if value is None:
            if op == 'IN' and "unset" in map(str, target):
                if verbose:
                    pinfo("%s: %s is not set, on target"%(path, keyname))
                return RET_OK
            else:
                if verbose:
                    perror("%s: %s[%d] is not set, target: %s"%(path, keyname, instance, str(target)))
                return RET_ERR

        if type(value) == list:
            if str(target) in value:
                if verbose:
                    pinfo("%s: %s[%d]=%s on target"%(path, keyname, instance, str(value)))
                return RET_OK
            else:
                if verbose:
                    perror("%s: %s[%d]=%s is not set"%(path, keyname, instance, str(target)))
                return RET_ERR

        if op == '=':
            if str(value) != str(target):
                if verbose:
                    perror("%s: %s[%d]=%s, target: %s"%(path, keyname, instance, str(value), str(target)))
                r |= RET_ERR
            elif verbose:
                pinfo("%s: %s=%s on target"%(path, keyname, str(value)))
        elif op == 'IN':
            if str(value) not in map(str, target):
                if verbose:
                    perror("%s: %s[%d]=%s, target: %s"%(path, keyname, instance, str(value), str(target)))
                r |= RET_ERR
            elif verbose:
                pinfo("%s: %s=%s on target"%(path, keyname, str(value)))
        else:
            if type(value) != int:
                if verbose:
                    perror("%s: %s[%d]=%s value must be integer"%(path, keyname, instance, str(value)))
                r |= RET_ERR
            elif op == '<=' and value > target:
                if verbose:
                    perror("%s: %s[%d]=%s target: <= %s"%(path, keyname, instance, str(value), str(target)))
                r |= RET_ERR
            elif op == '>=' and value < target:
                if verbose:
                    perror("%s: %s[%d]=%s target: >= %s"%(path, keyname, instance, str(value), str(target)))
                r |= RET_ERR
            elif verbose:
                pinfo("%s: %s[%d]=%s on target"%(path, keyname, instance, str(value)))
        return r

    def check_key(self, path, data, key, instance=0, verbose=True):
        if 'key' not in key:
            if verbose:
                perror("'key' not set in rule %s"%str(key))
            return RET_NA
        if 'value' not in key:
            if verbose:
                perror("'value' not set in rule %s"%str(key))
            return RET_NA
        if 'op' not in key:
            op = "="
        else:
            op = key['op']
        target = key['value']

        allowed_ops = ('>=', '<=', '=', 'unset', 'reset', 'IN')
        if op not in allowed_ops:
            if verbose:
                perror(key['key'], "'op' value must be one of", ", ".join(allowed_ops))
            return RET_NA

        keyname = key['key']
        value = data["conf"].get(keyname, instance=instance)

        r = self._check_key(path, data, keyname, target, op, value, instance=instance, verbose=verbose)

        return r

    def fix_key(self, path, data, key, instance=0):
        if key['op'] == "unset" or (key['op'] == "IN" and key['value'][0] == "unset"):
            pinfo("%s: %s unset"%(path, key['key']))
            if key['op'] == "IN":
                target = None
            else:
                target = key['value']
            data["conf"].unset(key['key'], target)
        elif key['op'] == "reset":
            target_n_key = data["target_n_key"][key['key']] if key['key'] in data["target_n_key"] else 0
            pinfo("%s: %s truncated to %d definitions"%(path, key['key'], target_n_key))
            data["conf"].truncate(key['key'], target_n_key)
        else:
            if key['op'] == "IN":
                target = key['value'][0]
            else:
                target = key['value']
            pinfo("%s: %s=%s set"%(path, key['key'], target))
            data["conf"].set(key['key'], target, instance=instance)

    def check(self):
        r = RET_OK
        for path, data in self.file_keys.items():
            r |= self.check_keys(path, data)
        return r

    def check_keys(self, path, data):
        r = RET_OK
        key_instance = {}
        for key in data["keys"]:
            if 'key' not in key or 'op' not in key:
                continue
            if key['op'] in ('reset', 'unset'):
                instance = None
            else:
                if key['key'] not in key_instance:
                    key_instance[key['key']] = 0
                else:
                    key_instance[key['key']] += 1
                instance = key_instance[key['key']]
            r |= self.check_key(path, data, key, instance=instance, verbose=True)
        return r

    def fix(self):
        r = RET_OK
        for path, data in self.file_keys.items():
            r |= self.fix_keys(path, data)
        return r

    def fix_keys(self, path, data):
        key_instance = {}
        for key in data["keys"]:
            if 'key' not in key or 'op' not in key:
                continue
            if key['op'] in ('reset', 'unset'):
                instance = None
            else:
                if key['key'] not in key_instance:
                    key_instance[key['key']] = 0
                else:
                    key_instance[key['key']] += 1
                instance = key_instance[key['key']]
            if self.check_key(path, data, key, instance=instance, verbose=False) == RET_ERR:
                self.fix_key(path, data, key, instance=instance)
        if not data["conf"].changed:
            return RET_OK
        try:
            data["conf"].write()
        except ParserError as e:
            perror(e)
            return RET_ERR
        return RET_OK

if __name__ == "__main__":
    main(KeyVal)
