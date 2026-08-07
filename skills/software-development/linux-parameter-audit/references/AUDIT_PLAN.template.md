# AUDIT_PLAN.md — TEMPLATE (copy to audit working dir, fill Keys from extract_keys.sh counts)
# Status: PENDING | IN_PROGRESS | DONE | SKIPPED (reason)
# After each batch: set DONE + append to AUDIT_LOG.md.

| Batch | Group / Surface                                  | Keys | Status      | Output file            |
|-------|--------------------------------------------------|------|-------------|-----------------------|
| A     | sysctl kernel.*                                  | ?    | PENDING     | batchA_kernel.md      |
| B     | sysctl vm.*                                      | ?    | PENDING     | batchB_vm.md          |
| C1    | sysctl fs.*                                      | ?    | PENDING     | batchC_fs.md          |
| C2    | sysctl net.* global (net.core/ipv4/ipv6)         | ?    | PENDING     | batchC_netcore.md     |
| C3    | sysctl user.* / dev.* / debug.* / abi.*          | ?    | PENDING     | batchC_misc.md        |
| D1    | kernel cmdline (tokens)                          | ?    | PENDING     | batchD_cmdline.md     |
| D2    | /sys/kernel, cpu freq/cstate, /sys/block IO, cgroup v2, THP | - | PENDING  | batchD_sysfs.md       |
| D3    | configs: nvidia modprobe, kwinrc, gamemode.ini, udev, env, docker | - | PENDING | batchD_configs.md |
| Z     | COMPILE master recommendations.md                | -    | PENDING     | recommendations.md     |

# Replace "?" with real counts from: wc -l batches/*.list
# Per-interface net conf keys (net.ipv4.conf.<iface>.* etc.) are SUMMARIZED in C2, not row-per-key.
