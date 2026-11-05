/* SPDX-License-Identifier: GPL-2.0 */
#ifndef _LINUX_NOCI_KSU_H
#define _LINUX_NOCI_KSU_H
#ifdef CONFIG_KSU
#include <linux/compiler.h>
#include <linux/types.h>
struct file;
struct filename;
extern bool ksu_vfs_read_hook;
extern bool ksu_input_hook;
extern int ksu_handle_execveat(int *fd, struct filename **filename,
			     void *argv, void *envp, int *flags);
extern int ksu_handle_vfs_read(struct file **file, char __user **buf,
			     size_t *count, loff_t **pos);
extern int ksu_handle_faccessat(int *dfd, const char __user **filename,
			      int *mode, int *flags);
extern int ksu_handle_stat(int *dfd, const char __user **filename, int *flags);
extern int ksu_handle_input_handle_event(unsigned int *type,
					unsigned int *code, int *value);
#endif
#endif
