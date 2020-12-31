import os
import maya.cmds as cmds

CLASS_NAME = "ModuleA" 

TITLE = "Module A"
DESCRIPTION = "Test Description for module A"
ICON = os.environ["RIGMAROLE"] + "/Icons/_hand.xpm"

class ModuleA():
    def __init__(self, user_specified_name):
        self.module_name = CLASS_NAME
        self.user_specified_name = user_specified_name
        self.module_namespace = self.module_name + "__" + self.user_specified_name
        
        print self.module_namespace
    
    def install(self):
        cmds.namespace(setNamespace=":")
        cmds.namespace(add=self.module_namespace)
        