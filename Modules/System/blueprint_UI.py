import maya.cmds as cmds

class Blueprint_UI:
    def __init__(self):
        # Store UI Element in a dictionary
        self.UI_elements = {}
        
        if cmds.window("blueprint_UI_window", exists=True):
            cmds.deleteUI("blueprint_UI_window")

        window_width = 400
        window_height = 590

        self.UI_elements["window"] = cmds.window("blueprint_UI_window", width=window_width, height=window_height, title="Blueprint Module UI", sizeable=False)


        # Display window
        cmds.showWindow(self.UI_elements["window"])