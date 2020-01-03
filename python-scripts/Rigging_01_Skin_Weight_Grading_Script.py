import maya.cmds as cmds

# Skin Weight Grading Script
# Script created for Rigging 1 (Term 2, Vancouver Film School)
# @Guilherme Trevisan - 2019-12-09
# Last update - 2019-12-18
# Version:
scriptVersion = "v1.0"
currentModel = "Betty"

#Define Initial Setup
defaultJointSize = 1
unparentList = ['rootJnt','geo_grp']
deleteList = ['controls','Controls', 'control_grp','Control_grp','controls_grp','Controls_grp','DO_NOT_TOUCH', \
               'proxy_geo_grp','proxy_geo','skeleton','Skeleton','skeleton_grp','Skeleton_grp''Betty']
wireSystemElements = ['left_upper_eyelashBaseWire','left_lower_eyelashBaseWire','left_eyebrow_BaseWire', \
                      'right_upper_eyelashBaseWire','right_eyebrow_BaseWire','right_lower_eyelashBaseWire',]
eyeGeoElements = ['left_brow_geo','left_upperLash_geo','left_lowerLash_geo', \
                      'right_lowerLash_geo','right_upperLash_geo','right_brow_geo',]
thumbFingers = ['left_thumb1Jnt', 'left_thumb2Jnt', 'left_thumb3Jnt', 'left_thumbEndJnt', \
                'right_thumb1Jnt', 'right_thumb2Jnt', 'right_thumb3Jnt', 'right_thumbEndJnt']
                    
indexFingers = ['left_index1Jnt', 'left_index2Jnt', 'left_index3Jnt', 'left_indexEndJnt', \
                'right_index1Jnt', 'right_index2Jnt', 'right_index3Jnt', 'right_indexEndJnt']
                    
middleFingers = ['left_middle1Jnt', 'left_middle2Jnt', 'left_middle3Jnt', 'left_middleEndJnt', \
                'right_middle1Jnt', 'right_middle2Jnt', 'right_middle3Jnt', 'right_middleEndJnt']
                    
ringFingers = ['left_ring1Jnt', 'left_ring2Jnt', 'left_ring3Jnt', 'left_ringEndJnt', \
                'right_ring1Jnt', 'right_ring2Jnt', 'right_ring3Jnt', 'right_ringEndJnt']
                    
pinkyFingers = ['left_pinky1Jnt', 'left_pinky2Jnt', 'left_pinky3Jnt', 'left_pinkyEndJnt', \
                'right_pinky1Jnt', 'right_pinky2Jnt', 'right_pinky3Jnt', 'right_pinkyEndJnt']
spineList = ['spine1Jnt', 'spine2Jnt', 'spine3Jnt',]

# Settings Dictionary
settingsDefault = { 'intervalBetweenKeyframes': 10, 
             'showSkeleton': False,
             'resetViewport': True,
             'showOpenDialog': False,
             'deleteUnnecessary': True
            }
settings = { 'intervalBetweenKeyframes': 10, 
             'showSkeleton': False,
             'resetViewport': True,
             'showOpenDialog': False,
             'deleteUnnecessary': True
            }

# Clean Up - If obj exists, it gets deleted
def bruteforceCleanUpScene(deleteList):
    
    for trash in deleteList:
        #print(trash) # debugging
        if cmds.objExists(trash):
            cmds.select(trash)
            deletionContainer = cmds.ls(selection=True)[0]
            cmds.delete(deletionContainer)
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

# Parents a list of objects to the world (unparents them from other objects)
def parentToWorld(parentedList):
    if  len(parentedList) > 0: #Check if list is empty
        for currentObj in parentedList:
            if cmds.objExists(currentObj):
                targetObj = cmds.select(currentObj)
                try:
                    cmds.parent(world = True)

                except Exception:
                    cmds.warning("Unexpected result!")

# Updates joints radius if it's not locked
def updateRadiusIfNotLocked(objList, value):
    for objId in objList:
        if cmds.objExists(objId):
            if cmds.getAttr(objId + ".radius" ,lock=True) is False:
                cmds.select(objId)
                myObj = cmds.ls(selection=True)[0]
                cmds.setAttr(objId + '.radius', value)

# Reset all modelPanels (Viewport)
def resetViewport(showSkeleton):
    try:
        panelList = cmds.getPanel(type="modelPanel")
    
        for eachPanel in panelList:
            print(eachPanel)
            cmds.modelEditor(eachPanel, e=1, allObjects=0)
            cmds.modelEditor(eachPanel, e=1, polymeshes=1)
            cmds.modelEditor(eachPanel, e=1, joints=1)
            cmds.modelEditor(eachPanel, e=1, jx=1)
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

# Removes key frames and resets rotation
def removeKeyFrames(objList):
    for objId in objList:
        if cmds.objExists(objId):
            cmds.select(objId)
            myObj = cmds.ls(selection=True)[0]
            cmds.cutKey(myObj, time = (0, 1000), clear = True)
            cmds.setAttr(myObj + ".rotate", 0,0,0)
                    
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

