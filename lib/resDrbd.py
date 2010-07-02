#
# Copyright (c) 2010 Christophe Varoqui <christophe.varoqui@free.fr>'
# Copyright (c) 2010 Cyril Galibern <cyril.galibern@free.fr>'
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

import os
import resources as Res
import rcStatus
import rcExceptions as ex
from rcUtilities import which

class Drbd(Res.Resource):
    """ Drbd device resource

        The tricky part is that drbd devices can be used as PV
        and LV can be used as drbd base devices. Treat the ordering
        with 'prevg' and 'postvg' tags.

        Start 'ups' and promotes the drbd devices to primary.
        Stop 'downs' the drbd devices.
    """
    def __init__(self, rid=None, res=None, always_on=set([]),
                 optional=False, disabled=False, tags=set([])):
        Res.Resource.__init__(self, rid, "disk.drbd",
                              optional=optional, disabled=disabled, tags=tags)
        self.res = res
        self.label = res
        self.drbdadm = None
        self.always_on = always_on

    def __str__(self):
        return "%s resource=%s" % (Res.Resource.__str__(self),\
                                 self.loopFile)

    def files_to_sync(self):
        cf = os.path.join(os.sep, 'etc', 'drbd.d', self.res+'.res')
        if os.path.exists(cf):
            return [cf]
        self.log.error("%s does not exist"%cf)
        return []

    def drbdadm_cmd(self, cmd):
        if self.drbdadm is None:
            if which('drbdadm'):
                self.drbdadm = 'drbdadm'
            else:
                self.log("drbdadm command not found")
                raise exc.excError
        return [self.drbdadm, cmd, self.res]

    def disklist(self):
        print "TODO: %s:disklist"%__file__

    def drbdadm_down(self):
        (ret, out) = self.vcall(self.drbdadm_cmd('down'))
        if ret != 0:
            raise ex.excError

    def drbdadm_up(self):
        (ret, out) = self.vcall(self.drbdadm_cmd('up'))
        if ret != 0:
            raise ex.excError

    def get_cstate(self):
        (ret, out) = self.call(self.drbdadm_cmd('cstate'))
        if ret != 0:
            raise ex.excError
        return out.strip()

    def start_connection(self):
        cstate = self.get_cstate()
        if cstate == "Connected":
            self.log.info("drbd resource %s is already up"%self.res)
        elif cstate == "StandAlone":
            self.drbdadm_down()
            self.drbdadm_up()
        elif cstate == "WFConnection":
            self.log.info("drbd resource %s peer node is not listening"%self.res)
            pass
        else:
            self.drbdadm_up()

    def get_roles(self):
        (ret, out) = self.call(self.drbdadm_cmd('role'))
        if ret != 0:
            raise ex.excError
        out = out.strip().split('/')
        if len(out) != 2:
            raise ex.excError
        return out

    def start_role(self, role):
        roles = self.get_roles()
        if roles[0] != role:
            self.vcall(self.drbdadm_cmd(role.lower()))
        else:
            self.log.info("drbd resource %s is already %s"%(self.res, role))

    def startstandby(self):
        self.start_connection()
        roles = self.get_roles()
        if roles[0] == "Primary":
            return
        self.start_role('Secondary')

    def stopstandby(self):
        self.start_connection()
        roles = self.get_roles()
        if roles[0] == "Secondary":
            return
        self.start_role('Secondary')

    def start(self):
        self.start_connection()
        self.start_role('Primary')

    def stop(self):
        self.drbdadm_down()

    def _status(self, verbose=False):
        (ret, out) = self.call(self.drbdadm_cmd('dstate'))
        if ret != 0:
            self.status_log("drbdadm dstate %s failed"%self.res)
            return rcStatus.WARN
        out = out.strip()
        if out == "UpToDate/UpToDate":
            return self.status_stdby(rcStatus.UP)
        elif out == "Unconfigured":
            return self.status_stdby(rcStatus.DOWN)
        self.status_log("unexpected drbd resource %s state: %s"%(self.res, out))
        return rcStatus.WARN

if __name__ == "__main__":
    help(Drbd)
    v = Drbd(res='test')
    print v

