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

class svcHosted(svc.Svc):
    """Define hosted services
    """

    def __init__(self,optional=False,disabled=False):
        svc.Svc.__init__(self,"Hosted",optional, disabled)

    def action(self,action=None):
        print "Calling action %s on %s" % (action,self.__class__.__name__)
        if action == "start" : self.start()
        if action == "stop" : self.start()

    def start(self):
        """start a hosted service:
        check ping
        start ips
        start VGs
        start mounts
        start apps
        """
        print "starting %s" % self.__class__.__name__
        for ip in self.get_res_sets("ip"):   ip.action("check_ping")
        for ip in self.get_res_sets("ip"):   ip.action("start")
        for g in self.get_res_sets("dg"):    g.action("start")
        for m in self.get_res_sets("Mount"): m.action("start")
        for a in self.get_res_sets("app"):   a.action("start")

    def stop(self):
        """stop a hosted service:
        stop apps
        stop mounts
        stop VGs
        stop ips
        """
        print "stopping %s" % self.__class__.__name__
        for a in self.get_res_sets("app"):   a.action("start")
        for m in self.get_res_sets("Mount"): m.action("stop")
        for g in self.get_res_sets("dg"):    g.action("stop")
        for ip in self.get_res_sets("ip"):   ip.action("stop")

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

