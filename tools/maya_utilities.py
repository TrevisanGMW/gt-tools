"""
 GT Maya Utilities
 github.com/TrevisanGMW - 2020-09-13
 
 - 2020-10-17
 Added move pivot to bottom/top
 Added copy/paste material
 Added move to origin
 
 - 2020-10-21
 Updated reset transform to better handle translate
 Added Uniform LRA Toggle
 Changed the order of the functions to match the menu
 
 - 2020-11-11
 Updates "references_import" to better handle unloaded references
 Added "references_remove"
 Added "curves_combine"
 Added "curves_separate"
 
 - 2020-11-13
 Updated combine and separate functions to work with Bezier curves
 
 - 2020-11-14
 Added "convert_bif_to_mesh"
 
 - 2020-11-16
 Added "delete_nucleus_nodes"
 Updated "delete_display_layers" to have inView feedback
 Updated "delete_keyframes" to have inView feedback
 
 - 2020-11-22
 Updated about window text
 
 - 2020-12-03
 Changed the background color for the title in the "About" window
 Changed the order of a few functions
 Added function to unlock/unhide default channels
 
 - 2021-01-05
 Added Uniform Joint Label Toggle
 
 - 2021-02-05
 Added "Select Non-Unique Objects" Utility
 
 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)
 Added refresh to combine curves function as they were not automatically updating after re-parenting shapes
 
 - 2021-06-25
 Updated bif to mesh to work with newer versions of bifrost
 Updated bif to mesh to delete empty meshes (objects that weren't geometry)
 Added function to delete all locators
 
 - 2021-10-25
 Updated bif to mesh to work with newer versions of bifrost
 Updated bif to mesh to delete empty meshes (objects that weren't geometry)
 Added function to delete all locators
 
 - 2021-10-10
 Created Full HUD Toggle
 
 - 2021-10-10
 Fixed gtu full hud toggle as it would return an error if xGen was not loaded
  
 - 2022-01-04
 Renamed script to "gt_maya_utilities"
  
 - 2022-01-04
 Renamed script to "gt_maya_utilities"

 - 2022-06-29
 Added string to notepad (txt)
 Renamed functions

 - 2022-07-30
 Removed version (only dates now)
 Made inView messages unique
 Removed prefix "gtu_" from functions
     - Added or updated feedback for:
       - Force Reload File
       - Unlock Default Channels
       - Unhide Default Channels
       - Uniform LRA Toggle
       - Full Hud Toggle
       - Select Non-Unique Objects
       - Import References
       - Remove References

    - Added validation
       - Uniform LRA Toggle
       - Uniform Joint Label Toggle
       - Reset Transforms

 - 2022-07-31
     - Added or updated feedback for:
       - Generate UDIM Previews
       - Move Pivot to Top
       - Move Pivot to Base
       - Move Object To Origin

    - Added validation
       - Move Pivot to Top
       - Move Pivot to Base
       - Move Object To Origin

 - 2022-08-01
     - Added "Delete Unused Nodes"
     - Added "Convert to Locators"
     - Fixed "Reset Transforms" so it works with multiple objects again
     - Added scale to "Reset "persp" Camera"
     - Added or updated feedback for:
       - Reset Transforms
       - Reset Joint Display
       - Reset "persp" Camera
       - Combine Curves
       - Separate Curves

     - Added validation
       - Reset Joint Display
       - Reset Transforms
       - Reset Joint Display

     = Added more validation
       - Move Pivot to Top
       - Move Pivot to Base
       - Move Object To Origin
       - Combine Curves
       - Separate Curves

 - 2022-08-17
    - Added feedback for when no elements were affected
    - Added some more validation

 - 2022-08-31
    - Added open file directory
    - Updated open file directory to support Mac-OS

 - 2023-02-23
    - Updated namespace delete function to allow for only selected elements
    - Added Set Joint Name as Label

 TODO:
     New functions:
        Assign lambert to everything function (Maybe assign to object missing shaders)
        Add Unlock all attributes
        Add unhide attributes (provide list?)
        Add Remove pasted_ function
        Add assign checkerboard function (already in bonus tools > rendering)
        Force focus (focus without looking at children)
        Brute force clean models (export OBJ and reimport)
     New options:
        Import all references : Add function to use a string to ignore certain references
        Reset Transforms : Add reset only translate, rotate or scale
        Delete all keyframes : Include option to delete or not set driven keys
        Reset persp camera : Reset all other attributes too (including transform?)
        Delete Display Layers : only empty? ignore string?
        Delete Namespaces : only empty? ignore string?
    
"""

# """ ____________________________ Functions Calls ____________________________"""
if __name__ == '__main__':
    pass
    # force_reload_file()
    # open_resource_browser()
    # unlock_default_channels()
    # unhide_default_channels()
    # references_import()
    # references_remove()
    # toggle_uniform_lra()
    # toggle_uniform_jnt_label()
    # select_non_unique_objects()
    set_joint_name_as_label()
    #
    # generate_udim_previews()
    # material_copy()
    # material_paste()
    #
    # move_pivot_top()
    # move_pivot_base()
    # move_to_origin()
    #
    # reset_joint_display()
    # reset_transforms()
    # reset_persp_shape_attributes()
    #
    # delete_namespaces()
    # delete_display_layers()
    # delete_keyframes()
    # delete_nucleus_nodes()
    # delete_user_defined_attributes()
    # delete_unused_nodes()
    # delete_all_locators()
    #
    # # --- Outside Utilities ---
    # curves_combine()
    # curves_separate()
    # convert_bif_to_mesh()
    # convert_to_locators()
    #
    # build_gui_about_gt_tools()
    #
    # # --- Other Functions ---
    # toggle_full_hud()
    # convert_joints_to_mesh()
    # output_string_to_notepad('Test')
