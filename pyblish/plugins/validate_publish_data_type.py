import pyblish.api


class ValidatePublishDataType(pyblish.api.ContextPlugin):
    """Validates the "publish" data members type to be boolean."""

    order = pyblish.api.ValidatorOrder
    label = "Publish Data Type"

    def process(self, context):

        for instance in context:
            msg = "\"publish\" data member on {0} is not a boolean.".format(
                instance
            )
            assert isinstance(instance.data.get("publish", True), bool), msg
