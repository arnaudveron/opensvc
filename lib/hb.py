"""
 Heartbeat parent class
"""
import logging
import time
import socket
import datetime
import fcntl
import struct

import osvcd_shared as shared
from rcGlobalEnv import rcEnv, Storage

class Hb(shared.OsvcThread):
    """
    Heartbeat parent class
    """
    default_hb_period = 5

    def __init__(self, name, role=None):
        shared.OsvcThread.__init__(self)
        self.name = name
        self.id = name + "." + role
        self.log = logging.getLogger(rcEnv.nodename+".osvcd."+self.id)
        self.peers = {}

    def status(self, **kwargs):
        data = shared.OsvcThread.status(self, **kwargs)
        data.peers = {}
        for nodename in self.cluster_nodes:
            if nodename == rcEnv.nodename:
                data.peers[nodename] = {}
                continue
            if "*" in self.peers:
                _data = self.peers["*"]
            else:
                _data = self.peers.get(nodename, Storage({
                    "last": 0,
                    "beating": False,
                    "success": True,
                }))
            data.peers[nodename] = {
                "last": datetime.datetime.utcfromtimestamp(_data.last)\
                                         .strftime('%Y-%m-%dT%H:%M:%SZ'),
                "beating": _data.beating,
            }
        return data

    def set_last(self, nodename="*", success=True):
        if nodename not in self.peers:
            self.peers[nodename] = Storage({
                "last": 0,
                "beating": False,
                "success": True,
            })
        if success:
            self.peers[nodename].last = time.time()
            if not self.peers[nodename].beating:
                self.log.info("node %s hb status stale => beating", nodename)
            self.peers[nodename].beating = True
        self.peers[nodename].success = success

    def get_last(self, nodename="*"):
        if nodename in self.peers:
            return self.peers[nodename]
        return Storage({
            "last": 0,
            "beating": False,
            "success": True,
        })

    def is_beating(self, nodename="*"):
        return self.peers.get(nodename, {"beating": False})["beating"]

    def set_peers_beating(self):
        for nodename in self.peers:
            self.set_beating(nodename)

    def set_beating(self, nodename="*"):
        now = time.time()
        if nodename not in self.peers:
            self.peers[nodename] = Storage({
                "last": 0,
                "beating": False,
                "success": True,
            })
        if now > self.peers[nodename].last + self.timeout:
            beating = False
        else:
            beating = True
        change = False
        if self.peers[nodename].beating != beating:
            change = True
            if beating:
                self.log.info("node %s hb status stale => beating", nodename)
            else:
                self.log.info("node %s hb status beating => stale", nodename)
        self.peers[nodename].beating = beating
        if not beating:
            self.forget_peer_data(nodename, change)

    @staticmethod
    def get_ip_address(ifname):
        try:
            ifname = bytes(ifname, "utf-8")
        except TypeError:
            ifname = str(ifname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )
        return socket.inet_ntoa(info[20:24])

    @staticmethod
    def get_message():
        with shared.HB_MSG_LOCK:
            if not shared.HB_MSG:
                # no data to send yet
                return None, 0
            return shared.HB_MSG, shared.HB_MSG_LEN

    def store_rx_data(self, data, nodename):
        node_status = data.get("monitor", {}).get("status")
        if node_status in ("init", "maintenance", "upgrade"):
            # preserve last service status
            bak = shared.CLUSTER_DATA[nodename].get("services", {}).get("status", {})
        else:
            bak = None
        with shared.CLUSTER_DATA_LOCK:
            shared.CLUSTER_DATA[nodename] = data
            if bak:
                self.duplog("info", "reconduct last known instances status from "
                            "node %(nodename)s in %(node_status)s state",
                            nodename=nodename, node_status=node_status)
                shared.CLUSTER_DATA[nodename]["services"]["status"] = bak