# Keys rotation of entire list        
def keyAttributes(objList, value, attribute, atFrame):
    for objId in objList:
        if cmds.objExists(objId):
            cmds.select(objId)
            myObj = cmds.ls(selection=True)[0]
            cmds.setKeyframe(myObj, v=value, at=attribute, t=atFrame )

# Change position of the camera and then look through it
def changeCameraPosition(translateX,translateY,translateZ,rotateX,rotateY,rotateZ):
    if cmds.objExists('persp'):
        cmds.select('persp')
        cam = cmds.ls(selection=True)[0]
        cmds.setAttr( cam + '.translate', translateX,translateY,translateZ)
        cmds.setAttr( cam + '.rotate', rotateX,rotateY,rotateZ)
        cmds.lookThru(cam)
    else:
        print('UNEXPECTED ERROR! "persp" camera not found!!!!!!!!')
  
# Keys Arms Joints
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

# Key Spine Joints
def keySpine(spineList,intervalBetweenKeyframes):    
    for spine in spineList:
        if cmds.objExists(spine):
            cmds.select(spine)
            spine = cmds.ls(selection=True)[0]
            cmds.setKeyframe(spine, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 10))
            cmds.setKeyframe(spine, v=30, at='rotateZ', t=(intervalBetweenKeyframes * 11 ))
            cmds.setKeyframe(spine, v=-30, at='rotateZ', t=(intervalBetweenKeyframes * 13 ))
            cmds.setKeyframe(spine, v=0, at='rotateZ', t=(intervalBetweenKeyframes * 14))

