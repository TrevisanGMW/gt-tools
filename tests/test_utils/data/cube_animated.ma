//Maya ASCII 2022 scene
//Name: cube_animated.ma
//Last modified: Fri, Jul 07, 2023 04:37:03 PM
//Codeset: 1252
requires maya "2022";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "cutIdentifier" "202205171752-c25c06f306";
fileInfo "UUID" "CB2BE9AE-480D-20EB-6CCE-80B25E39E096";
createNode transform -s -n "persp";
	rename -uid "92D793BD-4448-E07F-0531-2899990D5C74";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 7 8 7 ;
	setAttr ".r" -type "double3" -30 45 -5 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "BDC38286-4AA8-1156-C15A-E3895CA2C952";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 13.068940645908343;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" -0.5 0.5 -0.5 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	rename -uid "8715328E-4F90-F91E-C40A-EFB223849A4C";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 1000.1 0 ;
	setAttr ".r" -type "double3" -90 0 0 ;
createNode camera -s -n "topShape" -p "top";
	rename -uid "F0374F56-48EE-2302-3842-219EDD1782AB";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	rename -uid "27A1DF94-4D04-710C-97CC-D3A2E15F2CAC";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 1000.1 ;
createNode camera -s -n "frontShape" -p "front";
	rename -uid "E285E9EA-4D84-EFEB-8BDB-8FAD4248D248";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	rename -uid "6E45E2E2-40A9-FAC3-5C6A-DFB71DC5C5C9";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1000.1 0 0 ;
	setAttr ".r" -type "double3" 0 90 0 ;
createNode camera -s -n "sideShape" -p "side";
	rename -uid "08191455-4FCA-FE09-BE22-5E9FCD049A77";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode transform -n "pCube1";
	rename -uid "0F1235E7-4A36-ABDF-2632-7C9E429D306E";
	setAttr ".t" -type "double3" 0 0.5 -1 ;
	setAttr ".rp" -type "double3" 0 -0.5 0 ;
	setAttr ".sp" -type "double3" 0 -0.5 0 ;
createNode mesh -n "pCubeShape1" -p "pCube1";
	rename -uid "F5C82BC2-4C02-ED1B-1B90-5DBEBFEB1560";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "pCube2";
	rename -uid "7BC0ED09-4B43-08AE-299D-28818D354DF5";
	setAttr ".t" -type "double3" -1 0.5 0 ;
	setAttr ".rp" -type "double3" 0 -0.5 0 ;
	setAttr ".sp" -type "double3" 0 -0.5 0 ;
createNode mesh -n "pCubeShape2" -p "pCube2";
	rename -uid "6072F97C-4321-B0DE-045F-248DEFE0E1A5";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode lightLinker -s -n "lightLinker1";
	rename -uid "3EB6141B-4162-500B-286E-3A952FC8466F";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "30F3E06F-43A0-FE2F-C09F-9A87A4CC431E";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "B71EC0DE-4A8A-30F0-19A3-E6BB0C27113A";
createNode displayLayerManager -n "layerManager";
	rename -uid "09B8C417-404C-5AE5-E332-8F85CE1FEFA8";
createNode displayLayer -n "defaultLayer";
	rename -uid "5C923D10-4C5B-DDE7-0000-12956F6D7B95";
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "86FB68AA-405F-3DA3-EC5F-D8ACED035945";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "5719A8FD-4EEA-2DDC-9719-AAADE7565297";
	setAttr ".g" yes;
createNode polyCube -n "polyCube1";
	rename -uid "22285883-4522-B452-E9D7-0B913DD4AAB2";
	setAttr ".cuv" 4;
createNode animCurveTL -n "pCube1_translateZ";
	rename -uid "F5D8D508-4429-57B3-BAA1-8AB7781DFCBB";
	setAttr ".tan" 2;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 -1 10 -10;
createNode animCurveTA -n "pCube1_rotateY";
	rename -uid "F5CB0CAE-443B-495E-FB37-9AAB85FB7FB4";
	setAttr ".tan" 2;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 90;
createNode animCurveTU -n "pCube1_scaleY";
	rename -uid "7EEF21FB-44EF-0604-C471-A79D162EEF34";
	setAttr ".tan" 2;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 2;
createNode polyCube -n "polyCube2";
	rename -uid "93AA1B23-47C9-439A-2C7F-CFA53FC0C3E7";
	setAttr ".cuv" 4;
createNode animCurveUL -n "pCube2_translateX";
	rename -uid "EAAF3913-4CFE-95F2-BCFE-5297F56A311E";
	setAttr ".tan" 2;
	setAttr ".wgt" no;
	setAttr -s 3 ".ktv[0:2]"  -10 -10 -1 -1 0 -2;
createNode animCurveUA -n "pCube2_rotateY";
	rename -uid "5A7FD8FE-4D20-8DB9-71F7-90BEA4511EB7";
	setAttr ".tan" 2;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  0 0 90 -90;
createNode unitConversion -n "unitConversion1";
	rename -uid "7910C638-40B6-54CE-216F-E8B0A40AE781";
	setAttr ".cf" 57.295779513082323;
createNode animCurveUU -n "pCube2_scaleY";
	rename -uid "FBCEF33C-4A33-0BB6-45D5-7897F98D5E87";
	setAttr ".tan" 2;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 2 2;
createNode script -n "uiConfigurationScriptNode";
	rename -uid "2AA56D34-421E-6246-8687-7B83BE85197D";
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "65DAFCCD-4CE2-BD57-576F-FB93A28826F5";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 120 -ast 1 -aet 200 ";
	setAttr ".st" 6;
createNode script -n "uiConfigurationScriptNode1";
	rename -uid "370D01B9-4202-7329-355A-A0BBF2B8B071";
	setAttr ".st" 3;
select -ne :time1;
	setAttr ".o" 1;
	setAttr ".unw" 1;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 5 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
select -ne :initialShadingGroup;
	setAttr -s 2 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr ".dss" -type "string" "lambert1";
select -ne :defaultResolution;
	setAttr ".pa" 1;
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "<MAYA_RESOURCES>/OCIO-configs/Maya2022-default/config.ocio";
	setAttr ".vtn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".vn" -type "string" "ACES 1.0 SDR-video";
	setAttr ".dn" -type "string" "sRGB";
	setAttr ".wsn" -type "string" "ACEScg";
	setAttr ".otn" -type "string" "ACES 1.0 SDR-video (sRGB)";
	setAttr ".potn" -type "string" "ACES 1.0 SDR-video (sRGB)";
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
connectAttr "pCube1_translateZ.o" "pCube1.tz";
connectAttr "pCube1_rotateY.o" "pCube1.ry";
connectAttr "pCube1_scaleY.o" "pCube1.sy";
connectAttr "polyCube1.out" "pCubeShape1.i";
connectAttr "pCube2_translateX.o" "pCube2.tx";
connectAttr "pCube2_rotateY.o" "pCube2.ry";
connectAttr "pCube2_scaleY.o" "pCube2.sy";
connectAttr "polyCube2.out" "pCubeShape2.i";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "pCube1.tz" "pCube2_translateX.i";
connectAttr "unitConversion1.o" "pCube2_rotateY.i";
connectAttr "pCube1.ry" "unitConversion1.i";
connectAttr "pCube1.sy" "pCube2_scaleY.i";
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
connectAttr "pCubeShape1.iog" ":initialShadingGroup.dsm" -na;
connectAttr "pCubeShape2.iog" ":initialShadingGroup.dsm" -na;
// End of cube_animated.ma