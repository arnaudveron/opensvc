#
# Copyright (c) 2009 Christophe Varoqui <christophe.varoqui@free.fr>'
# Copyright (c) 2009 Cyril Galibern <cyril.galibern@free.fr>'
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# To change this template, choose Tools | Templates
# and open the template in the editor.
"""Module providing ZFS resources
"""

from rcGlobalEnv import rcEnv
import resDg
from rcUtilities import qcall

import re

class Pool(resDg.Dg):
    """ basic pool resource
    """
    def __init__(self, rid=None, name=None, type=None,
                 optional=False, disabled=False):
        self.label = 'pool ' + name
        resDg.Dg.__init__(self, rid=rid, name=name,
                          type='disk.zpool',
                          optional=optional, disabled=disabled)

    def has_it(self):
        """Returns True if the pool is present
        """
        ret = qcall( [ 'zpool', 'list', self.name ] )
        if ret == 0 :
            return True
        return False

    def is_up(self):
        """Returns True if the pool is present and activated
        """
        if not self.has_it():
            return False
        cmd = [ 'zpool', 'list', '-H', '-o', 'health', self.name ]
        (ret, out) = self.call(cmd)
        if out.strip() == "ONLINE" :
            return True
        return False

    def do_start(self):
        if self.is_up():
            self.log.info("%s is already up" % self.name)
            return 0
        cmd = [ 'zpool', 'import', self.name ]
        (ret, out) = self.vcall(cmd)
        return ret

    def do_stop(self):
        if not self.is_up():
            self.log.info("%s is already down" % self.name)
            return 0
        cmd = [ 'zpool', 'export', self.name ]
        (ret, out) = self.vcall(cmd)
        return ret

    def disklist(self):
        """disklist() search zpool vdevs from
        output of : zpool status poolname if status cmd == 0
        else
        output of : zpool import output if status cmd == 0

        disklist(self) update self.disks[]
        """
        if len(self.disks) > 0 :
            return self.disks

        disks = set()
        cmd = [ 'zpool', 'status', self.name ]
        (ret, out) = self.call(cmd, errlog=False)
        if ret != 0 :
            matchedPool=False
            cmd = [ 'zpool', 'import' ]
            (ret, out) = self.call(cmd)
            if ret != 0 :
                return []
            for line in out.split('\n'):
                if re.match('^  pool: ', line) is not None:
                    # This is pool: xxxx
                    # set watchNext if it is serached pool
                    # else disable watchNext
                    if line == '  pool: ' + self.name :
                        if matchedPool == True :
                            raise Exception("duplicated pools available")
                        matchedPool = True
                        watchNext = True
                    else :
                        watchNext = False
                elif watchNext == True :
                    # only look for 'tab  c*d vdev entries
                    if re.match('^\t  ', line) is not None:
                        if re.match('^\t  mirror', line) is not None:
                            continue
                        if re.match('^\t  raid', line) is not None:
                            continue
                        disk = line.split()[0]
                        disks.add("/dev/rdsk/" + disk )
        else :
            for line in out.split('\n'):
                if re.match('^\t  ', line) is not None:
                    if re.match('^\t  mirror', line) is not None:
                        continue
                    if re.match('^\t  raid', line) is not None:
                        continue
                    # vdev entry
                    disk=line.split()[0]
                    if re.match("^.*", disk) is not None :
                        disks.add("/dev/rdsk/" + disk )
        self.log.debug("found disks %s held by pool %s" % (disks, self.name))
        self.disks = disks

        return disks

if __name__ == "__main__":
    for c in (Pool,) :
        help(c)

    print """p=Pool("svczfs1")"""
    p=Pool("svczfs1")
    print "show p", p
    print """p.do_action("start")"""
    p.do_action("start")
    print """p.do_action("stop")"""
    p.do_action("stop")
