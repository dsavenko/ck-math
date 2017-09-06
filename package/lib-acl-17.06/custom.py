#!/usr/bin/python

#
# Developers:
# - Grigori Fursin, Grigori.Fursin@cTuning.org, http://fursin.net
# - Anton Lokhmotov, anton@dividiti.com
#

import os
import sys
import json
import errno

##############################################################################
# customize installation

def setup(i):
    """
    Input:  {
              cfg              - meta of the soft entry
              self_cfg         - meta of module soft
              ck_kernel        - import CK kernel module (to reuse functions)

              host_os_uoa      - host OS UOA
              host_os_uid      - host OS UID
              host_os_dict     - host OS meta

              target_os_uoa    - target OS UOA
              target_os_uid    - target OS UID
              target_os_dict   - target OS meta

              target_device_id - target device ID (if via ADB)

              tags             - list of tags used to search this entry

              env              - updated environment vars from meta
              customize        - updated customize vars from meta

              deps             - resolved dependencies for this soft

              interactive      - if 'yes', can ask questions, otherwise quiet

              path             - path to entry (with scripts)
              install_path     - installation path
            }

    Output: {
              return        - return code =  0, if successful
                                          >  0, if error
              (error)       - error text if return > 0

              (install_env) - prepare environment to be used before the install script
            }

    """

    import os
    import shutil
    import glob

    # Get variables
    o=i.get('out','')

    ck=i['ck_kernel']

    hos=i['host_os_uoa']
    tos=i['target_os_uoa']

    hosd=i['host_os_dict']
    tosd=i['target_os_dict']

    hbits=hosd.get('bits','')
    tbits=tosd.get('bits','')

    hname=hosd.get('ck_name','')    # win, linux
    hname2=hosd.get('ck_name2','')  # win, mingw, linux, android
    tname2=tosd.get('ck_name2','')  # win, mingw, linux, android

    macos=hosd.get('macos','')      # yes/no

    hft=i.get('features',{}) # host platform features
    habi=hft.get('os',{}).get('abi','') # host ABI (only for ARM-based); if you want to get target ABI, use tosd ...
                                        # armv7l, etc...

    p=i['path']

    env=i['new_env']

    pi=i.get('install_path','')

    cus=i['customize']
    ie=cus.get('install_env',{})
    nie={} # new env

    deps=i.get('deps','')

    # Converting sconscript to CK format
    flags = ['-D_GLIBCXX_USE_NANOSLEEP','-Wno-deprecated-declarations','-Wall','-DARCH_ARM',
         '-Wextra','-Wno-unused-parameter','-pedantic','-Wdisabled-optimization','-Wformat=2',
         '-Winit-self','-Wstrict-overflow=2','-Wswitch-default',
         '-fpermissive','-std=gnu++11','-Wno-vla','-Woverloaded-virtual',
         '-Wctor-dtor-privacy','-Wsign-promo','-Weffc++','-Wno-format-nonliteral','-Wno-overlength-strings','-Wno-strict-overflow']

    lcore_flags=['-ldl']
    lflags=['-ldl']

    # Check various target params from CK
    cpu_features=tosd.get('cpu_features',{})
    tneon=cpu_features.get('arm_fp_neon','')
    thardfp=cpu_features.get('arm_fp_hard','')

    # ABI for Android
    tabi=tosd.get('abi','')
    if tabi=='': # Means host
        tabi=habi # Means ARM
        if tabi=='': # Means x86 (indirectly)
            tabi='x86'
            if str(tbits)=='64': tabi='x86_64'

    neon=False
    if env.get('USE_NEON','').lower()=='on' or tneon=='yes':
        neon=True
        nie['USE_NEON']='ON'

    hardfp=False
    if env.get('USE_BARE_METAL','').lower()=='on' or thardfp=='yes':
        hardfp=True
        nie['USE_BARE_METAL']='ON'

    if neon and 'x86' in tabi:
        return {'return':1, 'error':'Cannot compile NEON for x86'}

    compiler_env=deps['compiler'].get('dict',{}).get('env',{})
    cxx=compiler_env['CK_CXX']

    if compiler_env.get('CK_ENV_LIB_STDCPP_INCLUDE','')!='':
        flags+=['-I'+compiler_env['CK_ENV_LIB_STDCPP_INCLUDE']]
    if compiler_env.get('CK_ENV_LIB_STDCPP_INCLUDE_EXTRA','')!='':
        flags+=['-I'+compiler_env['CK_ENV_LIB_STDCPP_INCLUDE_EXTRA']]

