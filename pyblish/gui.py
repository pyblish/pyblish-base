import pyblish.api


def show(parent=None):
    """Try showing the most desirable GUI
    This function cycles through the currently registered
    graphical user interfaces, if any, and presents it to
    the user.

    parent (QWidget): the Parent widget to pass to GUI, preferably parented under QApplication
    to avoid any dependencies on Qt, pyside2, or your favorite QT wrapper:
    if you don't have a QApplication instance, instantiate one yourself

    return a QWidget instance
    """
    gui_show = _discover_gui()

    if gui_show is None:
        raise RuntimeError("No GUI found")
    else:
        return gui_show(parent)


def _discover_gui():
    """Return the most desirable of the currently registered GUIs"""

    # Prefer last registered
    guis = reversed(pyblish.api.registered_guis())

    for gui in guis:
        try:
            gui_show = __import__(gui).show
        except (ImportError, AttributeError) as e:
            print("Failed to import GUI: %s" % gui, e)
            continue
        else:
            return gui_show
