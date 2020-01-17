import maya.cmds as cmds

# Control Rig Grading Script
# Script created for Rigging 1 (Term 2, Vancouver Film School)
# @Guilherme Trevisan - 2019-12-09
# Last update - 2020-01-14 - Fixed the width and ratio of the window
# Version:
scriptVersion = "v1.1"
currentModel = "Betty"

# Define Main Lists
unparentList = ['rootCtrl','geo_grp']
deleteList = ['controls', 'control_grp','DO_NOT_TOUCH','proxy_geo_grp','skeleton','skeleton_grp','Betty']
wireSystemElements = ['left_upper_eyelashBaseWire','left_lower_eyelashBaseWire','left_eyebrow_BaseWire', \
                      'right_upper_eyelashBaseWire','right_eyebrow_BaseWire','right_lower_eyelashBaseWire',]
thumbFingersCtrl = ['left_thumb1Ctrl', 'left_thumb2Ctrl', 'left_thumb3Ctrl', 'left_thumbEndCtrl', \
                'right_thumb1Ctrl', 'right_thumb2Ctrl', 'right_thumb3Ctrl', 'right_thumbEndCtrl']
                    
indexFingersCtrl = ['left_index1Ctrl', 'left_index2Ctrl', 'left_index3Ctrl', 'left_indexEndCtrl', \
                'right_index1Ctrl', 'right_index2Ctrl', 'right_index3Ctrl', 'right_indexEndCtrl']
                    
middleFingersCtrl = ['left_middle1Ctrl', 'left_middle2Ctrl', 'left_middle3Ctrl', 'left_middleEndCtrl', \
                'right_middle1Ctrl', 'right_middle2Ctrl', 'right_middle3Ctrl', 'right_middleEndCtrl']
                    
ringFingersCtrl = ['left_ring1Ctrl', 'left_ring2Ctrl', 'left_ring3Ctrl', 'left_ringEndCtrl', \
                'right_ring1Ctrl', 'right_ring2Ctrl', 'right_ring3Ctrl', 'right_ringEndCtrl']
                    
pinkyFingersCtrl = ['left_pinky1Ctrl', 'left_pinky2Ctrl', 'left_pinky3Ctrl', 'left_pinkyEndCtrl', \
                'right_pinky1Ctrl', 'right_pinky2Ctrl', 'right_pinky3Ctrl', 'right_pinkyEndCtrl']
spineListCtrl = ['spine1Ctrl', 'spine2Ctrl', 'spine3Ctrl',]

#Defines Settings Dictionary
settingsDefault = { 'intervalBetweenKeyframes': 10, 
             'showSkeleton': False,
             'resetViewport': True,
             'showOpenDialog': False,
             'psychedelicCamera': False
            }
settings = { 'intervalBetweenKeyframes': 10, 
             'showSkeleton': False,
             'resetViewport': True,
             'showOpenDialog': False,
             'psychedelicCamera': False
            }

# Defines how fast the animations will happen
#intervalBetweenKeyframes = 10

# Defines size of joints
defaultJointSize = 1

# If objects in the list exists, it gets deleted, else print to expression editor
def bruteforceCleanUpScene(deleteList):
    deleted = []
    print('_' * 80)
    for trash in deleteList:
        #print(trash) # debugging
        if cmds.objExists(trash):
            cmds.select(trash)
            deletionContainer = cmds.ls(selection=True)[0]
            cmds.delete(deletionContainer)
            deleted.append(trash)
        else:
            print('"' + trash + ' was not found in the scene')

# If persp shape exists, reset its attributes
def resetPerspShapeAttributes():
    if cmds.objExists('perspShape'):
        cmds.setAttr('perspShape' + ".focalLength", 35)
        cmds.setAttr('perspShape' + ".verticalFilmAperture", 0.945)
        cmds.setAttr('perspShape' + ".horizontalFilmAperture", 1.417)
        cmds.setAttr('perspShape' + ".lensSqueezeRatio", 1)
        cmds.setAttr('perspShape' + ".fStop", 5.6)
        cmds.setAttr('perspShape' + ".focusDistance", 5)
        cmds.setAttr('perspShape' + ".shutterAngle", 144)
        cmds.setAttr('perspShape' + ".centerOfInterest", 44.822)
        cmds.setAttr('perspShape' + ".locatorScale", 1)
        cmds.setAttr('perspShape' + ".nearClipPlane", 0.100)
        cmds.setAttr('perspShape' + ".farClipPlane", 10000.000)
        cmds.setAttr('perspShape' + ".cameraScale", 1)
        cmds.setAttr('perspShape' + ".preScale", 1)
        cmds.setAttr('perspShape' + ".postScale", 1)
        cmds.setAttr('perspShape' + ".depthOfField", 0)

# Reset all modelPanels (Viewport)
def resetViewport(showSkeleton):
    try:
        panelList = cmds.getPanel(type="modelPanel")
    
        for eachPanel in panelList:
            print(eachPanel)
            cmds.modelEditor(eachPanel, e=1, allObjects=0)
            cmds.modelEditor(eachPanel, e=1, polymeshes=1)
            cmds.modelEditor(eachPanel, e=1, joints=1)
            if showSkeleton is False:
                cmds.modelEditor(eachPanel, e=1, joints=0)
            cmds.modelEditor(eachPanel, e=1, nurbsCurves=1)
            cmds.modelEditor(eachPanel, e=1, ikHandles=1)
            cmds.modelEditor(eachPanel, e=1, locators=1)
            cmds.modelEditor(eachPanel, e=1, grid=0)
            cmds.modelEditor(eachPanel, e=1, displayLights='default')
            cmds.modelEditor(eachPanel, e=1, udm=False)
            cmds.modelEditor(eachPanel, e=1, wireframeOnShaded=0)
            cmds.modelEditor(eachPanel, e=1, displayTextures=1)
            cmds.DisplayShadedAndTextured()
    except:
        cmds.warning("Something went wrong, script couldn't find the viewport")
        
# Sets visibility for all display layers
def setLayersVisibility(value):
	layers = cmds.ls(long=True, type='displayLayer')
	for l in layers[0:]:	
		if l.find("defaultLayer") == -1:													
			cmds.setAttr( '%s.visibility' % l, value)

# Sets display layer type
def setLayersDisplayType(value):
	layers = cmds.ls(long=True, type='displayLayer')
	for l in layers[0:]:	
		if l.find("defaultLayer") == -1:
                    cmds.setAttr(l + '.displayType', value)
            
# Applied a new lambert with a checker to objects in the list
def applyMaterial(nodeList):
    for node in nodeList:
        if cmds.objExists(node):
            shd = cmds.shadingNode('lambert', name="%s_lambert" % node, asShader=True)
            shdSG = cmds.sets(name='%sSG' % shd, empty=True, renderable=True, noSurfaceShader=True)
            cmds.connectAttr('%s.outColor' % shd, '%s.surfaceShader' % shdSG)
            cmds.sets(node, e=True, forceElement=shdSG)
            checkerNode = cmds.shadingNode("checker", asTexture=True, n = "Checker_%s" % node)
            checkerUVNode = cmds.shadingNode("place2dTexture", asTexture=True, n = "text_%s" % node)
            cmds.connectAttr('%s.outColor' %checkerNode,'%s.color' %shd)
            cmds.connectAttr('%s.outUV' %checkerUVNode,'%s.uvCoord' %checkerNode)
            cmds.connectAttr('%s.outUvFilterSize' %checkerUVNode,'%s.uvFilterSize' %checkerNode)
            cmds.setAttr(checkerUVNode + ".repeatU", 4)
            cmds.setAttr(checkerUVNode + ".repeatV", 4)

