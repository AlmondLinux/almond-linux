#!/bin/sh
# measure-memory.sh - Almond Linux memory report.
# Status: Implemented (source exists, untested). Checked with `sh -n` and against a
# synthetic /proc tree on macOS; never run on a real Linux system yet.
#
# POSIX sh plus tools every Debian system has (awk, sort, head, uname, date).
# Run it as root so it can read every process (smaps_rollup is protected):
#   sudo sh measure-memory.sh [-w SECONDS] [-u USER] [-n COUNT] > report.txt
#   -w SECONDS  wait this long before measuring (the method uses 120)
#   -u USER     desktop session user (default: SUDO_USER, else the owner
#               of lxqt-session)
#   -n COUNT    rows in the process table (default 25)
# Method and how to read the numbers: docs/PERFORMANCE.md.
set -u

proc=${ALMOND_PROC:-/proc}           # alternative trees are for testing only
sys=${ALMOND_SYS:-/sys}
passwd_file=${ALMOND_PASSWD:-/etc/passwd}
os_release=${ALMOND_OS_RELEASE:-/etc/os-release}
top=25
wait_seconds=0
session_user=${SUDO_USER:-}

usage() {
  echo 'usage: measure-memory.sh [-w SECONDS] [-u USER] [-n COUNT]'
}

while getopts 'w:u:n:h' opt; do
  case "$opt" in
    w) wait_seconds=$OPTARG ;;
    u) session_user=$OPTARG ;;
    n) top=$OPTARG ;;
    h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
for number in "$top" "$wait_seconds"; do
  case "$number" in
    ''|*[!0-9]*) echo 'error: -n and -w need whole numbers' >&2; exit 2 ;;
  esac
done
if [ ! -r "$proc/meminfo" ]; then
  echo "error: cannot read $proc/meminfo; this script needs Linux." >&2
  exit 1
fi
if [ "$wait_seconds" -gt 0 ]; then
  echo "Waiting $wait_seconds s before measuring; do not touch the machine." >&2
  sleep "$wait_seconds"
fi

tab=$(printf '\t')
uid=$(id -u)
os_name=unknown
if [ -r "$os_release" ]; then
  os_name=$(awk -F= '$1 == "PRETTY_NAME" { v = $2; gsub(/^"|"$/, "", v); print v }' "$os_release")
fi
uptime_s=$(awk '{ printf "%d", $1 }' "$proc/uptime" 2>/dev/null || echo unknown)

echo 'Almond Linux memory report'
echo '=========================='
echo "Date (local):  $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Date (UTC):    $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "System:        $os_name"
echo "Kernel:        $(uname -srm)"
echo "Uptime:        $uptime_s s"
echo "Measured as:   uid $uid"
if [ "$uid" -ne 0 ]; then
  echo 'WARNING:       not root - other users'"'"' processes cannot be read, so the'
  echo '               process totals below are INCOMPLETE. Run with sudo.'
fi
echo 'Units:         MiB (1 MiB = 1024 KiB), from the kernel'"'"'s kB figures.'
echo 'Method:        docs/PERFORMANCE.md (fresh boot, 120 s idle, 5 boots, median).'
echo

echo 'System memory (/proc/meminfo)'
echo '------------------------------'
awk '
  { v[$1] = $2 }
  function mib(k) { return sprintf("%9.1f MiB  (%s kB)", k / 1024, k) }
  END {
    n = split("MemTotal: MemFree: MemAvailable: Buffers: Cached: Shmem: SwapTotal: SwapFree:", keys, " ")
    for (i = 1; i <= n; i++) {
      k = keys[i]
      if (k in v) printf "%-14s %s\n", k, mib(v[k])
      else printf "%-14s not reported by this kernel\n", k
    }
    print ""
    if (("MemTotal:" in v) && ("MemAvailable:" in v)) {
      printf "%-14s %s\n", "Used", mib(v["MemTotal:"] - v["MemAvailable:"])
      print  "               = MemTotal - MemAvailable (the figure AALDM targets use)"
      printf "%-14s %s\n", "Available", mib(v["MemAvailable:"])
    }
    if (("SwapTotal:" in v) && ("SwapFree:" in v))
      printf "%-14s %s\n", "Swap used", mib(v["SwapTotal:"] - v["SwapFree:"])
  }
