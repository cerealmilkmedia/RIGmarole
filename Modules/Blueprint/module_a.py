import os

CLASS_NAME = "ModuleA" 

TITLE = "Module A"
DESCRIPTION = "Test Description for module A"
ICON = os.environ["RIGMAROLE"] + "/Icons/_hand.xpm"

class ModuleA():
    def __init__(self):
        print "We're in the constructor"

    
    def install(self):
        print "Install " + CLASS_NAME