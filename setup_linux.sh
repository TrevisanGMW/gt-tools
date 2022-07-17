#!/bin/sh -x
#######################################
#
# 	Linux Auto Installer for GT-Tools (Tested in Ubuntu 20.10)
#
#	To run it, open Terminal and type "sudo sh" + the path to this bash script
#
# 	@Guilherme Trevisan - github.com/TrevisanGMW/gt-tools - 2021-01-16
#
# 	1.0 - 2021-01-16 - Initial Release
#
# 	1.1 - 2022-03-16 - Changed script target folder to scripts/gt_tools
#
#######################################

# Set Variables
BASEDIR=${PWD}
PYTHONDIR="$BASEDIR/python-scripts"
MELDIR="$BASEDIR/mel-scripts"
MAYADIR="/home/linux/maya"
is_uninstalling=false

# Tell the user that the setup is complete
print_uninstallation_complete() {
	echo ""
	echo " \033[1;96;1m Uninstallation Complete.\033[0m"
	echo "  Any issues? Let me know on Github. "
	echo "  Need help? Check the \"docs\" page."
	echo ""
	break
}

# Tell the user that the setup is complete
print_installation_complete() {
	echo ""
	echo " \033[1;92;1m Installation Complete. Enjoy!\033[0m"
	echo "  Scripts were installed. Please restart Maya load GT Tools menu."
	echo "  Any issues? Read the \"docs\" page on Github."
	echo ""
	break
}

# Copy files to "scripts" folder
copy_delete_files_to_maya_version() {
	install_dir=$1
	if $is_uninstalling ; then
  	 	rm "$install_dir/gt_tools_menu.mel"
  	 	rm "$install_dir/userSetup.mel"
		rm "$install_dir/gt_connect_attributes.py"
		rm "$install_dir/gt_connect_attributes.pyc"
		rm "$install_dir/gt_create_ctrl_auto_fk.py"
		rm "$install_dir/gt_create_ctrl_auto_fk.pyc"
		rm "$install_dir/gt_create_ctrl_auto_FK.py"
		rm "$install_dir/gt_create_ctrl_auto_FK.pyc"
		rm "$install_dir/gt_create_ctrl_simple_ik_leg.py"
		rm "$install_dir/gt_create_ctrl_simple_ik_leg.pyc"
		rm "$install_dir/gt_generate_icons.py"
		rm "$install_dir/gt_generate_icons.pyc"
		rm "$install_dir/gt_generate_inbetween.py"
		rm "$install_dir/gt_generate_inbetween.pyc"
		rm "$install_dir/gt_generate_python_curve.py"
		rm "$install_dir/gt_generate_python_curve.pyc"
		rm "$install_dir/gt_generate_text_curve.py"
		rm "$install_dir/gt_generate_text_curve.pyc"
		rm "$install_dir/gt_make_stretchy_leg.py"
		rm "$install_dir/gt_make_stretchy_leg.pyc"
		rm "$install_dir/gt_maya_to_discord.py"
		rm "$install_dir/gt_maya_to_discord.pyc"
		rm "$install_dir/gt_mirror_cluster_tool.py"
		rm "$install_dir/gt_mirror_cluster_tool.pyc"
		rm "$install_dir/gt_renamer.py"
		rm "$install_dir/gt_renamer.pyc"
		rm "$install_dir/gt_render_checklist.py"
		rm "$install_dir/gt_render_checklist.pyc"
		rm "$install_dir/gt_replace_reference_paths.py"
		rm "$install_dir/gt_replace_reference_paths.pyc"
		rm "$install_dir/gt_selection_manager.py"
		rm "$install_dir/gt_selection_manager.pyc"
		rm "$install_dir/gt_transfer_transforms.py"
		rm "$install_dir/gt_transfer_transforms.pyc"
		rm "$install_dir/gt_utilities.py"
		rm "$install_dir/gt_utilities.pyc"
		rm "$install_dir/gt_api.py"
		rm "$install_dir/gt_api.pyc"
		rm "$install_dir/gt_create_sphere_types.py"
		rm "$install_dir/gt_create_sphere_types.pyc"
		rm "$install_dir/gt_create_auto_fk.py"
		rm "$install_dir/gt_create_auto_fk.pyc"
		rm "$install_dir/gt_create_ik_leg.py"
		rm "$install_dir/gt_create_ik_leg.pyc"
		rm "$install_dir/gt_path_manager.py"
		rm "$install_dir/gt_path_manager.pyc"
		rm "$install_dir/gt_check_for_updates.py"
		rm "$install_dir/gt_check_for_updates.pyc"
		rm "$install_dir/gt_color_manager.py"
		rm "$install_dir/gt_color_manager.pyc"
		rm "$install_dir/gt_startup_booster.py"
		rm "$install_dir/gt_startup_booster.pyc"
		rm "$install_dir/gt_fspy_importer.py"
		rm "$install_dir/gt_fspy_importer.pyc"
		rm "$install_dir/gt_auto_biped_rigger.py"
		rm "$install_dir/gt_auto_biped_rigger.pyc"
		rm "$install_dir/gt_make_ik_stretchy.py"
		rm "$install_dir/gt_make_ik_stretchy.pyc"
		rm "$install_dir/gt_add_sine_attributes.py"
		rm "$install_dir/gt_add_sine_attributes.pyc"
		rm "$install_dir/gt_create_testing_keys.py"
		rm "$install_dir/gt_create_testing_keys.pyc"
		rm -r "$install_dir/gt_tools"
  	else
  		mkdir -p "$install_dir/gt_tools"
  		for f in "$PYTHONDIR/"*.py; do cp "$f" "$install_dir/gt_tools"; done
		for f in "$MELDIR/"*.mel; do cp "$f" "$install_dir"; done
	fi

}


