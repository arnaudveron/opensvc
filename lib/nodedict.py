import sys
from rcGlobalEnv import rcEnv
from keywords import Keyword, KeywordStore

# deprecated => supported
DEPRECATED_KEYWORDS = {
    "node.host_mode": "env",
}

# supported => deprecated
REVERSE_DEPRECATED_KEYWORDS = {
    "node.env": "host_mode"
}

DEPRECATED_SECTIONS = {
}

BASE_SECTIONS = [
    "node",
    "cluster",
    "compliance",
    "stats",
    "checks",
    "packages",
    "patches",
    "asset",
    "nsr",
    "dcs",
    "hds",
    "necism",
    "eva",
    "ibmsvc",
    "vioserver",
    "brocade",
    "disks",
    "sym",
    "rotate_root_pw",
    "listener",
    "syslog",
    "stats_collection",
    "reboot",
    "cluster",
]

class KeywordNodeEnv(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="env",
                  order=15,
                  default="TST",
                  candidates=rcEnv.allowed_svc_envs,
                  text="A non-PRD service can not be brought up on a PRD node, but a PRD service can be startup on a non-PRD node (in a DRP situation)."
                )

class KeywordNodeMaxParallel(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="max_parallel",
                  order=15,
                  default=10,
                  convert="integer",
                  text="Allow a maximum of <max_parallel> subprocesses to run simultaneously on 'svcmgr --parallel <action>' commands."
                )

