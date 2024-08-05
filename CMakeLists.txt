cmake_minimum_required(VERSION 3.4...3.18)
project(boolean_circuit_tool)

add_subdirectory(third_party/pybind11)
add_subdirectory(third_party/mockturtle)

pybind11_add_module(dummy_extension extensions/dummy_extension/src/module.cpp)

pybind11_add_module(mockturtle_wrapper extensions/mockturtle_wrapper/src/module.cpp)
target_link_libraries(mockturtle_wrapper PRIVATE mockturtle)

target_include_directories(mockturtle_wrapper PRIVATE third_party)
