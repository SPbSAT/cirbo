from pybind11.setup_helpers import Pybind11Extension, build_ext


ext_modules = [
    Pybind11Extension(
        "dummy_extension",
        ["extensions/dummy_extension/src/main.cpp"],
    ),
]


def build(setup_kwargs):
    setup_kwargs.update({
        "ext_modules": ext_modules,
        "cmd_class": {"build_ext": build_ext},
        "zip_safe": False,
    })