# Removes non-vector key frames from attribute
def removeKeyFramesNonVector(objList,attributeToRemoveKey):
    for objId in objList:
        if cmds.objExists(objId):
            cmds.select(objId)
            myObj = cmds.ls(selection=True)[0]
            cmds.cutKey(myObj, time = (0, 2000), clear = True)
            cmds.cutKey( myObj, time=(0,1000), attribute=attributeToRemoveKey, option="keys" )

# Removes key frames from attributes
def removeKeyFrames(objList,attributeToRemoveKey):
    for objId in objList:
        if cmds.objExists(objId):
            cmds.select(objId)
            myObj = cmds.ls(selection=True)[0]
            cmds.cutKey(myObj, time = (0, 2000), clear = True)
            cmds.setAttr(myObj + "." + attributeToRemoveKey, 0,0,0)
 
# Keys provided parameters      
def keyAttributes(objList, value, attribute, atFrame):
    for objId in objList:
        if cmds.objExists(objId):
            cmds.select(objId)
            myObj = cmds.ls(selection=True)[0]
            cmds.setKeyframe(myObj, v=value, at=attribute, t=atFrame )

# Keys attributes that are not locked  
def keyAttributesIfNotLocked(objList, value, attribute, atFrame, lockedAttribute):
    for objId in objList:
        if cmds.objExists(objId):
            if cmds.getAttr(objId + lockedAttribute ,lock=True) is False:
                cmds.select(objId)
                myObj = cmds.ls(selection=True)[0]
                cmds.setKeyframe(myObj, v=value, at=attribute, t=atFrame )

# Change position of the camera and then look through it
def changeCameraPosition(translateX,translateY,translateZ,rotateX,rotateY,rotateZ):
    if cmds.objExists('persp'):
        cmds.select('persp')
        cam = cmds.ls(selection=True)[0]
        cmds.setAttr(cam + '.translate', translateX,translateY,translateZ)
        cmds.setAttr(cam + '.rotate', rotateX,rotateY,rotateZ)
        cmds.lookThru(cam)
    else:
        print('UNEXPECTED ERROR! "persp" camera not found!!!!!!!!')
        
def makeObjectPsychedelic(object,parent,timeStart,timeEnd,keepPrevious):
    
    if keepPrevious is False:
        print(object +'_parentConstraint1')
        if cmds.objExists(object +'_parentConstraint1'):
            cmds.delete(object + '_parentConstraint1')
        
    if cmds.objExists(object):
        cmds.select(object)
        obj = cmds.ls(selection=True)[0]
        constraintOne = cmds.parentConstraint(parent,obj, mo=True)
        cmds.setKeyframe(constraintOne, v=0, at=(parent + "W0"), t=timeStart - 1)
        cmds.setKeyframe(constraintOne, v=1, at=(parent + "W0"), t=timeStart)
        cmds.setKeyframe(constraintOne, v=1, at=(parent + "W0"), t=(timeEnd - timeEnd/10))
        cmds.setKeyframe(constraintOne, v=0, at=(parent + "W0"), t=timeEnd)
        cmds.setKeyframe(constraintOne, v=0, at=(parent + "W1"), t=timeStart - 1)
        cmds.setKeyframe(constraintOne, v=1, at=(parent + "W1"), t=timeStart)
        cmds.setKeyframe(constraintOne, v=1, at=(parent + "W1"), t=(timeEnd - timeEnd/10))
        cmds.setKeyframe(constraintOne, v=0, at=(parent + "W1"), t=timeEnd)
        cmds.setKeyframe(constraintOne, v=0, at=(parent + "W2"), t=timeStart - 1)
        cmds.setKeyframe(constraintOne, v=1, at=(parent + "W2"), t=timeStart)
        cmds.setKeyframe(constraintOne, v=1, at=(parent + "W2"), t=(timeEnd - timeEnd/10))
        cmds.setKeyframe(constraintOne, v=0, at=(parent + "W2"), t=timeEnd)
    else:
        print('UNEXPECTED ERROR! Object not found!!!!!!!!')
        
        
# Keys a camera
def keyAllAttributes(object, time, tx,ty,tz,rx,ry,rz):
            cmds.setKeyframe(object, v=tx, at='translateX', t=time)
            cmds.setKeyframe(object, v=ty, at='translateY', t=time)
            cmds.setKeyframe(object, v=tz, at='translateZ', t=time)
            cmds.setKeyframe(object, v=rx, at='rotateX', t=time)
            cmds.setKeyframe(object, v=ry, at='rotateY', t=time)
            cmds.setKeyframe(object, v=rz, at='rotateZ', t=time)
            

# Unlocks attribute from a list of objects
def unlockLocked(objList, attributeName):
    lockedElements = []
    for objId in objList:
        if cmds.objExists(objId):
            if cmds.getAttr(objId + "." + attributeName ,lock=True) is True:
                lockedElements.append(objId)
                cmds.setAttr(objId + "." + attributeName, lock=0)
    #Tell user that it was locked.
    '''            
    if len(lockedElements) > 0:
        print(lockedElements)
        cmds.warning("Some elements that shouldn't be locked were locked. Open Expression Editor to see list")
        #cmds.confirmDialog(str(lockedElements) + " was locked")
    '''
    
# Updates joints radius if it's not locked
def updateRadiusIfNotLocked(objList, value):
    for objId in objList:
        if cmds.objExists(objId):
            if cmds.getAttr(objId + ".radius" ,lock=True) is False:
                cmds.select(objId)
                myObj = cmds.ls(selection=True)[0]
                cmds.setAttr(objId + '.radius', value)

# Keys Arms
def keyArms(shoulderName,elbowName,intervalBetweenKeyframes):
    if cmds.objExists(elbowName):
        cmds.select(elbowName)
        elbowSelection = cmds.ls(selection=True)[0]
        cmds.setKeyframe(elbowSelection, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 4))
        cmds.setKeyframe(elbowSelection, v=-90, at='rotateZ', t=(intervalBetweenKeyframes * 5 ))
        cmds.setKeyframe(elbowSelection, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 6))
        if cmds.objExists(shoulderName):
            cmds.select(shoulderName)
            shoulderSelection = cmds.ls(selection=True)[0]
            cmds.setKeyframe(shoulderSelection, v=0, at='rotateY', t=(intervalBetweenKeyframes * 6))
            cmds.setKeyframe(shoulderSelection, v=-50, at='rotateY', t=(intervalBetweenKeyframes * 7 ))
            cmds.setKeyframe(shoulderSelection, v=0, at='rotateY', t=(intervalBetweenKeyframes * 8 ))
            cmds.setKeyframe(shoulderSelection, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 8 ))
            cmds.setKeyframe(shoulderSelection, v=-50, at='rotateZ', t=(intervalBetweenKeyframes * 9 ))
            cmds.setKeyframe(shoulderSelection, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 10 ))

# Keys Spine
def keySpine(spineListCtrl,intervalBetweenKeyframes):    
    for spine in spineListCtrl:
        if cmds.objExists(spine):
            cmds.select(spine)
            spine = cmds.ls(selection=True)[0]
            cmds.setKeyframe(spine, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 10))
            cmds.setKeyframe(spine, v=30, at='rotateZ', t=(intervalBetweenKeyframes * 11 ))
            cmds.setKeyframe(spine, v=-30, at='rotateZ', t=(intervalBetweenKeyframes * 13 ))
            cmds.setKeyframe(spine, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 14))

