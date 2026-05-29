name = "pyblish_base"
version = "1.8.12"

description = "Plug-in driven automation framework for content"
authors = ["Abstract Factory and Contributors"]

requires = []

build_system = "cmake"


def commands():
    env.PYTHONPATH.prepend("{root}")
