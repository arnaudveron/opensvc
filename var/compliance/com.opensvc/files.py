#!/usr/bin/env /opt/opensvc/bin/python

data = {
  "default_prefix": "OSVC_COMP_FILE_",
  "example_value": """ 
{
  "path": "/some/path/to/file",
  "fmt": "root@corp.com		%%HOSTNAME%%@corp.com",
  "uid": 500,
  "gid": 500,
}
  """,
  "description": """* Verify and install file content.
* Verify and set file or directory ownership and permission
* Directory mode is triggered if the path ends with /

Special wildcards::

  %%ENV:VARNAME%%	Any environment variable value
  %%HOSTNAME%%		Hostname
  %%SHORT_HOSTNAME%%	Short hostname

""",
  "form_definition": """
Desc: |
  A file rule, fed to the 'files' compliance object to create a directory or a file and set its ownership and permissions. For files, a reference content can be specified or pointed through an URL.
Css: comp48

Outputs:
  -
    Dest: compliance variable
    Class: file
    Type: json
    Format: dict

Inputs:
  -
    Id: path
    Label: Path
    DisplayModeLabel: path
    LabelCss: action16
    Mandatory: Yes
    Help: File path to install the reference content to. A path ending with '/' is treated as a directory and as such, its content need not be specified.
    Type: string

  -
    Id: mode
    Label: Permissions
    DisplayModeLabel: perm
    LabelCss: action16
    Help: "In octal form. Example: 644"
    Type: integer

  -
    Id: uid
    Label: Owner
    DisplayModeLabel: uid
    LabelCss: guy16
    Help: Either a user ID or a user name
    Type: string or integer

  -
    Id: gid
    Label: Owner group
    DisplayModeLabel: gid
    LabelCss: guy16
    Help: Either a group ID or a group name
    Type: string or integer

  -
    Id: ref
    Label: Content URL pointer
    DisplayModeLabel: ref
    LabelCss: loc
    Help: "Examples:
        http://server/path/to/reference_file
        https://server/path/to/reference_file
        ftp://server/path/to/reference_file
        ftp://login:pass@server/path/to/reference_file"
    Type: string

  -
    Id: fmt
    Label: Content
    DisplayModeLabel: fmt
    LabelCss: hd16
    Css: pre
    Help: A reference content for the file. The text can embed substitution variables specified with %%ENV:VAR%%.
    Type: text
"""
}

import os
import sys
import json
import stat
import re
import urllib
import ssl
import tempfile
import pwd
import grp
import codecs
from subprocess import *

sys.path.append(os.path.dirname(__file__))

from comp import *

class InitError(Exception):
    pass

