#!/usr/bin/env bash
set -euo pipefail
export ARCH=arm64 SUBARCH=arm64
export CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-} CROSS_COMPILE_ARM32=${CROSS_COMPILE_ARM32:-arm-linux-gnueabi-}
export KBUILD_BUILD_USER=ProjectNoci KBUILD_BUILD_HOST=Singularity
export KBUILD_BUILD_VERSION=1
export KBUILD_BUILD_TIMESTAMP='Fri Oct 30 00:00:00 UTC 2026'
case "${1:-raw}" in
 raw) fragment=vendor/xiaomi/singularity.config;;
 baseline) fragment=vendor/xiaomi/singularity-baseline.config;;
 *) echo 'Usage: ./build-kernel.sh [raw|baseline]' >&2; exit 2;;
esac
make -C kernel O=../out CC=clang HOSTCC=gcc LD=ld.lld CLANG_TRIPLE=aarch64-linux-gnu- vendor/xiaomi/mi845_defconfig vendor/xiaomi/polaris.config "$fragment"
make -C kernel O=../out CC=clang HOSTCC=gcc LD=ld.lld CLANG_TRIPLE=aarch64-linux-gnu- olddefconfig
make -C kernel O=../out -j"${JOBS:-8}" CC=clang HOSTCC=gcc LD=ld.lld CLANG_TRIPLE=aarch64-linux-gnu- Image.gz-dtb
python3 pair-dtbs.py
