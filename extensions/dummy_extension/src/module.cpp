#include <pybind11/pybind11.h>

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

int add(int i, int j)
{
    return i + j;
}

PYBIND11_MODULE(dummy_extension, m) {
    m.doc() = "Pybind11 example plugin.";
    m.def("add", &add, "Add two numbers");
    m.def("subtract", [](int i, int j) { return i - j; }, "Subtract two numbers");

#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
}