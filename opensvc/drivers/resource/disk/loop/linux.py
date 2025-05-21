import os
import time

import core.exceptions as ex
import core.status
import utilities.devices.linux

from . import BaseDiskLoop
from env import Env
from utilities.cache import clear_cache
from utilities.lock import cmlock
from utilities.mounts.linux import Mounts
from utilities.files import getmount

DRIVER_GROUP = "disk"
DRIVER_BASENAME = "loop"

def driver_capabilities(node=None):
    from utilities.proc import which
    if which("losetup"):
        return ["disk.loop"]
    return []

class DiskLoop(BaseDiskLoop):
    def is_up(self):
        """
        Returns True if the loop group is present and activated
        """
        self.loop = utilities.devices.linux.file_to_loop(self.loopfile)
        if len(self.loop) == 0:
            return False
        return True

    def is_volatile(self):
        mnt = getmount(self.loopfile)
        mount = Mounts().mount("tmpfs", mnt)
        if mount and mount.type == "tmpfs":
            return True
        return False

    def auto_provision(self):
        """
        If the loop file is hosted on a volatile fs, auto provision on start.
        """
        if not self.is_volatile():
            return
        self.provisioner()

    def auto_unprovision(self):
        """
        If the loop file is hosted on a volatile fs, auto unprovision on stop.
        Free the memory asap.
        """
        if not self.is_volatile():
            return
        self.unprovisioner()

    def start(self):
        if self.is_up():
            self.log.info("%s is already up" % self.label)
            return
        if not os.path.exists(self.loopfile):
            self.auto_provision()
        lockfile = os.path.join(Env.paths.pathlock, "disk.loop")
        try:
            with cmlock(timeout=30, delay=1, lockfile=lockfile):
                cmd = [Env.syspaths.losetup, '-f', self.loopfile]
                ret, out, err = self.vcall(cmd)
                clear_cache("losetup.json")
        except Exception as exc:
            raise ex.Error(str(exc))
        if ret != 0:
            raise ex.Error
        self.loop = utilities.devices.linux.file_to_loop(self.loopfile)
        if len(self.loop) == 0:
            raise ex.Error("loop device did not appear or disappeared")
        time.sleep(2)
        self.log.info("%s now loops to %s" % (', '.join(self.loop), self.loopfile))
        self.can_rollback = True

    def stop(self):
        if not self.is_up():
            self.log.info("%s is already down" % self.label)
            return 0
        for loop in self.loop:
            cmd = [Env.syspaths.losetup, '-d', loop]
            ret, out, err = self.vcall(cmd)
            clear_cache("losetup.json")
            if ret != 0:
                raise ex.Error
        if os.path.exists(self.loopfile):
            self.auto_unprovision()

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
        self.loop = utilities.devices.linux.file_to_loop(self.loopfile)
        return set(self.loop)
