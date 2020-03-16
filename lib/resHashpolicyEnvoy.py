from resData import Data

def adder(svc, s):
    kwargs = {"rid": s}
    kwargs.update(svc.section_kwargs(s, "envoy"))
    r = Hashpolicy(**kwargs)
    svc += r

class Hashpolicy(Data):
    def __init__(self, rid, **kwargs):
        Data.__init__(self, rid, type="hash_policy.envoy", **kwargs)
        self.label = "envoy hash policy"

