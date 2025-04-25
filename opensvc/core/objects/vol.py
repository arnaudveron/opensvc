import core.status

from core.objects.svc import Svc
from utilities.lazy import lazy
from utilities.naming import split_path, factory

class Vol(Svc):
    kind = "vol"

    def users(self, exclude=None):
        exclude = exclude or []
        users = []

        # purge lazies that may have changed due to claims
        # that occured in the lifespan of this object
        self.unset_lazy("cd")
        self.unset_lazy("children")

        for child in self.children:
            if child in exclude:
                continue
            name, namespace, kind = split_path(child)
            obj = factory(kind)(name=name, namespace=self.namespace, volatile=True, node=self.node)
            for res in obj.get_resources("volume"):
                if res.name != self.name:
                    continue
                if res.status() in (core.status.UP, core.status.STDBY_UP, core.status.WARN):
                    users.append(child)
        return users

    @lazy
    def devices_from(self):
        return self.oget("DEFAULT", "devices_from")

    def devices(self):
        devs = set()
        if not self.devices_from:
            dev = self.device()
            if dev is None:
                return set()
            return set([dev])
        for rid in self.devices_from:
            r = self.get_resource(rid)
            if r:
                try:
                    devs |= r.exposed_devs()
                except AttributeError:
                    continue
        return devs

