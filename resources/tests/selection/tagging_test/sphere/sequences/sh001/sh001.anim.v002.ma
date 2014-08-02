//Maya ASCII 2014 scene
//Name: sh001.anim.v002.ma
//Last modified: Sat, Aug 02, 2014 07:38:55 PM
//Codeset: 1252
file -rdi 1 -ns "sphere" -rfn "sphere_rig_v001RN" "C:/Users/admin/Documents/GitHub/publish/resources/tests/selection/tagging_objects/sphere/library/characters/sphere/sphere.rig.v002.ma";
file -rdi 2 -ns "geo" -rfn "sphere:sphere_geo_v001RN" "C:/Users/admin/Documents/GitHub/publish/resources/tests/selection/tagging_objects/sphere/library/characters/sphere//sphere.geo.v002.ma";
file -r -ns "sphere" -dr 1 -rfn "sphere_rig_v001RN" "C:/Users/admin/Documents/GitHub/publish/resources/tests/selection/tagging_objects/sphere/library/characters/sphere/sphere.rig.v002.ma";
requires maya "2014";
currentUnit -l centimeter -a degree -t pal;
fileInfo "application" "maya";
fileInfo "product" "Maya 2014";
fileInfo "version" "2014";
fileInfo "cutIdentifier" "201307170459-880822";
fileInfo "osv" "Microsoft Windows 8 Enterprise Edition, 64-bit  (Build 9200)\n";
createNode transform -s -n "persp";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -2.8683243166572523 6.6107836938107027 14.756249382364297 ;
	setAttr ".r" -type "double3" -23.738352729603058 -10.999999999999959 0 ;
createNode camera -s -n "perspShape" -p "persp";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999986;
	setAttr ".coi" 16.421834284464161;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" 0 0 2.2204460492503131e-016 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 100.1 0 ;
	setAttr ".r" -type "double3" -89.999999999999986 0 0 ;
createNode camera -s -n "topShape" -p "top";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 100.1 ;
createNode camera -s -n "frontShape" -p "front";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 100.1 0 0 ;
	setAttr ".r" -type "double3" 0 89.999999999999986 0 ;
createNode camera -s -n "sideShape" -p "side";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode lightLinker -s -n "lightLinker1";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode displayLayerManager -n "layerManager";
createNode displayLayer -n "defaultLayer";
createNode renderLayerManager -n "renderLayerManager";
createNode renderLayer -n "defaultRenderLayer";
	setAttr ".g" yes;
createNode reference -n "sphere_rig_v001RN";
	setAttr ".fn[0]" -type "string" "C:/Users/marcus/Dropbox/AF/development/marcus/pipi/repos/publish/resources/tests/selection/tagging_test/sphere/library/characters/sphere/sphere.rig.v002.ma";
	setAttr -s 12 ".phl";
	setAttr ".phl[2]" 0;
	setAttr ".phl[3]" 0;
	setAttr ".phl[4]" 0;
	setAttr ".phl[5]" 0;
	setAttr ".phl[6]" 0;
	setAttr ".phl[7]" 0;
	setAttr ".phl[8]" 0;
	setAttr ".phl[9]" 0;
	setAttr ".phl[10]" 0;
	setAttr ".phl[11]" 0;
	setAttr ".phl[12]" 0;
	setAttr ".ed" -type "dataReferenceEdits" 
		"sphere_rig_v001RN"
		"sphere_rig_v001:sphere_geo_v001RN" 0
		"sphere:sphere_geo_v001RN" 0
		"sphere_rig_v001RN" 1
		5 4 "sphere_rig_v001RN" "|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.Publish" 
		"sphere_rig_v001RN.placeHolderList[1]" ""
		"sphere_rig_v001RN" 16
		2 "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt" "translate" 
		" -type \"double3\" 0 0 0"
		2 "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt" "translateX" 
		" -av"
		2 "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt" "translateY" 
		" -av"
		2 "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt" "translateZ" 
		" -av"
		2 "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt" "publish" 
		" -k 1 1"
		5 3 "sphere_rig_v001RN" "|sphere:Sphere_AST.instObjGroups" "sphere_rig_v001RN.placeHolderList[2]" 
		""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.translateX" 
		"sphere_rig_v001RN.placeHolderList[3]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.translateY" 
		"sphere_rig_v001RN.placeHolderList[4]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.translateZ" 
		"sphere_rig_v001RN.placeHolderList[5]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.rotateX" 
		"sphere_rig_v001RN.placeHolderList[6]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.rotateY" 
		"sphere_rig_v001RN.placeHolderList[7]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.rotateZ" 
		"sphere_rig_v001RN.placeHolderList[8]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.scaleX" 
		"sphere_rig_v001RN.placeHolderList[9]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.scaleY" 
		"sphere_rig_v001RN.placeHolderList[10]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.scaleZ" 
		"sphere_rig_v001RN.placeHolderList[11]" ""
		5 4 "sphere_rig_v001RN" "|sphere:Sphere_AST|sphere:rig_grp|sphere:world_grp|sphere:world_cnt.visibility" 
		"sphere_rig_v001RN.placeHolderList[12]" "";
	setAttr ".ptag" -type "string" "";
