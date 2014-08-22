import os
import time
import shutil
import tempfile

import publish.lib
import publish.abstract

from maya import cmds


@publish.lib.log
class ExtractReviewAsPng(publish.abstract.Extractor):
    """Extract family members as image-sequence (png)

    Some things are lacking; including setting shaded state
    (shaded, textured et. al.). As well as including any HUD
    information, e.g. frame-range, camera name or shot details.

    The plugin defines a number of overrides to be written into
    the instance upon being published.

    Overrides:
        startFrame (int): The equivalent of cmds.playblast(startTime)
        endFrame (int): --> endTime
        format (str): --> format
        width (int): --> width
        height (int): --> height
        compression (str): --> compression


    """

    @property
    def families(self):
        return ['review']

    @property
    def hosts(self):
        return ['maya']

    @property
    def version(self):
        return (0, 1, 0)

    def process(self):
        """Extracting a playblast is quite involved.

        Step one is finding an appropriate panel to playblast from.
        The panel must be a valid "modelPanel", which means a 3d view.
        We modify the current camera of this panel to the one specified
        in our publish, and then trigger a playblast. The next step is
        restoring the previous panels and cameras so as to make the publish
        as transparent to the end-user as possible.

        ..note:: At the moment, if there is no active modelPanel,
            the publish fails.

        """

        self.log.info("Extracting playblast")

        temp_dir = tempfile.mkdtemp()

        # Get cameras
        cameras = list()
        for node in self.instance:
            self.log.debug("Looking for camera: {0}".format(node))

            test_node = node
            if cmds.nodeType(test_node) == 'transform':
                try:
                    test_node = cmds.listRelatives(node, shapes=True)[0]
                except TypeError:
                    # listRelatives returns None if no items are found
                    # which causes a TypeError, as opposed to an IndexError
                    # which is normally the case on empty lists.
                    continue

            if cmds.nodeType(test_node) == 'camera':
                cameras.append(node)

        if not cameras:
            self.log.info("No cameras found..")
            raise ValueError("No cameras found for Review '{0}'".format(
                self.instance.name))

        # Setup panel
        previous_panel = cmds.getPanel(withFocus=True)

        # If we're taking over a model panel, ensure we also
        # restore the camera which was used at the time of publish.
        if previous_panel in cmds.getPanel(type='modelPanel'):
            previous_camera = cmds.modelPanel(previous_panel,
                                              query=True,
                                              camera=True)
        else:
            previous_camera = None

        playblast_panel = cmds.getPanel(withLabel='Persp View')
        cmds.panel(previous_panel, edit=True, replacePanel=playblast_panel)

        # Establish configuration
        config = self.instance.config

        min_time = cmds.playbackOptions(minTime=True, query=True)
        max_time = cmds.playbackOptions(maxTime=True, query=True)
        default_width = cmds.getAttr('defaultResolution.width')
        default_height = cmds.getAttr('defaultResolution.height')

        playblast_kwargs = {
            'percent': 100,
            'quality': 100,
            'offScreen': True,
            'viewer': False,
            'startTime': config.get('startFrame', min_time),
            'endTime': config.get('endFrame', max_time),
            'format': config.get('format', 'image'),
            'width': config.get('width', default_width),
            'height': config.get('height', default_height),
            'compression': config.get('compression', 'png')
        }

        self.log.info("Configuration: {0}".format(playblast_kwargs))

        # Make one playblast per included camera
        try:
            for camera in cameras:
                self.log.info("Playblasting {camera}".format(camera=camera))
                cmds.lookThru(playblast_panel, camera)

                cmds.isolateSelect(playblast_panel, state=True)

                for obj in self.instance:
                    cmds.isolateSelect(playblast_panel, addDagObject=obj)

                temp_file = os.path.join(temp_dir, camera, camera)
                playblast_kwargs['filename'] = temp_file

                self.log.info("Running playblast..")
                cmds.playblast(**playblast_kwargs)  # Do not open player
                self.log.info("Completed at {0}".format(temp_file))

        finally:
            # No matter what happens, always restore panels
            cmds.refresh(suspend=True)

            self.log.info("Restoring panels")
            cmds.isolateSelect(playblast_panel, state=False)

            if previous_camera:
                cmds.lookThru(playblast_panel, previous_camera)

            cmds.panel(playblast_panel, edit=True, replacePanel=previous_panel)
            cmds.refresh(suspend=False)

        # Move temporary files to directory relative the
        # current working file.
        family = self.instance.config.get('family')

        self.commit(temp_dir, family=family)
        self.log.info("_extract_model: Clearing local cache..")
        shutil.rmtree(temp_dir)

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