# Main Form ============================================================================
def skinWeightCheckMainDialog():
    if cmds.window("swMainDialog", exists =True):
        cmds.deleteUI("swMainDialog")    

    # swMainDialog Start Here =================================================================================

    crMainDialog = cmds.window("swMainDialog", title="Skin Weight Grading Script - " + scriptVersion, widthHeight=(480,250),\
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
    swOrganizationContainer = cmds.columnLayout(p=tabMain)
    swOrganization = cmds.intSliderGrp('swMainDialog', width = 350 ,p=swOrganizationContainer, l = "Organization Grade",min =0,max =10, field =True, value=10)
    swDeductionContainer = cmds.columnLayout(p=tabMain)
    swDeduction = cmds.intSliderGrp(l = "Deduction Grade",  width = 350 ,p=swDeductionContainer ,min =0,max =100, field =True, value=0)
    cmds.separator(h=10)

    #Settings Tab ======================================================
    tabSettings = cmds.rowColumnLayout(numberOfColumns=2, p=tabs)
    
    settingsContainer = cmds.columnLayout(p=tabSettings)
    cmds.text("   ", p=settingsContainer)
    cmds.text("   ", p=settingsContainer, height = 10)
    swSpeed = cmds.intSliderGrp(l = "Interval Between Keys",  width = 350 ,p=settingsContainer ,min =0,max =100, field =True, value=settings.get("intervalBetweenKeyframes"))
    cmds.text("   ", p=settingsContainer, height = 10)
    checkboxContainer = cmds.rowColumnLayout(numberOfColumns=2, adj=True)
    cmds.text("            Viewport :    ", p=checkboxContainer)

    checkboxSettingsOne = cmds.checkBoxGrp(p=checkboxContainer, numberOfCheckBoxes=2, labelArray2=['Show Skeleton', 'Reset Viewport'], value1 = settings.get("showSkeleton"), value2 = settings.get("resetViewport"))
    cmds.text("   ", p=settingsContainer, height = 10)
    cmds.text("            Bonus :    ", p=checkboxContainer)
    checkboxSettingsTwo = cmds.checkBoxGrp(p=checkboxContainer, numberOfCheckBoxes=2, labelArray2=['Open Dialog', 'Delete Unnecessary'], value1 = settings.get("showOpenDialog"), value2 = settings.get("deleteUnnecessary"))
    settingsSeparator = cmds.rowColumnLayout(numberOfColumns=2, p=settingsContainer, adj=True, width = 370)
    cmds.separator(p=settingsSeparator)
    cmds.text("   ", p=settingsContainer, height = 10)
    settingsButtons = cmds.rowColumnLayout(numberOfColumns=2, p=settingsContainer)
    cmds.button(p=settingsButtons, l ="Save Changes",w=184, h=40, c=lambda x:saveModifiedSettings())
    cmds.button(p=settingsButtons, l ="Restore Default",w=184, h=40, c=lambda x:restoreDefaultSettings())

    def saveModifiedSettings():
        settings["intervalBetweenKeyframes"] = cmds.intSliderGrp(swSpeed, q= True,value =True)
        settings["showSkeleton"] = cmds.checkBoxGrp (checkboxSettingsOne, q=True, value1=True)
        settings["resetViewport"] = cmds.checkBoxGrp (checkboxSettingsOne, q=True, value2=True)
        settings["showOpenDialog"] = cmds.checkBoxGrp (checkboxSettingsTwo, q=True, value1=True)
        settings["deleteUnnecessary"] = cmds.checkBoxGrp (checkboxSettingsTwo, q=True, value2=True)
        print(settings.get("intervalBetweenKeyframes"))
        print(settings.get("showSkeleton"))
        print(settings.get("resetViewport"))
        print(settings.get("showOpenDialog"))
        print(settings.get("deleteUnnecessary"))
        print("Current Settings Saved")
        
    def restoreDefaultSettings():
        settings["intervalBetweenKeyframes"] = settingsDefault.get("intervalBetweenKeyframes")
        settings["showSkeleton"] = settingsDefault.get("showSkeleton")
        settings["resetViewport"] = settingsDefault.get("resetViewport")
        settings["showOpenDialog"] = settingsDefault.get("showOpenDialog")
        settings["deleteUnnecessary"] = settingsDefault.get("deleteUnnecessary")
        cmds.intSliderGrp(swSpeed, e=True, value = settings["intervalBetweenKeyframes"])
        cmds.checkBoxGrp(checkboxSettingsOne, e=True, value1 = settings["showSkeleton"])
        cmds.checkBoxGrp(checkboxSettingsOne, e=True, value2 = settings["resetViewport"])
        cmds.checkBoxGrp(checkboxSettingsTwo, e=True, value1 = settings["showOpenDialog"])
        cmds.checkBoxGrp(checkboxSettingsTwo, e=True, value2 = settings["deleteUnnecessary"])
        print("Default Settings Restored")

    #About Tab ======================================================
    tabAbout = cmds.columnLayout(p=tabs, adj=True)

    aboutContainer = cmds.rowColumnLayout(numberOfColumns=2, height = 33, width = 300)
    cmds.text("Skin Weight Grading Script - VFS - " + scriptVersion  , p=tabAbout, ww=False)
    cmds.text("Current model being rigged:  " + currentModel, p=tabAbout, ww=True)
    cmds.text("This script was created for grading, use it at your own risk", p=tabAbout, ww=False)
    cmds.text("Problems? Questions? Send me an email:", p=tabAbout, ww=True)
    cmds.text(l='<a href="mailto:gtrevisan@gmail.com">Guilherme Trevisan : gtrevisan@vfs.com</a>', hl=True, p=tabAbout, highlightColor=[1,1,1])

    #Generate Tabs
    cmds.tabLayout(tabs, edit=True, tabLabel=((tabMain, 'Grader'),(tabSettings, 'Settings'),(tabAbout,'About')))

    #Outside Tabs
    outsideTabs = cmds.rowLayout(numberOfColumns=2, p=columnMain)
    startScript = cmds.rowLayout(numberOfColumns=2, p=outsideTabs)
    cmds.button(p=startScript, l ="Run Script", w=375, h=40, bgc = (.6, .8, .6), c=lambda x:skinWeightCheckJawHead(cmds.intSliderGrp(\
                swOrganization, q= True,value =True), cmds.intSliderGrp(swDeduction, q= True,value =True)))
    cmds.showWindow(crMainDialog)
    # crMainDialog Ends Here =================================================================================


# Jaw and Head Check ============================================================================
def skinWeightCheckJawHead(organizationGrade, deductionGrade):
    if cmds.window("swMainDialog", exists =True):
        cmds.deleteUI("swMainDialog")
    
    #Reset persp camera attributes
    resetPerspShapeAttributes()
    
    #Check for Wire System
    if settings.get("deleteUnnecessary") is True:
        
        wireSystemStatus = False
        for wireSyStemObj in wireSystemElements:
            if cmds.objExists(wireSyStemObj):
                cmds.delete(wireSyStemObj)
                wireSystemStatus = True
                
        if cmds.objExists('eye_elements_mainWireGrp') and cmds.objExists('headJnt'):
            cmds.delete('eye_elements_mainWireGrp')
            wireSystemStatus = True
        
        if wireSystemStatus is True:
            for eyeGeo in eyeGeoElements:
                    if cmds.objExists(eyeGeo) and cmds.objExists('headJnt'):
                        cmds.parent(eyeGeo,"headJnt")
                    
                        

       
    #Run Initial Setup ===========================================================================
    if settings.get("deleteUnnecessary") is True:
        parentToWorld(unparentList)
        bruteforceCleanUpScene(deleteList)
    
    #Setup Viewport
    if settings.get("resetViewport"):
        resetViewport(settings.get("showSkeleton"))
        setLayersVisibility(True)
        setLayersDisplayType(0)
    
    #Give eyes a checker material
    if cmds.objExists('left_pupil_geo') and cmds.objExists('right_pupil_geo'):
        applyMaterial(["left_pupil_geo", "right_pupil_geo"])
        
    #Normalize all joints
    allJoints = cmds.ls(type='joint')
    updateRadiusIfNotLocked(allJoints, defaultJointSize)
    
    #Unsubdivide Geo
    allGeo = cmds.ls(type='mesh')
    for everyGeo in allGeo:
        if cmds.objExists(everyGeo):
            cmds.displaySmoothness(everyGeo, polygonObject=1)

    #Focus on Head
    if cmds.objExists('headJnt'):
        cmds.select('headJnt')
        cmds.FrameSelectedWithoutChildren()
    
    #Change position of the camera for head inspection
    changeCameraPosition(32.279,122.473,49.756,2.2,41.6,0)
    cmds.currentTime(0)

    #Jaw and Head Setup 
    intervalBetweenKeyframesJawHead = settings.get("intervalBetweenKeyframes")
    timelineLength = intervalBetweenKeyframesJawHead * 14
    cmds.playbackOptions(minTime=0, max = timelineLength)
    #currentFrameTime = intervalBetweenKeyframesJawHead
    
    #If jaw exists, add animation
    if cmds.objExists('jawJnt'):
        cmds.select('jawJnt')
        jawJnt = cmds.ls(selection=True)[0]
        cmds.setKeyframe( jawJnt, v=0, at='rotateZ', t=0 )
        cmds.setKeyframe( jawJnt, v=30, at='rotateZ', t=intervalBetweenKeyframesJawHead )
        cmds.setKeyframe( jawJnt, v=0, at='rotateZ', t=(intervalBetweenKeyframesJawHead * 2) )
    else:
        print("Missing jawJnt!")
        
    #If head exists, add animation and play it
    if cmds.objExists('headJnt'):
        cmds.select('headJnt')
        headJnt = cmds.ls(selection=True)[0]
        #Move Front and Back
        cmds.setKeyframe( headJnt, v=0, at='rotateZ', t=(intervalBetweenKeyframesJawHead * 2) )
        cmds.setKeyframe( headJnt, v=30, at='rotateZ', t=(intervalBetweenKeyframesJawHead * 3) )
        cmds.setKeyframe( headJnt, v=0, at='rotateZ', t=(intervalBetweenKeyframesJawHead * 4) )
        cmds.setKeyframe( headJnt, v=-30, at='rotateZ', t=(intervalBetweenKeyframesJawHead * 5) )
        cmds.setKeyframe( headJnt, v=0, at='rotateZ', t=(intervalBetweenKeyframesJawHead * 6) )
        # Move to Left and Right
        cmds.setKeyframe( headJnt, v=0, at='rotateY', t=(intervalBetweenKeyframesJawHead * 6) )
        cmds.setKeyframe( headJnt, v=30, at='rotateY', t=(intervalBetweenKeyframesJawHead * 7) )
        cmds.setKeyframe( headJnt, v=0, at='rotateY', t=(intervalBetweenKeyframesJawHead * 8) )
        cmds.setKeyframe( headJnt, v=-30, at='rotateY', t=(intervalBetweenKeyframesJawHead * 9) )
        cmds.setKeyframe( headJnt, v=0, at='rotateY', t=(intervalBetweenKeyframesJawHead * 10) )
        # Move to Left and Right
        cmds.setKeyframe( headJnt, v=0, at='rotateX', t=(intervalBetweenKeyframesJawHead * 10) )
        cmds.setKeyframe( headJnt, v=30, at='rotateX', t=(intervalBetweenKeyframesJawHead * 11) )
        cmds.setKeyframe( headJnt, v=0, at='rotateX', t=(intervalBetweenKeyframesJawHead * 12) )
        cmds.setKeyframe( headJnt, v=-30, at='rotateX', t=(intervalBetweenKeyframesJawHead * 13) )
        cmds.setKeyframe( headJnt, v=0, at='rotateX', t=(intervalBetweenKeyframesJawHead * 14) )
        # Play it
        cmds.PlaybackForward()
    else:
        print("Missing headJnt!")
        
    #No Selection
    cmds.select(clear=True)

    #Build UI ==========================================================
    if cmds.window("stepJawHead", exists =True):
        cmds.deleteUI("stepJawHead")
    stepJawHead = cmds.window("stepJawHead", t = "Step 1 - Jaw & Head Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade and press next (Max 30)")
    cmds.separator(h=10)
    stepJawHeadGradeSlider = cmds.intSliderGrp(l = "Jaw & Head Grade",min =0,max =30, field =True, value=30)
    cmds.separator(h=10)
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:skinWeightCheckUpperBody(\
                organizationGrade, deductionGrade, cmds.intSliderGrp(stepJawHeadGradeSlider, q= True,value =True)))
    cmds.showWindow(stepJawHead)



