'''
An example of how to geenrate user interface using Python and Maya commands (cmds)
For more documentation go to "Maya > Help > Maya Scripting Reference > Python Command Reference" or visit the link below:
https://help.autodesk.com/view/MAYAUL/2020/ENU/index.html?contextId=COMMANDSPYTHON-INDEX
'''
import maya.cmds as cmds # Import Maya API


def window_name(): # Define a function for the window
    if cmds.window("window_name", exists =True): # Check if the window exists
        cmds.deleteUI("window_name")# if it does, delete it (so you don't have multiple windows with the same content)

    # main dialog start here =================================================================================

    window_name = cmds.window("window_name", title="My Window",\
                          titleBar=True,minimizeButton=False,maximizeButton=False, sizeable =True)# Create a window object (Unsure what the parameters do? Search for the documentation for cmds.window)
                          
    content_main = cmds.columnLayout(adj = True) # Create a column to populate with elements
    
    cmds.separator(h=5, st="none" ) # Empty Space
    # Create a text (these elements are all children of the columnLayout we created above, unless otherwise declared)
    # How do you change the parent of a UI element? Use the "parent" parameter. For example cmds.text(parent='content_main_02')
    my_text = cmds.text("This is an example of a text!") # Notice that the text is stored in a variable so we can reference it later
    cmds.separator(h=10, st="none" ) # Empty Space
    
    my_textfield = cmds.textField(placeholderText='This is a textfield') # Creates a textfield, and store it in a variable so we can reference it later
    cmds.separator(h=10, st="none" ) # Empty Space
    
    # Create a rowColumnLayout so we can have multiple elements in a row (this element is super helpful when adjusting your UI)
    # columnWidth needs a list of tuples describing every column. For example [(1, 10)(2, 15)] would make change columns of the size 10 and 15
    cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100),(3,10)], cs=[(1,10),(2,5),(3,5)]) 
    
    cmds.button(l ="Create Cube", c=lambda x:create_standard_cube(), w=100, bgc=(.3,.7,.3)) # Create a button - (The lambda part of it is to make the button capable of calling other functions)
    cmds.button(l ="Create Sphere", c=lambda x:create_standard_sphere(), w=100, bgc=(.3,.7,.3)) # Another button
    cmds.separator(h=5, st="none" ) # Empty Space
    
    cmds.rowColumnLayout( p=content_main, numberOfColumns=1, columnWidth=[(1, 205), (2, 100),(3,10)], cs=[(1,10),(2,5),(3,5)]) # Another rowColumnLayout, this time with only one Column
    cmds.separator(h=5, st="none" ) # Empty Space
    cmds.button(l ="Replace Text with Textfield", c=lambda x:replace_textfield(), w=100, bgc=(.3,.7,.3)) # Another button to update the text

    cmds.separator(h=10, st="none" )# Empty Space
    
    # Functions for the buttons (They have been declared inside of the main function so the have access to the button variables)
    def create_standard_sphere(): # A function to create a sphere (used by one of the buttons)
        cmds.polySphere(name='mySphere') # Function to create a simple sphere named "mySphere"
        
    def create_standard_cube(): # Same thing for a cube
        cmds.polyCube(name='myCube') # Function to create a simple cube named "myCube"
        
    def replace_textfield(): # Function to replace the text element with the provided text
        # Query the the information from the text field, dump it into a variable. The "q=True" means query, "text=True" tells the function what to query.
        text_from_textfield = cmds.textField(my_textfield, q=True, text=True) 
        # Update the text with the information that what extracted from the variable
        # Instead of using "q=True", this time we used "e=True" which means "edit". "label=text_from_textfield" determines what is being edited.
        cmds.text(my_text, e=True, label=text_from_textfield) 
    
    cmds.showWindow(window_name) # Finally show the window element we created at the beginning
    # main dialog ends here =================================================================================


window_name() # Call the main function