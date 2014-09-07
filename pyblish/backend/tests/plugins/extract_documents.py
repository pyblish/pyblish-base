import os
import tempfile

import pyblish.backend.lib
import pyblish.backend.plugin


@pyblish.backend.lib.log
class ExtractDocuments(pyblish.backend.plugin.Extractor):
    """Extract instances"""

    hosts = ['python']
    families = ['test.family']
    version = (0, 1, 0)

    def process_instance(self, instance):
        temp_dir = tempfile.mkdtemp()

        for document in instance:
            for name, content in document.iteritems():
                temp_file = os.path.join(temp_dir,
                                         '{0}.txt'.format(name))
                with open(temp_file, 'w') as f:
                    f.write(content)

        self.commit(temp_dir, instance)