# Change directory to Maya Folder and iterate through folders
cd_maya_folder(){
	cd "$MAYADIR"
	for i in $(ls -d -- */); do check_if_maya_version_folder ${i}; done
}

# Looks for a #### pattern to find Maya Versions
check_if_maya_version_folder(){
	current_dir=$1
	expr match "$current_dir" "[0-9][0-9][0-9][0-9]" >/dev/null && copy_delete_files_to_maya_version "$MAYADIR/$current_dir""scripts"
}



# Checks if Maya Dir exists before copying
maya_dir_exists () {
	if [ -d "$MAYADIR" ]
	then
	    cd_maya_folder
	    if $is_uninstalling ; then
  	 		print_uninstallation_complete
	  	else
	  		print_installation_complete
		fi
	else
		echo ""
		echo " \033[1;31;5m Error!!!\033[0m"
		echo "  Maya Directory couldn't be found.\n  You might have to install the scripts manually."
		echo "  For more information read the \"docs\" page."
		echo ""
		offer_to_open_docs
	fi
}

# Draws/Prints a big saying "GT Tools Setup" 
draw_gt_tools_text () {
	echo " ██████ ████████     ████████  ██████   ██████  ██      ███████ "
	echo "██         ██           ██    ██    ██ ██    ██ ██      ██      "
	echo "██   ███   ██           ██    ██    ██ ██    ██ ██      ███████ "
	echo "██    ██   ██           ██    ██    ██ ██    ██ ██           ██ "
	echo " ██████    ██           ██     ██████   ██████  ███████ ███████ "
	echo "                                                                "
	echo "                                                                "
	echo "                    ███████ ███████ ████████ ██    ██ ██████    "
	echo "                    ██      ██         ██    ██    ██ ██   ██   "
	echo "                    ███████ █████      ██    ██    ██ ██████    "
	echo "                         ██ ██         ██    ██    ██ ██        "
	echo "                    ███████ ███████    ██     ██████  ██        "
	echo "                                                                "
}

# Prints About Text
print_about_text () {	
	echo "__________________________________________________"
	echo ""
	echo "  This bash script attempts to automatically install all python and mel"
	echo "  scripts for GT Tools so the user doesn't need to mannualy copy them."
	echo ""
	echo "  It assumes that Maya preferences are stored in the default path"
	echo "  under \"/home/linux/maya/####\""
	echo "  (#### being the version number)"
	echo ""
	echo "  This is what the script does when installing:"
	echo "  1. It copies necessary scripts to all \"home/linux/maya/####/scripts\" folders."
	echo "  2. The Linux version of the installer currently overwrites the \"userSetup.mel\""
	echo "     so in case \"userSetup.mel\" is being used, make sure to backup first."
	echo ""
	echo "  This is what the script does when uninstalling:"
	echo "  1. It removes the installed scripts."
	echo ""
	echo "__________________________________________________"
}



# Opens the documentation for how to install GT Tools
offer_to_open_docs(){
	echo 'Type 1 or 2 then press ENTER: '
	echo "1 = Open \"docs\"" "2 = Exit Installation"

	read answer

	case "$answer" in
	    "1" )
	        xdg-open "https://github.com/TrevisanGMW/gt-tools/tree/master/docs"
	        break
	    ;;
	    "2" )
	        break
	    ;;
	    * )
	        echo "  Invalid Option"
	        break
	    ;;
	esac
}


# Run Script
echo ""
draw_gt_tools_text
echo "1 = Install GT Tools"
echo "2 = Uninstall GT Tools"
echo "3 = About Installer"
echo "4 = Exit Installer"
echo ""
echo 'Type 1, 2, 3 or 4 then press ENTER: '

read answer

case "$answer" in
    "1" )
        is_uninstalling=false
	    maya_dir_exists
        break
    ;;
    "2" )
        is_uninstalling=true
		maya_dir_exists
        break
    ;;
    "3" )
        print_about_text
   	    echo ""
        break
    ;;
    "4" )
        echo "  Closing script...."
		echo ""
        break
    ;;
    * )
        echo "  Invalid Option"
        break
    ;;
esac