cmake_minimum_required(VERSION 3.4...3.18)
project(boolean_circuit_tool)

set(CMAKE_CXX_STANDARD 17 CACHE STRING "C++ version selection")  # or 11, 14, 17, 20
set(CMAKE_CXX_STANDARD_REQUIRED ON)  # optional, ensure standard is supported
set(CMAKE_CXX_EXTENSIONS OFF)  # optional, keep compiler extensions off

# Force mockturtle to not compile heavy examples.
# Note: must be before mockturtle's CMakeLists is added.
SET(MOCKTURTLE_EXAMPLES OFF CACHE BOOL "Build examples" FORCE)

add_subdirectory(third_party/pybind11)
add_subdirectory(third_party/mockturtle)

pybind11_add_module(dummy_extension extensions/dummy_extension/src/module.cpp)

pybind11_add_module(mockturtle_wrapper extensions/mockturtle_wrapper/src/module.cpp)

target_link_libraries(mockturtle_wrapper PRIVATE mockturtle)

target_include_directories(mockturtle_wrapper PRIVATE third_party)