class KeywordNodeLocCountry(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_country",
                  order=15,
                  example="fr",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeLocCity(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_city",
                  order=15,
                  example="Paris",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeLocZip(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_zip",
                  order=15,
                  example="75017",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeLocAddr(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_addr",
                  order=15,
                  example="7 rue blanche",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeLocBuilding(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_building",
                  order=15,
                  example="Crystal",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeLocFloor(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_floor",
                  order=15,
                  example="21",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeLocRoom(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_room",
                  order=15,
                  example="102",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeLocRack(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="loc_rack",
                  order=15,
                  example="R42",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeTeamInteg(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="team_integ",
                  order=15,
                  example="TINT",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeTeamSupport(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="team_support",
                  order=15,
                  example="TSUP",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeAssetEnv(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="asset_env",
                  order=15,
                  example="Production",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeConnectTo(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="connect_to",
                  order=15,
                  example="1.2.3.4",
                  default_text="On GCE instances, defaults to the instance ip address.",
                  text="An asset information to push to the collector on pushasset, overriding the currently stored value."
                )

class KeywordNodeDbopensvc(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="dbopensvc",
                  order=15,
                  example="https://collector.opensvc.com",
                  text="Set the uri of the collector main xmlrpc server. The path part of the uri can be left unspecified. If not set, the agent does not try to communicate with a collector."
                )

class KeywordNodeDbcompliance(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="dbcompliance",
                  order=15,
                  example="https://collector.opensvc.com/init/compliance/call/xmlrpc",
                  default_text="Same protocol, server and port as dbopensvc, but with an different path.",
                  text="Set the uri of the collectors' main xmlrpc server. The path part of the uri can be left unspecified."
                )

class KeywordNodeBranch(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="branch",
                  order=15,
                  example="1.9",
                  text="Set the targeted opensvc agent branch. The downloaded upgrades will honor that branch. If not set, the repopkg imposes the target branch, which is not recommended with a public repopkg."
                )

class KeywordNodeRepo(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="repo",
                  order=15,
                  example="http://opensvc.repo.corp",
                  text="""Set the uri of the opensvc agent package repository and compliance modules gzipped tarball repository. This parameter is used by the 'nodemgr updatepkg' and 'nodemgr updatecomp' commands.

Expected repository structure::

	ROOT
	+- compliance
	 +- compliance-100.tar.gz
	 +- compliance-101.tar.gz
	 +- current -> compliance-101.tar.gz
	+- packages
	 +- deb
	 +- depot
	 +- pkg
	 +- sunos-pkg
	 +- rpms
	  +- current -> 1.9/current
	  +- 1.9
	   +- current -> opensvc-1.9-50.rpm
	   +- opensvc-1.9-49.rpm
	   +- opensvc-1.9-50.rpm
	 +- tbz

"""
                )

class KeywordNodeRepopkg(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="repopkg",
                  order=15,
                  example="http://repo.opensvc.com",
                  text="""Set the uri of the opensvc agent package repository. This parameter is used by the 'nodemgr updatepkg' command.

Expected repository structure::

	ROOT
	+- deb
	+- depot
	+- pkg
	+- sunos-pkg
	+- rpms
	 +- current -> 1.9/current
	 +- 1.9
	  +- current -> opensvc-1.9-50.rpm
	  +- opensvc-1.9-49.rpm
	  +- opensvc-1.9-50.rpm
	+- tbz

"""
                )

class KeywordNodeRepocomp(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="repocomp",
                  order=15,
                  example="http://compliance.repo.corp",
                  text="""Set the uri of the opensvc compliance modules gzipped tarball repository. This parameter is used by the 'nodemgr updatecomp' command.

Expected repository structure::

	ROOT
	+- compliance-100.tar.gz
	+- compliance-101.tar.gz
	+- current -> compliance-101.tar.gz

"""
                )

class KeywordNodeRuser(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="ruser",
                  order=15,
                  example="root opensvc@node1",
                  text="""Set the remote user to use to login to a remote node with ssh and rsync. The remote user must have the privileges to run as root the following commands on the remote node:

* nodemgr
* svcmgr
* rsync

The default ruser is root for all nodes. ruser accepts a list of user[@node] ... If @node is ommited, user is considered the new default user.
"""
                )

class KeywordNodeMaintenanceGracePeriod(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="maintenance_grace_period",
                  convert="duration",
                  order=15,
                  default="60s",
                  text="A duration expression, like 1h30m, defining how long the daemon retains a remote in-maintenance node data. As long as the remote node data are retained, the local daemon won't opt-in to takeover its running instances. This parameter should be adjusted to span the node reboot time, so the services have a chance to be restarted on the same node if their placement was optimal."
                )

class KeywordNodeRejoinGracePeriod(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="rejoin_grace_period",
                  convert="duration",
                  order=15,
                  default="90s",
                  text="A duration expression, like 90m, defining how long the daemon restrains from taking start decisions if no heartbeat has been received from a peer since daemon startup."
                )

class KeywordNodeReadyPeriod(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="node",
                  keyword="ready_period",
                  convert="duration",
                  order=15,
                  default="16s",
                  text="A duration expression, like 10s, defining how long the daemon monitor waits before starting a service instance in ready state. A peer node can preempt the start during this period. The default is 16s. Usually set to allow at least a couple of heartbeats to be received."
                )

class KeywordComplianceSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="compliance",
                  keyword="schedule",
                  order=15,
                  default="02:00-06:00@241 sun",
                  text="Schedule parameter for the 'compliance auto' node action, which check all modules and fix only modules flagged 'autofix'."
                )

class KeywordComplianceAutoUpdate(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="compliance",
                  keyword="auto_update",
                  convert="boolean",
                  order=15,
                  default=False,
                  text="If set to True, and if the execution context indicates a scheduled run, execute 'updatecomp' upon 'compliance check'. This toggle helps keep the compliance modules in sync with the reference repository. Beware of the security impact of this setting: you must be careful your module repository is kept secure."
                )

class KeywordStatsSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="stats",
                  keyword="schedule",
                  order=15,
                  default="00:00-06:00@361 mon-sun",
                  text="Schedule parameter for the 'pushstats' node action."
                )

class KeywordStatsDisable(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="stats",
                  keyword="disable",
                  convert="list",
                  order=15,
                  example="blockdev, mem_u",
                  text="Disable push for a stats group (mem_u, cpu, proc, swap, netdev, netdev_err, block, blockdev, fs_u)."
                )

class KeywordChecksSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="checks",
                  keyword="schedule",
                  order=15,
                  default="00:00-06:00@361 mon-sun",
                  text="Schedule parameter for the 'pushchecks' node action."
                )

class KeywordPackagesSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="packages",
                  keyword="schedule",
                  order=15,
                  default="00:00-06:00@361 mon-sun",
                  text="Schedule parameter for the 'pushpkg' node action."
                )

class KeywordPatchesSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="patches",
                  keyword="schedule",
                  order=15,
                  default="00:00-06:00@361 mon-sun",
                  text="Schedule parameter for the 'pushpatch' node action."
                )

class KeywordAssetSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="asset",
                  keyword="schedule",
                  order=15,
                  default="00:00-06:00@361 mon-sun",
                  text="Schedule parameter for the 'pushasset' node action."
                )

class KeywordNsrSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="nsr",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushnsr' node action."
                )

class KeywordDcsSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="dcs",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushdcs' node action."
                )

class KeywordHdsSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hds",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushhds' node action."
                )

class KeywordNecismSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="necism",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushnecism' node action."
                )

class KeywordEvaSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="eva",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pusheva' node action."
                )

class KeywordIbmsvcSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="ibmsvc",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushibmsvc' node action."
                )

class KeywordVioserverSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="vioserver",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushvioserver' node action."
                )

class KeywordBrocadeSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="brocade",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushbrocade' node action."
                )

class KeywordDisksSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="disks",
                  keyword="schedule",
                  order=15,
                  default="00:00-06:00@361 mon-sun",
                  text="Schedule parameter for the 'pushdisks' node action."
                )

class KeywordSymSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="sym",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'pushsym' node action."
                )

class KeywordRotateRootPwSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="rotate_root_pw",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'rotate root pw' node action."
                )

class KeywordStatsCollectionSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="stats_collection",
                  keyword="schedule",
                  order=15,
                  default="@10",
                  text="Schedule parameter for the 'collect stats' node action."
                )

class KeywordRebootSchedule(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="reboot",
                  keyword="schedule",
                  order=15,
                  text="Schedule parameter for the 'auto reboot' node action."
                )

class KeywordRebootOnce(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="reboot",
                  keyword="once",
                  convert="boolean",
                  order=15,
                  default=True,
                  text="""If once is set to false, do not remove the reboot flag before rebooting,
so that the node is ready to reboot again in the next allowed timerange.
This setup is needed to enforce a periodic reboot, with a patching script
hooked as a pre trigger for example.

If not set, or set to true, the reboot flag is removed before reboot, and a 'nodemgr schedule reboot' is needed to rearm.
"""
                )

class KeywordRebootPre(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="reboot",
                  keyword="pre",
                  convert="shlex",
                  order=15,
                  example="yum upgrade -y",
                  text="A command to execute before reboot. Errors are ignored."
                )

class KeywordRebootBlockingPre(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="reboot",
                  keyword="blocking_pre",
                  convert="shlex",
                  order=15,
                  example="yum upgrade -y",
                  text="A command to execute before reboot. Abort the reboot on error."
                )

class KeywordListenerAddr(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="listener",
                  keyword="addr",
                  order=15,
                  default="0.0.0.0",
                  example="1.2.3.4",
                  text="The ip addr the daemon listener must listen on."
                )

class KeywordListenerPort(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="listener",
                  keyword="port",
                  order=15,
                  default=1214,
                  text="""The port the daemon listener must listen on. In pull action mode, the collector sends a tcp packet to the server to notify there are actions to unqueue. The opensvc daemon executes the 'dequeue actions' node action upon receive. The listener.port parameter is sent to the collector upon pushasset. The collector uses this port to notify the node."""
                )

class KeywordSyslogFacility(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="syslog",
                  keyword="facility",
                  order=15,
                  default="daemon",
                  text="""The syslog facility to log to."""
                )

class KeywordSyslogLevel(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="syslog",
                  keyword="level",
                  order=15,
                  default="daemon",
                  candidates=["critical", "error", "warning", "info", "debug"],
                  text="The minimum message criticity to feed to syslog. Setting to critical actually disables the syslog logging, as the agent does not emit message at this level."
                )

class KeywordSyslogHost(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="syslog",
                  keyword="host",
                  order=15,
                  default_text="localhost if port is set",
                  text="The syslog host to send logs to. If neither host nor port are specified and if /dev/log exists, the messages are posted to /dev/log."
                )

