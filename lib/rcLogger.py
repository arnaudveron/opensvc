#
# Copyright (c) 2009 Christophe Varoqui <christophe.varoqui@free.fr>'
# Copyright (c) 2009 Cyril Galibern <cyril.galibern@free.fr>'
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
import sys
import os
import logging
import logging.handlers
from rcGlobalEnv import *

min_name_len = 8

def set_streamformatter(svcs):
    maxlen = get_max_name_len(svcs)
    streamformatter = logging.Formatter("%(levelname)-7s %(name)-"+str(maxlen)+"s %(message)s")
    for svc in svcs:
        handler = svc.log.handlers[1]
        handler.setFormatter(streamformatter)

def get_max_name_len(svcs):
    maxlen = min_name_len
    for svc in svcs:
        if svc.is_disabled():
            continue
        for r in svc.resources_by_id.values():
            if r is None:
                continue
            if r.is_disabled():
                continue
            l = len(r.log_label())
            if l > maxlen:
                maxlen = l
    return maxlen

def initLogger(name):
    log = logging.getLogger(name)
    if name in rcEnv.logging_initialized:
        return log

    """Common log formatter
    """
    fileformatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    streamformatter = logging.Formatter("%(levelname)-7s %(name)s %(message)s")

    """Common logfile with rotation
    """
    filehandler = logging.handlers.RotatingFileHandler(rcEnv.logfile,
                                                       maxBytes=5242880,
                                                       backupCount=5)
    filehandler.setFormatter(fileformatter)
    log.addHandler(filehandler)

    """Stdout logger
    """
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(streamformatter)
    log.addHandler(streamhandler)

    """ syslog
    """
    try:
        import ConfigParser
    except ImportError:
        import configparser as ConfigParser
    config = ConfigParser.RawConfigParser({})
    try:
        config.read("/opt/opensvc/etc/node.conf")
    except:
        pass
    try:
        facility = config.get("syslog", "facility")
    except:
        facility = "user"
    try:
        host = config.get("syslog", "host")
    except:
        host = None
    try:
        port = int(config.get("syslog", "port"))
    except:
        port = None
    address = None
    if host is None and port is None:
        if os.path.exists("/dev/log"):
            address = os.path.realpath("/dev/log")
        elif os.path.exists("/var/log/syslog"):
            address = os.path.realpath("/var/log/syslog")
    if address is None:
        if host is None:
            host = "localhost"
        if port is None:
            port = 514
        address = (host, port)

    syslogformatter = logging.Formatter("opensvc: %(name)s %(message)s")
    try:
        sysloghandler = logging.handlers.SysLogHandler(address=address, facility=facility)
        sysloghandler.setFormatter(syslogformatter)
        log.addHandler(sysloghandler)
    except Exception as e:
        pass

    if '--debug' in sys.argv:
            rcEnv.loglevel = logging.DEBUG
            log.setLevel(logging.DEBUG)
    elif '--warn' in sys.argv:
            rcEnv.loglevel = logging.WARNING
            log.setLevel(logging.WARNING)
    elif '--error' in sys.argv:
            rcEnv.loglevel = logging.ERROR
            log.setLevel(logging.ERROR)
    else:
            rcEnv.loglevel = logging.INFO
            log.setLevel(logging.INFO)

    rcEnv.logging_initialized.append(name)
    return log
