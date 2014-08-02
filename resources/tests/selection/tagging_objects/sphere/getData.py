import pymel.core as pm

for node in pm.ls(type='transform'):
    if (node + '.publish') in node.listAttr() and node.publish.get():
        print 'Node: %s, needs exporting as:' % node
        for data in eval(node.dataExport.get()):
            print data
