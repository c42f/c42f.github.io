Title: Windows develement from linux
Slug: windows-gpu-dev-from-linux-kvm
Date: 2018-07-16
Summary: Windows development with KVM from the comfort of your linux host
Status: draft

# Notes on windows VM setup with KVM and libvirt

Occasionally I've got to do some windows development using proprietary
development environments (for example, for Siemens MRI scanner hardware). On
the other hand, I vastly prefer software development on a linux system and my
other software can be developed there without an issue. A traditional solution
is to dual-boot but this makes the cost of switching environments really high
and I find that one system ends up abandoned fairly quickly.

So here's some notes on how I set this up with KVM and libvirt (with QEMU
backend), and got a usable windows guest development environment running. I'm
running ubuntu 18.04 as the host system, but the setup should apply to most
linux distributions.

The physical hardware is a 2018 Dell XPS 15 9560 laptop which has the Intel
VT-x hardware virtualization support (`grep --color vmx /proc/cpuinfo`). It's
got the usual intel graphics, as well as a discrete NVidia GTX 1050 GPU,
currently disabled to avoid the extra power draw. I originally chose KVM
because of the potential to do GPU passthrough though this turned out to be
rather difficult on a laptop. My experience has been that KVM with virt-manager
is less beginner friendly but cleaner overall than using virtualbox for the
same thing.

## Hardware setup using virt-manager

Firstly, install the `virt-manager` package which provides a GUI which will let
you configure VM hardware interactively, gives a list of VMs and a graphical
console for each VM. Let's create a VM with the `virt-manager` GUI:

* Click `File->New Virtual Machine`.
* When starting from scratch you'll probably want "Local install media" to
  point the system at a Windows 10 ISO or physical CDROM media. If
  `virt-manager` doesn't autodetect the OS on the ISO correctly, you may want
  to tell it which OS you're going to install so that some hardware defaults
  are sensibly populated.
* Configure the next few pages of simple settings as you please until you get
  to "Create a new virtual machine".  To set up some additional hardware,
  you'll want to click the "Customize configuration before install" checkbox
  before proceeding.

Now set up the hardware to use VirtIO drivers where possible as these allow
more direct and faster access to the host resources.  The hardware details
GUI gives access to many options - we'll be modifying some of the (virtualized)
hardware, and also adding a few new devices. In the windows guest OS, this
hardware will appear in the Device Manager and we'll need to install extra
drivers in some cases.

* Modify the **Disk** to use the VirtIO driver in `Advanced options->Disk bus`.
* Modify the **NIC** device to use the VirtIO driver. This gives good
  performance, just note that you'll need to install the NetKVM driver as
  described below.