class CompFiles(CompObject):
    def __init__(self, prefix=None):
        CompObject.__init__(self, prefix=prefix, data=data)

    def init(self):
        self._usr = {}
        self._grp = {}
        self.sysname, self.nodename, x, x, self.machine = os.uname()
        self.files = []

        for rule in self.get_rules():
            try:
                self.files += self.add_file(rule)
            except InitError:
                continue
            except ValueError:
                print >>sys.stderr, 'file: failed to parse variable', os.environ[k]

        if len(self.files) == 0:
            raise NotApplicable()

    def parse_fmt(self, d, add_linefeed=True):
        if isinstance(d['fmt'], int):
            d['fmt'] = str(d['fmt'])
        d['fmt'] = d['fmt'].replace('%%HOSTNAME%%', self.nodename)
        d['fmt'] = d['fmt'].replace('%%SHORT_HOSTNAME%%', self.nodename.split('.')[0])
        d['fmt'] = self.subst(d['fmt'])
        if add_linefeed and not d['fmt'].endswith('\n'):
            d['fmt'] += '\n'
        return [d]

    def parse_ref(self, d):
        f = tempfile.NamedTemporaryFile()
        tmpf = f.name
        f.close()
        try:
            self.urlretrieve(d['ref'], tmpf)
        except IOError as e:
            print >>sys.stderr, "file ref", d['ref'], "download failed:", e
            raise InitError()
        with open(tmpf, "r") as f:
            d['fmt'] = f.read()
        return self.parse_fmt(d, add_linefeed=False)

    def add_file(self, d):
        if 'path' not in d:
            print >>sys.stderr, 'file: path should be in the dict:', d
            RET = RET_ERR
            return []
        if 'fmt' not in d and 'ref' not in d and not d['path'].endswith("/"):
            print >>sys.stderr, 'file: fmt or ref should be in the dict:', d
            RET = RET_ERR
            return []
        if 'fmt' in d and 'ref' in d:
            print >>sys.stderr, 'file: fmt and ref are exclusive:', d
            RET = RET_ERR
            return []
        try:
            d["uid"] = int(d["uid"])
        except:
            pass
        try:
            d["gid"] = int(d["gid"])
        except:
            pass
        if 'fmt' in d:
            return self.parse_fmt(d)
        if 'ref' in d:
            if not d["ref"].startswith("safe://"):
                return self.parse_ref(d)
        return [d]

    def fixable(self):
        return RET_NA

    def check_file_fmt(self, f, verbose=False):
        if not os.path.exists(f['path']):
            return RET_ERR
        if f['path'].endswith('/'):
            # don't check content if it's a directory
            return RET_OK
        if 'ref' in f and f['ref'].startswith("safe://"):
            return self.check_file_fmt_safe(f, verbose=verbose)
        else:
            return self.check_file_fmt_buffered(f, verbose=verbose)

    def fix_file_fmt_safe(self, f):
        print "file reference %s download to %s" % (f["ref"], f["path"])
        tmpfname = self.get_safe_file(f["ref"])
        print "file %s content install" % f["path"]
        import shutil
        shutil.copy(tmpfname, f["path"])
        os.unlink(tmpfname)
        return RET_OK

    def check_file_fmt_safe(self, f, verbose=False):
        try:
            data = self.collector_safe_file_get_meta(f["ref"])
        except ComplianceError as e:
            raise ComplianceError(str(e))
        target_md5 = data.get("md5")
        current_md5 = self.md5(f["path"])
        if target_md5 == current_md5:
            print "file %s md5 verified" % f["path"]
            return RET_OK
        else:
            print >>sys.stderr, "file %s content md5 differs from its reference" % f["path"]
            if verbose and data["size"] < 1000000:
                tmpfname = self.get_safe_file(f["ref"])
                self.check_file_diff(f, tmpfname, verbose=verbose)
                os.unlink(tmpfname)
            return RET_ERR

    def get_safe_file(self, uuid):
        tmpf = tempfile.NamedTemporaryFile()
        tmpfname = tmpf.name
        tmpf.close()
        try:
            self.collector_safe_file_download(uuid, tmpfname)
        except Exception as e:
            raise ComplianceError("%s: %s" % (uuid, str(e)))
        return tmpfname

    def check_file_fmt_buffered(self, f, verbose=False):
        tmpf = tempfile.NamedTemporaryFile()
        tmpfname = tmpf.name
        tmpf.close()
        with codecs.open(tmpfname, 'w', encoding="utf8", errors="ignore") as tmpf:
            tmpf.write(f['fmt'])
        ret = self.check_file_diff(f, tmpfname, verbose=verbose)
        os.unlink(tmpfname)
        return ret

    def check_file_diff(self, f, refpath, verbose=False):
        if "OSVC_COMP_NODES_OS_NAME" in os.environ and os.environ['OSVC_COMP_NODES_OS_NAME'] in ("Linux"):
            cmd = ['diff', '-u', f['path'], refpath]
        else:
            cmd = ['diff', f['path'], refpath]
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if verbose and len(out) > 0:
            print >>sys.stderr, out.strip('\n')
        if p.returncode != 0:
            return RET_ERR
        return RET_OK

    def check_file_mode(self, f, verbose=False):
        if 'mode' not in f:
            return RET_OK
        try:
            mode = oct(stat.S_IMODE(os.stat(f['path']).st_mode))
        except:
            if verbose: print >>sys.stderr, "file", f['path'], 'stat() failed'
            return RET_ERR
        mode = str(mode).lstrip("0")
        if mode != str(f['mode']):
            if verbose: print >>sys.stderr, "file", f['path'], 'mode should be %s but is %s'%(f['mode'], mode)
            return RET_ERR
        return RET_OK

    def get_uid(self, uid):
        if uid in self._usr:
            return self._usr[uid]
        tuid = uid
        if isinstance(uid, (str, unicode)):
            try:
                info=pwd.getpwnam(uid)
                tuid = info[2]
                self._usr[uid] = tuid
            except:
                print >>sys.stderr, "file: user %s does not exist"%uid
                raise ComplianceError()
        return tuid

    def get_gid(self, gid):
        if gid in self._grp:
            return self._grp[gid]
        tgid = gid
        if isinstance(gid, (str, unicode)):
            try:
                info=grp.getgrnam(gid)
                tgid = info[2]
                self._grp[gid] = tgid
            except:
                print >>sys.stderr, "file: group %s does not exist"%gid
                raise ComplianceError()
        return tgid

    def check_file_uid(self, f, verbose=False):
        if 'uid' not in f:
            return RET_OK
        tuid = self.get_uid(f['uid'])
        uid = os.stat(f['path']).st_uid
        if uid != tuid:
            if verbose: print >>sys.stderr, "file", f['path'], 'uid should be %s but is %s'%(tuid, str(uid))
            return RET_ERR
        return RET_OK

    def check_file_gid(self, f, verbose=False):
        if 'gid' not in f:
            return RET_OK
        tgid = self.get_gid(f['gid'])
        gid = os.stat(f['path']).st_gid
        if gid != tgid:
            if verbose: print >>sys.stderr, "file", f['path'], 'gid should be %s but is %s'%(tgid, str(gid))
            return RET_ERR
        return RET_OK

    def check_file(self, f, verbose=False):
        if not os.path.exists(f['path']):
            print >>sys.stderr, "file", f['path'], "does not exist"
            return RET_ERR
        r = 0
        r |= self.check_file_fmt(f, verbose)
        r |= self.check_file_mode(f, verbose)
        r |= self.check_file_uid(f, verbose)
        r |= self.check_file_gid(f, verbose)
        if r == 0 and verbose:
            print "file", f['path'], "is ok"
        return r

    def fix_file_mode(self, f):
        if 'mode' not in f:
            return RET_OK
        if self.check_file_mode(f) == RET_OK:
            return RET_OK
        try:
            print "file %s mode set to %s"%(f['path'], str(f['mode']))
            os.chmod(f['path'], int(str(f['mode']), 8))
        except:
            return RET_ERR
        return RET_OK

    def fix_file_owner(self, f):
        uid = -1
        gid = -1

        if 'uid' not in f and 'gid' not in f:
            return RET_OK
        if 'uid' in f and self.check_file_uid(f) != RET_OK:
            uid = self.get_uid(f['uid'])
        if 'gid' in f and self.check_file_gid(f) != RET_OK:
            gid = self.get_gid(f['gid'])
        if uid == -1 and gid == -1:
            return RET_OK
        try:
            os.chown(f['path'], uid, gid)
        except:
            print >>sys.stderr, "file %s ownership set to %d:%d failed"%(f['path'], uid, gid)
            return RET_ERR
        print "file %s ownership set to %d:%d"%(f['path'], uid, gid)
        return RET_OK

    def fix_file_fmt(self, f):
        if f['path'].endswith("/") and not os.path.exists(f['path']):
            try:
                print "file: mkdir", f['path']
                os.makedirs(f['path'])
            except:
                print >>sys.stderr, "file: failed to create", f['path']
                return RET_ERR
            return RET_OK
        if self.check_file_fmt(f, verbose=False) == RET_OK:
            return RET_OK

        if 'ref' in f and f['ref'].startswith("safe://"):
            return self.fix_file_fmt_safe(f)

        d = os.path.dirname(f['path'])
        if not os.path.exists(d):
           print "file: mkdir", d
           os.makedirs(d)
           try:
               os.chown(d, f['uid'], f['gid'])
           except Exception as e:
               print >>sys.stderr, "file:", e
               pass
        try:
            with codecs.open(f['path'], 'w', encoding="utf8", errors="ignore") as fi:
                fi.write(f['fmt'])
        except Exception as e:
            print >>sys.stderr, "file:", e
            return RET_ERR
        print "file", f['path'], "rewritten"
        return RET_OK

    def check(self):
        r = 0
        for f in self.files:
            r |= self.check_file(f, verbose=True)
        return r

    def fix(self):
        r = 0
        for f in self.files:
            r |= self.fix_file_fmt(f)
            r |= self.fix_file_mode(f)
            r |= self.fix_file_owner(f)
        return r

if __name__ == "__main__":
    main(CompFiles)