# Main Control Rig Grading Dialog
def controlRigCheckMainDialog():
    if cmds.window("crMainDialog", exists =True):
        cmds.deleteUI("crMainDialog")    

    # crMainDialog Start Here =================================================================================

    crMainDialog = cmds.window("crMainDialog", title="Controls Rig Grading Script - " + scriptVersion, widthHeight=(382,236),\
                          titleBar=True,minimizeButton=True,maximizeButton=False, sizeable =False)

    columnMain = cmds.columnLayout() 

    form = cmds.formLayout(p=columnMain,)
    tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5, p=form,  width = 380)

    tabMain = cmds.columnLayout(adj = True, p=tabs)

    cmds.text("")
    cmds.text("Warning!", bgc=[.3,0,0],  fn="boldLabelFont")
    cmds.text("  ")
    cmds.text("This script will break your scene!")
    cmds.text("SAVE IT FIRST IN CASE YOU WANT TO PROCEED")
    cmds.text("   ")

    cmds.separator(h=10, p=tabMain)
    cmds.text(" ")
    cgOrganizationContainer = cmds.columnLayout(p=tabMain)
    crOrganization = cmds.intSliderGrp('crMainDialog', width = 350 ,p=cgOrganizationContainer, l = "Organization Grade",min =0,max =10, field =True, value=10)
    crDeductionContainer = cmds.columnLayout(p=tabMain)
    crDeduction = cmds.intSliderGrp(l = "Deduction Grade",  width = 350 ,p=crDeductionContainer ,min =0,max =100, field =True, value=0)
    cmds.separator(h=10)

    #Settings Tab ======================================================
    tabSettings = cmds.rowColumnLayout(numberOfColumns=2, p=tabs)
    
    settingsContainer = cmds.columnLayout(p=tabSettings)
    cmds.text("   ", p=settingsContainer)
    cmds.text("   ", p=settingsContainer, height = 10)
    crSpeed = cmds.intSliderGrp(l = "Interval Between Keys",  width = 350 ,p=settingsContainer ,min =0,max =100, field =True, value=settings.get("intervalBetweenKeyframes"))
    cmds.text("   ", p=settingsContainer, height = 10)
    checkboxContainer = cmds.rowColumnLayout(numberOfColumns=2, adj=True)
    cmds.text("            Viewport :    ", p=checkboxContainer)

    checkboxSettingsOne = cmds.checkBoxGrp(p=checkboxContainer, numberOfCheckBoxes=2, labelArray2=['Show Skeleton', 'Reset Viewport'], value1 = settings.get("showSkeleton"), value2 = settings.get("resetViewport"))
    cmds.text("   ", p=settingsContainer, height = 10)
    cmds.text("            Bonus :    ", p=checkboxContainer)
    checkboxSettingsTwo = cmds.checkBoxGrp(p=checkboxContainer, numberOfCheckBoxes=2, labelArray2=['Open Dialog', 'Psychedelic Camera'], value1 = settings.get("showOpenDialog"), value2 = settings.get("psychedelicCamera"))
    settingsSeparator = cmds.rowColumnLayout(numberOfColumns=2, p=settingsContainer, adj=True, width = 370)
    cmds.separator(p=settingsSeparator)
    cmds.text("   ", p=settingsContainer, height = 10)
    settingsButtons = cmds.rowColumnLayout(numberOfColumns=2, p=settingsContainer)
    cmds.button(p=settingsButtons, l ="Save Changes",w=184, h=40, c=lambda x:saveModifiedSettings())
    cmds.button(p=settingsButtons, l ="Restore Default",w=184, h=40, c=lambda x:restoreDefaultSettings())


    def saveModifiedSettings():
        settings["intervalBetweenKeyframes"] = cmds.intSliderGrp(crSpeed, q= True,value =True)
        settings["showSkeleton"] = cmds.checkBoxGrp (checkboxSettingsOne, q=True, value1=True)
        settings["resetViewport"] = cmds.checkBoxGrp (checkboxSettingsOne, q=True, value2=True)
        settings["showOpenDialog"] = cmds.checkBoxGrp (checkboxSettingsTwo, q=True, value1=True)
        settings["psychedelicCamera"] = cmds.checkBoxGrp (checkboxSettingsTwo, q=True, value2=True)
        print(settings.get("intervalBetweenKeyframes"))
        print(settings.get("showSkeleton"))
        print(settings.get("resetViewport"))
        print(settings.get("showOpenDialog"))
        print(settings.get("psychedelicCamera"))
        print("Current Settings Saved")
        
    def restoreDefaultSettings():
        settings["intervalBetweenKeyframes"] = settingsDefault.get("intervalBetweenKeyframes")
        settings["showSkeleton"] = settingsDefault.get("showSkeleton")
        settings["resetViewport"] = settingsDefault.get("resetViewport")
        settings["showOpenDialog"] = settingsDefault.get("showOpenDialog")
        settings["psychedelicCamera"] = settingsDefault.get("psychedelicCamera")
        cmds.intSliderGrp(crSpeed, e=True, value = settings["intervalBetweenKeyframes"])
        cmds.checkBoxGrp(checkboxSettingsOne, e=True, value1 = settings["showSkeleton"])
        cmds.checkBoxGrp(checkboxSettingsOne, e=True, value2 = settings["resetViewport"])
        cmds.checkBoxGrp(checkboxSettingsTwo, e=True, value1 = settings["showOpenDialog"])
        cmds.checkBoxGrp(checkboxSettingsTwo, e=True, value2 = settings["psychedelicCamera"])
        print("Default Settings Restored")

    #About Tab ======================================================
    tabAbout = cmds.columnLayout(p=tabs, adj=True)

    aboutContainer = cmds.rowColumnLayout(numberOfColumns=2, height = 33, width = 300)
    cmds.text("Control Rig Grading Script - VFS - " + scriptVersion  , p=tabAbout, ww=False)
    cmds.text("Current model being rigged:  " + currentModel, p=tabAbout, ww=True)
    cmds.text("This script was created for grading, use it at your own risk", p=tabAbout, ww=False)
    cmds.text("Problems? Questions? Send me an email:", p=tabAbout, ww=True)
    cmds.text(l='<a href="mailto:gtrevisan@gmail.com">Guilherme Trevisan : gtrevisan@vfs.com</a>', hl=True, p=tabAbout, highlightColor=[1,1,1])

    #Generate Tabs
    cmds.tabLayout(tabs, edit=True, tabLabel=((tabMain, 'Grader'),(tabSettings, 'Settings'),(tabAbout,'About')))

    #Outside Tabs
    outsideTabs = cmds.rowLayout(numberOfColumns=2, p=columnMain)
    startScript = cmds.rowLayout(numberOfColumns=2, p=outsideTabs)
    cmds.button(p=startScript, l ="Run Script", w=375, h=40, bgc = (.6, .8, .6), c=lambda x:controlRigCheckFK(cmds.intSliderGrp(\
                crOrganization, q= True,value =True), cmds.intSliderGrp(crDeduction, q= True,value =True)))
    cmds.showWindow(crMainDialog)
    # crMainDialog Ends Here =================================================================================


