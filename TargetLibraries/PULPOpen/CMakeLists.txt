# SPDX-FileCopyrightText: 2024 ETH Zurich and University of Bologna
#
# SPDX-License-Identifier: Apache-2.0

file(GLOB_RECURSE SOURCES
  "src/**"
)

if(NOT DEFINED ENV{PULP_SDK_HOME})
  message(FATAL_ERROR "Environment variable PULP_SDK_HOME not set.")
endif()

if(platform STREQUAL "Siracusa" OR platform STREQUAL "Siracusa_w_neureka")
  include(cmake/pulp-sdk-siracusa.cmake)
elseif(platform STREQUAL "PULPOpen")
  include(cmake/pulp-sdk-pulp-open.cmake)
else()
  message(FATAL_ERROR "Unrecognized platform: ${platform}")
endif()

add_deeploy_library(deeploypulp STATIC ${SOURCES})
target_include_directories(deeploypulp
  PUBLIC
  ${CMAKE_CURRENT_LIST_DIR}/inc
)

target_compile_options(deeploypulp PRIVATE
  -Wno-implicit-function-declaration
  -Wno-implicit-int-conversion
  -Wno-sign-conversion
  -Wno-sign-compare
  -Wno-typedef-redefinition
  -Wno-unused-parameter
  -Wno-unused-function
  -Wno-unused-variable
  -Wno-uninitialized
)

# Option to use a prebuilt pulp-nn-mixed library instead of compiling it (default: ON for faster builds).
#
# The library is looked up, in this order, in:
#   1. PULPNN_PREBUILT_DIR (CMake cache variable, or environment variable of the same name), if set.
#      It must hold libpulp-nn-mixed.a and include/, built for the current platform, toolchain and NUM_CORES.
#   2. <install>/pulp-nn-mixed/<platform>-<toolchain>-<NUM_CORES>cores, as installed by `make pulp-nn-mixed`,
#      where <install> is $DEEPLOY_INSTALL_DIR if set, then <Deeploy>/install.
#   3. The legacy in-tree folder TargetLibraries/PULPOpen/prebuilt (only for NUM_CORES=8).
# If none of them holds the library, it is built from source.
option(USE_PREBUILT_PULPNN "Use a prebuilt pulp-nn-mixed library" ON)
set(PULPNN_PREBUILT_DIR "$ENV{PULPNN_PREBUILT_DIR}" CACHE PATH
  "Folder with a prebuilt libpulp-nn-mixed.a and include/ (empty: search the Deeploy install folder)")

if(USE_PREBUILT_PULPNN)
  include(${CMAKE_CURRENT_LIST_DIR}/cmake/pulp-nn-mixed-prebuilt.cmake)

  # Resolved on every configure (not cached), so a build folder reused with another NUM_CORES
  # or platform picks the matching library.
  set(_pulpnn_candidates)
  if(PULPNN_PREBUILT_DIR)
    list(APPEND _pulpnn_candidates ${PULPNN_PREBUILT_DIR})
  else()
    if(DEFINED ENV{DEEPLOY_INSTALL_DIR})
      list(APPEND _pulpnn_candidates $ENV{DEEPLOY_INSTALL_DIR}/pulp-nn-mixed/${PULPNN_PREBUILT_SUBDIR})
    endif()
    list(APPEND _pulpnn_candidates ${CMAKE_CURRENT_LIST_DIR}/../../install/pulp-nn-mixed/${PULPNN_PREBUILT_SUBDIR})
    if(NUM_CORES EQUAL 8)
      list(APPEND _pulpnn_candidates ${CMAKE_CURRENT_LIST_DIR}/prebuilt)
    endif()
  endif()

  set(_pulpnn_dir)
  foreach(_candidate IN LISTS _pulpnn_candidates)
    if(EXISTS ${_candidate}/libpulp-nn-mixed.a AND IS_DIRECTORY ${_candidate}/include)
      get_filename_component(_pulpnn_dir ${_candidate} ABSOLUTE)
      break()
    endif()
  endforeach()

  if(_pulpnn_dir)
    message(STATUS "[Deeploy PULP-OPEN] Using prebuilt pulp-nn-mixed library from ${_pulpnn_dir}")

    # Create imported target for prebuilt library
    add_library(pulp-nn-mixed STATIC IMPORTED)
    set_target_properties(pulp-nn-mixed PROPERTIES
      IMPORTED_LOCATION ${_pulpnn_dir}/libpulp-nn-mixed.a
      INTERFACE_INCLUDE_DIRECTORIES ${_pulpnn_dir}/include
    )
  else()
    list(JOIN _pulpnn_candidates ", " _pulpnn_searched)
    message(WARNING "[Deeploy PULP-OPEN] No prebuilt pulp-nn-mixed library for ${PULPNN_PREBUILT_SUBDIR} (searched: ${_pulpnn_searched})")
    message(WARNING "[Deeploy PULP-OPEN] Falling back to building from source. Run `make pulp-nn-mixed` to install it.")
    set(USE_PREBUILT_PULPNN OFF)
  endif()
endif()

if(NOT USE_PREBUILT_PULPNN)
  # Build pulp-nn from source
  message(STATUS "[Deeploy PULP-OPEN] Building pulp-nn-mixed from source")

  add_subdirectory(../third_party/pulp-nn-mixed ${CMAKE_CURRENT_BINARY_DIR}/pulp-nn-mixed)

  #RW: GCC not recognizing -Wno-typedef-redefinition defined in PULP-NN CMakelist
  target_compile_options(pulp-nn-mixed PRIVATE -Wno-error)
  target_compile_definitions(pulp-nn-mixed PUBLIC NUM_CORES=${NUM_CORES})
endif()

target_include_directories(deeploypulp PUBLIC ${PULP_SDK_INCLUDES})
target_compile_options(deeploypulp PUBLIC ${PULP_SDK_COMPILE_FLAGS})

# add_subdirectory(../third_party/pulp-nn-mixed ${CMAKE_CURRENT_BINARY_DIR}/pulp-nn-mixed)
# target_include_directories(pulp-nn-mixed PUBLIC ${PULP_SDK_INCLUDES})
# target_compile_options(pulp-nn-mixed PUBLIC ${PULP_SDK_COMPILE_FLAGS})

target_link_libraries(deeploypulp PUBLIC pulp-nn-mixed)
target_link_libraries(deeploypulp INTERFACE pulp-sdk)
target_sources(deeploypulp INTERFACE $<TARGET_OBJECTS:pulp-sdk>)

set(PULP_NNX_PLATFORMS "Siracusa;Siracusa_w_neureka")
if (platform IN_LIST PULP_NNX_PLATFORMS)
  if (platform STREQUAL "Siracusa" OR platform STREQUAL "Siracusa_w_neureka")
    set(USE_NEUREKA ON)
  else()
    message(FATAL_ERROR "Missing accelerator flags for platform ${platform}")
  endif()
  add_subdirectory(../third_party/pulp-nnx ${CMAKE_CURRENT_BINARY_DIR}/pulp-nnx)
  target_include_directories(pulp-nnx PUBLIC ${PULP_SDK_INCLUDES})
  target_compile_options(pulp-nnx PUBLIC ${PULP_SDK_COMPILE_FLAGS})
    target_compile_options(pulp-nnx PRIVATE
    -Wno-implicit-int-conversion
    -Wno-sign-conversion
    -Wno-typedef-redefinition
    -Wno-unused-parameter
    -Wno-incompatible-pointer-types
    -Wno-discards-qualifiers
    )
  target_link_libraries(deeploypulp INTERFACE pulp-nnx)
endif()
