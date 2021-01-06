import maya.cmds as cmds

def find_all_modules(relative_directory):
    # Search the relative directory for all available modules
    # Return a list of all module names (excluding the ".py" extension)
    all_py_files = find_all_files(relative_directory, ".py")

    return_modules = []

    for file in all_py_files:
        if file != "__init__":
            return_modules.append(file)

    return return_modules


def find_all_files(relative_directory, file_extension):
    # Search the relative directory for all files with the give extension
    # Return a list of all file names, excluding the file extension
    import os

    file_directory = os.environ["RIGMAROLE"] + "/" + relative_directory + "/"

    all_files = os.listdir(file_directory)

    # Refine all files, listing only those of the specified file extension
    return_files = []

    for f in all_files:
        split_string = str(f).rpartition(file_extension)

        if not split_string[1] == "" and split_string[2] == "":
            return_files.append(split_string[0])


    return return_files


def find_highest_trailing_number(names, basename):
    import re

    highest_value = 0

    for n in names:
        if n.find(basename) == 0:
            suffix = n.partition(basename)[2]
            if re.match("^[0-9]*$", suffix):
                numerical_element = int(suffix)

                if numerical_element > highest_value:
                    highest_value = numerical_element

    return highest_value


def strip_leading_namespace(nodename):
    if nodename.find(":") == -1:
        return None
    
    split_string = str(nodename).partition(":")
    return [split_string[0], split_string[2]]

def strip_all_namespaces(nodename):
    if str(nodename).find(":") == -1:
        return None
    split_string = str(nodename).rpartition(":")
    return [split_string[0], split_string[2]]



def basic_stretchy_IK(root_joint, end_joint, container=None, lockMinimumLength=True, poleVectorObject=None, scaleCorrectionAttribute=None):
    from math import fabs

    contained_nodes = []

    total_original_length = 0.0

    done = False
    parent = root_joint

    child_joints = []

    while not done:
        children = cmds.listRelatives(parent, children=True)
        children = cmds.ls(children, type="joint")

        if len(children) == 0:
            done = True
        else:
            child = children[0]
            child_joints.append(child)

            total_original_length += fabs(cmds.getAttr(child+".translateX"))

            parent = child

            if child == end_joint:
                done = True


    # Create RP IK on joint chain
    ik_nodes = cmds.ikHandle(sj=root_joint, ee=end_joint, sol="ikRPsolver", n=root_joint+"_ikHandle")
    ik_nodes[1] = cmds.rename(ik_nodes[1], root_joint+"_ikEffector")
    ik_effector = ik_nodes[1]
    ik_handle = ik_nodes[0]
    
    cmds.setAttr(ik_handle+".visibility", 0)
    contained_nodes.extend(ik_nodes)

    # Create pole vector locator 
    if poleVectorObject == None:
        poleVectorObject = cmds.spaceLocator(n=ik_handle+"._poleVectorLocator")[0]
        contained_nodes.append(poleVectorObject)

        cmds.xform(poleVectorObject, worldSpace=True, absolute=True, translation=cmds.xform(root_joint, q=True, worldSpace=True, translation=True))
        cmds.xform(poleVectorObject, worldSpace=True, relative=True, translation=[0.0, 1.0, 0.0])
        cmds.setAttr(poleVectorObject+".visibility", 0)

    pole_vector_constraint = cmds.poleVectorConstraint(poleVectorObject, ik_handle)[0]
    contained_nodes.append(pole_vector_constraint)

    # Create root and end locators
    root_locator = cmds.spaceLocator(n=root_joint+"_rootPosLocator")[0]
    root_locator_point_constraint = cmds.pointConstraint(root_joint, root_locator, maintainOffset=False, n=root_locator+"_pointConstraint")[0]
    end_locator = cmds.spaceLocator(n=end_joint+"_endPosLocator")[0]
    cmds.xform(end_locator, worldSpace=True, absolute=True, translation=cmds.xform(ik_handle, q=True, worldSpace=True, translation=True))
    ik_handle_point_constraint = cmds.pointConstraint(end_locator, ik_handle, maintainOffset=False, n=ik_handle+"_pointConstraint")[0]

    contained_nodes.extend([root_locator, end_locator, root_locator_point_constraint, ik_handle_point_constraint])

    cmds.setAttr(root_locator+".visibility", 0)
    cmds.setAttr(end_locator+".visibility", 0)

    # Compute distance between locators
    root_locator_without_namespace = strip_all_namespaces(root_locator)[1]
    end_locator_without_namespace = strip_all_namespaces(end_locator)[1]

    module_namespace = strip_all_namespaces(root_joint)[0]
    dist_node = cmds.shadingNode("distanceBetween", asUtility=True, n=module_namespace+":distBetween_"+root_locator_without_namespace+"_"+end_locator_without_namespace)

    contained_nodes.append(dist_node)

    cmds.connectAttr(root_locator+"Shape.worldPosition[0]", dist_node+".point1")
    cmds.connectAttr(end_locator+"Shape.worldPosition[0]", dist_node+".point2")

    scale_attr = dist_node+".distance"

    # Divide distance by total_original_length * scale_factor
    scale_factor = cmds.shadingNode("multiplyDivide", asUtility=True, n=ik_handle+"_scaleFactor")
    contained_nodes.append(scale_factor)

    cmds.setAttr(scale_factor+".operation", 2) #Divide   
    cmds.connectAttr(scale_attr, scale_factor+".input1X")
    cmds.setAttr(scale_factor+".input2X", total_original_length)

    translation_driver = scale_factor + ".outputX" 


    # Connect joints to stretchy calulations
    for joint in child_joints:
        mult_node = cmds.shadingNode("multiplyDivide", asUtility=True, n=joint+"_scaleMultiply")
        contained_nodes.append(mult_node)

        cmds.setAttr(mult_node+".input1X", cmds.getAttr(joint+".translateX"))
        cmds.connectAttr(translation_driver, mult_node+".input2X")
        cmds.connectAttr(mult_node+".outputX", joint+".translateX")


    if container != None:
        add_node_to_container(container, contained_nodes, ihb=True)

    returned_dict = {}
    returned_dict["ik_handle"] = ik_handle
    returned_dict["ik_effector"] = ik_effector
    returned_dict["root_locator"] = root_locator
    returned_dict["end_locator"] = end_locator
    returned_dict["poleVectorObject"] = poleVectorObject
    returned_dict["ik_handle_point_constraint"] = ik_handle_point_constraint
    returned_dict["root_locator_point_constraint"] = root_locator_point_constraint

    return returned_dict

def force_scene_update():
    cmds.setToolTo("moveSuperContext") 
    nodes = cmds.ls()

    for node in nodes:
        cmds.select(node, replace=True)
    
    cmds.select(clear=True)
    cmds.setToolTo("selectSuperContext")


def add_node_to_container(container, nodesIn, ihb=False, includeShapes=False, force=False):
    import types

    nodes = []
    if type(nodesIn) is types.ListType:
        nodes = list(nodesIn)
    else:
        nodes = [nodesIn]

    conversion_nodes = []
    for node in nodes:
        node_conversion_nodes = cmds.listConnections(node, source=True, destination=True)
        node_conversion_nodes = cmds.ls(node_conversion_nodes, type="unitConversion")

        conversion_nodes.extend(node_conversion_nodes)
    nodes.extend(conversion_nodes)
    cmds.container(container, edit=True, addNode=nodes, ihb=ihb, includeShapes=includeShapes, force=force)