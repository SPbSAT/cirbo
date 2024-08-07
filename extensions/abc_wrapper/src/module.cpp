#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "run_abc.h"

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

PYBIND11_MODULE(abc_wrapper, m) {
    m.doc() = "Example doc";
    m.def("run_abc_commands", &runAbcCommands, "Enumerates cuts.");

#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}