import os

import daemon.handler
from env import Env

class Handler(daemon.handler.BaseHandler):
    """
    Return the object logs back to <backlog> bytes.
    """
    routes = (
        ("GET", "node_backlogs"),
        (None, "node_backlogs"),
    )
    prototype = [
        {
            "name": "backlog",
            "required": False,
            "format": "size",
            "default": "10k",
            "desc": "The per-instance backlog size.",
        },
        {
            "name": "since",
            "required": False,
            "format": "string",
            "default": None,
            "desc": "The timestamp to limit result since (timestamp or datetime)",
        },
        {
            "name": "until",
            "required": False,
            "format": "string",
            "default": None,
            "desc": "The timestamp to limit result until (timestamp or datetime)",
        },
    ]

    def action(self, nodename, thr=None, stream_id=None, **kwargs):
        options = self.parse_options(kwargs)
        logfile = os.path.join(Env.paths.pathlog, "node.log")
        ofile = thr._action_logs_open(logfile, options.backlog, "node")
        return thr.read_file_lines(ofile, since=options.since, until=options.until)

