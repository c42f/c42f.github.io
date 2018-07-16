Title: Windows develement from linux
Slug: windows-gpu-dev-from-linux-kvm
Date: 2018-07-16
Summary: Windows development from the comfort of your linux host
Status: draft

# Notes on windows VM setup with KVM and libvirt

I've got to do some windows development involving 3D graphics, so I need a
windows development environment with a proper GPU. On the other hand, I vastly
prefer software development on a linux system and a portion of my software can
be developed there without an issue. A traditional solution is a dual-boot
system but I find the wasted time of rebooting and restarting applications is
far too high with dual-boot and one system ends up abandoned fairly quickly.

Enter virtualization with KVM and GPU passthrough! This allows a physical GPU
to be used directly by a virtual machine.
[Several](https://gist.github.com/Misairu-G/616f7b2756c488148b7309addc940b28)
[people](https://davidyat.es/2016/09/08/gpu-passthrough/)
[have](https://taxes.moe/2017/07/08/linux-and-windows-running-simultaneously-with-gpu-passthrough/)
set this kind of thing up, often to run games in windows with a linux host.
Below I've got some notes on how I've used it to get a windows VM with GPU
enabled development environment. My physical hardware is a 2018 Dell XPS 15
(9560) laptop which has the usual intel graphics, as well as a discrete NVidia
GTX 1050 GPU. This is a GPU without a physical output; ie a muxless card, so
<https://github.com/jscinoz/optimus-vfio-docs> probably applies.

Anyway, here's some notes on how I set this up and got a usable windows guest
development environment running. I assume you're running ubuntu with KVM as the
host system.

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

* To allow GPU passthrough, UEFI firmware should be selected on the
  **Overview** page instead of BIOS, at least according to
  [this article](https://taxes.moe/2017/07/08/linux-and-windows-running-simultaneously-with-gpu-passthrough/).
  On ubuntu the open OVMF firmware implementation is provided by the
  `ovmf` package which must be installed before restarting the virtio service
  with `systemctl restart libvirt-bin.service`. Note that this unfortunately
  has the side effect of breaking VM snapshots as they're
  [not yet implemented with UEFI](https://www.redhat.com/archives/virt-tools-list/2017-September/msg00008.html).
* Modify the **Disk** to use the VirtIO driver in `Advanced options->Disk bus`.
* Modify the **NIC** device to use the VirtIO driver.
* Create an additional new IDE CDROM with `Add Hardware->Storage->Select custom
  storage->CDROM device` so that we have access to the VirtIO
  drivers during the install. As of this writing, ubuntu seems to provide
  ancient VirtIO drivers, so you should download the
  [iso with RedHat virtio-win drivers](https://docs.fedoraproject.org/quick-docs/en-US/creating-windows-virtual-machines-using-virtio-drivers.html#virtio-win-direct-downloads)
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

Now that all the above is configured, you can begin the installation. Just
click through all the usual windows guff. The one tricky part is getting the
VirtIO disk driver installed so that windows can see the virtual hard drive. If
you attached the virtio-win driver disk as suggested above, these can be
manually selected during setup from path like `E:\viostor\w10\amd64`. After
installing these, you'll be able to see the virtual hard drive.

After finishing the installation, there will be a few additional VirtIO drivers
and guest agents to install.  The fastest way to get all this working is to
install the "windows guest tools" from
<https://www.spice-space.org/download.html>.
This includes
* The SPICE guest agent for copy/paste and window resizing
* The QEMU guest agent for proper remote shutdown of the guest.
* Various drivers

In the event you've got to install drivers and agents manually, open the
windows Device Manager, and select a device from the tree.  The unknown VirtIO
devices appear under "Other devices". You want to right click these and select
`Update Driver->Browse my computer for Drivers`, entering the location of the
CDROM with the virtio-win driver disk for example,
* The network driver (NetKVM)
* The Balloon driver, which lets the VM obtain addtional host memory (Balloon)
* The serial controller (vioserial)
* The VirtIO disk driver (viostor)
* The qemu guest agent can be found in the virtio-win disk under
  libvirt guest-agent.  Running the installer should result in a new windows
  service "QEMU guest agent" visible in the "Services" application.
* Unfortunately the SPICE agent isn't available on this disk, so you'll have to
  get the installer for this from elsewhere to get copy/paste/resizing working.

## Folder sharing

QEMU's netdev user,smb support seems to be a good option because it
encapsulates the local file sharing along with the VM config. I followed the
[instructions here](https://unix.stackexchange.com/questions/188301/how-to-set-up-samba-sharing-with-libvirtd)
to add the following to the vm config using `virsh edit`:

```
<domain type='kvm' xmlns:qemu='http://libvirt.org/schemas/domain/qemu/1.0'>
...
<qemu:commandline>
  <qemu:arg value='-netdev'/>
  <qemu:arg value='user,smb=/home/tcfoster/win10,id=smb0,smbserver=10.0.2.4'/>
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

One obvious alternative to the above is to set up a samba server manually,
though this will need to be maintained separately to the VM config.

Note that there are several attractive and obvious alternatives which **do not
work** when the guest VM is windows:

* You *can't* just add the obvious "Filesystem" device as
  [virtfs/9p isn't yet supported](https://github.com/virtio-win/kvm-guest-drivers-windows/issues/126).
* Folder sharing [via SPICE](https://www.spice-space.org/spice-user-manual.html#_folder_sharing)
  does work, but only seems good for one-off ad hoc sharing. My short
  experience suggests that it's completely dependent on the SPICE viewer, so
  isn't really a viable option for reliable VM setup.

## GPU setup

### Kernel options

<https://www.ovirt.org/documentation/install-guide/appe-Configuring_a_Hypervisor_Host_for_PCI_Passthrough>

## Additional links

* [The funtoo windows kvm guide](https://www.funtoo.org/Windows_10_Virtualization_with_KVM)
  covers some of the same ground, but using `qemu` directly.

