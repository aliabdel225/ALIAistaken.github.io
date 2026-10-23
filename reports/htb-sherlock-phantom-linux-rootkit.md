# HTB Sherlock: Phantom — Linux Rootkit Memory Investigation

## Executive summary

A memory image from an Ubuntu Linux server was analyzed with Volatility 3. The investigation identified an unsigned out-of-tree kernel module named **singularity**. Cross-view module analysis found it in a memory scan, while it was absent from the kernel module views exposed through procfs and sysfs. Kernel logs record the module loading at **2,490.473832 seconds after boot**, under **PID 2669**.

The module registered a hook on the **sched_process_fork** tracepoint and was associated with **82 ftrace hook entries** that shared callback address **0xffffc0b3aac0**. The hooked functions cover directory and file metadata calls, IPv4 and IPv6 TCP listings, BPF calls, packet reception, and other system calls. These hooks indicate broad interception capabilities; the hook names alone do not prove the exact behavior of every handler.

Three bash processes—PIDs **2693, 2695, and 2698**—each had file descriptors 0, 1, and 2 attached to a separate established TCP connection to **192.168.200.164:8081**. This pattern is consistent with interactive remote shells and makes that endpoint a high-priority network indicator.

## Case details

| Field | Finding |
|---|---|
| Scenario | HTB Sherlock: Phantom |
| Evidence | Linux memory image and matching kernel symbol file |
| Operating system | Ubuntu, kernel 6.8.0-87-generic |
| Analysis framework | Volatility 3 Framework 2.28.2 |
| Suspicious module | singularity |
| Module loader | PID 2669 |
| Load time | 2,490.473832 seconds after boot |
| Rootkit tracepoint | sched_process_fork |
| Shared ftrace callback | 0xffffc0b3aac0 |
| ftrace entries attributed to singularity | 82 |

## Investigation and findings

### 1. Validated the memory image and kernel symbols

The memory image was identified as raw data, and the supplied symbol file matched the kernel banner recovered from memory: Ubuntu 6.8.0-87-generic. The evidence hashes recorded before analysis were:

| Evidence file | SHA-256 |
|---|---|
| dump_srv.mem | 61271fad70e13734542988a66439a66d28752f67c7ccfbfa20bb95343c52f1d2 |
| Ubuntu_6.8.0-87-generic.json | 2ba400b7fba78b528ab87559dcacd81fa2390c856a507a4a563a2521ea827ca4 |

### 2. Detected the hidden kernel module

The hidden-module scan identified singularity with taints OOT_MODULE and UNSIGNED_MODULE. The module cross-view output reported:

- Not present in procfs view
- Not present in sysfs view
- Present in the memory scan

This discrepancy is evidence of a concealed or unlinked kernel module. A separate module extraction attempt did not reconstruct an ELF, so no recovered module binary was available for static analysis.

### 3. Established load time and loading process

The kernel log contained these entries:

- At 2,490.473832 seconds after boot, PID 2669 logged that singularity was loading as an out-of-tree module.
- At 2,490.473840 seconds after boot, the kernel logged failed module signature verification and kernel tainting.

The 8-microsecond separation and matching module name link these messages to the same load event. PID 2669 was not present in the later process memory scan, which is consistent with a short-lived loader process exiting before capture.

### 4. Identified kernel hooks

The tracepoint analysis associated singularity with sched_process_fork. This tracepoint fires when a process is forked, giving the module visibility into process creation.

The ftrace analysis attributed 82 hook entries to singularity. All entries pointed to callback address 0xffffc0b3aac0. Notable targets included:

| Hooked functions | Potential significance |
|---|---|
| getdents variants | Could filter directory entries returned to user space |
| stat, lstat, statx, newfstatat, readlink, openat | Could affect file metadata, path resolution, or access |
| tcp4_seq_show, tcp6_seq_show | Could filter IPv4 and IPv6 TCP connection listings |
| __x64_sys_bpf, __ia32_sys_bpf | Could intercept BPF system calls |
| tpacket_rcv, icmp_rcv | Could intercept packet-socket or ICMP receive handling |
| __x64_sys_kill | Could inspect or alter signal-related system-call behavior |
| read/write, splice, sendfile, io_uring calls | Could intercept data and file operations |
| init_module, finit_module | Could intercept module-loading operations |

These are capability indicators based on hook targets. Without the module’s code, they do not establish the precise conditions or actions implemented by the callback.

### 5. Correlated shell history and process evidence

Recovered Bash history included:

- PID 2774 ran OPERATOR=access bash at 2025-11-19 17:41:02 UTC.
- The resulting shell, PID 2792, ran kill -59 $$ and ps aufwx at 17:41:06–17:41:08 UTC.
- PID 2861 later ran ./avml dump_srv.mem at 17:41:29 UTC.

