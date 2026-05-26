import pyblish.api
import random


class Execution1(pyblish.api.InstancePlugin):
   order = pyblish.api.ExtractorOrder
   hosts = ["maya"]
   label = "Execution 1"
   optional = True

   def process(self, instance):
       if random.choice([True, False]):
           raise Exception("Random error")
       self.log.info(f"Execution 1 {instance.data['name']}")