#       env['CK_ENV_LIB_STDCPP_STATIC']=libstdcpppath+sep+'libgnustl_static.a'
#       env['CK_ENV_LIB_STDCPP_DYNAMIC']=libstdcpppath+sep+'libgnustl_shared.so'
#       env['CK_ENV_LIB_STDCPP_INCLUDE_EXTRA']=libstdcpppath+sep+'include'


    if 'clang++' in cxx:
        flags += ['-Wno-format-nonliteral','-Wno-deprecated-increment-bool','-Wno-vla-extension','-Wno-mismatched-tags']
    elif 'g++' in cxx:
        flags += ['-Wlogical-op','-Wnoexcept','-Wstrict-null-sentinel']

    if env.get('USE_CPPTHREADS','').lower()=='on':
        flags += ['-DARM_COMPUTE_CPP_SCHEDULER=1']

    if env.get('USE_OPENMP','').lower()=='on':
        if 'clang++' in cxx:
            return {'return':1, 'error':'Clang does not support OpenMP. Use --env.USE_CPPTHREADS=ON'}

        flags += ['-DARM_COMPUTE_OPENMP_SCHEDULER=1','-fopenmp']
        lflags += ['-fopenmp']
        lcore_flags += ['-fopenmp']

    if 'v7a' in tabi:
        flags += ['-march=armv7-a','-mthumb','-mfpu=neon']

        if hardfp:
            flags += ['-mfloat-abi=hard']
        elif tname2=='android':
            flags += ['-mfloat-abi=softfp']
    elif 'arm64' in tabi:
        flags += ['-march=armv8-a']
    elif env.get('USE_ARM64_V82A','').lower()=='on':
        flags += ['-march=armv8.2-a+fp16+simd']
        flags += ['-DARM_COMPUTE_ENABLE_FP16']
    elif tabi=='x86':
        flags += ['-m32']
    elif tabi=='x86_64':
        flags += ['-m64']

    if tname2=='android':
        flags += ['-DANDROID']
        if compiler_env.get('CK_ENV_LIB_STDCPP_STATIC','')!='':
           lflags+=[compiler_env['CK_ENV_LIB_STDCPP_STATIC']]
           lcore_flags+=[compiler_env['CK_ENV_LIB_STDCPP_STATIC']]
# Done via CK
#        lflags+=['-static-libstdc++']
#        lcore_flags+=['-static-libstdc++']
    elif env.get('USE_BARE_METAL','').lower()=='on':
        flags += ['-fPIC','-DNO_MULTI_THREADING']
        lflags+=['-static']
        lcore_flags+=['-static']
    else:
        lflags += ['-lpthread']

    flags += ['-O3','-ftree-vectorize']

    nie['CXXFLAGS']=' '.join(flags)
    nie['LFLAGS']=' '.join(lflags)
    nie['LCORE_FLAGS']=' '.join(lcore_flags)

    return {'return':0, 'install_env':nie}

##############################################################################
# customize installation after download

def _slash(s):
    return s.replace('\\','/')