' "$proc/meminfo"
if [ -r "$sys/block/zram0/mm_stat" ]; then
  awk '{
    printf "%-14s %9.1f MiB stored, %.1f MiB compressed, %.1f MiB RAM used\n", "zram0", $1 / 1048576, $2 / 1048576, $3 / 1048576
  }' "$sys/block/zram0/mm_stat"
else
  echo 'zram0          not present'
fi
echo

# One awk pass over every /proc/<pid>. getline returns -1 for files it
# cannot open (permission denied, or the process exited), so unreadable
# processes are counted instead of aborting the report.
records=$(awk -v self="$$" -v want_user="$session_user" -v passwd="$passwd_file" '
  function component(comm) {
    if (comm == "Xorg" || comm == "X") return "X server (Xorg)"
    if (comm ~ /^lightdm/) return "Display manager (LightDM)"
    if (comm == "openbox") return "Window manager (Openbox)"
    if (comm ~ /^lxqt-/) return "LXQt session + panel (lxqt-*)"
    if (comm == "pcmanfm-qt") return "Desktop + file manager (pcmanfm-qt)"
    if (comm == "nm-tray") return "Network tray (nm-tray)"
    if (comm == "rofi") return "Launcher (rofi)"
    if (comm ~ /^(pulseaudio|pipewire|wireplumber)/) return "Audio (PulseAudio/PipeWire)"
    if (comm ~ /^gvfs/ || comm == "udisksd") return "Files and devices (gvfs, udisks2)"
    if (comm == "NetworkManager" || comm == "wpa_supplicant") return "Network service (NetworkManager)"
    return ""
  }
  BEGIN {
    FS = ":"
    while ((getline line < passwd) > 0) {
      split(line, p, ":")
      name[p[3]] = p[1]
      uid_of[p[1]] = p[3]
    }
    close(passwd)
    FS = " "
    norder = split("X server (Xorg);Display manager (LightDM);Window manager (Openbox);LXQt session + panel (lxqt-*);Desktop + file manager (pcmanfm-qt);Network tray (nm-tray);Launcher (rofi);Audio (PulseAudio/PipeWire);Files and devices (gvfs, udisks2);Network service (NetworkManager)", order, ";")
    readable = 0; unreadable = 0; kthreads = 0; total = 0
    n = 0
    for (i = 1; i < ARGC; i++) {
      dir = ARGV[i]
      pid = dir
      sub(/.*\//, "", pid)
      if (pid == self) continue
      f = dir "/smaps_rollup"
      rss = 0; pss = 0; shared = 0; private = 0; swappss = 0; got = 0
      while ((r = (getline line < f)) > 0) {
        split(line, a, " ")
        if (a[1] == "Rss:") { rss = a[2]; got = 1 }
        else if (a[1] == "Pss:") pss = a[2]
        else if (a[1] == "Shared_Clean:" || a[1] == "Shared_Dirty:") shared += a[2]
        else if (a[1] == "Private_Clean:" || a[1] == "Private_Dirty:") private += a[2]
        else if (a[1] == "SwapPss:") swappss = a[2]
      }
      close(f)
      if (r < 0) { unreadable++; continue }
      if (!got) { kthreads++; continue }
      comm = "?"
      c = dir "/comm"
      if ((getline comm < c) <= 0) comm = "?"
      close(c)
      puid = ""; ppid = ""
      s = dir "/status"
      while ((getline line < s) > 0) {
        split(line, a, " ")
        if (a[1] == "Uid:") puid = a[2]
        else if (a[1] == "PPid:") ppid = a[2]
      }
      close(s)
      if (ppid == self) continue
      readable++
      n++
      P_pid[n] = pid; P_uid[n] = puid; P_comm[n] = comm
      P_pss[n] = pss; P_rss[n] = rss; P_sh[n] = shared; P_pr[n] = private; P_sw[n] = swappss
      total += pss
      if (want_user == "" && comm == "lxqt-session" && puid != "" && (puid in name)) want_user = name[puid]
    }
    want_uid = ""
    if (want_user != "" && (want_user in uid_of)) want_uid = uid_of[want_user]
    user_total = 0; user_count = 0; system_total = 0; xorg_total = 0; dm_total = 0
    for (i = 1; i <= n; i++) {
      user = (P_uid[i] in name) ? name[P_uid[i]] : P_uid[i]
      printf "P\t%d\t%s\t%s\t%d\t%d\t%d\t%d\t%s\n", P_pss[i], P_pid[i], user, P_rss[i], P_sh[i], P_pr[i], P_sw[i], P_comm[i]
      comp = component(P_comm[i])
      if (comp == "" && want_uid != "" && P_uid[i] == want_uid) comp = "Other processes of the session user"
      if (comp == "") comp = "Other system processes"
      ctotal[comp] += P_pss[i]; ccount[comp]++
      if (want_uid != "" && P_uid[i] == want_uid) { user_total += P_pss[i]; user_count++ }
      else if (P_comm[i] == "Xorg" || P_comm[i] == "X") xorg_total += P_pss[i]
      else if (P_comm[i] ~ /^lightdm/) dm_total += P_pss[i]
      else system_total += P_pss[i]
    }
    order[++norder] = "Other processes of the session user"
    order[++norder] = "Other system processes"
    for (j = 1; j <= norder; j++)
      printf "C\t%s\t%d\t%d\n", order[j], ctotal[order[j]], ccount[order[j]]
    printf "S\tsession_user\t%s\n", (want_uid != "") ? want_user : "(not found)"
    printf "S\tuser_total\t%d\n", user_total
    printf "S\tuser_count\t%d\n", user_count
    printf "S\txorg_total\t%d\n", xorg_total
    printf "S\tdm_total\t%d\n", dm_total
    printf "S\tsystem_total\t%d\n", system_total
    printf "S\ttotal\t%d\n", total
    printf "S\treadable\t%d\n", readable
    printf "S\tunreadable\t%d\n", unreadable
    printf "S\tkthreads\t%d\n", kthreads
  }
' "$proc"/[0-9]*)

summary() {
  printf '%s\n' "$records" | awk -F "$tab" -v key="$1" '$1 == "S" && $2 == key { print $3 }'
}
mib() {
  awk -v k="$1" 'BEGIN { printf "%.1f", k / 1024 }'
}

echo "Top $top processes by PSS (/proc/<pid>/smaps_rollup)"
echo '----------------------------------------------------'
printf '%s\n' "$records" | awk -F "$tab" '$1 == "P"' | sort -t "$tab" -k2,2nr | head -n "$top" | awk -F "$tab" '
  BEGIN { printf "%7s  %-10s %9s %9s %9s %9s %9s  %s\n", "PID", "USER", "PSS", "RSS", "SHARED", "PRIVATE", "SWAPPSS", "COMMAND" }
  { printf "%7s  %-10s %9.1f %9.1f %9.1f %9.1f %9.1f  %s\n", $3, substr($4, 1, 10), $2 / 1024, $5 / 1024, $6 / 1024, $7 / 1024, $8 / 1024, $9 }
'
echo '(MiB. RSS counts shared pages in full for every process; PSS divides each'
echo ' shared page between the processes that map it, so PSS values add up.)'
echo

echo 'PSS by AALDM component (budgets: docs/PERFORMANCE.md)'
echo '-----------------------------------------------------'
printf '%s\n' "$records" | awk -F "$tab" '$1 == "C" { printf "%-40s %9.1f MiB  (processes: %d)\n", $2, $3 / 1024, $4 }'
echo

session=$(summary session_user)
echo 'Totals (PSS)'
echo '------------'
echo "Session user:                       $session"
echo "Session user processes:             $(mib "$(summary user_total)") MiB (processes: $(summary user_count))"
echo "X server (Xorg):                    $(mib "$(summary xorg_total)") MiB"
echo "Display manager (LightDM):          $(mib "$(summary dm_total)") MiB"
desktop_total=$(( $(summary user_total) + $(summary xorg_total) + $(summary dm_total) ))
echo "DESKTOP SESSION TOTAL:              $(mib "$desktop_total") MiB  (session user + Xorg + LightDM)"
echo "All other processes (system):       $(mib "$(summary system_total)") MiB"
echo "All readable processes:             $(mib "$(summary total)") MiB (processes: $(summary readable))"
echo "Kernel threads (no user memory):    $(summary kthreads)"
echo "Unreadable or exited during scan:   $(summary unreadable)"
echo
echo 'Notes: "Used" above also counts the kernel, page tables, tmpfs/Shmem (in'
echo 'a live session every file written lives in RAM) and zram, which no process'
echo 'owns, so "Used" and the PSS total are not expected to match. This script'
echo 'is excluded from the table; the sudo or shell that started it is not.'
