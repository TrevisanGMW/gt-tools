import maya.cmds as cmds
import maya.mel as mel

# GT Replace Reference Paths Script
# @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-03-03
# Last update - 2020-03-03
# https://github.com/TrevisanGMW
#
# To do: 
# Show list of current paths directly in the UI
# Add an option for the user to auto search through folders for his reference.

scriptVersion = "v1.0";

defaultSearchPath = "H:\\"
defaultReplacePath = "\\\\vfsstorage10\\3D\\Students"


#Loads PyMel (if necessary)
try:
    pm.about(version=True)
except:
    if cmds.window("pyMelLoadMessage", exists =True):
        cmds.deleteUI("pyMelLoadMessage")    

    pyMelLoadMessage = cmds.window("pyMelLoadMessage", title="PyMel",\
                          titleBar=True,minimizeButton=False,maximizeButton=False, sizeable =False)
    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("", h=5)
    cmds.text("    Loading PyMel     ", bgc=[.1,.1,.1],  fn="boldLabelFont")
    cmds.text("    Please Wait     ", bgc=[.1,.1,.1],  fn="boldLabelFont")
    cmds.text(" ", h=5)
    cmds.showWindow(pyMelLoadMessage)

    import pymel.core as pm
                                                                   
    if cmds.window("pyMelLoadMessage", exists =True):
        cmds.deleteUI("pyMelLoadMessage")  


# Store References
refs = pm.listReferences()

# Main Form ============================================================================
def replaceReferencePathsDialog():
    if cmds.window("replaceReferencePathsDialog", exists =True):
        cmds.deleteUI("replaceReferencePathsDialog")    

    # mainDialog Start Here =================================================================================
    
    # Build UI
    replaceReferencePathsDialog = cmds.window("replaceReferencePathsDialog", title="gt_ref_paths - " + scriptVersion,\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)
    
    contentMain = cmds.columnLayout(adj = True)

    
    cmds.text(" ")
    row1 = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, ) #Empty Space
    cmds.text( "      GT - Replace Reference Paths -  " + scriptVersion + "     ",p=row1, bgc=[0,.5,0],  fn="boldLabelFont")
    
    cmds.button( l ="Help", bgc=(0, .5, 0), c=lambda x:helpMenuDialog())
    cmds.text("    ", bgc=[0,.5,0])
    
    
    cmds.rowColumnLayout(p=contentMain)

    # cmds.text(" ")
    # cmds.text("GT - Replace Reference Paths - " + scriptVersion, bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("      This script allows you to search and replace       ")
    cmds.text('      strings in the path of your references.   ')
    cmds.text('        ')
    cmds.text('    It auto adjusts the direction of slashes   ', fn="boldLabelFont")
    cmds.text('        ', height=13)

    cmds.separator(h=15, p=contentMain)
    
    cmds.button(l ="Print Current Paths", c=lambda x:printCurrentPaths("print"))
    
    
    bottomContainer = cmds.rowColumnLayout(p=contentMain,adj=True)
    cmds.text('Search:',p=bottomContainer)
    searchTextfield = cmds.textField(p = bottomContainer, text=defaultSearchPath, enterCommand=lambda x:searchAndReplaceReferencePath\
                                        (cmds.textField(searchTextfield, q=True, text=True),\
                                        cmds.textField(replaceTextfield, q=True, text=True)))
    cmds.separator(h=15)
 
    
    bottomContainer = cmds.rowColumnLayout(p=contentMain,adj=True)
    cmds.text('Replace:',p=bottomContainer)
    replaceTextfield = cmds.textField(p = bottomContainer, text=defaultReplacePath, enterCommand=lambda x:searchAndReplaceReferencePath\
                                        (cmds.textField(searchTextfield, q=True, text=True),\
                                        cmds.textField(replaceTextfield, q=True, text=True)))
    cmds.text(' ',p=bottomContainer, height=7)
    cmds.button( l ="Attempt to Auto Detect Student Path (VFS)", c=lambda x:autoDetectPath())
    cmds.separator(h=15)
    cmds.button( l ="Replace", bgc=(.6, .8, .6), c=lambda x:searchAndReplaceReferencePath\
                                        (cmds.textField(searchTextfield, q=True, text=True),\
                                        cmds.textField(replaceTextfield, q=True, text=True)))
                                                                        
    def autoDetectPath():
        filePath = cmds.file(q=True, sn=True)
        if filePath != '':
            currentPathAsList = filePath.split("/") # check its length
            if len(currentPathAsList) >= 6:
                guessedPath = currentPathAsList[0] + '/' + currentPathAsList[1] + '/' + currentPathAsList[2] + '/' \
                + currentPathAsList[3] + '/' + currentPathAsList[4] + '/' + currentPathAsList[5] + '/' + currentPathAsList[6]  + '/' 
                cmds.textField(replaceTextfield, e=True, text=guessedPath)
            else:
                cmds.warning("The length of the path found doesn't seem to be long enough. Try opening the scene directly from the students folder")
        else:
            cmds.warning("Scene file path seems empty, try opening the scene instead of importing it")

                                                                                                                              
    cmds.showWindow(replaceReferencePathsDialog)

    # mainDialog Ends Here =================================================================================

