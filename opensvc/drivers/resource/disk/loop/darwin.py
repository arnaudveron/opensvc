import os

import core.exceptions as ex
import core.status
import utilities.devices.darwin

from . import BaseDiskLoop

DRIVER_GROUP = "disk"
DRIVER_BASENAME = "loop"

def driver_capabilities(node=None):
    from utilities.proc import which
    if which("hdiutil"):
        return ["disk.loop"]
    return []


class DiskLoop(BaseDiskLoop):
    def is_up(self):
        """Returns True if the loop group is present and activated
        """
        self.loop = utilities.devices.darwin.file_to_loop(self.loopfile)
        if len(self.loop) == 0:
            return False
        return True

    def start(self):
        if self.is_up():
            self.log.info("%s is already up" % self.loopfile)
            return
        cmd = ['hdiutil', 'attach', '-imagekey', 'diskimage-class=CRawDiskImage', '-nomount', self.loopfile]
        (ret, out, err) = self.call(cmd, info=True, outlog=False)
        if ret != 0:
            raise ex.Error
        self.loop = utilities.devices.darwin.file_to_loop(self.loopfile)
        self.log.info("%s now loops to %s" % (', '.join(self.loop), self.loopfile))
        self.can_rollback = True

    def stop(self):
        if not self.is_up():
            self.log.info("%s is already down" % self.loopfile)
            return 0
        for loop in self.loop:
            cmd = ['hdiutil', 'detach', loop.strip('md')]
            (ret, out, err) = self.vcall(cmd)
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