# Forward Kinematics Check + Initial Setup
def controlRigCheckFK(organizationGrade,deductionGrade):
    
    #Delete previous dialog
    if cmds.window("crMainDialog", exists =True):
        cmds.deleteUI("crMainDialog")

    #Reset Persp Camera
    resetPerspShapeAttributes()

    #Setup Viewport
    if settings.get("resetViewport"):
        #resetViewport()
        resetViewport(settings.get("showSkeleton"))
        setLayersVisibility(True)
        setLayersDisplayType(0)
    
    #Normalize all joints
    allJoints = cmds.ls(type='joint')
    updateRadiusIfNotLocked(allJoints, defaultJointSize)
    
    #Unsubdivide Geo
    allGeo = cmds.ls(type='mesh')
    for everyGeo in allGeo:
        if cmds.objExists(everyGeo):
            cmds.displaySmoothness(everyGeo, polygonObject=1)

    #Change position of the camera
    changeCameraPosition(65.719,116.795,117.03,-7.4,26.6,0)
    cmds.currentTime(0)
        
    #Give eyes a checker material
    applyMaterial(["left_pupil_geo", "right_pupil_geo"])
    
    #Remove Key frames from previous step
    removeKeyFirstStep = ['headCtrl', 'jawCtrl']
    removeKeyFrames(removeKeyFirstStep, "rotate")
            
    #Set Offsets and Setup Scene
    intervalBetweenKeyframesFK =  settings.get("intervalBetweenKeyframes") + 5 
    intervalBetweenKeyframes = settings.get("intervalBetweenKeyframes") 
    middleFingersCtrlOffset = 3
    ringFingersCtrlOffset = middleFingersCtrlOffset + middleFingersCtrlOffset
    pinkyFingersCtrlOffset = ringFingersCtrlOffset + middleFingersCtrlOffset
    waitBeforeArmOffset = 2
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesFK * 14)
    cmds.PlaybackForward()
       
    #Key Thumb Fingers
    keyAttributes(thumbFingersCtrl, 15, 'rotateZ', (intervalBetweenKeyframesFK * 2))
    keyAttributes(thumbFingersCtrl, -25, 'rotateZ', (intervalBetweenKeyframesFK * 3))
    keyAttributes(thumbFingersCtrl, 0, 'rotateZ', (intervalBetweenKeyframesFK * 4))
        
    #Key Index Fingers
    keyAttributes(indexFingersCtrl, 0, 'rotateZ', 0)
    keyAttributes(indexFingersCtrl, -70, 'rotateZ', intervalBetweenKeyframesFK)
    currentFrameTime = intervalBetweenKeyframesFK + intervalBetweenKeyframesFK;
    keyAttributes(indexFingersCtrl, 0, 'rotateZ', currentFrameTime)
    
    #Key Middle Fingers
    keyAttributes(middleFingersCtrl, 0, 'rotateZ', (0 + middleFingersCtrlOffset))
    keyAttributes(middleFingersCtrl, -70, 'rotateZ', (intervalBetweenKeyframesFK + middleFingersCtrlOffset))
    currentFrameTime = intervalBetweenKeyframesFK + intervalBetweenKeyframesFK;
    keyAttributes(middleFingersCtrl, 0, 'rotateZ', (currentFrameTime + middleFingersCtrlOffset))
    
    #Key Ring Fingers
    keyAttributes(ringFingersCtrl, 0, 'rotateZ', (0 + ringFingersCtrlOffset))
    keyAttributes(ringFingersCtrl, -70, 'rotateZ', (intervalBetweenKeyframesFK + ringFingersCtrlOffset))
    currentFrameTime = intervalBetweenKeyframesFK + intervalBetweenKeyframesFK;
    keyAttributes(ringFingersCtrl, 0, 'rotateZ', (currentFrameTime + ringFingersCtrlOffset))
    
    #Key Pinky Fingers
    keyAttributes(pinkyFingersCtrl, 0, 'rotateZ', (0 + pinkyFingersCtrlOffset))
    keyAttributes(pinkyFingersCtrl, -70, 'rotateZ', (intervalBetweenKeyframesFK + pinkyFingersCtrlOffset))
    currentFrameTime = intervalBetweenKeyframesFK + intervalBetweenKeyframesFK;
    keyAttributes(pinkyFingersCtrl, 0, 'rotateZ', (currentFrameTime + pinkyFingersCtrlOffset))
    
    #Key Shoulder and Elbow Joints
    keyArms('left_shoulderCtrl','left_elbowCtrl',intervalBetweenKeyframesFK)
    keyArms('right_shoulderCtrl','right_elbowCtrl',intervalBetweenKeyframesFK)

    keySpine(spineListCtrl,intervalBetweenKeyframesFK)
    
    #Head Ctrls
    # If head exists, add animation to it
    if cmds.objExists('headCtrl'):
        cmds.select('headCtrl')
        headCtrl = cmds.ls(selection=True)[0]
        # Move Front and Back
        cmds.setKeyframe( headCtrl, v=0, at='rotateZ', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=30, at='rotateZ', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=0, at='rotateZ', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=-30, at='rotateZ', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=0, at='rotateZ', t=currentFrameTime )
        # Move to Left and Right
        cmds.setKeyframe( headCtrl, v=0, at='rotateY', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=30, at='rotateY', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=0, at='rotateY', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=-30, at='rotateY', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=0, at='rotateY', t=currentFrameTime )
        # Move to Left and Right
        cmds.setKeyframe( headCtrl, v=0, at='rotateX', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=30, at='rotateX', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=0, at='rotateX', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=-30, at='rotateX', t=currentFrameTime )
        currentFrameTime += intervalBetweenKeyframes
        cmds.setKeyframe( headCtrl, v=0, at='rotateX', t=currentFrameTime )
    else:
        print("Missing headCtrl!")
    
    # if Jaw exists add animation to it
    if cmds.objExists('jawCtrl'):
        cmds.select('jawCtrl')
        jawCtrl = cmds.ls(selection=True)[0]
        # Move Front and Back
        cmds.setKeyframe( jawCtrl, v=0, at='rotateZ', t=0 )
        cmds.setKeyframe( jawCtrl, v=30, at='rotateZ', t=(intervalBetweenKeyframes* 1.5) )
        cmds.setKeyframe( jawCtrl, v=0, at='rotateZ', t=(intervalBetweenKeyframes* 3) )
    else:
        print("Missing jawCtrl!")
       
    if cmds.objExists('main_eyeCtrl'):
        cmds.setAttr("main_eyeCtrl.visibility", lock=0)
        cmds.setAttr("main_eyeCtrl.visibility", 0)
    
    
    #Bonus Psychedelic Camera ---------------------------------------
    if settings.get("psychedelicCamera") is True:
        group = cmds.group( em=True, name='PsychedelicRig' )
        cmds.parent('persp',group)
        keyAllAttributes(group, 0, 54.639,53.817,6.859,34.6,79.4,0)
        changeCameraPosition(0,0,0,0,0,0)
        keyAllAttributes('persp', 0, 0,0,0,0,0,0)
        keyAllAttributes('persp', (intervalBetweenKeyframesFK * 10 + middleFingersCtrlOffset), 0,0,0,0,0,0)
        keyAllAttributes('persp', (intervalBetweenKeyframesFK * 10 + middleFingersCtrlOffset + 1), -250,23,-51,-88,-60,80)
            
        if cmds.objExists('left_middle2Ctrl'):
            makeObjectPsychedelic(group,'left_middle2Ctrl',0,(intervalBetweenKeyframesFK * 5 + middleFingersCtrlOffset), False)
            
        if cmds.objExists('left_elbowCtrl'):
            makeObjectPsychedelic(group,'left_elbowCtrl',(intervalBetweenKeyframesFK * 5 + middleFingersCtrlOffset),(intervalBetweenKeyframesFK * 10), True)
            
        if cmds.objExists('spine2Ctrl'):
            makeObjectPsychedelic(group,'spine2Ctrl',(intervalBetweenKeyframesFK * 10),(intervalBetweenKeyframesFK * 14), True)
        

    
    #No Selection
    cmds.select(clear=True)
    
    #Build UI ======================================================= Forward Kinematics Check
    if cmds.window("stepFK", exists =True):
        cmds.deleteUI("stepFK")
    stepFK = cmds.window("stepFK", t = "Step 1 - FK Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade for the FK system (Max 25)")
    cmds.separator(h=15)
    stepFKGradeSlider = cmds.intSliderGrp(l = "FK System Grade",min =0,max =25, field =True, value=25)
    cmds.separator(h=20)
    cmds.button(l ="Default Camera", c="changeCameraPosition(65.719,116.795,117.03,-7.4,26.6,0)")
    cmds.button(l ="Arm Camera", c="changeCameraPosition(66.252,123.98,34.871,-24.8,65.8,0)")
    cmds.button(l ="Front Camera", c="changeCameraPosition(7.664,112.688,126.455,-7.4,3.4,0)")
    cmds.separator(h=20)

    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:controlRigCheckIK(organizationGrade, deductionGrade, \
                cmds.intSliderGrp(stepFKGradeSlider, q= True,value =True)))
    cmds.showWindow(stepFK)


