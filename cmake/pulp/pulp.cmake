# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0


if(NOT DEFINED ENV{PULP_OPEN_HOME})
    message(FATAL_ERROR "Environment variable PULP_OPEN_HOME not set.")
endif()

set(PULP_OPEN_HOME $ENV{PULP_OPEN_HOME})
set(PULP_OPEN_RUNTIME_HOME $ENV{PULP_SDK_HOME})

set(SVLIB $ENV{PULP_OPEN_HOME}/rtl/tb/remote_bitbang/librbs)
set(VSIM_FLAGS -gUSE_SDVT_SPI=0 -gUSE_SDVT_CPI=0 -gBAUDRATE=115200 -gENABLE_DEV_DPI=0 -gLOAD_L2=JTAG -gUSE_SDVT_I2S=0)

add_compile_definitions(
  DEEPLOY_PULP_PLATFORM
)

set(DEEPLOY_ARCH PULP)

set(num_threads  ${NUM_CORES})

macro(add_pulp_open_vsim_simulation name)
  add_custom_target(vsim_${name}
	WORKING_DIRECTORY ${PULP_OPEN_HOME}/sim
	DEPENDS ${name}
	COMMAND ${QUESTA} -quiet vopt_tb -L models_lib -L vip_lib -t ps
  "+nowarnTRAN" "+nowarnTSCALE" "+nowarnTFMPC" "+UVM_NO_RELNOTES" "+ENTRY_POINT=0x1c008080" -permit_unmatched_virtual_intf "+VSIM_PATH=${PULP_OPEN_HOME}/sim"
  -gUSE_SDVT_SPI=0 -gUSE_SDVT_CPI=0 -gBAUDRATE=115200 -gENABLE_DEV_DPI=0 -gLOAD_L2=JTAG -gUSE_SDVT_I2S=0
	${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/${name} || true
	COMMENT "Simulating deeploytest with vsim"
	POST_BUILD
	USES_TERMINAL
	VERBATIM
    )
endmacro()

add_compile_options(
  -ffast-math
)

add_link_options(
  -ffast-math
  -Wl,--gc-sections
)
