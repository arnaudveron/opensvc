from subprocess import *

repo_subdir = "depot"

def update(fpath):
    cmd = ['swinstall', '-x', 'downdate=true', '-x', 'mount_all_filesystems=false', '-s', fpath]
    print ' '.join(cmd)
    p = Popen(cmd)
    p.communicate()
    return p.returncode
