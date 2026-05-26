import pyblish.api


class Execution2(pyblish.api.InstancePlugin):
   order = pyblish.api.ExtractorOrder
   hosts = ["maya"]
   label = "Execution 2"
   optional = True

   def process(self, instance):
       self.log.info(f"Execution 2 {instance.data['name']}")