def printCurrentPaths(headerMode):
    print("#" * 80)
    if headerMode == "print":
        print("     References Paths:")
    else:
        print("     Updated References Paths:")
    for ref in refs:
        print("%s"%  ref.path) #Old Path
    print("#" * 80)
    if headerMode == "print":
        cmds.headsUpMessage( 'Open script editor to see a list of the current paths', verticalOffset=150 , time=5.0)
    else:
        cmds.headsUpMessage( 'Open script editor to see an updated list of paths', verticalOffset=150 , time=5.0)


def searchAndReplaceReferencePath(search,replace):

    invertSlashSearch = search.replace("\\","/")
    invertSlashReplace = replace.replace("\\","/")
    
    for ref in refs:
        newPath = ("%s"%  ref.path).replace(invertSlashSearch,invertSlashReplace)
        referenceNode = ("%s" % ref.refNode)
        cmds.file(newPath, loadReference=referenceNode)
        
    printCurrentPaths("replace")


def helpMenuDialog():
    if cmds.window("helpMenuDialog", exists =True):
        cmds.deleteUI("helpMenuDialog")    

    # About Dialog Start Here =================================================================================
    
    # Build About UI
    helpMenuDialog = cmds.window("helpMenuDialog", title="GT Replace Ref Path - Help",\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain)

    contentMain = cmds.columnLayout(adj = True)

    cmds.text("")
    cmds.text("Help for GT Replace Reference Paths ", bgc=[0,.5,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text(" Version Installed: " + scriptVersion)
    cmds.text("  ")
    cmds.text("      This script allows you to search for a string       ")
    cmds.text('      in the path for your references and replace it  ')
    cmds.text(' ')
    cmds.text('      The "Print Current Paths" button prints a list   ')
    cmds.text('      containing the current path of all your references.    ')
    cmds.text('      Use this to make sure you\'re searching for the    ')
    cmds.text('      correct string.    ')
    cmds.text(' ')
    cmds.text('      Under that, you\'ll find two text fields (boxes),    ')
    cmds.text('      type the string you want to search for on the first      ')
    cmds.text('      one (Search:), and what you want to replace    ')
    cmds.text('      it with in the second (Replace:)    ')
    cmds.text(' ')
    cmds.text('      In case you\'re using this script at VFS you can   ')
    cmds.text('      try to use the "Attempt to Auto Detect Student Path (VFS)"    ')
    cmds.text('      This button will use the path of the scene to try to    ')
    cmds.text('      figure it out what the path of your reference should be    ')
    cmds.text('      (so you don\'t have to find the path manually every time)    ')
    cmds.text(' ')
    cmds.text("      In case something doesn't work or you    ")
    cmds.text('      have a suggestion, send me an email.    ')
    cmds.text(' ')

    emailContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    
    cmds.text('             Guilherme Trevisan : ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1], p=emailContainer)
    websiteContainer = cmds.rowColumnLayout(p=contentMain, numberOfRows=1, h= 25)
    cmds.text('                      Visit my ')
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1], p=websiteContainer)
    cmds.text(' for updated versions')
    cmds.text(' ', p= contentMain)
    cmds.separator(h=15, p=contentMain)
    
    cmds.button(l ="Ok", p= contentMain, c=lambda x:closeAboutWindow())
                                                                                                                              
    def closeAboutWindow():
        if cmds.window("helpMenuDialog", exists =True):
            cmds.deleteUI("helpMenuDialog")  
        
    cmds.showWindow(helpMenuDialog)
    
    # About Dialog Ends Here =================================================================================


#Run Script
replaceReferencePathsDialog()