# Upper Body Check ============================================================================
def skinWeightCheckUpperBody(organizationGrade,deductionGrade,stepJawHeadGrade):
    if cmds.window("stepJawHead", exists =True):
        cmds.deleteUI("stepJawHead")
    
    #Second Step Setup
    #Change position of the camera for head inspection
    changeCameraPosition(57.122,84.03,90.902,-1.4,28.6,0)
    cmds.currentTime(0)
    
    #Remove Key frames from previous step
    removeKeyFirstStep = ['headJnt', 'jawJnt']
    removeKeyFrames(removeKeyFirstStep)
        
    #Set Offsets and Setup Scene
    intervalBetweenKeyframesUpperBody = settings.get("intervalBetweenKeyframes") + 5  
    middleFingersOffset = 3
    ringFingersOffset = middleFingersOffset + middleFingersOffset
    pinkyFingersOffset = ringFingersOffset + middleFingersOffset
    waitBeforeArmOffset = 2
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesUpperBody * 14)
       
    #Key Thumb Fingers
    keyAttributes(thumbFingers, 15, 'rotateZ', (intervalBetweenKeyframesUpperBody * 2))
    keyAttributes(thumbFingers, -25, 'rotateZ', (intervalBetweenKeyframesUpperBody * 3))
    keyAttributes(thumbFingers, 0, 'rotateZ', (intervalBetweenKeyframesUpperBody * 4))
        
    #Key Index Fingers
    keyAttributes(indexFingers, 0, 'rotateZ', 0)
    keyAttributes(indexFingers, -70, 'rotateZ', intervalBetweenKeyframesUpperBody)
    currentFrameTime = intervalBetweenKeyframesUpperBody + intervalBetweenKeyframesUpperBody;
    keyAttributes(indexFingers, 0, 'rotateZ', currentFrameTime)
    
    #Key Middle Fingers
    keyAttributes(middleFingers, 0, 'rotateZ', (0 + middleFingersOffset))
    keyAttributes(middleFingers, -70, 'rotateZ', (intervalBetweenKeyframesUpperBody + middleFingersOffset))
    currentFrameTime = intervalBetweenKeyframesUpperBody + intervalBetweenKeyframesUpperBody;
    keyAttributes(middleFingers, 0, 'rotateZ', (currentFrameTime + middleFingersOffset))
    
    #Key Ring Fingers
    keyAttributes(ringFingers, 0, 'rotateZ', (0 + ringFingersOffset))
    keyAttributes(ringFingers, -70, 'rotateZ', (intervalBetweenKeyframesUpperBody + ringFingersOffset))
    currentFrameTime = intervalBetweenKeyframesUpperBody + intervalBetweenKeyframesUpperBody;
    keyAttributes(ringFingers, 0, 'rotateZ', (currentFrameTime + ringFingersOffset))
    
    #Key Pinky Fingers
    keyAttributes(pinkyFingers, 0, 'rotateZ', (0 + pinkyFingersOffset))
    keyAttributes(pinkyFingers, -70, 'rotateZ', (intervalBetweenKeyframesUpperBody + pinkyFingersOffset))
    currentFrameTime = intervalBetweenKeyframesUpperBody + intervalBetweenKeyframesUpperBody;
    keyAttributes(pinkyFingers, 0, 'rotateZ', (currentFrameTime + pinkyFingersOffset))
    
    #Key Arms
    keyArms('left_shoulderJnt','left_elbowJnt',intervalBetweenKeyframesUpperBody)
    keyArms('right_shoulderJnt','right_elbowJnt',intervalBetweenKeyframesUpperBody)

    #Key Spine
    keySpine(spineList,intervalBetweenKeyframesUpperBody)

    #No Selection
    cmds.select(clear=True)

    #Build UI ==========================================================
    if cmds.window("stepUpperBody", exists =True):
        cmds.deleteUI("stepUpperBody")
    stepUpperBody = cmds.window("stepUpperBody", t = "Step 2 - Upper Body Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("Jaw & Head Grade: " + str(stepJawHeadGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(stepJawHeadGrade + organizationGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade for the upper body (Max 20)")
    cmds.separator(h=15)
    stepUpperBodyGradeSlider = cmds.intSliderGrp(l = "Upper Body Grade",min =0,max =20, field =True, value=20)
    cmds.separator(h=20)
    cmds.button(l ="Default Camera", c="changeCameraPosition(57.122,84.03,90.902,-1.4,28.6,0)")
    cmds.button(l ="Arm Camera", c="changeCameraPosition(66.252,123.98,34.871,-24.8,65.8,0)")
    cmds.button(l ="Front Camera", c="changeCameraPosition(7.664,112.688,126.455,-7.4,3.4,0)")
    cmds.separator(h=20)
    
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:skinWeightCheckLowerBody(organizationGrade, deductionGrade, stepJawHeadGrade, \
                cmds.intSliderGrp(stepUpperBodyGradeSlider, q= True,value =True)))
    cmds.showWindow(stepUpperBody)


