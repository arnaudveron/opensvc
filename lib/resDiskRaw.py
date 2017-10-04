import resDisk
import os
import rcStatus
import re
import pwd
import grp
import stat
import sys
import glob
import rcExceptions as ex
from rcUtilities import which, is_string, lazy

class Disk(resDisk.Disk):
    def __init__(self,
                 rid=None,
                 devs=set(),
                 user=None,
                 group=None,
                 perm=None,
                 create_char_devices=False,
                 **kwargs):
        resDisk.Disk.__init__(self,
                          rid=rid,
                          name="raw",
                          type='disk.raw',
                          **kwargs)

        self.label = "raw"
        self.user = user
        self.group = group
        self.perm = perm
        self.create_char_devices = create_char_devices
        self.original_devs = devs

        self.devs = set()
        self.devs_not_found = set()
        self.dst_devs_not_found = set()
        self.major_minor_errs = set()
        self.devs_map = {}

    def reload_config(self):
        """
        The dev parameter can use exposed_devs reference that were not
        resolvable at build time, as the ressource exposing can be down.
        """
        self.svc.ref_cache = {}
        self.clear_caches()
        self.devs = set()
        self.original_devs = self.conf_get('devs')
        try:
            zone = self.conf_get('zone')
        except ex.OptNotFound as exc:
            zone = exc.default
        if zone is not None:
            self.original_devs = set([dev.replace(":", ":<%s>" % zone) for dev in self.original_devs])

    def clear_caches(self):
        pass

    def verify_dev(self, path):
        # os specific plug
        return True

    def info(self):
        self.validate_devs()
        data = []
        if self.create_char_devices:
            data += [["create_char_devices", str(self.create_char_devices)]]
        if self.user:
            data += [["user", str(self.user)]]
        if self.group:
            data += [["group", str(self.group)]]
        if self.perm:
            data += [["perm", str(self.perm)]]
        for dev in self.devs:
            if dev in self.devs_map:
                data += [["dev", dev+":"+self.devs_map[dev]]]
            else:
                data += [["dev", dev]]
        return self.fmt_info(data)

    def subst_container_root(self, path):
        m = re.match("<(\w+)>", path)
        if m is None:
            return path
        container_name = m.group(1)
        for r in self.svc.get_resources("container"):
            if hasattr(r, "name") and r.name == container_name:
                if hasattr(r, "get_zonepath"):
                    # zone
                    container_root = r.get_zonepath()
                elif hasattr(r, "get_rootfs"):
                    # lxc
                    container_root = r.get_rootfs()
                else:
                    return path
                path = re.sub("<\w+>", container_root, path)
                break
        return path

    def validate_devs(self):
        self.devs = set()
        self.devs_not_found = set()
        self.dst_devs_not_found = set()
        for dev in self.original_devs:
            if ":" in dev:
                try:
                    src, dst = dev.split(":")
                except:
                    continue
                if not os.path.exists(src) or not self.verify_dev(src):
                    self.devs_not_found.add(src)
                    continue
                dst = self.subst_container_root(dst)
                if not os.path.exists(dst):
                    self.dst_devs_not_found.add(dst)
                self.devs_map[src] = dst
                self.devs.add(src)
                continue
            l = set(glob.glob(dev))
            if len(l) > 0:
                for _dev in l:
                    if not self.verify_dev(_dev):
                        continue
                    self.devs.add(_dev)
            else:
                self.devs_not_found.add(dev)

    def on_add(self):
        try:
            n = self.rid.split('#')[1]
        except:
            n = "0"
        self.name = self.svc.svcname+".raw"+n
        self.label = self.name

    @lazy
    def uid(self):
        uid = self.user
        if is_string(uid):
            try:
                info=pwd.getpwnam(uid)
                uid = info[2]
            except:
                pass
        return uid

    @lazy
    def gid(self):
        gid = self.group
        if is_string(gid):
            try:
                info=grp.getgrnam(gid)
                gid = info[2]
            except:
                pass
        return gid

    def check_uid(self, rdev, verbose=False):
        if not os.path.exists(rdev):
            return True
        if self.user is None:
            return True
        if self.uid is None:
            if verbose:
                self.status_log('user %s uid not found'%str(self.user))
            return False
        uid = os.stat(rdev).st_uid
        if uid != self.uid:
            if verbose:
                self.status_log('%s uid should be %s but is %d'%(rdev, str(self.uid), uid))
            return False
        return True

    def check_gid(self, rdev, verbose=False):
        if not os.path.exists(rdev):
            return True
        if self.group is None:
            return True
        if self.gid is None:
            if verbose:
                self.status_log('group %s gid not found'%str(self.group))
            return False
        gid = os.stat(rdev).st_gid
        if gid != self.gid:
            if verbose:
                self.status_log('%s gid should be %s but is %d'%(rdev, str(self.gid), gid))
            return False
        return True

    def check_perm(self, rdev, verbose=False):
        if not os.path.exists(rdev):
            return True
        try:
            perm = oct(stat.S_IMODE(os.stat(rdev).st_mode))
        except:
            self.log.error('%s can not stat file'%rdev)
            return False
        perm = str(perm).lstrip("0o").lstrip("0")
        if perm != str(self.perm):
            if verbose:
                self.status_log('%s perm should be %s but is %s'%(rdev, str(self.perm), perm))
            return False
        return True

    def check_dst(self, src, dst):
        if dst in self.major_minor_errs:
            self.major_minor_errs.remove(dst)
        if src is None or dst is None:
            return False
        if not os.path.exists(src) or not os.path.exists(dst):
            return False
        src_st = os.stat(src)
        dst_st = os.stat(dst)
        r = True
        if os.major(src_st.st_rdev) != os.major(dst_st.st_rdev) or \
           os.minor(src_st.st_rdev) != os.minor(dst_st.st_rdev):
            self.major_minor_errs.add(dst)
            r &= False
        return r

    def fix_ownership(self, path):
        self.fix_ownership_user(path)
        self.fix_ownership_group(path)

    def fix_ownership_user(self, path):
        if self.user is None:
            return
        if self.uid is None:
            raise ex.excError("user %s does not exist" % str(self.user))
        if not self.check_uid(path):
            self.vcall(['chown', str(self.uid), path])
        else:
            self.log.info("%s has correct user ownership (%s)"% (path, str(self.uid)))

    def fix_ownership_group(self, path):
        if self.group is None:
            return
        if self.gid is None:
            raise ex.excError("group %s does not exist" % str(self.group))
        if self.gid and not self.check_gid(path):
            self.vcall(['chgrp', str(self.gid), path])
        else:
            self.log.info("%s has correct group ownership (%s)"% (path, str(self.gid)))

    def fix_perms(self, path):
        if self.uid is None:
            return
        if not self.check_perm(path):
            self.vcall(['chmod', self.perm, path])
        else:
            self.log.info("%s has correct permissions (%s)"% (path, str(self.perm)))

    def mangle_devs_map(self):
        pass

    def has_it_char_devices(self):
        return True

    def has_it_devs_map(self):
        r = True
        if len(self.dst_devs_not_found) == len(self.devs_map):
            # all dst unlinked: report no error => down state
            r &= False
        elif len(self.dst_devs_not_found) > 0:
            self.status_log("%s dst devs not found"%', '.join(self.dst_devs_not_found))
            r &= False
        for src, dst in self.devs_map.items():
            r &= self.has_it_dev_map(src, dst)
        return r

    def has_it_dev_map(self, src, dst):
        r = True
        if not self.check_dst(src, dst):
            r &= False
        if not self.check_uid(dst, verbose=True):
            r &= False
        elif not self.check_gid(dst, verbose=True):
            r &= False
        elif not self.check_perm(dst, verbose=True):
            r &= False
        return r

    def has_it(self):
        """Returns True if all raw devices are present and correctly
           named
        """
        r = True
        if self.create_char_devices:
            r &= self.has_it_char_devices()
        if len(self.devs_map) > 0:
            r &= self.has_it_devs_map()
        if len(self.devs_not_found) > 0:
            status = self.svc.group_status(excluded_groups=set([
                "sync",
                "app",
                "disk",
                "hb"
            ]))
            msg = "%s not found"%', '.join(self.devs_not_found)
            if str(status["avail"]) not in ("up", "n/a"):
                self.status_log(msg, "info")
            else:
                self.status_log(msg, "warn")
            r &= False
        if len(self.major_minor_errs) > 0:
            self.status_log("%s have major:minor diff with their src" % ', '.join(sorted(list(self.major_minor_errs))))
            r &= False
        return r

    def is_up(self):
        """Returns True if the volume group is present and activated
        """
        return self.has_it()

    def _status(self, verbose=False):
        self.validate_devs()
        self.mangle_devs_map()
        r = self.is_up()
        if not self.create_char_devices and len(self.devs_map) == 0:
            return rcStatus.NA
        if r:
            return rcStatus.UP
        else:
            return rcStatus.DOWN

    def do_start(self):
        self.reload_config()
        self.validate_devs()
        self.can_rollback = True
        self.do_start_char_devices()
        self.mangle_devs_map()
        self.do_start_blocks()

    def do_start_block(self, src, dst):
        if src is not None:
            if not os.path.exists(src):
                raise ex.excError("src file %s does not exist" % src)
            d = os.path.dirname(dst)
            if not os.path.exists(d):
                self.log.info("create dir %s" % d)
                os.makedirs(d)
            if not os.path.exists(dst) or not self.check_dst(src, dst):
                self.do_create_dst(src, dst)
        self.fix_ownership(dst)
        self.fix_perms(dst)

    def do_create_dst(self, src, dst):
        if os.path.exists(dst):
            self.log.info("remove existing dst %s", dst)
            os.unlink(dst)
        src_st = os.stat(src)
        if stat.S_ISBLK(src_st.st_mode):
            t = "b"
        elif stat.S_ISCHR(src_st.st_mode):
            t = "c"
        else:
            raise ex.excError("%s is not a block nor a char device" % src)
        major = os.major(src_st.st_rdev)
        minor = os.minor(src_st.st_rdev)
        cmd = ["mknod", dst, t, str(major), str(minor)]
        ret, out, err = self.vcall(cmd)
        if ret != 0:
            raise ex.excError

    def do_start_blocks(self):
        if which("mknod") is None:
            raise ex.excError("mknod not found")
        for src, dst in self.devs_map.items():
            self.do_start_block(src, dst)

    def do_start_char_devices(self):
        pass

    def do_stop_char_devices(self):
        pass

    def do_stop(self):
        self.validate_devs()
        self.mangle_devs_map()
        self.do_stop_blocks()
        self.do_stop_char_devices()

    def do_stop_blocks(self):
        for src, dst in self.devs_map.items():
            self.do_stop_block(src, dst)

    def do_stop_block(self, src, dst):
        if src is None:
            # never unlink unmapped devs
            return
        if os.path.exists(dst):
            self.log.info("unlink %s" % dst)
            try:
                os.unlink(dst)
            except Exception as e:
                raise ex.excError(str(e))
        else:
            self.log.info("%s already unlinked" % dst)

    def sub_devs(self):
        return self.devs

