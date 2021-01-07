<!-- GT Tools Docs -->

<body>

<p></p>
<!-- Table of Contents -->
<div>
<h1> Table of Contents </h1>
<a href="https://github.com/TrevisanGMW/gt-tools"><img src="./media/gt_logo.png" align="right" alt="GT Tools Logo" width="400"></a>
<h3><b>General:</b></h3>
<ul>
  <li><a href="#-gt-menu-">GT Menu</a></li>
  <li><a href="#-gt-check-for-updates-">GT Check for Updates</a></li>
</ul>
<h3><b>Tools:</b></h3>
<ul>
  <li><a href="#-gt-renamer-">GT Renamer</a></li>
  <li><a href="#-gt-selection-manager-">GT Selection Manager</a></li>
  <li><a href="#-gt-path-manager-">GT Path Manager</a></li>
  <li><a href="#-gt-color-manager-">GT Color Manager</a></li>
  <li><a href="#-gt-transfer-transforms-">GT Transfer Transforms</a></li>
  <li><a href="#-gt-render-checklist-">GT Render Checklist</a></li>
</ul>
<h3><b>Curves:</b></h3>
<ul>
  <li><a href="#-gt-generate-python-curve-">GT Generate Python Curve</a></li>
  <li><a href="#-gt-generate-text-curve-">GT Generate Text Curve</a></li>
</ul>
<h3><b>Modeling:</b></h3>
<ul>
  <li><a href="#-gt-sphere-types-">GT Sphere Types</a></li>
</ul>

<div>
<h3><b>Rigging:</b></h3>
<ul>
  <li><a href="#-gt-auto-biped-rigger-">GT Auto Biped Rigger</a></li>
  <li><a href="#-gt-connect-attributes-">GT Connect Attributes</a></li>
  <li><a href="#-gt-mirror-cluster-tool-">GT Mirror Cluster Tool</a></li>
  <li><a href="#-gt-generate-in-between-">GT Generate In-Between</a></li>
  <li><a href="#-gt-create-auto-fk-">GT Create Auto FK</a></li>
  <li><a href="#-gt-create-ik-leg-">GT Create IK Leg</a></li>
  <li><a href="#-gt-make-ik-stretchy-">GT Make IK Stretchy</a></li>
</ul>
<h3><b>Utilities:</b></h3>
<ul>
  <li><a href="#-gt-utilities-">GT Utilities</a></li>
</ul>
<h3><b>Miscellaneous:</b></h3>
<ul>
  <li><a href="#-gt-startup-booster-">GT Startup Booster</a></li>
  <li><a href="#-gt-fspy-importer-">GT fSpy Importer</a></li>
  <li><a href="#-gt-maya-to-discord-">GT Maya to Discord</a></li>
</ul>
</div>

<br>
</div>

<!-- GT Menu -->
<div>
<h1> GT Menu </h1>
<img src="./media/gt_menu.jpg" align="right"
     alt="GT Dropdown Menu and Help">


<p>The script "gt_tools_menu.mel" adds a new dropdown menu to the main Maya window. It provides the user with easy access to the other scripts based on categories. 
<br>This menu contains sub-menus that have been organized to contain related tools. For example: modeling, rigging, utilities, etc...</p>

<p><b>How does Maya know to run the script and create the menu?:</b> When you install the script package, it adds a line of code to the "userSetup.mel" file. This file gets executed every time Maya opens.</p>

<p><b>Help > About: </b><br>This option opens a window showing basic information about GT Tools.</p>

