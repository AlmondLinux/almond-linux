# Building and testing AALDM on a Windows PC

This guide sets up a 64-bit Intel/AMD Windows PC to **build** the Almond Linux AALDM ISO and **test** it in a virtual machine. Nothing here touches Windows itself or the PC's own disks: all Linux work happens inside VirtualBox virtual machines.

Status: written 2026-10-14, **not yet followed end-to-end**. If a step does not match what you see, stop and report it rather than improvising.

You will need about **100 GB free disk space**, 1–2 hours the first time, and an internet connection (Debian downloads roughly 1–2 GB of packages during the first build).

---

## Part 1 — Install VirtualBox (once)

1. On the PC, download the latest **VirtualBox 7.x for Windows hosts** from the official site: <https://www.virtualbox.org/wiki/Downloads>.
2. Install it with the default options.
3. If Windows features *Hyper-V*, *Virtual Machine Platform* or *WSL2* are on, VirtualBox still works, just slower. Leave them as they are for now.

## Part 2 — Create the Debian 13 build VM (once)

1. Download the **Debian 13 "trixie" netinst ISO for amd64** from <https://www.debian.org/distrib/netinst> (file name like `debian-13.x.y-amd64-netinst.iso`, about 650–800 MB).
2. Check the download is genuine: in the same folder on the Debian mirror, open `SHA256SUMS`. In Windows PowerShell run
   ```powershell
   Get-FileHash .\debian-13*-amd64-netinst.iso -Algorithm SHA256
   ```
   The hash must match the line for your file exactly. If it does not, delete the file and download again.
3. In VirtualBox: **New** →
   - Name: `almond-build`
   - ISO image: the Debian netinst ISO
   - Type: Linux, Version: Debian (64-bit)
   - **Skip unattended installation** (tick it)
   - Memory: **8192 MB**, Processors: **1** (4 froze the Debian install under the Windows hypervisor in the first test; 1 worked: [test results](../tests/results/2026-10-17-vm/RESULTS.md), Problem 1)
   - Hard disk: **80 GB**, dynamically allocated
4. Start the VM and install Debian:
   - Choose **Install** (text mode is fine).
   - Hostname `almond-build`, any user name and a password you will remember.
   - Partitioning: **Guided – use entire disk** (this is the *virtual* disk inside the VM, not your PC's disk).
   - Software selection: untick every desktop; tick only **SSH server** and **standard system utilities**.
5. Reboot, log in, and give your user sudo rights (if the installer did not):
   ```sh
   su -
   apt install sudo
   usermod -aG sudo YOUR_USER_NAME
   exit
   ```
   Log out and in again.

## Part 3 — Build the ISO (every time you want a fresh build)

> **Prerequisite: the AALDM build configuration must be on GitHub.** This part clones <https://github.com/AlmondLinux/almond-linux>, so the AALDM files (`auto/config`, `config/package-lists/aaldm.list.chroot`, the hooks and `scripts/build.sh`) must have been pushed there first. After cloning, check:
>
> ```sh
> ls config/package-lists/aaldm.list.chroot
> ```
>
> If that file is missing, **stop**: the clone is an older version of the repository and would not build AALDM. Report it instead of building or changing files.

Inside the `almond-build` VM:

```sh
sudo apt update
sudo apt install live-build debootstrap xorriso squashfs-tools \
  grub-efi-amd64-bin grub-pc-bin syslinux isolinux mtools dosfstools \
  git ca-certificates
git clone https://github.com/AlmondLinux/almond-linux.git
cd almond-linux
if [ -f config/package-lists/aaldm.list.chroot ]; then
  sudo ./scripts/build.sh
else
  echo 'STOP: no AALDM configuration in this clone (see the prerequisite above).'
fi
```

- The build takes a while (often 20–60 minutes the first time).
- It writes everything into `build/attempt.XXXXXX/`: the ISO, `SHA256SUMS`, logs, build-tool versions and the package list.
- If it fails, **do not change any options to force it through**. Keep the whole `build/attempt.XXXXXX/` folder and report the last ~80 lines the script prints.

To update later: `cd almond-linux && git pull`, check again that `config/package-lists/aaldm.list.chroot` exists, then run the build again. Old attempts stay until you delete them yourself.

### Getting the ISO out of the VM

The simplest way is a VirtualBox **shared folder**:

1. VM **Settings → Shared Folders → +**: pick a Windows folder (e.g. `C:\AlmondISO`), name `almondiso`, tick **Auto-mount** and **Make Permanent**.
2. Install VirtualBox's Guest Additions in the VM (Debian's main archive does not package them): VirtualBox menu **Devices → Insert Guest Additions CD image**, then in the VM:
   ```sh
   sudo apt install build-essential dkms linux-headers-amd64
   sudo mount /dev/cdrom /mnt && sudo sh /mnt/VBoxLinuxAdditions.run; sudo umount /mnt
   sudo usermod -aG vboxsf $USER   # then reboot the VM
   ```
