<!-- GT Tools Docs -->
<p></p>

<!-- GT Renamer -->
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

<!-- GT Selection Manager-->
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

<!-- GT Path Manager -->
<h1> GT Path Manager </h1>
<img src="./media/gt_path_manager.gif" align="right"
     alt="GT Path Manager GUI">
	 
<p>This script displays a list with the name, type and path of any common nodes found in Maya. You can select the node listed by clicking on it or change its name or path by double clicking the cell.

The icon on the left describes the validity of the path. If the file or directory is found in the system it shows a green confirm icon otherwise it shows a red icon.</p>


<p><b>Auto Path Repair: </b>This function walks through the folders under the provided directory looking for missing files. If it finds a match, the path is updated.</p>


<p><b>Search and Replace: </b>This function allows you to search and replace strings in the listed paths.</p>

<p><b>Refresh: </b>Re-populates the list while re-checking for path validity.</p>

<p><b>Search Path: </b>A directory path used when looking for missing files.</p>




