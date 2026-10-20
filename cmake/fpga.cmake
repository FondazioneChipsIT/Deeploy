# SPDX-FileCopyrightText: 2026 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

set(DEEPLOY_GDB_PORT 3344 CACHE STRING "OpenOCD GDB port of the pulp-open FPGA")

# The macro creates a new fpga_<name> target and the GDB script that puts the test on
# the board: connect, preload the L3 image into the HyperRAM (if the network has L3
# buffers), load the ELF. OpenOCD must have sourced the pulp-sdk OpenOCD helper
# tools/openocd/pulp_hyperram.tcl. Continue (and the UART) are left to the user.
macro(add_pulp_open_fpga_bin_generation name)
    set(FPGA_GDB_SCRIPT ${CMAKE_BINARY_DIR}/fpga_${name}.gdb)
    set(FPGA_L3_PRELOAD ${GENERATED_SOURCE}/fpga/l3_preload.gdb)

    set(FPGA_GDB_CONTENT "file $<TARGET_FILE:${name}>\ntarget extended-remote :${DEEPLOY_GDB_PORT}\n")
    if(EXISTS ${FPGA_L3_PRELOAD})
        string(APPEND FPGA_GDB_CONTENT "source ${FPGA_L3_PRELOAD}\n")
    endif()
    string(APPEND FPGA_GDB_CONTENT "load\n")

    file(GENERATE OUTPUT ${FPGA_GDB_SCRIPT} CONTENT "${FPGA_GDB_CONTENT}")

    add_custom_target(fpga_${name}
        COMMAND ${CMAKE_COMMAND} -E echo "[CMAKE] FPGA binary: $<TARGET_FILE:${name}>"
        COMMAND ${CMAKE_COMMAND} -E echo "[CMAKE] FPGA GDB script: ${FPGA_GDB_SCRIPT}"
        DEPENDS ${name}
    )
endmacro()
