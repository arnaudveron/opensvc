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

import svc

class SvcHosted(svc.Svc):
    """Define hosted services
    """

    def __init__(self, svcname, optional=False, disabled=False):
        svc.Svc.__init__(self, svcname, "Hosted", optional, disabled)
        self.status_types = ["disk.loop", "fs", "disk.vg", "disk.zpool", "ip"]

    def start(self):
        """start a hosted service:
        start ips
        start loops
        start VGs
        start Pools
        start fs
        start apps
        """
        self.sub_set_action("ip", "start")
        self.sub_set_action("disk.loop", "start")
        self.sub_set_action("disk.vg", "start")
        self.sub_set_action("disk.zpool", "start")
        self.sub_set_action("fs", "start")
        self.sub_set_action("app", "start")

    def stop(self):
        """stop a hosted service:
        stop apps
        stop fs
        stop VGs
        stop ips
        """
        self.sub_set_action("app", "stop")
        self.sub_set_action("fs", "stop")
        self.sub_set_action("disk.vg", "stop")
        self.sub_set_action("disk.zpool", "stop")
        self.sub_set_action("disk.loop", "stop")
        self.sub_set_action("ip", "stop")

    def diskstart(self):
        """start a hosted service:
        start loops
        start VGs
        start Pools
        start fs
        """
        self.sub_set_action("disk.loop", "start")
        self.sub_set_action("disk.vg", "start")
        self.sub_set_action("disk.zpool", "start")
        self.sub_set_action("fs", "start")

    def diskstop(self):
        """stop a hosted service:
        stop apps
        stop fs
        stop VGs
        stop Pools
        stop ips
        """
        self.sub_set_action("fs", "stop")
        self.sub_set_action("disk.vg", "stop")
        self.sub_set_action("disk.zpool", "stop")
        self.sub_set_action("disk.loop", "stop")

    def startip(self):
        self.sub_set_action("ip", "start")

    def stopip(self):
        self.sub_set_action("ip", "stop")

    def startloop(self):
        self.sub_set_action("disk.loop", "start")

    def stoploop(self):
        self.sub_set_action("disk.loop", "stop")

    def startvg(self):
        self.sub_set_action("disk.vg", "start")

    def stopvg(self):
        self.sub_set_action("disk.vg", "stop")

    def startpool(self):
        self.sub_set_action("disk.zpool", "start")

    def stoppool(self):
        self.sub_set_action("disk.zpool", "stop")

    def mount(self):
        self.sub_set_action("fs", "start")

    def umount(self):
        self.sub_set_action("fs", "stop")

if __name__ == "__main__":
    for c in (SvcHosted,) :
        help(c)
    import mountSunOS as mount
    import ipSunOS as ip
    print """
    S=SvcHosted()
    S+=mount.Mount("/mnt1","/dev/sda")
    S+=mount.Mount("/mnt2","/dev/sdb")
    S+=ip.Ip("eth0","192.168.0.173")
    S+=ip.Ip("eth0","192.168.0.174")
    """

    S=SvcSone()
    S+=mount.Mount("/mnt1","/dev/sda")
    S+=mount.Mount("/mnt2","/dev/sdb")
    S+=ip.Ip("eth0","192.168.0.173")
    S+=ip.Ip("eth0","192.168.0.174")

    print "Show S: ", S
    print "start S:"
    S.start()

    print "stop S:"
    S.stop()