def post_setup(i):
    """
    Input:  {
              The same as in setup(i)

              new_env - last env (can be directly updated)
            }

    Output: {
              return        - return code =  0, if successful
                                          >  0, if error
              (error)       - error text if return > 0
            }

    """

    import os
    import shutil
    import glob
    import subprocess

    # Get variables
    o=i.get('out','')

    ck=i['ck_kernel']

    cfg=i.get('cfg',{})
    hosd=i['host_os_dict']
    tosd=i['target_os_dict']
    env=i.get('new_env',{})
    deps=i.get('deps',{})

    hname=hosd.get('ck_name','')    # win, linux
    hname2=hosd.get('ck_name2','')  # win, mingw, linux, android
    tname2=tosd.get('ck_name2','')  # win, mingw, linux, android
    winh=hosd.get('windows_base','')

    lib_prefix=''
    if winh!='yes' or tname2=='android':
        lib_prefix='lib'

    flags=env.get('CXXFLAGS','')
    lflags=env.get('LFLAGS','')
    lcore_flags=env.get('LCORE_FLAGS','')
    bare_metal=env.get('USE_BARE_METAL','').lower()
    use_neon=env.get('USE_NEON','').lower()

    pop=i.get('path_original_package','')
    pi=i.get('install_path','')
    pi1=cfg.get('customize',{}).get('extra_dir','')
    if pi1=='': pi1=cfg.get('customize',{}).get('git_src_dir','')

    build_dir=pi
    if pi1!='': build_dir=os.path.join(pi,pi1)

    if not os.path.isdir(build_dir):
        return {'return':1, 'error':'Something is wrong - build directory is not there ('+build_dir+')'}

    os.chdir(build_dir)

    xcore_files = glob.glob('src/core/*.cpp')
    xcore_files += glob.glob('src/core/CPP/*.cpp')

    xfiles = glob.glob('src/runtime/*.cpp')

    embed_files = []
    xcore_files += glob.glob('src/core/CPP/kernels/*.cpp')

    # CLHarrisCorners uses the Scheduler to run CPP kernels
    xfiles += glob.glob('src/runtime/CPP/SingleThreadScheduler.cpp')

    if bare_metal=='on':
        if env.get('USE_CPPTHREADS','').lower()=='on' or env.get('USE_OPENMP','').lower()=='on':
            return {'return':1, 'error':'OpenMP and C++11 threads not supported in bare_metal. use --env.USE_CPPTHREADS=OFF --env.USE_OPENMP=OFF'}
    else:
        if env.get('USE_CPPTHREADS','').lower()=='on':
            xfiles += glob.glob('src/runtime/CPP/CPPScheduler.cpp')
        if env.get('USE_OPENMP','').lower()=='on':
            xfiles += glob.glob('src/runtime/OMP/OMPScheduler.cpp')

    if use_neon=='on':
        xcore_files += glob.glob('src/core/NEON/*.cpp')
        xcore_files += glob.glob('src/core/NEON/kernels/*.cpp')
        xfiles += glob.glob('src/runtime/NEON/*.cpp')
        xfiles += glob.glob('src/runtime/NEON/functions/*.cpp')

    # Generate string with build options library version to embed in the library:
    r=ck.run_and_get_stdout({'cmd':['git','rev-parse','HEAD']})
    if r['return']==0 and r['return_code']==0:
        git_hash=r['stdout'].strip()

    version_filename = 'arm_compute_version.embed' #"%s/arm_compute_version.embed" % os.path.dirname(glob.glob("src/core/*")[0].rstr())
    build_info = "\"arm_compute_version=%s Build options: %s Git hash=%s\"" % ('', '', git_hash.strip())

    r=ck.save_text_file({'text_file':version_filename, 'string':build_info})
    if r['return']>0: return r

    # Common functionality to build the core lib or the core+runtime libs.
    def build(lib_target, files, link_flags, hosd, deps, pop, bare_metal, build_script_name):
        oext=deps.get('compiler',{}).get('dict',{}).get('env',{}).get('CK_OBJ_EXT','')
        sext=hosd.get('script_ext','')
        eset=hosd.get('env_set','')
        eifs=hosd.get('env_quotes_if_space','')

        # Prepare obj names.
        core_files=''
        obj_core_files=''
        for f in files:
            f=_slash(f)
            fo=os.path.splitext(f)[0]+oext

            core_files+=' ../'+f
            obj_core_files+=' ../'+fo

        # Set up compiler env.
        sb=hosd.get('batch_prefix','')+'\n'

        sb+=deps.get('compiler',{}).get('bat','')+'\n'

        sb+=eset+' INSTALL_DIR='+_slash(pi)+'\n\n'
        sb+=eset+' BUILD_DIR='+_slash(build_dir)+'\n\n'
        sb+=eset+' CK_TARGET_LIB='+_slash(lib_target)+'\n\n'
        sb+=eset+' CK_BARE_METAL='+_slash(bare_metal)+'\n\n'
        sb+=eset+' CK_CXXFLAGS='+_slash(eifs+flags+eifs)+'\n\n'
        sb+=eset+' CK_LFLAGS='+_slash(eifs+link_flags+eifs)+'\n\n'
        sb+=eset+' CK_SRC_FILES='+_slash(eifs+core_files+eifs)+'\n\n'
        sb+=eset+' ORIGINAL_PACKAGE_DIR='+_slash(pop)+'\n\n'
        sb+=eset+' USE_BARE_METAL='+env.get('USE_BARE_METAL','')+'\n\n'
        sb+=eset+' USE_CPPTHREADS='+env.get('USE_CPPTHREADS','')+'\n\n'
        sb+=eset+' USE_OPENMP='+env.get('USE_OPENMP','')+'\n\n'
        sb+=eset+' USE_NEON='+env.get('USE_NEON','')+'\n\n'
        sb+=eset+' CK_HOST_CPU_NUMBER_OF_PROCESSORS='+str(env.get('CK_HOST_CPU_NUMBER_OF_PROCESSORS', 1))+'\n\n'

        rest_params_var = '%*' if hname == 'win' else '$@'
        sb+=hosd.get('env_call','')+' '+os.path.join(pop,'build'+sext) + ' ' + rest_params_var

        # Prepare build script
        fn=os.path.join(pi, build_script_name + sext)
        try:
            os.makedirs(os.path.dirname(fn))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
        rx=ck.save_text_file({'text_file':fn, 'string':sb})
        if rx['return']>0: return rx

        # Set script as executable if required.
        se=hosd.get('set_executable','')
        if se!='':
            x=se+' '+fn
            rx=os.system(x)

        # Run script.
        rx=os.system(fn)

    # Build the core lib.
    build(lib_prefix+'arm_compute_core', xcore_files, lcore_flags, hosd, deps, pop, bare_metal, 'build_core')

    # Build the core and runtime libs.
    build(lib_prefix+'arm_compute', xcore_files+xfiles, lflags, hosd, deps, pop, bare_metal, 'build')

    return {'return':0}