class KeywordSyslogPort(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="syslog",
                  keyword="port",
                  order=15,
                  default=514,
                  text="The syslog host to send logs to. If neither host nor port are specified and if /dev/log exists, the messages are posted to /dev/log."
                )

class KeywordClusterName(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="cluster",
                  keyword="name",
                  order=15,
                  default="default",
                  text="This information is fetched from the join command payload received from the joined node."
                )

class KeywordClusterSecret(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="cluster",
                  keyword="secret",
                  order=15,
                  default_text="<random autogenerated on first use>",
                  text="The cluster shared secret. Used to encrypt/decrypt data with AES256. This secret is either autogenerated or fetched from a join command."
                )

class KeywordClusterNodes(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="cluster",
                  keyword="nodes",
                  convert="list",
                  order=15,
                  text="This list is fetched from the join command payload received from the joined node."
                )

class KeywordClusterQuorum(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="cluster",
                  keyword="quorum",
                  convert="boolean",
                  order=15,
                  text="Should a split segment of the cluster commit suicide. Default is False. If set to true, please set at least 2 arbitrators so you can rolling upgrade the opensvc daemons."
                )

class KeywordArbitratorName(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="arbitrator",
                  keyword="name",
                  order=15,
                  required=True,
                  text="""The arbitrator resolvable node name.

An arbitrator is a opensvc node (running the usual osvc daemon) this
cluster nodes can ask for a vote when the cluster is split.

Arbitrators are tried in sequence, the first reachable arbitrator
gives a vote. In case of a real split, all arbitrators are expected to
be unreachable from the lost segment. At least one of them is
expected to be reachable from the surviving segment.

Arbitrators of a cluster must thus be located close enough to each
other, so a subset of arbitrators can't be reachable from a split
cluster segment, while another subset of arbitrators is reachable
from the other split cluster segment. But not close enough so they can
all fail together. Usually, this can be interpreted as: same site,
not same rack and power lines.

Arbitrators usually don't run services, even though they could, as their
secret might be known by multiple clusters of different responsibles.

Arbitrators can be tested using "nodemgr ping --node <arbitrator name>".
"""
                )

class KeywordArbitratorSecret(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="arbitrator",
                  keyword="secret",
                  order=15,
                  required=True,
                  text="The secret to use to encrypt/decrypt data exchanged with the arbitrator (AES256)."
                )

class KeywordStonithCmd(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="stonith",
                  keyword="cmd",
                  convert="shlex",
                  order=15,
                  required=True,
                  example="/bin/true",
                  text="The command to use to STONITH a peer. Usually comes from a fencing utilities collection."
                )

class KeywordHbType(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="type",
                  candidates=["unicast", "multicast", "disk", "relay"],
                  order=15,
                  required=True,
                  text="The heartbeat driver name."
                )

class KeywordHbUcastAddr(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="addr",
                  rtype="ucast",
                  order=15,
                  example="1.2.3.4",
                  default_text="0.0.0.0 for listening and to the resolved nodename for sending.",
                  text="The ip address of each node."
                )

class KeywordHbUcastIntf(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="intf",
                  rtype="ucast",
                  order=15,
                  default_text="The natural interface for <addr>",
                  example="eth0",
                  text="The interface to bind."
                )

class KeywordHbUcastPort(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="port",
                  rtype="ucast",
                  order=15,
                  default=10000,
                  text="The port for each node to send to or listen on."
                )

class KeywordHbTimeout(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="timeout",
                  order=15,
                  default=15,
                  text="The delay since the last received heartbeat from a node before considering this node is gone."
                )

class KeywordHbMcastAddr(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="addr",
                  rtype="mcast",
                  order=15,
                  default="224.3.29.71",
                  text="The multicast address to send to and listen on."
                )

class KeywordHbMcastIntf(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="intf",
                  rtype="mcast",
                  order=15,
                  default_text="The natural interface for <addr>",
                  example="eth0",
                  text="The interface to bind."
                )

class KeywordHbMcastPort(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="port",
                  rtype="mcast",
                  order=15,
                  default=10000,
                  text="The port for each node to send to or listen on."
                )