lockNode -l 1 ;
createNode script -n "sceneConfigurationScriptNode";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 24 -ast 1 -aet 48 ";
	setAttr ".st" 6;
createNode animCurveTU -n "world_cnt_visibility";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 1;
	setAttr ".kot[0]"  5;
createNode animCurveTL -n "world_cnt_translateX";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 24 -5.9113266960156654;
createNode animCurveTL -n "world_cnt_translateY";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 24 5.5794239161961334;
createNode animCurveTL -n "world_cnt_translateZ";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 24 -2.0317705732361446;
createNode animCurveTA -n "world_cnt_rotateX";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 0;
createNode animCurveTA -n "world_cnt_rotateY";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 0;
createNode animCurveTA -n "world_cnt_rotateZ";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 0;
createNode animCurveTU -n "world_cnt_scaleX";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 1;
createNode animCurveTU -n "world_cnt_scaleY";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 1;
createNode animCurveTU -n "world_cnt_scaleZ";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 1;
createNode animCurveTU -n "world_cnt_Publish";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr ".ktv[0]"  1 1;
	setAttr ".kot[0]"  5;
createNode reference -n "sharedReferenceNode";
	setAttr ".ed" -type "dataReferenceEdits" 
		"sharedReferenceNode";
createNode objectSet -n "publish_SEL";
	addAttr -ci true -sn "publishable" -ln "publishable" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "class" -ln "class" -dt "string";
	setAttr ".ihi" 0;
	setAttr -k on ".publishable" yes;
	setAttr -k on ".class" -type "string" "animation";
select -ne :time1;
	setAttr ".o" 1;
	setAttr ".unw" 1;
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :initialShadingGroup;
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultShaderList1;
	setAttr -s 2 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
	setAttr -s 3 ".r";
select -ne :renderGlobalsList1;
select -ne :defaultRenderGlobals;
	setAttr ".fs" 1;
	setAttr ".ef" 10;
select -ne :defaultResolution;
	setAttr ".pa" 1;
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 18 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surfaces" "Particles" "Fluids" "Image Planes" "UI:" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 18 0 1 1 1 1 1
		 1 0 0 0 0 0 0 0 0 0 0 0 ;
select -ne :defaultHardwareRenderGlobals;
	setAttr ".fn" -type "string" "im";
	setAttr ".res" -type "string" "ntsc_4d 646 485 1.333";
connectAttr "sphere_rig_v001RN.phl[2]" "publish_SEL.dsm" -na;
connectAttr "world_cnt_translateX.o" "sphere_rig_v001RN.phl[3]";
connectAttr "world_cnt_translateY.o" "sphere_rig_v001RN.phl[4]";
connectAttr "world_cnt_translateZ.o" "sphere_rig_v001RN.phl[5]";
connectAttr "world_cnt_rotateX.o" "sphere_rig_v001RN.phl[6]";
connectAttr "world_cnt_rotateY.o" "sphere_rig_v001RN.phl[7]";
connectAttr "world_cnt_rotateZ.o" "sphere_rig_v001RN.phl[8]";
connectAttr "world_cnt_scaleX.o" "sphere_rig_v001RN.phl[9]";
connectAttr "world_cnt_scaleY.o" "sphere_rig_v001RN.phl[10]";
connectAttr "world_cnt_scaleZ.o" "sphere_rig_v001RN.phl[11]";
connectAttr "world_cnt_visibility.o" "sphere_rig_v001RN.phl[12]";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "world_cnt_Publish.o" "sphere_rig_v001RN.phl[1]";
connectAttr "sharedReferenceNode.sr" "sphere_rig_v001RN.sr";
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
// End of sh001.anim.v002.ma
