# The macro creates a new fpga_<name> target
macro(add_pulp_open_fpga_bin_generation name)
    add_custom_target(fpga_${name}
        COMMAND ${CMAKE_COMMAND} -E echo "[CMAKE] Generating FPGA binary"
        DEPENDS ${name}
    )
endmacro()