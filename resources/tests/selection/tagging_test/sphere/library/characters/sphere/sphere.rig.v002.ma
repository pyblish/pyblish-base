//Maya ASCII 2014 scene
//Name: sphere.rig.v002.ma
//Last modified: Sat, Aug 02, 2014 07:23:08 PM
//Codeset: 1252
file -rdi 1 -ns "geo" -rfn "sphere_geo_v001RN" "C:/Users/admin/Documents/GitHub/publish/resources/tests/selection/tagging_objects/sphere/library/characters/sphere//sphere.geo.v002.ma";
file -r -ns "geo" -dr 1 -rfn "sphere_geo_v001RN" "C:/Users/admin/Documents/GitHub/publish/resources/tests/selection/tagging_objects/sphere/library/characters/sphere//sphere.geo.v002.ma";
requires maya "2014";
currentUnit -l centimeter -a degree -t pal;
fileInfo "application" "maya";
fileInfo "product" "Maya 2014";
fileInfo "version" "2014";
fileInfo "cutIdentifier" "201307170459-880822";
fileInfo "osv" "Microsoft Windows 8 Enterprise Edition, 64-bit  (Build 9200)\n";
createNode transform -s -n "persp";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -0.52372763900640873 3.0450360417157958 8.710195071367874 ;
	setAttr ".r" -type "double3" -17.138352729602659 -3.8000000000000642 0 ;
createNode camera -s -n "perspShape" -p "persp";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999986;
	setAttr ".coi" 9.196989178547998;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" 0 -2.4651903288156619e-032 4.4408920985006262e-016 ;
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
createNode transform -n "Sphere_AST";
createNode transform -n "rig_grp" -p "Sphere_AST";
createNode transform -n "world_grp" -p "rig_grp";
createNode transform -n "world_cnt" -p "world_grp";
	addAttr -ci true -sn "dataExport" -ln "dataExport" -dt "string";
	addAttr -ci true -sn "publish" -ln "publish" -min 0 -max 1 -at "bool";
	setAttr -k on ".dataExport" -type "string" "['json', 'atom']";
	setAttr -k on ".publish" yes;
createNode nurbsCurve -n "world_cntShape" -p "world_cnt";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.2769381054359947 7.8189908176573765e-017 -1.2769381054359916
		-2.0602739686138166e-016 1.105772285840176e-016 -1.8058631870185882
		-1.276938105435993 7.8189908176573814e-017 -1.276938105435993
		-1.8058631870185882 3.2042514419814014e-032 -5.2329397246819583e-016
		-1.2769381054359934 -7.818990817657379e-017 1.2769381054359925
		-5.4414182168837648e-016 -1.1057722858401765e-016 1.8058631870185886
		1.2769381054359916 -7.8189908176573814e-017 1.2769381054359934
		1.8058631870185882 -5.9391245179286985e-032 9.6993264050724632e-016
		1.2769381054359947 7.8189908176573765e-017 -1.2769381054359916
		-2.0602739686138166e-016 1.105772285840176e-016 -1.8058631870185882
		-1.276938105435993 7.8189908176573814e-017 -1.276938105435993
		;
createNode transform -n "geo_grp" -p "Sphere_AST";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
createNode fosterParent -n "sphere_geo_v001RNfosterParent1";
createNode parentConstraint -n "body_parentConstraint1" -p "sphere_geo_v001RNfosterParent1";
	addAttr -ci true -k true -sn "w0" -ln "world_cntW0" -dv 1 -min 0 -at "double";
	setAttr -k on ".nds";
	setAttr -k off ".v";
	setAttr -k off ".tx";
	setAttr -k off ".ty";
	setAttr -k off ".tz";
	setAttr -k off ".rx";
	setAttr -k off ".ry";
	setAttr -k off ".rz";
	setAttr -k off ".sx";
	setAttr -k off ".sy";
	setAttr -k off ".sz";
	setAttr ".erp" yes;
	setAttr -k on ".w0";
createNode lightLinker -s -n "lightLinker1";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode displayLayerManager -n "layerManager";
createNode displayLayer -n "defaultLayer";
createNode renderLayerManager -n "renderLayerManager";
createNode renderLayer -n "defaultRenderLayer";
	setAttr ".g" yes;
createNode script -n "sceneConfigurationScriptNode";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 24 -ast 1 -aet 48 ";
	setAttr ".st" 6;
