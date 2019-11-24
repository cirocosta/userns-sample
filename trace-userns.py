#!/usr/bin/python

# trace-userns.py  traces use of userns primitives.
#

from bcc import BPF


program = BPF(
        text=r"""
#include <linux/cred.h>
#include <linux/sched.h>
#include <linux/user_namespace.h>
#include <uapi/linux/ptrace.h>

BPF_HASH(procs, u32, u32);


static inline int
__print_uid_map(struct pt_regs* ctx)
{
        struct task_struct* task;
        struct uid_gid_map* mapping;

        task = (struct task_struct*)bpf_get_current_task();
        mapping = &task->cred->user_ns->uid_map;

        if (mapping->nr_extents < 1) {
                return 0;
        }

        bpf_trace_printk("%d,%d,%d\n",
                         mapping->extent[0].first,
                         mapping->extent[0].lower_first,
                         mapping->extent[0].count);

        return 0;
}


int
kr__create_user_ns(struct pt_regs* ctx)
{
    bpf_trace_printk("create_user_ns\n");
    return __print_uid_map(ctx);
}


int
kr__proc_uid_map_write(struct pt_regs* ctx)
{
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    procs.update(&pid, &pid);

    bpf_trace_printk("proc_uid_map\n");
    return __print_uid_map(ctx);
}

int
k__generic_permission(struct pt_regs* ctx)
{
        struct task_struct* task;
        struct uid_gid_map* mapping;
        u32 pid = bpf_get_current_pid_tgid() >> 32;

        u32 *pid_ptr = procs.lookup(&pid);
        if (pid_ptr == NULL) {
            return 0;
        }

        bpf_trace_printk("generic_permission\n");
        task = (struct task_struct*)bpf_get_current_task();
        bpf_trace_printk("fsuid=%d\n", task->cred->fsuid);

        return 0;
}
"""
)

program.attach_kretprobe(
    event="proc_uid_map_write", fn_name="kr__proc_uid_map_write"
)

program.attach_kretprobe(
    event="create_user_ns", fn_name="kr__create_user_ns"
)

program.attach_kprobe(
    event="generic_permission", fn_name="k__generic_permission"
)

program.trace_print()
