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

from subprocess import *

import rcIfconfigLinux
from rcGlobalEnv import rcEnv
from rcUtilities import which
import os
import rcExceptions as ex

class ifconfig(rcIfconfigLinux.ifconfig):
    def __init__(self, svc):
        self.intf = []
        ret, out, err = svc.vmcmd("env LANG=C /sbin/ifconfig -a", r=svc)
        if ret != 0:
            raise ex.excError(err)
        self.parse(out)
