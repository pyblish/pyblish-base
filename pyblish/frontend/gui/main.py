import sys
import os

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtQml

# import maya.cmds as cmds

# import pyblish.main


class Instance(set):
    pass


class Host(object):
    """This Class is a fake class instead of
        Maya for getting fake information
    """
    pass


class Pyblish(object):
    """This Class is intended for simulating pyblish"""

    def publish_all(self):
        print "Your instances is published"


class Controller(QtCore.QObject):

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)
        self.pyblish = Pyblish()

    @QtCore.pyqtSlot()
    def callPublish(self):
        self.pyblish.publish_all()  # pyblish.main.publish_all()


def main(qml_file="pyblish.qml"):

    # Show QML Window
    full_directory = os.path.dirname(os.path.abspath(__file__))

    app = QtWidgets.QApplication(sys.argv)

    QtQml.qmlRegisterType(Controller, 'Controller', 1, 0, 'Controller')
    engine = QtQml.QQmlApplicationEngine()
    qml_file = os.path.join(full_directory, qml_file)
    engine.load(str(qml_file))
    window = engine.rootObjects()[0]
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
