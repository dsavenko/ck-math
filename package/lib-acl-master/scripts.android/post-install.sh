#! /bin/bash

set -e

cd ${INSTALL_DIR}/${PACKAGE_SUB_DIR}

env

arch=${CK_ANDROID_ABI}

if [ "$arch" == "armeabi-v7a" ]; then
    arch="armv7a"
fi

scons Werror=1 -j ${CK_HOST_CPU_NUMBER_OF_PROCESSORS} debug=0 neon=${USE_NEON} opencl=0 os=android arch="$arch" extra_cxx_flags="${CK_COMPILER_FLAGS_OBLIGATORY} -I${CK_ENV_LIB_STDCPP_INCLUDE} -I${CK_ENV_LIB_STDCPP_INCLUDE_EXTRA} -I${CK_SYS_ROOT}/usr/include -L${CK_ENV_LIB_STD}"
