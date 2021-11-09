"""
 GT Path Manager - A script for quickly repathing many elements in Maya.
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-08-26 - github.com/TrevisanGMW
 
 0.1a - 2020-08-26
 Created initial setup, added table and icons for file nodes
 
 1.0 - 2020-12-02
 Initial Release
 Added support for UDIMS and Image Sequences to the "file" node
 Added support for a lot of common nodes: 
    audio, cacheFile, AlembicNode, BifMeshImportNode, gpuCache, MASH_Audio
 Added support for Arnold Lights
    aiPhotometricLight, aiStandIn, aiVolume
 Added support for Redshift Lights
    RedshiftProxyMesh, RedshiftVolumeShape, RedshiftNormalMap, RedshiftDomeLight, RedshiftIESLight
 Added support for Reference Files through OpenMaya API (Instead of PyMEL)
 
 1.1 - 2020-12-03
 Added support for Image Planes
 
 1.2 - 2021-05-11
 Made script compatible with Python 3 (Maya 2022+)
 
 Todo:
    Add support for Goalem Nodes
        'SimulationCacheProxyManager', 'destinationTerrainFile', accepts_empty=True
        'SimulationCacheProxyManager', 'skinningShaderFile', accepts_empty=True
        'CrowdEntityTypeNode', 'characterFile', accepts_empty=True
        'CharacterMakerLocator', 'currentFile', accepts_empty=True
        'TerrainLocator', 'navMeshFile', accepts_empty=True
        'SimulationCacheProxy', 'inputCacheDir', accepts_empty=True
    # Manage Multiple Files?
        'SimulationCacheProxy', 'characterFiles', accepts_empty=True, checks_multiple_paths=True
        'CrowdManagerNode', 'characterFiles', accepts_empty=True, checks_multiple_paths=True
         
    Add:
    Only Files Checkbox
 
"""
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import time
import sys
import os
import re

# Script Name
script_name = "GT Path Manager" 

# Version
script_version = '1.2'

# Python Version
python_version = sys.version_info.major

def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    
    if python_version == 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)
    
    
def list_reference_pairs():
    ''' 
    Returns all references and their paths. Used to get a reference path when the file is not found.
    cmds.referenceQuery would return an error.
    
            Returns:
                reference_list (list): A list of pairs, containing reference name and reference path
    
    '''
    it = om.MItDependencyNodes(om.MFn.kReference)
    ref_nodes = om.MObjectArray()
    while not it.isDone():
        ref_nodes.append(it.thisNode())
        it.next()

    ref_pairs = []
    for i in range(ref_nodes.length()):
        try:
            ref = ref_nodes.__getitem__(i)  
            mfn_ref = om.MFnReference(ref)
            ref_pairs.append([mfn_ref.absoluteName(), mfn_ref.fileName(False,False,False)])
        except:
            pass
    return ref_pairs
  
    