* Create an additional new IDE CDROM with `Add Hardware->Storage->Select custom
  storage->CDROM device` so that we have access to the VirtIO
  drivers during the install. As of this writing, ubuntu seems to provide
  ancient VirtIO drivers, so you should download the
  [iso with RedHat virtio-win drivers](https://docs.fedoraproject.org/en-US/quick-docs/creating-windows-virtual-machines-using-virtio-drivers/index.html)
  instead and attach this to the new CDROM device. Note that the other CDROM
  device needs to be free so that it can be used for the windows install media.
* For a good experience sharing the mouse with the host, an emulated tablet is
  better than a mouse, as it sends absolute rather than relative coordinates.
  This will probably be added by default, but you can add it manually by adding
  an "EvTouch USB graphics tablet" input device.
* For copy/paste integration and other guest agent interaction, you'll need a
  VirtIO serial controller and guest agent channel.
  Add a VirtIO serial controller with `Add Hardware->Controller->VirtIO Serial`.
  Add a guest agent channel with `Add Hardware->Channel->Name="org.qemu.guest_agent.0"`.
* For installation, verify the boot order in `Boot Options`. For the first
  boot, you should boot into the install media - probably `IDE CDROM 1` or some
  such. On subsequent reboots you'll want the `VirtIO Disk 1` so that you boot
  the installed OS. If you encounter the UEFI Boot console, you've probably got
  the order wrong here and are trying to boot into the disk without an OS
  installed.

## Windows installation; virtio drivers and guest agent tools

Now that the hardware is configured, you can begin the software installation.
The one tricky part is getting the VirtIO disk driver installed up front so
that windows can see the virtual hard drive. You may need to click the
"Advanced" install button or some such thing to get to the "Load driver"
button. If you attached the virtio-win driver disk as suggested above, the
drivers can be manually selected during setup from path like
`E:\viostor\w10\amd64`. After installing these, you'll be able to see the
virtual hard drive and you can just click through all the usual windows setup
guff. 

After finishing the windows installation, there will be a few additional VirtIO
drivers and guest agents to install. First, install the NetKVM driver to get
your network working by opening `Device Manager` and selecting `Other
devices->Ethernet Controller`. Right click this and select `Update
Driver->Browse my computer for Drivers`, followed by entering the location of
the NetKVM directory on the virtio-win CDROM.

For all other drivers and tools, the fastest way to get things working is to
install the "windows guest tools" from <https://www.spice-space.org/download.html>.
This includes
* The SPICE guest agent for desktop integration of copy/paste and window resizing.
* The QEMU guest agent to allow graceful shutdown of the guest from the host.
* Various drivers (memory Balloon driver, virtio serial controller)

In the event you've got to install other drivers and agents manually, the
procedure is the same as the NetKVM one above: Open the windows Device Manager,
and select a device from the tree.  The unknown VirtIO devices appear under
"Other devices". You want to right click these and select `Update
Driver->Browse my computer for Drivers`, entering the location of the CDROM
with the virtio-win driver disk for example,
* The Balloon driver, which lets the VM obtain addtional host memory (Balloon)
* The serial controller (vioserial)
* The VirtIO disk driver (viostor)
* The qemu guest agent can be found in the virtio-win disk under
  libvirt guest-agent.  Running the installer should result in a new windows
  service "QEMU guest agent" visible in the "Services" application.
* Unfortunately the SPICE agent isn't available on the virtio-win driver disk,
  so you'll have to get the installer for this from elsewhere to get
  copy/paste/resizing working.

Once you've installed the drivers, restart the machine, and select the
`View->Scale Display->Auto Resize VM with window` checkbox in the virt-manager
menu. The VM screen should now resize with your host window. If not, you might
have forgotten to install the SPICE guest or the spice hardware channel is not
working.

## Snapshot the clean state

At this point it's worth creating a snapshot of the clean functioning system.
It's probably a good idea to install all windows updates and perhaps some basic
software like a [modern web browser](www.google.com/chrome). Other than that
keep it clean and minimal.

When you're ready to make a snapshot, shut down the VM. In the `virt-manager`
interface, select `View->Snapshots` and click the "Create new snapshot" button
labelled with a `+` in the snapshots list.

## Windows package management tools

If you're a linux dev you might not know that there's finally package managers
for windows with a good range of dev tools. Use one. For example,
[chocolatey](https://chocolatey.org/) will save you heaps of time and sanity.

## File sharing between linux hosts and windows guests

Firstly, note there are several attractive and obvious options which **do not
work** when the guest VM is windows:

* You *can't* just add the obvious "Filesystem" device as
  [virtfs/9p isn't yet supported](https://github.com/virtio-win/kvm-guest-drivers-windows/issues/126).
  Signs are that it's also poorly supported on linux guests. Just forget it.
* Folder sharing [via SPICE webdav](https://www.spice-space.org/spice-user-manual.html#_folder_sharing)
  does work, but only seems good for one-off ad hoc sharing. My short
  experience suggests that it's completely dependent on the SPICE viewer, so
  isn't a viable option for reliable VM setup.
* QEMU's `netdev user,smb` support *seems* to be a good option because it
  encapsulates the local file sharing along with the VM config. But it turns
  out to be [extrodinarily difficult to debug](#qemu-netdev-usersmb) and more
  effort it's worth.

### Setting up samba on the host

So screw it, just manually set up a samba server on the host machine. For
security you will want to restrict the network interfaces the samba server can
bind to. By default, virt-manager creates a virtual bridge called `virbr0` on
the host and connects the VMs to that, so you'll need something like the
following in your samba config file `/etc/samba/smb.conf`:

```
# Only allow local VMs to see the samba server
interfaces = virbr0
bind interfaces only = yes
```

While you're at it, you may want to comment out the sections dealing with
printers and add the following to disable them completely:

```
# Disable printers
load printers = no
printing = bsd
printcap name = /dev/null
disable spoolss = yes
```

Shared samba folder setup is pretty standard and there's examples in
`smb.conf`. You might share your home directory, or if you don't trust the VMs
as much as the host set up a special shared directory as follows:

```
# Share for all local VMs
[vmshare]
    path = /home/$your_user_name/vmshare
    writable = yes
    browseable = yes
```

It's sometimes necessary to be able to execute files which you've generated on
the samba share. For this you may need to turn off a security feature as
[described](https://wiki.samba.org/index.php/Setting_up_a_Share_Using_POSIX_ACLs#Making_Files_Executable)
on the samba wiki:

```
# Allow users to execute all files on the share
acl allow execute always = True
```

Naturally you'll also need to restart smbd after these changes — on ubuntu with
systemd use `sudo systemctl restart smbd`. You'll also need to add a samba
password to your user with `sudo smbpasswd -a $your_user_name`


### Mapping network drives on the guest

Once all this is set up, map the network drive in the usual way on the guest
side to avoid problems with ancient programs like `cmd` which don't understand
UNC paths. A couple of traps to avoid:

* Be sure to use the samba host name as the windows domain when mapping the
  network drive or windows
  [won't remember your credentials](https://superuser.com/questions/309570/windows-refuses-to-remember-network-share-credentials)
  across a reboot.
* The administrator account won't be able to see the mapped drive unless you
  set a new registry key
  `HKEY_LOCAL_MACHINE/SOFTWARE/Microsoft/Windows/CurrentVersion/Policies/System/EnableLinkedConnections`
  DWORD to `1`. See [here](http://www.winability.com/how-to-make-elevated-programs-recognize-network-drives/)
  for additional detail.

## Appendix — Other setup which I may revisit eventually

Here's a few notes on things which didn't work out but which seemed worth
recording.

### GPU passthrough

If you need to develop GPU code in a windows VM things are generally bad.
However, with two GPUs, KVM can pass one piece of GPU hardware directly through
to a VM, leaving the other for the host system. This should be a really great
system for productive cross platform GPU development on the right hardware as
of 2018. Sadly it's early days for getting this to work on *laptop* GPU
hardware such as is contained in the XPS-15. Here's some notes and links I
collected before I gave up on this for now:

GPU passthrough allows a physical GPU to be used directly by a virtual machine.
[Several](https://gist.github.com/Misairu-G/616f7b2756c488148b7309addc940b28)
[people](https://davidyat.es/2016/09/08/gpu-passthrough/)
[have](https://taxes.moe/2017/07/08/linux-and-windows-running-simultaneously-with-gpu-passthrough/)
set this kind of thing up, often to run games in windows with a linux host.
My physical hardware is a 2018 Dell XPS 15 (9560) laptop which has the usual
intel graphics, as well as a discrete NVidia GTX 1050 GPU. This is a GPU
without a physical output; ie a muxless card, so
<https://github.com/jscinoz/optimus-vfio-docs> probably applies.

To allow GPU passthrough, UEFI firmware should be selected on the **Overview**
page during VM hardware setup instead of BIOS, at least according to
[this article](https://taxes.moe/2017/07/08/linux-and-windows-running-simultaneously-with-gpu-passthrough/).
On ubuntu can open UEFI firmware implementation is provided by the
`ovmf` package which must be installed before restarting the virtio service
with `systemctl restart libvirt-bin.service`. Note that this unfortunately
has the side effect of breaking VM snapshots as they're
[not yet implemented with UEFI](https://www.redhat.com/archives/virt-tools-list/2017-September/msg00008.html).

### QEMU netdev user,smb

QEMU's netdev user,smb support seems to be a good option because it
encapsulates the local file sharing along with the VM config. I tried hard to
get this working with an ubuntu 18.04 host, but eventually it proved more
difficult than worthwhile. Nevertheless, here's some things I found out.

I followed the [instructions here](https://unix.stackexchange.com/questions/188301/how-to-set-up-samba-sharing-with-libvirtd)
to add the following to the vm config using `virsh edit`:

```
<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
...
<qemu:commandline>
  <qemu:arg value='-netdev'/>
  <qemu:arg value='user,smb=/home/$your_user_name/win10,id=smb0,smbserver=10.0.2.4'/>
  <qemu:arg value='-device'/>
  <qemu:arg value='virtio-net-pci,netdev=smb0'/>
</qemu:commandline>
</domain>
```

Note that we can't do this directly in virt-manager, because it's not
[not natively supported by libvirt](https://bugzilla.redhat.com/show_bug.cgi?id=1459995).

With this solution, we've also got to disable some apparmor security to
allow samba to access /tmp and exec smbd. The simple way to do this is to
diable apparmor for libvirtd completely using `sudo aa-disable libvirtd`.
(Note that you should think twice about this if you're going to run other
untrusted VMs on the same machine!)

If I remember correctly, the above gives you a read only share to the guest.
However, I eventually gave up on this because it was so difficult to debug.

