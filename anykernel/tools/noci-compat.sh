#!/sbin/sh
# Singularity / polaris compatibility checks.
noci_system_prop_files() {
  printf '%s\n' /system/build.prop /system_root/system/build.prop /system/system/build.prop /system/etc/build.prop /system_root/system/etc/build.prop;
}

noci_detect_android() {
  local propfile sdk release;
  NOCI_ANDROID_SDK=;
  NOCI_ANDROID_RELEASE=;
  for propfile in $(noci_system_prop_files); do
    sdk=$(file_getprop "$propfile" ro.build.version.sdk 2>/dev/null);
    [ "$sdk" ] || sdk=$(file_getprop "$propfile" ro.system.build.version.sdk 2>/dev/null);
    case "$sdk" in ''|*[!0-9]*) continue;; esac;
    release=$(file_getprop "$propfile" ro.build.version.release 2>/dev/null);
    [ "$release" ] || release=$(file_getprop "$propfile" ro.system.build.version.release 2>/dev/null);
    NOCI_ANDROID_SDK=$sdk;
    NOCI_ANDROID_RELEASE=${release:-SDK-$sdk};
    return 0;
  done;
  # In recovery, getprop describes recovery rather than the installed ROM.
  if [ "$BOOTMODE" = true ]; then
    sdk=$(getprop ro.build.version.sdk 2>/dev/null);
    case "$sdk" in ''|*[!0-9]*) return 1;; esac;
    NOCI_ANDROID_SDK=$sdk;
    NOCI_ANDROID_RELEASE=$(getprop ro.build.version.release 2>/dev/null);
    return 0;
  fi;
  return 1;
}

noci_check_payload() {
  local magic;
  [ -s "$AKHOME/Image.gz-dtb" ] || abort "Kernel + DTB payload missing. Aborting...";
  mkdir -p "$AKHOME/.noci-payload-check" || abort "Cannot validate payload. Aborting...";
  (cd "$AKHOME/.noci-payload-check" && magiskboot split -n "$AKHOME/Image.gz-dtb") >/dev/null 2>&1 || abort "Kernel + DTB payload is corrupt. Aborting...";
  [ -s "$AKHOME/.noci-payload-check/kernel_dtb" ] || abort "Paired device trees missing. Aborting...";
  magiskboot dtb "$AKHOME/.noci-payload-check/kernel_dtb" print >/dev/null 2>&1 || abort "Paired device trees are corrupt. Aborting...";
  gzip -t "$AKHOME/.noci-payload-check/kernel" 2>/dev/null || abort "Kernel payload is corrupt. Aborting...";
  gzip -dc "$AKHOME/.noci-payload-check/kernel" > "$AKHOME/.noci-kernel-check" || abort "Cannot decompress kernel. Aborting...";
  magic=$(od -An -j56 -N4 -tx1 "$AKHOME/.noci-kernel-check" | tr -d ' \n');
  [ "$magic" = 41524d64 ] || abort "Kernel payload is not ARM64. Aborting...";
  [ "$(wc -c < "$AKHOME/.noci-kernel-check")" -ge 8388608 ] || abort "Kernel payload is incomplete. Aborting...";
  rm -f "$AKHOME/.noci-kernel-check";
  rm -rf "$AKHOME/.noci-payload-check";
}

noci_check_boot() {
  local magic header release;
  magic=$(od -An -N8 -tc "$BOOTIMG" | tr -d ' \n');
  [ "$magic" = 'ANDROID!' ] || abort "Unsupported boot format. Aborting...";
  header=$(od -An -j40 -N4 -tu4 "$BOOTIMG" | tr -d ' \n');
  case "$header" in 0|1|2) ;; *) abort "Boot header $header is not the polaris 4.9 layout. Aborting...";; esac;
  [ -s "$SPLITIMG/kernel" ] || abort "Existing kernel could not be unpacked. Aborting...";
  release=$(strings "$SPLITIMG/kernel" | sed -n 's/^Linux version \([^ ]*\).*/\1/p' | head -n1);
  case "$release" in
    4.9.*) ;;
    *) abort "Installed kernel ${release:-unknown} needs a matching kernel family. This package targets polaris 4.9. Aborting...";;
  esac;
  # Require the legacy appended-DTB layout; flash_boot installs our paired DTBs.
  [ -s "$SPLITIMG/kernel_dtb" ] || abort "Original polaris device tree missing. Aborting...";
  ui_print "Android $NOCI_ANDROID_RELEASE | existing kernel $release";
}
