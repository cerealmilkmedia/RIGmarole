import maya.cmds as cmds
import System.utils as utils
reload(utils)

class Blueprint_UI:
    def __init__(self):
        # Store UI Element in a dictionary
        self.UI_elements = {}
        
        if cmds.window("blueprint_UI_window", exists=True):
            cmds.deleteUI("blueprint_UI_window")

        window_width = 400
        window_height = 590

        self.UI_elements["window"] = cmds.window("blueprint_UI_window", width=window_width, height=window_height, title="Blueprint Module UI", sizeable=False)

        self.UI_elements["top_level_column"] = cmds.columnLayout(adjustableColumn=True, columnAlign="center")

        # Setup tabs
        tab_height = 500
        self.UI_elements["tabs"] = cmds.tabLayout(height=tab_height, innerMarginWidth=5, innerMarginHeight=5)

        tab_width = cmds.tabLayout(self.UI_elements["tabs"], q=True, width=True)
        self.scroll_width = tab_width - 40

        self.initialiseModuleTab(tab_height, tab_width)

        cmds.tabLayout(self.UI_elements["tabs"], edit=True, tabLabelIndex=([1, "Modules"]))

        
        # Display window
        cmds.showWindow(self.UI_elements["window"])

    def initialiseModuleTab(self, tab_height, tab_width):
        scroll_height = tab_height #temp value

        self.UI_elements["module_column"] = cmds.columnLayout(adj=True, rs=3)

        self.UI_elements["module_frame_layout"] = cmds.frameLayout(height=scroll_height, collapsable=False, borderVisible=False, labelVisible=False)

        self.UI_elements["module_scroll"] = cmds.scrollLayout(hst=0)

        self.UI_elements["module_list_column"] = cmds.columnLayout(columnWidth = self.scroll_width, adj=True, rs=2)

        # First separator
        cmds.separator()

        for module in utils.find_all_modules("Modules/Blueprint"):
            self.create_module_install_button(module)
            cmds.setParent(self.UI_elements["module_list_column"])
            cmds.separator()

        cmds.setParent(self.UI_elements["module_column"])
        cmds.separator()


    def create_module_install_button(self, module):
        mod = __import__("Blueprint." + module, {}, {}, [module])
        reload(mod)

        title = mod.TITLE
        description = mod.DESCRIPTION
        icon = mod.ICON

        # Create UI
        button_size = 64
        row = cmds.rowLayout(numberOfColumns=2, columnWidth=([1, button_size]), adjustableColumn=2, columnAttach=([1, "both", 0], [2, "both", 5]))

        self.UI_elements["module_button_" + module] = cmds.symbolButton(width=button_size, height=button_size, image=icon)

        text_column = cmds.columnLayout(columnAlign="center")
        cmds.text(align="center", width=300, label=title)

        cmds.scrollField(text=description, editable=False, width=300, height=button_size - 5, wordWrap=True)
        cmds.setParent(self.UI_elements["module_list_column"])
        