class GTPathManagerDialog(QtWidgets.QDialog):
    ''' Main GT Path Manager Class '''
    ATTR_ROLE = QtCore.Qt.UserRole
    VALUE_ROLE = QtCore.Qt.UserRole + 1
    
    def __init__(self, parent=maya_main_window()):
        ''' Create main dialog, set title and run other UI calls '''
        super(GTPathManagerDialog, self).__init__(parent)

        self.setWindowTitle(script_name + ' - (v' + str(script_version) + ')')
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(700)
        self.resize(self.width() + 250,500)
        
        # Set Icon
        self.setWindowIcon(QtGui.QIcon(':/annotation.png'))
        
        # Setup Window Content and Signals
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        # Remove Focus from Line Edit
        self.setFocus()

        # Initial Table Refresh
        self.refresh_table()


    def create_widgets(self):
        ''' Create Widgets '''
        # Title
        self.title_label = QtWidgets.QLabel(script_name)
        self.title_label.setStyleSheet('background-color: rgb(93, 93, 93); \
                                        border: 0px solid rgb(93, 93, 93); \
                                        color: rgb(255, 255, 255);\
                                        font: bold 12px; \
                                        padding: 5px;') 
        self.help_btn = QtWidgets.QPushButton('Help')
        self.help_btn.setStyleSheet('color: rgb(255, 255, 255); font: bold 12px;') 
        
        # Search Path
        self.search_path_label = QtWidgets.QLabel("Search Path: ")
        self.filepath_le = QtWidgets.QLineEdit()
        self.filepath_le.setPlaceholderText('Path to a Directory')
        
        self.filepath_le.setMinimumSize(QtCore.QSize(380, 0))

        self.select_dir_path_btn = QtWidgets.QPushButton()
        self.select_dir_path_btn.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.select_dir_path_btn.setToolTip('Select Directory')
        
        self.table_wdg = QtWidgets.QTableWidget()
        self.table_wdg.setColumnCount(4)

        self.table_wdg.setColumnWidth(0, 22)
        self.table_wdg.setColumnWidth(1, 80) 
        self.table_wdg.setColumnWidth(3, 280) 
        header_view = self.table_wdg.horizontalHeader()
        header_view.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
    
        self.table_wdg.setHorizontalHeaderLabels(["", "Node", "Node Type", "Path"])

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(55)
        self.start_repair_btn = QtWidgets.QPushButton("Auto Path Repair")
        #self.start_repair_btn.setFixedWidth(120)
        self.search_replace_btn = QtWidgets.QPushButton("Search and Replace")
        
        self.only_files_cb = QtWidgets.QCheckBox("Only File Nodes")

        
    def create_layout(self):
        ''' Layout '''
        # Build File Path Layout
        file_path_layout = QtWidgets.QHBoxLayout()        
        file_path_layout.addWidget(self.search_path_label)
        file_path_layout.addWidget(self.filepath_le)
        file_path_layout.addWidget(self.select_dir_path_btn)
        
        # Build Title Layout
        title_layout = QtWidgets.QHBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title_label,5) 
        title_layout.addWidget(self.help_btn)

        # Bottom Left Buttons (Search Path)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addLayout(file_path_layout)
        
        # Bottom Right Buttons (Main Buttons)
        button_layout.setSpacing(2)
        button_layout.addStretch()
        #button_layout.addWidget(self.only_files_cb)
        button_layout.addWidget(self.start_repair_btn)
        button_layout.addWidget(self.search_replace_btn)
        button_layout.addWidget(self.refresh_btn)
  
        # Build Main Layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(title_layout)
        main_layout.setContentsMargins(15, 15, 15, 11) # Make Margins Uniform LTRB
        main_layout.addWidget(self.table_wdg)
        main_layout.addLayout(button_layout)
        
    def create_connections(self):
        ''' Create Connections '''
        self.refresh_btn.clicked.connect(self.refresh_table)
        self.table_wdg.cellChanged.connect(self.on_cell_changed)
        self.table_wdg.cellClicked.connect(self.select_clicked_item)
        
        # Auto Path Repair Btn
        self.start_repair_btn.clicked.connect(self.start_attempt_repair)
        
        self.help_btn.clicked.connect(self.build_gui_help_path_manager)
        self.search_replace_btn.clicked.connect(self.build_gui_search_replace_path_manager)
        
        self.select_dir_path_btn.clicked.connect(self.show_dir_select_dialog)
            
    def show_dir_select_dialog(self):
        ''' Invoke open file dialog so the user can select a search directory (Populate filepath_le with user input) '''
        multiple_filters = "Directories Only (.donotshowfiles)"
        file_path = cmds.fileDialog2(fileFilter=multiple_filters, dialogStyle=2, fm=3, caption='Select Search Directory', okc='Select Directory')

        if file_path:
            self.filepath_le.setText(file_path[0])


    def set_cell_changed_connection_enabled(self, enabled):
        ''' To turn on and off the connection so it doesn't update unnecessarily '''
        if enabled:
            self.table_wdg.cellChanged.connect(self.on_cell_changed)
        else:
            self.table_wdg.cellChanged.disconnect(self.on_cell_changed)
            
    def select_clicked_item(self, row, column): 
        ''' 
        Executed when clicking on a table item, it tries to select the node clicked 
        '''
        item = self.table_wdg.item(row, 1)
        node_name = self.get_item_value(item)
        try:
            if cmds.objExists(node_name):
                cmds.select(node_name)
        except:
            pass

    def showEvent(self, e):
        ''' Cause it to refresh when opening. I might have to change this for heavy projects '''
        super(GTPathManagerDialog, self).showEvent(e)
        self.refresh_table 
        
    def keyPressEvent(self, e):
        ''' Key presses should not be passed to the parent '''
        super(GTPathManagerDialog, self).keyPressEvent(e)
        e.accept()

    def get_path_items(self, obj):
        ''' 
        Get a tuple containing file_path, is_valid_path, obj_type, obj_icon, obj_attr
        
                Parameters:
                    obj (string): Name of the object.
                    
                Returns:
                    file_path (string): The path extracted from the object.
                    is_valid_path (bool): Whether or not the file exists in the system (or directory).
                    obj_type (string): Type of object. E.g. "file".
                    obj_icon (string): Icon path for the Node Type cell.
                    obj_attr (string): Attribute used to get/set the new path.
        '''
        if cmds.objExists(obj):
            file_path = ''
            obj_type = cmds.objectType(obj) or ''
            obj_icon = ''
            obj_attr = ''
            is_dir = False
            
            try:
                # Common Types
                if obj_type == 'file': 
                    obj_icon = ':file.svg'
                    obj_type = obj_type.capitalize()
                    obj_attr = '.fileTextureName'
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                elif obj_type == 'audio':
                    obj_icon = ':audio.svg'
                    obj_type = obj_type.capitalize()
                    obj_attr = '.filename'
                    file_path = cmds.getAttr(obj + obj_attr)
                
                elif obj_type == 'cacheFile':
                    obj_icon = ':cachedPlayback.png'
                    obj_type = 'Cache File'
                    obj_attr = '.cachePath'
                    path_no_file = cmds.getAttr(obj + obj_attr) or ''
                    file_path =  path_no_file + '/' + cmds.getAttr(obj + '.cacheName') + '.xml'
                    file_path = file_path.replace('//', '/')
                    
                elif obj_type == 'AlembicNode':
                    obj_icon = ':enableAllCaches.png'
                    obj_type = 'Alembic File'
                    obj_attr = '.abc_File'
                    file_path = cmds.getAttr(obj + obj_attr)
                     
                elif obj_type == 'BifMeshImportNode':
                    obj_icon = ':bifrostContainer.svg'
                    obj_type = 'Bifrost Cache'
                    obj_attr = '.bifMeshDirectory'
                    is_dir = True
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                elif obj_type == 'gpuCache':
                    obj_icon = ':importCache.png'
                    obj_type = 'GPU Cache'
                    obj_attr = '.cacheFileName'
                    file_path = cmds.getAttr(obj + obj_attr)

                # Arnold
                elif obj_type == 'aiPhotometricLight':
                    obj_icon = ':LM_spotLight.png'
                    obj_type = 'aiPhotometricLight'
                    obj_attr = '.aiFilename'
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                elif obj_type == 'aiStandIn': 
                    obj_icon = ':envCube.svg'
                    obj_type = 'aiStandIn'
                    obj_attr = '.dso'
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                elif obj_type == 'aiVolume': 
                    obj_icon = ':cube.png'
                    obj_type = 'aiVolume'
                    obj_attr = '.filename'
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                # Redshift
                elif obj_type == 'RedshiftProxyMesh':
                    obj_icon = ':envCube.svg'
                    obj_type = 'rsProxyMesh'
                    obj_attr = '.fileName'
                    file_path = cmds.getAttr(obj + obj_attr)

                elif obj_type == 'RedshiftVolumeShape':
                    obj_icon = ':cube.png'
                    obj_type = 'rsVolumeShape'
                    obj_attr = '.fileName'
                    file_path = cmds.getAttr(obj + obj_attr)

                elif obj_type == 'RedshiftNormalMap':
                    obj_icon = ':normalDetails.svg'
                    obj_type = 'rsNormalMap'
                    obj_attr = '.tex0'
                    file_path = cmds.getAttr(obj + obj_attr)

                elif obj_type == 'RedshiftDomeLight':
                    obj_icon = ':ambientLight.svg'
                    obj_type = 'rsDomeLight'
                    obj_attr = '.tex0'
                    file_path = cmds.getAttr(obj + obj_attr)

                elif obj_type == 'RedshiftIESLight':
                    obj_icon = ':LM_spotLight.png'
                    obj_type = 'rsIESLight'
                    obj_attr = '.profile'
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                # MASH
                elif obj_type == 'MASH_Audio':
                    obj_icon = ':audio.svg'
                    obj_type = 'MASH Audio'
                    obj_attr = '.filename'
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                # Image Plane
                elif obj_type == 'imagePlane':
                    obj_icon = ':imagePlane.svg'
                    obj_type = 'Image Plane'
                    obj_attr = '.imageName'
                    file_path = cmds.getAttr(obj + obj_attr)
                    
                # References
                elif obj_type == 'reference':
                    obj_icon = ':reference.png'
                    obj_type = 'Reference'
                    obj_attr = '.fileNames' # Not used
                    try:
                        ref_pairs = list_reference_pairs()
                        r_file = ''
                        reference_name = ''
                        for i in range(len(ref_pairs)):
                            reference_name = ref_pairs[i][0]
                            if reference_name.startswith(':'):
                                reference_name = reference_name[1:]
                            if reference_name == obj:
                                r_file = ref_pairs[i][1]
                        if reference_name == '':
                            r_file = 'Unknown'
                    except Exception as e:
                        r_file = 'Unknown'
                        print(e)
                    file_path = r_file
                    
                is_valid_path = os.path.isfile(file_path)
                if is_dir:
                    is_valid_path = os.path.isdir(file_path)
                
                return (file_path, is_valid_path, obj_type, obj_icon, obj_attr)
            except:
                return (file_path, False, obj_type, obj_icon, obj_attr)
        else:
            return None

    def refresh_table(self, is_repair_attempt=False, is_search_replace=False):
        ''' 
        Main Refresh Function
        
                Parameters:
                    is_repair_attempt=False (bool): Is attempting to auto repair paths? (Called by the Auto Path Repair Button)
                    is_search_replace=False (bool): Is it doing a search and replace? (Called by the Search and Replace Button)
        
        '''
        
        
        common_locations = [] # Locations where files were found
        is_search_dir_valid = False
        if is_repair_attempt:
            search_dir = self.filepath_le.text()
            if os.path.isdir(search_dir):
                is_search_dir_valid = True
            else:
                cmds.warning('The search directory doesn\'t exist. Please select a valid path and try again.')
        
        self.set_cell_changed_connection_enabled(False) # So it doesn't update it unecessarly
        
        self.table_wdg.setRowCount(0) # Remove all rows

        # Used to detect installed plugins
        node_types = cmds.ls(nodeTypes=True)
        
        # Common Nodes
        file_nodes = cmds.ls(type='file')
        path_nodes = file_nodes
        
        # Available Types
        available_node_types = ['audio', 'cacheFile', 'AlembicNode', 'gpuCache','BifMeshImportNode',\
                           'RedshiftProxyMesh','RedshiftVolumeShape','RedshiftNormalMap','RedshiftDomeLight','RedshiftIESLight', \
                           'MASH_Audio','aiPhotometricLight','aiStandIn','aiVolume', 'imagePlane']
        
        # Add Types for Loaded Plugins
        path_node_types = []
        for obj_type in available_node_types:
            if obj_type in node_types:
                path_node_types.append(obj_type)

        # Add Extra Nodes to Path Nodes
        for node_type in path_node_types:
            try:
                nodes_list = cmds.ls(type=node_type)
                path_nodes += nodes_list
            except:
                pass
                
        # Add References
        refs = cmds.ls(rf=True)
        path_nodes += refs

        # Populate Table
        for i in range(len(path_nodes)):
 
            ################ Start Directory Search ################
            if is_repair_attempt and is_search_dir_valid:
                try:
                    file_items = self.get_path_items(path_nodes[i]) # (path, is_path_valid, node_type_string, icon, node_attr)
                    progress_bar_name = 'Searching'
                    query_path = file_items[0]
                    initial_result = os.path.exists(query_path)
                    query_path = query_path.replace('\\','/') # Format it - The main Query
                    desired_file = query_path.split('/')[-1] # Extract file name (short_name)
                    accept_dir = False
                    is_udim_file = False
                    is_image_sequence = False
                    
                    # Check if using UDIMs or Image Sequences
                    if file_items[2] == 'File':
                        try:
                            uv_tiling_mode = cmds.getAttr(path_nodes[i] + '.uvTilingMode') # Is it using UDIM?
                            use_frame_extension = cmds.getAttr(path_nodes[i] + '.useFrameExtension') # Is it an image sequence?
                            is_image_sequence = use_frame_extension
                            if uv_tiling_mode != 0:
                                udim_file_pattern = maya.app.general.fileTexturePathResolver.getFilePatternString(query_path, use_frame_extension, uv_tiling_mode)
                                query_path = udim_file_pattern#.replace('<UDIM>','1001') Handled later using regex
                                is_udim_file = True
                        except:
                            pass

                    # Handle desired folder (instead of file)
                    if file_items[2] == 'Bifrost Cache':
                        if query_path.endswith('/'):
                            desired_file = query_path.split('/')[-2]
                        else:
                            desired_file = query_path.split('/')[-1]
                        accept_dir = True

                    is_found = False
                    if (initial_result != True) and (len(common_locations) != 0): # If common locations are available try them first
                        for loc in common_locations:
                            formatted_path = loc.replace("\\","/")
                            formatted_path = formatted_path[::-1]
                            formatted_path = formatted_path.split("/", 1)[-1]
                            formatted_path = formatted_path[::-1]
                            common_path_result = os.path.exists(formatted_path + "/" + desired_file) 
                            if common_path_result == True:
                                resolved_path = (formatted_path + "/" + desired_file).replace('/','\\')
                                #print(path_nodes[i] + ' found using known location.') # Debugging
                                self.set_attr_enhanced(path_nodes[i], file_items[4], resolved_path)      
                                is_found = True
                                
                    # Full Search/Walk   
                    if (initial_result != True) and (is_found == False):
                        search_count = 0 # How many folders to look into (walk) for the progress bar
                        for path in os.walk(search_dir): # generates the file names in a directory tree by walking the tree either top-b or b-top
                            search_count += 1 
                        resolved_path = query_path

                        self.make_progress_bar(progress_bar_name, search_count) # make_progress_bar(name, maxVal) - Max value is the number of folders
                        for path, dirs, files in os.walk(search_dir): # root_dir_path, sub_dirs, files in os.walk(my_dir)
                            self.move_progress_bar(progress_bar_name, 1) 
                            path = path.replace('/','\\')
                            
                            # Handle Files
                            if desired_file in files:
                                resolved_path = (path + '\\' + desired_file).replace('/','\\')
                                common_locations.append(resolved_path) 
                                is_found = True
                            
                            # Handle Folders (instead of files)
                            if accept_dir and desired_file in dirs:
                                resolved_path = (path + '\\' + desired_file).replace('/','\\')
                                common_locations.append(resolved_path) 
                                is_found = True
                                
                            # Handle UDIMs
                            if is_udim_file and is_found == False:
                                file_name = os.path.splitext(desired_file)[0].replace('<UDIM>', '')
                                extension = os.path.splitext(desired_file)[1]

                                pattern = re.compile(file_name + '\\d\\d\\d\\d' + extension)   
                                                            
                                first_found_file = ''
                                
                                if any(pattern.match(line) for line in files):
                                    lines_to_log = [line for line in files if pattern.match(line)]
                                    first_found_file = lines_to_log[0]

                                if first_found_file != '':
                                    resolved_path = (path + '\\' + first_found_file).replace('/','\\')
                                    if os.path.exists(resolved_path):
                                        common_locations.append(resolved_path)
                                        is_found = True
                                        
                            # Handle Image sequences
                            if is_image_sequence and is_found == False:
                                file_name = os.path.splitext(desired_file)[0].replace('<f>', '').replace('<F>', '')
                                extension = os.path.splitext(desired_file)[1]

                                pattern = re.compile(file_name + '\\d+' + extension)   
                                                            
                                first_found_file = ''
                                
                                if any(pattern.match(line) for line in files):
                                    lines_to_log = [line for line in files if pattern.match(line)]
                                    first_found_file = lines_to_log[0]

                                if first_found_file != '':
                                    resolved_path = (path + '\\' + first_found_file).replace('/','\\')
                                    if os.path.exists(resolved_path):
                                        common_locations.append(resolved_path)
                                        is_found = True
                        if is_found:
                            #print(path_nodes[i] + ' has a valid path.') # Debugging
                            self.set_attr_enhanced(path_nodes[i], file_items[4], resolved_path)
                    self.kill_progress_window(progress_bar_name) # Kill progress bar
                except:
                    self.kill_progress_window(progress_bar_name)    
            ################ End Directory Search ################

            # Search and Replace
            if is_search_replace:
                try:
                    file_items = self.get_path_items(path_nodes[i])
                    old_path = file_items[0]
                    new_path = old_path.replace(self.search_string, self.replace_string)
                    self.set_attr_enhanced(path_nodes[i], file_items[4], new_path) #(path, is_path_valid, node_type_string, icon, node_attr)
                except:
                    pass
        
            # Refresh Table
            file_items = self.get_path_items(path_nodes[i])
            self.table_wdg.insertRow(i)
            
            self.table_wdg.setFocusPolicy(QtCore.Qt.NoFocus) # No highlight           
            
            self.insert_item(i, 1, path_nodes[i], None, path_nodes[i])
            
            if file_items: # (path, is_path_valid, node_type_string, icon, node_attr)
                if file_items[1]:
                    self.insert_item(i, 2, file_items[2], None, cmds.objectType(path_nodes[i]), icon_path=file_items[3], editable=False )
                    self.insert_icon(i, 0, ':confirm.png')
                else:
                    self.insert_item(i, 2, file_items[2], None, cmds.objectType(path_nodes[i]), icon_path=file_items[3], editable=False )
                    self.insert_icon(i, 0, ':error.png')

                self.insert_item(i, 3, file_items[0], file_items[4], file_items[0])
            
        self.set_cell_changed_connection_enabled(True)
        
    def insert_item(self, row, column, node_name, attr, value, icon_path='', editable=True, centered=True):
        item = QtWidgets.QTableWidgetItem(node_name)
        #item.setBackgroundColor(QtGui.QColor(255,0,0, 10)) Make the background of the cells green/red?
        self.set_item_value(item, value)
        self.set_item_attr(item, attr)
        
        if icon_path != '':
            item.setIcon(QtGui.QIcon(icon_path))
        
        if centered:
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            
        if not editable:
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            
        self.table_wdg.setItem(row, column, item)  
            
    def insert_icon(self, row, column, icon_path):       
        item = QtWidgets.QWidget()
        label = QtWidgets.QLabel()
        label.setScaledContents(True)
        label.maximumSize()
        label.setPixmap(QtGui.QPixmap(icon_path))
        
        layout = QtWidgets.QHBoxLayout(item)
        layout.addWidget(label)
        layout.setAlignment(QtCore.Qt.AlignHCenter)
        layout.setContentsMargins(0,5,0,5)
        item.setLayout(layout)
        
        self.table_wdg.setCellWidget(row, column, item)

    def set_item_text(self, item, text):
        item.setText(text)
        
    def get_item_text(self, item):
        return item.text()
        
    def set_item_attr(self, item, attr):
        item.setData(self.ATTR_ROLE, attr)
        
    def get_item_attr(self, item):
        return item.data(self.ATTR_ROLE)
        
    def set_item_value(self, item, value):
        item.setData(self.VALUE_ROLE, value)
        
    def get_item_value(self, item):
        return item.data(self.VALUE_ROLE)
        
    def on_cell_changed(self, row, column):
        self.set_cell_changed_connection_enabled(False)
        
        item = self.table_wdg.item(row, column)

        if column == 1:
            self.rename(item)
        if column == 3:
            self.repath(item)
        
        self.set_cell_changed_connection_enabled(True)

    def rename(self, item):
        old_name = self.get_item_value(item)
        new_name = self.get_item_text(item)
        if old_name != new_name:
            actual_new_name = cmds.rename(old_name, new_name)
            if actual_new_name != new_name:
                self.set_item_text(item, actual_new_name)
            self.set_item_value(item, actual_new_name)
    
    def repath(self, item):
        old_path = self.get_item_value(item)
        new_path = self.get_item_text(item)
        attr_to_change = self.get_item_attr(item)
   
        object_name = self.get_item_value(self.table_wdg.item(item.row(), 1))
        if old_path != new_path:
            try:
                is_valid_path = os.path.isfile(new_path)
                complex_output = self.set_attr_enhanced(object_name, attr_to_change, new_path)
                
                if complex_output != None and complex_output == False:
                    self.set_item_value(item, old_path)
                    self.set_item_text(item, old_path)
                    is_valid_path = os.path.isfile(old_path)
                else:
                    self.set_item_text(item, new_path)

                if is_valid_path:
                    self.insert_icon(item.row(), 0, ':confirm.png')
                else:
                    self.insert_icon(item.row(), 0, ':error.png')
                
                self.set_cell_changed_connection_enabled(True)
                self.refresh_table()
            except Exception as e:
                self.set_item_value(item, old_path)
                self.set_cell_changed_connection_enabled(True)
                self.refresh_table()
                raise e             

    def set_attr_enhanced(self, obj, attribute, new_value):
        ''' 
        Set attribute for the provided object using different methods depending on its type
        
                Parameters:
                    obj (string): Name of the node/object.
                    attribute (string): Name of the attribute to set. E.g. ".cacheFile"
                    new_value (string): New value to update
        '''
        
        #print(obj + ' ' + attribute  + ' ' + new_value) # Debugging
        
        if cmds.objExists(obj):
            obj_type = cmds.objectType(obj) or ''
        else:
            obj_type = ''
        
        complex_types = ['cacheFile', 'reference']
        
        if obj_type not in complex_types:
            cmds.setAttr( obj + attribute , new_value, type='string')
        else:
            if obj_type == 'cacheFile':
                format_path = os.path.splitext(new_value)[0].replace("\\","/")
                file_name = format_path.split('/')[-1]
                format_path_no_file = format_path[::-1].split("/", 1)[-1][::-1]
                                
                try:
                    if os.path.isfile(format_path_no_file + '/' + file_name.replace('.xml','') + '.xml'):
                        cmds.setAttr(obj + '.cachePath', format_path_no_file, type='string')
                        cmds.setAttr(obj + '.cacheName', file_name, type='string')
                        return True
                    else:
                        return False
                except:
                    return False
            
            if obj_type == 'reference':
                not_skipped = True
                try:
                    cmds.referenceQuery(obj,isLoaded=True)
                except:
                    not_skipped = False
                
                if not_skipped:
                    if os.path.isfile(new_value):
                        try:
                            cmds.file(new_value, loadReference=obj)
                        except:
                            return False
                    else:
                        cmds.warning('Provided reference path : "' + new_value + '" doesn\'t lead to a valid file. Previous path was retained.')
                else:
                    cmds.warning('Reference file inaccessible.')

    def start_attempt_repair(self):
        ''' Runs refresh function while searching for files '''
        self.refresh_table(is_repair_attempt=True)

        
    def make_progress_bar(self, prog_win_name, max_value):
        ''' 
        Create Progress Window 
        
                Parameters:
                       prog_win_name (string): Name of the window
                       max_value (int): The maximum or "ending" value of the progress indicator.
        
        '''
        if(cmds.window(prog_win_name, q=1, ex=1)):
            cmds.deleteUI(prog_win_name)
        if(cmds.windowPref(prog_win_name, q=1, ex=1)):
            cmds.windowPref(prog_win_name, r=1)

        prog_window = cmds.window(prog_win_name, title=prog_win_name, widthHeight=(300, 50))
        cmds.columnLayout(p=prog_win_name)
        progress_control = cmds.progressBar(prog_win_name + '_progress', maxValue=max_value, width=300, height=50)
        cmds.showWindow( prog_window )

    def move_progress_bar(self, prog_win_name, step_size):
        cmds.progressBar(prog_win_name + '_progress', edit=True, step=step_size)

    def kill_progress_window(self, prog_win_name):
        ''' 
        Close progress window in case it exists
        
                Parameters:
                       prog_win_name (string): Name of the window
        '''
        if(cmds.window(prog_win_name, q=1, ex=1)):
            cmds.deleteUI(prog_win_name)
        if(cmds.windowPref(prog_win_name, q=1, ex=1)):
            cmds.windowPref(prog_win_name, r=1)
            
    def build_gui_help_path_manager(self):
        ''' Creates the Help GUI for GT Path Manager '''
        window_name = "build_gui_help_path_manager"
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)

        cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
        cmds.window(window_name, e=True, s=True, wh=[1,1])

        main_column = cmds.columnLayout(p= window_name)
       
        # Title Text
        cmds.separator(h=12, style='none') # Empty Space
        cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
        cmds.text(script_name + " Help", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
        cmds.separator(h=10, style='none', p=main_column) # Empty Space

        # Body ====================
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
        # cmds.text(l='Script for managing paths', align="center")
        # cmds.separator(h=15, style='none') # Empty Space

        cmds.text(l='This script displays a list with the name, type and path\n of any common nodes found in Maya.', align="center")
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text(l='You can select the node listed by clicking on it or \nchange its name or path by double clicking the cell.', align="center")
        
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text(l='The icon on the left describes the validity of the path.\nIf the file or directory is found in the system it shows\n a green confirm icon otherwise it shows a red icon.', align="center")
        
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text(l='Auto Path Repair', align="center", font='boldLabelFont')
        cmds.text(l='This function walks through the folders under the\nprovided directory looking for missing files. \nIf it finds a match, the path is updated.', align="center")
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text(l='Search and Replace', align="center", font='boldLabelFont')
        cmds.text(l='This function allows you to search and replace strings\nin the listed paths.', align="center")
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text(l='Refresh', align="center", font='boldLabelFont')
        cmds.text(l='Re-populates the list while re-checking for path validity.', align="center")
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text(l='Search Path', align="center", font='boldLabelFont')
        cmds.text(l='A directory path used when looking for missing files.', align="center")
        
        cmds.separator(h=15, style='none') # Empty Space
        cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
        cmds.text('Guilherme Trevisan  ')
        cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
        cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
        cmds.separator(h=7, style='none') # Empty Space
        
        # Close Button 
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
        
        cmds.separator(h=5, style='none')
        cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
        cmds.separator(h=8, style='none')
        
        # Show and Lock Window
        cmds.showWindow(window_name)
        cmds.window(window_name, e=True, s=False)
        
        # Set Window Icon
        qw = omui.MQtUtil.findWindow(window_name)
        if python_version == 3:
            widget = wrapInstance(int(qw), QtWidgets.QWidget)
        else:
            widget = wrapInstance(long(qw), QtWidgets.QWidget)
        icon = QtGui.QIcon(':/question.png')
        widget.setWindowIcon(icon)
        
        def close_help_gui():
            ''' Closes Help UI in case it's opened. '''
            if cmds.window(window_name, exists=True):
                cmds.deleteUI(window_name, window=True)


    def build_gui_search_replace_path_manager(self):
        ''' Creates the GUI for Searching and Replacing Paths '''
        window_name = "build_gui_search_replace_path_manager"
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)

        cmds.window(window_name, title= 'Search and Replace', mnb=False, mxb=False, s=True)
        cmds.window(window_name, e=True, s=True, wh=[1,1])

        main_column = cmds.columnLayout(p= window_name)
       
        # Body
        cmds.separator(h=12, style='none') # Empty Space
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
        cmds.text(l='This will search and replace strings in your paths', align="center")
        cmds.separator(h=12, style='none') # Empty Space
        cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
        cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
        cmds.text('Search for:', bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
        search_txtfield = cmds.textField(placeholderText='Type search here')
        cmds.separator(h=10, style='none') # Empty Space
        cmds.text('Replace with:', bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
        replace_txtfield = cmds.textField(placeholderText='Type replace here')
        
        # Close Button 
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(nc=2, cw=[(1, 148),(2, 148)], cs=[(1,10),(2,4)], p=main_column)
        
        # Apply Button
        cmds.button(l='Search and Replace', h=30, c=lambda args: apply_search_replace())
        
        #cmds.separator(h=10, style='none')
        cmds.button(l='Cancel', h=30, c=lambda args: close_snr_gui())
        cmds.separator(h=8, style='none')
        
        # Show and Lock Window
        cmds.showWindow(window_name)
        cmds.window(window_name, e=True, s=False)
        
        # Set Window Icon
        qw = omui.MQtUtil.findWindow(window_name)
        if python_version == 3:
            widget = wrapInstance(int(qw), QtWidgets.QWidget)
        else:
            widget = wrapInstance(long(qw), QtWidgets.QWidget)
        icon = QtGui.QIcon(':/search.png')
        widget.setWindowIcon(icon)
        
        def apply_search_replace():
            ''' Runs Search and Replace Function '''
            self.search_string = cmds.textField(search_txtfield, q=True, text=True) 
            self.replace_string = cmds.textField(replace_txtfield, q=True, text=True) 
            
            if self.search_string != '':
                try:
                    gt_path_manager_dialog.show()
                except:
                    pass
                self.refresh_table(is_search_replace=True)
                if cmds.window(window_name, exists=True):
                    cmds.deleteUI(window_name, window=True)
            else:
                cmds.warning('"Search for" string can\'t be empty.')
        
        def close_snr_gui():
            ''' Closes Search and Replace GUI in case it's opened. '''
            if cmds.window(window_name, exists=True):
                cmds.deleteUI(window_name, window=True)
      
def try_to_close_gt_path_manager():
    ''' Attempts to close GT Path Manager '''
    try:
        gt_path_manager_dialog.close() # pylint: disable=E0601
        gt_path_manager_dialog.deleteLater()
    except:
        pass

# Build GUI
if __name__ == "__main__":
    try_to_close_gt_path_manager()
    gt_path_manager_dialog = GTPathManagerDialog()
    gt_path_manager_dialog.show()