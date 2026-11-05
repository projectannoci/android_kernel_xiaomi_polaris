#!/sbin/sh
properties() { '
kernel.string=Singularity v1 @ProjectNoci #1
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=polaris
supported.versions=13+
supported.patchlevels=
supported.vendorpatchlevels=
'; }
BLOCK=boot;
IS_SLOT_DEVICE=0;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=auto;
. tools/ak3-core.sh;
ui_print "Singularity v1 @ProjectNoci #1";
ui_print "Mi MIX 2S | polaris | Android 13+ AOSP | 4.9";
ui_print "Gaming | KSU Next | matched Polaris DTB";
. "$AKHOME/tools/noci-compat.sh";
noci_check_payload;
split_boot;
noci_check_boot;
flash_boot;
