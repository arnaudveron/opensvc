import os

import core.exceptions as ex
from utilities.converters import convert_size
from .. import BASE_KEYWORDS
from core.resource import Resource
from core.objects.svcdict import KEYS

KEYWORDS = BASE_KEYWORDS + [
    {
        "keyword": "size",
        "at": True,
        "required": True,
        "default": "100m",
        "convert": "size",
        "text": "The size of the loop file to provision.",
        "provisioning": True
    },
    {
        "keyword": "file",
        "protoname": "loopfile",
        "at": True,
        "required": True,
        "text": "The loopback device backing file full path."
    },
]
DEPRECATED_SECTIONS = {
    "loop": ["disk", "loop"],
}

KEYS.register_driver(
    "disk",
    "loop",
    name=__name__,
    keywords=KEYWORDS,
    deprecated_sections=DEPRECATED_SECTIONS,
)


class BaseDiskLoop(Resource):
    """
    Base loopback device resource
    """

    def __init__(self, loopfile=None, size=None, **kwargs):
        super(BaseDiskLoop, self).__init__(type="disk.loop", **kwargs)
        self.loopfile = loopfile
        self.size = size
        self.label = "loop %s" % loopfile

    def _info(self):
        return [["file", self.loopfile]]

    def __str__(self):
        return "%s loopfile=%s" % (super(BaseDiskLoop, self).__str__(), self.loopfile)

    def chown(self):
        if os.name != 'posix':
            return
        self.log.info("chown 0:0 %s", self.loopfile)
        os.chown(self.loopfile, 0, 0)

    def chmod(self):
        if os.name != 'posix':
            return
        self.log.info("chmod 600 %s", self.loopfile)
        os.chmod(self.loopfile, 0o0600)

    def provisioned(self):
        try:
            return os.path.exists(self.loopfile)
        except Exception:
            return False

    def unprovisioner(self):
        try:
            self.loopfile
        except Exception as e:
            raise ex.Error(str(e))

        if not self.provisioned():
            return

        self.log.info("unlink %s" % self.loopfile)
        os.unlink(self.loopfile)
        self.svc.node.unset_lazy("devtree")

    def provisioner(self):
        d = os.path.dirname(self.loopfile)
        try:
            if not os.path.exists(d):
                self.log.info("create directory %s"%d)
                os.makedirs(d)
            with open(self.loopfile, 'w') as f:
                self.log.info("create file %s, size %s"%(self.loopfile, self.size))
                f.seek(convert_size(self.size, _to='b', _round=512)-1)
                f.write('\0')
            self.chown()
            self.chmod()
        except Exception as e:
            raise ex.Error("failed to create %s: %s"% (self.loopfile, str(e)))
        self.svc.node.unset_lazy("devtree")