# Inverse Kinematics Check
def controlRigCheckIK(organizationGrade, deductionGrade, fkGrade):
    
    #Deletes previous dialog
    if cmds.window("stepFK", exists =True):
        cmds.deleteUI("stepFK")

    #Change position of the camera
    changeCameraPosition(64.961,64.3,111.476,-10.4,30.6,0)
    cmds.currentTime(0)
    
    #Define timeline length and keyframe interval
    intervalBetweenKeyframesIK = settings.get("intervalBetweenKeyframes")
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesIK * 15)
    
    #Remove Key frames from previous step
    removeKeySecondStep = ['left_shoulderCtrl', 'left_elbowCtrl','right_elbowCtrl','right_shoulderCtrl']
    removeKeyFrames(removeKeySecondStep,"rotate")
    removeKeyFrames(thumbFingersCtrl,"rotate")
    removeKeyFrames(indexFingersCtrl,"rotate")
    removeKeyFrames(middleFingersCtrl,"rotate")
    removeKeyFrames(ringFingersCtrl,"rotate")
    removeKeyFrames(pinkyFingersCtrl,"rotate")
    removeKeyFrames(spineListCtrl,"rotate")
    removeKeyFrames(['jawCtrl'],"rotate")
    
    
    #hipJoints = ['left_hipCtrl', 'right_hipCtrl']
    
    kneeCtrls = ['left_kneeCtrl','right_kneeCtrl']
    footCtrls = ['left_footCtrl', 'right_footCtrl']

    
    #First Step IK
    keyAttributes(footCtrls, 0, 'translateY', 0)
    keyAttributes(footCtrls, 30, 'translateY', intervalBetweenKeyframesIK + (intervalBetweenKeyframesIK/2))
    keyAttributes(footCtrls, 0, 'translateY', (intervalBetweenKeyframesIK* 3))
    
    keyAttributes(footCtrls, 0, 'translateZ', 0)
    keyAttributes(footCtrls, 15, 'translateZ', intervalBetweenKeyframesIK + (intervalBetweenKeyframesIK/2))
    keyAttributes(footCtrls, 0, 'translateZ', (intervalBetweenKeyframesIK* 3))
    
    keyAttributes(footCtrls, 0, 'rotateX', 0)
    keyAttributes(footCtrls, 30, 'rotateX', intervalBetweenKeyframesIK + (intervalBetweenKeyframesIK/2))
    keyAttributes(footCtrls, 0, 'rotateX', (intervalBetweenKeyframesIK* 3))

    #Second Step IK
    keyAttributes(footCtrls, 0, 'translateY', (intervalBetweenKeyframesIK* 3))
    keyAttributes(footCtrls, 15, 'translateY', (intervalBetweenKeyframesIK* 4))
    keyAttributes(footCtrls, 0, 'translateY', (intervalBetweenKeyframesIK* 5))
    
    keyAttributes(footCtrls, 0, 'translateX', (intervalBetweenKeyframesIK* 3))
    keyAttributes(footCtrls, 40, 'translateX', (intervalBetweenKeyframesIK* 4))
    keyAttributes(footCtrls, 0, 'translateX', (intervalBetweenKeyframesIK* 5))
    
    #Third Step IK
    keyAttributes(footCtrls, 0, 'heelRoll', (intervalBetweenKeyframesIK* 5))
    keyAttributes(footCtrls, 10, 'heelRoll', (intervalBetweenKeyframesIK* 6))
    keyAttributes(footCtrls, 0, 'heelRoll', (intervalBetweenKeyframesIK* 7))
    
    keyAttributes(footCtrls, 0, 'ballRoll', (intervalBetweenKeyframesIK* 7))
    keyAttributes(footCtrls, 10, 'ballRoll', (intervalBetweenKeyframesIK* 8))
    keyAttributes(footCtrls, 0, 'ballRoll', (intervalBetweenKeyframesIK* 9))
    
    keyAttributes(footCtrls, 0, 'toeRoll', (intervalBetweenKeyframesIK* 9))
    keyAttributes(footCtrls, 10, 'toeRoll', (intervalBetweenKeyframesIK* 10))
    keyAttributes(footCtrls, 0, 'toeRoll', (intervalBetweenKeyframesIK* 11))
    
    #Change if HeelRoll, BallRoll or ToeRoll
    keyAttributes(footCtrls, 0, 'HeelRoll', (intervalBetweenKeyframesIK* 5))
    keyAttributes(footCtrls, 10, 'HeelRoll', (intervalBetweenKeyframesIK* 6))
    keyAttributes(footCtrls, 0, 'HeelRoll', (intervalBetweenKeyframesIK* 7))
    
    keyAttributes(footCtrls, 0, 'BallRoll', (intervalBetweenKeyframesIK* 7))
    keyAttributes(footCtrls, 10, 'BallRoll', (intervalBetweenKeyframesIK* 8))
    keyAttributes(footCtrls, 0, 'BallRoll', (intervalBetweenKeyframesIK* 9))
    
    keyAttributes(footCtrls, 0, 'ToeRoll', (intervalBetweenKeyframesIK* 9))
    keyAttributes(footCtrls, 10, 'ToeRoll', (intervalBetweenKeyframesIK* 10))
    keyAttributes(footCtrls, 0, 'ToeRoll', (intervalBetweenKeyframesIK* 11))

    #Fourth Step IK
    keyAttributes(footCtrls, 0, 'translateY', (intervalBetweenKeyframesIK* 11))
    keyAttributes(footCtrls, 10, 'translateY', (intervalBetweenKeyframesIK* 12))
    keyAttributes(footCtrls, 10, 'translateY', (intervalBetweenKeyframesIK* 13))
    keyAttributes(footCtrls, 0, 'translateY', (intervalBetweenKeyframesIK* 14))
    
    keyAttributes(kneeCtrls, 0, 'translateX', (intervalBetweenKeyframesIK* 11))
    keyAttributes(kneeCtrls, 40, 'translateX', (intervalBetweenKeyframesIK* 12))
    keyAttributes(kneeCtrls, 0, 'translateX', (intervalBetweenKeyframesIK* 13))
    
    keyAttributes(kneeCtrls, 0, 'translateX', (intervalBetweenKeyframesIK* 13))
    keyAttributes(kneeCtrls, -40, 'translateX', (intervalBetweenKeyframesIK* 14))
    keyAttributes(kneeCtrls, 0, 'translateX', (intervalBetweenKeyframesIK* 15))
    
    #No Selection
    cmds.select(clear=True)
    
    #Bonus Psychedelic Camera ---------------------------------------
    if settings.get("psychedelicCamera") is True:
        removeKeyFrames(['PsychedelicRig'],"translate")
        keyAllAttributes("PsychedelicRig", 0, 24.655,58.166,21.606,-51.8,47,0)
        changeCameraPosition(0,0,0,0,0,0)
        removeKeyFrames(['persp'],"translate")
            
        if cmds.objExists('left_kneeJnt'):
            makeObjectPsychedelic('PsychedelicRig','left_kneeJnt',0,(intervalBetweenKeyframesIK * 15), False)
            
   
    #Build UI ======================================================= Inverse Kinematics Check
    if cmds.window("stepIK", exists =True):
        cmds.deleteUI("stepIK")
    stepIK = cmds.window("stepIK", t = "Step 2 - IK Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("FK Grade: " + str(fkGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + fkGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade IK system (Max 25)")
    cmds.separator(h=15)
    stepIKGradeSlider = cmds.intSliderGrp(l = "IK System Grade",min =0,max =25, field =True, value=25)
    cmds.separator(h=20)
    cmds.button(l ="Front Camera", c="changeCameraPosition(64.961,64.3,111.476,-10.4,30.6,0)")
    cmds.button(l ="Back Camera", c="changeCameraPosition(119.966,93.182,-127.111,-12.8,132.6,0)")
    cmds.separator(h=20)
    
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:controlRigCheckMainEyes(organizationGrade, deductionGrade, fkGrade, \
                cmds.intSliderGrp(stepIKGradeSlider, q= True,value =True)))
    cmds.showWindow(stepIK)
    
