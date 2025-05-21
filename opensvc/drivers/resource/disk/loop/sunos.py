import os
import time

import core.exceptions as ex
import core.status
import utilities.devices.sunos

from . import BaseDiskLoop
from utilities.lock import cmlock
from env import Env

DRIVER_GROUP = "disk"
DRIVER_BASENAME = "loop"

def driver_capabilities(node=None):
    from utilities.proc import which
    if which("lofiadm"):
        return ["disk.loop"]
    return []


class DiskLoop(BaseDiskLoop):
    def is_up(self):
        """Returns True if the loop group is present and activated
        """
        self.loop = utilities.devices.sunos.file_to_loop(self.loopfile)
        if len(self.loop) == 0:
            return False
        return True

    def start(self):
        lockfile = os.path.join(Env.paths.pathlock, "disk.loop")
        if self.is_up():
            self.log.info("%s is already up" % self.label)
            return
        try:
            with cmlock(timeout=30, delay=1, lockfile=lockfile):
                cmd = ['lofiadm', '-a', self.loopfile]
                ret, out, err = self.vcall(cmd)
        except Exception as exc:
            raise ex.Error(str(exc))
        if ret != 0:
            raise ex.Error
        self.loop = utilities.devices.sunos.file_to_loop(self.loopfile)
        if len(self.loop) == 0:
            raise ex.Error("loop device did not appear or disappeared")
        time.sleep(1)
        self.log.info("%s now loops to %s" % (self.loop, self.loopfile))
        self.can_rollback = True

    def stop(self):
        if not self.is_up():
            self.log.info("%s is already down" % self.label)
            return 0
        for loop in self.loop:
            cmd = ['lofiadm', '-d', loop]
            ret, out, err = self.vcall(cmd)
            if ret != 0:
                raise ex.Error

    def _status(self, verbose=False):
        r = self.svc.resource_handling_file(self.loopfile)
        if self.is_provisioned() and not os.path.exists(self.loopfile):
            if r is None or (r and r.status() in (core.status.UP, core.status.STDBY_UP)):
                self.status_log("%s does not exist" % self.loopfile)
        if self.is_up():
            return core.status.UP
        else:
            return core.status.DOWN

    def exposed_devs(self):
        self.loop = utilities.devices.sunos.file_to_loop(self.loopfile)
        return set(self.loop)