<p><b>Help > Re-Build Menu: </b>It re-creates the GT Tools menu, and does a rehash to pick up any new scripts.
<br>(Good for when updating, so you don't need to restart Maya)</p>

<p><b>Help > Check for Updates: </b><br>Opens the script "gt_check_for_updates" to compare your version with the latest release.</p>

<p><b>Help > Installed Version: </b>What version is currently installed.</p>
<br>
</div>

<!-- GT Check for Updates -->
<div>
<h1> GT Check for Updates </h1>
<img src="./media/gt_check_for_updates.jpg" align="right"
     alt="GT Check for Updates UI">


<p>This script compares your current GT Tools version with the latest release from Github. In case the version installed is older than the latest release, an option to update becomes available.<br>In this window you can also control how often the script will automatically check for updates.</p>

<p><b>Status: </b><br>Result from the comparison. In case you have an older version it will let you know that the script package can be updated.</p>

<p><b>Web Response: </b><br>The script needs to ask Github for the latest release to be able to compare with the one you have. In case internet is not available or a firewall blocked the connection you will see the error code here. (These are HTTP status codes)</p>

<p><b>Re-Build Menu: </b>It re-creates the GT Tools menu, and does a rehash to pick up any new scripts. (Good for when updating, so you don't need to restart Maya)</p>

<p><b>Installed Version: </b><br>Version currently installed on your computer. In case you never installed the menu, it will be (v0.0.0).</p>

<p><b>Latest Release: </b>Latest version available on Github.</p>

<p><b>Latest Release Changelog: </b>Here you can find a list showing all the main changes applied to the three latest versions. The version number can be found on the top left corner and the release date on the top right corner.</p>

<p><b>Auto Check For Updates: </b>This function controls the behaviour of the auto updater. In case active, it will use the interval value to determine if it should check for new releases. The user will only see the update window in case there is an actual update. (This function has no impact in your Maya startup time as it only gets executed only when necessary and it waits for the program to be idle. Click on the button to toggle between Activated/Deactivated</p>

<p><b>Interval: </b>This is how often the script will auto check for updates. Click on the button to change between the available intervals. (5 day, 15 days, 30 days, 3 months, 6 months, 1 year)</p>

<p><b>Refresh: </b>Checks for updates again.</p>

<p><b>Update: </b>This button is only available in case there is a new update available. When clicked it opens the page for you to download the latest version. Simply install it again to update.</p>

<br>
</div>

<!-- GT Renamer -->
<div>
<h1> GT Renamer </h1>
<img src="./media/gt_renamer.jpg" align="right"
     alt="GT Renamer GUI">
<img src="./media/gt_renamer_sample.gif" align="right"
     alt="GT Renamer Sample">

<p>Script for quickly renaming multiple objects.<br>Feedback is given through inView messages at the left bottom corner.</p>

<p><b>Modes: </b><br>- Selected: uses selected objects when renaming.<br>- Hierarchy: uses hierarchy when renaming.<br>- All: uses everything in the scene (even hidden nodes)</p>

<p><b>Other Tools: </b><br>- Remove First Letter: removes the first letter of a name.<br>If the next character is a number, it will be deleted.<br>- Remove Last Letter: removes the last letter of a name.<br>- U-Case: makes all letters uppercase.<br>- Capitalize: makes the 1st letter of every word uppercase.<br>- L-Case: makes all letters lowercase</p>

<p><b>Rename and Number: </b>Renames selected objects and number them.<br>- Start # : first number when countaing the new names.<br>- Padding : how many zeros before the number. e.g. "001"</p>

<p><b>Prefix and Suffix: </b><br>Prefix: adds a string in front of a name.<br>Suffix: adds a string at the end of a name.<br> - Auto: Uses the provided strings to automatically name objects according to their type or position.<br>1st example: a mesh would automatically receive "_geo"<br>2nd example: an object in positive side of X, would automatically receive "left_: .<br> - Input: uses the provided text as a prefix or suffix.</p>

<p><b>Search and Replace: </b>Uses the well-known method of search and replace to rename objects.</p>
<br>
</div>

<!-- GT Selection Manager-->
<div>
<h1> GT Selection Manager </h1>
<img src="./media/gt_selection_manager.jpg" align="right"
     alt="GT Selection Manager GUI">

<p>This script allows you to update selections to contain (or not) filtered elements. You can also save and load previous selections.</p>	 
<p><b>Element Name: </b>This option allows you to check if the string used for the object name contains or doesn't contain the, the provided strings (parameters).</p>
<p><b>Element Type:  </b>This filter will check the type of the element to determine if it should be part of the selection or not.</p>
<p><b>Element Type > Behavior (Dropdown Menu): </b>Since most elements are transforms, you can use the dropdown menu "Behavior" to determine how to filter the shape element (usually hidden inside the transform). <br>(You can consider transform, shape, both or ignore it)</p>

<p><b>Visibility State: </b>Selection based on the current state of the node's visibility attribute.</p>

<p><b>Outliner Color (Transform): </b>Filters the option under Node > Display > Outliner Color. In case you're unsure about the exact color, you can use the "Get" button to automatically copy a color.</p>

<p><b>Store Selection Options: </b><br>Select objects and click on "Store Selection" to store them for later.<br>Use the "-" and "+" buttons to add or remove elements.<br>Use the "Reset" button to clear your selection.</p>

<p><b>You can save your selection in two ways: </b><br>As a set: creates a set containing your selection.<br> As text: creates a txt file containing  the code necessary to recreate selection.</p>

<p><b>Create New Selection: </b>Uses all objects as initial selection<br><b>Update Current Selection: </b>Considers only selected objects</p>
<br>
</div>

<!-- GT Path Manager -->
<div>
<h1> GT Path Manager </h1>
<img src="./media/gt_path_manager.gif" align="right"
     alt="GT Path Manager GUI">
	 
<p>This script displays a list with the name, type and path of any common nodes found in Maya.<br><br>You can select the node listed by clicking on it or change its name or path by double clicking the cell.

The icon on the left describes the validity of the path. If the file or directory is found in the system it shows a green confirm icon otherwise it shows a red icon.</p>

<p><b>Auto Path Repair: </b>This function walks through the folders under the provided directory looking for missing files. If it finds a match, the path is updated.</p>


<p><b>Search and Replace: </b>This function allows you to search and replace strings in the listed paths.</p>

<p><b>Refresh: </b>Re-populates the list while re-checking for path validity.</p>

<p><b>Search Path: </b>A directory path used when looking for missing files.</p>

<p><b>Supported Nodes: </b>
<br>file (UDIMS and Image Sequences), audio, cacheFile, AlembicNode, BifMeshImportNode, gpuCache, MASH_Audio, aiPhotometricLight, aiStandIn, aiVolume, RedshiftProxyMesh, RedshiftVolumeShape, RedshiftNormalMap, RedshiftDomeLight, RedshiftIESLight, imagePlane</p>

<br><br>
</div>

<!-- GT Color Manager -->
<div>
<h1> GT Color Manager </h1>


<img src="./media/gt_color_manager.jpg" align="right"
     alt="GT Color Manager GUI">

<p>Script for quickly coloring elements in Maya.<br>Feedback is given through inView messages at the left bottom corner.</p>
<br>
<p><b>Modes: </b><br>- Drawing Override: Utilize "Object > Object Display > Drawing Overrides" to set color.<br>- Wireframe Color:  Utilize "Display > Wireframe Color..." to set color.</p>
<br>
<p><b>Target: </b><br>- Transform:  Colorize actual selection. Usually a "transform"<br>- Wireframe Color:  Colorize the shape node inside the transform</p>
<br>

<img src="./media/gt_color_manager_sample_b.gif" align="right"
	 alt="GT Path Manager Sample B">
<img src="./media/gt_color_manager_sample_a.gif" align="right"
	 alt="GT Path Manager Sample A">


<p><b>Current Color: </b><br>The color used in the operation. Click on the color to open Maya's color picker.</p>

<p><b>Color Presets: </b><br>A list of common colors. When clicked it sets the color.</p>


<p><b>Set Color For: </b><br>- Outliner:  Control the outliner color
<br>- Wireframe Color:  Control the wireframe color seen in the viewport</p>
<br><br><br><br><br>

</div>

<!-- GT Transfer Transforms -->
<div>
<h1> GT Transfer Transforms </h1>

<img src="./media/gt_transfer_transforms.jpg" align="right"
     alt="GT Transfer Transforms GUI">

<p>Script for transfering translate, rotate or scale data from one object to antoher.</p>

<p><b>Transfer (Source/Targets): </b><br>1. Select Source 1st<br>- Wireframe Color:  Utilize "Display > Wireframe Color..." to set color.</p>

<p><b>Target: </b><br>- Transform:  Colorize actual selection. Usually a "transform"<br>2. Select Targets 2nd,3rd...<br>3. Select which transforms to transfer (or maybe invert)</p>

<p><b>Transfer from one side to the other: </b><br>"From Right to Left" and From Left To Right" functions.</p>
<p>1. Select all elements
<br>2. Select which transforms to transfer (or maybe invert)
<br>3. Select one of the "From > To" options
<br>e.g. "From Right to Left" : <br>Copy transforms from objects
with the provided prefix "Right Side Tag" to objects 
with the provided prefix "Left Side Tag".</p>

<p><b>Copy and Paste Transforms: </b><br>This function doesn't take in consideration the previous settings.
It works on its own. <br>As the name suggests, it copy transforms, which populates the text fields, or it pastes transforms from selected fields back to selected objects.</p>
<br>

</div>

<!-- GT Render Checklist -->
<div>
<h1> GT Render Checklist </h1>

<img src="./media/gt_render_checklist.gif" align="right"
     alt="GT Render Checklist GUI">

<p>This script performs a series of checks to detect common issues that are often accidently ignored/unnoticed.</p>

<p><b>Checklist: </b>
<br>- Operation: Name of the check the script will perform
<br>- Status: Result received from the test
<br>- Info: Extra info or comments regarding the results
</p>

<p><b>Checklist Status: </b><br>These are also buttons, you can click on them for extra functions:
<br>- Grey: Default color, not yet tested.
<br>- Green: Pass color, no issues were found.
<br>- Yellow: Warning color, some possible issues were found.
<br>- Red: Error color, issues were found.
<br>- Black: Exception color, an issue caused the check to fail. (Likely because of a missing plug-in or unexpected value)
<br>- Question Mark, click on button for more help.</p>

<p><b>Settings: </b>
<br>Change what values cause the script to return a warnings and errors.
<br>- Apply: Stores the settings and go back to the main window (settings are persistent between Maya sessions)
<br>- Export Settings: Exports a txt file containing all current settings.
<br>- Import Settings: Imports a txt file exported using the previously mentioned function.
<br>- Reset to Default Values: Resets expected values to default values.
</p>

<p><b>Main Buttons: </b>
<br>- Generate Report: Creates a temporary txt file with all the information collected during the checks.
<br>- Refresh: Runs all checks again.</p>

<p><b>Checklist Operations:</b></p>
<ul>
	<li> Frame Rate: returns error if not matching expected frame rate, for example "film" (24fps).
		<br>Examples of custom values:"film" (24fps),"23.976fps", "ntsc" (30fps), "ntscf" (60fps), "29.97fps"
	</li>
	<li> Scene Units: returns error if not matching expected value, for example "cm".
		<br>Examples of custom values: "mm" (milimeter), "cm" (centimeter), "m" (meter).
	</li>
	<li> Output Resolution: returns error if not matching expected value, for example : ['1920', '1080'].
		<br>Please use a comma "," for entering a custom value. Examples of custom values: "1280, 720" (720p), "1920, 1080" (1080p), "2560, 1440" (1440p), "3840, 2160" (4K), "7680, 4320" (8K)
	</li>
	<li> Total Texture Count: error if more than expected value 50 (default value) and a warning if more than 40 (default value). (UDIM tiles are counted as individual textures)
	</li>
	<li> Network File Paths: must start with ['path']. Path is a list, you can enter all acceptable locations (usually in the network for render farms)
		<br>This function completely ignore slashes. You may use a list as custom value. Use a comma "," to separate multiple paths.
	</li>
	<li> Network Reference Paths: must start with ['path']. Path is a list, you can enter all acceptable locations (usually in the network for render farms)
		<br>This function completely ignore slashes. You may use a list as custom value. Use a comma "," to separate multiple paths
	</li>
	<li> Unparented Objects: returns an error if common objects are found outside hierarchies. For example a cube outside of a group.</li>
	<li> Total Triangle Count: : error if more than 2000000 (default value) warning if more than: 1800000 (default value).
	</li>
	<li> Total Poly Object Count: error if more than 100 (default value) warning if more than 90 (default value).
	</li>
	<li> Shadow Casting Lights: error if more than 3 (default value) warning if more than 2 (default value).
	</li>
	<li> RS Shadow Casting Lights: error if more than 4 (default value) warning if more than 3(default value).
	</li>
	<li> Ai Shadow Casting Lights: error if more than 4 (default value) warning if more than 3 (default value).
	</li>
	<li> Default Object Names: error if using default names. Warning if containing default names. 
		<br>Examples of default names: "pCube1" = Error, "pointLight1" = Error, "nurbsPlane1" = Error, "my_pCube" = Warning
	</li>
	<li> Objects Assigned to lambert1: error if anything is assigned to the default shader "lambert1".
	</li>
	<li> Ngons: error if any ngons are found. (A polygon that is made up of five or more vertices. Anything over a quad (4 sides) is considered an ngon)
	</li>
	<li> Non-manifold Geometry: error if is found. A non-manifold geometry is a 3D shape that cannot be unfolded into a 2D surface with all its normals pointing the same direction.
		<br>For example, objects with faces inside of it or faces with edges extruded out of it.
	</li>
	<li> Empty UV Sets: error if multiples UV Sets and Empty UV Sets. It ignores objects without UVs if they have only one UV Set.
	</li>
	<li> Frozen Transforms: error if rotation(XYZ) not frozen. It doesn't check objects with incoming connections, for example, animations or rigs.
	</li>
	<li> Animated Visibility: error if animated visibility is found warning if hidden object is found.
	</li>
	<li> Non Deformer History: error if any non-deformer history found.
	</li>
	<li> Textures Color Space: error if incorrect color space found. It only checks commonly used nodes for Redshift and Arnold
		<br>Generally "sRGB" -> float3(color), and "Raw" -> float(value).
	</li>
	<li> Other Network Paths: must start with ['path']. Path is a list, you can enter all acceptable locations (usually in the network for render farms)
		<br>This function completely ignore slashes. You may use a list as custom value. Use a comma "," to separate multiple paths.
		<br>This function checks: Audio Nodes, Mash Audio Nodes, nCache Nodes, Maya Fluid Cache Nodes, Arnold Volumes/Standins/Lights, Redshift Proxy/Volume/Normal/Lights, Alembic/BIF/GPU Cache, Golaem Common and Cache Nodes.
	</li>
</ul>
<br>
</div>

<!-- GT Generate Python Curve -->
<div>
<h1> GT Generate Python Curve </h1>

<img src="./media/gt_generate_python_curve.jpg" align="right"
     alt="GT Generate Python Curve GUI">

<p>This script generates the Python code necessary to create a selected curve.<br>Helpful for when you want to save a curve to your shelf or to add it to a script.</p>

<p><b>How to use it:</b>
<br>1. Make sure you delete the curve's history before generating the code.
<br>2. Select the curve you want to convert to code.
<br>3. Click on the "Generate" button to generate the code.</p>

<p><b>Add import "maya.cmds": </b><br>Adds a line that imports Maya's cmds API. This is necessary for when running python scripts.</p>

<p><b>Close Curve: </b><br>Adds a line to close the curve after creating it.</p>

<p><b>"Generate" button:</b><br>Outputs the python code necessary to create the curve inside the "Output PYthon Curve" box.</p>

<p><b>Run Code: </b><br>Attempts to run the code (or anything written) inside  "Output Python Curve" box  </p>

<br>

</div>

<!-- GT Generate Text Curve -->
<div>
<h1> GT Generate Text Curve </h1>

<img src="./media/gt_generate_text_curve.jpg" align="right"
     alt="GT Generate Text Curve GUI">

<p>This script creates merged curves containing the input text from the text field. <br>(All shapes go under one transform)</p>

<p><b>How to use it:</b>
<br>1. Select what font you want to use.
<br>2. Type the word you want to create in the "Text:" text field.
<br>3. Click on the "Generate" button.</p>

<p>You can create multiple curves at the same time by separanting them with commas ",".</p>

<p><b>Current Font: </b><br>Click on the button on its right to change the font</p>

<br>

</div>

<!-- GT Sphere Types -->
<div>
<h1> GT Sphere Types </h1>

<img src="./media/gt_create_sphere_types.jpg" align="right"
     alt="GT Sphere Types GUI">

<p>Quite simple script used as a reminder that the standard sphere is not the only sphere option.</p>

<p><b>Standard Sphere: </b><br>Creates the standard Maya sphere. "Create > Polygon Primitives > Sphere"</p>
<p><b>Standard Sphere: </b><br>Creates a sphere using a cube. "Create > Polygon Primitives > Cube" then "Mesh > Smooth (2x)"</p>
<p><b>Platonic Sphere A: </b><br>Creates a sphere using a platonic solid. (Settings: Icosahedron, Quads, 1, 1, 1)</p>
<p><b>Platonic Sphere A: </b><br>Creates a sphere using a platonic solid. (Settings: Octaheadron, Quads, 2, 1, 1)</p>

<br>

</div>


<!-- GT Auto Biped Rigger -->
<div>
<h1> GT Auto Biped Rigger </h1>

<img src="./media/gt_auto_biped_rigger.jpg" align="right"
     alt="GT Auto Biped Rigger GUI">

<p>Script for quickly generating an advanced biped rig.
<br>For more predictable results execute the script in a new scene containing only the geometry of the desired character. This prevents naming conflicts and data loss.</p>
<p>Here are some highlights of what it creates: 
<br>- FK/IK switches with automated control visibility 
<br>- Automated finger posing with offset (for a natural motion) 
<br>- Foot rolls (with manual limiters for more flexibility) 
<br>- Options to have pole vectors, IK controls and eyes follow parts of the body (like effectors) 
<br>- Stretchy and squash for the arms and legs (with automatic volume preservation) 
<br>- Automatic forearm rotation with support for stretched limbs.
<br>- Shelf button with Seamless FK/IK Switch for arms and legs.
<br>- Automatic HumanIK character definition with custom rig profiles for retargeting (mocap)
</p>

<p><h3>Step 1:</h3>
<b>- Create Proxy:</b><br>
This button will create many temporary curves that will later be used to generate the rig. 
<br>In case you want to re-scale the proxy, use the root proxy control for that.
<br>The initial scale is the average height of a woman (160cm) but you can download proxy presets (poses) for other scales from the  <a href="./assets">assets folder</a>.
<br>
<br> The arrow found in the shape of the clavicles, hands and finger proxies indicate their up position. 
<br>The bigger arrows in the shape of the knees and elbows show the direction of their up vector constraint. (that's the direction they will bend)
<br>
<br>To position the eye proxies: Center the pivot point of the eye geometry then display its Local Rotation Axes then snap the proxy to its center.
<br>To center the pivot of eye geometry go to <b>"Modify > Center Pivot"</b> (It's often already in the center, check it first)
<br>To show the Local Rotation Axes (so you have a point to snap it to) go to <b>"Display > Transform Display > Local Rotation Axes"</b>
<br>Hold "V" while moving the eye proxy to snap it to points. 
<br>
<br>Some proxy curves have custom attributes on them that allow you to tweak their posing behavior or visibility. 
<br>The ankle proxy curves have an attribute called "Follow Hip" when activated, they will follow the position of the hip allowing you to pose the character a bit faster while keeping a hip and ankle perfectly aligned.
<br>The Root proxy has an attribute called "Lines Visibility" that allows you to turn off the visibility of the lines
<br>
<br>Proxy curves are not joints. Please don't delete or rename them. 
<br>For tips on how to position every proxy curve, open the attribute editor and read the information under "Transform Node > Notes:"
</p>


<p><h3>Step 2:</h3>
Pose the proxy (guide) to match your character. 
<br><b>- Reset Proxy:</b>  Resets the position and rotation of the proxy elements, essentially "recreating" the proxy.  
<br><b>- Mirror Right to Left:</b> Copies the transform data from the right side to the left side, mirroring the pose.
<br><b>- Mirror Left to Right:</b> Copies the transform data from one left side to the right side, mirroring the pose.
<br><b>- Import Pose:</b> Imports a JSON file containing the transforms of the proxy elements. This file is generated  using the "Export Pose" function. 
<br><b>- Export Pose:</b> Exports a JSON file containing the transforms of the proxy elements. 
<br><b>- Delete Proxy:</b> Simply deletes the proxy in case you no longer need it.</p>

<p><h3>Step 3:</h3>
<b>- Create Rig:</b> This button uses the proxy elements to automatically create the control rig.
<br>It uses the transform data found in the proxy to determine how to position, orient and setup the skeleton and controls.
<br>This function will delete the proxy. Make sure you export it first if you plan to reuse it later. </p>

<p><h3>Step 4:</h3>
Now that the rig has been created,  it's time to to attach it to the geometry.
<br><b>- Select Skinning Joints:</b>  Select only joints that should  be used when skinning the character. This means that it will not include end or toe joints. If you don't plan to include the eyes joints in the influences of the character's body, simply unselect them before skinning.
<br><b>- Bind Skin Options:</b>  Opens the options for the function "Bind Skin" so the desired geometry can attached to the skinning joints. Make sure to set the option "Bind to" as "Selected Joints" to guarantee that only the desired joints are part of the influence. </p>
<br>

<p><h3>Utilities:</h3>

<img src="./media/gt_auto_biped_rigger_fkik.jpg" align="right"
     alt="GT Seamless FK/IK Switcher for Auto Biped Rigger GUI">

These are utilities and extra functions that you can use after creating your rig.
<br>
<br><b>- Add Seamless FK/IK Switch to Shelf:</b>  Adds a new button to your current shelf. This button allows the animator to seamlessly switch between FK and IK for the arms and legs.
<br><b>		- Toggle:</b> Seamlessly Toggles between FK and IK. 
<br><b>		- FK to IK:</b> Switches to IK and copies the FK pose into it. 
<br><b>		- IK to FK:</b> Switches to FK and copies the IK pose into it.
<br>
<br><b>- Toggle Label Visibility:</b> Uniformly toggles the option "Joint > Joint Labelling > Draw Label" (".drawLabel") for all joints in the scene (according to the state of the majority of them).
<br>
<br><b>- Attach to HumanIK:</b> Automatically creates a HumanIK character definition called "auto_biped" and assign all the available joints/bones to it. In case a character with the same name is already present in the scene, it will be overwritten.</p>

<br>
<h3>Example of seamless FK/IK switch being used:</h3>
<img src="https://github.com/TrevisanGMW/maya-scripts/blob/main/gt_tools/media/gt_auto_biped_rigger_fkik.gif"
     alt="GT Seamless FK/IK Switcher for Auto Biped Rigger Example">

<p><br><br><h3>How to attach motion capture data to the rig through HumanIK:</h3>
<b>- 1.</b> Start by defining a character and assigning all bones to the definition (You can do that in one click using the utility "Attach to HumanIK")
<br><b>2.</b> Create a custom rig by clicking on the custom rig button. <img src="./media//human_ik_custom_rig_btn.jpg" alt="HumanIK Custom Rig Button">
<br><b>3.</b> Assign the desired controls or use one of the provided templates so HumanIK knows what controls to update. 
<br>You can load a template by clicking on the button "Load Custom Rig Mapping". <img src="./media/human_ik_load_mapping_btn.jpg" alt="HumanIK Load Custom Rig Mapping Button"> Templates can be found in the <a href="./assets">assets folder</a>.
<br><b>4.</b> Now you can source the motion from another character like you would normally do in HumanIK and it should automatically reverse engineer the control position to match the mocap data.
<br>In case the elbows or knees pole vector controls give you trouble, you might be able to fix it using their custom attribute "Follow Foot" or "Follow Wrist" instead of relying on HumanIK to position it. <a href="https://youtu.be/eBwYi8FeK3I">This video</a> explains in more details how this process works.
<br><b>5.</b> Now you can bake the movements to the custom rig by going to "HumanIK Button (blue button) > Bake > Bake to Custom Rig".
<br>Feel free to delete the HumanIK character definition and mocap data after that as the keyframes are now already baked to the controls.
</p>
<img src="https://github.com/TrevisanGMW/maya-scripts/blob/main/gt_tools/media/gt_auto_biped_rigger_hik.gif"
     alt="GT Auto Biped attached to HumanIK Example">

<h3>Custom Attributes and Stretchy System:</h3>
<p>This rig comes with many custom attributes so you can tweak how much stability/flexibility you want and how the systems should behave.
<b>- Lock Attribute</b> Many controls come with channels automatically locked so they behave in an expected way, but in certain situations you might want to unlock these so you have more flexibity. For this, you can just change the "Lock Channel" (Channel could be Translate, Rotate, XY and Z) custom attribute. A good example is the foot rolls. They have their Y and Z rotations locked by default, but in case you want to rotate the foot in another diretion you can change "Lock YZ" to "Off". </p>
<img src="./media/gt_auto_biped_rigger_lock_attr.jpg"
     alt="GT Auto Biped Lock Attribute Example">

<img src="https://github.com/TrevisanGMW/maya-scripts/blob/main/gt_tools/media/gt_auto_biped_rigger_foot.gif"
     alt="GT Auto Biped Foot Rolls Example">


<br>

</div>


<!-- GT Connect Attributes -->
<div>
<h1> GT Connect Attributes </h1>

<img src="./media/gt_connect_attributes.jpg" align="right"
     alt="GT Connect Attributes GUI">

<p>This script automates the creation of connections between attributes from source (output) and target (input).</p>

<p><b>Use Selection for Source and Target (s): </b>
<br>When this option is activated, you no longer need to load sources/target (s).
<br>You can simply select: 1st: source, 2nd, 3rd... : target(s)</p>
<p><b>Add Reverse Node:  </b><br>Adds a reverse node between connections.</p>
<p><b>Disconnect: </b><br>Break connections between selected nodes.</p>
<p><b>Force Connection (Overrides Existing): </b><br>Connects nodes even if they already have a connection.</p>

<p><b>Add Custom Node Between Connection: </b>
<br>Allows user to create a node between connections. (Excellent for controlling dataflow.)
<br>-Custom Node: Which node to create
<br>-Add Input Node: Creates one master control to update all in betweens.</p>

<p><b>Load Source/Target Objects: </b>
<br>Use these buttons to load the objects you want to use as source and target (s).</p>

<p><b>Source Attribute and Target Attributes: </b>
<br>Name of the attribute you want to connect. <br>Requirement: Use long or short name (no nice names)</p>

<p><b>List All Attributes and List Keyable Attributes: </b>
<br>Returns a list of attributes that can be used to populate the Source and Target Attributes fields.</p>

<br>

</div>

<!-- GT Mirror Cluster Tool -->
<div>
<h1> GT Mirror Cluster Tool </h1>

<img src="./media/gt_mirror_cluster_tool.jpg" align="right"
     alt="GT Mirror Cluster Tool GUI">

<p>Script for mirroring clusters on mesh objects.</p>

<p><b>Step 1: </b>
<br>Load your mesh by selecting it in the viewport or in the outliner,<br> then click on "Select Mesh".
<br>Requirements: Must be one single mesh transform.</p>

<p><b>Step 2: </b>
<br>Load your clusterHandle by selecting it in the viewport or in the outliner,<br> then click on "Select Cluster".
<br>Requirements: Must be one single clusterHandle.</p>

<p><b>Step 3: </b>
<br>Select your mirror axis X, Y or Z. It will always mirror on the negative direction</p>

<p><b>Step 4: </b>
<br>To save time you can automatically rename the mirrored clusters using the search and replace text fields.
<br>For example search for "left_" and replace with "right_"</p>

<br>

</div>

<!-- GT Generate In-Between -->
<div>
<h1> GT Generate In-Between </h1>

<img src="./media/gt_generate_inbetween.jpg" align="right"
     alt="GT Generate In-Between GUI">

<p>This script creates a inbetween transform for the selected elements.</p>

<p><b>Layer Type: </b>
<br>This pull-down menu determines what type object will be created.</p>

<p><b>Parent Type: </b>
<br>This pull-down menu determines where the pivot point of the generated element will be extracted from.</p>

<p><b>Outliner Color: </b>
<br>Determines the outliner color of the generated element.</p>

<p><b>New Transform Suffix: </b>
<br>Determines the suffix to be added to generated transforms.</p>

<br>

</div>

<!-- GT Create Auto FK -->
<div>
<h1> GT Create Auto FK </h1>

<img src="./media/gt_create_auto_fk.jpg" align="right"
     alt="GT GT Create Auto FK GUI">

<p>This script generates FK controls for joints while storing their transforms in groups.
<br>Just select the desired joints and run the script.</p>

<p><b>Colorize Controls: </b>
<br>Automatically colorize controls according to their names (prefix). It ignores uppercase/lowercase.
<br>No Prefix = Yellow
<br>"l_" or "left_" = Blue
<br>"r_" or "right_" = Red</p>

<p><b>Select Hierarchy:  </b>
<br>Automatically selects the rest of the hierarchy of the selected object, thus allowing you to only select the root joint before creating controls.</p>

<p><b>(Advanced) Custom Curve: </b>
<br>You can change the curve used for the creation of the controls. Use the script "GT Generate Python Curve" to generate the code you need to enter here.</p>

<p><b>Joint, Control, and Control Group Tag: </b>
<br>Used to determine the suffix of the elements.
<br>Joint Tag is removed from the joint name for the control.
<br>Control Tag is added to the generated control.
<br>Control Group Tag is added to the control group.
<br>(The control group is the transform carrying the transforms of the joint).</p>

<p><b>Ignore Joints Containing These Strings:  </b>
<br>The script will ignore joints containing these strings. To add multiple strings use commas - ",".</p>

<br>

</div>

<!-- GT Create IK Leg -->
<div>
<h1> GT Create IK Leg </h1>

<img src="./media/gt_create_ik_leg.jpg" align="right"
     alt="GT Create IK Leg GUI">

<p>This script is no longer part of the GT Tools Menu, I've temporarily removed it so I can make it more user-friendly.<br><br>This script assumes that you are using a simple leg composed of a hip joint, a knee joint an ankle joint and maybe ball and toe joints.<br>In case your setup is different, I suggest you try a different solution. </p>

<p><b>Joint Tag (Suffix) and Ctrl Group Tag (Suffix): </b>
<br>These two textfields allow you to define what suffix you used for you base skeleton joints and your control groups. 
<br>(used when creating new names or looking for controls)
<br>The Ctrl Group Tag is used to define the visibility of the FK system.</p>

<p><b>Custom PVector Ctrl, IK Ctrl and IK Switch:  </b>
<br>These options allow you to load an already existing control.
<br>In case you already created curve you could simply load them and the script will use yours instead of creating a new one.</p>

<p><b>Colorize Controls:  </b>
<br>This option looks for "right_" and "left_" tags and assign colors based on the found tag.</p>

<p><b>Make Stretchy Legs: </b>
<br>This option creates measure tools to define how to strechy the leg when it goes beyong its current size.
<br>- Term = What is being compared
<br>- Condition = Default Size (used for scalling the rig)</p>

<p><b>Use Ball Joint:  </b>
<br>This option allows you to define whether or not to use a ball joint.</p>

<p><b>Load "Content" Buttons:  </b>
<br>These buttons allow you to load the necessary objects before running the script.</p>

<br>

</div>

<!-- GT Make Stretchy Legs -->
<div>
<h1> GT Make IK Stretchy </h1>

<img src="./media/gt_make_ik_stretchy.jpg" align="right"
     alt="GT Make IK Stretchy GUI">

<p>This script makes an IK setup stretchy.
<br>Load an ikHandle, then click on "Make Stretchy"</p>

<p><b>Stretchy System Prefix:</b>
<br>As the name suggests, it determined the prefix used when naming nodes for the stretchy system.<br>If nothing is provided, it will be automatically named "temp".</p>

<p><b>Load IK Handle:</b>
<br>Use this button to load your ikHandle.The joints will be automatically extracted from it.</p>

<p><b>Load Attribute Holder:</b>
<br>Use this button to load your attribute holder.
<br>This is usually a control. A few custom attributes will be added to this object, so the user can control the stretchy system.</p>

<p><b>Important:</b>
<br>The ikHandle cannot be outside of a group. So it will be automatically grouped when this is the case.
<br>If an attribute holder is not provided, a simpler version of the stretchy system will be created instead.</p>

<br><br>

</div>

<!-- GT Utilities -->
<div>
<h1> GT Utilities </h1>

<img src="./media/gt_utilities.jpg" align="right"
     alt="GT Utilities Menu">
	 

<p>GT Utilities (GTU) is a collection of smaller functions that don't necessary need or use a window/dialog.
<br>Most of these functions can be found under "GT Tools > Utilities" but a few of them are scattered throughout other menus.</p>

<p><b>Standalone use: </b>
<br>In case you're using the standalone version of GT Utilities, you'll have to uncomment one of the functions at the bottom of the script.</p>

<h3>Reload File</h3>
<p>This utility attempts to reload the current scene.
<br>Realoading means reopening it without attempting to save it first.
<br>It only works if the file was saved at least once.</p>

<h3>Resource Browser</h3>
<p>Opens the resource browser, a menu that allows the used to see what images are available inside Maya and download them.</p>

<h3>Unlock Default Channels</h3>
<p>This function unlocks the translate, rotate, scale and visibility channels for the selected objects.</p>

<h3>Unhide Default Channels</h3>
<p>This function unhides/shows the translate, rotate, scale and visibility channels for the selected objects.</p>

<h3>Unhide Default Channels</h3>
<p>This function unhides/shows the translate, rotate, scale and visibility channels for the selected objects.</p>

<h3>Uniform LRA Toggle</h3>
<p>This utility makes the visibility of the local rotation axis of the selected objects uniform.<br> For example, if two out of three objects have their LRA visible, it makes all of them visible.</p>

<h3>Uniform Joint Label Toggle</h3>
<p>Uniformly toggles the option "Joint > Joint Labelling > Draw Label" (".drawLabel") for all joints in the scene (according to the state of the majority of them).</p>

<h3>Import References</h3>
<p>Attempts to import all loaded references.</p>

<h3>Remove References</h3>
<p>Attempts to remove all references.</p>

<h3>Move Pivot to Top</h3>
<p>Moves the pivot point of the selected objects to the top of their bounding box.</p>

<h3>Move Pivot to Base</h3>
<p>Moves the pivot point of the selected objects to the base of their bounding box.</p>

<h3>Move Object to Origin</h3>
<p>Moves the selected objects to the center of the grid (0,0,0) origin point.</p>

<h3>Reset Transforms</h3>
<p>Resets translate, rotate and scale back to zero. For example, you can select all controls of a character and reset its pose.</p>

<h3>Reset Joints Display</h3>
<p>Resets the visibility of all joints. It sets the radius of all joints to one. (Unless the channel is locked) and sets the visibility to "On". It also changes the global joint display scale (multiplier) back to one.</p>

<h3>Reset "persp" Camera</h3>
<p>Resets most of the attributes for the default "persp" camera.</p>

<h3>Delete Namespaces</h3>
<p>Merges all namespaces back to the root, essentially deleting them.</p>

<h3>Delete Display Layers</h3>
<p>Deletes all display layers.</p>

<h3>Delete Nucleus Nodes</h3>
<p>Deletes all nodes related to the nucleus system.</p>

<h3>Delete Keyframes</h3>
<p>Deletes all keyframes. (It does not affect set driven keys)</p>

<img src="./media/gtu_modeling.jpg" align="right"
     alt="GT Utilities Modeling">

<h3>Convert Bif to Mesh</h3>
<p>Converts selected Bifrost meshes into the standard Maya meshes.<br>(Bif objects are created using Bifrost Graph)</p>

<h3>Copy Material</h3>
<p>Copies a material from the selection to the clipboard to later be applied to another object.
<br>It supports components such as faces.</p>

<h3>Paste Material</h3>
<p>Pastes a material to the selection. (Use the Copy Material function to copy it first)
<br>It supports components such as faces.</p>

<img src="./media/gtu_curves.jpg" align="right"
     alt="GT Utilities Curves">
	 
<h3>Combine Curves</h3>
<p>Moves curve shapes of the selected curves into one single transform, essentially combining them.
<br>In case a bezier curve is found, the script gives you the option of converting them to NURBS.</p>

<h3>Separate Curves</h3>
<p>Parents every curve shape of the selection under a new transform, causing them to be separated.</p>
	 
	 
<br>

</div>

<!-- GT Startup Booster -->
<div>
<h1> GT Startup Booster </h1>

<img src="./media/gt_startup_booster.jpg" align="right"
     alt="GT Startup Booster GUI">

<p>This script helps decrease the time Maya takes to load before becoming fully functional.</p>

<p><b>How It works: </b>
<br>Not all plugins are used every time Maya is opened, but they are usually still loaded during startup. This causes the startup time to be quite slow.
<br>This script aims to fix that, by helping you skip the heavy plugins while still having easy access to them.</p>

<p>1st: Optimize.
<br>2nd: Create Shelf Buttons.
<br>3rd: Enjoy faster startups.</p>

<p><b>Plugin List: </b>
<br>This is a list of common plugins that are usually automatically loaded by default.
<br>Plugin File: Name of the file used by the plugin.
<br>Auto Load: Is this plugin automatically loading?
<br>Installed: Is the plugin installed?
<br>Control: General name of the plugin.</p>

<p><b>"Shelf Button" and "Auto Load" Buttons: </b>
<br>Shelf Button: Creates a Shelf Button (under the current shelf) to load the plugin and give you feedback on its current state.
<br>Auto Load: Toggles the Auto Load function of the plugin.<br>(same as "Auto Load" in the plugin manager)</p>

<p><b>Custom Shelf Button: </b>
<br>This script couldn't account for every heavy 3rd party plug-in.This shouldn't be an issue as you can manually add any plugin.
<br>Just manually deactivate your third party plugin by going to "Windows > Settings/Preferences > Plug-in Manager"
<br>Then create a custom load button using the textField that says "Other Plugins"</p>

<br>

</div>



<!-- GT fSpy Importer -->
<div>
<h1> GT fSpy Importer </h1>

<img src="./media/gt_fspy_importer.jpg" align="right"
     alt="GT fSpy Importer GUI">

<p>This script allows you import the data of a JSON file (exported out of fSpy) into Maya.</p>


<p><b>What is fSpy: </b>
<br>fSpy is a fantastic software that allows you to quickly and easily create a 3D camera match.<br>The files created with it can easily be imported in Blender, but not in Maya. That's what this script aims to address.<br>
<br>You can find more information and a tutorial on their website: <a href="https://fspy.io/">https://fspy.io/</a></p>


<p><b>How It works: </b>
<br>Using the JSON file, this script applies the exported matrix to a camera so it matches the position and rotation identified in fSpy.
<br>It also calculates the focal length assuming that the default camera in Maya is a 35mm camera.</p>

<p><b>How to use it:</b>
<br><b>Step 1:</b> Create a camera match in fSpy. (There is a tutorial about it on their website)
<br><b>Step 2:</b> Export the JSON file by going to "File > Export > Camera parameters as JSON".
<br><b>Step 3:</b> Load the files by opening the script and entering the path for your JSON and Image files.
<br><b>Step 4:</b> Use the Import button to generate the camera.</p>

<p><b>JSON File Path: </b>
<br>This is a path pointing to the JSON file you exported out of fSpy.<br>
In case the file was altered or exported/created using another program it might not work as expected.</p>

<p><b>Image File Path:</b>
<br>A path pointing to the image file you used for your camera match with in fSpy.<br>
Do not change the resolution of the image file or crop the image or it might not work properly.</p>

<p><b>Set Scene Resolution: </b>
<br>Uses the size of the image to determine the resolution of the scene.<br>This settings are found under "Render Settings > Image Size" (Resolution)</p>

<p><b>+Z Axis is +Y: </b>
<br>Rotates the camera so the default +Z axis becomes +Y.
<br>This might be necessary in case the default settings were used inside fSpy. This is because different softwares use different world coordinate systems.</p>

<p><b>Lock Camera </b>
<br>Locks the generated camera, so you don't accidenty move it.</p>

<br>

</div>




<!-- GT Maya to Discord -->
<div>
<h1> GT Maya to Discord </h1>

<img src="./media/gt_maya_to_discord.jpg" align="right"
     alt="GT Maya to Discord GUI">

<p>This script allows you to quickly send images and videos (playblasts) from Maya to Discord using a Discord Webhook to bridge the two programs.</p>

<p><b>Webhooks: </b>
<br>A webhook (a.k.a. web callback or HTTP push API) is a way for an app to provide other applications with real-time information.
<br>You can use it to send messages to text channels without needing the discord application.</p>

<p><b>How to get a Webhook URL: </b>
<br>If you own a Discord server or you have the correct privileges, you can go to the settings to create a Webhook URL.</p>

<p><b>To create one go to: </b>
<br>"Discord > Server > Server Settings > Webhooks > Create Webhook"
<br>Give your webhook a name and select what channel it will operate.
<br>Copy the "Webhook URL" and load it in the setttings for this script.<br>
<br>If you're just an user in the server, you'll have to ask the administrator of the server to provide you with a Webhook URL.</p>

<p><b>Send Buttons: </b>
<br>Send Message Only: Sends only the attached message.
<br>(Use the textfield above the buttons to type your message)</p>

<p><b>Send Desktop Screenshot: Sends a screenshot of your desktop. </b>
<br>(This includes other programs and windows that are open)</p>

<p><b>Send Maya Window: Sends only the main Maya window. </b>
<br>(This ignores other windows, even within Maya)</p>

<p><b>Send Viewport: Sends an image of the active viewport. </b>
<br>(Includes Heads Up Display text, but no UI elements)</p>

<p><b>Send Playblast: Sends a playblast video. </b>
<br>(Use the script settings to determine details about the video)</p>

<p><b>Send OBJ/FBX: Sends a model using the chosen format. </b>
<br>For settings, go to "File > Export Selection... > Options"</p>

<p><b>Settings: </b>
<br>The settings are persistent, which means they will stay the same between Maya sessions.</p>

<p><b>Custom Username: </b>
<br>Nickname used when posting content through the webhook.</p>

<p><b>Image and Video Format: </b>
<br>Extension used for the image and video files.</p>

<p><b>Video Options: </b>
<br>Determines the settings used when recording a playblast.</p>

<p><b>Feedback and Timestamp Options: </b>
<br>Determines feedback visibility and timestamp use.</p>

<p><b>Limitations: </b>
<br>Discord has a limit of 8MB for free users and 50MB for paid users for when uploading a file.
<br>If you get the error "Payload Too Large" it means your file exceeds the limits. Try changing the settings.</p>

<br>

</div>

</body>
