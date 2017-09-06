
CXX=$(CK_CXX)
AR_RCS=$(CK_LB)

CXXFLAGS=$(CK_COMPILER_FLAGS_OBLIGATORY) $(CK_FLAGS_STATIC_LIB) $(CK_CXXFLAGS) $(CK_FLAG_PREFIX_INCLUDE).. -MMD -MP
LDFLAGS=$(CK_LFLAGS)

# SRC_DIR=$(BUILD_DIR)/src
SRC_DIR=../src

CORE_SRC=$(wildcard $(SRC_DIR)/core/*.cpp) \
	$(wildcard $(SRC_DIR)/core/CPP/*.cpp) \
	$(wildcard $(SRC_DIR)/core/CPP/kernels/*.cpp)

RUNTIME_SRC=$(wildcard $(SRC_DIR)/runtime/*.cpp) \
	$(SRC_DIR)/runtime/CPP/SingleThreadScheduler.cpp

ifeq ($(USE_BARE_METAL), ON)
ifeq ($(USE_CPPTHREADS), ON)
$(error C++11 threads not supported in bare_metal.)
endif
ifeq ($(USE_OPENMP), ON)
$(error OpenMP not supported in bare_metal.)
endif
endif

ifeq ($(USE_CPPTHREADS), ON)
RUNTIME_SRC += $(SRC_DIR)/runtime/CPP/CPPScheduler.cpp
endif

ifeq ($(USE_OPENMP), ON)
RUNTIME_SRC += $(SRC_DIR)/runtime/OMP/OMPScheduler.cpp
endif

ifeq ($(USE_NEON), ON)
CORE_SRC += $(wildcard $(SRC_DIR)/core/NEON/*.cpp) \
	$(wildcard $(SRC_DIR)/core/NEON/kernels/*.cpp)
RUNTIME_SRC += $(wildcard $(SRC_DIR)/runtime/NEON/*.cpp) \
	$(wildcard $(SRC_DIR)/runtime/NEON/functions/*.cpp)
endif

CORE_OBJ=$(CORE_SRC:.cpp=.o)
CORE_DEP=$(CORE_SRC:.cpp=.d)

SRC=$(CORE_SRC) $(RUNTIME_SRC)
OBJ=$(SRC:.cpp=.o)
DEP=$(SRC:.cpp=.d)

TARGET_DIR=$(INSTALL_DIR)/install/lib

LIB_CORE=libarm_compute_core
LIB=libarm_compute

LIB_CORE_STATIC=$(TARGET_DIR)/$(LIB_CORE)$(CK_LIB_EXT)
LIB_CORE_DYNAMIC=$(TARGET_DIR)/$(LIB_CORE)$(CK_DLL_EXT)

LIB_STATIC=$(TARGET_DIR)/$(LIB)$(CK_LIB_EXT)
LIB_DYNAMIC=$(TARGET_DIR)/$(LIB)$(CK_DLL_EXT)

.PHONY: all clean

all: $(LIB_CORE_STATIC) $(LIB_CORE_DYNAMIC) $(LIB_STATIC) $(LIB_DYNAMIC)

-include $(DEP)

$(LIB_CORE_STATIC): $(CORE_OBJ) | $(TARGET_DIR)
	$(AR_RCS) $@ $^

$(LIB_CORE_DYNAMIC): $(CORE_OBJ) | $(TARGET_DIR)
	$(CXX) $(CK_FLAGS_DLL) $(CXXFLAGS) $(CK_FLAGS_OUTPUT) $@ $(CK_FLAGS_DLL_EXTRA) $(CK_LD_FLAGS_MISC) $(CK_LD_FLAGS_EXTRA) $^ $(CK_LFLAGS)

$(LIB_STATIC): $(OBJ) | $(TARGET_DIR)
	$(AR_RCS) $@ $^

$(LIB_DYNAMIC): $(OBJ) | $(TARGET_DIR)
	$(CXX) $(CK_FLAGS_DLL) $(CXXFLAGS) $(CK_FLAGS_OUTPUT) $@ $(CK_FLAGS_DLL_EXTRA) $(CK_LD_FLAGS_MISC) $(CK_LD_FLAGS_EXTRA) $^ $(CK_LFLAGS)

clean:
	rm -rf $(OBJ) $(LIB_CORE_STATIC) $(LIB_CORE_DYNAMIC) $(LIB_STATIC) $(LIB_DYNAMIC) $(DEP)

$(TARGET_DIR):
	mkdir -p $@
