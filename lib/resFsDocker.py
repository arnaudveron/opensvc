import os
import rcExceptions as ex
import resources
from rcGlobalEnv import rcEnv
from rcUtilities import lazy

class Fs(resources.Resource):
    def __init__(self,
                 rid=None,
                 driver=None,
                 options=None,
                 **kwargs):
        resources.Resource.__init__(self,
                                    rid=rid,
                                    type='fs.docker',
                                    **kwargs)
        self.driver = driver
        self.options = options

    @lazy
    def label(self):
        return "%s volume %s" % (self.driver, self.volname)

    def _info(self):
        data = [
          ["name", self.volname],
          ["driver", self.driver],
          ["options", self.options],
          ["vol_path", self.vol_path],
        ]
        return data

    @lazy
    def vol_path(self):
        return self.svc.dockerlib.docker_volume_inspect(self.volname).get("Mountpoint")

    def has_it(self):
        try:
            data = self.svc.dockerlib.docker_volume_inspect(self.volname)
            return True
        except (ValueError, IndexError):
            return False

    def is_up(self):
        """
        Returns True if the logical volume is present and activated
        """
        return self.has_it()

    @lazy
    def volname(self):
        return ".".join([self.svc.svcname, self.rid.replace("#", ".")])

    def create_vol(self):
        if self.has_it():
            return 0
        cmd = self.svc.dockerlib.docker_cmd + ["volume", "create", "--name", self.volname]
        if self.options:
            cmd += options
        ret, out, err = self.vcall(cmd)
        if ret != 0:
            raise ex.excError

    def start(self):
        self.create_vol()
        self.can_rollback = True

    def stop(self):
        pass
