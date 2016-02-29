#
# Copyright (c) 2009 Christophe Varoqui <christophe.varoqui@opensvc.com>
# Copyright (c) 2009 Cyril Galibern <cyril.galibern@free.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# To change this template, choose Tools | Templates
# and open the template in the editor.

from __future__ import print_function
from svc import Svc
from freezer import Freezer
import svcBuilder
import xmlrpcClient
import os
import datetime
import time
import sys
import json
from rcGlobalEnv import rcEnv
import rcCommandWorker
import socket
import rcLogger
import rcUtilities
import rcExceptions as ex
from subprocess import *
from rcScheduler import *

try:
    import urllib2
    import base64
except:
    pass

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

class Options(object):
    def __init__(self):
        self.cron = False
        self.syncrpc = False
        self.force = False
        self.debug = False
        self.stats_dir = None
        self.begin = None
        self.end = None
        self.moduleset = ""
        self.module = ""
        self.ruleset_date = ""
        self.waitlock = 60
        self.parallel = False
        self.objects = []
        os.environ['LANG'] = 'C'

class Node(Svc, Freezer, Scheduler):
    """ Defines a cluster node.  It contain list of Svc.
        Implements node-level actions and checks.
    """
    def __str__(self):
        s = self.nodename
        return s

    def __init__(self):
        self.auth_config = None
        self.nodename = socket.gethostname().lower()
        self.authconf = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'auth.conf'))
        self.nodeconf = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'node.conf'))
        self.setup_sync_flag = os.path.join(rcEnv.pathvar, 'last_setup_sync')
        self.reboot_flag = os.path.join(rcEnv.pathvar, "REBOOT_FLAG")
        self.config_defaults = {
          'clusters': '',
          'host_mode': 'TST',
          'push_schedule': '00:00-06:00@361 mon-sun',
          'sync_schedule': '04:00-06:00@121 mon-sun',
          'comp_schedule': '02:00-06:00@241 sun',
          'no_schedule': '',
        }
        self.svcs = None
        try:
            self.clusters = list(set(self.config.get('node', 'clusters').split()))
        except:
            self.clusters = []
        self.load_config()
        self.options = Options()
        Scheduler.__init__(self)
        Freezer.__init__(self, '')
        self.action_desc = {
          'Node actions': {
            'shutdown': 'shutdown the node to powered off state',
            'reboot': 'reboot the node',
            'scheduler': 'run the node task scheduler',
            'schedule_reboot_status': 'tell if the node is scheduled for reboot',
            'schedule_reboot': 'mark the node for reboot at the next allowed period. the allowed period is defined by a "reboot" section in node.conf. the created flag file is %s' % self.reboot_flag,
            'unschedule_reboot': 'unmark the node for reboot at the next allowed period. the removed flag file is %s' % self.reboot_flag,
            'provision': 'provision the resources described in --resource arguments',
            'updatepkg': 'upgrade the opensvc agent version. the packages must be available behind the node.repo/packages url.',
            'updatecomp': 'upgrade the opensvc compliance modules. the modules must be available as a tarball behind the node.repo/compliance url.',
            'scanscsi': 'scan the scsi hosts in search of new disks',
            'dequeue_actions': "dequeue and execute actions from the collector's action queue for this node and its services.",
            'rotate_root_pw': "set a new root password and store it in the collector",
            'print_schedule': "print the node tasks schedule",
            'wol': "forge and send udp wake on lan packet to mac address specified by --mac and --broadcast arguments",
          },
          'Service actions': {
            'discover': 'discover vservices accessible from this host, cloud nodes for example',
          },
          'Node configuration edition': {
            'edit_config': 'open the node.conf configuration file with the preferred editor',
            'edit_authconfig': 'open the auth.conf configuration file with the preferred editor',
            'register': 'obtain a registration number from the collector, used to authenticate the node',
            'get': 'get the value of the node configuration parameter pointed by --param',
            'set': 'set a node configuration parameter (pointed by --param) value (pointed by --value)',
            'unset': 'unset a node configuration parameter (pointed by --param)',
          },
          'Push data to the collector': {
            'pushasset':      'push asset information to collector',
            'pushstats':      'push performance metrics to collector. By default pushed stats interval begins yesterday at the beginning of the allowed interval and ends now. This interval can be changed using --begin/--end parameters. The location where stats files are looked up can be changed using --stats-dir.',
            'pushdisks':      'push disks usage information to collector',
            'pushpkg':        'push package/version list to collector',
            'pushpatch':      'push patch/version list to collector',
            'pushsym':        'push symmetrix configuration to collector',
            'pushemcvnx':     'push EMC CX/VNX configuration to collector',
            'pushcentera':    'push EMC Centera configuration to collector',
            'pushnetapp':     'push Netapp configuration to collector',
            'pusheva':        'push HP EVA configuration to collector',
            'pushnecism':     'push NEC ISM configuration to collector',
            'pushhds':        'push HDS configuration to collector',
            'pushdcs':        'push Datacore configuration to collector',
            'pushfreenas':    'push FreeNAS configuration to collector',
            'pushibmsvc':     'push IBM SVC configuration to collector',
            'pushhp3par':     'push HP 3par configuration to collector',
            'pushibmds':      'push IBM DS configuration to collector',
            'pushvioserver':  'push IBM VIO server configuration to collector',
            'pushgcedisks':   'push Google Compute Engine disks configuration to collector',
            'pushbrocade':    'push Brocade switch configuration to collector',
            'pushnsr':        'push EMC Networker index to collector',
            'sysreport':      'push system report to the collector for archiving and diff analysis',
            'checks':         'run node sanity checks, push results to collector',
          },
          'Misc': {
            'prkey':          'show persistent reservation key of this node',
          },
          'Compliance': {
            'compliance_auto': 'run compliance checks or fix, according to the autofix property of each module. --ruleset <md5> instruct the collector to provide an historical ruleset.',
            'compliance_env': 'show the compliance modules environment variables.',
            'compliance_check': 'run compliance checks. --ruleset <md5> instruct the collector to provide an historical ruleset.',
            'compliance_fix':   'run compliance fixes. --ruleset <md5> instruct the collector to provide an historical ruleset.',
            'compliance_fixable': 'verify compliance fixes prerequisites. --ruleset <md5> instruct the collector to provide an historical ruleset.',
            'compliance_list_module': 'list compliance modules available on this node',
            'compliance_show_moduleset': 'show compliance rules applying to this node',
            'compliance_list_moduleset': 'list available compliance modulesets. --moduleset f% limit the scope to modulesets matching the f% pattern.',
            'compliance_attach_moduleset': 'attach moduleset specified by --moduleset for this node',
            'compliance_detach_moduleset': 'detach moduleset specified by --moduleset for this node',
            'compliance_list_ruleset': 'list available compliance rulesets. --ruleset f% limit the scope to rulesets matching the f% pattern.',
            'compliance_show_ruleset': 'show compliance rules applying to this node',
            'compliance_show_status': 'show compliance modules status',
            'compliance_attach': 'attach ruleset specified by --ruleset and/or moduleset specified by --moduleset for this node',
            'compliance_detach': 'detach ruleset specified by --ruleset and/or moduleset specified by --moduleset for this node',
            'compliance_attach_ruleset': 'attach ruleset specified by --ruleset for this node',
            'compliance_detach_ruleset': 'detach ruleset specified by --ruleset for this node',
          },
          'Collector management': {
            'collector_events': 'display node events during the period specified by --begin/--end. --end defaults to now. --begin defaults to 7 days ago',
            'collector_alerts': 'display node alerts',
            'collector_checks': 'display node checks',
            'collector_disks': 'display node disks',
            'collector_status': 'display node services status according to the collector',
            'collector_list_actions': 'list actions on the node, whatever the service, during the period specified by --begin/--end. --end defaults to now. --begin defaults to 7 days ago',
            'collector_ack_action': 'acknowledge an action error on the node. an acknowlegment can be completed by --author (defaults to root@nodename) and --comment',
            'collector_show_actions': 'show actions detailled log. a single action is specified by --id. a range is specified by --begin/--end dates. --end defaults to now. --begin defaults to 7 days ago',
            'collector_list_nodes': 'show the list of nodes matching the filterset pointed by --filterset',
            'collector_list_services': 'show the list of services matching the filterset pointed by --filterset',
            'collector_list_filtersets': 'show the list of filtersets available on the collector. if specified, --filterset <pattern> limits the resulset to filtersets matching <pattern>',
            'collector_asset': 'display asset information known to the collector',
            'collector_networks': 'display network information known to the collector for each node ip',
            'collector_json_asset': 'display asset information known to the collector, output in JSON',
            'collector_json_networks': 'display network information known to the collector for each node ip, output in JSON',
            'collector_json_list_unavailability_ack': 'same as "collector list unavailability ack", output in JSON',
            'collector_json_list_actions': 'same as "collector list actions", output in JSON',
            'collector_json_show_actions': 'same as "collector show actions", output in JSON',
            'collector_json_status': 'same as "collector status", output in JSON',
            'collector_json_checks': 'same as "collector checks", output in JSON',
            'collector_json_disks': 'same as "collector disks", output in JSON',
            'collector_json_alerts': 'same as "collector alerts", output in JSON',
            'collector_json_events': 'same as "collector events", output in JSON',
            'collector_json_list_nodes': 'same as "collector list nodes", output in JSON',
            'collector_json_list_services': 'same as "collector list services", output in JSON',
            'collector_json_list_filtersets': 'same as "collector list filtersets", output in JSON',
            'collector_tag': 'set a node tag (pointed by --tag)',
            'collector_untag': 'unset a node tag (pointed by --tag)',
            'collector_show_tags': 'list all node tags',
            'collector_list_tags': 'list all available tags. use --like to filter the output.',
            'collector_create_tag': 'create a new tag',
          },
        }
        self.collector = xmlrpcClient.Collector()
        self.cmdworker = rcCommandWorker.CommandWorker()
        try:
            rcos = __import__('rcOs'+rcEnv.sysname)
        except ImportError:
            rcos = __import__('rcOs')
        self.os = rcos.Os()
        rcEnv.logfile = os.path.join(rcEnv.pathlog, "node.log")
        self.log = rcLogger.initLogger(rcEnv.nodename)
	self.scheduler_actions = {
	 "checks": SchedOpts("checks"),
	 "dequeue_actions": SchedOpts("dequeue_actions", schedule_option="no_schedule"),
	 "pushstats": SchedOpts("stats"),
	 "pushpkg": SchedOpts("packages"),
	 "pushpatch": SchedOpts("patches"),
	 "pushasset": SchedOpts("asset"),
	 "pushnsr": SchedOpts("nsr", schedule_option="no_schedule"),
	 "pushhp3par": SchedOpts("hp3par", schedule_option="no_schedule"),
	 "pushemcvnx": SchedOpts("emcvnx", schedule_option="no_schedule"),
	 "pushcentera": SchedOpts("centera", schedule_option="no_schedule"),
	 "pushnetapp": SchedOpts("netapp", schedule_option="no_schedule"),
	 "pushibmds": SchedOpts("ibmds", schedule_option="no_schedule"),
	 "pushdcs": SchedOpts("dcs", schedule_option="no_schedule"),
	 "pushfreenas": SchedOpts("freenas", schedule_option="no_schedule"),
	 "pushgcedisks": SchedOpts("gcedisks", schedule_option="no_schedule"),
	 "pushhds": SchedOpts("hds", schedule_option="no_schedule"),
	 "pushnecism": SchedOpts("necism", schedule_option="no_schedule"),
	 "pusheva": SchedOpts("eva", schedule_option="no_schedule"),
	 "pushibmsvc": SchedOpts("ibmsvc", schedule_option="no_schedule"),
	 "pushvioserver": SchedOpts("vioserver", schedule_option="no_schedule"),
	 "pushsym": SchedOpts("sym", schedule_option="no_schedule"),
	 "pushbrocade": SchedOpts("brocade", schedule_option="no_schedule"),
	 "pushdisks": SchedOpts("disks"),
	 "sysreport": SchedOpts("sysreport"),
	 "compliance_auto": SchedOpts("compliance", fname="last_comp_check", schedule_option="comp_schedule"),
	 "auto_rotate_root_pw": SchedOpts("rotate_root_pw", fname="last_rotate_root_pw", schedule_option="no_schedule"),
	 "auto_reboot": SchedOpts("reboot", fname="last_auto_reboot", schedule_option="no_schedule")
        }


    def call(self, cmd=['/bin/false'], cache=False, info=False,
             errlog=True, err_to_warn=False, err_to_info=False,
             outlog=False):
        """Use subprocess module functions to do a call
        """
        return rcUtilities.call(cmd, log=self.log,
                                cache=cache,
                                info=info, errlog=errlog,
                                err_to_warn=err_to_warn,
                                err_to_info=err_to_info,
                                outlog=outlog)

    def vcall(self, cmd, err_to_warn=False, err_to_info=False):
        """Use subprocess module functions to do a call and
        log the command line using the resource logger
        """
        return rcUtilities.vcall(cmd, log=self.log,
                                 err_to_warn=err_to_warn,
                                 err_to_info=err_to_info)

    def supported_actions(self):
        a = []
        for s in self.action_desc:
            a += self.action_desc[s].keys()
        return a

    def build_services(self, *args, **kwargs):
        if self.svcs is not None and \
           ('svcnames' not in kwargs or \
           (type(kwargs['svcnames']) == list and len(kwargs['svcnames'])==0)):
            return

        if 'svcnames' in kwargs and \
           type(kwargs['svcnames']) == list and \
           len(kwargs['svcnames'])>0 and \
           self.svcs is not None:
            svcnames_request = set(kwargs['svcnames'])
            svcnames_actual = set([s.svcname for s in self.svcs])
            svcnames_request = list(svcnames_request-svcnames_actual)
            if len(svcnames_request) == 0:
                return

        self.svcs = []
        autopush = True
        if 'autopush' in kwargs:
            if not kwargs['autopush']:
                autopush = False
            del kwargs['autopush']
        svcs = svcBuilder.build_services(*args, **kwargs)
        for svc in svcs:
            self += svc
        if autopush:
            for svc in self.svcs:
                if svc.collector_outdated():
                    svc.action('push')

        if 'svcnames' in kwargs:
            if type(kwargs['svcnames']) == list:
                n = len(kwargs['svcnames'])
            else:
                n = 1
            if len(self.svcs) != n:
                raise ex.excError("building error")


    def close(self):
        self.collector.stop_worker()
        self.cmdworker.stop_worker()

    def edit_config(self):
        cf = os.path.join(rcEnv.pathetc, "node.conf")
        return self.edit_cf(cf)

    def edit_authconfig(self):
        cf = os.path.join(rcEnv.pathetc, "auth.conf")
        return self.edit_cf(cf)

    def edit_cf(self, cf):
        if "EDITOR" in os.environ:
            editor = os.environ["EDITOR"]
        elif os.name == "nt":
            editor = "notepad"
        else:
            editor = "vi"
        from rcUtilities import which
        if not which(editor):
            print("%s not found" % editor, file=sys.stderr)
            return 1
        return os.system(' '.join((editor, cf)))

    def write_config(self):
        for o in self.config_defaults:
            if self.config.has_option('DEFAULT', o):
                self.config.remove_option('DEFAULT', o)
        for s in self.config.sections():
            if '#sync#' in s:
                self.config.remove_section(s)
        try:
            fp = open(self.nodeconf, 'w')
            self.config.write(fp)
            fp.close()
        except:
            print("failed to write new %s"%self.nodeconf, file=sys.stderr)
            raise Exception()
        try:
            os.chmod(self.nodeconf, 0600)
        except:
            pass
        self.load_config()

    def purge_status_last(self):
        for s in self.svcs:
            s.purge_status_last()

    def load_config(self):
        self.config = ConfigParser.RawConfigParser(self.config_defaults)
        self.config.read(self.nodeconf)

    def load_auth_config(self):
        if self.auth_config is not None:
            return
        self.auth_config = ConfigParser.ConfigParser()
        self.auth_config.read(self.authconf)

    def setup_sync_outdated(self):
        """ return True if one env file has changed in the last 10'
            else return False
        """
        import datetime
        import glob
        envs = glob.glob(os.path.join(rcEnv.pathetc, '*.env'))
        if not os.path.exists(self.setup_sync_flag):
            return True
        for pathenv in envs:
            try:
                mtime = os.stat(pathenv).st_mtime
                f = open(self.setup_sync_flag)
                last = float(f.read())
                f.close()
            except:
                return True
            if mtime > last:
                return True
        return False

    def format_desc(self, action=None):
        from textwrap import TextWrapper
        from compliance import Compliance
        from collector import Collector
        wrapper = TextWrapper(subsequent_indent="%19s"%"", width=78)
        desc = ""
        for s in sorted(self.action_desc):
            valid_actions = []
            for a in sorted(self.action_desc[s]):
                if action is not None and not a.startswith(action):
                    continue
                valid_actions.append(a)
            if len(valid_actions) == 0:
                continue
            l = len(s)
            desc += s+'\n'
            for i in range(0, l):
                desc += '-'
            desc += "\n\n"
            for a in valid_actions:
                if a.startswith("compliance_"):
                    o = Compliance(self.skip_action, self.options, self.collector)
                    if not hasattr(o, a):
                        continue
                elif a.startswith("collector_"):
                    o = Collector(self.options, self.collector)
                    if not hasattr(o, a):
                        continue
                elif not hasattr(self, a):
                    continue
                fancya = a.replace('_', ' ')
                if len(a) < 16:
                    text = "  %-16s %s\n"%(fancya, self.action_desc[s][a])
                    desc += wrapper.fill(text)
                else:
                    text = "  %-16s"%(fancya)
                    desc += wrapper.fill(text)
                    desc += '\n'
                    text = "%19s%s"%(" ", self.action_desc[s][a])
                    desc += wrapper.fill(text)
                desc += '\n\n'
        return desc[0:-2]

    def __iadd__(self, s):
        if not isinstance(s, Svc):
            return self
        if self.svcs is None:
            self.svcs = []
        s.node = self
        if not hasattr(s, "clustername") and len(self.clusters) == 1:
            s.clustername = self.clusters[0]
        self.svcs.append(s)
        return self

    def action(self, a):
        if a.startswith("compliance_"):
            from compliance import Compliance
            o = Compliance(self.skip_action, self.options, self.collector)
            if self.options.cron and a == "compliance_auto" and \
               self.config.has_option('compliance', 'auto_update') and \
               self.config.getboolean('compliance', 'auto_update'):
                o.updatecomp = True
                o.node = self
            return getattr(o, a)()
        elif a.startswith("collector_"):
            from collector import Collector
            o = Collector(self.options, self.collector)
            return getattr(o, a)()
        else:
            return getattr(self, a)()

    def scheduler(self):
        self.options.cron = True
        for action in self.scheduler_actions:
            try:
                self.action(action)
            except:
                import traceback
                traceback.print_exc()

    def get_push_objects(self, s):
        if len(self.options.objects) > 0:
            return self.options.objects
        try:
            objects = self.config.get(s, "objects").split(",")
        except Exception as e:
            objects = ["magix123456"]
            print(e)
        return objects

    def pushstats(self):
        # set stats range to push to "last pushstat => now"

        ts = self.get_timestamp_f(self.scheduler_actions["pushstats"].fname)
        try:
            with open(ts, "r") as f:
                buff = f.read()
            start = datetime.datetime.strptime(buff, "%Y-%m-%d %H:%M:%S.%f\n")
            now = datetime.datetime.now()
            delta = now - start
            interval = delta.days * 1440 + delta.seconds // 60 + 10
            #print("push stats for the last %d minutes since last push" % interval)
        except Exception as e:
            interval = 1450
            #print("can not determine last push date. push stats for the last %d minutes" % interval)
        if interval < 21:
            interval = 21

        if self.skip_action("pushstats"):
            return
        self.task_pushstats(interval)

    @scheduler_fork
    def task_pushstats(self, interval):
        if self.config.has_option("stats", "disable"):
            disable = self.config.get("stats", "disable")
        else:
            disable = []

        if isinstance(disable, str):
            try:
                disable = json.loads(disable)
            except:
                if ',' in disable:
                    disable = disable.replace(' ','').split(',')
                else:
                    disable = disable.split(' ')
        else:
            disable = []

        return self.collector.call('push_stats',
                                stats_dir=self.options.stats_dir,
                                stats_start=self.options.begin,
                                stats_end=self.options.end,
                                interval=interval,
                                disable=disable)

    def pushpkg(self):
        if self.skip_action("pushpkg"):
            return
        self.task_pushpkg()

    @scheduler_fork
    def task_pushpkg(self):
        self.collector.call('push_pkg')

    def pushpatch(self):
        if self.skip_action("pushpatch"):
            return
        self.task_pushpatch()

    @scheduler_fork
    def task_pushpatch(self):
        self.collector.call('push_patch')

    def pushasset(self):
        if self.skip_action("pushasset"):
            return
        self.task_pushasset()

    @scheduler_fork
    def task_pushasset(self):
        self.collector.call('push_asset', self)

    def pushnsr(self):
        if self.skip_action("pushnsr"):
            return
        self.task_pushnsr()

    @scheduler_fork
    def task_pushnsr(self):
        self.collector.call('push_nsr')

    def pushhp3par(self):
        if self.skip_action("pushhp3par"):
            return
        self.task_pushhp3par()

    @scheduler_fork
    def task_pushhp3par(self):
        self.collector.call('push_hp3par', self.options.objects)

    def pushnetapp(self):
        if self.skip_action("pushnetapp"):
            return
        self.task_pushnetapp()

    @scheduler_fork
    def task_pushnetapp(self):
        self.collector.call('push_netapp', self.options.objects)

    def pushcentera(self):
        if self.skip_action("pushcentera"):
            return
        self.task_pushcentera()

    @scheduler_fork
    def task_pushcentera(self):
        self.collector.call('push_centera', self.options.objects)

    def pushemcvnx(self):
        if self.skip_action("pushemcvnx"):
            return
        self.task_pushemcvnx()

    @scheduler_fork
    def task_pushemcvnx(self):
        self.collector.call('push_emcvnx', self.options.objects)

    def pushibmds(self):
        if self.skip_action("pushibmds"):
            return
        self.task_pushibmds()

    @scheduler_fork
    def task_pushibmds(self):
        self.collector.call('push_ibmds', self.options.objects)

    def pushgcedisks(self):
        if self.skip_action("pushgcedisks"):
            return
        self.task_pushgcedisks()

    @scheduler_fork
    def task_pushgcedisks(self):
        self.collector.call('push_gcedisks', self.options.objects)

    def pushfreenas(self):
        if self.skip_action("pushfreenas"):
            return
        self.task_pushfreenas()

    @scheduler_fork
    def task_pushfreenas(self):
        self.collector.call('push_freenas', self.options.objects)

    def pushdcs(self):
        if self.skip_action("pushdcs"):
            return
        self.task_pushdcs()

    @scheduler_fork
    def task_pushdcs(self):
        self.collector.call('push_dcs', self.options.objects)

    def pushhds(self):
        if self.skip_action("pushhds"):
            return
        self.task_pushhds()

    @scheduler_fork
    def task_pushhds(self):
        self.collector.call('push_hds', self.options.objects)

    def pushnecism(self):
        if self.skip_action("pushnecism"):
            return
        self.task_pushnecism()

    @scheduler_fork
    def task_pushnecism(self):
        self.collector.call('push_necism', self.options.objects)

    def pusheva(self):
        if self.skip_action("pusheva"):
            return
        self.task_pusheva()

    @scheduler_fork
    def task_pusheva(self):
        self.collector.call('push_eva', self.options.objects)

    def pushibmsvc(self):
        if self.skip_action("pushibmsvc"):
            return
        self.task_pushibmsvc()

    @scheduler_fork
    def task_pushibmsvc(self):
        self.collector.call('push_ibmsvc', self.options.objects)

    def pushvioserver(self):
        if self.skip_action("pushvioserver"):
            return
        self.task_pushvioserver()

    @scheduler_fork
    def task_pushvioserver(self):
        self.collector.call('push_vioserver', self.options.objects)

    def pushsym(self):
        if self.skip_action("pushsym"):
            return
        self.task_pushsym()

    @scheduler_fork
    def task_pushsym(self):
        objects = self.get_push_objects("sym")
        self.collector.call('push_sym', objects)

    def pushbrocade(self):
        if self.skip_action("pushbrocade"):
            return
        self.task_pushbrocade()

    @scheduler_fork
    def task_pushbrocade(self):
        self.collector.call('push_brocade', self.options.objects)

    def auto_rotate_root_pw(self):
        if self.skip_action("auto_rotate_root_pw"):
            return
        self.task_auto_rotate_root_pw()

    @scheduler_fork
    def task_auto_rotate_root_pw(self):
        self.rotate_root_pw()

    def unschedule_reboot(self):
        if not os.path.exists(self.reboot_flag):
            print("reboot already not scheduled")
            return
        os.unlink(self.reboot_flag)
        print("reboot unscheduled")

    def schedule_reboot(self):
        if not os.path.exists(self.reboot_flag):
            with open(self.reboot_flag, "w") as f: f.write("")
        import stat
        s = os.stat(self.reboot_flag)
        if s.st_uid != 0:
            os.chown(self.reboot_flag, 0, -1)
            print("set %s root ownership"%self.reboot_flag)
        if s.st_mode & stat.S_IWOTH:
            mode = s.st_mode ^ stat.S_IWOTH
            os.chmod(self.reboot_flag, mode)
            print("set %s not world-writable"%self.reboot_flag)
        print("reboot scheduled")

    def schedule_reboot_status(self):
        import stat
        if not os.path.exists(self.reboot_flag):
            print("reboot is not scheduled")
            return
        s = os.stat(self.reboot_flag)
        if s.st_uid != 0 or s.st_mode & stat.S_IWOTH:
            print("reboot is not scheduled")
            return
        sch = self.scheduler_actions["auto_reboot"]
        schedule = self.sched_get_schedule_raw(sch.section, sch.schedule_option)
        print("reboot is scheduled")
        print("reboot schedule: %s" % schedule)
        now = datetime.datetime.now()
        _max = 14400
        self.options.cron = True
        for i in range(_max):
            d = now + datetime.timedelta(minutes=i*10)
            if not self.skip_action("auto_reboot", now=d, verbose=False):
                print("next allowed reboot:", d.strftime("%a %Y-%m-%d %H:%M"))
                break
        if i == _max - 1:
            print("next allowed reboot: none in the next %d days" % (_max/144))

    def auto_reboot(self):
        if self.skip_action("auto_reboot"):
            return
        self.task_auto_reboot()

    @scheduler_fork
    def task_auto_reboot(self):
        if not os.path.exists(self.reboot_flag):
            print("%s is not present. no reboot scheduled" % self.reboot_flag)
            return
        import stat
        s = os.stat(self.reboot_flag)
        if s.st_uid != 0:
            print("%s does not belong to root. abort scheduled reboot" % self.reboot_flag)
            return
        if s.st_mode & stat.S_IWOTH:
            print("%s is world writable. abort scheduled reboot" % self.reboot_flag)
            return
        print("remove %s and reboot" % self.reboot_flag)
        os.unlink(self.reboot_flag)
        self.reboot()

    def pushdisks(self):
        if self.skip_action("pushdisks"):
            return
        self.task_pushdisks()

    @scheduler_fork
    def task_pushdisks(self):
        if self.svcs is None:
            self.build_services()
        self.collector.call('push_disks', self)

    def shutdown(self):
        print("TODO")

    def reboot(self):
        print("TODO")

    def sysreport(self):
        if self.skip_action("sysreport"):
            return
        try:
            self.task_sysreport()
        except Exception as e:
            print(e)
            return 1

    @scheduler_fork
    def task_sysreport(self):
        from rcGlobalEnv import rcEnv
        try:
            m = __import__('rcSysReport'+rcEnv.sysname)
        except ImportError:
            print("sysreport is not supported on this os")
            return
        m.SysReport(node=self).sysreport(force=self.options.force)

    def get_prkey(self):
        if self.config.has_option("node", "prkey"):
            hostid = self.config.get("node", "prkey")
            if len(hostid) > 18 or not hostid.startswith("0x") or \
               len(set(hostid[2:]) - set("0123456789abcdefABCDEF")) > 0:
                raise ex.excError("prkey in node.conf must have 16 significant hex digits max (ex: 0x90520a45138e85)")
            return hostid
        self.log.info("can't find a prkey forced in node.conf. generate one.")
        hostid = "0x"+self.hostid()
        self.config.set('node', 'prkey', hostid)
        self.write_config()
        return hostid

    def prkey(self):
        print(self.get_prkey())

    def hostid(self):
        from rcGlobalEnv import rcEnv
        m = __import__('hostid'+rcEnv.sysname)
        return m.hostid()

    def checks(self):
        if self.skip_action("checks"):
            return
        self.task_checks()

    @scheduler_fork
    def task_checks(self):
        import checks
        if self.svcs is None:
            self.build_services()
        c = checks.checks(self.svcs)
        c.node = self
        c.do_checks()

    def wol(self):
        import rcWakeOnLan
        if self.options.mac is None:
            print("missing parameter. set --mac argument. multiple mac addresses must be separated by comma", file=sys.stderr)
            print("example 1 : --mac 00:11:22:33:44:55", file=sys.stderr)
            print("example 2 : --mac 00:11:22:33:44:55,66:77:88:99:AA:BB", file=sys.stderr)
            return 1
        if self.options.broadcast is None:
            print("missing parameter. set --broadcast argument. needed to identify accurate network to use", file=sys.stderr)
            print("example 1 : --broadcast 10.25.107.255", file=sys.stderr)
            print("example 2 : --broadcast 192.168.1.5,10.25.107.255", file=sys.stderr)
            return 1
        macs = self.options.mac.split(',')
        broadcasts = self.options.broadcast.split(',')
        for brdcast in broadcasts:
            for mac in macs:
                req = rcWakeOnLan.wolrequest(macaddress=mac, broadcast=brdcast)
                if not req.check_broadcast():
                    print("Error : skipping broadcast address <%s>, not in the expected format 123.123.123.123"%req.broadcast, file=sys.stderr)
                    break
                if not req.check_mac():
                    print("Error : skipping mac address <%s>, not in the expected format 00:11:22:33:44:55"%req.mac, file=sys.stderr)
                    continue
                if req.send():
                    print("Sent Wake On Lan packet to mac address <%s>"%req.mac)
                else:
                    print("Error while trying to send Wake On Lan packet to mac address <%s>"%req.mac, file=sys.stderr)

    def unset(self):
        if self.options.param is None:
            print("no parameter. set --param", file=sys.stderr)
            return 1
        l = self.options.param.split('.')
        if len(l) != 2:
            print("malformed parameter. format as 'section.key'", file=sys.stderr)
            return 1
        section, option = l
        if not self.config.has_section(section):
            print("section '%s' not found"%section, file=sys.stderr)
            return 1
        if not self.config.has_option(section, option):
            print("option '%s' not found in section '%s'"%(option, section), file=sys.stderr)
            return 1
        try:
            self.config.remove_option(section, option)
            self.write_config()
        except:
            return 1
        return 0

    def get(self):
        if self.options.param is None:
            print("no parameter. set --param", file=sys.stderr)
            return 1
        l = self.options.param.split('.')
        if len(l) != 2:
            print("malformed parameter. format as 'section.key'", file=sys.stderr)
            return 1
        section, option = l
        if not self.config.has_section(section):
            print("section '%s' not found"%section, file=sys.stderr)
            return 1
        if not self.config.has_option(section, option):
            print("option '%s' not found in section '%s'"%(option, section), file=sys.stderr)
            return 1
        print(self.config.get(section, option))
        return 0

    def set(self):
        if self.options.param is None:
            print("no parameter. set --param", file=sys.stderr)
            return 1
        if self.options.value is None:
            print("no value. set --value", file=sys.stderr)
            return 1
        l = self.options.param.split('.')
        if len(l) != 2:
            print("malformed parameter. format as 'section.key'", file=sys.stderr)
            return 1
        section, option = l
        if not self.config.has_section(section):
            try:
                self.config.add_section(section)
            except ValueError as e:
                print(e)
                return 1
        if self.config.has_option(section, option) and \
           self.config.get(section, option) == self.options.value:
            return
        self.config.set(section, option, self.options.value)
        try:
            self.write_config()
        except:
            return 1
        return 0

    def register(self):
        u = self.collector.call('register_node')
        if u is None:
            print("failed to obtain a registration number", file=sys.stderr)
            return 1
        elif isinstance(u, dict) and "ret" in u and u["ret"] != 0:
            print("failed to obtain a registration number", file=sys.stderr)
            try:
                print(u["msg"])
            except:
                pass
            return 1
        elif isinstance(u, list):
            print(u[0], file=sys.stderr)
            return 1
        try:
            if not self.config.has_section('node'):
                self.config.add_section('node')
            self.config.set('node', 'uuid', u)
            self.write_config()
        except:
            print("failed to write registration number: %s"%u, file=sys.stderr)
            return 1
        print("registered")
        return 0

    def service_action_worker(self, s, **kwargs):
        r = s.action(**kwargs)
        self.close()
        sys.exit(r)

    def devlist(self, tree=None):
        if tree is None:
            try:
                m = __import__("rcDevTree"+rcEnv.sysname)
            except ImportError:
                return
            tree = m.DevTree()
            tree.load()
        l = []
        for dev in tree.get_top_devs():
            if len(dev.devpath) > 0:
                l.append(dev.devpath[0])
        return l

    def updatecomp(self):
        if self.config.has_option('node', 'repocomp'):
            pkg_name = self.config.get('node', 'repocomp').strip('/') + "/current"
        elif self.config.has_option('node', 'repo'):
            pkg_name = self.config.get('node', 'repo').strip('/') + "/compliance/current"
        else:
            if self.options.cron:
                return 0
            print("node.repo or node.repocomp must be set in node.conf", file=sys.stderr)
            return 1
        import tempfile
        f = tempfile.NamedTemporaryFile()
        tmpf = f.name
        f.close()
        print("get %s (%s)"%(pkg_name, tmpf))
        import urllib
        kwargs = {}
        try:
            import ssl
            context = ssl._create_unverified_context()
            kwargs['context'] = context
        except:
            pass
        try:
            fname, headers = urllib.urlretrieve(pkg_name, tmpf, **kwargs)
        except IOError as e:
            print("download failed", ":", e[1], file=sys.stderr)
            try:
                os.unlink(fname)
            except:
                pass
            if self.options.cron:
                return 0
            return 1
        if 'invalid file' in headers.values():
            try:
                os.unlink(fname)
            except:
                pass
            if self.options.cron:
                return 0
            print("invalid file", file=sys.stderr)
            return 1
        with open(fname, 'r') as f:
            content = f.read()
        if content.startswith('<') and '404 Not Found' in content:
            try:
                os.unlink(fname)
            except:
                pass
            if self.options.cron:
                return 0
            print("not found", file=sys.stderr)
            return 1
        tmpp = os.path.join(rcEnv.pathtmp, 'compliance')
        backp = os.path.join(rcEnv.pathtmp, 'compliance.bck')
        compp = os.path.join(rcEnv.pathvar, 'compliance')
        if not os.path.exists(compp):
            os.makedirs(compp, 0o755)
        import shutil
        try:
            shutil.rmtree(backp)
        except:
            pass
        print("extract compliance in", rcEnv.pathtmp)
        import tarfile
        tar = tarfile.open(f.name)
        os.chdir(rcEnv.pathtmp)
        try:
            tar.extractall()
            tar.close()
        except:
            try:
                os.unlink(fname)
            except:
                pass
            print("failed to unpack", file=sys.stderr)
            return 1
        try:
            os.unlink(fname)
        except:
            pass
        print("install new compliance")
        shutil.move(compp, backp)
        shutil.move(tmpp, compp)

    def updatepkg(self):
        if not os.path.exists(os.path.join(rcEnv.pathlib, 'rcUpdatePkg'+rcEnv.sysname+'.py')):
            print("updatepkg not implemented on", rcEnv.sysname, file=sys.stderr)
            return 1
        m = __import__('rcUpdatePkg'+rcEnv.sysname)
        if self.config.has_option('node', 'repopkg'):
            pkg_name = self.config.get('node', 'repopkg').strip('/') + "/" + m.repo_subdir + '/current'
        elif self.config.has_option('node', 'repo'):
            pkg_name = self.config.get('node', 'repo').strip('/') + "/packages/" + m.repo_subdir + '/current'
        else:
            print("node.repo or node.repopkg must be set in node.conf", file=sys.stderr)
            return 1
        import tempfile
        f = tempfile.NamedTemporaryFile()
        tmpf = f.name
        f.close()
        print("get %s (%s)"%(pkg_name, tmpf))
        import urllib
        kwargs = {}
        try:
            import ssl
            context = ssl._create_unverified_context()
            kwargs['context'] = context
        except:
            pass
        try:
            fname, headers = urllib.urlretrieve(pkg_name, tmpf, **kwargs)
        except IOError as e:
            print("download failed", ":", e[1], file=sys.stderr)
            try:
                os.unlink(fname)
            except:
                pass
            return 1
        if 'invalid file' in headers.values():
            try:
                os.unlink(fname)
            except:
                pass
            print("invalid file", file=sys.stderr)
            return 1
        with open(fname, 'r') as f:
            content = f.read()
        if content.startswith('<') and '404 Not Found' in content:
            print("not found", file=sys.stderr)
            try:
                os.unlink(fname)
            except:
                pass
            return 1
        print("updating opensvc")
        m.update(tmpf)
        print("clean up")
        try:
            os.unlink(fname)
        except:
            pass
        return 0

    def provision(self):
        self.provision_resource = []
        for rs in self.options.resource:
            try:
                d = json.loads(rs)
            except:
                print("JSON read error: %s", rs, file=sys.stderr)
                return 1
            if 'rtype' not in d:
                print("'rtype' key must be set in resource dictionary: %s", rs, file=sys.stderr)
                return 1

            rtype = d['rtype']
            if len(rtype) < 2:
                print("invalid 'rtype' value: %s", rs, file=sys.stderr)
                return 1
            rtype = rtype[0].upper() + rtype[1:].lower()

            if 'type' in d:
                rtype +=  d['type'][0].upper() + d['type'][1:].lower()
            modname = 'prov' + rtype
            try:
                m = __import__(modname)
            except ImportError:
                print("provisioning is not available for resource type:", d['rtype'], "(%s)"%modname, file=sys.stderr)
                return 1
            if not hasattr(m, "d_provisioner"):
                print("provisioning with nodemgr is not available for this resource type:", d['rtype'], file=sys.stderr)
                return 1

            self.provision_resource.append((m, d))

        for o, d in self.provision_resource:
            getattr(o, "d_provisioner")(d)

    def get_ruser(self, node):
        default = "root"
        if not self.config.has_option('node', "ruser"):
            return default
        h = {}
        s = self.config.get('node', 'ruser').split()
        for e in s:
            l = e.split("@")
            if len(l) == 1:
                default = e
            elif len(l) == 2:
                _ruser, _node = l
                h[_node] = _ruser
            else:
                continue
        if node in h:
            return h[node]
        return default

    def dequeue_actions(self):
        if self.skip_action("dequeue_actions"):
            return
        self.task_dequeue_actions()

    @scheduler_fork
    def task_dequeue_actions(self):
        actions = self.collector.call('collector_get_action_queue')
        if actions is None:
            return "unable to fetch actions scheduled by the collector"
        import re
        regex = re.compile("\x1b\[([0-9]{1,3}(;[0-9]{1,3})*)?[m|K|G]", re.UNICODE)
        data = []
        for action in actions:
            ret, out, err = self.dequeue_action(action)
            out = regex.sub('', out).decode('utf8', 'ignore')
            err = regex.sub('', err).decode('utf8', 'ignore')
            data.append((action.get('id'), ret, out, err))
        if len(actions) > 0:
            self.collector.call('collector_update_action_queue', data)

    def dequeue_action(self, action):
        if rcEnv.sysname == "Windows":
            nodemgr = os.path.join(rcEnv.pathsvc, "nodemgr.cmd")
            svcmgr = os.path.join(rcEnv.pathsvc, "svcmgr.cmd")
        else:
            nodemgr = os.path.join(rcEnv.pathbin, "nodemgr")
            svcmgr = os.path.join(rcEnv.pathbin, "svcmgr")
        if action.get("svcname") is None or action.get("svcname") == "":
            cmd = [nodemgr]
        else:
            cmd = [svcmgr, "-s", action.get("svcname")]
        cmd += action.get("command", "").split()
        print("dequeue action %s" % " ".join(cmd))
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        return p.returncode, out, err

    def rotate_root_pw(self):
        pw = self.genpw()

        from collector import Collector
        o = Collector(self.options, self.collector)
        try:
            data = getattr(o, 'rotate_root_pw')(pw)
        except Exception as e:
            print("unexpected error sending the new password to the collector (%s). Abording password change."%str(e), file=sys.stderr)
            return 1

        try:
            rc = __import__('rcPasswd'+rcEnv.sysname)
        except ImportError:
            print("not implemented")
            return 1
        except Exception as e:
            print(e)
            return 1
        r = rc.change_root_pw(pw)
        if r == 0:
            print("root password changed")
        else:
            print("failed to change root password")
        return r

    def genpw(self):
        import string
        chars = string.letters + string.digits + r'+/'
        assert 256 % len(chars) == 0  # non-biased later modulo
        PWD_LEN = 16
        return ''.join(chars[ord(c) % len(chars)] for c in os.urandom(PWD_LEN))

    def scanscsi(self):
        try:
            m = __import__("rcDiskInfo"+rcEnv.sysname)
        except ImportError:
            print("scanscsi is not supported on", rcEnv.sysname, file=sys.stderr)
            return 1
        o = m.diskInfo()
        if not hasattr(o, 'scanscsi'):
            print("scanscsi is not implemented on", rcEnv.sysname, file=sys.stderr)
            return 1
        return o.scanscsi()

    def discover(self):
        self.cloud_init()

    def cloud_init(self):
        r = 0
        for s in self.config.sections():
            try:
                self.cloud_init_section(s)
            except ex.excInitError as e:
                print(str(e), file=sys.stderr)
                r |= 1
        return r

    def cloud_get(self, s):
        if not s.startswith("cloud"):
            return

        if not s.startswith("cloud#"):
            raise ex.excInitError("cloud sections must have a unique name in the form '[cloud#n] in %s"%self.nodeconf)

        if hasattr(self, "clouds") and s in self.clouds:
            return self.clouds[s]

        try:
            cloud_type = self.config.get(s, 'type')
        except:
            raise ex.excInitError("type option is mandatory in cloud section in %s"%self.nodeconf)

        # noop if already loaded
        self.load_auth_config()
        try:
            auth_dict = {}
            for key, val in self.auth_config.items(s):
                auth_dict[key] = val
        except:
            raise ex.excInitError("%s must have a '%s' section"%(self.authconf, s))

        if len(cloud_type) == 0:
            raise ex.excInitError("invalid cloud type in %s"%self.nodeconf)

        mod_name = "rcCloud" + cloud_type[0].upper() + cloud_type[1:].lower()

        try:
            m = __import__(mod_name)
        except ImportError:
            raise ex.excInitError("cloud type '%s' is not supported"%cloud_type)

        if not hasattr(self, "clouds"):
            self.clouds = {}
        c = m.Cloud(s, auth_dict)
        self.clouds[s] = c
        return c

    def cloud_init_section(self, s):
        c = self.cloud_get(s)

        if c is None:
            return

        cloud_id = c.cloud_id()
        svcnames = c.list_svcnames()

        self.cloud_purge_services(cloud_id, map(lambda x: x[1], svcnames))

        for vmname, svcname in svcnames:
            self.cloud_init_service(c, vmname, svcname)

    def cloud_purge_services(self, suffix, svcnames):
        import glob
        envs = glob.glob(os.path.join(rcEnv.pathetc, '*.env'))
        for env in envs:
            svcname = os.path.basename(env).rstrip('.env')
            if svcname.endswith(suffix) and svcname not in svcnames:
                print("purge_service(svcname)", svcname)

    def cloud_init_service(self, c, vmname, svcname):
        import glob
        envs = glob.glob(os.path.join(rcEnv.pathetc, '*.env'))
        env = os.path.join(rcEnv.pathetc, svcname+'.env')
        if env in envs:
            print(svcname, "is already defined")
            return
        print("initialize", svcname)

        defaults = {
          'app': c.app_id(svcname),
          'mode': c.mode,
          'nodes': rcEnv.nodename,
          'service_type': 'TST',
          'vm_name': vmname,
          'cloud_id': c.cid,
        }
        config = ConfigParser.RawConfigParser(defaults)

        try:
            fp = open(env, 'w')
            config.write(fp)
            fp.close()
        except:
            print("failed to write %s"%env, file=sys.stderr)
            raise Exception()

        d = env.rstrip('.env')+'.dir'
        s = env.rstrip('.env')+'.d'
        x = os.path.join(rcEnv.pathbin, "svcmgr")
        b = env.rstrip('.env')
        try:
            os.makedirs(d)
        except:
            pass
        try:
            os.symlink(d, s)
        except:
            pass
        try:
            os.symlink(x, b)
        except:
            pass

    def do_svcs_action(self, action, rid=None, tags=None, subsets=None):
        err = 0
        if self.options.parallel:
            from multiprocessing import Process
	    if rcEnv.sysname == "Windows":
                from multiprocessing import set_executable
                set_executable(os.path.join(sys.exec_prefix, 'pythonw.exe'))
            p = {}
        for s in self.svcs:
            if self.options.parallel:
                d = {
                  'action': action,
                  'rid': rid,
                  'tags': tags,
                  'subsets': subsets,
                  'waitlock': self.options.waitlock
                }
                p[s.svcname] = Process(target=self.service_action_worker,
                                       name='worker_'+s.svcname,
                                       args=[s],
                                       kwargs=d)
                p[s.svcname].start()
            else:
                try:
                    err += s.action(action, rid=rid, tags=tags, subsets=subsets, waitlock=self.options.waitlock)
                except s.exMonitorAction:
                    s.action('toc')
                except ex.excSignal:
                    break

        if self.options.parallel:
            for svcname in p:
                p[svcname].join()
                r = p[svcname].exitcode
                if r > 0:
                   # r is negative when p[svcname] is killed by signal.
                   # in this case, we don't want to decrement the err counter.
                   err += r

        return err

    def collector_api(self):
        if hasattr(self, "collector_api_cache"):
            return self.collector_api_cache
        import platform
        sysname, nodename, x, x, machine, x = platform.uname()
        try:
            import ConfigParser
        except ImportError:
            import configparser as ConfigParser
        config = ConfigParser.RawConfigParser({})
        config.read("/opt/opensvc/etc/node.conf")
        data = {}
        data["username"] = nodename
        data["password"] = config.get("node", "uuid")
        data["url"] = config.get("node", "dbopensvc").replace("/feed/default/call/xmlrpc", "/init/rest/api")
        self.collector_api_cache = data
        return self.collector_api_cache

    def collector_url(self):
        api = self.collector_api()
        s = "%s:%s@" % (api["username"], api["password"])
        url = api["url"].replace("https://", "https://"+s)
        url = url.replace("http://", "http://"+s)
        return url

    def collector_request(self, path):
        api = self.collector_api()
        url = api["url"]
        request = urllib2.Request(url+path)
        base64string = base64.encodestring('%s:%s' % (api["username"], api["password"])).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        return request

    def collector_rest_get(self, path):
        api = self.collector_api()
        request = self.collector_request(path)
        if api["url"].startswith("https"):
            import ssl
            context = ssl._create_unverified_context()
        else:
            raise ex.excError("refuse to submit auth tokens through a non-encrypted transport")
        try:
            f = urllib2.urlopen(request, context=context)
        except urllib2.HTTPError as e:
            try:
                err = json.loads(e.read())["error"]
                e = ex.excError(err)
            except:
                pass
            raise e
        import json
        data = json.loads(f.read())
        f.close()
        return data

    def collector_rest_get_to_file(self, path, fpath):
        api = self.collector_api()
        request = self.collector_request(path)
        if api["url"].startswith("https"):
            import ssl
            context = ssl._create_unverified_context()
        else:
            raise ex.excError("refuse to submit auth tokens through a non-encrypted transport")
        try:
            f = urllib2.urlopen(request, context=context)
        except urllib2.HTTPError as e:
            try:
                err = json.loads(e.read())["error"]
                e = ex.excError(err)
            except:
                pass
            raise e
        with open(fpath, 'wb') as df:
            for chunk in iter(lambda: f.read(4096), b""):
                df.write(chunk)
        f.close()

    def install_service_files(self, svcname):
        if rcEnv.sysname == 'Windows':
            return

        # install svcmgr link
        ls = os.path.join(rcEnv.pathetc, svcname)
        s = os.path.join(rcEnv.pathbin, 'svcmgr')
        if not os.path.exists(ls):
            os.symlink(s, ls)
        elif os.path.realpath(s) != os.path.realpath(ls):
            os.unlink(ls)
            os.symlink(s, ls)

    def pull(self, svcname):
        env = os.path.join(rcEnv.pathetc, svcname+'.env')
        data = self.collector_rest_get("/services/"+svcname+"?props=svc_envfile&meta=0")
        if "error" in data:
            self.log.error(data["error"])
            return 1
        if len(data["data"]) == 0:
            self.log.error("service not found on the collector")
            return 1
        if len(data["data"][0]["svc_envfile"]) == 0:
            self.log.error("service has an empty configuration")
            return 1
        with open(env, "w") as f:
            f.write(data["data"][0]["svc_envfile"].replace("\\n", "\n").replace("\\t", "\t"))
        self.log.info("%s pulled" % env)
        self.install_service_files(svcname)


if __name__ == "__main__" :
    for n in (Node,) :
        help(n)
