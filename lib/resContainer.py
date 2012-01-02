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
import rcStatus
import resources as Res
import time
import rcExceptions as ex
from rcUtilities import qcall
from rcGlobalEnv import rcEnv
import socket

class Container(Res.Resource):
    """ in seconds
    """
    startup_timeout = 600
    shutdown_timeout = 60

    def __init__(self, name, rid=None, type=None, optional=False,
                 disabled=False, monitor=False, tags=set([])):
        Res.Resource.__init__(self, rid=rid, type=type,
                              optional=optional, disabled=disabled,
                              monitor=monitor, tags=tags)
        self.sshbin = '/usr/bin/ssh'
        self.name = name
        self.label = name

    def vmcmd(self, cmd, verbose=False, timeout=10):
        return self.svc.vmcmd(cmd, verbose, timeout, r=self)

    def getaddr(self):
        if hasattr(self, 'addr'):
            return
        try:
            a = socket.getaddrinfo(self.name, None)
            if len(a) == 0:
                raise Exception
            self.addr = a[0][4][0]
        except:
            if not disabled:
                raise ex.excInitError

    def __str__(self):
        return "%s name=%s" % (Res.Resource.__str__(self), self.name)

    def operational(self):
        if self.svc.guestos == "Windows":
            """ Windows has no sshd.
            """
            return True
        timeout = 1
        ret, out, err = self.vmcmd("pwd", timeout=timeout)
        if ret == 0:
            return True
        return False

    def wait_for_fn(self, fn, tmo, delay):
        for tick in range(tmo//2):
            if fn():
                return
            time.sleep(delay)
        self.log.error("Waited too long for startup")
        raise ex.excError

    def wait_for_startup(self):
        self.log.info("wait for container up status")
        self.wait_for_fn(self.is_up, self.startup_timeout, 2)
        if hasattr(self, 'ping'):
            self.log.info("wait for container ping")
            self.wait_for_fn(self.ping, self.startup_timeout, 2)
        self.log.info("wait for container operational")
        self.wait_for_fn(self.operational, self.startup_timeout, 2)

    def wait_for_shutdown(self):
        self.log.info("wait for container down status")
        for tick in range(self.shutdown_timeout):
            if self.is_down():
                return
            time.sleep(1)
        self.log.error("Waited too long for shutdown")
        raise ex.excError

    def install_drp_flag(self):
        print "TODO: install_drp_flag()"

    def start(self):
        try:
            self.getaddr()
        except:
            self.log.error("could not resolve %s to an ip address"%self.name)
            raise ex.excError
        if self.is_up():
            self.log.info("container %s already started" % self.name)
            return
        if rcEnv.nodename in self.svc.drpnodes:
            self.install_drp_flag()
        self.container_start()
        self.wait_for_startup()

    def stop(self):
        try:
            self.getaddr()
        except:
            self.log.error("could not resolve %s to an ip address"%self.name)
            raise ex.excError
        if self.is_down():
            self.log.info("container %s already stopped" % self.name)
            return
        self.container_stop()
        try:
            self.wait_for_shutdown()
        except ex.excError:
            self.container_forcestop()
            self.wait_for_shutdown()

    def check_capabilities(self):
        #print "TODO: check_capabilities(self)"
        pass

    def container_start(self):
        print "TODO: container_start(self)"

    def container_stop(self):
        print "TODO: container_stop(self)"

    def container_forcestop(self):
        print "TODO: container_forcestop(self)"

    def check_manual_boot(self):
        print "TODO: check_manual_boot(self)"
        return False

    def is_up(self):
        return False

    def is_down(self):
        return not self.is_up()

    def _status(self, verbose=False):
        try:
            self.getaddr()
        except:
            self.status_log("could not resolve %s to an ip address"%self.name)
            return rcStatus.WARN
        if not self.check_capabilities():
            self.status_log("node capabilities do not permit this action")
            return rcStatus.WARN
        if not self.check_manual_boot():
            self.status_log("container auto boot is on")
            return rcStatus.WARN
        if self.is_up():
            return rcStatus.UP
        if self.is_down():
            return rcStatus.DOWN
        else:
            self.status_log("container status is neither up nor down")
            return rcStatus.WARN

    def get_container_info(self):
        print "TODO: get_container_info(self)"
        return {'vcpus': '0', 'vmem': '0'}
