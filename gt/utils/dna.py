"""
DNA Utilities
"""

import dna
import dna_viewer
import dnacalib
import maya.cmds as cmds
import os
import logging
import maya.mel as mel
import json


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DNA:

    DNA_FORMAT = ".dna"

    def __init__(self):
        """
        DNA class with core functions related to the Metahuman DNA pipeline.
        """
        if "DNACALIB_FOLDER" not in os.environ.keys():
            logger.warning("Cannot load DNA library folder, please check that is not missing")

        self.ROOT_DIR = os.environ["DNACALIB_FOLDER"]
        self.ROOT_LIB_DIR = f"{self.ROOT_DIR}/lib"
        self.DATA_DIR = f"{self.ROOT_DIR}/data"
        self.DNA_DIR = f"{self.DATA_DIR}/dna_files"
        self.ANALOG_GUI = f"{self.DATA_DIR}/analog_gui.ma"
        self.GUI = f"{self.DATA_DIR}/gui.ma"
        self.ADDITIONAL_ASSEMBLE_SCRIPT = f"{self.DATA_DIR}/additional_assemble_script.py"
        self.ADD_MESH_NAME_TO_BLEND_SHAPE_CHANNEL_NAME = True
        self.joint_position_file = f"{self.DATA_DIR}/joint_position.json"

    @staticmethod
    def open_dna_viewer():
        """Opens DNA Viewer"""
        dna_viewer.show()

    @staticmethod
    def load_dna_reader(path):
        """Loads DNA Reader
        Args:
            path(dir): Directory of the DNA.
        """

        stream = dna.FileStream(path, dna.FileStream.AccessMode_Read, dna.FileStream.OpenMode_Binary)
        reader = dna.BinaryStreamReader(stream, dna.DataLayer_All)
        reader.read()
        if not dna.Status.isOk():
            status = dna.Status.get()
            logger.error(f"Error loading DNA: {status.message}")
        return reader

    def save_dna(self, reader, dna_folder_path, character_name):
        """Saves DNA
        Args:
            reader(str): Original DNA to use as reference.
            dna_folder_path(dir): DNA folder path to save to.
            character_name(str): Character name.
        """
        if character_name.endswith(".dna"):
            char_name = character_name
        else:
            char_name = f"{character_name}{self.DNA_FORMAT}"
        stream = dna.FileStream(
            f"{dna_folder_path}/{char_name}",
            dna.FileStream.AccessMode_Write,
            dna.FileStream.OpenMode_Binary,
        )
        writer = dna.BinaryStreamWriter(stream)
        writer.setFrom(reader)
        writer.write()

        if not dna.Status.isOk():
            status = dna.Status.get()
            logger.error(f"Error saving DNA: {status.message}")

    def assemble_maya_scene(self, dna_folder_path, character_name):
        """Builds maya scene based on the dna
        Args:
            dna_folder_path(dir): Directory of the dna you want to assemble.
            character_name(str): Character name.
        """
        if character_name.endswith(".dna"):
            char_name = character_name
        else:
            char_name = f"{character_name}{self.DNA_FORMAT}"
        dna_output = dna_viewer.DNA(f"{dna_folder_path}/{char_name}")
        config = dna_viewer.RigConfig(
            gui_path=f"{self.DATA_DIR}/gui.ma",
            analog_gui_path=f"{self.DATA_DIR}/analog_gui.ma",
            aas_path=self.ADDITIONAL_ASSEMBLE_SCRIPT,
        )
        dna_viewer.build_rig(dna=dna_output, config=config)

    @staticmethod
    def transfer_joints_positions_distance(pos_a, pos_b):
        """Transfers positions between 2 items
        Args:
            pos_a(int): Position A.
            pos_b(int): Position B.
        """
        return pow((pos_a[0] - pos_b[0]), 2) + pow((pos_a[1] - pos_b[1]), 2) + pow((pos_a[2] - pos_b[2]), 2)

    def find_and_save_joint_positions_in_file(self, reader, joints, file_path):
        """Gets joint positions and saves in an output json
        Args:
            reader(dir): DNA Path used as reference.
            joints(dir): List of joints to save.
            file_path(dir): Character path.
        """

        mesh = reader.getMeshName(0)
        output = {}
        if not cmds.pluginInfo("nearestPointOnMesh.mll", query=True, loaded=True):
            cmds.loadPlugin("nearestPointOnMesh.mll")
        for joint_name in joints:
            cmds.select(joint_name)
            joint_pos = cmds.xform(joint_name, q=True, ws=True, translation=True)
            near_point = mel.eval(f"nearestPointOnMesh {mesh}")
            cmds.setAttr(f"{near_point}.inPositionX", joint_pos[0])
            cmds.setAttr(f"{near_point}.inPositionY", joint_pos[1])
            cmds.setAttr(f"{near_point}.inPositionZ", joint_pos[2])
            best_face = cmds.getAttr(f"{near_point}.nearestFaceIndex")

            face_vtx_str = cmds.polyInfo(f"{mesh}.f[{best_face}]", fv=True)
            buffer = face_vtx_str[0].split()
            closest_vtx = 0
            dist = 10000
            for v in range(2, len(buffer)):
                vtx = buffer[v]
                vtx_pos = cmds.xform(f"{mesh}.vtx[{vtx}]", q=True, ws=True, translation=True)
                new_dist = self.transfer_joints_positions_distance(joint_pos, vtx_pos)
                if new_dist < dist:
                    dist = new_dist
                    closest_vtx = vtx
            output[joint_name] = closest_vtx

        with open(file_path, "w") as out_file:
            json.dump(output, out_file, indent=4)

    @staticmethod
    def run_joints_command(reader, calibrated_dna):
        """Calibrates the DNA with new positions
        Args:
            reader(dir): DNA file to use as reference.
            calibrated_dna(dir): New calibrated DNA.
        """

        # Making arrays for joints' transformations and their corresponding mapping arrays
        joint_translations = []
        joint_rotations = []

        for i in range(reader.getJointCount()):
            joint_name = reader.getJointName(i)

            translation = cmds.xform(joint_name, query=True, translation=True)
            joint_translations.append(translation)

            rotation = cmds.joint(joint_name, query=True, orientation=True)
            joint_rotations.append(rotation)

        set_new_joints_translations = dnacalib.SetNeutralJointTranslationsCommand(joint_translations)
        set_new_joints_rotations = dnacalib.SetNeutralJointRotationsCommand(joint_rotations)

        # Abstraction to collect all commands into a sequence, and run them with only one invocation
        commands = dnacalib.CommandSequence()
        # Add vertex position deltas (NOT ABSOLUTE VALUES) onto existing vertex positions
        commands.add(set_new_joints_translations)
        commands.add(set_new_joints_rotations)

        commands.run(calibrated_dna)
        # Verify that everything went fine
        if not dna.Status.isOk():
            status = dna.Status.get()
            logger.error(f"Error run_joints_command: {status.message}")

    def save_calibrated_dna(self, current_dna_path, joints_to_save, file_path, dna_name):
        """Generates and saves a calibrated DNA
        Args:
            current_dna_path(dir): DNA Path used as reference
            joints_to_save(list): List of joints to save.
            file_path(dir): Path where to save the DNA file.
            dna_name(str): Name of the DNA file.
        """
        # Save surface joints positions
        reader = self.load_dna_reader(current_dna_path)
        self.find_and_save_joint_positions_in_file(reader, joints_to_save, self.joint_position_file)
        # Propagate changes to dna
        calibrated = dnacalib.DNACalibDNAReader(reader)
        self.run_joints_command(reader, calibrated)
        self.save_dna(calibrated, file_path, dna_name)
        logger.info(f"Saved {dna_name} DNA in {file_path}.")
