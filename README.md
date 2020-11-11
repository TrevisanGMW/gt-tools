<!-- GT Tools README.md file -->
<p></p>

<img src="./gt_logo.png">

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


<h1> Description </h1>
This is my collection of scripts for Autodesk Maya – These scripts were created with the aim of automating, enhancing or simply filling the missing details of what I find lacking in Maya.

After installing the script collection, you’ll find a pull-down menu that provides easy access to a variety of tools. This menu contains sub-menus that have been organized to contain related tools, for example: modeling, rigging, utilities, etc…

For help on how to use these scripts, click on the “Help” button at the top right of their window (within Maya) or check their documentation at the top of the script file (just open the “.py” or “.mel” file using any text editor, such as notepad)

Do you want to use a script but don't want to install the whole package? That's fine too, every script in GT Tools is standalone and will run if you just copy the code and paste it in your script editor.
PS: for "gt_utilities" you will have to uncomment a function at the bottom of the script, as it wouldn't make sense to call all of them at once.

Have a suggestion? Want to report a bug? Want to contribute? Check the issues tab on Github. 

All of these items are supplied as is. You alone are solely responsible for any issues. Use at your own risk. 
Hopefully these scripts are helpful to you as they are to me.

<p><b>Tested using Autodeks Maya 2020 (Windows 10)</b></p>


<h1> Organization </h1>
<p><code>mel-scripts</code>: contains scripts written in MEL</p>
<p><code>python-scripts</code>: contains scripts written in Python</p>

<h1> Installation </h1>

<b>TL;DR :</b> Download files, then open "setup.bat".

<h3>Auto Installation</h3>

This script collection comes with an auto installer (setup.bat) you can simply download it, run the setup and reopen Maya.
Here is how you do it in more details:
<ol>
	<li>Close Maya (in case it's opened).</li>
	<li>Download the latest release (or clone this repository).</li>
	<li>Un-zip (Decompress) the file you downloaded. (the setup won't work if it's still compressed)</li>
	<li>Open "setup.bat". (It will show you the options - "Install, Uninstall and About")</li>
	<li>Type "1" for the "install" option, then press enter.</li>
	<li>Open Autodesk Maya.</li>
</ol>


If you want, you can now delete the downloaded/extracted files (as they have already been installed)

<h3>Manual Installation</h3>

In case you need/want to manually install the scripts. It's also a pretty straightforward process.
<ol>
	<li>Close Maya (in case it's opened).</li>
	<li>Download the latest release (or clone this repository).</li>
	<li>Un-zip (Decompress) the file you downloaded.</li>
	<li>Move all the contents from the folders "mel-scripts" and "python-scripts" to your scripts folder (usually located under the path below):
	<b>C:\Users\USERNAME\Documents\maya\VERSION\scripts\ </b></li>
	<li>In case you don't want to replace an already existing <b>"userSetup.mel" </b> script (inside your scripts folder), you can easily merge them by opening the existing one and adding the line: <code>source "gt_tools_menu.mel";" </code></li>
	(This command adds the menu when Maya opens)
	<li>Open Autodesk Maya. </li>
</ol>

<h1> Uninstallation </h1>

<h3>Auto Uninstallation</h3>

<ol>
	<li>Close Maya (in case it's opened).</li>
	<li>Download the latest release (or clone this repository).</li>
	<li>Un-zip (Decompress) the file you downloaded.</li>
	<li>Open "setup.bat". (It will show you the options - "Install, Uninstall and About")</li>
	<li>Type "2" for the "uninstall" option, then press enter.</li>
	<li>Open Autodesk Maya.</li>
</ol>

<h3>Manual Uninstallation</h3>

<ol>
	<li>Close Maya (in case it's opened).</li>
	<li>Navigate to your scripts folder, usually located under the following path:
	<b>C:\Users\USERNAME\Documents\maya\VERSION\scripts\ </b></li>
	<li>Delete all files starting with the prefix "gt_" (use the search bar to quickly select all of them)</li>
	<li>Open your <b>"userSetup.mel" </b> script (inside your scripts folder), and remove the line: <code>source "gt_tools_menu.mel";" </code></li>
	<li>Open Autodesk Maya. </li>
</ol>

<h1> Frequently Asked Questions </h1>
<ul>
	<li><b>How do I update GT Tools to a new version?</b> <br>A: Simply install it again, it will overwrite previous files.</li>
	<li><b>What do I do if I have multiple "userSetup.mel" files?</b> One inside "maya/####/scripts" and another one inside "maya/scripts"<br>A: The "userSetup.mel" file gets executed when you open Maya, but Maya supports only one file. In case you have two files it will give priority to the file located inside "maya/####/scripts", so manage your initialization commands there.</li>
	<li><b>Where are the other scripts you had in this repository?</b> <br> A: I moved all other scripts that are not part of GT Tools to another reposity. Here is the link: <a href="https://github.com/TrevisanGMW/maya-scripts">TrevisanGMW/maya-scripts</a> </li>
</ul>

<h1> Contributors </h1>
If you'd like to contribute, please fork the repository and make changes as you'd like. <br><b>Pull requests are warmly welcome.</b>
<p></p>
<a href="https://github.com/TrevisanGMW/gt-tools/graphs/contributors">
  <img src="https://contributors-img.web.app/image?repo=TrevisanGMW/gt-tools" />
</a>


<h1> Licensing </h1>
The MIT License 2020 - Guilherme Trevisan