#Main and Eyes Check
def controlRigCheckMainEyes(organizationGrade, deductionGrade, fkGrade, ikGrade):
    
    #Delete previous dialog
    if cmds.window("stepIK", exists =True):
        cmds.deleteUI("stepIK")

    #Bring back eyes
    if cmds.objExists('main_eyeCtrl'):
        cmds.setAttr("main_eyeCtrl.visibility", lock=0)
        cmds.setAttr("main_eyeCtrl.visibility", 1)

    #Change position of the camera for lower body inspection
    changeCameraPosition(0,100,270,-5,0,0)
    cmds.currentTime(0)
    
    #Define timeline length and keyframe interval
    intervalBetweenKeyframesMainEyes = settings.get("intervalBetweenKeyframes")
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesMainEyes * 16)
    
    #Remove Previous Keyframes
    kneeCtrls = ['left_kneeCtrl','right_kneeCtrl']
    footCtrls = ['left_footCtrl', 'right_footCtrl']
    headCtrls = ['jawCtrl','headCtrl']
    eyeCtrls = ['left_eyeCtrl','right_eyeCtrl']
    
    removeKeyFrames(kneeCtrls, "translate")
    removeKeyFrames(footCtrls, "rotate")
    removeKeyFrames(footCtrls, "translate")
    removeKeyFrames(headCtrls, "rotate")
    removeKeyFramesNonVector(kneeCtrls, "translateX")
    removeKeyFramesNonVector(footCtrls, "translateX")
    removeKeyFramesNonVector(footCtrls, "translateY")
    removeKeyFramesNonVector(footCtrls, "translateZ")
    removeKeyFramesNonVector(eyeCtrls, "translateX")
    
    keyAttributes(["mainCtrl"], 0, 'translateX', 0)
    keyAttributes(["mainCtrl"], 65, 'translateX', (intervalBetweenKeyframesMainEyes * 1))
    keyAttributes(["mainCtrl"], -65, 'translateX', (intervalBetweenKeyframesMainEyes * 3))
    keyAttributes(["mainCtrl"], 0, 'translateX', (intervalBetweenKeyframesMainEyes * 4))
    
    keyAttributes(["directionCtrl"], 0, 'translateX', (intervalBetweenKeyframesMainEyes * 4))
    keyAttributes(["directionCtrl"], 65, 'translateX', (intervalBetweenKeyframesMainEyes * 5))
    keyAttributes(["directionCtrl"], -65, 'translateX', (intervalBetweenKeyframesMainEyes * 7))
    keyAttributes(["directionCtrl"], 0, 'translateX', (intervalBetweenKeyframesMainEyes * 8))
    
    keyAttributes(["main_eyeCtrl"], 0, 'translateZ', (intervalBetweenKeyframesMainEyes * 8))
    keyAttributes(["main_eyeCtrl"], 35, 'translateZ', (intervalBetweenKeyframesMainEyes * 9))
    keyAttributes(["main_eyeCtrl"], -35, 'translateZ', (intervalBetweenKeyframesMainEyes * 11))
    keyAttributes(["main_eyeCtrl"], 0, 'translateZ', (intervalBetweenKeyframesMainEyes * 12))
    keyAttributes(["main_eyeCtrl"], 0, 'translateX', (intervalBetweenKeyframesMainEyes * 8))
    keyAttributes(["main_eyeCtrl"], 35, 'translateX', (intervalBetweenKeyframesMainEyes * 9))
    keyAttributes(["main_eyeCtrl"], -35, 'translateX', (intervalBetweenKeyframesMainEyes * 11))
    keyAttributes(["main_eyeCtrl"], 0, 'translateX', (intervalBetweenKeyframesMainEyes * 12))
    
    keyAttributes(eyeCtrls, 0, 'translateZ', (intervalBetweenKeyframesMainEyes * 12))
    keyAttributes(eyeCtrls, 35, 'translateZ', (intervalBetweenKeyframesMainEyes * 13))
    keyAttributes(eyeCtrls, -35, 'translateZ', (intervalBetweenKeyframesMainEyes * 15))
    keyAttributes(eyeCtrls, 0, 'translateZ', (intervalBetweenKeyframesMainEyes * 16))
    keyAttributes(eyeCtrls, 0, 'translateX', (intervalBetweenKeyframesMainEyes * 12))
    keyAttributes(eyeCtrls, 35, 'translateX', (intervalBetweenKeyframesMainEyes * 13))
    keyAttributes(eyeCtrls, -35, 'translateX', (intervalBetweenKeyframesMainEyes * 15))
    keyAttributes(eyeCtrls, 0, 'translateX', (intervalBetweenKeyframesMainEyes * 16))
    
    #No Selection
    cmds.select(clear=True)
    
    #Bonus Psychedelic Camera ---------------------------------------
    if settings.get("psychedelicCamera") is True:
        removeKeyFrames(['PsychedelicRig'],"translate")
        keyAllAttributes("PsychedelicRig", 0, 0,0,0,0,0,0)
        
        removeKeyFrames(['persp'],"rotate")
        changeCameraPosition(0,100,270,-5,0,0)
        
        keyAllAttributes("persp", (intervalBetweenKeyframesMainEyes * 8), 0,100,270,-5,0,0)
        keyAllAttributes("persp", (intervalBetweenKeyframesMainEyes * 8 + 1), 0,130,100,-5,0,0)
        keyAllAttributes("persp", (intervalBetweenKeyframesMainEyes * 16), 0,130,160,-5,0,0)
    
   
   
    #Build UI ======================================================= Main & Eyes Check
    if cmds.window("stepMainEyes", exists =True):
        cmds.deleteUI("stepMainEyes")
    stepMainEyes = cmds.window("stepMainEyes", t = "Step 3 - Main & Eyes", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("FK Grade: " + str(fkGrade))
    cmds.text("IK Grade: " + str(ikGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + fkGrade + ikGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade for the Main & Eye Ctrls (Max 20)")
    cmds.separator(h=15)
    stepMainEyesGradeSlider = cmds.intSliderGrp(l = "Main & Eyes Grade",min =0,max =20, field =True, value=20)
    cmds.separator(h=20)
    
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:controlRigCheckCustomAttributes(organizationGrade, deductionGrade, fkGrade, \
                ikGrade, cmds.intSliderGrp(stepMainEyesGradeSlider, q= True,value =True)))
    cmds.showWindow(stepMainEyes)

#Custom Attributes Check
def controlRigCheckCustomAttributes(organizationGrade, deductionGrade, fkGrade, ikGrade, mainEyeGrade):
    
    #Delete previous dialog
    if cmds.window("stepMainEyes", exists =True):
        cmds.deleteUI("stepMainEyes")

    #Change position of the camera for body inspection
    changeCameraPosition(0,100,270,-5,0,0)
    cmds.currentTime(0)

    #Define timeline length and keyframe interval
    intervalBetweenKeyframesCA = settings.get("intervalBetweenKeyframes")
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesCA * 6)

    wristCtrls = ['left_wristCtrl', 'right_wristCtrl']
    eyeCtrls = ['left_eyeCtrl','right_eyeCtrl','main_eyeCtrl']
    mainCtrls = ['mainCtrl','directionCtrl','main_eyeCtrl']
    
    #Unlocks attributes in case they were locked
    unlockLocked(mainCtrls,"translateX")
    unlockLocked(mainCtrls,"translateY")
    unlockLocked(mainCtrls,"translateZ")
    unlockLocked(wristCtrls,"translateX")
    unlockLocked(wristCtrls,"translateY")
    unlockLocked(wristCtrls,"translateZ")
    
    #Remove Previous Keyframes
    removeKeyFrames(eyeCtrls, "translate")
    removeKeyFrames(mainCtrls, "translate")
    removeKeyFramesNonVector(mainCtrls, "translateX")
    removeKeyFrames(wristCtrls, "translate")

    #Check if bulletproof by scaling it
    shouldBeBulletproof = ['spine1Ctrl','spine3Ctrl','left_elbowCtrl','right_elbowCtrl','directionCtrl']
    keyAttributesIfNotLocked(shouldBeBulletproof, 1, 'scaleX', 0,'.scaleX')
    keyAttributesIfNotLocked(shouldBeBulletproof, 1.5, 'scaleX', intervalBetweenKeyframesCA,'.scaleX')
    keyAttributesIfNotLocked(shouldBeBulletproof, 1, 'scaleX', (intervalBetweenKeyframesCA * 2),'.scaleX')

    keyAttributesIfNotLocked(shouldBeBulletproof, 1, 'scaleX', 0,'.scaleX')
    keyAttributesIfNotLocked(shouldBeBulletproof, 1.5, 'scaleX', intervalBetweenKeyframesCA,'.scaleX')
    keyAttributesIfNotLocked(shouldBeBulletproof, 1, 'scaleX', (intervalBetweenKeyframesCA * 2),'.scaleX')
    
    keyAttributesIfNotLocked(eyeCtrls, 0, 'translateZ', 0,'.rotateX')
    keyAttributesIfNotLocked(eyeCtrls, 120, 'translateZ', intervalBetweenKeyframesCA,'.rotateX')
    keyAttributesIfNotLocked(eyeCtrls, 0, 'translateZ', (intervalBetweenKeyframesCA * 2),'.rotateX')

    #Define possible naming variations
    fistVariations = ['fist','Fist']
    smileVariations = ['smile','Smile']
    splayVariations = ['splay','Splay']
    sadVariations = ['sad', 'Sad']
    
    for each in fistVariations:
        keyAttributes(wristCtrls, 0, each, 0)
        keyAttributes(wristCtrls, 10, each, intervalBetweenKeyframesCA)
        keyAttributes(wristCtrls, 0, each, (intervalBetweenKeyframesCA* 2))
    
    for each in sadVariations:
        keyAttributes(['headCtrl'], 0, each, 0)
        keyAttributes(['headCtrl'], 10, each, intervalBetweenKeyframesCA)
        keyAttributes(['headCtrl'], 0, each, (intervalBetweenKeyframesCA* 2))
    
    for each in fistVariations:
        keyAttributes(wristCtrls, 0, each, (intervalBetweenKeyframesCA* 4))
        keyAttributes(wristCtrls, 10, each, (intervalBetweenKeyframesCA* 5))
        keyAttributes(wristCtrls, 0, each, (intervalBetweenKeyframesCA* 6))
    
    for each in sadVariations:
        keyAttributes(['headCtrl'], 0, each, (intervalBetweenKeyframesCA* 4))
        keyAttributes(['headCtrl'], 10, each, (intervalBetweenKeyframesCA* 5))
        keyAttributes(['headCtrl'], 0, each, (intervalBetweenKeyframesCA* 6))
    
    for each in splayVariations:
        keyAttributes(wristCtrls, 0, each, (intervalBetweenKeyframesCA* 2))
        keyAttributes(wristCtrls, 10, each, (intervalBetweenKeyframesCA* 3))
        keyAttributes(wristCtrls, 0, each, (intervalBetweenKeyframesCA* 4))

    for each in smileVariations:
        keyAttributes(['headCtrl'], 0, each, (intervalBetweenKeyframesCA* 2))
        keyAttributes(['headCtrl'], 10, each, (intervalBetweenKeyframesCA* 3))
        keyAttributes(['headCtrl'], 0, each, (intervalBetweenKeyframesCA* 4))
    
    #No Selection
    cmds.select(clear=True)
    
    #Bonus Psychedelic Camera ---------------------------------------
    if settings.get("psychedelicCamera") is True:
        removeKeyFrames(['PsychedelicRig'],"translate")
        keyAllAttributes("PsychedelicRig", 0, 53.908,54.279,16.23,31.2,59.4,0)
        
        
        removeKeyFrames(['persp'],"rotate")
        keyAllAttributes("persp", 0, -271.865,10.268,-54.399,3689,-121,-93.393)
        keyAllAttributes("persp", (intervalBetweenKeyframesCA * 2), -271.865,10.268,-54.399,3689,-121,-93.393)
        keyAllAttributes("persp", (intervalBetweenKeyframesCA * 2 + 1), -63.896,37.407,-83.759,3688.17,-106.679,-93.393)
        keyAllAttributes("persp", (intervalBetweenKeyframesCA * 4), -63.896,37.407,-83.759,3688.17,-106.679,-93.393)
        keyAllAttributes("persp", (intervalBetweenKeyframesCA * 4 + 1), 0,0,0,0,0,0)
        
        if cmds.objExists('left_middle1Ctrl'):
            makeObjectPsychedelic('PsychedelicRig','left_middle1Ctrl',(intervalBetweenKeyframesCA * 4),(intervalBetweenKeyframesCA * 6), False)
   
   
    #Build UI ======================================================= Custom Attributes Check
    if cmds.window("StepCA", exists =True):
        cmds.deleteUI("StepCA")
    StepCA = cmds.window("StepCA", t = "Step 4 - Custom Attribute Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("FK Grade: " + str(fkGrade))
    cmds.text("IK Grade: " + str(ikGrade))
    cmds.text("Main & Eyes Grade: " + str(mainEyeGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + fkGrade + ikGrade + mainEyeGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade for custom attributes (Max 10)")
    cmds.separator(h=15)
    StepCAGradeSlider = cmds.intSliderGrp(l = "Custom Attributes Grade",min =0,max =10, field =True, value=10)
    cmds.separator(h=20)
    
    cmds.button(l ="Default Camera", c="changeCameraPosition(0,100,270,-5,0,0)")
    cmds.button(l ="Head Camera", c="changeCameraPosition(23.044,125.273,48.172,4,26.8,0)")
    cmds.button(l ="Hand Camera", c="changeCameraPosition(48.168,69.608,25.955,-9.2,26.8,0)")
    cmds.separator(h=15)
    
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:controlRigCheckIfScalable(organizationGrade, deductionGrade, fkGrade, \
                ikGrade, mainEyeGrade, cmds.intSliderGrp(StepCAGradeSlider, q= True,value =True)))
    cmds.showWindow(StepCA)

#Scalable Rig check
def controlRigCheckIfScalable(organizationGrade, deductionGrade, fkGrade, ikGrade, mainEyeGrade, customAttrGrade):
    #Close third dialog
    if cmds.window("StepCA", exists =True):
        cmds.deleteUI("StepCA")

    #Change position of the camera for body inspection
    changeCameraPosition(0,100,270,-5,0,0)
    cmds.currentTime(0)
    
    #Define timeline length and keyframe interval
    intervalBetweenKeyframesScale = settings.get("intervalBetweenKeyframes")
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesScale * 6)
    
    #Remove Previous Keyframes
    eyeCtrls = ['left_eyeCtrl','right_eyeCtrl','main_eyeCtrl']
    mainCtrls = ['mainCtrl','directionCtrl','main_eyeCtrl']
    shouldBeBulletproof = ['spine1Ctrl','spine3Ctrl','left_elbowCtrl','right_elbowCtrl','directionCtrl']

    #Unlocks attributes in case necessary
    unlockLocked(shouldBeBulletproof,"translateX")
    unlockLocked(shouldBeBulletproof,"translateY")
    unlockLocked(shouldBeBulletproof,"translateZ")
    unlockLocked(['headCtrl'],"translateX")
    unlockLocked(['headCtrl'],"translateY")
    unlockLocked(['headCtrl'],"translateZ")

    #Remove previous keyframes
    wristCtrls = ['left_wristCtrl', 'right_wristCtrl' ]
    removeKeyFrames(shouldBeBulletproof, "translate")
    removeKeyFrames(wristCtrls, "translate")
    removeKeyFrames(eyeCtrls, "translate")
    removeKeyFrames(mainCtrls, "translate")
    removeKeyFrames(['headCtrl'], "translate")
    removeKeyFrames(['main_eyeCtrl'], "translate")
    removeKeyFramesNonVector(shouldBeBulletproof, "scaleX")
    
    #Make eye controls invisible
    if cmds.objExists('main_eyeCtrl'):
        cmds.setAttr("main_eyeCtrl.visibility", lock=0)
        cmds.setAttr("main_eyeCtrl.visibility", 0)
    
    #Scale mainCtrl
    keyAttributesIfNotLocked(['mainCtrl'], 1, 'scaleX', 0,'.scaleX')
    keyAttributesIfNotLocked(['mainCtrl'], 0.2, 'scaleX', (intervalBetweenKeyframesScale * 2),'.scaleX')
    keyAttributesIfNotLocked(['mainCtrl'], 2, 'scaleX', (intervalBetweenKeyframesScale * 4),'.scaleX')
    keyAttributesIfNotLocked(['mainCtrl'], 1, 'scaleX', (intervalBetweenKeyframesScale * 6),'.scaleX')
    
    keyAttributesIfNotLocked(['mainCtrl'], 1, 'scaleY', 0,'.scaleY')
    keyAttributesIfNotLocked(['mainCtrl'], 0.2, 'scaleY', (intervalBetweenKeyframesScale * 2),'.scaleY')
    keyAttributesIfNotLocked(['mainCtrl'], 2, 'scaleY', (intervalBetweenKeyframesScale * 4),'.scaleY')
    keyAttributesIfNotLocked(['mainCtrl'], 1, 'scaleY', (intervalBetweenKeyframesScale * 6),'.scaleY')
    
    keyAttributesIfNotLocked(['mainCtrl'], 1, 'scaleZ', 0,'.scaleZ')
    keyAttributesIfNotLocked(['mainCtrl'], 0.2, 'scaleZ', (intervalBetweenKeyframesScale * 2),'.scaleZ')
    keyAttributesIfNotLocked(['mainCtrl'], 2, 'scaleZ', (intervalBetweenKeyframesScale * 4),'.scaleZ')
    keyAttributesIfNotLocked(['mainCtrl'], 1, 'scaleZ', (intervalBetweenKeyframesScale * 6),'.scaleZ')

    #No Selection
    cmds.select(clear=True)
    
    #Bonus Psychedelic Camera ---------------------------------------
    if settings.get("psychedelicCamera") is True:
        removeKeyFrames(['PsychedelicRig'],"translate")
        keyAllAttributes("PsychedelicRig", 0, 0,0,0,0,0,0)
        
        removeKeyFrames(['persp'],"rotate")
        changeCameraPosition(0,100,270,-5,0,0)
        
        try:
            panelList = cmds.getPanel(type="modelPanel")
    
            for eachPanel in panelList:
                cmds.modelEditor(eachPanel, e=1, grid=1)
        except:
            cmds.warning("Something went wrong, script couldn't find the viewport")
        
        if cmds.objExists('PsychedelicRig_parentConstraint1'):
            cmds.delete('PsychedelicRig_parentConstraint1')
        
        if cmds.objExists('mainCtrl'):
            cmds.scaleConstraint( 'mainCtrl', "PsychedelicRig" )
        
   
    #Build UI ======================================================= Scale Check
    if cmds.window("stepScale", exists =True):
        cmds.deleteUI("stepScale")
    stepScale = cmds.window("stepScale", t = "Step 5 - Is Scalable Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("FK Grade: " + str(fkGrade))
    cmds.text("IK Grade: " + str(ikGrade))
    cmds.text("Main & Eye Grade: " + str(mainEyeGrade))
    cmds.text("Custom Attributes Grade: " + str(customAttrGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + fkGrade + ikGrade + mainEyeGrade + customAttrGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade for being scalable (Max 10)")
    cmds.separator(h=15)
    stepScaleGradeSlider = cmds.intSliderGrp(l = "Is Scalable Grade",min =0,max =10, field =True, value=10)
    cmds.separator(h=20)
    
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:controlRigCheckResult(organizationGrade, deductionGrade, fkGrade, \
                ikGrade, mainEyeGrade, customAttrGrade,  cmds.intSliderGrp(stepScaleGradeSlider, q= True,value =True)))
    cmds.showWindow(stepScale)


#Control Rig Result Dialog
def controlRigCheckResult(organizationGrade, deductionGrade, fkGrade, ikGrade, mainEyeGrade, customAttrGrade, isScalableGrade):
    
    #Delete previous dialog
    if cmds.window("stepScale", exists =True):
        cmds.deleteUI("stepScale")

    #Change position of the camera
    changeCameraPosition(0,100,270,-5,0,0)
    
    #No Selection
    cmds.select(clear=True)
    
    #Bonus Psychedelic Camera ---------------------------------------
    if settings.get("psychedelicCamera") is True:
        removeKeyFrames(['PsychedelicRig'],"translate")
        keyAllAttributes("PsychedelicRig", 0, 0,0,0,0,0,0)
        
        removeKeyFrames(['persp'],"rotate")
        changeCameraPosition(0,100,270,-5,0,0)
        
        if cmds.objExists('PsychedelicRig_scaleConstraint1'):
            cmds.delete('PsychedelicRig_scaleConstraint1')
        
        if cmds.objExists('persp'):
            cmds.parent('persp', w=True, r=True)
            
        if cmds.objExists('PsychedelicRig'):
            cmds.delete('PsychedelicRig')
            
        try:
            panelList = cmds.getPanel(type="modelPanel")
    
            for eachPanel in panelList:
                cmds.modelEditor(eachPanel, e=1, grid=0)
        except:
            cmds.warning("Something went wrong, script couldn't find the viewport")
        

    
    #Build UI ======================================================= Result
    if cmds.window("stepResult", exists =True):
        cmds.deleteUI("stepResult")
    
    #Result Setup
    cmds.currentTime(0)
    cmds.PlaybackStop()    
    
    stepResult = cmds.window("stepResult", t = "Result - Control Rig Grade", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("FK Grade: " + str(fkGrade))
    cmds.text("IK Grade: " + str(ikGrade))
    cmds.text("Main and Eye Grade: " + str(mainEyeGrade))
    cmds.text("Custom Attributes Grade: " + str(customAttrGrade))
    cmds.text("Scalable Rig Grade: " + str(isScalableGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + fkGrade + ikGrade + mainEyeGrade + customAttrGrade + isScalableGrade - deductionGrade), hyperlink = True)
    cmds.separator(h=15)
    cmds.button(l ="Restart Script (New Scene)", w=280, h=40, bgc = (.5, 0, 0), c=lambda x:controlRigCheckRestartScript())
    cmds.showWindow(stepResult)

#Delete previous dialog and Restart scene
def controlRigCheckRestartScript():
    if cmds.window("stepResult", exists =True):
        cmds.deleteUI("stepResult")
    cmds.file( f=True, new=True )
    
    #Show open dialog or not
    if settings.get("showOpenDialog") is True:
        multipleFilters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);;All Files (*.*)"
        filePath = cmds.fileDialog2(fileFilter=multipleFilters, dialogStyle=2, fm=1)
        if filePath is not None:
            cmds.file(filePath, open=True)
    controlRigCheckMainDialog()

#Start current "Main"
controlRigCheckMainDialog()