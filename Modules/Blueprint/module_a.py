import os
import maya.cmds as cmds
import System.utils as utils
reload(utils)

CLASS_NAME = "ModuleA" 

TITLE = "Module A"
DESCRIPTION = "Test Description for module A"
ICON = os.environ["RIGMAROLE"] + "/Icons/_hand.xpm"

class ModuleA():
    def __init__(self, user_specified_name):
        self.module_name = CLASS_NAME
        self.user_specified_name = user_specified_name
        self.module_namespace = self.module_name + "__" + self.user_specified_name
        self.container_name = self.module_namespace + ":module_container"
        self.joint_info = [["root_joint", [0.0, 0.0, 0.0]], ["end_joint", [4.0, 0.0, 0.0]]]
    
    def install(self):
        cmds.namespace(setNamespace=":")
        cmds.namespace(add=self.module_namespace)
        
        self.joints_grp = cmds.group(empty=True, name=self.module_namespace+":joints_grp")
        self.hierarchy_representation_grp = cmds.group(empty=True, name=self.module_namespace+".hierarchyRepresentation_grp")
        self.orientation_controls_grp = cmds.group(empty=True, name=self.module_namespace+":orientation_controls_grp")
        self.module_grp = cmds.group([self.joints_grp, self.hierarchy_representation_grp, self.orientation_controls_grp], name=self.module_namespace+":module_grp")

        cmds.container(name=self.container_name, addNode=self.module_grp, ihb=True)
        cmds.select(clear=True)

        index = 0
        joints = []

        for joint in self.joint_info:
            joint_name = joint[0]
            joint_pos = joint[1]

            parent_joint = ""
            if index > 0:
                parent_joint = self.module_namespace + ":" + self.joint_info[index - 1][0]
                cmds.select(parent_joint, replace=True)

            joint_name_full = cmds.joint(n=self.module_namespace+":"+joint_name, p=joint_pos)
            joints.append(joint_name_full)

            cmds.setAttr(joint_name_full+".visibility", 0)

            utils.add_node_to_container(self.container_name, joint_name_full) 
           
            cmds.container(self.container_name, edit=True, publishAndBind=[joint_name_full+".rotate", joint_name+"_R"])
            cmds.container(self.container_name, edit=True, publishAndBind=[joint_name_full+".rotateOrder", joint_name+"_rotateOrder"] )

            if index > 0:
                cmds.joint(parent_joint, edit=True, orientJoint="xyz", sao="yup")

            index += 1
        
        cmds.parent(joints[0], self.joints_grp, absolute=True)

        self.initialis_module_transfom(self.joint_info[0][1])

        translation_controls = []
        for joint in joints:
            translation_controls.append(self.create_translation_control_at_joint(joint)) 

        

        root_joint_point_constraint = cmds.pointConstraint(translation_controls[0], joints[0], maintainOffset=False, name=joints[0]+"_pointConstraint")

        utils.add_node_to_container(self.container_name, root_joint_point_constraint)
        
        # Setup stretchy joint segments
        for index in range(len(joints) - 1):
            self.setup_stretchy_joint_segment(joints[index], joints[index+1])

        # NON DEFAULT FUNCTIONALITY
        self.create_orientation_control(joints[0], joints[1])
    

        utils.force_scene_update()

        cmds.lockNode(self.container_name, lock=True, lockUnpublished=True)

    def create_translation_control_at_joint(self, joint):
        pos_control_file = os.environ["RIGMAROLE"] + "/ControlObjects/Blueprint/translation_control.ma"
        cmds.file(pos_control_file, i=True)

        container = cmds.rename("translation_control_container", joint+"_translation_control_container")
        utils.add_node_to_container(self.container_name, container)
        

        for node in cmds.container(container, q=True, nodeList=True): 
            cmds.rename(node, joint+"_"+node, ignoreShape=True)
        
        control = joint + "_translation_control"
        cmds.parent(control, self.module_transform, absolute=True )

        joint_pos = cmds.xform(joint, q=True, worldSpace=True, translation=True)
        cmds.xform(control, worldSpace=True, absolute=True, translation=joint_pos)

        nice_name = utils.strip_leading_namespace(joint)[1]
        attr_name = nice_name + "_T"

        cmds.container(container, edit=True, publishAndBind=[control+".translate", attr_name])
        cmds.container(self.container_name, edit=True, publishAndBind=[container+"."+attr_name, attr_name])

        return control

    def get_translation_control(self, joint_name):
        return joint_name + "_translation_control"

    def setup_stretchy_joint_segment(self, parent_joint, child_joint):
        parent_translation_control = self.get_translation_control(parent_joint)
        child_translation_control = self.get_translation_control(child_joint)

        pole_vector_locator = cmds.spaceLocator(n=parent_translation_control+"_poleVector")[0]
        pole_vector_locator_grp = cmds.group(pole_vector_locator, n=pole_vector_locator+"_parentConstraintGrp")

        cmds.parent(pole_vector_locator_grp, self.module_grp, absolute=True)
        parent_constraint = cmds.parentConstraint(parent_translation_control, pole_vector_locator_grp, maintainOffset=False)[0]

        cmds.setAttr(pole_vector_locator+".visibility", 0)

        cmds.setAttr(pole_vector_locator+".ty", -0.5)

        ik_nodes = utils.basic_stretchy_IK(parent_joint, child_joint, container=self.container_name, lockMinimumLength=False, poleVectorObject=pole_vector_locator, scaleCorrectionAttribute=None)

        ik_handle = ik_nodes["ik_handle"]
        root_locator = ik_nodes["root_locator"]
        end_locator = ik_nodes["end_locator"]

        child_point_constraint = cmds.pointConstraint(child_translation_control, end_locator, maintainOffset=False, n=end_locator+"_pointConstraint" )[0]

        utils.add_node_to_container(self.container_name,[pole_vector_locator_grp, parent_constraint, child_point_constraint], ihb=True )
       

        for node in [ik_handle, root_locator, end_locator]:
            cmds.parent(node, self.joints_grp, absolute=True)
            cmds.setAttr(node+".visibility", 0)
        
        self.create_hierarchy_representation(parent_joint, child_joint)

    def create_hierarchy_representation(self, parent_joint, child_joint):
        nodes = self.create_stretchy_object("/ControlObjects/Blueprint/hierarchy_representation.ma", "hierarchy_representation_container", "hierarchy_representation", parent_joint, child_joint)

        constrained_grp = nodes[2]
        cmds.parent(constrained_grp, self.hierarchy_representation_grp, relative=True)

    def create_stretchy_object(self, object_relative_file_path, object_container_name, object_name, parent_joint, child_joint):
        object_file = os.environ["RIGMAROLE"] + object_relative_file_path
        cmds.file(object_file, i=True)

        object_container = cmds.rename(object_container_name, parent_joint+"_"+object_container_name)
        
        for node in cmds.container(object_container, q=True, nodeList=True):
            cmds.rename(node, parent_joint+"_"+node, ignoreShape=True)

        object = parent_joint+"_"+object_name

        constrained_grp = cmds.group(empty=True, name=object+"_parentConstraint_grp")
        cmds.parent(object, constrained_grp, absolute=True) 

        parent_contraint = cmds.parentConstraint(parent_joint, constrained_grp, maintainOffset=False)[0]

        cmds.connectAttr(child_joint+".translateX", constrained_grp+".scaleX")
        scale_constraint = cmds.scaleConstraint(self.module_transform, constrained_grp, skip=["x"], maintainOffset=False)[0]


        utils.add_node_to_container(object_container, [constrained_grp, parent_contraint, scale_constraint], ihb=True)
        utils.add_node_to_container(self.container_name, object_container)
        

        return(object_container, object, constrained_grp)

    def initialis_module_transfom(self, root_pos):
        control_grp_file = os.environ["RIGMAROLE"] + "/ControlObjects/Blueprint/controlGroup_control.ma"
        cmds.file(control_grp_file, i=True)

        self.module_transform = cmds.rename("controlGroup_control", self.module_namespace+":module_transform")
        cmds.xform(self.module_transform, worldSpace=True, absolute=True, translation=root_pos)
        utils.add_node_to_container(self.container_name, self.module_transform, ihb=True)

        # Setup global scaling
        cmds.connectAttr(self.module_transform+".scaleY", self.module_transform+".scaleX")
        cmds.connectAttr(self.module_transform+".scaleY", self.module_transform+".scaleZ")

        cmds.aliasAttr("globalScale", self.module_transform+".scaleY")

        cmds.container(self.container_name, edit=True, publishAndBind=[self.module_transform+".translate", "moduleTransform_T"])
        cmds.container(self.container_name, edit=True, publishAndBind=[self.module_transform+".rotate", "moduleTransform_R"])
        cmds.container(self.container_name, edit=True, publishAndBind=[self.module_transform+".globalScale", "moduleTransform_globalScale"])

    def delete_hierarchy_representation(self, parent_joint):
        hierarchy_container = parent_joint + "_hierarchy_representation_container"
        cmds.delete(hierarchy_container)

    def create_orientation_control(self, parent_joint, child_joint):
        self.delete_hierarchy_representation(parent_joint)

        nodes = self.create_stretchy_object("/ControlObjects/Blueprint/orientation_control.ma", "orientation_control_container", "orientation_control", parent_joint, child_joint)

        orientation_container = nodes[0]
        orientation_control = nodes[1]
        constrained_grp = nodes[2]

        cmds.parent(constrained_grp, self.orientation_controls_grp, relative=True)

        parent_joint_without_namespace = utils.strip_all_namespaces(parent_joint)[1]

        attr_name = parent_joint_without_namespace + "_orientation"
        cmds.container(orientation_container, edit=True, publishAndBind=[orientation_control+".rotateX", attr_name])
        cmds.container(self.container_name, edit=True, publishAndBind=[orientation_container+"."+attr_name, attr_name])

        return orientation_control


