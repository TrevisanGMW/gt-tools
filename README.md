<!-- GT Tools README.md file -->
<p></p>
<img src="./docs/media/gt_logo.png">
<p></p>
<p align="center"> 
   <a href="https://github.com/TrevisanGMW/gt-tools/graphs/contributors">
   <img alt="GitHub contributors" src="https://img.shields.io/github/contributors/TrevisanGMW/gt-tools.svg?style=flat-square" ></a>
   <img alt="GitHub language count" src="https://img.shields.io/github/languages/count/TrevisanGMW/gt-tools?style=flat-square">
   <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/TrevisanGMW/gt-tools?style=flat-square">
   <a href="https://github.com/TrevisanGMW/gt-tools/network/members">
   <img alt="GitHub forks" src="https://img.shields.io/github/forks/TrevisanGMW/gt-tools.svg?style=flat-square" ></a>
   <a href="https://github.com/TrevisanGMW/gt-tools/stargazers">
   <img alt="GitHub stars" src="https://img.shields.io/github/stars/TrevisanGMW/gt-tools.svg?style=flat-square" ></a>
   <a href="https://github.com/TrevisanGMW/gt-tools/issues">
   <img alt="GitHub issues" src="https://img.shields.io/github/issues/TrevisanGMW/gt-tools.svg?style=flat-square" ></a>
   <a href="https://github.com/TrevisanGMW/gt-tools/blob/master/LICENSE">
   <img alt="GitHub license" src="https://img.shields.io/github/license/TrevisanGMW/gt-tools.svg?style=flat-square" ></a>
   <a href="https://www.paypal.me/TrevisanGMW"> 
   <img src="https://img.shields.io/badge/$-donate-blue.svg?maxAge=2592000&amp;style=flat-square">
   <a href="https://www.linkedin.com/in/trevisangmw/">
   <img alt="GitHub stars" src="https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555" ></a>
</p>

<h1>Description</h1>
This is my collection of scripts for Autodesk Maya – These scripts were created with the aim of automating, 
enhancing or simply filling the missing details of what I find lacking in Maya.

After installing or running the script collection, you’ll find a pull-down menu that provides easy access to a
variety of tools and utilities. This menu contains sub-menus that have been organized to contain related tools,
for example: modeling, rigging, utilities, etc…

For help on how to use these scripts, click on the “Help” button at the top right of their window (within Maya) or
check their documentation by going to the <a href="./docs">docs</a> folder. For changelog see the <a href="https://github.com/TrevisanGMW/gt-tools/releases">releases</a> page.

All of these items are supplied as is. You alone are solely responsible for any issues. Use at your own risk.
Hopefully these scripts are helpful to you as they are to me.

Note: Python 2 is no longer supported. If you want to still use an older versions of Maya, make sure to use a GT-Tools version below "3.0.0" for compatibility.

<p><b>Package tested using Autodesk Maya 2022, 2023 and 2024 (Windows 10)</b></p>

<h1>Organization</h1>
<ul>
<li><code>docs</code>: Documentation on installation, usage, and troubleshooting of the package and its tools.</li>
<li><code>gt.tools</code>: The "tools" directory contains separate folders, each representing a distinct tool.</li>
<li><code>gt.ui</code>: The "ui" module provides utilities for user interface operations.</li>
<li><code>gt.utils</code>: The "utils" module is a set of reusable functions that are not tied to any specific tool.</li>
<li><code>tests</code>: Package unittests for tools, ui and utilities. See <a href="./CONTRIBUTING.md">CONTRIBUTING</a> for more details.</li>
</ul>

<h1>Setup (Install, Uninstall, Run Only)</h1>
<p><b>TL;DR:</b> Download and extract the files; Drag and drop the file "setup_drag_drop_maya.py" onto the Maya viewport; 
Select the option "Install", "Uninstall" or "Run Only"; Enjoy! <br></p>

<img src="./docs/media/setup_tutorial.svg"
     alt="GT Tools Installation Tutorial"
     width="1000" 
     align="center">

<p>This script collection comes with an auto setup tool ("setup_drag_drop_maya.py") to call it drag and drop the file on your Maya viewport. From the setup window you can "Install", "Uninstall" or "Run Only".
<br>Here is how you do it in more details:</p>

<ol>
	<li>Open Maya (in case it's closed).</li>
	<li>Download the latest release (or clone this repository).</li>
	<li>Un-zip (Decompress) the file you downloaded. (the setup won't work if it's still compressed)</li>
	<li>Drag and drop "setup_drag_drop_maya.py" on to your Maya viewport.</li>
    <li>An user interface with the setup options will open.</li>
	<li>Select the desired operation. E.g. "Install", "Uninstall", or "Run Only"</li>
	<li>Enjoy!</li>
</ol>

<p>
After installing, you can delete the downloaded/extracted files (as they have already been copied)
</p>

<h3>Setup Window</h3>
<img src="./docs/media/setup_window.jpg"
     alt="GT Tools Installation Setup Window"
     width="500"
     align="center">
<ol>
	<li><b>Install:</b> Copies the files to the installation path and loads (reloads) the package. </li>
	<li><b>Uninstall:</b> Deletes the files from the installation path and unloads the package.</li>
	<li><b>Run Only:</b> "One time use only"; Loads tools from current location without copying files.</li>
</ol>

<h3>Checksum Verification</h3>
<p>When installing it for the first time, Maya might show you a small dialog window saying "UserSetup Checksum Verification", you can confirm it with a "Yes". This window is only letting you know that the "userSetup.mel" script was modified. This is a security feature from Autodesk that is used to tell the user that the startup script was modified. This check is used to prevent infected scenes from modifying the startup script without the user knowing. In our case, we did it deliberately as part of the installation process, so you can just confirm it.
</p>

<h3>Run Only</h3>
<p>The setup window offers the option to run the tools without installing them. To do this, follow the same drag and drop steps and click on "Run Only" instead of "Install". This is going to load the tools from the location you have them, allowing you to run it one time only.</p>

<h3>Updating</h3>
<p>Simply install it again. The auto setup will handle the file changes.
<br>If updating a major version, it's recommended that you uninstall it first before installing it again. This will eliminate any unnecessary files.
<br>In case updating it manually, make sure to overwrite (replace) the files when moving them.</p>

<h1> Contributors </h1>
If you'd like to contribute, see the <a href="./CONTRIBUTING.md">CONTRIBUTING</a> file for a detailed explanation on how to do that. 
<br><b>Pull requests are warmly welcome.</b> 
<p></p>
<a href="https://github.com/TrevisanGMW/gt-tools/graphs/contributors">
  <img src="https://contributors-img.web.app/image?repo=TrevisanGMW/gt-tools" />
</a>

Looking for other ways to contribute? You could [**buy me a coffee! :coffee:**](https://www.buymeacoffee.com/TrevisanGMW) or use the [**Github sponsor :heart:**](https://github.com/sponsors/TrevisanGMW) options!
<br>This is definitely a huge motivation boost! :star_struck:

<h1> Licensing </h1>
The MIT License 2020 - Guilherme Trevisan
