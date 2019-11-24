#!/usr/bin/python

from bcc import BPF


program = BPF(
        text=r"""
#include <linux/cred.h>
#include <linux/sched.h>
#include <linux/user_namespace.h>
#include <uapi/linux/ptrace.h>


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
    bpf_trace_printk("proc_uid_map\n");
    return __print_uid_map(ctx);
}
"""
)

program.attach_kretprobe(
    event="proc_uid_map_write", fn_name="kr__proc_uid_map_write"
)

program.attach_kretprobe(
    event="create_user_ns", fn_name="kr__create_user_ns"
)

program.trace_print()