3. Copy the results: `cp build/attempt.*/live-image-amd64.hybrid.iso build/attempt.*/SHA256SUMS /media/sf_almondiso/`

(If shared folders give trouble, `scp` from Windows PowerShell also works because the VM has an SSH server.)

## Part 4 — Boot-test the ISO in a second VM

1. VirtualBox **New** → Name `almond-test`, ISO image = the Almond ISO, Type Linux / Debian (64-bit), **Skip unattended installation**.
2. Memory **2048 MB**, Processors **2**. **Do not create a hard disk** (choose "Do not add a virtual hard disk").
3. Test **both** firmware types, one after the other:
   - **Legacy BIOS:** Settings → System → *Enable EFI* **off**.
   - **UEFI:** Settings → System → *Enable EFI* **on**.
4. Run the acceptance checks from `docs/BUILD.md` and write down what actually happened, including failures.
5. Memory test: after the desktop appears, wait 2 minutes without touching anything, then open a terminal and run
   ```sh
   sudo sh /usr/share/almond/tests/measure-memory.sh -w 120 > ~/memory-2gb.txt
   ```
   The script waits another 120 seconds itself before measuring, the same method as `docs/BUILD.md` and `docs/PERFORMANCE.md`. (If that path does not exist in the image, copy `tests/measure-memory.sh` from the repository into the VM.) Repeat with the VM set to **1024 MB** RAM and save `memory-1gb.txt`.

## Part 5 — Send the results back

Collect into one folder on Windows:

- `SHA256SUMS`, the `*.packages` file and `build-tool-versions.txt` from the build attempt
- the last 80 lines of `build.log` if anything failed
- `memory-2gb.txt`, `memory-1gb.txt`
- a few screenshots of the desktop and the launcher (VirtualBox: **View → Take Screenshot**)
- short notes: BIOS boot OK/failed, UEFI boot OK/failed, what did not work

Then copy the results to the computer you report from, for example with a shared folder, `scp` or a file-transfer tool, and attach them to the report. These results are what allows the website and roadmap to say anything was "Tested". Until then everything stays "Implemented (source exists, untested)".

---

## Later: the Dell OptiPlex 390 (second-hand PC)

The OptiPlex 390 is a second-hand PC whose internal disk may still hold someone else's data. Until that disk has been wiped **with the owner's explicit permission**:

- Boot Almond **only from a USB stick**. Write the ISO to a USB stick on Windows with **Rufus** (choose *DD image mode* when asked) or **balenaEtcher**. This erases the *USB stick*, nothing else.
- On the OptiPlex press **F12** at power-on for the one-time boot menu and pick the USB stick (try both the UEFI and the Legacy entry if both appear).
- In the live session, **never open, mount, browse or read the internal drive**, even if it appears in the file manager's Devices list. Check with `findmnt` and `lsblk -f` that it has no mount point (details: the OptiPlex test plan in [BUILD.md](BUILD.md)). Do not run any installer.
- Measure memory exactly as in Part 4 and send the report the same way.
