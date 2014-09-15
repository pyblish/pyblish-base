import sys
import os

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtQml

import pyblish.backend.plugin


class Host(object):
    """This Class is a fake class instead of
        Maya for getting fake information
    """

    context = pyblish.backend.plugin.Context()

    def __init__(self):
        self.instances = []

        instance1 = self.context.create_instance(name='MyInstance1')
        instance1.set_data('family', value='my_family')
        instance1.set_data('document_content', 'Hello World 1!')
        instance1.set_data('document_name', 'MyDocument1.txt')
        self.instances.append(instance1)

        instance2 = self.context.create_instance(name='MyInstance2')
        instance2.set_data('family', value='my_family')
        instance2.set_data('document_content', 'Hello World 2!')
        instance2.set_data('document_name', 'MyDocument2.txt')
        self.instances.append(instance2)

        instance3 = self.context.create_instance(name='Cube_GEO')
        instance3.set_data('family', value='maya')
        instance3.set_data('document_content', 'This is a Cube')
        instance3.set_data('document_name', 'cube.txt')
        self.instances.append(instance3)

        instance4 = self.context.create_instance(name='sphere_GEO')
        instance4.set_data('family', value='nuke')
        instance4.set_data('document_content', 'This is Sphere')
        instance4.set_data('document_name', 'sphere.txt')
        self.instances.append(instance4)


class Pyblish(object):
    """This Class is intended for simulating pyblish"""

    def publish_all(self):
        for type in ('selectors', 'validators', 'extractors', 'conforms'):
            for plugin in pyblish.backend.plugin.discover(type):
                plugin().process_all(Host.context)

            if type == 'validators':
                # Run our mocked up plugin once validators kick in
                ValidateMyInstance().process_all(Host.context)

            if type == 'extractors':
                ExtractDocument().process_all(Host.context)

        print "Your instances is published"


class ValidateMyInstance(pyblish.backend.plugin.Validator):
    families = ['my_family', 'maya', 'nuke']
    hosts = ['*']

    def process_instance(self, instance):
        print "Validating instance: %s" % instance
        # assert instance.data('family') == 'my_family'


class ExtractDocument(pyblish.backend.plugin.Extractor):
    families = ['my_family', 'maya', 'nuke']
    hosts = ['*']

    def process_instance(self, instance):
        content = instance.data('document_content')
        name = instance.data('document_name')

        # Since we aren't in Maya or anything, let's use the Current
        # Working Directory as parent to our document.
        parent_dir = instance.context.data('cwd')

        # The current working directory is being added to the context by
        # one of the included selector plugins. Now let's write the
        # document to disk.
        path = os.path.join(parent_dir, name)
        with open(path, 'w') as f:
            print "Writing message to %s" % path
            f.write(content)


class MyInstance(QtCore.QObject):

    def __init__(self, parent=None):
        super(MyInstance, self).__init__(parent)
        self._name = ''
        self._family = ''
        self._document_content = ''
        self._document_name = ''

    @QtCore.pyqtProperty(str)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @QtCore.pyqtProperty(str)
    def family(self):
        return self._family

    @family.setter
    def family(self, family):
        self._family = family

    @QtCore.pyqtProperty(str)
    def document_content(self):
        return self._document_content

    @document_content.setter
    def document_content(self, document_content):
        self._document_content = document_content

    @QtCore.pyqtProperty(str)
    def document_name(self):
        return self._document_name

    @document_name.setter
    def document_name(self, document_name):
        self._document_name = document_name


class Controller(QtCore.QObject):

    def __init__(self, parent=None):
        super(Controller, self).__init__(parent)
        self.pyblish = Pyblish()
        self._lists = []

        _host = Host()
        for inst in _host.instances:
            myInstance = MyInstance()
            myInstance.name = inst.data(key='name')
            myInstance.family = inst.data(key='family')
            myInstance.document_name = inst.data(key='document_name')
            myInstance.document_content = inst.data(key='document_content')
            self._lists.append(myInstance)



    @QtCore.pyqtSlot()
    def callPublish(self):
        self.pyblish.publish_all()  # pyblish.main.publish_all()

    @QtCore.pyqtProperty(QtQml.QQmlListProperty)
    def lists(self):
        return QtQml.QQmlListProperty(MyInstance, self, self._lists)


def main(qml_file="pyblishLauncher.qml"):

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
