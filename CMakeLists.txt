cmake_minimum_required(VERSION 3.4...3.18)
project(cirbo)

set(CMAKE_CXX_STANDARD 17 CACHE STRING "C++ version selection")  # or 11, 14, 17, 20
set(CMAKE_CXX_STANDARD_REQUIRED ON)  # optional, ensure standard is supported
set(CMAKE_CXX_EXTENSIONS OFF)  # optional, keep compiler extensions off

option(DISABLE_ABC_CEXT "Controls if ABC should be compiled." OFF)

# Force mockturtle to not compile heavy examples.
# Note: must be before mockturtle's CMakeLists is added.
SET(MOCKTURTLE_EXAMPLES OFF CACHE BOOL "Build examples" FORCE)

add_subdirectory(third_party/pybind11)
add_subdirectory(third_party/mockturtle)

pybind11_add_module(mockturtle_wrapper extensions/mockturtle_wrapper/src/module.cpp)
target_link_libraries(mockturtle_wrapper PRIVATE mockturtle)
target_include_directories(mockturtle_wrapper PRIVATE third_party)

# ABC related libs can be disabled using environment variable.
IF(NOT DISABLE_ABC_CEXT)
    # Disabled because it requires gnu readline to be installed on build
    # machine, but is not necessary for the ABC compilation as library.
    set(READLINE_FOUND FALSE CACHE BOOL "" FORCE)

    add_subdirectory(third_party/abc)

    # Fixes case in CI, when ABC compilation
    # fails with "#error unknown platform" on
    # macos runners (both intel and apple silicon).
    if(NOT WIN32)
      target_compile_definitions(libabc-pic PRIVATE ABC_USE_STDINT_H)
      if(TARGET libabc)
        target_compile_definitions(libabc PRIVATE ABC_USE_STDINT_H)
      endif()
    endif()

    pybind11_add_module(abc_wrapper extensions/abc_wrapper/src/module.cpp)
    target_link_libraries(abc_wrapper PRIVATE libabc-pic)
    target_include_directories(abc_wrapper PRIVATE third_party)
ENDIF(NOT DISABLE_ABC_CEXT)
