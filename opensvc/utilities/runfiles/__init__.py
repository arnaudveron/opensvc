import os
from env import Env

def has_running(run_dir, log=None, cleanup=False):
    try:
        return [info for info in (is_valid(os.path.join(run_dir, f), log=log, cleanup=cleanup) for f in os.listdir(run_dir)) if info]
    except FileNotFoundError:
        return []

def get_sid(run_file):
    try:
        with open(run_file, 'r') as f:
            sid = f.read().strip()
            if sid:
                return sid
            return "unknown"
    except FileNotFoundError:
        return "unknown"

def is_valid(run_file, log=None, cleanup=False):
    pid = os.path.basename(run_file)

    def do_cleanup(reason):
        if not cleanup:
            return
        if log:
            log.info("clean up stale run file (%s)", reason)
        try:
            os.unlink(run_file)
        except FileNotFoundError as e:
            pass
        except Exception as e:
            if log:
                log.warn(e)

    if str(os.getpid()) == pid:
        return { "pid": int(pid), "session_id": Env.session_uuid }

    try:
        run_file_mtime = os.path.getmtime(run_file)
    except FileNotFoundError:
        return False

    try:
        proc_pid_mtime = os.path.getmtime("/proc/"+pid)
    except FileNotFoundError:
        do_cleanup("proc %s does not run" % pid)
        return False

    if proc_pid_mtime <= run_file_mtime:
        return { "pid": int(pid), "session_id": get_sid(run_file) }

    do_cleanup("proc %s is not the one that created %s" % (pid, run_file))
    return False

def count(run_dir, log=None, cleanup=False):
    try:
        return sum(1 for entry in os.listdir(run_dir) if is_valid(os.path.join(run_dir, entry), log=log, cleanup=cleanup))
    except OSError:
        return 0

