#!/usr/bin/python

from bcc import BPF


program = BPF(
        text=r"""
#include <linux/cred.h>
#include <linux/sched.h>
#include <linux/user_namespace.h>
#include <uapi/linux/ptrace.h>


static inline void
show_uid_map(struct uid_gid_map* mapping)
{
        bpf_trace_printk("FIRST\tLOWER\tCOUNT\n");
        bpf_trace_printk("%d\t%d\t%d\n",
                         mapping->extent[0].first,
                         mapping->extent[0].lower_first,
                         mapping->extent[0].count);
}

int
kr__proc_uid_map_write(struct pt_regs* ctx)
{

        struct task_struct* task;
        struct uid_gid_map* mapping;

        task = (struct task_struct*)bpf_get_current_task();

        if (task->cred->user_ns->uid_map.nr_extents < 1) {
                return 0;
        }

        mapping = &task->cred->user_ns->uid_map;
        show_uid_map(mapping);

        return 0;
}
"""
)

program.attach_kretprobe(
    event="proc_uid_map_write", fn_name="kr__proc_uid_map_write"
)

program.trace_print()