# Lower Body Check ============================================================================
def skinWeightCheckLowerBody(organizationGrade, deductionGrade, stepJawHeadGrade, stepUpperBodyGrade):
    #Close second dialog
    if cmds.window("stepUpperBody", exists =True):
        cmds.deleteUI("stepUpperBody")
    
    #Change position of the camera for lower body inspection
    changeCameraPosition(64.961,64.3,111.476,-10.4,30.6,0)
    cmds.currentTime(0)
    
    intervalBetweenKeyframesLowerBody = settings.get("intervalBetweenKeyframes")
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesLowerBody * 13)
    
    #Remove Key frames from previous step
    removeKeySecondStep = ['left_shoulderJnt', 'left_elbowJnt','right_elbowJnt','right_shoulderJnt']
    removeKeyFrames(removeKeySecondStep)
    removeKeyFrames(thumbFingers)
    removeKeyFrames(indexFingers)
    removeKeyFrames(middleFingers)
    removeKeyFrames(ringFingers)
    removeKeyFrames(pinkyFingers)
    removeKeyFrames(spineList)
    
    hipJoints = ['left_hipJnt', 'right_hipJnt']
    kneeJoints = ['left_kneeJnt','right_kneeJnt']
    
    #Key Legs Z Knees
    keyAttributes(kneeJoints, 0, 'rotateZ', 0)
    keyAttributes(kneeJoints, 90, 'rotateZ', intervalBetweenKeyframesLowerBody + (intervalBetweenKeyframesLowerBody/2))
    keyAttributes(kneeJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 3))
    #Key Hips Z Negative
    keyAttributes(hipJoints, 0, 'rotateZ', 0)
    keyAttributes(hipJoints, -75, 'rotateZ', intervalBetweenKeyframesLowerBody + (intervalBetweenKeyframesLowerBody/2))
    keyAttributes(hipJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 3))
    #Key Hips Y Sides
    keyAttributes(hipJoints, 0, 'rotateY', (intervalBetweenKeyframesLowerBody* 3))
    keyAttributes(hipJoints, -35, 'rotateY', (intervalBetweenKeyframesLowerBody* 4))
    keyAttributes(hipJoints, 0, 'rotateY', (intervalBetweenKeyframesLowerBody* 5))
    #Key Hips Z Positive Left
    keyAttributes(['left_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 5))
    keyAttributes(['left_hipJnt'], 75, 'rotateZ', (intervalBetweenKeyframesLowerBody* 6))
    keyAttributes(['left_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 7))
    #Key Hips Z Positive Right
    keyAttributes(['right_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 7))
    keyAttributes(['right_hipJnt'], 75, 'rotateZ', (intervalBetweenKeyframesLowerBody* 8))
    keyAttributes(['right_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 9))
    
    #Define Joint Names
    feetJoints = ['left_ankleJnt','right_ankleJnt']
    ballJoints = ['left_ballJnt','right_ballJnt']
    
    #Leg Setup for visibility
    keyAttributes(hipJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 9))
    keyAttributes(hipJoints, -75, 'rotateZ', (intervalBetweenKeyframesLowerBody* 10))
    keyAttributes(hipJoints, -75, 'rotateZ', (intervalBetweenKeyframesLowerBody* 11))
    keyAttributes(hipJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 13))
    
    keyAttributes(kneeJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 9))
    keyAttributes(kneeJoints, 40, 'rotateZ', (intervalBetweenKeyframesLowerBody* 10))
    keyAttributes(kneeJoints, 40, 'rotateZ', (intervalBetweenKeyframesLowerBody* 11))
    keyAttributes(kneeJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 13))
    #Key Foot Joints
    keyAttributes(feetJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 9))
    keyAttributes(feetJoints, 70, 'rotateZ', (intervalBetweenKeyframesLowerBody* 10))
    keyAttributes(feetJoints, 70, 'rotateZ', (intervalBetweenKeyframesLowerBody* 11))
    keyAttributes(feetJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 13))
    #Key Ball Joints
    keyAttributes(ballJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 9))
    keyAttributes(ballJoints, -50, 'rotateZ', (intervalBetweenKeyframesLowerBody* 10))
    keyAttributes(ballJoints, -50, 'rotateZ', (intervalBetweenKeyframesLowerBody* 11))
    keyAttributes(ballJoints, 0, 'rotateZ', (intervalBetweenKeyframesLowerBody* 13))
   
    #No Selection
    cmds.select(clear=True)
   
    #Build UI ==========================================================
    if cmds.window("stepLowerBody", exists =True):
        cmds.deleteUI("stepLowerBody")
    stepLowerBody = cmds.window("stepLowerBody", t = "Step 3 - Lower Body Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("Jaw & Head Grade: " + str(stepJawHeadGrade))
    cmds.text("Upper Body Grade: " + str(stepUpperBodyGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + stepJawHeadGrade + stepUpperBodyGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade for the lower body (Max 20)")
    cmds.separator(h=15)
    stepLowerBodyGradeSlider = cmds.intSliderGrp(l = "Lower Body Grade",min =0,max =20, field =True, value=20)
    cmds.separator(h=20)
    cmds.button(l ="Default Camera", c="changeCameraPosition(64.961,64.3,111.476,-10.4,30.6,0)")
    cmds.button(l ="Back Camera", c="changeCameraPosition(119.966,93.182,-127.111,-12.8,132.6,0)")
    cmds.separator(h=20)
    
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:skinWeightCheckSymmetry(organizationGrade, deductionGrade, stepJawHeadGrade, \
                stepUpperBodyGrade, cmds.intSliderGrp(stepLowerBodyGradeSlider, q= True,value =True)))
    cmds.showWindow(stepLowerBody)
    
# Symmetry Check ============================================================================
def skinWeightCheckSymmetry(organizationGrade, deductionGrade, stepJawHeadGrade, stepUpperBodyGrade, stepLowerBodyGrade):
    #Close third dialog
    if cmds.window("stepLowerBody", exists =True):
        cmds.deleteUI("stepLowerBody")

    #Change position of the camera for lower body inspection
    changeCameraPosition(0,100,270,-5,0,0)
    cmds.currentTime(0)
    
    intervalBetweenKeyframesSymmetry = settings.get("intervalBetweenKeyframes")
    cmds.playbackOptions(minTime=0, max = intervalBetweenKeyframesSymmetry * 13)
    
    hipJoints = ['left_hipJnt', 'right_hipJnt']
    kneeJoints = ['left_kneeJnt','right_kneeJnt']
    
    #Key Legs Z Knees
    keyAttributes(kneeJoints, 0, 'rotateZ', 0)
    keyAttributes(kneeJoints, 90, 'rotateZ', intervalBetweenKeyframesSymmetry + (intervalBetweenKeyframesSymmetry/2))
    keyAttributes(kneeJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 3))
    #Key Hips Z Negative
    keyAttributes(hipJoints, 0, 'rotateZ', 0)
    keyAttributes(hipJoints, -75, 'rotateZ', intervalBetweenKeyframesSymmetry + (intervalBetweenKeyframesSymmetry/2))
    keyAttributes(hipJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 3))
    #Key Hips Y Sides
    keyAttributes(hipJoints, 0, 'rotateY', (intervalBetweenKeyframesSymmetry* 3))
    keyAttributes(hipJoints, -35, 'rotateY', (intervalBetweenKeyframesSymmetry* 4))
    keyAttributes(hipJoints, 0, 'rotateY', (intervalBetweenKeyframesSymmetry* 5))
    #Key Hips Z Positive Left
    keyAttributes(['left_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 5))
    keyAttributes(['left_hipJnt'], 75, 'rotateZ', (intervalBetweenKeyframesSymmetry* 6))
    keyAttributes(['left_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 7))
    #Key Hips Z Positive Right
    keyAttributes(['right_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 7))
    keyAttributes(['right_hipJnt'], 75, 'rotateZ', (intervalBetweenKeyframesSymmetry* 8))
    keyAttributes(['right_hipJnt'], 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 9))
    
    feetJoints = ['left_ankleJnt','right_ankleJnt']
    ballJoints = ['left_ballJnt','right_ballJnt']
    
    #Leg Setup for visibility
    keyAttributes(hipJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 9))
    keyAttributes(hipJoints, -75, 'rotateZ', (intervalBetweenKeyframesSymmetry* 10))
    keyAttributes(hipJoints, -75, 'rotateZ', (intervalBetweenKeyframesSymmetry* 11))
    keyAttributes(hipJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 13))
    
    keyAttributes(kneeJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 9))
    keyAttributes(kneeJoints, 40, 'rotateZ', (intervalBetweenKeyframesSymmetry* 10))
    keyAttributes(kneeJoints, 40, 'rotateZ', (intervalBetweenKeyframesSymmetry* 11))
    keyAttributes(kneeJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 13))
    #Key Foot Joints
    keyAttributes(feetJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 9))
    keyAttributes(feetJoints, 70, 'rotateZ', (intervalBetweenKeyframesSymmetry* 10))
    keyAttributes(feetJoints, 70, 'rotateZ', (intervalBetweenKeyframesSymmetry* 11))
    keyAttributes(feetJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 13))
    #Key Ball Joints
    keyAttributes(ballJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 9))
    keyAttributes(ballJoints, -50, 'rotateZ', (intervalBetweenKeyframesSymmetry* 10))
    keyAttributes(ballJoints, -50, 'rotateZ', (intervalBetweenKeyframesSymmetry* 11))
    keyAttributes(ballJoints, 0, 'rotateZ', (intervalBetweenKeyframesSymmetry* 13))
    #Key Arms
    keyArms('left_shoulderJnt','left_elbowJnt',intervalBetweenKeyframesSymmetry)
    keyArms('right_shoulderJnt','right_elbowJnt',intervalBetweenKeyframesSymmetry)
    #Key Spine
    keySpine(spineList,intervalBetweenKeyframesSymmetry)
   
    #No Selection
    cmds.select(clear=True)
   
    #Build UI ==========================================================
    if cmds.window("stepSymmetry", exists =True):
        cmds.deleteUI("stepSymmetry")
    stepSymmetry = cmds.window("stepSymmetry", t = "Step 4 - Symmetry Check", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("Jaw & Head Grade: " + str(stepJawHeadGrade))
    cmds.text("Upper Body Grade: " + str(stepUpperBodyGrade))
    cmds.text("Lower Body Grade: " + str(stepLowerBodyGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + stepJawHeadGrade + stepUpperBodyGrade + stepLowerBodyGrade - deductionGrade))
    cmds.separator(h=10)
    cmds.text("Please enter the grade for symmetry (Max 20)")
    cmds.separator(h=15)
    stepSymmetryGradeSlider = cmds.intSliderGrp(l = "Symmetry Grade",min =0,max =20, field =True, value=20)
    cmds.separator(h=20)
    
    #Pass results to the next stage
    cmds.button(l ="Next Step", w=280, h=40, bgc = (.6, .8, .6), c=lambda x:skinWeightCheckResult(organizationGrade, deductionGrade, stepJawHeadGrade, \
                stepUpperBodyGrade, stepLowerBodyGrade, cmds.intSliderGrp(stepSymmetryGradeSlider, q= True,value =True)))
    cmds.showWindow(stepSymmetry)


# Result Check ============================================================================
def skinWeightCheckResult(organizationGrade, deductionGrade, stepJawHeadGrade, stepUpperBodyGrade, stepLowerBodyGrade, stepSymmetryGrade):
    #Close fourth dialog
    if cmds.window("stepSymmetry", exists =True):
        cmds.deleteUI("stepSymmetry")

    #Result Step Setup
    changeCameraPosition(0,100,270,-5,0,0)
    cmds.currentTime(0)
    cmds.PlaybackStop() 
    
    #Define Joints
    hipJoints = ['left_hipJnt', 'right_hipJnt']
    kneeJoints = ['left_kneeJnt','right_kneeJnt']
    feetJoints = ['left_ankleJnt','right_ankleJnt']
    ballJoints = ['left_ballJnt','right_ballJnt']
    armJoints = ['left_shoulderJnt','left_elbowJnt','right_shoulderJnt','right_elbowJnt']

    #Remove Animation
    removeKeyFrames(hipJoints)
    removeKeyFrames(kneeJoints)
    removeKeyFrames(feetJoints)
    removeKeyFrames(ballJoints)
    removeKeyFrames(armJoints)
    removeKeyFrames(spineList)
    
    #No Selection
    cmds.select(clear=True)
    
    #Build UI ==========================================================
    if cmds.window("stepResult", exists =True):
        cmds.deleteUI("stepResult")
    
    stepResult = cmds.window("stepResult", t = "Result - Skin Weight Grade", w=30, h=30, sizeable =False)
    cmds.columnLayout(adj = True)
    cmds.separator(h=10)
    cmds.text("Organization Grade: " + str(organizationGrade))
    cmds.text("Jaw & Head Grade: " + str(stepJawHeadGrade))
    cmds.text("Upper Body Grade: " + str(stepUpperBodyGrade))
    cmds.text("Lower Body Grade: " + str(stepLowerBodyGrade))
    cmds.text("Lower Body Grade: " + str(stepSymmetryGrade))
    cmds.text("")
    if deductionGrade > 0:
        cmds.text("Deduction: -" + str(deductionGrade))
    cmds.text("Total: " + str(organizationGrade + stepJawHeadGrade + stepUpperBodyGrade + stepLowerBodyGrade + stepSymmetryGrade - deductionGrade), hyperlink = True)
    cmds.separator(h=15)
    cmds.button(l ="Restart Script (New Scene)", w=280, h=40, bgc = (.5, 0, 0), c=lambda x:skinWeightCheckRestartScript())
    cmds.showWindow(stepResult)
    
    
#Restart Script
def skinWeightCheckRestartScript():
    if cmds.window("stepResult", exists =True):
        cmds.deleteUI("stepResult")
    cmds.file( f=True, new=True )
    
    #Show open dialog or not
    if settings.get("showOpenDialog") is True:
        multipleFilters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb);;All Files (*.*)"
        filePath = cmds.fileDialog2(fileFilter=multipleFilters, dialogStyle=2, fm=1)
        if filePath is not None:
            cmds.file(filePath, open=True)
        
    #Restart Script
    skinWeightCheckMainDialog()


#Start current "Main"
skinWeightCheckMainDialog()