createNode reference -n "sphere_geo_v001RN";
	setAttr -s 2 ".fn";
	setAttr ".fn[0]" -type "string" "C:/Users/marcus/Dropbox/AF/development/marcus/pipi/repos/publish/resources/tests/selection/tagging_test/sphere/library/characters/sphere/sphere.geo.v002.ma";
	setAttr ".fn[1]" -type "string" "Y:/sandbox/tokejepsen//sphere.geo.v001.ma";
	setAttr -s 10 ".phl";
	setAttr ".phl[1]" 0;
	setAttr ".phl[2]" 0;
	setAttr ".phl[3]" 0;
	setAttr ".phl[4]" 0;
	setAttr ".phl[5]" 0;
	setAttr ".phl[6]" 0;
	setAttr ".phl[7]" 0;
	setAttr ".phl[8]" 0;
	setAttr ".phl[9]" 0;
	setAttr ".phl[10]" 0;
	setAttr ".ed" -type "dataReferenceEdits" 
		"sphere_geo_v001RN"
		"sphere_geo_v001RN" 0
		"sphere_geo_v001RN" 12
		0 "|geo:body" "|Sphere_AST|geo_grp" "-s -r "
		0 "|sphere_geo_v001RNfosterParent1|body_parentConstraint1" "|Sphere_AST|geo_grp|geo:body" 
		"-s -r "
		5 4 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.translateX" "sphere_geo_v001RN.placeHolderList[1]" 
		""
		5 4 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.translateY" "sphere_geo_v001RN.placeHolderList[2]" 
		""
		5 4 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.translateZ" "sphere_geo_v001RN.placeHolderList[3]" 
		""
		5 4 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.rotateX" "sphere_geo_v001RN.placeHolderList[4]" 
		""
		5 4 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.rotateY" "sphere_geo_v001RN.placeHolderList[5]" 
		""
		5 4 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.rotateZ" "sphere_geo_v001RN.placeHolderList[6]" 
		""
		5 3 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.rotateOrder" "sphere_geo_v001RN.placeHolderList[7]" 
		""
		5 3 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.parentInverseMatrix" 
		"sphere_geo_v001RN.placeHolderList[8]" ""
		5 3 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.rotatePivot" "sphere_geo_v001RN.placeHolderList[9]" 
		""
		5 3 "sphere_geo_v001RN" "|Sphere_AST|geo_grp|geo:body.rotatePivotTranslate" 
		"sphere_geo_v001RN.placeHolderList[10]" "";
	setAttr ".ptag" -type "string" "";
lockNode -l 1 ;
createNode reference -n "sharedReferenceNode";
	setAttr ".ed" -type "dataReferenceEdits" 
		"sharedReferenceNode";
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
	setAttr -s 2 ".r";
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
select -ne :ikSystem;
	setAttr -s 4 ".sol";
connectAttr "body_parentConstraint1.ctx" "sphere_geo_v001RN.phl[1]";
connectAttr "body_parentConstraint1.cty" "sphere_geo_v001RN.phl[2]";
connectAttr "body_parentConstraint1.ctz" "sphere_geo_v001RN.phl[3]";
connectAttr "body_parentConstraint1.crx" "sphere_geo_v001RN.phl[4]";
connectAttr "body_parentConstraint1.cry" "sphere_geo_v001RN.phl[5]";
connectAttr "body_parentConstraint1.crz" "sphere_geo_v001RN.phl[6]";
connectAttr "sphere_geo_v001RN.phl[7]" "body_parentConstraint1.cro";
connectAttr "sphere_geo_v001RN.phl[8]" "body_parentConstraint1.cpim";
connectAttr "sphere_geo_v001RN.phl[9]" "body_parentConstraint1.crp";
connectAttr "sphere_geo_v001RN.phl[10]" "body_parentConstraint1.crt";
connectAttr "world_cnt.t" "body_parentConstraint1.tg[0].tt";
connectAttr "world_cnt.rp" "body_parentConstraint1.tg[0].trp";
connectAttr "world_cnt.rpt" "body_parentConstraint1.tg[0].trt";
connectAttr "world_cnt.r" "body_parentConstraint1.tg[0].tr";
connectAttr "world_cnt.ro" "body_parentConstraint1.tg[0].tro";
connectAttr "world_cnt.s" "body_parentConstraint1.tg[0].ts";
connectAttr "world_cnt.pm" "body_parentConstraint1.tg[0].tpm";
connectAttr "body_parentConstraint1.w0" "body_parentConstraint1.tg[0].tw";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "sphere_geo_v001RNfosterParent1.msg" "sphere_geo_v001RN.fp";
connectAttr "sharedReferenceNode.sr" "sphere_geo_v001RN.sr";
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
// End of sphere.rig.v002.ma
