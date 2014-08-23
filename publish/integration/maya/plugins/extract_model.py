import os
import time
import shutil
import tempfile

import publish.lib
import publish.plugin

from maya import cmds


@publish.lib.log
class ExtractModelAsMa(publish.plugin.Extractor):
    """Extract family members of Model in Maya ASCII

    Attributes:
        families: The extractor is triggered upon families of "model"
        hosts: This extractor is designed for Autodesk Maya
        version: The current version of the extractor.

    """

    families = ['model']
    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, context):
        """Returns list of value and exception"""

        for instance in context:
            family = instance.config.get('family')

            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, 'publish')

            self.log.info("Extracting locally..")
            previous_selection = cmds.ls(selection=True)
            cmds.select(list(instance), replace=True)
            cmds.file(temp_file, type='mayaBinary', exportSelected=True)

            self.log.info("Moving extraction relative working file..")
            output = self.commit(path=temp_dir, family=family)

            # Record where instance was extracted
            if not hasattr(instance, 'output_paths'):
                instance.output_paths = list()

            instance.output_paths.append(output)

            self.log.info("Clearing local cache..")
            shutil.rmtree(temp_dir)

            if previous_selection:
                cmds.select(previous_selection, replace=True)
            else:
                cmds.select(deselect=True)

            self.log.info("Extraction successful.")

            yield instance, None  # Value, Exception

    def commit(self, path, family):
        """Move to timestamped destination relative workspace"""

        date = time.strftime(publish.config.date_format)

        workspace_dir = cmds.workspace(rootDirectory=True, query=True)
        if not workspace_dir:
            # Project has not been set. Files will
            # instead end up next to the working file.
            workspace_dir = cmds.workspace(dir=True, query=True)
        published_dir = os.path.join(workspace_dir,
                                     publish.config.prefix,
                                     family)

        commit_dir = os.path.join(published_dir, date)

        shutil.copytree(path, commit_dir)

        return commit_dir
