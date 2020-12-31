import os

CLASS_NAME = "ModuleB" 

TITLE = "Module B"
DESCRIPTION = "Test Description for module B"
ICON = os.environ["RIGMAROLE"] + "/Icons/_hinge.xpm"

class ModuleB():
    def __init__(self):
        print "We're in the constructor"

    
    def install(self):
        print "Install " + CLASS_NAME
        