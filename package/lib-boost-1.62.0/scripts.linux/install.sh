#! /bin/bash

#
# Extra installation script
#
# See CK LICENSE.txt for licensing details.
# See CK COPYRIGHT.txt for copyright details.
#
# Developer(s):
# - Grigori Fursin, 2016-2017
# - Anton Lokhmotov, 2017
#

############################################################
cd ${INSTALL_DIR}/${PACKAGE_SUB_DIR1}
./bootstrap.sh
if [ "${?}" != "0" ] ; then
  echo "Error: cmake failed!"
  exit 1
fi

############################################################
echo ""
echo "Building Boost (can take a long time) ..."

TOOLCHAIN=gcc
if [ "${CK_COMPILER_TOOLCHAIN_NAME}" != "" ] ; then
  TOOLCHAIN=$CK_COMPILER_TOOLCHAIN_NAME
fi

export BOOST_BUILD_PATH=$INSTALL_DIR/install
echo "using ${TOOLCHAIN} : : ${CK_CXX} -fPIC ${CK_CXX_FLAGS_FOR_CMAKE} ${EXTRA_FLAGS} -DNO_BZIP2 ;" > $BOOST_BUILD_PATH/user-config.jam

./b2 install -j ${CK_HOST_CPU_NUMBER_OF_PROCESSORS} toolset=${TOOLCHAIN} address-model=${CK_TARGET_CPU_BITS} --prefix=${BOOST_BUILD_PATH} ${BOOST_B2_FLAGS}

if [ "${?}" != "0" ] ; then
  echo "Error: b2 make failed!"
  exit 1
fi

return 0