The OPERATOR=access entry identifies the suspicious environment variable and value associated with the privilege-escalation scenario. The kill -59 $$ command is notable because singularity also hooked __x64_sys_kill, but the available evidence does not prove the purpose of signal 59.

Process scanning found three psimon kernel threads (PIDs 548, 1495, and 2809) and the three bash processes discussed below. The selected psimon and bash entries also appeared in the earlier process-list view; this comparison did not show those entries being hidden from that view.

### 6. Correlated suspicious network connections

The socket analysis found three established connections to the same remote endpoint. For each bash process, file descriptors 0, 1, and 2 referred to its connected socket:

| PID | Local endpoint | Remote endpoint | Assessment |
|---:|---|---|---|
| 2693 | 192.168.200.177:48440 | 192.168.200.164:8081 | Bash standard streams attached to established TCP socket |
| 2695 | 192.168.200.177:48444 | 192.168.200.164:8081 | Bash standard streams attached to established TCP socket |
| 2698 | 192.168.200.177:48454 | 192.168.200.164:8081 | Bash standard streams attached to established TCP socket |

This repeated pattern is consistent with remote interactive shells. The tcp4_seq_show hook could affect how IPv4 TCP connections appear in standard kernel connection listings, making memory-based socket analysis an important corroborating source.

## Indicators of compromise

| Indicator | Type | Context |
|---|---|---|
| singularity | Kernel module name | Hidden from procfs and sysfs views; found in scan |
| 0xffffc0b3aac0 | Kernel callback address | Shared callback reported for 82 ftrace entries |
| sched_process_fork | Tracepoint | Hooked by singularity |
| PID 2669 | Process ID | Recorded by kernel log as module loader |
| 2,490.473832 seconds after boot | Load time | Kernel log timestamp for module load |
| OPERATOR=access | Environment variable | Recovered in Bash history before child shell |
| 192.168.200.164:8081 | Remote endpoint | Destination for three established bash-associated TCP sessions |
| PIDs 2693, 2695, 2698 | Process IDs | bash processes with standard streams attached to remote TCP sockets |
| psimon (PIDs 548, 1495, 2809) | Process names and IDs | Unusual kernel threads observed in process output |

Address notes: hidden-module and tracepoint output reported the module structure at 0xffffc0b42640; the ftrace output reported module address 0xffffc0b35000. These are recorded as reported by their respective plugin fields and should not be assumed to be the same address type.

## How to interpret the evidence

The memory image contains several independent views of kernel and process state. Their value comes from comparison and correlation, not from treating one plugin result as a complete explanation.

- **Module cross-view:** a scan can find module structures that ordinary kernel lists no longer expose. Finding `singularity` in memory but not in procfs or sysfs is consistent with a hidden or unlinked module. The discrepancy is a strong lead; the kernel log, tracepoint, and ftrace results provide additional corroboration.
- **Tracepoint and ftrace results:** these records show that the module registered process-creation tracing and that many hook entries shared one callback address. They identify interception points and a broad potential capability. Because module extraction failed, they do not prove the exact logic executed by every hook.
- **Process and socket correlation:** when file descriptors 0, 1, and 2 for a shell point to the same established TCP socket, the process may be using that socket for interactive input and output. This pattern supports a remote-shell interpretation, but does not by itself identify the remote operator or prove what commands were issued.
- **Timeline correlation:** kernel-relative time, wall-clock timestamps, process IDs, and socket records come from different artifacts. I compare them to build a sequence, while retaining the timestamp source and its limits so readers do not mistake correlation for direct causation.

## Conclusion

The strongest evidence is the combined presence of a concealed unsigned kernel module, its process-creation tracepoint hook, 82 ftrace hooks sharing a module callback, and three bash processes whose standard streams were connected to the same external endpoint on port 8081. The hooked TCP listing functions are consistent with an effort to impair visibility into network connections.

The analysis establishes the module name, loading process and time, hook targets, suspicious environment variable, and network endpoint. Because module extraction failed, the exact implementation and behavior of individual hooks could not be confirmed from the module binary.

## Analysis commands

Representative Volatility commands used during the investigation:

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.banners

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.malware.hidden_modules

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.malware.modxview

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.tracing.tracepoints.CheckTracepoints

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.tracing.ftrace.CheckFtrace

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.kmsg

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.pslist

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.psscan

    vol --symbol-dirs "$PWD/symbols" --offline -f dump_srv.mem linux.sockstat

---

*This report documents the evidence and analysis from the memory image. Conclusions about hook behavior are framed as capabilities unless corroborated by direct code or additional telemetry.*

