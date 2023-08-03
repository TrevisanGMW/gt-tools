//Maya ASCII 2022 scene
//Name: curves_nurbs_bezier.ma
//Last modified: Mon, Jul 31, 2023 02:59:29 PM
//Codeset: 1252
requires maya "2022";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2022";
fileInfo "version" "2022";
fileInfo "cutIdentifier" "202205171752-c25c06f306";
fileInfo "osv" "Windows 10 Pro v2009 (Build: 19044)";
fileInfo "UUID" "F922BE79-45B7-3B08-D79C-F4A02F242806";
createNode transform -s -n "persp";
	rename -uid "09E1FB54-4E3B-95A4-B681-C39BE047228D";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 13.664525830951824 12.726010960112353 4.4474284442724814 ;
	setAttr ".r" -type "double3" -42.93835272960898 71.000000000000128 0 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "DE12EB19-4020-C1BC-0BD4-C99F954CDEAB";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 18.842486223764546;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	rename -uid "7BDCD2FA-4A69-0099-9B91-87AEE2578468";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 1000.1 0 ;
	setAttr ".r" -type "double3" -90 0 0 ;
createNode camera -s -n "topShape" -p "top";
	rename -uid "08752A1A-4DAE-2536-C0D3-1ABF6BDA4AC2";
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
	rename -uid "623F7850-494E-0DB8-E5E3-43B4146ECB3C";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 1000.1 ;
createNode camera -s -n "frontShape" -p "front";
	rename -uid "D8AC274C-4156-5DAC-5F8C-6A86CD935A08";
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
	rename -uid "C53FCD1A-4728-A08F-D82B-1AA02600CD3B";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1000.1 0 0 ;
	setAttr ".r" -type "double3" 0 90 0 ;
createNode camera -s -n "sideShape" -p "side";
	rename -uid "1435E1D4-4BBE-3945-BF9C-9D95632AFE00";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode transform -n "curve_01";
	rename -uid "FD8B98BB-44F0-EB98-5A5F-82807D360FF1";
createNode nurbsCurve -n "curve_Shape1" -p "curve_01";
	rename -uid "2F5D90FD-41EB-2347-C2E9-10BC190300DB";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 1 0 no 3
		6 0 0 0 1 1 1
		4
		0 0 5
		-5 0 5
		-5 0 0
		0 0 0
		;
createNode transform -n "curve_02";
	rename -uid "08C477E7-40DE-4807-B68F-5289F5DC5BE8";
createNode nurbsCurve -n "curve_Shape2" -p "curve_02";
	rename -uid "A62700C6-44A5-9B97-EDE3-6F8088A02CB0";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 1 0 no 3
		6 0 0 0 1 1 1
		4
		0 0 0
		-5 0 0
		-5 0 -5
		0 0 -5
		;
createNode transform -n "bezier_01";
	rename -uid "22C0A109-4550-239D-7B71-F8A069D577C7";
createNode bezierCurve -n "bezier_Shape1" -p "bezier_01";
	rename -uid "A317D023-4432-38ED-DA31-D8951E95077D";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 13 0 no 3
		18 0 0 0 1 1 1 2 2 2 3 3 3 4 4 4 5 5 5
		16
		5 0 0
		5 0 -1
		4 0 -1
		4 0 -1
		4 0 -1
		3 0 -1
		3 0 -2
		3 0 -3
		2 0 -3
		2 0 -3
		2 0 -3
		1 0 -3
		1 0 -4
		1 0 -5
		0 0 -5
		0 0 -5
		;
createNode transform -n "bezier_02";
	rename -uid "F6A61B7A-4E82-C2D0-54C3-E789FF92E1D1";
createNode bezierCurve -n "bezier_Shape2" -p "bezier_02";
	rename -uid "584A441C-45AB-7424-7145-DF9CDDC7BB17";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 28 0 no 3
		33 0 0 0 1 1 1 2 2 2 3 3 3 4 4 4 5 5 5 6 6 6 7 7 7 8 8 8 9 9 9 10 10 10
		31
		5 0 5
		5 0 5
		5 0 4
		5 0 4
		5 0 4
		4 0 4
		4 0 4
		4 0 4
		4 0 3
		4 0 3
		4 0 3
		3 0 3
		3 0 3
		3 0 3
		3 0 2
		3 0 2
		3 0 2
		2 0 2
		2 0 2
		2 0 2
		2 0 1
		2 0 1
		2 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 0
		1 0 0
		1 0 0
		0 0 0
		0 0 0
		;
createNode transform -n "combined_curve_01";
	rename -uid "8CEA3360-4866-5F36-5855-55A38338C1E9";
createNode nurbsCurve -n "combined_curve_Shape1" -p "combined_curve_01";
	rename -uid "07D82968-4846-1D8D-7460-A982B5DA8992";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		6 0 2
		7 0 2
		;
createNode nurbsCurve -n "combined_curve_Shape2" -p "combined_curve_01";
	rename -uid "62D7F6B3-413F-81ED-FF3B-8E88FF825CA4";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		1 1 0 no 3
		2 0 1
		2
		6 0 1
		7 0 1
		;
createNode lightLinker -s -n "lightLinker1";
	rename -uid "395AACFA-4133-DF0C-50C1-07AC81DFE8F2";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "568576C9-4621-F388-9FC5-36BCFF547896";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "B83F689B-40DF-B300-F5A7-0F95E4DB2B85";
createNode displayLayerManager -n "layerManager";
	rename -uid "E3F9458C-4121-D711-F05B-D68E56807A40";
createNode displayLayer -n "defaultLayer";
	rename -uid "94F92593-485B-5F4F-23AC-569691AE4083";
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "A28B2F35-482A-477A-5F8D-7888241E5265";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "2197C579-44FF-3D12-F75A-24B1F96E3AB5";
	setAttr ".g" yes;
createNode script -n "uiConfigurationScriptNode";
	rename -uid "AA5A5BD4-4870-95FD-FFC3-F98E08F2D0E9";
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "0D03AB30-431A-E674-5C2B-8888AC03A4B0";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 120 -ast 1 -aet 200 ";
	setAttr ".st" 6;
createNode script -n "uiConfigurationScriptNode1";
	rename -uid "E72B52C6-41A4-B495-FCD2-979CB70E263D";
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
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
// End of curves_nurbs_bezier.ma
