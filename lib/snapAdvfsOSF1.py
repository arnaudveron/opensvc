import os
from rcUtilities import justcall, protected_mount
import rcExceptions as ex
import snap
import rcAdvfs
from rcMountsOSF1 import Mounts
from rcGlobalEnv import rcEnv

class Snap(snap.Snap):
    """Defines a snap object with ZFS
    """

    def snapcreate(self, m):
        """ create a snapshot for m
        add self.snaps[m] with
            dict(snapinfo key val)
        """
        dom, fset = m.device.split('#')
        o = rcAdvfs.Fdmns()
        try:
            d = o.get_fdmn(dom)
        except rcAdvfs.ExInit:
            raise ex.syncNotSnapable
        if fset not in d.fsets:
            raise ex.syncNotSnapable
        clonefset = fset +'@osvc_sync'
        mountPoint = m.mountPoint
        snapMountPoint = os.path.join(rcEnv.pathtmp, 'clonefset/%s/%s/osvc_sync'%(m.svc.svcname,mountPoint))
        snapMountPoint = os.path.normpath(snapMountPoint)
        if not os.path.exists(snapMountPoint):
            try:
                os.makedirs(snapMountPoint)
                self.log.info('create directory %s'%snapMountPoint)
            except:
                self.log.error('failed to create directory %s'%snapMountPoint)
                raise ex.syncSnapCreateError
        clonedev = '#'.join((dom, clonefset))
        if Mounts().has_mount(clonedev, snapMountPoint):
            cmd = ['fuser', '-kcv', snapMountPoint]
            (ret, out, err) = self.vcall(cmd, err_to_info=True)
            cmd = ['umount', snapMountPoint]
            (ret, out, err) = self.vcall(cmd)
            if ret != 0:
                raise ex.excError
        if clonefset in d.fsets:
            (ret, buff, err) = self.vcall(['rmfset', '-f', dom, clonefset])
            if ret != 0:
                raise ex.syncSnapDestroyError
        (ret, buff, err) = self.vcall(['clonefset', dom, fset, clonefset])
        if ret != 0:
            raise ex.syncSnapCreateError
        (ret, buff, err) = self.vcall(['mount', '-t', 'advfs', clonedev, snapMountPoint])
        if ret != 0:
            raise ex.syncSnapCreateError
        self.snaps[mountPoint]={'snap_mnt' : snapMountPoint, \
                                'snapdev' : clonedev }

    def snapdestroykey(self, snap_key):
        """ destroy a snapshot for a mountPoint
        """
        clonedev = self.snaps[snap_key]['snapdev']
        dom, clonefset = clonedev.split('#')
        o = rcAdvfs.Fdmns()
        try:
            d = o.get_fdmn(dom)
        except rcAdvfs.ExInit:
            raise ex.syncSnapDestroyError
        if clonefset not in d.fsets:
            return

        if protected_mount(self.snaps[snap_key]['snap_mnt']):
            self.log.error("the clone fset is no longer mounted in %s. panic."%self.snaps[snap_key]['snap_mnt'])
            raise ex.excError
        cmd = ['fuser', '-kcv', self.snaps[snap_key]['snap_mnt']]
        (ret, out, err) = self.vcall(cmd, err_to_info=True)
        cmd = ['umount', self.snaps[snap_key]['snap_mnt']]
        (ret, out, err) = self.vcall(cmd)
        if ret != 0:
            raise ex.excError

        (ret, buff, err) = self.vcall(['rmfset', '-f', dom, clonefset])
        if ret != 0:
            raise ex.syncSnapDestroyError
