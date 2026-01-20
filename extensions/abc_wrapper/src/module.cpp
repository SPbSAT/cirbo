#ifdef _WIN32
  #ifndef WIN32_LEAN_AND_MEAN
  #define WIN32_LEAN_AND_MEAN
  #endif
  #ifndef NOMINMAX
  #define NOMINMAX
  #endif
  #include <Windows.h>
#endif

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "run_abc.h"

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

PYBIND11_MODULE(abc_wrapper, m) {
    m.doc() = "Example doc";
    m.def("run_abc_commands_c", &runAbcCommands, "Run ABC.");

#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}