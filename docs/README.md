<!-- GT Tools Docs -->


<body>


<p></p>
<!-- Table of Contents -->
<div>
<h1> Table of Contents </h1>
<a href="https://github.com/TrevisanGMW/gt-tools"><img src="../gt_logo.png" align="right" alt="GT Tools Logo" width="400"></a>
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

<p><b>Re-Build Menu: </b>It re-creates the GT Tools menu, and does a rehash to pick up any new scripts. (Good for when updating, so you don't need to restart Maya)</p>

<p><b>Check for Updates: </b><br>Opens the script "gt_check_for_updates" to compare your version with the latest release.</p>

<p><b>Installed Version: </b>What version is currently installed.</p>
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
<br><br>
</div>

<!-- GT Color Manager -->
<div>
<h1> GT Color Manager </h1>


<img src="./media/gt_color_manager.jpg" align="right"
     alt="GT Color Manager GUI"><br>

<p>Script for quickly coloring elements in Maya.<br>Feedback is given through inView messages at the left bottom corner.</p>

<p><b>Modes: </b><br>- Drawing Override: Utilize "Object > Object Display > Drawing Overrides" to set color.<br>- Wireframe Color:  Utilize "Display > Wireframe Color..." to set color.</p>

<p><b>Target: </b><br>- Transform:  Colorize actual selection. Usually a "transform"<br>- Wireframe Color:  Colorize the shape node inside the transform</p>
<br><br>

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
     alt="GT Transfer Transforms GUI"><br>

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
     alt="GT Render Checklist GUI"><br>

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
     alt="GT Generate Python Curve GUI"><br>

<p>This script generates the Python code necessary to create a selected curve. Helpful for when you want to save a curve to your shelf or to add it to a script.</p>

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
     alt="GT Generate Text Curve GUI"><br>

<p>This script creates merged curves containing the input text from the text field. <br>(All shapes go under one transform)</p>

<p><b>How to use it:</b>
<br>1. Select what font you want to use.
<br>2. Type the word you want to create in the "Text:" text field.
<br>3. Click on the "Generate" button.</p>

<p>You can create multiple curves at the same time by separanting them with commas ",".</p>

<p><b>Current Font: </b><br>Click on the button on its right to change the font</p>

<br>

</div>

</body>
