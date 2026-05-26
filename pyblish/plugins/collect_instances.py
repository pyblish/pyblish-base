import pyblish.api


INSTANCE_DEFAULTS = {
    "foo": {
        "family": "default",
        "asset_type": "ve",
        "entity_name": "main",
        "asset_name": "Halftrack",
        "entity_variant": "main",
        "lod_template_path": "config/template/houdini/template_export_mod.hip",
        "override_shape_attributes": False,
        "comment": "",
        "optional": True,
        "plugins": {
            "Execution 2": False,
        },
    },
    "bar": {
        "family": "default",
        "asset_type": "ve",
        "entity_name": "main",
        "asset_name": "Halftrack",
        "entity_variant": "variant_a",
        "lod_template_path": "config/template/houdini/template_export_mod.hip",
        "override_shape_attributes": False,
        "comment": "",
        "optional": True,
        "plugins": {
            "Execution 1": True,
        },
    },
    "baz": {
        "family": "default",
        "asset_type": "ve",
        "entity_name": "main",
        "asset_name": "Halftrack",
        "entity_variant": "variant_b",
        "lod_template_path": "config/template/houdini/template_export_mod.hip",
        "override_shape_attributes": True,
        "comment": "",
        "optional": True,
    },
}


class CreateInstances(pyblish.api.ContextPlugin):
    label = "Create instances"
    order = pyblish.api.CollectorOrder
    hosts = ["maya"]

    def process(self, context):
        for name in ("foo", "bar", "baz"):
            instance_obj = context.create_instance(name)
            print(f"sCreating instance {name}, {instance_obj.data} type {type(instance_obj)}")
            defaults = INSTANCE_DEFAULTS.get(name, {})
            instance_obj.data.update(defaults)
            instance_obj.data.setdefault("publish", True)