class KeywordHbDiskDev(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="dev",
                  rtype="disk",
                  required=True,
                  order=15,
                  text="The device to write the hearbeats to and read from. It must be dedicated to the daemon use. Its size should be 1M + 1M per cluster node."
                )

class KeywordHbRelayRelay(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="relay",
                  rtype="relay",
                  order=15,
                  required=True,
                  example="relaynode1",
                  text="The relay resolvable node name."
                )

class KeywordHbRelaySecret(Keyword):
    def __init__(self):
        Keyword.__init__(
                  self,
                  section="hb",
                  keyword="secret",
                  rtype="relay",
                  order=15,
                  required=True,
                  example="123123123124325543565",
                  text="The secret to use to encrypt/decrypt data exchanged with the relay (AES256)."
                )


class KeyDict(KeywordStore):
    def __init__(self):
        KeywordStore.__init__(
           self,
           deprecated_keywords=DEPRECATED_KEYWORDS,
           deprecated_sections=DEPRECATED_SECTIONS,
           template_prefix="template.node.",
           base_sections=BASE_SECTIONS,
        )

        self += KeywordNodeEnv()
        self += KeywordNodeAssetEnv()
        self += KeywordNodeMaxParallel()
        self += KeywordNodeLocCountry()
        self += KeywordNodeLocCity()
        self += KeywordNodeLocZip()
        self += KeywordNodeLocBuilding()
        self += KeywordNodeLocFloor()
        self += KeywordNodeLocRoom()
        self += KeywordNodeLocRack()
        self += KeywordNodeTeamInteg()
        self += KeywordNodeTeamSupport()
        self += KeywordNodeConnectTo()
        self += KeywordNodeDbopensvc()
        self += KeywordNodeDbcompliance()
        self += KeywordNodeBranch()
        self += KeywordNodeRepo()
        self += KeywordNodeRepopkg()
        self += KeywordNodeRepocomp()
        self += KeywordNodeRuser()
        self += KeywordNodeMaintenanceGracePeriod()
        self += KeywordNodeRejoinGracePeriod()
        self += KeywordNodeReadyPeriod()
        self += KeywordComplianceSchedule()
        self += KeywordComplianceAutoUpdate()
        self += KeywordStatsSchedule()
        self += KeywordStatsCollectionSchedule()
        self += KeywordStatsDisable()
        self += KeywordChecksSchedule()
        self += KeywordPackagesSchedule()
        self += KeywordPatchesSchedule()
        self += KeywordAssetSchedule()
        self += KeywordNsrSchedule()
        self += KeywordDcsSchedule()
        self += KeywordHdsSchedule()
        self += KeywordNecismSchedule()
        self += KeywordEvaSchedule()
        self += KeywordIbmsvcSchedule()
        self += KeywordVioserverSchedule()
        self += KeywordBrocadeSchedule()
        self += KeywordDisksSchedule()
        self += KeywordSymSchedule()
        self += KeywordRotateRootPwSchedule()
        self += KeywordRebootSchedule()
        self += KeywordRebootOnce()
        self += KeywordRebootPre()
        self += KeywordRebootBlockingPre()
        self += KeywordListenerAddr()
        self += KeywordListenerPort()
        self += KeywordSyslogFacility()
        self += KeywordSyslogLevel()
        self += KeywordSyslogHost()
        self += KeywordSyslogPort()
        self += KeywordClusterName()
        self += KeywordClusterSecret()
        self += KeywordClusterNodes()
        self += KeywordClusterQuorum()
        self += KeywordArbitratorName()
        self += KeywordArbitratorSecret()
        self += KeywordStonithCmd()
        self += KeywordHbType()
        self += KeywordHbTimeout()
        self += KeywordHbUcastAddr()
        self += KeywordHbUcastIntf()
        self += KeywordHbUcastPort()
        self += KeywordHbMcastAddr()
        self += KeywordHbMcastIntf()
        self += KeywordHbMcastPort()
        self += KeywordHbDiskDev()
        self += KeywordHbRelayRelay()
        self += KeywordHbRelaySecret()

NODEKEYS = KeyDict()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        fmt = sys.argv[1]
    else:
        fmt = "text"

    NODEKEYS.print_templates(fmt=fmt)
