//Maya ASCII 2023 scene
//Name: cylinder_rig.ma
//Last modified: Wed, Oct 09, 2024 11:13:44 AM
//Codeset: 1252
requires maya "2023";
currentUnit -l centimeter -a degree -t ntsc;
fileInfo "application" "maya";
fileInfo "product" "Maya 2023";
fileInfo "version" "2023";
fileInfo "cutIdentifier" "202405151550-05a853e76d";
fileInfo "osv" "Windows 11 Pro v2009 (Build: 22631)";
fileInfo "UUID" "DB128520-4C4F-0BA4-5A7F-0DA26FE2EDFA";
fileInfo "timeline-marker" "{}";
createNode transform -s -n "persp";
	rename -uid "72C57BD1-4FB3-E447-BE9D-B7B25ABE1B2A";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 46.989483877830935 42.826446570963746 94.242413527134943 ;
	setAttr ".r" -type "double3" -12.938352729726951 26.600000000001483 0 ;
createNode camera -s -n "perspShape" -p "persp";
	rename -uid "7792D484-4FA9-B03B-8523-92B833CE8B8C";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".ncp" 1;
	setAttr ".coi" 117.31979861224373;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" -1.1920928955078125e-07 0 -1.7881393432617188e-07 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	rename -uid "7135CBF4-4FAC-5BAA-3811-80BD927038FD";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 1000.1 0 ;
	setAttr ".r" -type "double3" -90 0 0 ;
createNode camera -s -n "topShape" -p "top";
	rename -uid "0A00CE33-4F6F-4C6C-43DF-FD927FAC7E69";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
	setAttr ".ai_translator" -type "string" "orthographic";
createNode transform -s -n "front";
	rename -uid "412D4C2E-47B2-218F-CB2D-6198B7E46C9D";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 103.37583923339842 1005.4285524776037 ;
createNode camera -s -n "frontShape" -p "front";
	rename -uid "2B4463D2-4D85-C943-A20F-4F88FF16D246";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1005.4285524776037;
	setAttr ".ow" 95.91473191240938;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".tp" -type "double3" 0 103.37583923339842 -5.3290705182007514e-15 ;
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
	setAttr ".ai_translator" -type "string" "orthographic";
createNode transform -s -n "side";
	rename -uid "C233BC75-4A6D-603F-BB48-F4955BB250CE";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1000.1 0 0 ;
	setAttr ".r" -type "double3" 0 90 0 ;
createNode camera -s -n "sideShape" -p "side";
	rename -uid "3E5DDC36-46C1-177B-AA6E-1684FCFE9B90";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 1000.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
	setAttr ".ai_translator" -type "string" "orthographic";
createNode transform -n "rig";
	rename -uid "3A9EBC23-430B-3A64-7AE2-0EBF34E287D7";
	addAttr -ci true -sn "nts" -ln "notes" -dt "string";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 1 0.44999999 0.69999999 ;
	setAttr ".nts" -type "string" "This rig was created using GT Biped Rigger. (v1.12.7)\n\nIssues, questions or suggestions? Go to:\ngithub.com/TrevisanGMW/gt-tools";
createNode transform -n "geometry" -p "rig";
	rename -uid "BB874C6E-4910-9049-03DF-9F910D97E0F8";
	setAttr ".ovdt" 2;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.30000001 1 0.80000001 ;
createNode transform -n "test_cylinder" -p "geometry";
	rename -uid "9E8E231C-40D5-FFD3-F673-438F7A4E31FF";
	setAttr -l on ".tx";
	setAttr -l on ".ty";
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr -l on ".rz";
	setAttr -l on ".sx";
	setAttr -l on ".sy";
	setAttr -l on ".sz";
createNode mesh -n "test_cylinderShape" -p "test_cylinder";
	rename -uid "A56F8EBC-4A04-E1C3-A50F-B6893CD0277D";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr ".vcs" 2;
createNode mesh -n "test_cylinderShapeOrig" -p "test_cylinder";
	rename -uid "8FBFD65B-4A19-89C9-6809-43864AD482BD";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr -s 10 ".gtag";
	setAttr ".gtag[0].gtagnm" -type "string" "bottom";
	setAttr ".gtag[0].gtagcmp" -type "componentList" 1 "f[20:39]";
	setAttr ".gtag[1].gtagnm" -type "string" "bottomRing";
	setAttr ".gtag[1].gtagcmp" -type "componentList" 1 "e[0:19]";
	setAttr ".gtag[2].gtagnm" -type "string" "cylBottomCap";
	setAttr ".gtag[2].gtagcmp" -type "componentList" 2 "vtx[0:19]" "vtx[40]";
	setAttr ".gtag[3].gtagnm" -type "string" "cylBottomRing";
	setAttr ".gtag[3].gtagcmp" -type "componentList" 1 "vtx[0:19]";
	setAttr ".gtag[4].gtagnm" -type "string" "cylSides";
	setAttr ".gtag[4].gtagcmp" -type "componentList" 1 "vtx[0:39]";
	setAttr ".gtag[5].gtagnm" -type "string" "cylTopCap";
	setAttr ".gtag[5].gtagcmp" -type "componentList" 2 "vtx[20:39]" "vtx[41]";
	setAttr ".gtag[6].gtagnm" -type "string" "cylTopRing";
	setAttr ".gtag[6].gtagcmp" -type "componentList" 1 "vtx[20:39]";
	setAttr ".gtag[7].gtagnm" -type "string" "sides";
	setAttr ".gtag[7].gtagcmp" -type "componentList" 1 "f[0:19]";
	setAttr ".gtag[8].gtagnm" -type "string" "top";
	setAttr ".gtag[8].gtagcmp" -type "componentList" 1 "f[40:59]";
	setAttr ".gtag[9].gtagnm" -type "string" "topRing";
	setAttr ".gtag[9].gtagcmp" -type "componentList" 1 "e[20:39]";
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 84 ".uvst[0].uvsp[0:83]" -type "float2" 0.64860266 0.10796607
		 0.62640899 0.064408496 0.59184152 0.029841021 0.54828393 0.0076473355 0.5 -7.4505806e-08
		 0.45171607 0.0076473504 0.40815851 0.029841051 0.37359107 0.064408526 0.3513974 0.1079661
		 0.34374997 0.15625 0.3513974 0.2045339 0.37359107 0.24809146 0.40815854 0.28265893
		 0.4517161 0.3048526 0.5 0.3125 0.54828387 0.3048526 0.59184146 0.28265893 0.62640893
		 0.24809146 0.6486026 0.2045339 0.65625 0.15625 0.375 0.3125 0.38749999 0.3125 0.39999998
		 0.3125 0.41249996 0.3125 0.42499995 0.3125 0.43749994 0.3125 0.44999993 0.3125 0.46249992
		 0.3125 0.4749999 0.3125 0.48749989 0.3125 0.49999988 0.3125 0.51249987 0.3125 0.52499986
		 0.3125 0.53749985 0.3125 0.54999983 0.3125 0.56249982 0.3125 0.57499981 0.3125 0.5874998
		 0.3125 0.59999979 0.3125 0.61249977 0.3125 0.62499976 0.3125 0.375 0.6875 0.38749999
		 0.6875 0.39999998 0.6875 0.41249996 0.6875 0.42499995 0.6875 0.43749994 0.6875 0.44999993
		 0.6875 0.46249992 0.6875 0.4749999 0.6875 0.48749989 0.6875 0.49999988 0.6875 0.51249987
		 0.6875 0.52499986 0.6875 0.53749985 0.6875 0.54999983 0.6875 0.56249982 0.6875 0.57499981
		 0.6875 0.5874998 0.6875 0.59999979 0.6875 0.61249977 0.6875 0.62499976 0.6875 0.64860266
		 0.79546607 0.62640899 0.75190848 0.59184152 0.71734101 0.54828393 0.69514734 0.5
		 0.68749994 0.45171607 0.69514734 0.40815851 0.71734107 0.37359107 0.75190854 0.3513974
		 0.79546607 0.34374997 0.84375 0.3513974 0.89203393 0.37359107 0.93559146 0.40815854
		 0.97015893 0.4517161 0.9923526 0.5 1 0.54828387 0.9923526 0.59184146 0.97015893 0.62640893
		 0.93559146 0.6486026 0.89203393 0.65625 0.84375 0.5 0.15625 0.5 0.84375;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 42 ".pt[0:41]" -type "float3"  8.559514 1 -2.7811546 7.281158 
		1 -5.2900705 5.2900705 1 -7.2811575 2.7811544 1 -8.5595131 0 1 -9.0000038 -2.7811544 
		1 -8.5595131 -5.2900696 1 -7.2811556 -7.2811551 1 -5.2900686 -8.5595112 1 -2.7811537 
		-9.0000019 1 0 -8.5595112 1 2.7811537 -7.2811546 1 5.2900681 -5.2900681 1 7.2811542 
		-2.7811537 1 8.5595102 -2.682209e-07 1 9.000001 2.7811527 1 8.5595093 5.2900672 1 
		7.2811537 7.2811532 1 5.2900677 8.5595093 1 2.781153 9 1 0 8.559514 41.549076 -2.7811546 
		7.281158 41.549076 -5.2900705 5.2900705 41.549076 -7.2811575 2.7811544 41.549076 
		-8.5595131 0 41.549076 -9.0000038 -2.7811544 41.549076 -8.5595131 -5.2900696 41.549076 
		-7.2811556 -7.2811551 41.549076 -5.2900686 -8.5595112 41.549076 -2.7811537 -9.0000019 
		41.549076 0 -8.5595112 41.549076 2.7811537 -7.2811546 41.549076 5.2900681 -5.2900681 
		41.549076 7.2811542 -2.7811537 41.549076 8.5595102 -2.682209e-07 41.549076 9.000001 
		2.7811527 41.549076 8.5595093 5.2900672 41.549076 7.2811537 7.2811532 41.549076 5.2900677 
		8.5595093 41.549076 2.781153 9 41.549076 0 0 1 0 0 41.549076 0;
	setAttr -s 42 ".vt[0:41]"  0.95105714 -1 -0.30901718 0.80901754 -1 -0.5877856
		 0.5877856 -1 -0.80901748 0.30901715 -1 -0.95105702 0 -1 -1.000000476837 -0.30901715 -1 -0.95105696
		 -0.58778548 -1 -0.8090173 -0.80901724 -1 -0.58778542 -0.95105678 -1 -0.30901706 -1.000000238419 -1 0
		 -0.95105678 -1 0.30901706 -0.80901718 -1 0.58778536 -0.58778536 -1 0.80901712 -0.30901706 -1 0.95105666
		 -2.9802322e-08 -1 1.000000119209 0.30901697 -1 0.9510566 0.58778524 -1 0.80901706
		 0.809017 -1 0.5877853 0.95105654 -1 0.309017 1 -1 0 0.95105714 1 -0.30901718 0.80901754 1 -0.5877856
		 0.5877856 1 -0.80901748 0.30901715 1 -0.95105702 0 1 -1.000000476837 -0.30901715 1 -0.95105696
		 -0.58778548 1 -0.8090173 -0.80901724 1 -0.58778542 -0.95105678 1 -0.30901706 -1.000000238419 1 0
		 -0.95105678 1 0.30901706 -0.80901718 1 0.58778536 -0.58778536 1 0.80901712 -0.30901706 1 0.95105666
		 -2.9802322e-08 1 1.000000119209 0.30901697 1 0.9510566 0.58778524 1 0.80901706 0.809017 1 0.5877853
		 0.95105654 1 0.309017 1 1 0 0 -1 0 0 1 0;
	setAttr -s 100 ".ed[0:99]"  0 1 0 1 2 0 2 3 0 3 4 0 4 5 0 5 6 0 6 7 0
		 7 8 0 8 9 0 9 10 0 10 11 0 11 12 0 12 13 0 13 14 0 14 15 0 15 16 0 16 17 0 17 18 0
		 18 19 0 19 0 0 20 21 0 21 22 0 22 23 0 23 24 0 24 25 0 25 26 0 26 27 0 27 28 0 28 29 0
		 29 30 0 30 31 0 31 32 0 32 33 0 33 34 0 34 35 0 35 36 0 36 37 0 37 38 0 38 39 0 39 20 0
		 0 20 1 1 21 1 2 22 1 3 23 1 4 24 1 5 25 1 6 26 1 7 27 1 8 28 1 9 29 1 10 30 1 11 31 1
		 12 32 1 13 33 1 14 34 1 15 35 1 16 36 1 17 37 1 18 38 1 19 39 1 40 0 1 40 1 1 40 2 1
		 40 3 1 40 4 1 40 5 1 40 6 1 40 7 1 40 8 1 40 9 1 40 10 1 40 11 1 40 12 1 40 13 1
		 40 14 1 40 15 1 40 16 1 40 17 1 40 18 1 40 19 1 20 41 1 21 41 1 22 41 1 23 41 1 24 41 1
		 25 41 1 26 41 1 27 41 1 28 41 1 29 41 1 30 41 1 31 41 1 32 41 1 33 41 1 34 41 1 35 41 1
		 36 41 1 37 41 1 38 41 1 39 41 1;
	setAttr -s 60 -ch 200 ".fc[0:59]" -type "polyFaces" 
		f 4 0 41 -21 -41
		mu 0 4 20 21 42 41
		f 4 1 42 -22 -42
		mu 0 4 21 22 43 42
		f 4 2 43 -23 -43
		mu 0 4 22 23 44 43
		f 4 3 44 -24 -44
		mu 0 4 23 24 45 44
		f 4 4 45 -25 -45
		mu 0 4 24 25 46 45
		f 4 5 46 -26 -46
		mu 0 4 25 26 47 46
		f 4 6 47 -27 -47
		mu 0 4 26 27 48 47
		f 4 7 48 -28 -48
		mu 0 4 27 28 49 48
		f 4 8 49 -29 -49
		mu 0 4 28 29 50 49
		f 4 9 50 -30 -50
		mu 0 4 29 30 51 50
		f 4 10 51 -31 -51
		mu 0 4 30 31 52 51
		f 4 11 52 -32 -52
		mu 0 4 31 32 53 52
		f 4 12 53 -33 -53
		mu 0 4 32 33 54 53
		f 4 13 54 -34 -54
		mu 0 4 33 34 55 54
		f 4 14 55 -35 -55
		mu 0 4 34 35 56 55
		f 4 15 56 -36 -56
		mu 0 4 35 36 57 56
		f 4 16 57 -37 -57
		mu 0 4 36 37 58 57
		f 4 17 58 -38 -58
		mu 0 4 37 38 59 58
		f 4 18 59 -39 -59
		mu 0 4 38 39 60 59
		f 4 19 40 -40 -60
		mu 0 4 39 40 61 60
		f 3 -1 -61 61
		mu 0 3 1 0 82
		f 3 -2 -62 62
		mu 0 3 2 1 82
		f 3 -3 -63 63
		mu 0 3 3 2 82
		f 3 -4 -64 64
		mu 0 3 4 3 82
		f 3 -5 -65 65
		mu 0 3 5 4 82
		f 3 -6 -66 66
		mu 0 3 6 5 82
		f 3 -7 -67 67
		mu 0 3 7 6 82
		f 3 -8 -68 68
		mu 0 3 8 7 82
		f 3 -9 -69 69
		mu 0 3 9 8 82
		f 3 -10 -70 70
		mu 0 3 10 9 82
		f 3 -11 -71 71
		mu 0 3 11 10 82
		f 3 -12 -72 72
		mu 0 3 12 11 82
		f 3 -13 -73 73
		mu 0 3 13 12 82
		f 3 -14 -74 74
		mu 0 3 14 13 82
		f 3 -15 -75 75
		mu 0 3 15 14 82
		f 3 -16 -76 76
		mu 0 3 16 15 82
		f 3 -17 -77 77
		mu 0 3 17 16 82
		f 3 -18 -78 78
		mu 0 3 18 17 82
		f 3 -19 -79 79
		mu 0 3 19 18 82
		f 3 -20 -80 60
		mu 0 3 0 19 82
		f 3 20 81 -81
		mu 0 3 80 79 83
		f 3 21 82 -82
		mu 0 3 79 78 83
		f 3 22 83 -83
		mu 0 3 78 77 83
		f 3 23 84 -84
		mu 0 3 77 76 83
		f 3 24 85 -85
		mu 0 3 76 75 83
		f 3 25 86 -86
		mu 0 3 75 74 83
		f 3 26 87 -87
		mu 0 3 74 73 83
		f 3 27 88 -88
		mu 0 3 73 72 83
		f 3 28 89 -89
		mu 0 3 72 71 83
		f 3 29 90 -90
		mu 0 3 71 70 83
		f 3 30 91 -91
		mu 0 3 70 69 83
		f 3 31 92 -92
		mu 0 3 69 68 83
		f 3 32 93 -93
		mu 0 3 68 67 83
		f 3 33 94 -94
		mu 0 3 67 66 83
		f 3 34 95 -95
		mu 0 3 66 65 83
		f 3 35 96 -96
		mu 0 3 65 64 83
		f 3 36 97 -97
		mu 0 3 64 63 83
		f 3 37 98 -98
		mu 0 3 63 62 83
		f 3 38 99 -99
		mu 0 3 62 81 83
		f 3 39 80 -100
		mu 0 3 81 80 83;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
	setAttr ".pd[0]" -type "dataPolyComponent" Index_Data UV 0 ;
	setAttr ".hfd" -type "dataPolyComponent" Index_Data Face 0 ;
	setAttr ".vcs" 2;
createNode transform -n "skeleton" -p "rig";
	rename -uid "D22B7045-4E16-8F03-F533-478286742815";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr ".uocol" yes;
	setAttr ".oclr" -type "float3" 0.75 0.44999999 0.94999999 ;
createNode joint -n "C_root_JNT" -p "skeleton";
	rename -uid "8DA6F43D-481F-C265-0164-A6A45A81D9BA";
	addAttr -ci true -sn "liw" -ln "lockInfluenceWeights" -min 0 -max 1 -at "bool";
	addAttr -s false -ci true -k true -sn "male_average_root_bone" -ln "male_average_root_bone" 
		-at "message";
	setAttr ".uoc" 1;
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0.40000001 0.40000001 0.40000001 ;
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".bps" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".radi" 0.77114505347442108;
createNode lightLinker -s -n "lightLinker1";
	rename -uid "BF0F0B76-4258-4895-EAE9-C5A654DCFDDC";
	setAttr -s 3 ".lnk";
	setAttr -s 2 ".slnk";
createNode shapeEditorManager -n "shapeEditorManager";
	rename -uid "799A9E02-4EB4-4343-30A0-69814CDB1828";
createNode poseInterpolatorManager -n "poseInterpolatorManager";
	rename -uid "7789EC8E-412D-572E-2F09-7991C55690D3";
createNode displayLayerManager -n "layerManager";
	rename -uid "DE39CA24-4243-0AA4-D7EE-668296494385";
createNode displayLayer -n "defaultLayer";
	rename -uid "234A96BE-4EB7-C016-628D-A6921DA86D49";
	setAttr ".ufem" -type "stringArray" 0  ;
createNode renderLayerManager -n "renderLayerManager";
	rename -uid "75961279-44B5-C152-1E8B-4C9BF9714BED";
createNode renderLayer -n "defaultRenderLayer";
	rename -uid "95A160EB-4438-E653-7652-AEA996E2B5BB";
	setAttr ".g" yes;
createNode script -n "uiConfigurationScriptNode";
	rename -uid "467F4A71-415B-DDA5-3F28-E39B9D672A85";
	setAttr ".b" -type "string" (
		"// Maya Mel UI Configuration File.\n//\n//  This script is machine generated.  Edit at your own risk.\n//\n//\n\nglobal string $gMainPane;\nif (`paneLayout -exists $gMainPane`) {\n\n\tglobal int $gUseScenePanelConfig;\n\tint    $useSceneConfig = $gUseScenePanelConfig;\n\tint    $nodeEditorPanelVisible = stringArrayContains(\"nodeEditorPanel1\", `getPanel -vis`);\n\tint    $nodeEditorWorkspaceControlOpen = (`workspaceControl -exists nodeEditorPanel1Window` && `workspaceControl -q -visible nodeEditorPanel1Window`);\n\tint    $menusOkayInPanels = `optionVar -q allowMenusInPanels`;\n\tint    $nVisPanes = `paneLayout -q -nvp $gMainPane`;\n\tint    $nPanes = 0;\n\tstring $editorName;\n\tstring $panelName;\n\tstring $itemFilterName;\n\tstring $panelConfig;\n\n\t//\n\t//  get current state of the UI\n\t//\n\tsceneUIReplacement -update $gMainPane;\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Top View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Top View\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -camera \"|top\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 1\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n"
		+ "            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n"
		+ "            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n"
		+ "            -activeCustomLighSet \"defaultAreaLightSet\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Side View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Side View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n            -camera \"|side\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"wireframe\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n"
		+ "            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 1\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n"
		+ "            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n"
		+ "            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            -activeCustomLighSet \"defaultAreaLightSet\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Front View\")) `;\n\tif (\"\" != $panelName) {\n"
		+ "\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Front View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n            -camera \"|front\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 1\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 1\n            -jointXray 1\n            -activeComponentsXray 0\n            -displayTextures 0\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n"
		+ "            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n"
		+ "            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 0\n            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1\n            -height 1\n"
		+ "            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            -activeCustomLighSet \"defaultAreaLightSet\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"ModelPanel\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"ModelPanel\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n            -camera \"|persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n"
		+ "            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 0\n            -holdOuts 1\n            -selectionHiliteDisplay 0\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 1\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 1\n            -activeComponentsXray 0\n            -displayTextures 1\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n"
		+ "            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 0\n            -nurbsCurves 0\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 0\n            -lights 0\n            -cameras 0\n            -controlVertices 0\n            -hulls 0\n            -grid 0\n            -imagePlane 0\n            -joints 0\n            -ikHandles 0\n            -deformers 0\n            -dynamics 0\n"
		+ "            -particleInstancers 0\n            -fluids 0\n            -hairSystems 0\n            -follicles 0\n            -nCloths 0\n            -nParticles 0\n            -nRigids 0\n            -dynamicConstraints 0\n            -locators 0\n            -manipulators 0\n            -pluginShapes 0\n            -dimensions 0\n            -handles 0\n            -pivots 0\n            -textures 0\n            -strokes 0\n            -motionTrails 0\n            -clipGhosts 0\n            -bluePencil 0\n            -greasePencils 0\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1015\n            -height 721\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            -activeCustomLighSet \"defaultAreaLightSet\" \n            $editorName;\n        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n"
		+ "            -pluginObjects \"gpuCacheDisplayFilter\" 0 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner2\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner2\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 1\n            -showReferenceMembers 1\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n"
		+ "            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -showUfeItems 1\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n"
		+ "            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -selectCommand \"print(\\\"\\\")\" \n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"Outliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"Outliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -docTag \"isolOutln_fromSeln\" \n            -showShapes 0\n            -showAssignedMaterials 0\n"
		+ "            -showTimeEditor 1\n            -showReferenceNodes 0\n            -showReferenceMembers 0\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n"
		+ "            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -showUfeItems 1\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"graphEditor\" (localizedPanelLabel(\"Graph Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n"
		+ "\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Graph Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 1\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 1\n"
		+ "                -showCompounds 0\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 1\n                -doNotSelectNewObjects 0\n                -dropIsParent 1\n                -transmitFilters 1\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -showUfeItems 1\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n"
		+ "                -showPinIcons 1\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"GraphEd\");\n            animCurveEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -showPlayRangeShades \"on\" \n                -lockPlayRangeShades \"off\" \n                -smoothness \"fine\" \n                -resultSamples 1.25\n                -resultScreenSamples 0\n                -resultUpdate \"delayed\" \n                -showUpstreamCurves 1\n                -keyMinScale 1\n                -stackedCurvesMin -1\n                -stackedCurvesMax 1\n                -stackedCurvesSpace 0.2\n                -preSelectionHighlight 0\n                -constrainDrag 0\n                -valueLinesToggle 1\n                -outliner \"graphEditor1OutlineEd\" \n                -highlightAffectedCurves 0\n                $editorName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dopeSheetPanel\" (localizedPanelLabel(\"Dope Sheet\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dope Sheet\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"OutlineEd\");\n            outlinerEditor -e \n                -showShapes 1\n                -showAssignedMaterials 0\n                -showTimeEditor 1\n                -showReferenceNodes 0\n                -showReferenceMembers 0\n                -showAttributes 1\n                -showConnected 1\n                -showAnimCurvesOnly 1\n                -showMuteInfo 0\n                -organizeByLayer 1\n                -organizeByClip 1\n                -showAnimLayerWeight 1\n                -autoExpandLayers 1\n                -autoExpand 0\n                -showDagOnly 0\n                -showAssets 1\n                -showContainedOnly 0\n                -showPublishedAsConnected 0\n"
		+ "                -showParentContainers 0\n                -showContainerContents 0\n                -ignoreDagHierarchy 0\n                -expandConnections 1\n                -showUpstreamCurves 1\n                -showUnitlessCurves 0\n                -showCompounds 1\n                -showLeafs 1\n                -showNumericAttrsOnly 1\n                -highlightActive 0\n                -autoSelectNewObjects 0\n                -doNotSelectNewObjects 1\n                -dropIsParent 1\n                -transmitFilters 0\n                -setFilter \"0\" \n                -showSetMembers 0\n                -allowMultiSelection 1\n                -alwaysToggleSelect 0\n                -directSelect 0\n                -showUfeItems 1\n                -displayMode \"DAG\" \n                -expandObjects 0\n                -setsIgnoreFilters 1\n                -containersIgnoreFilters 0\n                -editAttrName 0\n                -showAttrValues 0\n                -highlightSecondary 0\n                -showUVAttrsOnly 0\n                -showTextureNodesOnly 0\n"
		+ "                -attrAlphaOrder \"default\" \n                -animLayerFilterOptions \"allAffecting\" \n                -sortOrder \"none\" \n                -longNames 0\n                -niceNames 1\n                -showNamespace 1\n                -showPinIcons 0\n                -mapMotionTrails 1\n                -ignoreHiddenAttribute 0\n                -ignoreOutlinerColor 0\n                -renderFilterVisible 0\n                $editorName;\n\n\t\t\t$editorName = ($panelName+\"DopeSheetEd\");\n            dopeSheetEditor -e \n                -displayValues 0\n                -snapTime \"integer\" \n                -snapValue \"none\" \n                -outliner \"dopeSheetPanel1OutlineEd\" \n                -showSummary 1\n                -showScene 0\n                -hierarchyBelow 0\n                -showTicks 1\n                -selectionWindow 0 0 0 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"timeEditorPanel\" (localizedPanelLabel(\"Time Editor\")) `;\n"
		+ "\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Time Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"clipEditorPanel\" (localizedPanelLabel(\"Trax Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Trax Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = clipEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 0 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"sequenceEditorPanel\" (localizedPanelLabel(\"Camera Sequencer\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n"
		+ "\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Camera Sequencer\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = sequenceEditorNameFromPanel($panelName);\n            clipEditor -e \n                -displayValues 0\n                -snapTime \"none\" \n                -snapValue \"none\" \n                -initialized 0\n                -manageSequencer 1 \n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperGraphPanel\" (localizedPanelLabel(\"Hypergraph Hierarchy\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypergraph Hierarchy\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"HyperGraphEd\");\n            hyperGraph -e \n                -graphLayoutStyle \"hierarchicalLayout\" \n                -orientation \"horiz\" \n                -mergeConnections 0\n                -zoom 1\n                -animateTransition 0\n                -showRelationships 1\n"
		+ "                -showShapes 0\n                -showDeformers 0\n                -showExpressions 0\n                -showConstraints 0\n                -showConnectionFromSelected 0\n                -showConnectionToSelected 0\n                -showConstraintLabels 0\n                -showUnderworld 0\n                -showInvisible 0\n                -transitionFrames 1\n                -opaqueContainers 0\n                -freeform 0\n                -image \"C:/work/Batman/characters/Bane/sourceimages/Bane_tpage_2048.tga\" \n                -imagePosition 0 0 \n                -imageScale 1\n                -imageEnabled 0\n                -graphType \"DAG\" \n                -heatMapDisplay 0\n                -updateSelection 1\n                -updateNodeAdded 1\n                -useDrawOverrideColor 0\n                -limitGraphTraversal -1\n                -range 0 0 \n                -iconSize \"smallIcons\" \n                -showCachedConnections 0\n                $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"hyperShadePanel\" (localizedPanelLabel(\"Hypershade\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Hypershade\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"visorPanel\" (localizedPanelLabel(\"Visor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Visor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"nodeEditorPanel\" (localizedPanelLabel(\"Node Editor\")) `;\n\tif ($nodeEditorPanelVisible || $nodeEditorWorkspaceControlOpen) {\n\t\tif (\"\" == $panelName) {\n\t\t\tif ($useSceneConfig) {\n\t\t\t\t$panelName = `scriptedPanel -unParent  -type \"nodeEditorPanel\" -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels `;\n"
		+ "\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n                -allAttributes 0\n                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -defaultPinnedState 0\n                -additiveGraphingMode 0\n                -connectedGraphingMode 1\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n                -gridSnap 0\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n"
		+ "                -useAssets 1\n                -syncedSelection 1\n                -extendToShapes 1\n                -showUnitConversions 0\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\t}\n\t\t} else {\n\t\t\t$label = `panel -q -label $panelName`;\n\t\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Node Editor\")) -mbv $menusOkayInPanels  $panelName;\n\n\t\t\t$editorName = ($panelName+\"NodeEditorEd\");\n            nodeEditor -e \n                -allAttributes 0\n                -allNodes 0\n                -autoSizeNodes 1\n                -consistentNameSize 1\n                -createNodeCommand \"nodeEdCreateNodeCommand\" \n                -connectNodeOnCreation 0\n                -connectOnDrop 0\n                -copyConnectionsOnPaste 0\n                -connectionStyle \"bezier\" \n                -defaultPinnedState 0\n                -additiveGraphingMode 0\n                -connectedGraphingMode 1\n                -settingsChangedCallback \"nodeEdSyncControls\" \n                -traversalDepthLimit -1\n"
		+ "                -keyPressCommand \"nodeEdKeyPressCommand\" \n                -nodeTitleMode \"name\" \n                -gridSnap 0\n                -gridVisibility 1\n                -crosshairOnEdgeDragging 0\n                -popupMenuScript \"nodeEdBuildPanelMenus\" \n                -showNamespace 1\n                -showShapes 1\n                -showSGShapes 0\n                -showTransforms 1\n                -useAssets 1\n                -syncedSelection 1\n                -extendToShapes 1\n                -showUnitConversions 0\n                -editorMode \"default\" \n                -hasWatchpoint 0\n                $editorName;\n\t\t\tif (!$useSceneConfig) {\n\t\t\t\tpanel -e -l $label $panelName;\n\t\t\t}\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"createNodePanel\" (localizedPanelLabel(\"Create Node\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Create Node\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"polyTexturePlacementPanel\" (localizedPanelLabel(\"UV Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"UV Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"renderWindowPanel\" (localizedPanelLabel(\"Render View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Render View\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"shapePanel\" (localizedPanelLabel(\"Shape Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tshapePanel -edit -l (localizedPanelLabel(\"Shape Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n"
		+ "\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"posePanel\" (localizedPanelLabel(\"Pose Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tposePanel -edit -l (localizedPanelLabel(\"Pose Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynRelEdPanel\" (localizedPanelLabel(\"Dynamic Relationships\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Dynamic Relationships\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"relationshipPanel\" (localizedPanelLabel(\"Relationship Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Relationship Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n"
		+ "\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"referenceEditorPanel\" (localizedPanelLabel(\"Reference Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Reference Editor\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"dynPaintScriptedPanelType\" (localizedPanelLabel(\"Paint Effects\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Paint Effects\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"scriptEditorPanel\" (localizedPanelLabel(\"Script Editor\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Script Editor\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"profilerPanel\" (localizedPanelLabel(\"Profiler Tool\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Profiler Tool\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"contentBrowserPanel\" (localizedPanelLabel(\"Content Browser\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Content Browser\")) -mbv $menusOkayInPanels  $panelName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextScriptedPanel \"Stereo\" (localizedPanelLabel(\"Stereo\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tscriptedPanel -edit -l (localizedPanelLabel(\"Stereo\")) -mbv $menusOkayInPanels  $panelName;\n"
		+ "{ string $editorName = ($panelName+\"Editor\");\n            stereoCameraView -e \n                -editorChanged \"updateModelPanelBar\" \n                -camera \"|persp\" \n                -useInteractiveMode 0\n                -displayLights \"default\" \n                -displayAppearance \"smoothShaded\" \n                -activeOnly 0\n                -ignorePanZoom 0\n                -wireframeOnShaded 0\n                -headsUpDisplay 1\n                -holdOuts 1\n                -selectionHiliteDisplay 1\n                -useDefaultMaterial 0\n                -bufferMode \"double\" \n                -twoSidedLighting 0\n                -backfaceCulling 0\n                -xray 0\n                -jointXray 0\n                -activeComponentsXray 0\n                -displayTextures 0\n                -smoothWireframe 0\n                -lineWidth 1\n                -textureAnisotropic 0\n                -textureHilight 1\n                -textureSampling 2\n                -textureDisplay \"modulate\" \n                -textureMaxSize 32768\n"
		+ "                -fogging 0\n                -fogSource \"fragment\" \n                -fogMode \"linear\" \n                -fogStart 0\n                -fogEnd 100\n                -fogDensity 0.1\n                -fogColor 0.5 0.5 0.5 1 \n                -depthOfFieldPreview 1\n                -maxConstantTransparency 1\n                -rendererOverrideName \"stereoOverrideVP2\" \n                -objectFilterShowInHUD 1\n                -isFiltered 0\n                -colorResolution 4 4 \n                -bumpResolution 4 4 \n                -textureCompression 0\n                -transparencyAlgorithm \"frontAndBackCull\" \n                -transpInShadows 0\n                -cullingOverride \"none\" \n                -lowQualityLighting 0\n                -maximumNumHardwareLights 0\n                -occlusionCulling 0\n                -shadingModel 0\n                -useBaseRenderer 0\n                -useReducedRenderer 0\n                -smallObjectCulling 0\n                -smallObjectThreshold -1 \n                -interactiveDisableShadows 0\n"
		+ "                -interactiveBackFaceCull 0\n                -sortTransparent 1\n                -controllers 1\n                -nurbsCurves 1\n                -nurbsSurfaces 1\n                -polymeshes 1\n                -subdivSurfaces 1\n                -planes 1\n                -lights 1\n                -cameras 1\n                -controlVertices 1\n                -hulls 1\n                -grid 1\n                -imagePlane 1\n                -joints 1\n                -ikHandles 1\n                -deformers 1\n                -dynamics 1\n                -particleInstancers 1\n                -fluids 1\n                -hairSystems 1\n                -follicles 1\n                -nCloths 1\n                -nParticles 1\n                -nRigids 1\n                -dynamicConstraints 1\n                -locators 1\n                -manipulators 1\n                -pluginShapes 1\n                -dimensions 1\n                -handles 1\n                -pivots 1\n                -textures 1\n                -strokes 1\n                -motionTrails 1\n"
		+ "                -clipGhosts 1\n                -bluePencil 1\n                -greasePencils 0\n                -shadows 0\n                -captureSequenceNumber -1\n                -width 0\n                -height 0\n                -sceneRenderFilter 0\n                -displayMode \"centerEye\" \n                -viewColor 0 0 0 1 \n                -useCustomBackground 1\n                $editorName;\n            stereoCameraView -e -viewSelected 0 $editorName;\n            stereoCameraView -e \n                -pluginObjects \"gpuCacheDisplayFilter\" 1 \n                $editorName; };\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"modelPanel\" (localizedPanelLabel(\"Persp View\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\tmodelPanel -edit -l (localizedPanelLabel(\"Persp View\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        modelEditor -e \n            -docTag \"RADRENDER\" \n            -editorChanged \"updateModelPanelBar\" \n"
		+ "            -camera \"|persp\" \n            -useInteractiveMode 0\n            -displayLights \"default\" \n            -displayAppearance \"smoothShaded\" \n            -activeOnly 0\n            -ignorePanZoom 0\n            -wireframeOnShaded 0\n            -headsUpDisplay 1\n            -holdOuts 1\n            -selectionHiliteDisplay 1\n            -useDefaultMaterial 0\n            -bufferMode \"double\" \n            -twoSidedLighting 0\n            -backfaceCulling 0\n            -xray 0\n            -jointXray 1\n            -activeComponentsXray 0\n            -displayTextures 1\n            -smoothWireframe 0\n            -lineWidth 1\n            -textureAnisotropic 0\n            -textureHilight 1\n            -textureSampling 2\n            -textureDisplay \"modulate\" \n            -textureMaxSize 32768\n            -fogging 0\n            -fogSource \"fragment\" \n            -fogMode \"linear\" \n            -fogStart 0\n            -fogEnd 100\n            -fogDensity 0.1\n            -fogColor 0.5 0.5 0.5 1 \n            -depthOfFieldPreview 1\n"
		+ "            -maxConstantTransparency 1\n            -rendererName \"vp2Renderer\" \n            -objectFilterShowInHUD 1\n            -isFiltered 0\n            -colorResolution 256 256 \n            -bumpResolution 512 512 \n            -textureCompression 0\n            -transparencyAlgorithm \"frontAndBackCull\" \n            -transpInShadows 0\n            -cullingOverride \"none\" \n            -lowQualityLighting 0\n            -maximumNumHardwareLights 1\n            -occlusionCulling 0\n            -shadingModel 0\n            -useBaseRenderer 0\n            -useReducedRenderer 0\n            -smallObjectCulling 0\n            -smallObjectThreshold -1 \n            -interactiveDisableShadows 0\n            -interactiveBackFaceCull 0\n            -sortTransparent 1\n            -controllers 1\n            -nurbsCurves 1\n            -nurbsSurfaces 1\n            -polymeshes 1\n            -subdivSurfaces 1\n            -planes 1\n            -lights 1\n            -cameras 1\n            -controlVertices 1\n            -hulls 1\n            -grid 1\n"
		+ "            -imagePlane 1\n            -joints 1\n            -ikHandles 1\n            -deformers 1\n            -dynamics 1\n            -particleInstancers 1\n            -fluids 1\n            -hairSystems 1\n            -follicles 1\n            -nCloths 1\n            -nParticles 1\n            -nRigids 1\n            -dynamicConstraints 1\n            -locators 1\n            -manipulators 1\n            -pluginShapes 1\n            -dimensions 1\n            -handles 1\n            -pivots 1\n            -textures 1\n            -strokes 1\n            -motionTrails 1\n            -clipGhosts 1\n            -bluePencil 1\n            -greasePencils 0\n            -shadows 0\n            -captureSequenceNumber -1\n            -width 1215\n            -height 722\n            -sceneRenderFilter 0\n            -activeShadingGraph \"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\" \n            -activeCustomGeometry \"meshShaderball\" \n            $editorName;\n"
		+ "        modelEditor -e -viewSelected 0 $editorName;\n        modelEditor -e \n            -pluginObjects \"gpuCacheDisplayFilter\" 1 \n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\t$panelName = `sceneUIReplacement -getNextPanel \"outlinerPanel\" (localizedPanelLabel(\"ToggledOutliner\")) `;\n\tif (\"\" != $panelName) {\n\t\t$label = `panel -q -label $panelName`;\n\t\toutlinerPanel -edit -l (localizedPanelLabel(\"ToggledOutliner\")) -mbv $menusOkayInPanels  $panelName;\n\t\t$editorName = $panelName;\n        outlinerEditor -e \n            -showShapes 0\n            -showAssignedMaterials 0\n            -showTimeEditor 1\n            -showReferenceNodes 1\n            -showReferenceMembers 1\n            -showAttributes 0\n            -showConnected 0\n            -showAnimCurvesOnly 0\n            -showMuteInfo 0\n            -organizeByLayer 1\n            -organizeByClip 1\n            -showAnimLayerWeight 1\n            -autoExpandLayers 1\n            -autoExpand 0\n            -showDagOnly 1\n            -showAssets 1\n"
		+ "            -showContainedOnly 1\n            -showPublishedAsConnected 0\n            -showParentContainers 0\n            -showContainerContents 1\n            -ignoreDagHierarchy 0\n            -expandConnections 0\n            -showUpstreamCurves 1\n            -showUnitlessCurves 1\n            -showCompounds 1\n            -showLeafs 1\n            -showNumericAttrsOnly 0\n            -highlightActive 1\n            -autoSelectNewObjects 0\n            -doNotSelectNewObjects 0\n            -dropIsParent 1\n            -transmitFilters 0\n            -setFilter \"defaultSetFilter\" \n            -showSetMembers 1\n            -allowMultiSelection 1\n            -alwaysToggleSelect 0\n            -directSelect 0\n            -isSet 0\n            -isSetMember 0\n            -showUfeItems 1\n            -displayMode \"DAG\" \n            -expandObjects 0\n            -setsIgnoreFilters 1\n            -containersIgnoreFilters 0\n            -editAttrName 0\n            -showAttrValues 0\n            -highlightSecondary 0\n            -showUVAttrsOnly 0\n"
		+ "            -showTextureNodesOnly 0\n            -attrAlphaOrder \"default\" \n            -animLayerFilterOptions \"allAffecting\" \n            -sortOrder \"none\" \n            -longNames 0\n            -niceNames 1\n            -showNamespace 1\n            -showPinIcons 0\n            -mapMotionTrails 0\n            -ignoreHiddenAttribute 0\n            -ignoreOutlinerColor 0\n            -renderFilterVisible 0\n            -renderFilterIndex 0\n            -selectionOrder \"chronological\" \n            -expandAttribute 0\n            $editorName;\n\t\tif (!$useSceneConfig) {\n\t\t\tpanel -e -l $label $panelName;\n\t\t}\n\t}\n\n\n\tif ($useSceneConfig) {\n        string $configName = `getPanel -cwl (localizedPanelLabel(\"Current Layout\"))`;\n        if (\"\" != $configName) {\n\t\t\tpanelConfiguration -edit -label (localizedPanelLabel(\"Current Layout\")) \n\t\t\t\t-userCreated false\n\t\t\t\t-defaultImage \"vacantCell.xP:/\"\n\t\t\t\t-image \"\"\n\t\t\t\t-sc false\n\t\t\t\t-configString \"global string $gMainPane; paneLayout -e -cn \\\"single\\\" -ps 1 100 100 $gMainPane;\"\n\t\t\t\t-removeAllPanels\n"
		+ "\t\t\t\t-ap true\n\t\t\t\t\t(localizedPanelLabel(\"Persp View\")) \n\t\t\t\t\t\"modelPanel\"\n"
		+ "\t\t\t\t\t\"$panelName = `modelPanel -unParent -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels `;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -docTag \\\"RADRENDER\\\" \\n    -editorChanged \\\"updateModelPanelBar\\\" \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 1\\n    -activeComponentsXray 0\\n    -displayTextures 1\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 32768\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -bluePencil 1\\n    -greasePencils 0\\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1215\\n    -height 722\\n    -sceneRenderFilter 0\\n    -activeShadingGraph \\\"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\\\" \\n    -activeCustomGeometry \\\"meshShaderball\\\" \\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t\t\"modelPanel -edit -l (localizedPanelLabel(\\\"Persp View\\\")) -mbv $menusOkayInPanels  $panelName;\\n$editorName = $panelName;\\nmodelEditor -e \\n    -docTag \\\"RADRENDER\\\" \\n    -editorChanged \\\"updateModelPanelBar\\\" \\n    -cam `findStartUpCamera persp` \\n    -useInteractiveMode 0\\n    -displayLights \\\"default\\\" \\n    -displayAppearance \\\"smoothShaded\\\" \\n    -activeOnly 0\\n    -ignorePanZoom 0\\n    -wireframeOnShaded 0\\n    -headsUpDisplay 1\\n    -holdOuts 1\\n    -selectionHiliteDisplay 1\\n    -useDefaultMaterial 0\\n    -bufferMode \\\"double\\\" \\n    -twoSidedLighting 0\\n    -backfaceCulling 0\\n    -xray 0\\n    -jointXray 1\\n    -activeComponentsXray 0\\n    -displayTextures 1\\n    -smoothWireframe 0\\n    -lineWidth 1\\n    -textureAnisotropic 0\\n    -textureHilight 1\\n    -textureSampling 2\\n    -textureDisplay \\\"modulate\\\" \\n    -textureMaxSize 32768\\n    -fogging 0\\n    -fogSource \\\"fragment\\\" \\n    -fogMode \\\"linear\\\" \\n    -fogStart 0\\n    -fogEnd 100\\n    -fogDensity 0.1\\n    -fogColor 0.5 0.5 0.5 1 \\n    -depthOfFieldPreview 1\\n    -maxConstantTransparency 1\\n    -rendererName \\\"vp2Renderer\\\" \\n    -objectFilterShowInHUD 1\\n    -isFiltered 0\\n    -colorResolution 256 256 \\n    -bumpResolution 512 512 \\n    -textureCompression 0\\n    -transparencyAlgorithm \\\"frontAndBackCull\\\" \\n    -transpInShadows 0\\n    -cullingOverride \\\"none\\\" \\n    -lowQualityLighting 0\\n    -maximumNumHardwareLights 1\\n    -occlusionCulling 0\\n    -shadingModel 0\\n    -useBaseRenderer 0\\n    -useReducedRenderer 0\\n    -smallObjectCulling 0\\n    -smallObjectThreshold -1 \\n    -interactiveDisableShadows 0\\n    -interactiveBackFaceCull 0\\n    -sortTransparent 1\\n    -controllers 1\\n    -nurbsCurves 1\\n    -nurbsSurfaces 1\\n    -polymeshes 1\\n    -subdivSurfaces 1\\n    -planes 1\\n    -lights 1\\n    -cameras 1\\n    -controlVertices 1\\n    -hulls 1\\n    -grid 1\\n    -imagePlane 1\\n    -joints 1\\n    -ikHandles 1\\n    -deformers 1\\n    -dynamics 1\\n    -particleInstancers 1\\n    -fluids 1\\n    -hairSystems 1\\n    -follicles 1\\n    -nCloths 1\\n    -nParticles 1\\n    -nRigids 1\\n    -dynamicConstraints 1\\n    -locators 1\\n    -manipulators 1\\n    -pluginShapes 1\\n    -dimensions 1\\n    -handles 1\\n    -pivots 1\\n    -textures 1\\n    -strokes 1\\n    -motionTrails 1\\n    -clipGhosts 1\\n    -bluePencil 1\\n    -greasePencils 0\\n    -shadows 0\\n    -captureSequenceNumber -1\\n    -width 1215\\n    -height 722\\n    -sceneRenderFilter 0\\n    -activeShadingGraph \\\"ballora_animatronic_shadow_rig:rsMaterial1SG,ballora_animatronic_shadow_rig:MAT_ballora,ballora_animatronic_shadow_rig:MAT_ballora\\\" \\n    -activeCustomGeometry \\\"meshShaderball\\\" \\n    $editorName;\\nmodelEditor -e -viewSelected 0 $editorName;\\nmodelEditor -e \\n    -pluginObjects \\\"gpuCacheDisplayFilter\\\" 1 \\n    $editorName\"\n"
		+ "\t\t\t\t$configName;\n\n            setNamedPanelLayout (localizedPanelLabel(\"Current Layout\"));\n        }\n\n        panelHistory -e -clear mainPanelHistory;\n        sceneUIReplacement -clear;\n\t}\n\n\ngrid -spacing 5 -size 12 -divisions 5 -displayAxes yes -displayGridLines yes -displayDivisionLines yes -displayPerspectiveLabels no -displayOrthographicLabels no -displayAxesBold yes -perspectiveLabelPosition axis -orthographicLabelPosition edge;\nviewManip -drawCompass 0 -compassAngle 0 -frontParameters \"\" -homeParameters \"\" -selectionLockParameters \"\";\n}\n");
	setAttr ".st" 3;
createNode script -n "sceneConfigurationScriptNode";
	rename -uid "4448A2AD-45AE-3AE2-552E-569526B83626";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 100 -ast 1 -aet 200 ";
	setAttr ".st" 6;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve1";
	rename -uid "279CB500-4344-1371-514A-B5B7DBB8C682";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve1";
	rename -uid "B4F91BFF-4957-84D1-17D8-CDAAC0CC36EF";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo1";
	rename -uid "9FB5729E-49FC-FB0D-D0F8-DDA47C723A81";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve2";
	rename -uid "B24864EF-4F3D-88CB-23F6-21B76A0BA649";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve2";
	rename -uid "F8B04062-4C91-CD2A-66E8-ABB1DFD769D4";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo2";
	rename -uid "444C26F0-40F4-0096-C63E-BFAAF5A8DDFB";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve3";
	rename -uid "EEE00F8C-4725-A0FA-1A10-73A8EB2EF8D7";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve3";
	rename -uid "0AE2BA44-4EFA-56A5-6966-298D90CDABD8";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo3";
	rename -uid "E753C2C5-40D8-B46B-F022-758980D87D3B";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve4";
	rename -uid "0F076BE1-48F9-0719-EC8B-E782C1D291B5";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve4";
	rename -uid "C4728FEB-4714-548E-2AF5-7DBBEAEF2221";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo4";
	rename -uid "DF6B034D-4F31-CC19-BB41-D091E46679C1";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve5";
	rename -uid "8F1F5FE3-4297-FACE-6C99-1E990D9A091E";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve5";
	rename -uid "06C42C4C-47FE-AC89-3A3A-0381488048F6";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo5";
	rename -uid "C0071C1A-4CCE-0A9B-5B58-DD9BC7F8949D";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve6";
	rename -uid "718522E6-4A96-3345-1E10-EEB825485DD6";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve6";
	rename -uid "E518F7CF-4451-84A9-7A72-B3B5E73C1471";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo7";
	rename -uid "2309AD6F-40AC-52E8-C3F4-DAA4CC07BC2B";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo8";
	rename -uid "F378CFAF-4F4A-69EA-9076-9DBC8EDA47EE";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo9";
	rename -uid "362DCFCD-4BC7-DBA9-D7C5-79B13CAF084C";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo10";
	rename -uid "F17EE0C0-433B-8A6B-0E38-B68A81E431CF";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo11";
	rename -uid "451D35BE-4E00-34F6-0B6B-90947ED6841C";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve7";
	rename -uid "65C9DBA0-4DF1-FB52-4F60-68ADA3D21937";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve7";
	rename -uid "F360FDD1-43B2-B157-DEFE-5190D9027042";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo13";
	rename -uid "DDC00723-4E6D-1316-AF3A-7F80382D6605";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo14";
	rename -uid "6293A5E1-42B8-B9D6-D11C-1499CF62E4C3";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo15";
	rename -uid "74156F2D-4867-5EDE-78D3-9ABA268BD5A0";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo16";
	rename -uid "7C456DF8-4DE2-3C75-FF08-658021778FBD";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo17";
	rename -uid "EBFCD6F9-43C3-C136-31BE-61923C98B23A";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve8";
	rename -uid "ABE730BE-4C3B-26C2-E4F1-A8A7DB13CB10";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve8";
	rename -uid "94A341F3-4094-4574-B6CA-1BBC438ED47C";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo19";
	rename -uid "BCDFA5B7-453A-FE7D-BF9A-3E9C57B72FFD";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo20";
	rename -uid "53FD8842-4341-51CD-32D7-D5851AD82DB9";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo21";
	rename -uid "541E10DC-42D6-A424-FF28-50BD59B73A29";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo22";
	rename -uid "FBDB2985-44B3-FE95-1E0A-8E963715E68A";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo23";
	rename -uid "2CF3F5C4-429D-86E0-186F-8287324ACA53";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve9";
	rename -uid "2F7A2403-40F2-9329-FCDE-78BA04D56CBB";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve9";
	rename -uid "1E9E0CF3-42C4-5099-652C-619BB98D8EDF";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo25";
	rename -uid "E20F62EC-4771-1A5E-3930-D1B0DDCC0CCB";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo26";
	rename -uid "5B9069B9-42E9-3032-CFB2-4A9823928D03";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo27";
	rename -uid "E36ED562-484D-3D7A-F9FC-7FB32735C193";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo28";
	rename -uid "B5B1150C-462A-4599-6D21-F29AD68383D3";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo29";
	rename -uid "BCAA5B55-4910-0AD6-03BB-6583CB4B21A9";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve10";
	rename -uid "86CC291B-47B4-5CB1-65C8-A982AB8FB9EA";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve10";
	rename -uid "D014C650-455E-A8D2-1295-329FEC09AA66";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo31";
	rename -uid "38258F08-4038-F207-BD6F-E185177EA599";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo32";
	rename -uid "9587B602-447A-FF7D-6B00-FEA3FD255210";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo33";
	rename -uid "1F248175-42D6-9E5D-2888-1EA4B1FF2632";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo34";
	rename -uid "352505E4-4895-6FEA-9869-B78705F142DE";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo35";
	rename -uid "E210CAAC-482B-5394-B6A0-EDAB1ABE953B";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve11";
	rename -uid "31E434DC-48E5-C5ED-1A51-97BEFC3191C5";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve11";
	rename -uid "AAFE791F-4E02-EA20-DBEA-839A83F9CDDA";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo37";
	rename -uid "5DB4503C-4ECF-6933-8247-4EAD56D229CD";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo38";
	rename -uid "05C2A40C-4B16-E26F-70E0-CC8E457D77FB";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo39";
	rename -uid "F15A4C26-43A9-5438-1E24-CF8CB57A05D5";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo40";
	rename -uid "D78B6D2F-4618-DF2F-5A37-1CB454EC695A";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo41";
	rename -uid "26977651-4D71-1394-6D60-BF9D967AA7CC";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve12";
	rename -uid "6A51AD33-498C-7F6F-F75E-0D83977C3DA5";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve12";
	rename -uid "E234EB4B-432C-A113-D4AC-DD9A59A8374E";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo43";
	rename -uid "755B96DD-41F5-B5F4-710F-6296CBECEC7D";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo44";
	rename -uid "D901E25E-40AD-C4A1-A2BF-B491B50BF62D";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo45";
	rename -uid "4E33960E-41CD-0C90-8CCD-1CA73CF27172";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo46";
	rename -uid "979202CB-492E-CF1B-D5EE-35AC58F96AAB";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo47";
	rename -uid "4C87963C-4F87-A458-A24C-AB8ABF005273";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve13";
	rename -uid "F339D536-4933-FFF1-9329-6FA49EBF15B2";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve13";
	rename -uid "DCE7E588-483D-DAA1-C799-DDB93DD1A836";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo48";
	rename -uid "5E642578-46A3-DC3D-6FCC-AC84F62B2C98";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve14";
	rename -uid "26E248B6-4AB5-CFCB-BF12-72824E7F8660";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve14";
	rename -uid "A3F82730-4B7E-4E68-8597-878F4AC84876";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo49";
	rename -uid "7CF7A660-4A98-CD28-EB68-1EA3C793218B";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve15";
	rename -uid "4E724D7D-40F0-B41F-4F01-369795378288";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve15";
	rename -uid "33715BB0-4C35-762B-DEFC-A3AAED0E2E15";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo50";
	rename -uid "AD48F493-442D-BFD2-734C-C9A261B53DA6";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve16";
	rename -uid "E689A9A8-4C29-A271-BFFC-05844540E97A";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve16";
	rename -uid "2CE90513-4B17-EDD7-494A-3BACC94D97F0";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo51";
	rename -uid "8B4FE970-4E93-A33E-301C-39849B3D357E";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve17";
	rename -uid "49EE0484-4161-ECD6-88B8-E795E9C88597";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve17";
	rename -uid "8FFAF047-41AC-3D2E-79E7-ABA8242D148B";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo52";
	rename -uid "25F95425-4F34-8015-BBBC-57B84911093E";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve18";
	rename -uid "338820ED-4F64-E17B-A841-CBB569404DB2";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve18";
	rename -uid "E5AFC6C3-4E7E-3C83-3FF4-2B861C1459F5";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo53";
	rename -uid "3AE844AE-42AA-76D7-FA60-A58CF914D975";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve19";
	rename -uid "1EAF2801-49E2-5CB6-CEDB-7A9F68E9AA2B";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve19";
	rename -uid "E8A1616A-4401-8B0D-ABFC-43B983C8A98F";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo54";
	rename -uid "67F357C1-47CA-7648-3695-B18D291DCBED";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo55";
	rename -uid "B07AE024-41A6-2E13-5814-EC85C4B76367";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo56";
	rename -uid "331910C1-4ECE-31B3-C67A-0BAB03C3BEA7";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo57";
	rename -uid "7E73AB56-4788-AA1E-8BC0-DCBF65A6463E";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo58";
	rename -uid "E85C23BA-4B7E-E12C-A14E-7BB4F87096E0";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve20";
	rename -uid "86C2335F-4669-2F7D-2E68-56A5357D8F2F";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve20";
	rename -uid "FFB57E27-456C-C947-EF51-78A242F70557";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo59";
	rename -uid "7494406E-4DD5-110E-4754-CD8E337DCCE4";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo60";
	rename -uid "F09A0B97-4AB9-302E-7CBE-2389906437B1";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo61";
	rename -uid "1ACAE2BD-4288-D599-48C9-8FBACABB4C9C";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo62";
	rename -uid "3E029B69-4C28-CB24-3324-2AA1ECD4C3D4";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo63";
	rename -uid "9AAE0810-4A38-E649-8121-2796D9DDFB6A";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve21";
	rename -uid "E2B52645-4016-E740-3BFD-DBA47C87DDFE";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve21";
	rename -uid "1B142B65-4E67-4DF0-74B9-E5989F59391B";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo64";
	rename -uid "3336E1F7-4847-FEED-51B0-A9A50EE455EE";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo65";
	rename -uid "7718EE8C-4F06-9AEC-A4A5-B288A5E74512";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo66";
	rename -uid "C411D66C-4F63-7BCF-72F9-D4AAFC239A6E";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo67";
	rename -uid "483A1A65-4434-C6D9-ECC6-B2B68854055D";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo68";
	rename -uid "6AB2AA41-4DC9-4A9C-C4D4-F0A49FD4160C";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve22";
	rename -uid "DC6416A7-4F3E-8055-8484-D8A4F40D4D6D";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve22";
	rename -uid "AE7EE560-457C-B329-41F4-8BB0DD477211";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo69";
	rename -uid "04F03F92-47D0-10BB-1803-5781FB41DAD7";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo70";
	rename -uid "47A352C2-4F49-A2D2-A7C2-22AB960DC8F9";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo71";
	rename -uid "6A3A8757-489B-011C-5BBD-63B5123B2BF9";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo72";
	rename -uid "BEFD59EC-4B06-55D7-AB83-A9AD70DBBEB1";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo73";
	rename -uid "0FB8DD5F-4008-8200-D495-1ABFAC997068";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve23";
	rename -uid "4352EE87-4140-AED2-E823-3C8429DBEA39";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve23";
	rename -uid "E1CCF830-4E6E-412C-5AF8-38A2518A3FEB";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo74";
	rename -uid "DCC7C4AF-489F-5D78-C857-06912340D7B8";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo75";
	rename -uid "30409001-4A71-6B0E-AF3A-7F95980609C9";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo76";
	rename -uid "1840BB3C-4669-33C5-406F-C4B79C2959BD";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo77";
	rename -uid "D57F8254-46B0-2EB7-0921-7FA31B4D9B41";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo78";
	rename -uid "11E1FA34-4C85-8848-A1D0-1086BF8EF17F";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve24";
	rename -uid "80DC9A04-4AA2-9743-67EF-14883815C52C";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve24";
	rename -uid "90B3D0B7-4CDB-F595-E66E-A2995D9F6BC2";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo79";
	rename -uid "8FC1C0D2-49DD-1A18-B6F2-B99728B72C4D";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo80";
	rename -uid "B15AE521-4623-A539-69FE-16AC1279AF5E";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo81";
	rename -uid "19DEA398-47F2-7EFA-4F7E-C9981FE79008";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo82";
	rename -uid "F675296B-4ED5-BCB4-A03C-45A6D4727705";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo83";
	rename -uid "8C334213-44D0-8A9A-F539-15BEB75F321D";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode pointOnCurveInfo -n "left_open_finger_ctrl_start_pointOnCurve25";
	rename -uid "5F50B8C3-4F0D-7F5E-FAC2-0F9323CD5AD1";
createNode pointOnCurveInfo -n "right_open_finger_ctrl_start_pointOnCurve25";
	rename -uid "3C85AAC7-44FB-50B5-3E2C-26B4E4B8A334";
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo84";
	rename -uid "E0BB6993-4AE5-4477-E144-29B937DD8B94";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo85";
	rename -uid "FCB35700-4542-B93B-7C1F-0EB5D10903C1";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo86";
	rename -uid "F11C09F7-4342-2EEF-CE50-85ACFA1D041A";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo87";
	rename -uid "FCB2AEA2-4516-E110-D627-B1986D3331DB";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo88";
	rename -uid "74C15578-4F6B-B2A0-992F-688B970FAFDF";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode network -n "male_average";
	rename -uid "976422B4-43D4-949F-5525-2F95DC53E92B";
	addAttr -ci true -k true -sn "version" -ln "version" -dv 1 -at "float";
	addAttr -s false -ci true -k true -m -sn "system_subs" -ln "system_subs" -at "message";
	addAttr -ci true -k true -sn "isMetaRig" -ln "isMetaRig" -dt "string";
	addAttr -ci true -k true -sn "isCharacter" -ln "isCharacter" -dt "string";
	addAttr -s false -ci true -k true -sn "root_bone" -ln "root_bone" -at "message";
	addAttr -s false -ci true -k true -sn "end_bone" -ln "end_bone" -at "message";
	addAttr -s false -ci true -k true -sn "system_parent" -ln "system_parent" -at "message";
	addAttr -s false -ci true -k true -sn "driver_hook" -ln "driver_hook" -at "message";
	addAttr -s false -ci true -k true -m -sn "hooks" -ln "hooks" -at "message";
	addAttr -s false -ci true -k true -m -sn "twisters" -ln "twisters" -at "message";
	addAttr -s false -ci true -k true -sn "node_container" -ln "node_container" -at "message";
	addAttr -s false -ci true -k true -m -sn "controls" -ln "controls" -at "message";
	addAttr -s false -ci true -k true -m -sn "system_controls" -ln "system_controls" 
		-at "message";
	addAttr -s false -ci true -k true -sn "rig_setup" -ln "rig_setup" -at "message";
	addAttr -s false -ci true -k true -sn "control_setup" -ln "control_setup" -at "message";
	addAttr -s false -ci true -k true -sn "untouchables_setup" -ln "untouchables_setup" 
		-at "message";
	addAttr -s false -ci true -k true -m -sn "systems" -ln "systems" -at "message";
	addAttr -s false -ci true -k true -m -sn "build_systems" -ln "build_systems" -at "message";
	addAttr -ci true -k true -sn "export_dict" -ln "export_dict" -dt "string";
	addAttr -s false -ci true -k true -sn "left_arm_root_bone" -ln "left_arm_root_bone" 
		-at "message";
	addAttr -s false -ci true -k true -sn "right_arm_root_bone" -ln "right_arm_root_bone" 
		-at "message";
	addAttr -s false -ci true -k true -sn "left_leg_root_bone" -ln "left_leg_root_bone" 
		-at "message";
	addAttr -s false -ci true -k true -sn "right_leg_root_bone" -ln "right_leg_root_bone" 
		-at "message";
	addAttr -s false -ci true -k true -sn "hip_control" -ln "hip_control" -at "message";
	setAttr -k on ".isMetaRig" -type "string" "";
	setAttr -k on ".isCharacter" -type "string" "";
	setAttr -k on ".export_dict" -type "string" "";
createNode dagPose -n "tpose";
	rename -uid "9D65E007-42C9-4353-83DD-E1B07FEA5055";
	setAttr -s 178 ".wm";
	setAttr ".wm[0]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[1]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 102.52082335847703 0 1;
	setAttr ".wm[2]" -type "matrix" 0 1 0 0 -1.2246467991473532e-16 0 -1 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415816 100.46989749000251 0 1;
	setAttr ".wm[3]" -type "matrix" 6.4093061293237171e-18 0.99862953475457383 0.05233595624294389 0
		 -1.2229684632711994e-16 0.05233595624294389 -0.99862953475457383 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415789 55.984585689940623 4.8744477902171874e-15 1;
	setAttr ".wm[4]" -type "matrix" 6.4093061293237171e-18 0.99862953475457383 0.05233595624294389 0
		 -1.2229684632711994e-16 0.05233595624294389 -0.99862953475457383 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415789 40.402669470304573 -0.81661362604552923 1;
	setAttr ".wm[5]" -type "matrix" 6.4093061293237171e-18 0.99862953475457383 0.05233595624294389 0
		 -1.2229684632711994e-16 0.05233595624294389 -0.99862953475457383 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415787 24.820753250668524 -1.633227252091054 1;
	setAttr ".wm[6]" -type "matrix" 6.4093061293237171e-18 0.99862953475457383 0.05233595624294389 0
		 -1.2229684632711994e-16 0.05233595624294389 -0.99862953475457383 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415785 9.2387371680788064 -2.4498461117322128 1;
	setAttr ".wm[7]" -type "matrix" 1.6948183510607676e-32 0.99999999999999989 1.3877787807814457e-16 0
		 -1.2246467991473532e-16 1.3877787807814457e-16 -0.99999999999999989 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415798 9.2384958469890961 -2.4498587588346052 1;
	setAttr ".wm[8]" -type "matrix" -1.9598161121821213e-06 0.018673377209548449 -0.99982563728869689 0
		 -2.28704092113567e-18 -0.99982563729061691 -0.01867337720958431 0 -0.99999999999807954 -3.6596385521911168e-08 1.9594743933349514e-06 0
		 -10.250846483915229 2.8973800023554874 10.782285554981877 1;
	setAttr ".wm[9]" -type "matrix" 0 1 0 0 -1.2246467991473532e-16 0 -1 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415814 100.46989749000251 -2.2204460492503131e-15 1;
	setAttr ".wm[10]" -type "matrix" 0 1 0 0 -1.2246467991473532e-16 0 -1 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415816 85.641567490002558 -2.1689999449292514e-15 1;
	setAttr ".wm[11]" -type "matrix" 0 1 0 0 -1.2246467991473532e-16 0 -1 0 -1 0 1.2246467991473532e-16 0
		 -10.250824075415814 70.81323749000255 -2.1175538406081885e-15 1;
	setAttr ".wm[12]" -type "matrix" -1.2246467991473532e-16 -1 0 0 0 0 1 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415816 100.46989749000251 0 1;
	setAttr ".wm[13]" -type "matrix" -1.2229684632711994e-16 -0.99862953475457383 -0.05233595624294389 0
		 -6.4093061293237171e-18 -0.05233595624294389 0.99862953475457383 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415842 55.984585689940424 -1.5465679670191926e-15 1;
	setAttr ".wm[14]" -type "matrix" -1.2229684632711994e-16 -0.99862953475457383 -0.05233595624294389 0
		 -6.4093061293237171e-18 -0.05233595624294389 0.99862953475457383 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415803 40.402669211258228 -0.81659322923952848 1;
	setAttr ".wm[15]" -type "matrix" -1.2229684632711994e-16 -0.99862953475457383 -0.05233595624294389 0
		 -6.4093061293237171e-18 -0.05233595624294389 0.99862953475457383 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415821 24.820753525531526 -1.6332170428193924 1;
	setAttr ".wm[16]" -type "matrix" -1.2229684632711994e-16 -0.99862953475457383 -0.05233595624294389 0
		 -6.4093061293237171e-18 -0.05233595624294389 0.99862953475457383 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415832 9.2387379768548854 -2.4498460900601917 1;
	setAttr ".wm[17]" -type "matrix" -1.2246467991473532e-16 -0.99999999999999989 9.7144514654701197e-17 0
		 1.2325951644078309e-32 9.7144514654701197e-17 0.99999999999999989 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415883 9.2384958469890535 -2.4498587588346212 1;
	setAttr ".wm[18]" -type "matrix" -7.8444957394317385e-06 -0.018673504796262074 0.99982563487694587 0
		 1.2244332634951955e-16 0.99982563490770859 0.018673504796836726 0 -0.99999999996923195 1.4648422894146617e-07 -7.8431279332058645e-06 0
		 10.2509066185055 2.8973805318404073 10.782285808483374 1;
	setAttr ".wm[19]" -type "matrix" -1.2246467991473532e-16 -1 0 0 0 0 1 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415814 100.46989749000245 -2.1191937094044988e-12 1;
	setAttr ".wm[20]" -type "matrix" -1.2246467991473532e-16 -1 0 0 0 0 1 0 -1 1.2246467991473532e-16 0 0
		 10.25082407541583 85.64156749000594 1.0201698696894876e-05 1;
	setAttr ".wm[21]" -type "matrix" -1.2246467991473532e-16 -1 0 0 0 0 1 0 -1 1.2246467991473532e-16 0 0
		 10.250824075415837 70.813237490009485 2.0403399513871639e-05 1;
	setAttr ".wm[22]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 108.93333709138719 0 1;
	setAttr ".wm[23]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 122.69739043611375 -9.1715364335046153e-17 1;
	setAttr ".wm[24]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 135.36052214998094 -1.1994634513325542e-14 1;
	setAttr ".wm[25]" -type "matrix" 0.9282927426960923 0 -0.37185021696614173 0 -0.37185021696614173 0 -0.9282927426960923 0
		 0 1 0 0 3.0000000000000004 152.48148675698707 -3.0968872820961243e-15 1;
	setAttr ".wm[26]" -type "matrix" 1 0 5.5511151231257827e-17 0 5.5511151231257827e-17 0 -1 0
		 0 1 0 0 17.281219774144503 152.48148675698755 -5.7206896351826506 1;
	setAttr ".wm[27]" -type "matrix" 0.99999390765779039 0 0.0034906514152237876 0 0.0034906514152237876 0 -0.99999390765779039 0
		 0 1 0 0 47.631869391267315 152.48148675698766 -5.720689635181575 1;
	setAttr ".wm[28]" -type "matrix" 1 0 5.5511151231257827e-17 0 5.5511151231257827e-17 0 -1 0
		 0 1 0 0 76.892350881397249 152.48148675698653 -5.6185508717936852 1;
	setAttr ".wm[29]" -type "matrix" 0.82139380484326951 -0.42261826174069966 0.38302222155948928 0
		 -0.3496866299470392 0.15737869562426263 0.92355357559802065 0 -0.45059014436778294 -0.89253893528903028 -0.018514070102097047 0
		 79.925357891549112 150.72893214465597 -2.4402200443671545 1;
	setAttr ".wm[30]" -type "matrix" 0.82139380484326951 -0.42261826174069966 0.38302222155948928 0
		 -0.3496866299470392 0.15737869562426263 0.92355357559802065 0 -0.45059014436778294 -0.89253893528903028 -0.018514070102097047 0
		 82.751910404915066 149.27463251045668 -1.1221769612074228 1;
	setAttr ".wm[31]" -type "matrix" 0.82139380484326951 -0.42261826174069966 0.38302222155948928 0
		 -0.3496866299470392 0.15737869562426263 0.92355357559802065 0 -0.45059014436778294 -0.89253893528903028 -0.018514070102097047 0
		 84.967637096572361 148.13461105254015 -0.088966636509029584 1;
	setAttr ".wm[32]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 81.44935088139664 152.20448675698691 -9.346550871793605 1;
	setAttr ".wm[33]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 84.757784714494051 151.89205402043652 -8.9796764956476469 1;
	setAttr ".wm[34]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 87.495407019922851 151.89205402043649 -8.9796764956473893 1;
	setAttr ".wm[35]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 89.789743365589757 151.89205402043663 -8.979676495647384 1;
	setAttr ".wm[36]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 81.552350881396606 153.24148675698675 -7.5085508717935898 1;
	setAttr ".wm[37]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 85.190870295968949 153.10541380964716 -7.508937711985447 1;
	setAttr ".wm[38]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 89.050841914281449 153.10541380964736 -7.5089377119854559 1;
	setAttr ".wm[39]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 91.778956671687908 153.1054138096473 -7.5089377119853884 1;
	setAttr ".wm[40]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 81.641350881396548 153.95148675698692 -5.2485508717935598 1;
	setAttr ".wm[41]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 85.791055874931402 153.99129669865368 -5.2457988277610959 1;
	setAttr ".wm[42]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 90.18645276636046 153.99129669865354 -5.2457988277611163 1;
	setAttr ".wm[43]" -type "matrix" 1 0 5.5511151231257827e-17 0 -2.4651903288156619e-32 1 4.4408920985006262e-16 0
		 -5.5511151231257827e-17 -4.4408920985006262e-16 1 0 92.789803451589023 153.991296698654 -5.2457988277611003 1;
	setAttr ".wm[44]" -type "matrix" 1 0 5.5511151231257827e-17 0 -1.2325951644078309e-32 1 2.2204460492503131e-16 0
		 -5.5511151231257827e-17 -2.2204460492503131e-16 1 0 81.704350881396508 153.71548675698656 -3.0815508717935853 1;
	setAttr ".wm[45]" -type "matrix" 1 0 5.5511151231257827e-17 0 -1.2325951644078309e-32 1 2.2204460492503131e-16 0
		 -5.5511151231257827e-17 -2.2204460492503131e-16 1 0 85.588492714921372 153.77367406464072 -3.0735658195466771 1;
	setAttr ".wm[46]" -type "matrix" 1 0 5.5511151231257827e-17 0 -1.2325951644078309e-32 1 2.2204460492503131e-16 0
		 -5.5511151231257827e-17 -2.2204460492503131e-16 1 0 89.422290377367617 153.77367406464089 -3.0735658195466709 1;
	setAttr ".wm[47]" -type "matrix" 1 0 5.5511151231257827e-17 0 -1.2325951644078309e-32 1 2.2204460492503131e-16 0
		 -5.5511151231257827e-17 -2.2204460492503131e-16 1 0 91.773227967718711 153.773674064641 -3.0735658195466375 1;
	setAttr ".wm[48]" -type "matrix" 1 0 5.5511151231257827e-17 0 5.5511151231257827e-17 0 -1 0
		 0 1 0 0 85.892350881396638 146.48148675698681 -5.6185508717936106 1;
	setAttr ".wm[49]" -type "matrix" 1 0 5.5511151231257827e-17 0 5.5511151231257827e-17 0 -1 0
		 0 1 0 0 85.892350881396879 146.48148675698715 -5.6185508717936292 1;
	setAttr ".wm[50]" -type "matrix" 0.99999390765779039 0 0.0034906514152237876 0 0.0034906514152237876 0 -0.99999390765779039 0
		 0 1 0 0 76.892691123242315 152.4814867569867 -5.6185496841206941 1;
	setAttr ".wm[51]" -type "matrix" 0.99999390765779039 0 0.0034906514152237876 0 0.0034906514152237876 0 -0.99999390765779039 0
		 0 1 0 0 67.138750547948234 152.4814867569867 -5.6525974980248064 1;
	setAttr ".wm[52]" -type "matrix" 0.99999390765779039 0 0.0034906514152237876 0 0.0034906514152237876 0 -0.99999390765779039 0
		 0 1 0 0 57.385809966561794 152.48148675698664 -5.6866418212774859 1;
	setAttr ".wm[53]" -type "matrix" 1 0 5.5511151231257827e-17 0 5.5511151231257827e-17 0 -1 0
		 0 1 0 0 17.2812197741445 152.48148675698783 -5.7206896351826595 1;
	setAttr ".wm[54]" -type "matrix" 1 0 5.5511151231257827e-17 0 5.5511151231257827e-17 0 -1 0
		 0 1 0 0 27.398219774144454 152.48148675698778 -5.7206896351826444 1;
	setAttr ".wm[55]" -type "matrix" 1 0 5.5511151231257827e-17 0 5.5511151231257827e-17 0 -1 0
		 0 1 0 0 37.515219774144484 152.48148675698783 -5.7206896351826568 1;
	setAttr ".wm[56]" -type "matrix" 0.92829274269609252 1.1102230246251565e-16 0.37185021696614134 0
		 -0.37185021696614134 -1.3877787807814459e-16 0.92829274269609241 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -3.0000000000000102 152.48148675698698 2.3345208779416607e-14 1;
	setAttr ".wm[57]" -type "matrix" 1 1.5466578172682261e-16 -6.106226635438361e-16 0
		 6.6613381477509392e-16 -8.7542829807937659e-17 1 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -17.28121977414439 152.4814867569869 -5.7206896351826018 1;
	setAttr ".wm[58]" -type "matrix" 0.99999390765779039 1.5497042095271398e-16 -0.0034906514152243428 0
		 0.0034906514152243983 -8.7002412137189058e-17 0.99999390765779039 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -47.631869391267131 152.48148675698695 -5.7206896351816177 1;
	setAttr ".wm[59]" -type "matrix" 1 1.5466578172682256e-16 -1.227316859253591e-16 0
		 1.7824283715661693e-16 -8.7542829807937746e-17 1 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -76.892350881396311 152.48148675698644 -5.6185508717937012 1;
	setAttr ".wm[60]" -type "matrix" -0.82139380484326963 -0.42261826174069977 0.38302222155948923 0
		 0.34968662994703914 0.15737869562426263 0.92355357559802043 0 -0.450590144367783 0.89253893528903039 0.018514070102096991 0
		 -79.925357891549083 150.72893214465608 -2.4402200443673565 1;
	setAttr ".wm[61]" -type "matrix" -0.82139380484326963 -0.42261826174069977 0.38302222155948923 0
		 0.34968662994703914 0.15737869562426263 0.92355357559802043 0 -0.450590144367783 0.89253893528903039 0.018514070102096991 0
		 -82.751910404914753 149.27463251045643 -1.1221769612076682 1;
	setAttr ".wm[62]" -type "matrix" -0.82139380484326963 -0.42261826174069977 0.38302222155948923 0
		 0.34968662994703914 0.15737869562426263 0.92355357559802043 0 -0.450590144367783 0.89253893528903039 0.018514070102096991 0
		 -84.96763709657256 148.13461105254109 -0.088966636509208774 1;
	setAttr ".wm[63]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -81.449350881396413 152.20448675698677 -9.3465508717937595 1;
	setAttr ".wm[64]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -84.757784714493653 151.89205402043606 -8.9796764956476629 1;
	setAttr ".wm[65]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -87.495407019922297 151.89205402043578 -8.979676495647519 1;
	setAttr ".wm[66]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -89.789743365589331 151.89205402043592 -8.9796764956474711 1;
	setAttr ".wm[67]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -81.552350881396336 153.24148675698686 -7.5085508717937079 1;
	setAttr ".wm[68]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -85.190870295968907 153.1054138096469 -7.5089377119856842 1;
	setAttr ".wm[69]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -89.050841914281534 153.10541380964696 -7.5089377119856193 1;
	setAttr ".wm[70]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -91.778956671687922 153.10541380964696 -7.5089377119855625 1;
	setAttr ".wm[71]" -type "matrix" -1 -3.2201101812087243e-17 1.227316859253591e-16 0
		 -9.9579925010295913e-17 1.0000000000000002 4.7184478546569153e-16 0 -1.7824283715661698e-16 5.3163203965800045e-16 -1 0
		 -81.641350881396434 153.95148675698692 -5.2485508717937241 1;
	setAttr ".wm[72]" -type "matrix" -1 -3.2201101812087243e-17 1.227316859253591e-16 0
		 -9.9579925010295913e-17 1.0000000000000002 4.7184478546569153e-16 0 -1.7824283715661698e-16 5.3163203965800045e-16 -1 0
		 -85.791055874931132 153.99129669865363 -5.2457988277612166 1;
	setAttr ".wm[73]" -type "matrix" -1 -3.2201101812087243e-17 1.227316859253591e-16 0
		 -9.9579925010295913e-17 1.0000000000000002 4.7184478546569153e-16 0 -1.7824283715661698e-16 5.3163203965800045e-16 -1 0
		 -90.186452766360404 153.99129669865331 -5.2457988277611909 1;
	setAttr ".wm[74]" -type "matrix" -1 -3.2201101812087243e-17 1.227316859253591e-16 0
		 -9.9579925010295913e-17 1.0000000000000002 4.7184478546569153e-16 0 -1.7824283715661698e-16 5.3163203965800045e-16 -1 0
		 -92.789803451588909 153.99129669865349 -5.245798827761365 1;
	setAttr ".wm[75]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -81.704350881396465 153.71548675698693 -3.0815508717937359 1;
	setAttr ".wm[76]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -85.588492714921173 153.77367406464006 -3.0735658195468099 1;
	setAttr ".wm[77]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -89.422290377367133 153.77367406464015 -3.0735658195467974 1;
	setAttr ".wm[78]" -type "matrix" -1 -1.5466578172682256e-16 2.4519636584009445e-16 0
		 -2.2204460492503131e-16 1.0000000000000002 2.775557561562892e-17 0 -3.0070751707135227e-16 8.7542829807937721e-17 -1 0
		 -91.773227967718427 153.77367406464015 -3.0735658195466766 1;
	setAttr ".wm[79]" -type "matrix" 1 1.5466578172682256e-16 -1.227316859253591e-16 0
		 1.7824283715661693e-16 -8.7542829807937746e-17 1 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -85.892350881396368 146.48148675698693 -5.6185508717937154 1;
	setAttr ".wm[80]" -type "matrix" 1 1.5466578172682256e-16 -1.227316859253591e-16 0
		 1.7824283715661693e-16 -8.7542829807937746e-17 1 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -85.892350881396467 146.48148675698707 -5.6185508717937509 1;
	setAttr ".wm[81]" -type "matrix" 0.99999390765779039 1.5497042095271398e-16 -0.0034906514152243428 0
		 0.0034906514152243983 -8.7002412137189058e-17 0.99999390765779039 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -57.38580996656124 152.48148675698624 -5.6866418212775134 1;
	setAttr ".wm[82]" -type "matrix" 0.99999390765779039 1.5497042095271398e-16 -0.0034906514152243428 0
		 0.0034906514152243983 -8.7002412137189058e-17 0.99999390765779039 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -67.138750547947453 152.48148675698624 -5.652597498024809 1;
	setAttr ".wm[83]" -type "matrix" 0.99999390765779039 1.5497042095271398e-16 -0.0034906514152243428 0
		 0.0034906514152243983 -8.7002412137189058e-17 0.99999390765779039 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -76.892691123241988 152.48148675698644 -5.618549684120743 1;
	setAttr ".wm[84]" -type "matrix" 1 1.5466578172682261e-16 -6.106226635438361e-16 0
		 6.6613381477509392e-16 -8.7542829807937659e-17 1 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -17.281219774144517 152.48148675698707 -5.7206896351826204 1;
	setAttr ".wm[85]" -type "matrix" 1 1.5466578172682261e-16 -6.106226635438361e-16 0
		 6.6613381477509392e-16 -8.7542829807937659e-17 1 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -27.398219774144493 152.48148675698681 -5.7206896351826124 1;
	setAttr ".wm[86]" -type "matrix" 1 1.5466578172682261e-16 -6.106226635438361e-16 0
		 6.6613381477509392e-16 -8.7542829807937659e-17 1 0 2.2204460492503131e-16 -1.0000000000000002 -2.775557561562892e-17 0
		 -37.515219774144541 152.48148675698684 -5.7206896351826089 1;
	setAttr ".wm[87]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 157.50266702114919 -4.0901220894534918 1;
	setAttr ".wm[88]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 163.71862529303183 -2.3517326116629924 1;
	setAttr ".wm[89]" -type "matrix" 0 0.99987202616752791 0.015997852594718635 0 0 -0.015997852594718635 0.99987202616752791 0
		 1 0 0 0 0 169.93458356491448 -0.61334313387248329 1;
	setAttr ".wm[90]" -type "matrix" 0 -0.74317002357032025 0.66910261998178566 0 0 -0.66910261998178566 -0.74317002357032025 0
		 1 0 0 0 -3.7617570592466878e-30 172.59621656826224 2.4219002499454723 1;
	setAttr ".wm[91]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.00038016863982193183 173.76652117275478 -1.9793420473600123 1;
	setAttr ".wm[92]" -type "matrix" 1 0 0 0 0 0.89879404994745782 -0.43837113930897276 0
		 0 0.43837113930897276 0.89879404994745782 0 3.1145354407199193 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[93]" -type "matrix" 1 0 0 0 0 0.89879404994745782 -0.43837113930897276 0
		 0 0.43837113930897276 0.89879404994745782 0 -3.1145352227322292 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[94]" -type "matrix" 1 0 0 0 0 0.95630478759499338 -0.29237160125924394 0
		 0 0.29237160125924394 0.95630478759499338 0 3.1145354407199193 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[95]" -type "matrix" 1 0 0 0 0 0.95630478759499338 -0.29237160125924394 0
		 0 0.29237160125924394 0.95630478759499338 0 -3.1145352227322292 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[96]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 1.771983136452036 175.80749103680017 9.1094165061963093 1;
	setAttr ".wm[97]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -1.8346883160702419 175.85418293273401 9.0757727856050696 1;
	setAttr ".wm[98]" -type "matrix" 0.70710678118654746 2.9424051220847856e-08 -0.70710678118654702 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 0.70710678118654768 -2.9424051220847849e-08 0.7071067811865468 0
		 4.7177437441714574 176.26134848988647 8.3592973157929436 1;
	setAttr ".wm[99]" -type "matrix" 0.70710682826502747 -2.9424049261823087e-08 0.70710673410806391 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 -0.70710673410806457 -2.9424053179872489e-08 0.7071068282650268 0
		 -4.7177440030209254 176.26134848988647 8.3592973157929436 1;
	setAttr ".wm[100]" -type "matrix" 1 0 0 0 0 0.98480774000571258 0.17364825143041546 0
		 0 -0.17364825143041546 0.98480774000571258 0 0.014948141790227965 168.18984078969552 10.580414146466676 1;
	setAttr ".wm[101]" -type "matrix" 1 0 0 0 0 0.9961947046198304 -0.087155668131274608 0
		 0 0.087155668131274594 0.9961947046198304 0 -0.08542726279119961 172.37153141026388 11.678945642158972 1;
	setAttr ".wm[102]" -type "matrix" 0.87542610384625508 0.23456973120763089 0.42261824133104509 0
		 -0.14434548178757922 0.96132276271448514 -0.23456966507735219 0 -0.4612954786165559 0.14434537432203826 0.87542612156580812 0
		 -1.8122304891876411 169.41694775328011 9.8613740144363184 1;
	setAttr ".wm[103]" -type "matrix" 0.85672027232130288 0.21360435010389528 0.46947157167437209 0
		 -0.089316058252099706 0.95790282739228394 -0.2728457714757106 0 -0.50798918958184547 0.19182115339701367 0.83973306971764483 0
		 -4.9136492116085719 178.02507713725814 7.6683927718752969 1;
	setAttr ".wm[104]" -type "matrix" 0.96592582198108812 0.066987296027185561 0.25000001720225046 0
		 -0.0090326678882680679 0.97406230094856983 -0.22609963463393323 0 -0.25866139515006786 0.21613730830595637 0.94147700270228385 0
		 0.83738185375113972 171.9615373719555 11.010316026819664 1;
	setAttr ".wm[105]" -type "matrix" 0.71397790464362321 -0.087665492422094454 0.69465841470401324 0
		 0.00029082330565945868 0.9921677706260994 0.1249120904982411 0 -0.70016817058654279 -0.088982449782120429 0.70841136109485581 0
		 -3.5644663674465846 168.92854289811561 7.3554622862346921 1;
	setAttr ".wm[106]" -type "matrix" 0.99026806874157025 5.7912560859831699e-09 -0.13917310096006544 0
		 -0.016960934433661517 0.99254615666318236 -0.12068327803089517 0 0.13813572576990221 0.12186930250536955 0.98288676579394285 0
		 1.8322424786456395 178.03611489126902 9.4113994785724184 1;
	setAttr ".wm[107]" -type "matrix" 0.94422277401706367 -0.17136375218483366 0.28120778343540936 0
		 0.039307209028531992 0.90648125829976578 0.42041250179991158 0 -0.32695304914606388 -0.3859095655570205 0.86265607913332598 0
		 4.9164775731333066 168.13766656116462 5.0382054652149524 1;
	setAttr ".wm[108]" -type "matrix" 0.90673602740601722 0.40370488433265039 0.12186936846441655 0
		 -0.36029276119458359 0.89181925445958321 -0.27358279113631395 0 -0.21913215837648545 0.2041587219325067 0.95409659543682901 0
		 -2.2843517167202663 173.87921623256796 8.6052212126396679 1;
	setAttr ".wm[109]" -type "matrix" 0.69555866798052424 0.22600071389231385 -0.68199839935099804 0
		 -0.1429226911306615 0.97379089199456537 0.17693050338592917 0 0.70411024971742053 -0.025592498678192323 0.70962932595424655 0
		 4.2916873591311742 173.40383570646637 6.4832719969962262 1;
	setAttr ".wm[110]" -type "matrix" 0.73443118078693848 0.4240240945780131 -0.52991924658876055 0
		 0.14743947022835763 0.66247440751579678 0.7344312507004146 0 0.66247448502314754 -0.6175202236395908 0.42402397348431281 0
		 3.2327471869357396 165.43979978485535 2.7427550029999561 1;
	setAttr ".wm[111]" -type "matrix" 0.93740357733598856 0.065549621595868093 0.34202014605331343 0
		 -0.015524236039380745 0.98901461758516374 -0.14700028672851573 0 -0.34789873712487795 0.13248899317117155 0.9281234483598636 0
		 -3.5927947861782741 178.52538511910251 8.9891649637147335 1;
	setAttr ".wm[112]" -type "matrix" 0.71539913001836131 -0.3889177926820217 0.58047139059932618 0
		 0.25490217490126915 0.91878289179766348 0.30143470100591552 0 -0.65056050141364596 -0.06768270292524442 0.75643247268025093 0
		 -3.0096341250173282 167.10466267043387 8.5752099079313684 1;
	setAttr ".wm[113]" -type "matrix" 0.90673602647945972 -0.40370488392012166 -0.121869376724761 0
		 0.36029276640937297 0.89181926218200891 -0.27358275909533897 0 0.21913215363638805 0.20415868901464468 0.95409660356931358 0
		 2.3607870238192845 173.88232898566818 8.6680788406377722 1;
	setAttr ".wm[114]" -type "matrix" 0.73443118078693848 -0.4240240945780131 0.52991924658876055 0
		 -0.14743947022835763 0.66247440751579678 0.7344312507004146 0 -0.66247448502314754 -0.6175202236395908 0.42402397348431281 0
		 -3.2327469689480495 165.43979978485535 2.7427550029999561 1;
	setAttr ".wm[115]" -type "matrix" 0.94584652918820311 0.099412463270238519 0.3090169985116889 0
		 -0.04957415415337664 0.98502189983680344 -0.16514920551389714 0 -0.32080640028310986 0.14088654651327659 0.93660783391393621 0
		 -1.1393774961761665 169.59750507330637 10.35059213775623 1;
	setAttr ".wm[116]" -type "matrix" 0.97442545380217871 -0.085251172007195633 -0.20791169436522211 0
		 0.15839811145451679 0.91686749194040829 0.36642057872143013 0 0.15938968997416511 -0.38998235843984641 0.90692264655572175 0
		 -6.453878532134695 178.32781589562549 5.4615637134280046 1;
	setAttr ".wm[117]" -type "matrix" 0.95994432019227605 0.050308538586853822 0.27563735791043303 0
		 -0.037858255867236297 0.99801593475782346 -0.050308512521824215 0 -0.27762142315260901 0.037858221230304981 0.95994432155828557 0
		 -3.6542927128903102 175.31957315701791 8.6214985858079913 1;
	setAttr ".wm[118]" -type "matrix" 1 0 0 0 0 0.99619470171846003 -0.087155701294111543 0
		 0 0.087155701294111543 0.99619470171846003 0 -0.041902507626218721 177.97529858808539 9.7764211816691766 1;
	setAttr ".wm[119]" -type "matrix" 0.96498034594513504 0.077809484014521507 -0.2505166983196957 0
		 -0.029774010774635696 0.98131248599427146 0.19010342741290737 0 0.26062701360756785 -0.17598718427526644 0.94926396263044976 0
		 0.94328918776591308 168.31242991659198 10.206220006365207 1;
	setAttr ".wm[120]" -type "matrix" 0.96592582198108801 -0.066987296027185797 -0.25000001720225062 0
		 0.0090326625065730737 0.97406229645162823 -0.22609965422225348 0 0.25866139533800125 0.21613732857224457 0.94147699799806672 0
		 -0.87500588686089031 171.97288564885827 11.016587648231509 1;
	setAttr ".wm[121]" -type "matrix" 0.91354545764260087 1.6925081384703515e-08 -0.40673664307579988 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 0.40673664307580026 -3.8014355191365776e-08 0.91354545764260009 0
		 2.5314910197921563 168.84117929147655 9.6460364755999368 1;
	setAttr ".wm[122]" -type "matrix" 0.93740357679045994 -0.065549629397294959 -0.34202014605331293 0
		 0.015524244270334366 0.98901461745596519 -0.14700028672851542 0 0.34789873822750089 0.1324889902758265 0.92812344835986382 0
		 3.6284381049044896 178.56402036949629 9.0736376215721695 1;
	setAttr ".wm[123]" -type "matrix" 1 0 0 0 0 0.98480775734770531 -0.17364815307910161 0
		 0 0.17364815307910161 0.98480775734770531 0 -0.0073873297951649874 169.67822742300788 10.641410832368818 1;
	setAttr ".wm[124]" -type "matrix" 0.9774671443599704 0.12001787514891858 0.17364818266110177 0
		 -0.13642722674428939 0.98692478629871783 0.085831684080485027 0 -0.16107635922017555 -0.10758799112339876 0.98106025842779121 0
		 -3.4994620186917018 176.96872277732871 9.486275265760197 1;
	setAttr ".wm[125]" -type "matrix" 1 0 0 0 0 0.86602539130087086 -0.50000002162217294 0
		 0 0.50000002162217294 0.86602539130087086 0 -0.13011744149844168 177.31936226162074 0.36751588665900403 1;
	setAttr ".wm[126]" -type "matrix" 0.99862953475457317 -0.052335956242942072 -3.9576109935451767e-08 0
		 0.05226422966783472 0.99726094974688873 -0.052335918900514852 0 0.0027390898292204919 0.052264192274159314 0.99862953671160615 0
		 6.4925340311892796 174.37365085215515 1.2130741690048978 1;
	setAttr ".wm[127]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.046596166648669168 171.38232070330628 10.799784642063496 1;
	setAttr ".wm[128]" -type "matrix" 1 0 0 0 0 0.83867058154349994 0.54463901407582582 0
		 0 -0.54463901407582582 0.83867058154349994 0 -3.1145352227322292 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[129]" -type "matrix" 0.89013135954335165 0.10402083765963599 -0.44367310949627314 0
		 -0.019244036206298283 0.98131111324198339 0.19146322387933862 0 0.45529751792426348 -0.16188935839136157 0.87549757613121826 0
		 1.6927850516804028 168.45688488522356 9.9039777333235151 1;
	setAttr ".wm[130]" -type "matrix" 1 0 0 0 0 0.96592583275103816 -0.25881902098611959 0
		 0 0.25881902098611959 0.96592583275103816 0 -0.018618152447743341 174.63550720197705 10.463572951568812 1;
	setAttr ".wm[131]" -type "matrix" 1 0 0 0 0 0.7880107689780248 0.61566145565128738 0
		 0 -0.61566145565128738 0.7880107689780248 0 -3.1145352227322292 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[132]" -type "matrix" 0.62874115819630405 0.13364309064319305 -0.7660444375578388 0
		 -0.074637665313063775 0.99094421093259255 0.11161894882051428 0 0.77402440200977207 -0.013003658812687974 0.63302221916051093 0
		 4.2770880358584691 169.61404502510172 5.56080746856823 1;
	setAttr ".wm[133]" -type "matrix" 0.70362049981358643 0.67947840974252394 0.20791171909214184 0
		 -0.66270976692613681 0.73307699385874292 -0.1530159661464576 0 -0.25638634336248167 -0.030119956321336454 0.96610497937254014 0
		 -2.5626086098782253 170.97410173108534 9.6738770594645196 1;
	setAttr ".wm[134]" -type "matrix" 1 0 0 0 0 0.34202026063282914 0.9396925780895854 0
		 0 -0.9396925780895854 0.34202026063282914 0 0.0016029672988224775 164.66795110346064 7.2301986367154782 1;
	setAttr ".wm[135]" -type "matrix" 1 0 0 0 0 0.7986355250728896 0.60181500321240733 0
		 0 -0.60181500321240733 0.7986355250728896 0 3.1145354407199193 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[136]" -type "matrix" 1 0 0 0 0 0.83867058154349994 0.54463901407582582 0
		 0 -0.54463901407582582 0.83867058154349994 0 3.1145354407199193 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[137]" -type "matrix" 0.62874115819630538 -0.13364309064319316 0.76604443755783758 0
		 0.074637678196511528 0.99094421114903508 0.11161893828401369 0 -0.77402440076744505 -0.013003642318663159 0.63302222101838246 0
		 -4.1869007451168727 169.38217246268414 5.652762643856093 1;
	setAttr ".wm[138]" -type "matrix" 0.9774671443599704 -0.12001787514891858 -0.17364818266110177 0
		 0.13642722674428939 0.98692478629871783 0.085831684080485027 0 0.16107635922017555 -0.10758799112339876 0.98106025842779121 0
		 3.4594067232974339 176.99704308960267 9.4917073958449105 1;
	setAttr ".wm[139]" -type "matrix" 1 0 0 0 0 0.76604441637136866 0.64278764156309764 0
		 0 -0.64278764156309764 0.76604441637136866 0 -0.092878448747796938 171.85448184627302 2.0039652346792098 1;
	setAttr ".wm[140]" -type "matrix" 0.85672027232130255 -0.21360435010389572 -0.46947157167437253 0
		 0.089316075162812203 0.95790283377791596 -0.27284574352140634 0 0.50798918660855774 0.19182112150889566 0.83973307880054671 0
		 4.8900741236575413 178.10691002238883 7.6830879428219685 1;
	setAttr ".wm[141]" -type "matrix" 0.71397790464362254 0.08766549242209469 -0.69465841470401402 0
		 -0.0002908116515303456 0.99216776914500782 0.12491210228957628 0 0.70016817059138414 -0.088982466296511992 0.70841135901572361 0
		 3.6371160643466283 169.03472881070564 7.3673794049111017 1;
	setAttr ".wm[142]" -type "matrix" 0.94584652918820311 -0.099412463270238519 -0.3090169985116889 0
		 0.04957415415337664 0.98502189983680344 -0.16514920551389714 0 0.32080640028310986 0.14088654651327659 0.93660783391393621 0
		 1.1652576709457207 169.5545973607866 10.294743060653378 1;
	setAttr ".wm[143]" -type "matrix" 0.94177633515080683 -0.16606058167669757 -0.29237171163283221 0
		 0.14789266666743472 0.98548514431491052 -0.083347402362729986 0 0.30196869654967579 0.035254979050009717 0.95266572981097264 0
		 3.5393220084079076 177.00784774317134 9.4820094821709695 1;
	setAttr ".wm[144]" -type "matrix" 0.94422276319391074 0.17136377285163759 -0.28120780718271027 0
		 -0.039307217692565406 0.90648125672735991 0.42041250438022837 0 0.32695307936112983 -0.38590956007339156 0.86265607013469514 0
		 -4.6801286814443301 168.06883465903485 4.9930573226046011 1;
	setAttr ".wm[145]" -type "matrix" 1 0 0 0 0 0.99619469446502928 0.087155784201204622 0
		 0 -0.087155784201204622 0.99619469446502928 0 -1.0842021724855044e-19 176.46973767964408 10.581535865113834 1;
	setAttr ".wm[146]" -type "matrix" 0.69555866798052435 -0.22600071389231352 0.68199839935099793 0
		 0.14292266769117329 0.97379089114260298 0.17693052700914411 0 -0.704110254475247 -0.025592531095217679 0.70962932006431578 0
		 -4.2028509480587672 173.34556238859486 6.5418905401035907 1;
	setAttr ".wm[147]" -type "matrix" 0.97442545451167129 0.085251163897658314 0.20791169436522206 0
		 -0.15839810382399869 0.91686749325865702 0.36642057872143069 0 -0.15938969321974572 -0.38998235711334572 0.90692264655572163 0
		 6.4538782732852269 178.32781589562549 5.4615637134280046 1;
	setAttr ".wm[148]" -type "matrix" 0.96498034945387479 -0.077809492380588 0.25051668220570228 0
		 0.029774022095477623 0.98131248549216488 0.19010342823170706 0 -0.26062699932304717 -0.175987183376134 0.94926396671905711 0
		 -1.0105417696468066 168.28958750864643 10.223498676679338 1;
	setAttr ".wm[149]" -type "matrix" 1 0 0 0 0 0.49999990630391233 0.86602545787989327 0
		 0 -0.86602545787989327 0.49999990630391233 0 -1.0842021724855044e-19 164.09664480698794 4.4403052438922028 1;
	setAttr ".wm[150]" -type "matrix" 0.89013137248178376 -0.10402085418997307 0.4436730796625869 0
		 0.019244058870619619 0.98131111218187206 0.19146322703475305 0 -0.45529749167097328 -0.16188935419590014 0.87549759055987941 0
		 -1.7157107321254443 168.34902050869454 9.8234427938373781 1;
	setAttr ".wm[151]" -type "matrix" 0.97437007227374584 -9.3606376956012923e-09 0.22495102190755908 0
		 -0.031307131283010756 0.99026806309874271 0.1356061456479489 0 -0.22276181402584139 -0.13917314111086349 0.96488756391884956 0
		 6.8346847193606663 172.06106148205683 3.1918462361647877 1;
	setAttr ".wm[152]" -type "matrix" 0.87542609025688078 -0.23456972756636757 -0.42261827150159004 0
		 0.14434547424494368 0.96132276473552825 -0.23456966143609073 0 0.46129550676605763 0.14434536677940174 0.8754261079764335 0
		 1.7999315047927666 169.35731640658886 9.8381835136028926 1;
	setAttr ".wm[153]" -type "matrix" 1 0 0 0 0 0.9848077573477052 0.17364815307910247 0
		 0 -0.17364815307910247 0.9848077573477052 0 -0.05311459579388611 166.47335596937953 8.7191788682721789 1;
	setAttr ".wm[154]" -type "matrix" 1 0 0 0 0 0.8660253580113535 0.50000007928130064 0
		 0 -0.50000007928130064 0.8660253580113535 0 -1.0842021724855044e-19 160.08921479695337 2.3635264429762581 1;
	setAttr ".wm[155]" -type "matrix" 0.91354545764260087 -1.6925081384703515e-08 0.40673664307579988 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 -0.40673664307580026 -3.8014355191365776e-08 0.91354545764260009 0
		 -2.5757444118789863 168.80141489147064 9.5429175774609813 1;
	setAttr ".wm[156]" -type "matrix" 0.71539913126990617 0.38891780180380614 -0.58047138294523948 0
		 -0.25490218984138613 0.9187828885475019 0.30143469827870595 0 0.65056049418353823 -0.067682694630193135 0.75643247964062632 0
		 2.9995044591196347 167.12135566804915 8.6167748440589165 1;
	setAttr ".wm[157]" -type "matrix" 0.99862953475457328 0.052335956242945202 -3.2291161408623606e-08 0
		 -0.052264233423922869 0.99726094955004052 -0.052335918900514873 0 -0.0027390181587973873 0.052264196030247047 0.99862953671160637 0
		 -6.9118086201779079 174.37102055875485 1.2138194653737164 1;
	setAttr ".wm[158]" -type "matrix" 0.97437006104097956 9.360639723674812e-09 -0.22495107056201727 0
		 0.031307138054402522 0.99026806309874282 0.13560614408464977 0 0.22276186220679772 -0.13917314111086276 0.96488755279539973 0
		 -6.8346849782101344 172.06106148205683 3.1918462361647877 1;
	setAttr ".wm[159]" -type "matrix" 0.94177633791484494 0.16606056600105948 0.29237171163283154 0
		 -0.14789265026427426 0.98548514677654786 -0.083347402362729694 0 -0.30196869596286452 0.035254984076205059 0.95266572981097286 0
		 -3.551861177169485 176.98221297645708 9.5082479225715453 1;
	setAttr ".wm[160]" -type "matrix" 0.99026806874157025 -5.7912560859831699e-09 0.13917310096006544 0
		 0.016960934433661517 0.99254615666318236 -0.12068327803089517 0 -0.13813572576990221 0.12186930250536955 0.98288676579394285 0
		 -1.7928798300854396 178.02796669884231 9.3889852707748407 1;
	setAttr ".wm[161]" -type "matrix" 0.70362049981358643 -0.67947840974252383 -0.20791171909214209 0
		 0.66270976265864834 0.73307699436008233 -0.15301598222703985 0 0.25638635439312463 -0.030119944119448405 0.96610497682562646 0
		 2.5626088278659154 170.97410173108534 9.6738770594645196 1;
	setAttr ".wm[162]" -type "matrix" 0.95994432019227605 -0.050308538586853822 -0.27563735791043303 0
		 0.037858255867236297 0.99801593475782346 -0.050308512521824215 0 0.27762142315260901 0.037858221230304981 0.95994432155828557 0
		 3.5844067232974339 175.32527994621347 8.5714268697368681 1;
	setAttr ".wm[163]" -type "matrix" 0.99999999999940736 8.3402239379980313e-07 6.9982829647245243e-07 0
		 -8.7947943066558237e-09 0.64895493692797401 -0.76082684615936702 0 -1.0887036554986818e-06 0.76082684615890983 0.64895493692759676 0
		 0.011626862018601969 169.77436345792032 3.7983193717464538 1;
	setAttr ".wm[164]" -type "matrix" 0.99999999999486266 -1.0688120739184e-06 -3.0219734489605814e-06 0
		 -3.3268375403896346e-09 0.94242489550192177 -0.33441787682208579 0 3.2054128763278593e-06 0.33441787682037782 0.94242489549707664 0
		 -3.3677978403788295e-07 168.3316332826171 4.1731307138167875 1;
	setAttr ".wm[165]" -type "matrix" 0.999999999984304 -1.8705601604285777e-06 -5.2813842311484129e-06 0
		 1.4469124627593517e-06 0.99686626012934376 -0.079105369056985855 0 5.4128050986450052e-06 0.079105369048102517 0.99686626011640345 0
		 3.8303996476991256e-06 168.3939380935831 6.3178394608422916 1;
	setAttr ".wm[166]" -type "matrix" 0.999999999984304 -1.8705601604285777e-06 -5.2813842311484002e-06 0
		 1.9131637042039094e-06 0.99996737004042247 0.0080782950416859473 0 5.26610096292526e-06 -0.0080782950516633065 0.9999673700283056 0
		 5.8269205086332473e-06 168.38575269098476 8.0548277855297634 1;
	setAttr ".wm[167]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.0016852495900820941 168.35958567689514 7.2708162992640215 1;
	setAttr ".wm[168]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.0016852495900820941 170.31915431178149 7.2708161191249232 1;
	setAttr ".wm[169]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 3.1145354407199193 176.31920961673305 7.4668221900267611 1;
	setAttr ".wm[170]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -3.1145352227322292 176.31920961673043 7.4668231437010775 1;
	setAttr ".wm[171]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[172]" -type "matrix" 0 -1 0 0 0 0 1 0 -1 0 0 0 10.250824075415883 9.2384958469890677 -2.4498587588346212 1;
	setAttr ".wm[173]" -type "matrix" -2.2204460492503131e-16 1 0 0 2.2204460492503131e-16 0 -1 0
		 -1 -2.2204460492503131e-16 -2.2204460492503131e-16 0 -10.250824075415798 9.2384958469891103 -2.4498587588346052 1;
	setAttr ".wm[174]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[175]" -type "matrix" 1 0 0 0 0 7.7715611723760958e-16 -1 0 0 1 7.7715611723760958e-16 0
		 76.892426183969576 152.46379243127296 -5.6183477607361212 1;
	setAttr ".wm[176]" -type "matrix" 1 0 0 0 0 0 1 0 0 -1 0 0 -76.892426183968894 152.46379243127274 -5.6183477607361239 1;
	setAttr ".wm[177]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 178 ".xm";
	setAttr ".xm[0]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[1]" -type "matrix" "xform" 1 1 1 0 0 0 1 0 102.52082335847703 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.50000000000000011 0.50000000000000011 0.50000000000000011 0.50000000000000011 1
		 1 1 yes;
	setAttr ".xm[2]" -type "matrix" "xform" 1 1 1 0 0 0 1 -2.050925868474522 0 -10.250824075415816 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -1 0 0 6.123233995736766e-17 1 1 1 yes;
	setAttr ".xm[3]" -type "matrix" "xform" 1 1 1 0 0 0 0 -44.485311800061886 -4.8744477902171905e-15
		 -2.6645352591003757e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.026176948307873173 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[4]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 -5.5511151231257827e-17
		 -5.5511151231257827e-17 0 -15.603300000000011 7.1054273576010019e-15 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[5]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 -5.5511151231257827e-17
		 -5.5511151231257827e-17 0 -31.206600000000016 5.3290705182007514e-15 -1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[6]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 -5.5511151231257827e-17
		 -5.5511151231257827e-17 0 -46.810000000000215 3.1086244689504383e-15 -3.5527136788005009e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[7]" -type "matrix" "xform" 1 1 1 0 0 0 1 -46.810241652265958 -1.0658141036401503e-14
		 8.8817841970012523e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.026176948307873104 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[8]" -type "matrix" "xform" 1 1 1 -1.9058241313221761e-21 5.505714157152953e-21
		 1.8175355256292058e-27 0 -6.3411158446336078 -13.232144313816484 2.2408499432913231e-05 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 6.863997566199437e-07 -6.9933909685157904e-07 0.700473633618523 0.71367828088313223 1
		 1 1 yes;
	setAttr ".xm[9]" -type "matrix" "xform" 1 1 1 -3.3306690738754701e-16 1.110223024625157e-16
		 -1.1102230246251565e-16 1 0 2.2204460492503127e-15 -1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[10]" -type "matrix" "xform" 1 1 1 -3.3306690738754701e-16 1.110223024625157e-16
		 -1.1102230246251565e-16 1 -14.828329999999951 2.1689999449292514e-15 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[11]" -type "matrix" "xform" 1 1 1 -3.3306690738754701e-16 1.110223024625157e-16
		 -1.1102230246251565e-16 1 -29.65665999999996 2.1175538406081881e-15 -1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[12]" -type "matrix" "xform" 1 1 1 0 0 0 1 -2.050925868474522 0
		 10.250824075415816 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 6.123233995736766e-17 1
		 1 1 yes;
	setAttr ".xm[13]" -type "matrix" "xform" 1 1 1 0 0 0 0 44.485311800062085 -1.5465679670191926e-15
		 -3.1974423109204508e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.026176948307873173 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[14]" -type "matrix" "xform" 1 1 1 2.2204460492503131e-16 2.2204460492503131e-16
		 2.4651903288156619e-32 0 15.60329919120479 2.0382410313768418e-05 3.730349362740526e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[15]" -type "matrix" "xform" 1 1 1 2.2204460492503131e-16 2.2204460492503131e-16
		 2.4651903288156619e-32 0 31.206599191201509 1.018089498217023e-05 1.7763568394002505e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[16]" -type "matrix" "xform" 1 1 1 2.2204460492503131e-16 2.2204460492503131e-16
		 2.4651903288156619e-32 0 46.809999191198116 -2.0685756219052109e-08 5.3290705182007514e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[17]" -type "matrix" "xform" 1 1 1 0 0 0 1 46.810241652265802 -7.5495165674510645e-15
		 -4.6185277824406512e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.026176948307873222 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[18]" -type "matrix" "xform" 1 1 1 0 -1.6940658945086007e-21 0 0 6.3411153151486479
		 13.232144567317997 -8.2543089616748944e-05 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		2.747431038670296e-06 -2.7992232921775686e-06 0.70047358807740434 0.71367832557152999 1
		 1 1 yes;
	setAttr ".xm[19]" -type "matrix" "xform" 1 1 1 3.3306690738754691e-16 -1.1102230246251565e-16
		 -1.110223024625156e-16 1 5.6843418860808015e-14 -2.1191937094044988e-12 1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[20]" -type "matrix" "xform" 1 1 1 3.3306690738754691e-16 -1.1102230246251565e-16
		 -1.110223024625156e-16 1 14.828329999996569 1.0201698696894876e-05 -1.5987211554602254e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[21]" -type "matrix" "xform" 1 1 1 3.3306690738754691e-16 -1.1102230246251565e-16
		 -1.110223024625156e-16 1 29.656659999993025 2.0403399513871639e-05 -2.4868995751603507e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[22]" -type "matrix" "xform" 1 1 1 0 0 0 1 6.4125137329101562 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[23]" -type "matrix" "xform" 1 1 1 0 0 0 1 13.764053344726562 -9.1715364335046153e-17
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[24]" -type "matrix" "xform" 1 1 1 0 0 0 1 12.663131713867188 -1.1902919148990496e-14
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[25]" -type "matrix" "xform" 1 1 1 0 0 0 3 17.12096460700613 8.897747231229418e-15
		 3.0000000000000004 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.69431490382536309 0.13389105394303585 -0.69431490382536309 0.13389105394303585 1
		 1 1 yes;
	setAttr ".xm[26]" -type "matrix" "xform" 1 1 1 0 0 0 3 15.384392355224893 2.1094237467877974e-14
		 4.8316906031686813e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.18935054436666898 0.98190955354759946 1
		 1 1 yes;
	setAttr ".xm[27]" -type "matrix" "xform" 1 1 1 0 0 0 0 30.350649617122812 -1.0738077094174514e-12
		 1.1368683772161603e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.0017453283658983088 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[28]" -type "matrix" "xform" 1 1 1 0 0 0 5 29.26065975608244 6.1284310959308641e-14
		 -1.1368683772161603e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.0017453283658983088 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[29]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.0330070101518629 -3.1783308274265307
		 -1.752554612330556 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.95360976239370576 -0.19208823158104982 -0.22892184008178468 0.036404992639125833 1
		 1 1 yes;
	setAttr ".xm[30]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.4411660968213704 6.2172489379008766e-15
		 -4.2632564145606011e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[31]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.6975205785491374 7.638334409421077e-14
		 3.694822225952521e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[32]" -type "matrix" "xform" 1 1 1 -4.4408920985006262e-16 0 0 0 4.5569999999993911
		 3.7279999999999198 -0.27699999999961733 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654768 0 0 0.70710678118654735 1
		 1 1 yes;
	setAttr ".xm[33]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.3084338330974106 -0.31243273655039161
		 0.36687437614595808 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[34]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.7376223054288005 -2.8421709430404007e-14
		 2.5757174171303632e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[35]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.2943363456669061 1.4210854715202004e-13
		 5.3290705182007514e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[36]" -type "matrix" "xform" 1 1 1 -4.4408920985006262e-16 0 0 0 4.6599999999993571
		 1.8899999999999046 0.76000000000021828 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654768 0 0 0.70710678118654735 1
		 1 1 yes;
	setAttr ".xm[37]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.6385194145723432 -0.13607294733958497
		 -0.0003868401918571962 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[38]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.8599716183124997 1.9895196601282805e-13
		 -8.8817841970012523e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[39]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.728114757406459 -5.6843418860808015e-14
		 6.7501559897209518e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[40]" -type "matrix" "xform" 1 1 1 -4.4408920985006262e-16 0 0 0 4.7489999999992989
		 -0.37000000000012534 1.4700000000003968 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654768 0 0 0.70710678118654735 1
		 1 1 yes;
	setAttr ".xm[41]" -type "matrix" "xform" 1 1 1 -1.3886164620156668e-16 -1.6614104955093601e-16
		 7.2378107283146636e-17 0 4.1497049935348542 0.039809941666760551 0.002752044032463985 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[42]" -type "matrix" "xform" 1 1 1 0 0 0 0 4.3953968914290584 -1.4210854715202004e-13
		 -2.042810365310288e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[43]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.6033506852285626 4.5474735088646412e-13
		 1.5987211554602254e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[44]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 4.8119999999992586
		 -2.5370000000000994 1.2340000000000373 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654757 0 0 0.70710678118654746 1
		 1 1 yes;
	setAttr ".xm[45]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.8841418335248648 0.058187307654151255
		 0.00798505224690782 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[46]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.8337976624462442 1.7053025658242404e-13
		 6.2172489379008766e-15 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[47]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.3509375903510943 1.1368683772161603e-13
		 3.3306690738754696e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[48]" -type "matrix" "xform" 1 1 1 -1.8022395907300292e-16 -7.2374718546320238e-17
		 -1.6613983649056767e-16 0 8.9999999999993889 -7.3718808835110394e-14 -5.9999999999997158 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[49]" -type "matrix" "xform" 1 1 1 -1.8022395907300292e-16 -7.2374718546320238e-17
		 -1.6613983649056767e-16 0 2.4158453015843406e-13 1.865174681370263e-14 3.4106051316484809e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[50]" -type "matrix" "xform" 1 1 1 0 0 0 0 29.261000000000386 -1.5987211554602254e-14
		 -9.6633812063373625e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[51]" -type "matrix" "xform" 1 1 1 0 0 0 0 19.507000000000396 3.5527136788005009e-15
		 -9.6633812063373625e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[52]" -type "matrix" "xform" 1 1 1 0 0 0 0 9.7540000000003957 5.3290705182007514e-15
		 -1.0231815394945443e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[53]" -type "matrix" "xform" 1 1 1 2.2204460492503136e-16 8.6736173798840374e-19
		 4.3368086899420197e-19 3 -3.5527136788005009e-15 8.8817841970012523e-15 2.8421709430404007e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[54]" -type "matrix" "xform" 1 1 1 2.2204460492503136e-16 8.6736173798840374e-19
		 4.3368086899420197e-19 3 10.116999999999951 -5.3290705182007514e-15 2.2737367544323206e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[55]" -type "matrix" "xform" 1 1 1 2.2204460492503136e-16 8.6736173798840374e-19
		 4.3368086899420197e-19 3 20.23399999999998 7.1054273576010019e-15 2.8421709430404007e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[56]" -type "matrix" "xform" 1 1 1 0 0 0 3 17.120964607006044 3.5339843292742149e-14
		 -3.0000000000000102 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.13389105394303569 -0.69431490382536287 0.13389105394303574 0.69431490382536309 1
		 1 1 yes;
	setAttr ".xm[57]" -type "matrix" "xform" 1 1 1 0 0 0 3 -15.384392355224771 -5.1958437552457326e-14
		 8.5265128291212022e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.18935054436666907 0.98190955354759946 1
		 1 1 yes;
	setAttr ".xm[58]" -type "matrix" "xform" 1 1 1 0 0 0 0 -30.350649617122738 9.6544994221403613e-13
		 -5.6843418860808015e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.0017453283658983088 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[59]" -type "matrix" "xform" 1 1 1 0 0 0 5 -29.260659756081694 -4.7961634663806763e-14
		 5.1159076974727213e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.0017453283658985528 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[60]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.0330070101527724 3.1783308274263442
		 1.752554612330357 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.19208823158104976 -0.95360976239370576 0.036404992639125867 0.22892184008178459 1
		 1 1 yes;
	setAttr ".xm[61]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.441166096821263 1.3322676295501878e-14
		 -2.8421709430404007e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[62]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.6975205785490841 1.4477308241112041e-13
		 9.0949470177292824e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[63]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.5570000000001016 -3.7280000000000584
		 0.27699999999967417 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -4.3297802811774664e-17 -0.70710678118654757 0.70710678118654757 4.3297802811774664e-17 1
		 1 1 yes;
	setAttr ".xm[64]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.30843383309724 -0.31243273655070425
		 -0.36687437614609664 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[65]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.7376223054286442 -2.8421709430404007e-13
		 -1.4388490399142029e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[66]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.294336345667034 1.4210854715202004e-13
		 -4.7961634663806763e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[67]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.660000000000025 -1.8900000000000077
		 -0.76000000000041723 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -4.3297802811774664e-17 -0.70710678118654757 0.70710678118654757 4.3297802811774664e-17 1
		 1 1 yes;
	setAttr ".xm[68]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.6385194145725706 -0.13607294733995445
		 0.00038684019197710029 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[69]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.8599716183126276 5.6843418860808015e-14
		 -6.3948846218409017e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[70]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.728114757406388 0 -5.595524044110789e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[71]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.7490000000001231 0.36999999999997613
		 -1.470000000000482 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 4.3297802811774652e-17 0.70710678118654768 -0.70710678118654735 4.3297802811774677e-17 1
		 1 1 yes;
	setAttr ".xm[72]" -type "matrix" "xform" 1 1 1 2.7922662873844912e-20 5.5402379462248942e-17
		 -7.6280188864810697e-21 0 4.1497049935346979 0.039809941666703708 -0.0027520440325066176 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[73]" -type "matrix" "xform" 1 1 1 0 0 0 0 4.3953968914292716 -3.1263880373444408e-13
		 -2.4868995751603507e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[74]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.6033506852285058 1.7053025658242404e-13
		 1.7408297026122455e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[75]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.8120000000001539 2.5369999999999648
		 -1.234000000000492 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -4.3297802811774664e-17 -0.70710678118654757 0.70710678118654757 4.3297802811774664e-17 1
		 1 1 yes;
	setAttr ".xm[76]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.8841418335247084 0.058187307653128073
		 -0.0079850522469251395 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[77]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.83379766244596 8.5265128291212022e-14
		 -1.1546319456101628e-14 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[78]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.3509375903512932 0
		 -1.2034817586936697e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[79]" -type "matrix" "xform" 1 1 1 -2.7924275431752929e-20 8.6007921725726606e-22
		 -5.5511158262293034e-17 0 -9.0000000000000568 -1.5099033134902129e-14 5.9999999999995168 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[80]" -type "matrix" "xform" 1 1 1 -2.7924275431752929e-20 8.6007921725726606e-22
		 -5.5511158262293034e-17 0 -9.9475983006414026e-14 -3.5527136788005009e-14 -1.4210854715202004e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[81]" -type "matrix" "xform" 1 1 1 1.3877787807814451e-17 1.1102230246251565e-16
		 -1.1102230246251565e-16 0 -9.7540000000000191 6.2172489379008766e-15 7.1054273576010019e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[82]" -type "matrix" "xform" 1 1 1 1.3877787807814451e-17 1.1102230246251565e-16
		 -1.1102230246251565e-16 0 -19.506999999999806 2.8421709430404007e-14 7.1054273576010019e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[83]" -type "matrix" "xform" 1 1 1 1.3877787807814451e-17 1.1102230246251565e-16
		 -1.1102230246251565e-16 0 -29.261000000000251 -5.3290705182007514e-15 5.1159076974727213e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[84]" -type "matrix" "xform" 1 1 1 2.220437578920841e-16 4.3368086899420177e-19
		 4.3368086899420187e-19 3 -1.2789769243681803e-13 -1.865174681370263e-14 -1.7053025658242404e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[85]" -type "matrix" "xform" 1 1 1 2.220437578920841e-16 4.3368086899420177e-19
		 4.3368086899420187e-19 3 -10.117000000000104 -1.6875389974302379e-14 8.5265128291212022e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[86]" -type "matrix" "xform" 1 1 1 2.220437578920841e-16 4.3368086899420177e-19
		 4.3368086899420187e-19 3 -20.234000000000151 -1.9539925233402755e-14 5.6843418860808015e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[87]" -type "matrix" "xform" 1 1 1 0 0 0 1 22.142144871168256 -4.0901220894534793
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[88]" -type "matrix" "xform" 1 1 1 0 0 -5.5511151231257827e-17 1 6.2159582718826414
		 1.7383894777904993 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[89]" -type "matrix" "xform" 1 1 1 0 0 -1.0408340855860843e-16 1 6.2159582718826414
		 1.7383894777905091 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.0079991822229547836 0.99996800603007496 1
		 1 1 yes;
	setAttr ".xm[90]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.7098497602150928 2.9922745396408477
		 -3.7617570592466878e-30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.93069079510034292 0.36580683962371668 1
		 1 1 yes;
	setAttr ".xm[91]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 -2.2204460492503131e-16
		 1.2325951644078309e-32 0 3.8095941708363057 -1.4271268743738053 -0.00038016863982193183 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.50398358380708985 -0.49598442238941554 -0.50398358380708985 0.49598442238941554 1
		 1 1 yes;
	setAttr ".xm[92]" -type "matrix" "xform" 1 1 1 -3.3306690738754696e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.2249510705620176 0 0 0.97437006104097956 1
		 1 1 yes;
	setAttr ".xm[93]" -type "matrix" "xform" 1 1 1 -3.3306690738754696e-16 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.2249510705620176 0 0 0.97437006104097956 1
		 1 1 yes;
	setAttr ".xm[94]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.14780937820575341 0 0 0.98901586828241972 1
		 1 1 yes;
	setAttr ".xm[95]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.14780937820575341 0 0 0.98901586828241972 1
		 1 1 yes;
	setAttr ".xm[96]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.7723633050918579 2.0409703254696296
		 11.088758468627695 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[97]" -type "matrix" "xform" 1 1 1 0 0 0 0 -1.8343081474304199 2.087662220003466
		 11.055114746093517 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[98]" -type "matrix" "xform" 1 1 1 0 0 0 0 4.7181239128112793 2.4948277473420433
		 10.338639259338461 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.38268343236508984 0 0.92387953251128674 1
		 1 1 yes;
	setAttr ".xm[99]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.7173638343811035 2.4948277473420433
		 10.338639259338461 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.38268340160958941 0 0.92387954525063154 1
		 1 1 yes;
	setAttr ".xm[100]" -type "matrix" "xform" 1 1 1 -3.0531133177191805e-16 0 0 0 0.015328310430049896
		 -5.5766798604240364 12.559756425882901 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.087155759329076835 0 0 0.9961946966410592 1
		 1 1 yes;
	setAttr ".xm[101]" -type "matrix" "xform" 1 1 1 -5.5511151231257815e-17 0 0 0 -0.085047094151377678
		 -1.3949891941437045 13.658287747567137 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.043619370736421366 0 0 0.9990482223078917 1
		 1 1 yes;
	setAttr ".xm[102]" -type "matrix" "xform" 1 1 1 -3.3306690738754691e-16 3.4694469519536152e-16
		 4.163336342344337e-16 0 -1.8118503205478191 -4.3495729267600609 11.8407162427903 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.098332643782895232 -0.22938533821280857 0.098332673562086484 0.96335027019760255 1
		 1 1 yes;
	setAttr ".xm[103]" -type "matrix" "xform" 1 1 1 -7.4246164771807344e-16 -1.6653345369377343e-16
		 1.5959455978986633e-16 0 -4.91326904296875 4.2585563659638694 9.6477346420287287 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12153640868793751 -0.25566065496168372 0.079230633872962697 0.95581851704384235 1
		 1 1 yes;
	setAttr ".xm[104]" -type "matrix" "xform" 1 1 1 -1.3183898417423731e-16 -3.4694469519536088e-18
		 7.2858385991025873e-17 0 0.83776202239096165 -1.8049832602750371 12.989658149288456 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.11223472806194172 -0.12909248220815037 0.019293005126064081 0.98507171150500816 1
		 1 1 yes;
	setAttr ".xm[105]" -type "matrix" "xform" 1 1 1 3.4694469519536123e-17 -3.2699537522162814e-16
		 1.1796119636642288e-16 0 -3.5640861988067627 -4.8379778862002922 9.3348045349121271 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.05787651514671753 -0.37741837077132329 -0.023799602570385429 0.92392600424291738 1
		 1 1 yes;
	setAttr ".xm[106]" -type "matrix" "xform" 1 1 1 1.8117018302232779e-16 -5.5294310796760726e-17
		 -8.6736173798840401e-18 0 1.8326226472854614 4.2695941925045418 11.390741348266546 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.060899828360838924 0.069626363859212809 0.0042585308451804482 0.99570339221899073 1
		 1 1 yes;
	setAttr ".xm[107]" -type "matrix" "xform" 1 1 1 -5.3429483060085649e-16 1.0755285551056199e-16
		 -9.7144514654701197e-17 0 4.9168577417731285 -5.6288543195767318 7.0175477468022507 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.20921603848139034 -0.15779924475825963 -0.05466270524947564 0.96350404059904449 1
		 1 1 yes;
	setAttr ".xm[108]" -type "matrix" "xform" 1 1 1 -9.7144514654701222e-17 -1.0408340855860836e-16
		 8.4307560932472815e-16 0 -2.2839715480804443 0.11269550025687636 10.584563255310215 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12330875616651776 -0.088015096329933679 0.19719363355601482 0.96858812936958649 1
		 1 1 yes;
	setAttr ".xm[109]" -type "matrix" "xform" 1 1 1 1.3877787807814457e-16 8.8470897274817211e-17
		 -5.9674487573602184e-16 0 4.2920675277709961 -0.36268511414303362 8.46261405944826 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.055087298001327896 0.37702881334098826 0.10034909028199568 0.91909995299160741 1
		 1 1 yes;
	setAttr ".xm[110]" -type "matrix" "xform" 1 1 1 2.7755575615628914e-17 -4.163336342344337e-17
		 -1.1102230246251565e-16 0 3.2331273555755615 -8.3267211914040331 4.7220973968505984 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.40247134790242234 0.35497156861833118 0.082338296552528834 0.8397811646560529 1
		 1 1 yes;
	setAttr ".xm[111]" -type "matrix" "xform" 1 1 1 1.1188966420050401e-16 5.6812193838240432e-16
		 -1.9428902930940237e-16 0 -3.5924146175384521 4.7588644027680687 10.968506813049402 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.071178513297624924 -0.17570400627580265 0.020647360863762159 0.98164933041933766 1
		 1 1 yes;
	setAttr ".xm[112]" -type "matrix" "xform" 1 1 1 8.3266726846886716e-17 -8.3266726846886778e-17
		 4.7184478546569153e-16 0 -3.0092539563775063 -6.6618580631260329 10.554552232503909 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.10022942454785251 -0.33427208185320906 -0.17482165279032458 0.92068106718015374 1
		 1 1 yes;
	setAttr ".xm[113]" -type "matrix" "xform" 1 1 1 -1.2490009027033014e-16 -7.6327832942979488e-17
		 4.9266146717741321e-16 0 2.3611671924591064 0.11580825597272337 10.647420883178793 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12330873915487948 0.088015097063470743 -0.19719363440328894 0.96858813129614785 1
		 1 1 yes;
	setAttr ".xm[114]" -type "matrix" "xform" 1 1 1 2.7755575615628914e-17 4.163336342344337e-17
		 1.1102230246251565e-16 0 -3.2323668003082275 -8.3267211914040331 4.7220973968505984 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.40247134790242234 -0.35497156861833118 -0.082338296552528834 0.8397811646560529 1
		 1 1 yes;
	setAttr ".xm[115]" -type "matrix" "xform" 1 1 1 -3.469446951953613e-17 4.4408920985006262e-16
		 5.8980598183211429e-17 0 -1.1389973275363445 -4.1690155863765028 12.32993435859688 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.077808752997641284 -0.1601308337930652 0.037879433399091125 0.98329500280996718 1
		 1 1 yes;
	setAttr ".xm[116]" -type "matrix" "xform" 1 1 1 5.8980598183211441e-17 -3.4694469519536134e-18
		 -2.0816681711721685e-17 0 -6.453498363494873 4.5612950325008796 7.4409055709839063 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.19405880798787045 0.094232943552212026 -0.062509402879856762 0.97445056618764203 1
		 1 1 yes;
	setAttr ".xm[117]" -type "matrix" "xform" 1 1 1 -1.8214596497756474e-17 2.1328169501319585e-34
		 2.3418766925686896e-17 0 -3.6539125442504883 1.5530524253841804 10.600840568542562 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.022271436555334249 -0.13975629904335413 0.022271434205425059 0.9896848706582817 1
		 1 1 yes;
	setAttr ".xm[118]" -type "matrix" "xform" 1 1 1 -4.163336342344337e-17 0 0 0 -0.04152233898639679
		 4.208777904510157 11.755763053893986 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.043619387365335972 0 0 0.9990482215818578 1
		 1 1 yes;
	setAttr ".xm[119]" -type "matrix" "xform" 1 1 1 -5.5771359752654348e-16 2.810252031082427e-16
		 -2.3592239273284586e-16 0 0.94366935640573502 -5.4540907490984978 12.185562280680266 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.092741417509509039 0.12948762296653127 0.027254036873643608 0.98685824840799419 1
		 1 1 yes;
	setAttr ".xm[120]" -type "matrix" "xform" 1 1 1 4.3801767768414369e-16 -1.1015494072452725e-16
		 1.1796119636642283e-16 0 -0.87462571822106838 -1.793634983111275 12.995929770228077 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.11223473830961643 0.12909248240885507 -0.019293003783118538 0.98507171033743313 1
		 1 1 yes;
	setAttr ".xm[121]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.5318711884319782 -4.9253413975242211
		 11.625378727912736 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.20791169081775937 0 0.97814760073380558 1
		 1 1 yes;
	setAttr ".xm[122]" -type "matrix" "xform" 1 1 1 -1.3877787807814466e-17 2.2854981795994433e-16
		 -9.0205620750793981e-17 0 3.6288182735443115 4.797499656676905 11.052979469299153 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.071178512566487204 0.17570400657198948 -0.020647364948590589 0.98164933033342028 1
		 1 1 yes;
	setAttr ".xm[123]" -type "matrix" "xform" 1 1 1 -5.5511151231257827e-17 0 0 0 -0.0070071611553430557
		 -4.0882932245734764 12.620753049850459 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.087155751038367382 0 0 0.99619469736640243 1
		 1 1 yes;
	setAttr ".xm[124]" -type "matrix" "xform" 1 1 1 -4.7357950894166824e-16 3.5822039778921066e-16
		 -8.6736173798840429e-17 0 -3.4990818500518799 3.2022020816799568 11.465617179870531 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.048688015940537878 -0.084257614797766528 0.064552940820740229 0.99315811897389183 1
		 1 1 yes;
	setAttr ".xm[125]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.12973727285861975
		 3.5528411865231533 2.3468577861785738 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.25881907725772157 0 0 0.96592581767310759 1
		 1 1 yes;
	setAttr ".xm[126]" -type "matrix" "xform" 1 1 1 -1.6657411127524171e-16 3.4694469519536042e-18
		 -1.2489331400675208e-16 0 6.4929141998291016 0.6071298122428459 3.1924161911010924 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.026167979711321621 0.00068525136350062077 -0.026167977630727021 0.99931476733565505 1
		 1 1 yes;
	setAttr ".xm[127]" -type "matrix" "xform" 1 1 1 6.6174449004242214e-24 0 0 0 -0.046215998008847237
		 -2.3841999376848548 12.77912678863459 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[128]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.28401531278527992 0 0 0.95881974432292516 1
		 1 1 yes;
	setAttr ".xm[129]" -type "matrix" "xform" 1 1 1 1.7347234759768071e-18 5.5511151231257827e-17
		 4.8148248609680896e-35 0 1.6931652203202248 -5.3096357930437819 11.88332000162753 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.091272470475058903 0.23220797725209505 0.031839841846571057 0.9678507198452948 1
		 1 1 yes;
	setAttr ".xm[130]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 0 0 0 -0.01823798380792141
		 0.86898654699550093 12.442914962768659 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.13052620047123084 0 0 0.99144486028752199 1
		 1 1 yes;
	setAttr ".xm[131]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.32556812298130305 0 0 0.94551858643732178 1
		 1 1 yes;
	setAttr ".xm[132]" -type "matrix" "xform" 1 1 1 1.040834085586084e-16 -2.7946395197986366e-15
		 3.4694469519536e-17 0 4.277468204498291 -4.1524758338931633 7.5401496887206267 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.034549684938575846 0.42696043074251805 0.057742631408790664 0.90176321635382595 1
		 1 1 yes;
	setAttr ".xm[133]" -type "matrix" "xform" 1 1 1 1.3877787807814457e-16 -5.8980598183211429e-17
		 -1.3183898417423734e-16 0 -2.5622284412384033 -2.7924189567569329 11.653219223022379 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.033311153148157684 -0.12584862638501892 0.36380196993723207 0.92233433037198231 1
		 1 1 yes;
	setAttr ".xm[134]" -type "matrix" "xform" 1 1 1 -4.4408920985006262e-16 0 0 0 0.0019831359386444092
		 -9.0985696860677194 9.2095410626842007 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.57357636817811142 0 0 0.81915209202419037 1
		 1 1 yes;
	setAttr ".xm[135]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.31730462483585864 0 0 0.94832366576911653 1
		 1 1 yes;
	setAttr ".xm[136]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.28401531278527992 0 0 0.95881974432292516 1
		 1 1 yes;
	setAttr ".xm[137]" -type "matrix" "xform" 1 1 1 -2.0816681711721688e-16 9.9052710478275705e-16
		 6.2450045135164969e-17 0 -4.1865205764770508 -4.384348392484327 7.6321048736571449 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.034549677433761368 -0.42696043026196123 -0.057742634962116887 0.90176321664136194 1
		 1 1 yes;
	setAttr ".xm[138]" -type "matrix" "xform" 1 1 1 -4.7357950894166824e-16 -3.5822039778921066e-16
		 8.6736173798840429e-17 0 3.4597868919372559 3.2305223941799568 11.471049308776783 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.048688015940537878 0.084257614797766528 -0.064552940820740229 0.99315811897389183 1
		 1 1 yes;
	setAttr ".xm[139]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.092498280107975006
		 -1.9120391607287957 3.9833073616027934 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.34202014332566871 0 0 0.93969262078590843 1
		 1 1 yes;
	setAttr ".xm[140]" -type "matrix" "xform" 1 1 1 6.8695049648681561e-16 -1.7000290064572714e-16
		 1.7347234759768066e-16 0 4.8904542922973633 4.3403892517060569 9.6624298095701793 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12153639277857145 0.25566065364290941 -0.079230638128372111 0.95581851906678605 1
		 1 1 yes;
	setAttr ".xm[141]" -type "matrix" "xform" 1 1 1 -2.4286128663675289e-16 -5.5858095926453188e-16
		 -2.7755575615628909e-16 0 3.6374962329864502 -4.7317919731143547 9.3467216491699396 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.057876522835979549 0.37741837096939301 0.023799599429366942 0.92392600376124667 1
		 1 1 yes;
	setAttr ".xm[142]" -type "matrix" "xform" 1 1 1 -3.469446951953613e-17 -4.4408920985006262e-16
		 -5.8980598183211429e-17 0 1.1656378395855427 -4.2119233012202528 12.274085283279499 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.077808752997641284 0.1601308337930652 -0.037879433399091125 0.98329500280996718 1
		 1 1 yes;
	setAttr ".xm[143]" -type "matrix" "xform" 1 1 1 -4.8572257327350592e-17 -1.1535911115245767e-16
		 -9.8879238130678004e-17 0 3.5397021770477295 3.241327047345095 11.46135139465324 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.030105921179207983 0.15086672707386009 -0.079693557372086193 0.98487654103717726 1
		 1 1 yes;
	setAttr ".xm[144]" -type "matrix" "xform" 1 1 1 -4.5102810375396984e-16 -3.4694469519536234e-17
		 -3.8857805861880479e-16 0 -4.6797485128045082 -5.6976862235851797 6.9723996070561256 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.20921603833075894 0.15779925921442625 0.054662713017402921 0.96350403782347371 1
		 1 1 yes;
	setAttr ".xm[145]" -type "matrix" "xform" 1 1 1 -6.9388939039072284e-17 0 0 0 0.00038016863982193172
		 2.7032170295711921 12.56087779998788 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.043619387365336028 0 0 0.9990482215818578 1
		 1 1 yes;
	setAttr ".xm[146]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 1.5612511283791245e-17
		 3.2612801348363973e-16 0 -4.2024707794189453 -0.42095842957530749 8.5212326049804865 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.055087313299523107 -0.37702881501127433 -0.10034908400644255 0.91909995207469253 1
		 1 1 yes;
	setAttr ".xm[147]" -type "matrix" "xform" 1 1 1 -4.9613091412936693e-16 2.567390744445674e-16
		 -1.2490009027033018e-16 0 6.4542584419250488 4.5612950325008796 7.4409055709839063 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.19405880759574962 -0.094232944359727552 0.062509398824983659 0.9744505664477553 1
		 1 1 yes;
	setAttr ".xm[148]" -type "matrix" "xform" 1 1 1 4.4669129506402763e-16 -4.1633363423443358e-17
		 -3.8163916471489756e-17 0 -1.0101616010069847 -5.4769331563250319 12.202840951944912 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.092741417404700252 -0.12948761514777815 -0.027254041836092514 0.98685824930671007 1
		 1 1 yes;
	setAttr ".xm[149]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.00038016863982193172
		 -9.6698760986331536 6.4196476936340634 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.50000002882956418 0 0 0.86602538713968136 1
		 1 1 yes;
	setAttr ".xm[150]" -type "matrix" "xform" 1 1 1 -2.8275992658421951e-16 3.3566899260151222e-16
		 1.7347234759768068e-16 0 -1.7153305634856224 -5.4175001729240364 11.802785066629834 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0912724698860016 -0.23220796194943097 -0.031839851858947485 0.967850723242898 1
		 1 1 yes;
	setAttr ".xm[151]" -type "matrix" "xform" 1 1 1 -4.7791631763161035e-16 -2.7755575615628914e-17
		 3.4694469519536211e-18 0 6.8350648880004883 -1.7054594755150276 5.1711883544922008 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.069308069194843905 -0.11292743993126493 0.0078966558553356606 0.99115156645255609 1
		 1 1 yes;
	setAttr ".xm[152]" -type "matrix" "xform" 1 1 1 -7.6327832942979512e-17 -6.9388939039072284e-18
		 -1.3877787807814457e-17 0 1.8003116734325886 -4.4092042744163109 11.817525744438248 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.098332641213754554 0.22938535412478414 -0.098332670992946125 0.96335026693325188 1
		 1 1 yes;
	setAttr ".xm[153]" -type "matrix" "xform" 1 1 1 -6.3837823915946501e-16 0 0 0 -0.052734427154064178
		 -7.2931647581895334 10.698521219114586 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.087155709584821286 0 0 0.99619470099311724 1
		 1 1 yes;
	setAttr ".xm[154]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 0.00038016863982193172
		 -13.67730619508643 4.3428690594748662 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.2588190692189215 0 0 0.96592581982709791 1
		 1 1 yes;
	setAttr ".xm[155]" -type "matrix" "xform" 1 1 1 0 0 0 0 -2.5753642432391644
		 -4.9651058018210961 11.522259831428451 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.20791169081775937 0 0.97814760073380558 1
		 1 1 yes;
	setAttr ".xm[156]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 4.1633363423443352e-17
		 -1.5265566588595902e-16 0 2.9998846277594566 -6.6451650637811497 10.59611716793683 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.1002294214815517 0.3342720775669995 0.17482165919613274 0.9206810678538071 1
		 1 1 yes;
	setAttr ".xm[157]" -type "matrix" "xform" 1 1 1 -1.736485304507096e-16 -2.1684043449710089e-18
		 -6.0986372202309432e-20 0 -6.9114284515380859 0.60449951887355269 3.1931614875793626 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.026167980651632221 -0.00068521545448785217 0.026167978571037753 0.99931476731103219 1
		 1 1 yes;
	setAttr ".xm[158]" -type "matrix" "xform" 1 1 1 -2.2529721144248782e-16 2.4849913793367762e-16
		 -3.8163916471489787e-17 0 -6.8343048095703125 -1.7054594755150276 5.1711883544922008 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.069308068997686906 0.11292746467747997 -0.0078966575857595724 0.9911515636330811 1
		 1 1 yes;
	setAttr ".xm[159]" -type "matrix" "xform" 1 1 1 -2.1857515797307767e-16 1.8301332671555317e-16
		 1.5092094240998219e-16 0 -3.5514810085296631 3.215692281722653 11.487589836120527 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.030105922434777888 -0.15086672682330721 0.079693549175570949 0.98487654170041727 1
		 1 1 yes;
	setAttr ".xm[160]" -type "matrix" "xform" 1 1 1 1.8117018302232779e-16 5.5294310796760726e-17
		 8.6736173798840401e-18 0 -1.7924996614456177 4.2614459991451383 11.368327140808031 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.060899828360838924 -0.069626363859212809 -0.0042585308451804482 0.99570339221899073 1
		 1 1 yes;
	setAttr ".xm[161]" -type "matrix" "xform" 1 1 1 1.387778780781446e-17 -1.2143064331837647e-16
		 -1.1969591984239966e-16 0 2.5629889965057373 -2.7924189567569329 11.653219223022379 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.033311160824172889 0.12584862941271666 -0.3638019688898721 0.9223343300947543 1
		 1 1 yes;
	setAttr ".xm[162]" -type "matrix" "xform" 1 1 1 -1.8214596497756474e-17 -2.1328169501319585e-34
		 -2.3418766925686896e-17 0 3.5847868919372559 1.5587592124961418 10.550768852233968 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.022271436555334249 0.13975629904335413 -0.022271434205425059 0.9896848706582817 1
		 1 1 yes;
	setAttr ".xm[163]" -type "matrix" "xform" 1 1 1 -1.1102230246175835e-16 -6.3527471044072516e-22
		 1.4823076576950256e-21 0 0.012007030658423901 -3.9921574744150234 5.7776615852276985 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.41895411128867305 -4.9243318443396159e-07 2.3205130541345381e-07 0.90800740780790001 1
		 1 1 yes;
	setAttr ".xm[164]" -type "matrix" "xform" 1 1 1 -3.3306690738512348e-16 -2.46168950295781e-21
		 -2.0117032497289626e-21 0 0.00037983186003789395 -5.4348876341216226 6.1524729873327644 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.1696689694871952 1.5797512067899606e-06 -2.7029024870752511e-07 0.9855011115115927 1
		 1 1 yes;
	setAttr ".xm[165]" -type "matrix" "xform" 1 1 1 -8.3266726842847748e-17 -8.4703294725430015e-22
		 -1.6940658945086003e-21 0 0.00038399903946963095 -5.3725827339102352 8.2971817317656438 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.039583728734186432 2.6756443302910299e-06 -8.3001873204433293e-07 0.99921625707934236 1
		 1 1 yes;
	setAttr ".xm[166]" -type "matrix" "xform" 1 1 1 -1.9949319974541075e-16 9.9741438261644077e-21
		 -9.8599929016320993e-22 0 0.00038599556033056508 -5.3807680642292155 10.034170056793725 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.004039159667283217 2.6368927893606113e-06 -9.4593873754117839e-07 0.99999184255739504 1
		 1 1 yes;
	setAttr ".xm[167]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 -0.0013050809502601624
		 -5.4069351109430386 9.2501585716168435 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[168]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.0013050809502601624
		 -3.4473664760567146 9.2501583099363867 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[169]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.1149156093597412 2.5526888370510221
		 9.4461641311645685 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[170]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[171]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[172]" -type "matrix" "xform" 1 1 1 5.5511151231257839e-17 -5.5511151231257839e-17
		 -5.5511151231257839e-17 0 10.250824075415883 9.2384958469890677 -2.4498587588346212 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.50000000000000011 -0.50000000000000011 -0.50000000000000011 0.50000000000000011 1
		 1 1 yes;
	setAttr ".xm[173]" -type "matrix" "xform" 1 1 1 1.110223024625156e-16 2.7755575615628914e-16
		 -4.4408920985006262e-16 0 -10.250824075415798 9.2384958469891103 -2.4498587588346052 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.5 -0.50000000000000011 0.5 0.49999999999999989 1
		 1 1 yes;
	setAttr ".xm[174]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[175]" -type "matrix" "xform" 1 1 1 0 0 0 0 76.892426183969576 152.46379243127296
		 -5.6183477607361212 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.70710678118654724 0 0 0.70710678118654779 1
		 1 1 yes;
	setAttr ".xm[176]" -type "matrix" "xform" 1 1 1 0 0 0 0 -76.892426183968894
		 152.46379243127274 -5.6183477607361239 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654757 0 0 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[177]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr -s 55 ".m";
	setAttr -s 178 ".p";
createNode dagPose -n "apose";
	rename -uid "CF3A2C8A-42E4-2346-0BC2-8197304875B1";
	setAttr -s 178 ".wm";
	setAttr ".wm[0]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[1]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 102.48998260498047 0 1;
	setAttr ".wm[2]" -type "matrix" 0.018162820752412226 0.99949302218403979 0.02614977146611808 0
		 -2.2257782703138228e-06 0.026154126201422861 -0.99965792233027706 0 -0.99983504236317011 0.018156549453420538 0.00047725735598251894 0
		 -10.250824075415816 100.43905673650595 0 1;
	setAttr ".wm[3]" -type "matrix" 0.018153094006778624 0.9984525025960147 0.052564866952522049 0
		 0.00059431213359569977 0.05256274532340649 -0.99861744657158613 0 -0.99983504238002663 0.018159236322653958 0.00036078401999835807 0
		 -11.058802819755481 55.976298002662766 -1.1632807371706193 1;
	setAttr ".wm[4]" -type "matrix" 0.018153094006778624 0.9984525025960147 0.052564866952522049 0
		 0.00059431213359569977 0.05256274532340649 -0.99861744657158613 0 -0.99983504238002663 0.018159236322653958 0.00036078401999835807 0
		 -11.342050991471451 40.397144068906357 -1.9834661256909143 1;
	setAttr ".wm[5]" -type "matrix" 0.018153094006778624 0.9984525025960147 0.052564866952522049 0
		 0.00059431213359569977 0.05256274532340649 -0.99861744657158613 0 -0.99983504238002663 0.018159236322653958 0.00036078401999835807 0
		 -11.625299163187417 24.817990135149959 -2.8036515142112002 1;
	setAttr ".wm[6]" -type "matrix" 0.018153094006778624 0.9984525025960147 0.052564866952522049 0
		 0.00059431213359569977 0.05256274532340649 -0.99861744657158613 0 -0.99983504238002663 0.018159236322653958 0.00036078401999835807 0
		 -11.908549150212789 9.2387363561431002 -3.6238421592181904 1;
	setAttr ".wm[7]" -type "matrix" -2.4633073358870661e-16 1 4.3391549712059121e-16 0
		 -3.3762055651198608e-16 4.3286687033189039e-16 -1 0 -1.0000000000000004 -2.3939183968479938e-16 3.3767476662061036e-16 0
		 -11.908553536949098 9.2384950778336119 -3.6238548616373745 1;
	setAttr ".wm[8]" -type "matrix" -1.9598161124018403e-06 0.018673377209548748 -0.999825637288697 0
		 2.3998305493089894e-16 -0.99982563729061702 -0.018673377209584608 0 -0.99999999999807998 -3.659638576130359e-08 1.9594743935501617e-06 0
		 -11.908575945448526 2.8973792331999988 9.6082894521791058 1;
	setAttr ".wm[9]" -type "matrix" 0.018162820752412226 0.99949302218403979 0.02614977146611808 0
		 -2.2257782703138228e-06 0.026154126201422861 -0.99965792233027706 0 -0.99983504236317011 0.018156549453420538 0.00047725735598251894 0
		 -10.250824075415814 100.43905673650595 -2.2205342636084934e-15 1;
	setAttr ".wm[10]" -type "matrix" 0.018162820752412226 0.99949302218403979 0.02614977146611808 0
		 -2.2257782703138228e-06 0.026154126201422861 -0.99965792233027706 0 -0.99983504236317011 0.018156549453420538 0.00047725735598251894 0
		 -10.520148375263432 85.618244370863735 -0.38775744072418361 1;
	setAttr ".wm[11]" -type "matrix" 0.018162820752412226 0.99949302218403979 0.02614977146611808 0
		 -2.2257782703138228e-06 0.026154126201422861 -0.99965792233027706 0 -0.99983504236317011 0.018156549453420538 0.00047725735598251894 0
		 -10.789472675111046 70.797432005221467 -0.77551488144836644 1;
	setAttr ".wm[12]" -type "matrix" 0.018159649943282879 -0.99949309688237409 -0.026149118501748274 0
		 1.0210002797572853e-06 -0.026153412665838795 0.99965794100026428 0 -0.99983509996043596 -0.018153464969845035 -0.0004739163361023209 0
		 10.250824075415816 100.43905673650595 0 1;
	setAttr ".wm[13]" -type "matrix" 0.018156107032326053 -0.99845241517638106 -0.052565486831973325 0
		 0.00059749713167568858 -0.052563308536415776 0.99861741502583623 0 -0.99983498577245644 -0.018162412399161089 -0.00035777260157779129 0
		 11.058661765322766 55.976294679683875 -1.1632516898470457 1;
	setAttr ".wm[14]" -type "matrix" 0.018156107032326053 -0.99845241517638106 -0.052565486831973325 0
		 0.00059749713167568858 -0.052563308536415776 0.99861741502583623 0 -0.99983498577245644 -0.018162412399161089 -0.00035777260157779129 0
		 11.341956947674081 40.397141846138858 -1.9834263537877617 1;
	setAttr ".wm[15]" -type "matrix" 0.018156107032326053 -0.99845241517638106 -0.052565486831973325 0
		 0.00059749713167568858 -0.052563308536415776 0.99861741502583623 0 -0.99983498577245644 -0.018162412399161089 -0.00035777260157779129 0
		 11.625252126436157 24.817989812645905 -2.8036316018837883 1;
	setAttr ".wm[16]" -type "matrix" 0.018156107032326053 -0.99845241517638106 -0.052565486831973325 0
		 0.00059749713167568858 -0.052563308536415776 0.99861741502583623 0 -0.99983498577245644 -0.018162412399161089 -0.00035777260157779129 0
		 11.908549120808889 9.2387379339149831 -3.6238421065938091 1;
	setAttr ".wm[17]" -type "matrix" -6.1756155744774333e-16 -1 3.5637386596419629e-16 0
		 -1.5558301175166989e-17 3.5794426504840576e-16 1 0 -0.99999999999999989 6.1756155744774333e-16 -1.5720931501039814e-17 0
		 11.908553522970397 9.2384958469890535 -3.6238548310207204 1;
	setAttr ".wm[18]" -type "matrix" -7.844495739456538e-06 -0.018673504796261817 0.99982563487694598 0
		 6.1716334825815819e-16 0.9998256349077087 0.018673504796836469 0 -0.99999999996923183 1.4648422943656103e-07 -7.8431279332215871e-06 0
		 11.90863606606001 2.89738053184041 9.6082897362972783 1;
	setAttr ".wm[19]" -type "matrix" 0.018159649943282879 -0.99949309688237409 -0.026149118501748274 0
		 1.0210002797572853e-06 -0.026153412665838795 0.99965794100026428 0 -0.99983509996043596 -0.018153464969845035 -0.0004739163361023209 0
		 10.250824075415816 100.43905673650595 -2.1199560672643745e-12 1;
	setAttr ".wm[20]" -type "matrix" 0.018159649943282879 -0.99949309688237409 -0.026149118501748274 0
		 1.0210002797572853e-06 -0.026153412665838795 0.99965794100026428 0 -0.99983509996043596 -0.018153464969845035 -0.0004739163361023209 0
		 10.520101357469665 85.618242996406323 -0.38773756014382527 1;
	setAttr ".wm[21]" -type "matrix" 0.018159649943282879 -0.99949309688237409 -0.026149118501748274 0
		 1.0210002797572853e-06 -0.026153412665838795 0.99965794100026428 0 -0.99983509996043596 -0.018153464969845035 -0.0004739163361023209 0
		 10.789378639523505 70.797429256306756 -0.77547512028552812 1;
	setAttr ".wm[22]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 108.90249633789062 0 1;
	setAttr ".wm[23]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 122.66654968261719 -9.1715364335046153e-17 1;
	setAttr ".wm[24]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 135.32968139648438 -1.1994634513325542e-14 1;
	setAttr ".wm[25]" -type "matrix" 0.92827745102459669 -0.0057398191852657821 -0.37184409151551406 0
		 -0.37185021696614168 0 -0.92829274269609208 0 0.0053282324940701065 0.99998352710218208 -0.0021343530093874958 0
		 3.0000000000000004 152.4506460034905 -3.0968872820961243e-15 1;
	setAttr ".wm[26]" -type "matrix" 0.80417589873551254 -0.59438396874882926 -0.0029701157083970786 0
		 -0.0036933405436226879 -7.6544673377476613e-16 -0.99999317959455525 0 0.59437991480917274 0.80418138357859958 -0.0021952624102600654 0
		 17.280984521070451 152.36234237309682 -5.720595398846843 1;
	setAttr ".wm[27]" -type "matrix" 0.73539834240599811 -0.54103722910382057 0.40800489544877999 0
		 0.3254479490608379 -0.24612154125311064 -0.91296649411864372 0 0.59436765594924867 0.8041784028776533 -0.0049179168905499893 0
		 41.6882454541269 134.32240279956633 -5.8107403400336413 1;
	setAttr ".wm[28]" -type "matrix" 0.62008096390219725 -0.68156193053703107 0.38855235560829754 0
		 0.38275973751099351 -0.16950411611782035 -0.90816481871939514 0 0.68483179069508537 0.71185791381549712 0.15576818992211192 0
		 63.206486136455169 118.49129652338489 6.1277520845090496 1;
	setAttr ".wm[29]" -type "matrix" -0.27106708400438156 -0.63456770130799867 0.72377238716743264 0
		 -0.46475174607187808 0.74475299881354529 0.47890373279122778 0 -0.84292849666653313 -0.20655944232814394 -0.49679447087561668 0
		 62.670453860150111 115.71528469766504 9.9196900828977377 1;
	setAttr ".wm[30]" -type "matrix" 0.15610830560490035 -0.65932648686930606 0.7354718081842061 0
		 -0.69715136444100234 0.45393243919056353 0.55491018706503648 0 -0.6997214960105308 -0.59936126364913167 -0.38878773599189093 0
		 61.73766700071036 113.53163183778618 12.410311083433992 1;
	setAttr ".wm[31]" -type "matrix" 0.081680974274691731 -0.7410075932852298 0.66651028884419228 0
		 -0.70698918777222919 0.42828393933551956 0.56279583836451075 0 -0.70249164181127477 -0.51718528014714449 -0.48890170707865066 0
		 62.158772367561703 111.75308507147354 14.39426142095353 1;
	setAttr ".wm[32]" -type "matrix" 0.61390804362397833 -0.73015603857474931 0.29998178829157018 0
		 0.78924277487836347 0.56073174706275708 -0.25035125351843079 0 0.014586167285497886 0.39045110727052323 0.92050810781608106 0
		 67.269424984375775 114.55632281891421 4.4695989362216277 1;
	setAttr ".wm[33]" -type "matrix" 0.50020916339506827 -0.79997810355277521 0.33139979887095738 0
		 0.86578174881405623 0.45561273760434751 -0.20697583615762272 0 0.014586167285497886 0.39045110727052323 0.92050810781608106 0
		 69.059265137377338 112.10870542964301 5.8779975989464281 1;
	setAttr ".wm[34]" -type "matrix" 0.25990565222728923 -0.89044218578225376 0.37357966448888735 0
		 0.96552384520747436 0.23379616466175179 -0.1144685883778971 0 0.014586167285497886 0.39045110727052323 0.92050810781608106 0
		 70.428648900467536 109.91866752950239 6.7852450803504221 1;
	setAttr ".wm[35]" -type "matrix" 0.075398416111182032 -0.91841447020119238 0.38836830428471947 0
		 0.99704680059255224 0.063740048292152074 -0.042835542156831372 0 0.014586167285497886 0.39045110727052323 0.92050810781608106 0
		 71.024959884817008 107.87569365894711 7.6423624825893128 1;
	setAttr ".wm[36]" -type "matrix" 0.57582335505632165 -0.72287525888694271 0.38194086435051267 0
		 0.7996742313092764 0.59519946657846701 -0.079112064595903614 0 -0.17014284455009948 0.35098284156614257 0.92079447075585585 0
		 67.339951493063168 115.53586716212003 6.3403583786047353 1;
	setAttr ".wm[37]" -type "matrix" 0.48908021595443019 -0.78113055816224797 0.38811801487060954 0
		 0.85548346261653052 0.5163778616781427 -0.038754988818736798 0 -0.17014284455009948 0.35098284156614257 0.92079447075585585 0
		 69.326347738324642 112.82454517840382 7.7404664402525736 1;
	setAttr ".wm[38]" -type "matrix" 0.28399152673820677 -0.87364465919552747 0.39508710710428507 0
		 0.94367736204968711 0.32763139637235039 0.046159554439443674 0 -0.16976998879615451 0.35972583667320107 0.91748322782158753 0
		 71.214183490987068 109.80940339370105 9.2385909622088995 1;
	setAttr ".wm[39]" -type "matrix" 0.033357313033973213 -0.92836675893085419 0.37016543677033731 0
		 0.98491900203585647 0.093447757287088845 0.14560932692209738 0 -0.16976998879615451 0.35972583667320107 0.91748322782158753 0
		 71.98894496605989 107.42600050622039 10.316433929561185 1;
	setAttr ".wm[40]" -type "matrix" 0.4742045030437636 -0.77912609826477952 0.40999099050554538 0
		 0.84129395719823385 0.5382744607576373 0.049850601579231033 0 -0.25952758403444054 0.32128356306972183 0.9107262515303215 0
		 67.016332263469195 116.36370657153769 8.5379874434044396 1;
	setAttr ".wm[41]" -type "matrix" 0.4742045030437636 -0.77912609826477952 0.40999099050554538 0
		 0.84129395719823385 0.5382744607576373 0.049850601579231033 0 -0.25952758403444054 0.32128356306972183 0.9107262515303215 0
		 69.016918689728371 113.15287597237095 10.243820012296258 1;
	setAttr ".wm[42]" -type "matrix" 0.27211618524137282 -0.88209736066926436 0.38452181736541341 0
		 0.92726331844083065 0.34716735534821253 0.14020544088810108 0 -0.25716827176730372 0.31840080665859738 0.91240638221977199 0
		 71.101235688308478 109.7283075420266 12.045893137478227 1;
	setAttr ".wm[43]" -type "matrix" 0.024421448323833639 -0.94908781025167166 0.31406356250519252 0
		 0.96642993937575161 0.10278841186725007 0.23547338419445532 0 -0.25576701339294605 0.29776982858828266 0.91973711681249293 0
		 71.809649545618811 107.43189877369012 13.046938274201887 1;
	setAttr ".wm[44]" -type "matrix" 0.4925952280028133 -0.73766559500499418 0.46173521773283011 0
		 0.76654808758932302 0.6189760808328354 0.17109249185740116 0 -0.4120121002616402 0.26966290308967461 0.87036081479765681 0
		 66.064336710404419 116.52008512188048 10.493698111150977 1;
	setAttr ".wm[45]" -type "matrix" 0.46201126569155582 -0.76148007610461788 0.45463577077677453 0
		 0.78536082128667384 0.58943194042480795 0.18915170629673717 0 -0.4120121002616402 0.26966290308967461 0.87036081479765681 0
		 68.018959873742176 113.69305714918578 12.304048474399616 1;
	setAttr ".wm[46]" -type "matrix" 0.15090576000109357 -0.92181811668155511 0.35704175015838591 0
		 0.89859528200212835 0.27844798159606005 0.33910653297834847 0 -0.4120121002616402 0.26966290308967461 0.87036081479765681 0
		 69.790217584174428 110.7736966134166 14.047030029668099 1;
	setAttr ".wm[47]" -type "matrix" 0.05855952548001532 -0.94539234078712098 0.32063079071823986 0
		 0.90929467787596108 0.18307168180332289 0.37372175225447513 0 -0.4120121002616402 0.26966290308967461 0.87036081479765681 0
		 70.144987607961582 108.60655975144333 14.886412901440259 1;
	setAttr ".wm[48]" -type "matrix" 0.62008096390219725 -0.68156193053703107 0.38855235560829754 0
		 0.38275973751099351 -0.16950411611782035 -0.90816481871939514 0 0.68483179069508537 0.71185791381549712 0.15576818992211192 0
		 64.678224067404216 108.08609166565925 8.6901141454509307 1;
	setAttr ".wm[49]" -type "matrix" 0.62008096390219725 -0.68156193053703107 0.38855235560829754 0
		 0.38275973751099351 -0.16950411611782035 -0.90816481871939514 0 0.68483179069508537 0.71185791381549712 0.15576818992211192 0
		 64.678224067404599 108.08609166565932 8.6901141454510604 1;
	setAttr ".wm[50]" -type "matrix" 0.73539834240599811 -0.54103722910382057 0.40800489544877999 0
		 0.3254479490608379 -0.24612154125311064 -0.91296649411864372 0 0.59436765594924867 0.8041784028776533 -0.0049179168905499893 0
		 63.206736351268518 118.49111243875846 6.1278909056932864 1;
	setAttr ".wm[51]" -type "matrix" 0.73539834240599811 -0.54103722910382057 0.40800489544877999 0
		 0.3254479490608379 -0.24612154125311064 -0.91296649411864372 0 0.59436765594924867 0.8041784028776533 -0.0049179168905499893 0
		 56.033660919440422 123.76838957143711 2.148211155485872 1;
	setAttr ".wm[52]" -type "matrix" 0.73539834240599811 -0.54103722910382057 0.40800489544877999 0
		 0.3254479490608379 -0.24612154125311064 -0.91296649411864372 0 0.59436765594924867 0.8041784028776533 -0.0049179168905499893 0
		 48.86132088595469 129.04512566688663 -1.8310605898260799 1;
	setAttr ".wm[53]" -type "matrix" 0.80417589873551254 -0.59438396874882926 -0.0029701157083970786 0
		 -0.0036933405436226879 -7.6544673377476613e-16 -0.99999317959455525 0 0.59437991480917274 0.80418138357859958 -0.0021952624102600654 0
		 17.280984521070618 152.36234237309705 -5.7205953988468528 1;
	setAttr ".wm[54]" -type "matrix" 0.80417589873551254 -0.59438396874882926 -0.0029701157083970786 0
		 -0.0036933405436226879 -7.6544673377476613e-16 -0.99999317959455525 0 0.59437991480917274 0.80418138357859958 -0.0021952624102600654 0
		 25.416832088577728 146.34895976126512 -5.7506440594686916 1;
	setAttr ".wm[55]" -type "matrix" 0.80417589873551254 -0.59438396874882926 -0.0029701157083970786 0
		 -0.0036933405436226879 -7.6544673377476613e-16 -0.99999317959455525 0 0.59437991480917274 0.80418138357859958 -0.0021952624102600654 0
		 33.552679656084962 140.33557714943325 -5.7806927200905571 1;
	setAttr ".wm[56]" -type "matrix" 0.92827745102459691 0.0057398191852631175 0.37184409151551373 0
		 -0.37185021696614134 -1.3877787807814459e-16 0.92829274269609241 0 0.005328232494067664 -0.99998352710218208 0.002134353009386442 0
		 -3.0000000000000102 152.45064600349042 2.3345208779416607e-14 1;
	setAttr ".wm[57]" -type "matrix" 0.80417589873551398 0.59438396874882748 0.002970115708397256 0
		 -0.0036933405436220808 -5.9370910965306223e-16 0.99999317959455547 0 0.59437991480917085 -0.80418138357860103 0.0021952624102586594 0
		 -17.280984521070334 152.3623423730962 -5.7205953988467941 1;
	setAttr ".wm[58]" -type "matrix" 0.73539834240599966 0.54103722910381868 -0.40800489544878032 0
		 0.32544794906083968 0.24612154125310848 0.91296649411864372 0 0.5943676559492459 -0.80417840287765541 0.0049179168905485095 0
		 -41.688245454126729 134.32240279956574 -5.8107403400337061 1;
	setAttr ".wm[59]" -type "matrix" 0.62008096390219936 0.68156193053703007 -0.3885523556082966 0
		 0.38275973751099451 0.16950411611781713 0.90816481871939536 0 0.68483179069508293 -0.71185791381549901 -0.1557681899221138 0
		 -63.206486136454856 118.49129652338526 6.127752084508697 1;
	setAttr ".wm[60]" -type "matrix" 0.27106708400437696 -0.63456770130800044 0.72377238716743297 0
		 0.46475174607188074 0.74475299881354284 0.47890373279122939 0 -0.84292849666653324 0.20655944232814755 0.49679447087561518 0
		 -62.67045386015058 115.71528469766488 9.9196900828975938 1;
	setAttr ".wm[61]" -type "matrix" -0.15610830560490546 -0.65932648686930617 0.73547180818420521 0
		 0.69715136444100478 0.45393243919055848 0.55491018706503814 0 -0.69972149601052736 0.59936126364913533 0.38878773599189109 0
		 -61.737667000710488 113.53163183778599 12.410311083433548 1;
	setAttr ".wm[62]" -type "matrix" -0.081680974274700113 -0.74100759328522892 0.66651028884419217 0
		 0.7069891877722303 0.42828393933551456 0.56279583836451363 0 -0.70249164181127277 0.51718528014714971 0.48890170707864777 0
		 -62.158772367562683 111.75308507147417 14.39426142095358 1;
	setAttr ".wm[63]" -type "matrix" -0.61390804362398166 -0.73015603857474731 0.29998178829156913 0
		 -0.78924277487836081 0.56073174706276185 -0.25035125351842769 0 0.014586167285494223 -0.39045110727052024 -0.92050810781608228 0
		 -67.269424984375931 114.55632281891405 4.4695989362214101 1;
	setAttr ".wm[64]" -type "matrix" -0.50020916339507371 -0.79997810355277299 0.33139979887095544 0
		 -0.8657817488140529 0.455612737604354 -0.20697583615762041 0 0.014586167285494223 -0.39045110727052024 -0.92050810781608228 0
		 -69.059265137377153 112.10870542964285 5.8779975989463615 1;
	setAttr ".wm[65]" -type "matrix" -0.25990565222729367 -0.89044218578225376 0.37357966448888508 0
		 -0.96552384520747303 0.23379616466175709 -0.11446858837789474 0 0.014586167285494223 -0.39045110727052024 -0.92050810781608228 0
		 -70.428648900467067 109.9186675295022 6.7852450803502471 1;
	setAttr ".wm[66]" -type "matrix" -0.07539841611118997 -0.91841447020119305 0.38836830428471658 0
		 -0.99704680059255146 0.063740048292160345 -0.042835542156830761 0 0.014586167285494223 -0.39045110727052024 -0.92050810781608228 0
		 -71.024959884816582 107.87569365894683 7.6423624825892205 1;
	setAttr ".wm[67]" -type "matrix" -0.57582335505632398 -0.72287525888694137 0.38194086435051122 0
		 -0.79967423130927429 0.59519946657846945 -0.079112064595903198 0 -0.17014284455009979 -0.35098284156614068 -0.92079447075585652 0
		 -67.339951493063452 115.53586716212008 6.3403583786045763 1;
	setAttr ".wm[68]" -type "matrix" -0.48908021595443474 -0.78113055816224564 0.38811801487060799 0
		 -0.85548346261652752 0.51637786167814703 -0.03875498881873745 0 -0.17014284455009979 -0.35098284156614068 -0.92079447075585652 0
		 -69.326347738324785 112.82454517840347 7.7404664402524146 1;
	setAttr ".wm[69]" -type "matrix" -0.2839915267382106 -0.87364465919552659 0.39508710710428391 0
		 -0.94367736204968544 0.32763139637235406 0.046159554439443556 0 -0.16976998879615529 -0.3597258366731993 -0.91748322782158809 0
		 -71.214183490987153 109.80940339370055 9.2385909622088569 1;
	setAttr ".wm[70]" -type "matrix" -0.033357313033979458 -0.92836675893085419 0.37016543677033648 0
		 -0.98491900203585581 0.093447757287094646 0.14560932692209616 0 -0.16976998879615529 -0.3597258366731993 -0.91748322782158809 0
		 -71.988944966060032 107.42600050621998 10.316433929561104 1;
	setAttr ".wm[71]" -type "matrix" -0.47420450304376627 -0.77912609826477897 0.40999099050554355 0
		 -0.84129395719823163 0.53827446075764041 0.049850601579233308 0 -0.25952758403444232 -0.32128356306971823 -0.91072625153032238 0
		 -67.016332263469522 116.36370657153753 8.5379874434042833 1;
	setAttr ".wm[72]" -type "matrix" -0.47420450304376627 -0.77912609826477897 0.40999099050554355 0
		 -0.84129395719823163 0.53827446075764041 0.049850601579233308 0 -0.25952758403444232 -0.32128356306971823 -0.91072625153032238 0
		 -69.016918689728584 113.15287597237091 10.243820012296066 1;
	setAttr ".wm[73]" -type "matrix" -0.2721161852413766 -0.88209736066926447 0.38452181736541108 0
		 -0.92726331844082888 0.34716735534821624 0.14020544088810258 0 -0.25716827176730539 -0.3184008066585936 -0.91240638221977299 0
		 -71.101235688308648 109.72830754202631 12.045893137478147 1;
	setAttr ".wm[74]" -type "matrix" -0.024421448323838274 -0.94908781025167299 0.31406356250518908 0
		 -0.96642993937575095 0.10278841186725395 0.23547338419445638 0 -0.25576701339294788 -0.29776982858827794 -0.91973711681249415 0
		 -71.809649545618754 107.43189877368974 13.046938274201565 1;
	setAttr ".wm[75]" -type "matrix" -0.49259522800281608 -0.73766559500499407 0.46173521773282844 0
		 -0.76654808758932014 0.61897608083283795 0.17109249185740447 0 -0.41201210026164253 -0.26966290308966978 -0.87036081479765715 0
		 -66.06433671040503 116.52008512188054 10.49369811115092 1;
	setAttr ".wm[76]" -type "matrix" -0.46201126569155887 -0.76148007610461765 0.45463577077677275 0
		 -0.78536082128667095 0.58943194042481073 0.18915170629674025 0 -0.41201210026164253 -0.26966290308966978 -0.87036081479765715 0
		 -68.018959873741935 113.69305714918532 12.304048474399321 1;
	setAttr ".wm[77]" -type "matrix" -0.15090576000109929 -0.92181811668155533 0.3570417501583838 0
		 -0.89859528200212635 0.27844798159606465 0.33910653297834992 0 -0.41201210026164253 -0.26966290308966978 -0.87036081479765715 0
		 -69.790217584174002 110.77369661341632 14.047030029667656 1;
	setAttr ".wm[78]" -type "matrix" -0.058559525480022676 -0.94539234078712131 0.32063079071823819 0
		 -0.90929467787595952 0.183071681803329 0.37372175225447579 0 -0.41201210026164253 -0.26966290308966978 -0.87036081479765715 0
		 -70.14498760796107 108.60655975144284 14.88641290143992 1;
	setAttr ".wm[79]" -type "matrix" 0.62008096390219936 0.68156193053703007 -0.3885523556082966 0
		 0.38275973751099451 0.16950411611781713 0.90816481871939536 0 0.68483179069508293 -0.71185791381549901 -0.1557681899221138 0
		 -64.678224067404528 108.0860916656593 8.6901141454507673 1;
	setAttr ".wm[80]" -type "matrix" 0.62008096390219936 0.68156193053703007 -0.3885523556082966 0
		 0.38275973751099451 0.16950411611781713 0.90816481871939536 0 0.68483179069508293 -0.71185791381549901 -0.1557681899221138 0
		 -64.678224067404699 108.08609166565932 8.6901141454507957 1;
	setAttr ".wm[81]" -type "matrix" 0.73539834240599966 0.54103722910381868 -0.40800489544878032 0
		 0.32544794906083968 0.24612154125310848 0.91296649411864372 0 0.5943676559492459 -0.80417840287765541 0.0049179168905485095 0
		 -48.861320885954441 129.04512566688652 -1.8310605898262855 1;
	setAttr ".wm[82]" -type "matrix" 0.73539834240599966 0.54103722910381868 -0.40800489544878032 0
		 0.32544794906083968 0.24612154125310848 0.91296649411864372 0 0.5943676559492459 -0.80417840287765541 0.0049179168905485095 0
		 -56.033660919439988 123.76838957143708 2.148211155485602 1;
	setAttr ".wm[83]" -type "matrix" 0.73539834240599966 0.54103722910381868 -0.40800489544878032 0
		 0.32544794906083968 0.24612154125310848 0.91296649411864372 0 0.5943676559492459 -0.80417840287765541 0.0049179168905485095 0
		 -63.20673635126856 118.49111243875835 6.1278909056931541 1;
	setAttr ".wm[84]" -type "matrix" 0.80417589873551398 0.59438396874882748 0.002970115708397256 0
		 -0.0036933405436220808 -5.9370910965306223e-16 0.99999317959455547 0 0.59437991480917085 -0.80418138357860103 0.0021952624102586594 0
		 -17.280984521070536 152.36234237309625 -5.7205953988468137 1;
	setAttr ".wm[85]" -type "matrix" 0.80417589873551398 0.59438396874882748 0.002970115708397256 0
		 -0.0036933405436220808 -5.9370910965306223e-16 0.99999317959455547 0 0.59437991480917085 -0.80418138357860103 0.0021952624102586594 0
		 -25.416832088577561 146.34895976126418 -5.7506440594686659 1;
	setAttr ".wm[86]" -type "matrix" 0.80417589873551398 0.59438396874882748 0.002970115708397256 0
		 -0.0036933405436220808 -5.9370910965306223e-16 0.99999317959455547 0 0.59437991480917085 -0.80418138357860103 0.0021952624102586594 0
		 -33.552679656084806 140.33557714943228 -5.7806927200905243 1;
	setAttr ".wm[87]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 157.47182626765263 -4.0901220894534918 1;
	setAttr ".wm[88]" -type "matrix" 0 1 0 0 0 0 1 0 1 0 0 0 0 163.68778453953527 -2.3517326116629924 1;
	setAttr ".wm[89]" -type "matrix" 0 0.99987202616752791 0.015997852594718635 0 0 -0.015997852594718635 0.99987202616752791 0
		 1 0 0 0 0 169.90374281141791 -0.61334313387248329 1;
	setAttr ".wm[90]" -type "matrix" 0 -0.74317002357032025 0.66910261998178566 0 0 -0.66910261998178566 -0.74317002357032025 0
		 1 0 0 0 -3.7617570592466878e-30 172.56537581476567 2.4219002499454723 1;
	setAttr ".wm[91]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.00038016863982193183 173.73568041925822 -1.9793420473600123 1;
	setAttr ".wm[92]" -type "matrix" 1 0 0 0 0 0.89879404994745782 -0.43837113930897276 0
		 0 0.43837113930897276 0.89879404994745782 0 3.1145354407199193 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[93]" -type "matrix" 1 0 0 0 0 0.89879404994745782 -0.43837113930897276 0
		 0 0.43837113930897276 0.89879404994745782 0 -3.1145352227322292 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[94]" -type "matrix" 1 0 0 0 0 0.95630478759499338 -0.29237160125924394 0
		 0 0.29237160125924394 0.95630478759499338 0 3.1145354407199193 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[95]" -type "matrix" 1 0 0 0 0 0.95630478759499338 -0.29237160125924394 0
		 0 0.29237160125924394 0.95630478759499338 0 -3.1145352227322292 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[96]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 1.771983136452036 175.77665028330361 9.1094165061963093 1;
	setAttr ".wm[97]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -1.8346883160702419 175.82334217923744 9.0757727856050696 1;
	setAttr ".wm[98]" -type "matrix" 0.70710678118654746 2.9424051220847856e-08 -0.70710678118654702 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 0.70710678118654768 -2.9424051220847849e-08 0.7071067811865468 0
		 4.7177437441714574 176.23050773638991 8.3592973157929436 1;
	setAttr ".wm[99]" -type "matrix" 0.70710682826502747 -2.9424049261823087e-08 0.70710673410806391 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 -0.70710673410806457 -2.9424053179872489e-08 0.7071068282650268 0
		 -4.7177440030209254 176.23050773638991 8.3592973157929436 1;
	setAttr ".wm[100]" -type "matrix" 1 0 0 0 0 0.98480774000571258 0.17364825143041546 0
		 0 -0.17364825143041546 0.98480774000571258 0 0.014948141790227965 168.15900003619896 10.580414146466676 1;
	setAttr ".wm[101]" -type "matrix" 1 0 0 0 0 0.9961947046198304 -0.087155668131274608 0
		 0 0.087155668131274594 0.9961947046198304 0 -0.08542726279119961 172.34069065676732 11.678945642158972 1;
	setAttr ".wm[102]" -type "matrix" 0.87542610384625508 0.23456973120763089 0.42261824133104509 0
		 -0.14434548178757922 0.96132276271448514 -0.23456966507735219 0 -0.4612954786165559 0.14434537432203826 0.87542612156580812 0
		 -1.8122304891876411 169.38610699978355 9.8613740144363184 1;
	setAttr ".wm[103]" -type "matrix" 0.85672027232130288 0.21360435010389528 0.46947157167437209 0
		 -0.089316058252099706 0.95790282739228394 -0.2728457714757106 0 -0.50798918958184547 0.19182115339701367 0.83973306971764483 0
		 -4.9136492116085719 177.99423638376157 7.6683927718752969 1;
	setAttr ".wm[104]" -type "matrix" 0.96592582198108812 0.066987296027185561 0.25000001720225046 0
		 -0.0090326678882680679 0.97406230094856983 -0.22609963463393323 0 -0.25866139515006786 0.21613730830595637 0.94147700270228385 0
		 0.83738185375113972 171.93069661845894 11.010316026819664 1;
	setAttr ".wm[105]" -type "matrix" 0.71397790464362321 -0.087665492422094454 0.69465841470401324 0
		 0.00029082330565945868 0.9921677706260994 0.1249120904982411 0 -0.70016817058654279 -0.088982449782120429 0.70841136109485581 0
		 -3.5644663674465846 168.89770214461905 7.3554622862346921 1;
	setAttr ".wm[106]" -type "matrix" 0.99026806874157025 5.7912560859831699e-09 -0.13917310096006544 0
		 -0.016960934433661517 0.99254615666318236 -0.12068327803089517 0 0.13813572576990221 0.12186930250536955 0.98288676579394285 0
		 1.8322424786456395 178.00527413777246 9.4113994785724184 1;
	setAttr ".wm[107]" -type "matrix" 0.94422277401706367 -0.17136375218483366 0.28120778343540936 0
		 0.039307209028531992 0.90648125829976578 0.42041250179991158 0 -0.32695304914606388 -0.3859095655570205 0.86265607913332598 0
		 4.9164775731333066 168.10682580766806 5.0382054652149524 1;
	setAttr ".wm[108]" -type "matrix" 0.90673602740601722 0.40370488433265039 0.12186936846441655 0
		 -0.36029276119458359 0.89181925445958321 -0.27358279113631395 0 -0.21913215837648545 0.2041587219325067 0.95409659543682901 0
		 -2.2843517167202663 173.84837547907139 8.6052212126396679 1;
	setAttr ".wm[109]" -type "matrix" 0.69555866798052424 0.22600071389231385 -0.68199839935099804 0
		 -0.1429226911306615 0.97379089199456537 0.17693050338592917 0 0.70411024971742053 -0.025592498678192323 0.70962932595424655 0
		 4.2916873591311742 173.3729949529698 6.4832719969962262 1;
	setAttr ".wm[110]" -type "matrix" 0.73443118078693848 0.4240240945780131 -0.52991924658876055 0
		 0.14743947022835763 0.66247440751579678 0.7344312507004146 0 0.66247448502314754 -0.6175202236395908 0.42402397348431281 0
		 3.2327471869357396 165.40895903135879 2.7427550029999561 1;
	setAttr ".wm[111]" -type "matrix" 0.93740357733598856 0.065549621595868093 0.34202014605331343 0
		 -0.015524236039380745 0.98901461758516374 -0.14700028672851573 0 -0.34789873712487795 0.13248899317117155 0.9281234483598636 0
		 -3.5927947861782741 178.49454436560595 8.9891649637147335 1;
	setAttr ".wm[112]" -type "matrix" 0.71539913001836131 -0.3889177926820217 0.58047139059932618 0
		 0.25490217490126915 0.91878289179766348 0.30143470100591552 0 -0.65056050141364596 -0.06768270292524442 0.75643247268025093 0
		 -3.0096341250173282 167.07382191693731 8.5752099079313684 1;
	setAttr ".wm[113]" -type "matrix" 0.90673602647945972 -0.40370488392012166 -0.121869376724761 0
		 0.36029276640937297 0.89181926218200891 -0.27358275909533897 0 0.21913215363638805 0.20415868901464468 0.95409660356931358 0
		 2.3607870238192845 173.85148823217162 8.6680788406377722 1;
	setAttr ".wm[114]" -type "matrix" 0.73443118078693848 -0.4240240945780131 0.52991924658876055 0
		 -0.14743947022835763 0.66247440751579678 0.7344312507004146 0 -0.66247448502314754 -0.6175202236395908 0.42402397348431281 0
		 -3.2327469689480495 165.40895903135879 2.7427550029999561 1;
	setAttr ".wm[115]" -type "matrix" 0.94584652918820311 0.099412463270238519 0.3090169985116889 0
		 -0.04957415415337664 0.98502189983680344 -0.16514920551389714 0 -0.32080640028310986 0.14088654651327659 0.93660783391393621 0
		 -1.1393774961761665 169.5666643198098 10.35059213775623 1;
	setAttr ".wm[116]" -type "matrix" 0.97442545380217871 -0.085251172007195633 -0.20791169436522211 0
		 0.15839811145451679 0.91686749194040829 0.36642057872143013 0 0.15938968997416511 -0.38998235843984641 0.90692264655572175 0
		 -6.453878532134695 178.29697514212893 5.4615637134280046 1;
	setAttr ".wm[117]" -type "matrix" 0.95994432019227605 0.050308538586853822 0.27563735791043303 0
		 -0.037858255867236297 0.99801593475782346 -0.050308512521824215 0 -0.27762142315260901 0.037858221230304981 0.95994432155828557 0
		 -3.6542927128903102 175.28873240352135 8.6214985858079913 1;
	setAttr ".wm[118]" -type "matrix" 1 0 0 0 0 0.99619470171846003 -0.087155701294111543 0
		 0 0.087155701294111543 0.99619470171846003 0 -0.041902507626218721 177.94445783458883 9.7764211816691766 1;
	setAttr ".wm[119]" -type "matrix" 0.96498034594513504 0.077809484014521507 -0.2505166983196957 0
		 -0.029774010774635696 0.98131248599427146 0.19010342741290737 0 0.26062701360756785 -0.17598718427526644 0.94926396263044976 0
		 0.94328918776591308 168.28158916309542 10.206220006365207 1;
	setAttr ".wm[120]" -type "matrix" 0.96592582198108801 -0.066987296027185797 -0.25000001720225062 0
		 0.0090326625065730737 0.97406229645162823 -0.22609965422225348 0 0.25866139533800125 0.21613732857224457 0.94147699799806672 0
		 -0.87500588686089031 171.9420448953617 11.016587648231509 1;
	setAttr ".wm[121]" -type "matrix" 0.91354545764260087 1.6925081384703515e-08 -0.40673664307579988 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 0.40673664307580026 -3.8014355191365776e-08 0.91354545764260009 0
		 2.5314910197921563 168.81033853797999 9.6460364755999368 1;
	setAttr ".wm[122]" -type "matrix" 0.93740357679045994 -0.065549629397294959 -0.34202014605331293 0
		 0.015524244270334366 0.98901461745596519 -0.14700028672851542 0 0.34789873822750089 0.1324889902758265 0.92812344835986382 0
		 3.6284381049044896 178.53317961599973 9.0736376215721695 1;
	setAttr ".wm[123]" -type "matrix" 1 0 0 0 0 0.98480775734770531 -0.17364815307910161 0
		 0 0.17364815307910161 0.98480775734770531 0 -0.0073873297951649874 169.64738666951132 10.641410832368818 1;
	setAttr ".wm[124]" -type "matrix" 0.9774671443599704 0.12001787514891858 0.17364818266110177 0
		 -0.13642722674428939 0.98692478629871783 0.085831684080485027 0 -0.16107635922017555 -0.10758799112339876 0.98106025842779121 0
		 -3.4994620186917018 176.93788202383215 9.486275265760197 1;
	setAttr ".wm[125]" -type "matrix" 1 0 0 0 0 0.86602539130087086 -0.50000002162217294 0
		 0 0.50000002162217294 0.86602539130087086 0 -0.13011744149844168 177.28852150812418 0.36751588665900403 1;
	setAttr ".wm[126]" -type "matrix" 0.99862953475457317 -0.052335956242942072 -3.9576109935451767e-08 0
		 0.05226422966783472 0.99726094974688873 -0.052335918900514852 0 0.0027390898292204919 0.052264192274159314 0.99862953671160615 0
		 6.4925340311892796 174.34281009865859 1.2130741690048978 1;
	setAttr ".wm[127]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.046596166648669168 171.35147994980971 10.799784642063496 1;
	setAttr ".wm[128]" -type "matrix" 1 0 0 0 0 0.83867058154349994 0.54463901407582582 0
		 0 -0.54463901407582582 0.83867058154349994 0 -3.1145352227322292 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[129]" -type "matrix" 0.89013135954335165 0.10402083765963599 -0.44367310949627314 0
		 -0.019244036206298283 0.98131111324198339 0.19146322387933862 0 0.45529751792426348 -0.16188935839136157 0.87549757613121826 0
		 1.6927850516804028 168.426044131727 9.9039777333235151 1;
	setAttr ".wm[130]" -type "matrix" 1 0 0 0 0 0.96592583275103816 -0.25881902098611959 0
		 0 0.25881902098611959 0.96592583275103816 0 -0.018618152447743341 174.60466644848049 10.463572951568812 1;
	setAttr ".wm[131]" -type "matrix" 1 0 0 0 0 0.7880107689780248 0.61566145565128738 0
		 0 -0.61566145565128738 0.7880107689780248 0 -3.1145352227322292 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[132]" -type "matrix" 0.62874115819630405 0.13364309064319305 -0.7660444375578388 0
		 -0.074637665313063775 0.99094421093259255 0.11161894882051428 0 0.77402440200977207 -0.013003658812687974 0.63302221916051093 0
		 4.2770880358584691 169.58320427160515 5.56080746856823 1;
	setAttr ".wm[133]" -type "matrix" 0.70362049981358643 0.67947840974252394 0.20791171909214184 0
		 -0.66270976692613681 0.73307699385874292 -0.1530159661464576 0 -0.25638634336248167 -0.030119956321336454 0.96610497937254014 0
		 -2.5626086098782253 170.94326097758878 9.6738770594645196 1;
	setAttr ".wm[134]" -type "matrix" 1 0 0 0 0 0.34202026063282914 0.9396925780895854 0
		 0 -0.9396925780895854 0.34202026063282914 0 0.0016029672988224775 164.63711034996408 7.2301986367154782 1;
	setAttr ".wm[135]" -type "matrix" 1 0 0 0 0 0.7986355250728896 0.60181500321240733 0
		 0 -0.60181500321240733 0.7986355250728896 0 3.1145354407199193 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[136]" -type "matrix" 1 0 0 0 0 0.83867058154349994 0.54463901407582582 0
		 0 -0.54463901407582582 0.83867058154349994 0 3.1145354407199193 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[137]" -type "matrix" 0.62874115819630538 -0.13364309064319316 0.76604443755783758 0
		 0.074637678196511528 0.99094421114903508 0.11161893828401369 0 -0.77402440076744505 -0.013003642318663159 0.63302222101838246 0
		 -4.1869007451168727 169.35133170918758 5.652762643856093 1;
	setAttr ".wm[138]" -type "matrix" 0.9774671443599704 -0.12001787514891858 -0.17364818266110177 0
		 0.13642722674428939 0.98692478629871783 0.085831684080485027 0 0.16107635922017555 -0.10758799112339876 0.98106025842779121 0
		 3.4594067232974339 176.96620233610611 9.4917073958449105 1;
	setAttr ".wm[139]" -type "matrix" 1 0 0 0 0 0.76604441637136866 0.64278764156309764 0
		 0 -0.64278764156309764 0.76604441637136866 0 -0.092878448747796938 171.82364109277646 2.0039652346792098 1;
	setAttr ".wm[140]" -type "matrix" 0.85672027232130255 -0.21360435010389572 -0.46947157167437253 0
		 0.089316075162812203 0.95790283377791596 -0.27284574352140634 0 0.50798918660855774 0.19182112150889566 0.83973307880054671 0
		 4.8900741236575413 178.07606926889227 7.6830879428219685 1;
	setAttr ".wm[141]" -type "matrix" 0.71397790464362254 0.08766549242209469 -0.69465841470401402 0
		 -0.0002908116515303456 0.99216776914500782 0.12491210228957628 0 0.70016817059138414 -0.088982466296511992 0.70841135901572361 0
		 3.6371160643466283 169.00388805720908 7.3673794049111017 1;
	setAttr ".wm[142]" -type "matrix" 0.94584652918820311 -0.099412463270238519 -0.3090169985116889 0
		 0.04957415415337664 0.98502189983680344 -0.16514920551389714 0 0.32080640028310986 0.14088654651327659 0.93660783391393621 0
		 1.1652576709457207 169.52375660729004 10.294743060653378 1;
	setAttr ".wm[143]" -type "matrix" 0.94177633515080683 -0.16606058167669757 -0.29237171163283221 0
		 0.14789266666743472 0.98548514431491052 -0.083347402362729986 0 0.30196869654967579 0.035254979050009717 0.95266572981097264 0
		 3.5393220084079076 176.97700698967478 9.4820094821709695 1;
	setAttr ".wm[144]" -type "matrix" 0.94422276319391074 0.17136377285163759 -0.28120780718271027 0
		 -0.039307217692565406 0.90648125672735991 0.42041250438022837 0 0.32695307936112983 -0.38590956007339156 0.86265607013469514 0
		 -4.6801286814443301 168.03799390553831 4.9930573226046011 1;
	setAttr ".wm[145]" -type "matrix" 1 0 0 0 0 0.99619469446502928 0.087155784201204622 0
		 0 -0.087155784201204622 0.99619469446502928 0 -1.0842021724855044e-19 176.43889692614752 10.581535865113834 1;
	setAttr ".wm[146]" -type "matrix" 0.69555866798052435 -0.22600071389231352 0.68199839935099793 0
		 0.14292266769117329 0.97379089114260298 0.17693052700914411 0 -0.704110254475247 -0.025592531095217679 0.70962932006431578 0
		 -4.2028509480587672 173.31472163509829 6.5418905401035907 1;
	setAttr ".wm[147]" -type "matrix" 0.97442545451167129 0.085251163897658314 0.20791169436522206 0
		 -0.15839810382399869 0.91686749325865702 0.36642057872143069 0 -0.15938969321974572 -0.38998235711334572 0.90692264655572163 0
		 6.4538782732852269 178.29697514212893 5.4615637134280046 1;
	setAttr ".wm[148]" -type "matrix" 0.96498034945387479 -0.077809492380588 0.25051668220570228 0
		 0.029774022095477623 0.98131248549216488 0.19010342823170706 0 -0.26062699932304717 -0.175987183376134 0.94926396671905711 0
		 -1.0105417696468066 168.25874675514987 10.223498676679338 1;
	setAttr ".wm[149]" -type "matrix" 1 0 0 0 0 0.49999990630391233 0.86602545787989327 0
		 0 -0.86602545787989327 0.49999990630391233 0 -1.0842021724855044e-19 164.06580405349138 4.4403052438922028 1;
	setAttr ".wm[150]" -type "matrix" 0.89013137248178376 -0.10402085418997307 0.4436730796625869 0
		 0.019244058870619619 0.98131111218187206 0.19146322703475305 0 -0.45529749167097328 -0.16188935419590014 0.87549759055987941 0
		 -1.7157107321254443 168.31817975519797 9.8234427938373781 1;
	setAttr ".wm[151]" -type "matrix" 0.97437007227374584 -9.3606376956012923e-09 0.22495102190755908 0
		 -0.031307131283010756 0.99026806309874271 0.1356061456479489 0 -0.22276181402584139 -0.13917314111086349 0.96488756391884956 0
		 6.8346847193606663 172.03022072856027 3.1918462361647877 1;
	setAttr ".wm[152]" -type "matrix" 0.87542609025688078 -0.23456972756636757 -0.42261827150159004 0
		 0.14434547424494368 0.96132276473552825 -0.23456966143609073 0 0.46129550676605763 0.14434536677940174 0.8754261079764335 0
		 1.7999315047927666 169.3264756530923 9.8381835136028926 1;
	setAttr ".wm[153]" -type "matrix" 1 0 0 0 0 0.9848077573477052 0.17364815307910247 0
		 0 -0.17364815307910247 0.9848077573477052 0 -0.05311459579388611 166.44251521588296 8.7191788682721789 1;
	setAttr ".wm[154]" -type "matrix" 1 0 0 0 0 0.8660253580113535 0.50000007928130064 0
		 0 -0.50000007928130064 0.8660253580113535 0 -1.0842021724855044e-19 160.05837404345681 2.3635264429762581 1;
	setAttr ".wm[155]" -type "matrix" 0.91354545764260087 -1.6925081384703515e-08 0.40673664307579988 0
		 0 0.99999999999999911 4.1611892293014208e-08 0 -0.40673664307580026 -3.8014355191365776e-08 0.91354545764260009 0
		 -2.5757444118789863 168.77057413797408 9.5429175774609813 1;
	setAttr ".wm[156]" -type "matrix" 0.71539913126990617 0.38891780180380614 -0.58047138294523948 0
		 -0.25490218984138613 0.9187828885475019 0.30143469827870595 0 0.65056049418353823 -0.067682694630193135 0.75643247964062632 0
		 2.9995044591196347 167.09051491455259 8.6167748440589165 1;
	setAttr ".wm[157]" -type "matrix" 0.99862953475457328 0.052335956242945202 -3.2291161408623606e-08 0
		 -0.052264233423922869 0.99726094955004052 -0.052335918900514873 0 -0.0027390181587973873 0.052264196030247047 0.99862953671160637 0
		 -6.9118086201779079 174.34017980525829 1.2138194653737164 1;
	setAttr ".wm[158]" -type "matrix" 0.97437006104097956 9.360639723674812e-09 -0.22495107056201727 0
		 0.031307138054402522 0.99026806309874282 0.13560614408464977 0 0.22276186220679772 -0.13917314111086276 0.96488755279539973 0
		 -6.8346849782101344 172.03022072856027 3.1918462361647877 1;
	setAttr ".wm[159]" -type "matrix" 0.94177633791484494 0.16606056600105948 0.29237171163283154 0
		 -0.14789265026427426 0.98548514677654786 -0.083347402362729694 0 -0.30196869596286452 0.035254984076205059 0.95266572981097286 0
		 -3.551861177169485 176.95137222296052 9.5082479225715453 1;
	setAttr ".wm[160]" -type "matrix" 0.99026806874157025 -5.7912560859831699e-09 0.13917310096006544 0
		 0.016960934433661517 0.99254615666318236 -0.12068327803089517 0 -0.13813572576990221 0.12186930250536955 0.98288676579394285 0
		 -1.7928798300854396 177.99712594534574 9.3889852707748407 1;
	setAttr ".wm[161]" -type "matrix" 0.70362049981358643 -0.67947840974252383 -0.20791171909214209 0
		 0.66270976265864834 0.73307699436008233 -0.15301598222703985 0 0.25638635439312463 -0.030119944119448405 0.96610497682562646 0
		 2.5626088278659154 170.94326097758878 9.6738770594645196 1;
	setAttr ".wm[162]" -type "matrix" 0.95994432019227605 -0.050308538586853822 -0.27563735791043303 0
		 0.037858255867236297 0.99801593475782346 -0.050308512521824215 0 0.27762142315260901 0.037858221230304981 0.95994432155828557 0
		 3.5844067232974339 175.29443919271691 8.5714268697368681 1;
	setAttr ".wm[163]" -type "matrix" 0.99999999999940736 8.3402239379980313e-07 6.9982829647245243e-07 0
		 -8.7947943066558237e-09 0.64895493692797401 -0.76082684615936702 0 -1.0887036554986818e-06 0.76082684615890983 0.64895493692759676 0
		 0.011626862018601969 169.74352270442375 3.7983193717464538 1;
	setAttr ".wm[164]" -type "matrix" 0.99999999999486266 -1.0688120739184e-06 -3.0219734489605814e-06 0
		 -3.3268375403896346e-09 0.94242489550192177 -0.33441787682208579 0 3.2054128763278593e-06 0.33441787682037782 0.94242489549707664 0
		 -3.3677978403788295e-07 168.30079252912054 4.1731307138167875 1;
	setAttr ".wm[165]" -type "matrix" 0.999999999984304 -1.8705601604285777e-06 -5.2813842311484129e-06 0
		 1.4469124627593517e-06 0.99686626012934376 -0.079105369056985855 0 5.4128050986450052e-06 0.079105369048102517 0.99686626011640345 0
		 3.8303996476991256e-06 168.36309734008654 6.3178394608422916 1;
	setAttr ".wm[166]" -type "matrix" 0.999999999984304 -1.8705601604285777e-06 -5.2813842311484002e-06 0
		 1.9131637042039094e-06 0.99996737004042247 0.0080782950416859473 0 5.26610096292526e-06 -0.0080782950516633065 0.9999673700283056 0
		 5.8269205086332473e-06 168.3549119374882 8.0548277855297634 1;
	setAttr ".wm[167]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.0016852495900820941 168.32874492339857 7.2708162992640215 1;
	setAttr ".wm[168]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -0.0016852495900820941 170.28831355828493 7.2708161191249232 1;
	setAttr ".wm[169]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 3.1145354407199193 176.28836886323649 7.4668221900267611 1;
	setAttr ".wm[170]" -type "matrix" 1 0 0 0 0 0.99999999999999911 4.1611892293014208e-08 0
		 0 -4.1611892296483655e-08 0.99999999999999911 0 -3.1145352227322292 176.28836886323387 7.4668231437010775 1;
	setAttr ".wm[171]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[172]" -type "matrix" 0 -1 0 0 0 0 1 0 -1 0 0 0 10.250824075415883 9.2384958469890677 -2.4498587588346212 1;
	setAttr ".wm[173]" -type "matrix" -2.2204460492503131e-16 1 0 0 2.2204460492503131e-16 0 -1 0
		 -1 -2.2204460492503131e-16 -2.2204460492503131e-16 0 -10.250824075415798 9.2384958469891103 -2.4498587588346052 1;
	setAttr ".wm[174]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[175]" -type "matrix" 1 0 0 0 0 7.7715611723760958e-16 -1 0 0 1 7.7715611723760958e-16 0
		 76.892426183969576 152.46379243127296 -5.6183477607361212 1;
	setAttr ".wm[176]" -type "matrix" 1 0 0 0 0 0 1 0 0 -1 0 0 -76.892426183968894 152.46379243127274 -5.6183477607361239 1;
	setAttr ".wm[177]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 178 ".xm";
	setAttr ".xm[0]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[1]" -type "matrix" "xform" 1 1 1 0 0 0 1 0 102.48998260498047 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.50000000000000011 0.50000000000000011 0.50000000000000011 0.50000000000000011 1
		 1 1 yes;
	setAttr ".xm[2]" -type "matrix" "xform" 1 1 1 2.2265399197750147e-06 0.018163761283801171
		 -0.026157108857040069 1 -2.050925868474522 0 -10.250824075415816 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 -1 0 0 6.123233995736766e-17 1 1 1 yes;
	setAttr ".xm[3]" -type "matrix" "xform" 1 1 1 -0.0001164535348512944 -3.4396944052691288e-06
		 0.02592352502662747 0 -44.485311800061886 -4.8744477902171905e-15 -2.6645352591003757e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.026176948307873173 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[4]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 -5.5511151231257827e-17
		 -5.5511151231257827e-17 0 -15.603300000000011 7.1054273576010019e-15 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[5]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 -5.5511151231257827e-17
		 -5.5511151231257827e-17 0 -31.206600000000016 5.3290705182007514e-15 -1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[6]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 -5.5511151231257827e-17
		 -5.5511151231257827e-17 0 -46.810000000000215 3.1086244689504383e-15 -3.5527136788005009e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[7]" -type "matrix" "xform" 1 1 1 -0.00036078403730384914 -0.01816031838038815
		 0.00022922964402953297 1 -46.810241652265958 -1.0658141036401503e-14 8.8817841970012523e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.026176948307873104 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[8]" -type "matrix" "xform" 1 1 1 -1.9058241313221761e-21 5.505714157152953e-21
		 1.8175355256292058e-27 0 -6.3411158446336078 -13.232144313816484 2.2408499432913231e-05 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 6.863997566199437e-07 -6.9933909685157904e-07 0.700473633618523 0.71367828088313223 1
		 1 1 yes;
	setAttr ".xm[9]" -type "matrix" "xform" 1 1 1 -3.3306690738754701e-16 1.110223024625157e-16
		 -1.1102230246251565e-16 1 0 2.2204460492503127e-15 -1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[10]" -type "matrix" "xform" 1 1 1 -3.3306690738754701e-16 1.110223024625157e-16
		 -1.1102230246251565e-16 1 -14.828329999999951 2.1689999449292514e-15 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[11]" -type "matrix" "xform" 1 1 1 -3.3306690738754701e-16 1.110223024625157e-16
		 -1.1102230246251565e-16 1 -29.65665999999996 2.1175538406081881e-15 -1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[12]" -type "matrix" "xform" 1 1 1 -1.0213496415969143e-06 0.018160674896577009
		 -0.026156395077294566 1 -2.050925868474522 0 10.250824075415816 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 1 0 6.123233995736766e-17 1 1 1 yes;
	setAttr ".xm[13]" -type "matrix" "xform" 1 1 1 -0.00011645353092074958 2.8305036716500547e-06
		 0.025922248156132126 0 44.485311800062085 -1.5465679670191926e-15 -3.1974423109204508e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.026176948307873173 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[14]" -type "matrix" "xform" 1 1 1 2.2204460492503131e-16 2.2204460492503131e-16
		 2.4651903288156619e-32 0 15.60329919120479 2.0382410313768418e-05 3.730349362740526e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[15]" -type "matrix" "xform" 1 1 1 2.2204460492503131e-16 2.2204460492503131e-16
		 2.4651903288156619e-32 0 31.206599191201509 1.018089498217023e-05 1.7763568394002505e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[16]" -type "matrix" "xform" 1 1 1 2.2204460492503131e-16 2.2204460492503131e-16
		 2.4651903288156619e-32 0 46.809999191198116 -2.0685756219052109e-08 5.3290705182007514e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[17]" -type "matrix" "xform" 1 1 1 -0.00035777261866111205 -0.018163494493094057
		 0.00022985032495144556 1 46.810241652265802 -7.5495165674510645e-15 -4.6185277824406512e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.026176948307873222 0.99965732497555726 1
		 1 1 yes;
	setAttr ".xm[18]" -type "matrix" "xform" 1 1 1 0 -1.6940658945086007e-21 0 0 6.3411153151486479
		 13.232144567317997 -8.2543089616748944e-05 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 
		2.747431038670296e-06 -2.7992232921775686e-06 0.70047358807740434 0.71367832557152999 1
		 1 1 yes;
	setAttr ".xm[19]" -type "matrix" "xform" 1 1 1 3.3306690738754691e-16 -1.1102230246251565e-16
		 -1.110223024625156e-16 1 5.6843418860808015e-14 -2.1191937094044988e-12 1.7763568394002505e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[20]" -type "matrix" "xform" 1 1 1 3.3306690738754691e-16 -1.1102230246251565e-16
		 -1.110223024625156e-16 1 14.828329999996569 1.0201698696894876e-05 -1.5987211554602254e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[21]" -type "matrix" "xform" 1 1 1 3.3306690738754691e-16 -1.1102230246251565e-16
		 -1.110223024625156e-16 1 29.656659999993025 2.0403399513871639e-05 -2.4868995751603507e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[22]" -type "matrix" "xform" 1 1 1 0 0 0 1 6.4125137329101562 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[23]" -type "matrix" "xform" 1 1 1 0 0 0 1 13.764053344726562 -9.1715364335046153e-17
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[24]" -type "matrix" "xform" 1 1 1 0 0 0 1 12.663131713867188 -1.1902919148990496e-14
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[25]" -type "matrix" "xform" 1 1 1 8.3186727614358281e-17 0.0057398507026252569
		 2.7994430273958182e-17 3 17.12096460700613 8.897747231229418e-15 3.0000000000000004 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.69431490382536309 0.13389105394303585 -0.69431490382536309 0.13389105394303585 1
		 1 1 yes;
	setAttr ".xm[26]" -type "matrix" "xform" 1 1 1 -0.00047547496416200548 0.63116819782179689
		 0.0042341740933760424 3 15.384392355224893 2.1094237467877974e-14 4.8316906031686813e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.18935054436666898 0.98190955354759946 1
		 1 1 yes;
	setAttr ".xm[27]" -type "matrix" "xform" 1 1 1 -0.0024824404112824801 -0.0011182590647253955
		 -0.41975123914685347 0 30.350649617122812 -1.0738077094174514e-12 1.1368683772161603e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.0017453283658983088 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[28]" -type "matrix" "xform" 1 1 1 0.096935350391972097 0.18272065590621719
		 -0.0062316162141403154 5 29.26065975608244 6.1284310959308641e-14 -1.1368683772161603e-12 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.0017453283658983088 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[29]" -type "matrix" "xform" 1 1 1 0.0054701176280620304 -0.21186465966806359
		 0.34449856776361631 0 3.0330070101518629 -3.1783308274265307 -1.752554612330556 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.95360976239370576 -0.19208823158104982 -0.22892184008178468 0.036404992639125833 1
		 1 1 yes;
	setAttr ".xm[30]" -type "matrix" "xform" 1 1 1 0.23615432433658992 0.36910017659167943
		 -0.22861602156432839 0 3.4411660968213704 6.2172489379008766e-15 -4.2632564145606011e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[31]" -type "matrix" "xform" 1 1 1 0.019350598041366397 -0.12819714213518779
		 -0.02365433319016055 0 2.6975205785491374 7.638334409421077e-14 3.694822225952521e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[32]" -type "matrix" "xform" 1 1 1 -0.45118401938200553 0.086418352979909366
		 -0.05283765625537807 0 4.5569999999993911 3.7279999999999198 -0.27699999999961733 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654768 0 0 0.70710678118654735 1
		 1 1 yes;
	setAttr ".xm[33]" -type "matrix" "xform" 1 1 1 4.5340068621794154e-17 -5.2527164765853196e-17
		 -0.13718287920675379 0 3.3084338330974106 -0.31243273655039161 0.36687437614595808 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[34]" -type "matrix" "xform" 1 1 1 -2.3908537558525959e-17 -3.1130785202470279e-17
		 -0.26094864309672838 0 2.7376223054288005 -2.8421709430404007e-14 2.5757174171303632e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[35]" -type "matrix" "xform" 1 1 1 -1.9839933078623883e-17 -8.5499104281768163e-17
		 -0.18747504961705855 0 2.2943363456669061 1.4210854715202004e-13 5.3290705182007514e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[36]" -type "matrix" "xform" 1 1 1 -0.28071556545568072 -0.0039329379183900932
		 -0.060785993592368665 0 4.6599999999993571 1.8899999999999046 0.76000000000021828 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654768 0 0 0.70710678118654735 1
		 1 1 yes;
	setAttr ".xm[37]" -type "matrix" "xform" 1 1 1 8.6057841873477233e-17 -5.1077231355009948e-17
		 -0.10471975511966015 0 3.6385194145723432 -0.13607294733958497 -0.0003868401918571962 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[38]" -type "matrix" "xform" 1 1 1 -0.0030636142463255694 -0.0088407276601592463
		 -0.22540489895161764 0 3.8599716183124997 1.9895196601282805e-13 -8.8817841970012523e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[39]" -type "matrix" "xform" 1 1 1 1.0730841483456213e-17 -8.2572373351206168e-17
		 -0.25846504529092351 0 2.728114757406459 -5.6843418860808015e-14 6.7501559897209518e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[40]" -type "matrix" "xform" 1 1 1 -0.18690868893923379 -0.058801801996214716
		 -0.16707685935614752 0 4.7489999999992989 -0.37000000000012534 1.4700000000003968 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654768 0 0 0.70710678118654735 1
		 1 1 yes;
	setAttr ".xm[41]" -type "matrix" "xform" 1 1 1 -1.3886164620156668e-16 -1.6614104955093601e-16
		 7.2378107283146636e-17 0 4.1497049935348542 0.039809941666760551 0.002752044032463985 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[42]" -type "matrix" "xform" 1 1 1 -0.0014224791846644098 0.0038309351522521347
		 -0.22870229334323908 0 4.3953968914290584 -1.4210854715202004e-13 -2.042810365310288e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[43]" -type "matrix" "xform" 1 1 1 -0.00096001621030559407 0.021918902252160338
		 -0.2660027855896957 0 2.6033506852285626 4.5474735088646412e-13 1.5987211554602254e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[44]" -type "matrix" "xform" 1 1 1 -0.033297389784642695 -0.10594679818669545
		 -0.11676291195887621 0 4.8119999999992586 -2.5370000000000994 1.2340000000000373 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654757 0 0 0.70710678118654746 1
		 1 1 yes;
	setAttr ".xm[45]" -type "matrix" "xform" 1 1 1 -5.4543331614883537e-17 -4.9656591397746886e-17
		 -0.039409534510032478 0 3.8841418335248648 0.058187307654151255 0.00798505224690782 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[46]" -type "matrix" "xform" 1 1 1 -1.0791418566106344e-16 -2.6993118119208252e-17
		 -0.36537387320022174 0 3.8337976624462442 1.7053025658242404e-13 6.2172489379008766e-15 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[47]" -type "matrix" "xform" 1 1 1 5.6854771784966719e-17 -2.4887643802775351e-17
		 -0.10207042227713424 0 2.3509375903510943 1.1368683772161603e-13 3.3306690738754696e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[48]" -type "matrix" "xform" 1 1 1 -1.8022395907300292e-16 -7.2374718546320238e-17
		 -1.6613983649056767e-16 0 8.9999999999993889 -7.3718808835110394e-14 -5.9999999999997158 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[49]" -type "matrix" "xform" 1 1 1 -1.8022395907300292e-16 -7.2374718546320238e-17
		 -1.6613983649056767e-16 0 2.4158453015843406e-13 1.865174681370263e-14 3.4106051316484809e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[50]" -type "matrix" "xform" 1 1 1 0 0 0 0 29.261000000000386 -1.5987211554602254e-14
		 -9.6633812063373625e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[51]" -type "matrix" "xform" 1 1 1 0 0 0 0 19.507000000000396 3.5527136788005009e-15
		 -9.6633812063373625e-13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[52]" -type "matrix" "xform" 1 1 1 0 0 0 0 9.7540000000003957 5.3290705182007514e-15
		 -1.0231815394945443e-12 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[53]" -type "matrix" "xform" 1 1 1 2.2204460492503136e-16 8.6736173798840374e-19
		 4.3368086899420197e-19 3 -3.5527136788005009e-15 8.8817841970012523e-15 2.8421709430404007e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[54]" -type "matrix" "xform" 1 1 1 2.2204460492503136e-16 8.6736173798840374e-19
		 4.3368086899420197e-19 3 10.116999999999951 -5.3290705182007514e-15 2.2737367544323206e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[55]" -type "matrix" "xform" 1 1 1 2.2204460492503136e-16 8.6736173798840374e-19
		 4.3368086899420197e-19 3 20.23399999999998 7.1054273576010019e-15 2.8421709430404007e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[56]" -type "matrix" "xform" 1 1 1 -1.3917558816227442e-16 0.0057398507026223695
		 1.3837902495475858e-16 3 17.120964607006044 3.5339843292742149e-14 -3.0000000000000102 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.13389105394303569 -0.69431490382536287 0.13389105394303574 0.69431490382536309 1
		 1 1 yes;
	setAttr ".xm[57]" -type "matrix" "xform" 1 1 1 -0.00047547496416176435 0.63116819782179678
		 0.00423417409337613 3 -15.384392355224771 -5.1958437552457326e-14 8.5265128291212022e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.18935054436666907 0.98190955354759946 1
		 1 1 yes;
	setAttr ".xm[58]" -type "matrix" "xform" 1 1 1 -0.0024824404112819593 -0.0011182590647263774
		 -0.41975123914685381 0 -30.350649617122738 9.6544994221403613e-13 -5.6843418860808015e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 -0.0017453283658983088 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[59]" -type "matrix" "xform" 1 1 1 0.096935350391972402 0.18272065590621761
		 -0.0062316162141397629 5 -29.260659756081694 -4.7961634663806763e-14 5.1159076974727213e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.0017453283658985528 0.99999847691328769 1
		 1 1 yes;
	setAttr ".xm[60]" -type "matrix" "xform" 1 1 1 -0.0054701176280619272 0.21186465966806045
		 0.34449856776361626 0 -3.0330070101527724 3.1783308274263442 1.752554612330357 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.19208823158104976 -0.95360976239370576 0.036404992639125867 0.22892184008178459 1
		 1 1 yes;
	setAttr ".xm[61]" -type "matrix" "xform" 1 1 1 -0.23615432433659145 -0.36910017659167943
		 -0.228616021564329 0 3.441166096821263 1.3322676295501878e-14 -2.8421709430404007e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[62]" -type "matrix" "xform" 1 1 1 -0.019350598041364978 0.12819714213518463
		 -0.023654333190161372 0 2.6975205785490841 1.4477308241112041e-13 9.0949470177292824e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[63]" -type "matrix" "xform" 1 1 1 0.45118401938200281 -0.08641835297990981
		 -0.052837656255376744 0 -4.5570000000001016 -3.7280000000000584 0.27699999999967417 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -4.3297802811774664e-17 -0.70710678118654757 0.70710678118654757 4.3297802811774664e-17 1
		 1 1 yes;
	setAttr ".xm[64]" -type "matrix" "xform" 1 1 1 -2.6739157986718965e-16 -1.5747457012321151e-16
		 -0.13718287920675176 0 3.30843383309724 -0.31243273655070425 -0.36687437614609664 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[65]" -type "matrix" "xform" 1 1 1 -2.2737953868792931e-16 2.6150332185218764e-17
		 -0.2609486430967301 0 2.7376223054286442 -2.8421709430404007e-13 -1.4388490399142029e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[66]" -type "matrix" "xform" 1 1 1 -1.45962414475733e-16 6.9911521254230497e-17
		 -0.18747504961705519 0 2.294336345667034 1.4210854715202004e-13 -4.7961634663806763e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[67]" -type "matrix" "xform" 1 1 1 0.28071556545568149 0.0039329379183895763
		 -0.060785993592368276 0 -4.660000000000025 -1.8900000000000077 -0.76000000000041723 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -4.3297802811774664e-17 -0.70710678118654757 0.70710678118654757 4.3297802811774664e-17 1
		 1 1 yes;
	setAttr ".xm[68]" -type "matrix" "xform" 1 1 1 -2.6543659857501778e-16 2.9181938188443467e-16
		 -0.10471975511965781 0 3.6385194145725706 -0.13607294733995445 0.00038684019197710029 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[69]" -type "matrix" "xform" 1 1 1 0.0030636142463251977 0.0088407276601595274
		 -0.22540489895161891 0 3.8599716183126276 5.6843418860808015e-14 -6.3948846218409017e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[70]" -type "matrix" "xform" 1 1 1 7.3630005448326095e-17 7.9541152609461288e-17
		 -0.25846504529092135 0 2.728114757406388 0 -5.595524044110789e-14 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[71]" -type "matrix" "xform" 1 1 1 0.1869086889392331 0.058801801996214105
		 -0.16707685935614749 0 -4.7490000000001231 0.36999999999997613 -1.470000000000482 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 4.3297802811774652e-17 0.70710678118654768 -0.70710678118654735 4.3297802811774677e-17 1
		 1 1 yes;
	setAttr ".xm[72]" -type "matrix" "xform" 1 1 1 2.7922662873844912e-20 5.5402379462248942e-17
		 -7.6280188864810697e-21 0 4.1497049935346979 0.039809941666703708 -0.0027520440325066176 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[73]" -type "matrix" "xform" 1 1 1 0.0014224791846644601 -0.0038309351522523389
		 -0.22870229334323847 0 4.3953968914292716 -3.1263880373444408e-13 -2.4868995751603507e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[74]" -type "matrix" "xform" 1 1 1 0.00096001621030529472 -0.021918902252161272
		 -0.26600278558969542 0 2.6033506852285058 1.7053025658242404e-13 1.7408297026122455e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[75]" -type "matrix" "xform" 1 1 1 0.033297389784640981 0.10594679818669464
		 -0.11676291195887627 0 -4.8120000000001539 2.5369999999999648 -1.234000000000492 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -4.3297802811774664e-17 -0.70710678118654757 0.70710678118654757 4.3297802811774664e-17 1
		 1 1 yes;
	setAttr ".xm[76]" -type "matrix" "xform" 1 1 1 -1.7241326764158395e-16 -5.544961232052635e-17
		 -0.0394095345100322 0 3.8841418335247084 0.058187307653128073 -0.0079850522469251395 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[77]" -type "matrix" "xform" 1 1 1 -6.6643915676035942e-17 -1.357978043088925e-16
		 -0.36537387320021963 0 3.83379766244596 8.5265128291212022e-14 -1.1546319456101628e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[78]" -type "matrix" "xform" 1 1 1 6.6262450616397687e-17 -7.3042685174252666e-17
		 -0.10207042227713262 0 2.3509375903512932 0 -1.2034817586936697e-13 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[79]" -type "matrix" "xform" 1 1 1 -2.7924275431752929e-20 8.6007921725726606e-22
		 -5.5511158262293034e-17 0 -9.0000000000000568 -1.5099033134902129e-14 5.9999999999995168 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[80]" -type "matrix" "xform" 1 1 1 -2.7924275431752929e-20 8.6007921725726606e-22
		 -5.5511158262293034e-17 0 -9.9475983006414026e-14 -3.5527136788005009e-14 -1.4210854715202004e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[81]" -type "matrix" "xform" 1 1 1 1.3877787807814451e-17 1.1102230246251565e-16
		 -1.1102230246251565e-16 0 -9.7540000000000191 6.2172489379008766e-15 7.1054273576010019e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[82]" -type "matrix" "xform" 1 1 1 1.3877787807814451e-17 1.1102230246251565e-16
		 -1.1102230246251565e-16 0 -19.506999999999806 2.8421709430404007e-14 7.1054273576010019e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[83]" -type "matrix" "xform" 1 1 1 1.3877787807814451e-17 1.1102230246251565e-16
		 -1.1102230246251565e-16 0 -29.261000000000251 -5.3290705182007514e-15 5.1159076974727213e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[84]" -type "matrix" "xform" 1 1 1 2.220437578920841e-16 4.3368086899420177e-19
		 4.3368086899420187e-19 3 -1.2789769243681803e-13 -1.865174681370263e-14 -1.7053025658242404e-13 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[85]" -type "matrix" "xform" 1 1 1 2.220437578920841e-16 4.3368086899420177e-19
		 4.3368086899420187e-19 3 -10.117000000000104 -1.6875389974302379e-14 8.5265128291212022e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[86]" -type "matrix" "xform" 1 1 1 2.220437578920841e-16 4.3368086899420177e-19
		 4.3368086899420187e-19 3 -20.234000000000151 -1.9539925233402755e-14 5.6843418860808015e-14 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[87]" -type "matrix" "xform" 1 1 1 0 0 0 1 22.142144871168256 -4.0901220894534793
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[88]" -type "matrix" "xform" 1 1 1 0 0 -5.5511151231257827e-17 1 6.2159582718826414
		 1.7383894777904993 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[89]" -type "matrix" "xform" 1 1 1 0 0 -1.0408340855860843e-16 1 6.2159582718826414
		 1.7383894777905091 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.0079991822229547836 0.99996800603007496 1
		 1 1 yes;
	setAttr ".xm[90]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.7098497602150928 2.9922745396408477
		 -3.7617570592466878e-30 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0.93069079510034292 0.36580683962371668 1
		 1 1 yes;
	setAttr ".xm[91]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 -2.2204460492503131e-16
		 1.2325951644078309e-32 0 3.8095941708363057 -1.4271268743738053 -0.00038016863982193183 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.50398358380708985 -0.49598442238941554 -0.50398358380708985 0.49598442238941554 1
		 1 1 yes;
	setAttr ".xm[92]" -type "matrix" "xform" 1 1 1 -3.3306690738754696e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.2249510705620176 0 0 0.97437006104097956 1
		 1 1 yes;
	setAttr ".xm[93]" -type "matrix" "xform" 1 1 1 -3.3306690738754696e-16 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.2249510705620176 0 0 0.97437006104097956 1
		 1 1 yes;
	setAttr ".xm[94]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.14780937820575341 0 0 0.98901586828241972 1
		 1 1 yes;
	setAttr ".xm[95]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.14780937820575341 0 0 0.98901586828241972 1
		 1 1 yes;
	setAttr ".xm[96]" -type "matrix" "xform" 1 1 1 0 0 0 0 1.7723633050918579 2.0409703254696296
		 11.088758468627695 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[97]" -type "matrix" "xform" 1 1 1 0 0 0 0 -1.8343081474304199 2.087662220003466
		 11.055114746093517 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[98]" -type "matrix" "xform" 1 1 1 0 0 0 0 4.7181239128112793 2.4948277473420433
		 10.338639259338461 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.38268343236508984 0 0.92387953251128674 1
		 1 1 yes;
	setAttr ".xm[99]" -type "matrix" "xform" 1 1 1 0 0 0 0 -4.7173638343811035 2.4948277473420433
		 10.338639259338461 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.38268340160958941 0 0.92387954525063154 1
		 1 1 yes;
	setAttr ".xm[100]" -type "matrix" "xform" 1 1 1 -3.0531133177191805e-16 0 0 0 0.015328310430049896
		 -5.5766798604240364 12.559756425882901 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.087155759329076835 0 0 0.9961946966410592 1
		 1 1 yes;
	setAttr ".xm[101]" -type "matrix" "xform" 1 1 1 -5.5511151231257815e-17 0 0 0 -0.085047094151377678
		 -1.3949891941437045 13.658287747567137 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.043619370736421366 0 0 0.9990482223078917 1
		 1 1 yes;
	setAttr ".xm[102]" -type "matrix" "xform" 1 1 1 -3.3306690738754691e-16 3.4694469519536152e-16
		 4.163336342344337e-16 0 -1.8118503205478191 -4.3495729267600609 11.8407162427903 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.098332643782895232 -0.22938533821280857 0.098332673562086484 0.96335027019760255 1
		 1 1 yes;
	setAttr ".xm[103]" -type "matrix" "xform" 1 1 1 -7.4246164771807344e-16 -1.6653345369377343e-16
		 1.5959455978986633e-16 0 -4.91326904296875 4.2585563659638694 9.6477346420287287 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12153640868793751 -0.25566065496168372 0.079230633872962697 0.95581851704384235 1
		 1 1 yes;
	setAttr ".xm[104]" -type "matrix" "xform" 1 1 1 -1.3183898417423731e-16 -3.4694469519536088e-18
		 7.2858385991025873e-17 0 0.83776202239096165 -1.8049832602750371 12.989658149288456 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.11223472806194172 -0.12909248220815037 0.019293005126064081 0.98507171150500816 1
		 1 1 yes;
	setAttr ".xm[105]" -type "matrix" "xform" 1 1 1 3.4694469519536123e-17 -3.2699537522162814e-16
		 1.1796119636642288e-16 0 -3.5640861988067627 -4.8379778862002922 9.3348045349121271 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.05787651514671753 -0.37741837077132329 -0.023799602570385429 0.92392600424291738 1
		 1 1 yes;
	setAttr ".xm[106]" -type "matrix" "xform" 1 1 1 1.8117018302232779e-16 -5.5294310796760726e-17
		 -8.6736173798840401e-18 0 1.8326226472854614 4.2695941925045418 11.390741348266546 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.060899828360838924 0.069626363859212809 0.0042585308451804482 0.99570339221899073 1
		 1 1 yes;
	setAttr ".xm[107]" -type "matrix" "xform" 1 1 1 -5.3429483060085649e-16 1.0755285551056199e-16
		 -9.7144514654701197e-17 0 4.9168577417731285 -5.6288543195767318 7.0175477468022507 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.20921603848139034 -0.15779924475825963 -0.05466270524947564 0.96350404059904449 1
		 1 1 yes;
	setAttr ".xm[108]" -type "matrix" "xform" 1 1 1 -9.7144514654701222e-17 -1.0408340855860836e-16
		 8.4307560932472815e-16 0 -2.2839715480804443 0.11269550025687636 10.584563255310215 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12330875616651776 -0.088015096329933679 0.19719363355601482 0.96858812936958649 1
		 1 1 yes;
	setAttr ".xm[109]" -type "matrix" "xform" 1 1 1 1.3877787807814457e-16 8.8470897274817211e-17
		 -5.9674487573602184e-16 0 4.2920675277709961 -0.36268511414303362 8.46261405944826 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.055087298001327896 0.37702881334098826 0.10034909028199568 0.91909995299160741 1
		 1 1 yes;
	setAttr ".xm[110]" -type "matrix" "xform" 1 1 1 2.7755575615628914e-17 -4.163336342344337e-17
		 -1.1102230246251565e-16 0 3.2331273555755615 -8.3267211914040331 4.7220973968505984 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.40247134790242234 0.35497156861833118 0.082338296552528834 0.8397811646560529 1
		 1 1 yes;
	setAttr ".xm[111]" -type "matrix" "xform" 1 1 1 1.1188966420050401e-16 5.6812193838240432e-16
		 -1.9428902930940237e-16 0 -3.5924146175384521 4.7588644027680687 10.968506813049402 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.071178513297624924 -0.17570400627580265 0.020647360863762159 0.98164933041933766 1
		 1 1 yes;
	setAttr ".xm[112]" -type "matrix" "xform" 1 1 1 8.3266726846886716e-17 -8.3266726846886778e-17
		 4.7184478546569153e-16 0 -3.0092539563775063 -6.6618580631260329 10.554552232503909 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.10022942454785251 -0.33427208185320906 -0.17482165279032458 0.92068106718015374 1
		 1 1 yes;
	setAttr ".xm[113]" -type "matrix" "xform" 1 1 1 -1.2490009027033014e-16 -7.6327832942979488e-17
		 4.9266146717741321e-16 0 2.3611671924591064 0.11580825597272337 10.647420883178793 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12330873915487948 0.088015097063470743 -0.19719363440328894 0.96858813129614785 1
		 1 1 yes;
	setAttr ".xm[114]" -type "matrix" "xform" 1 1 1 2.7755575615628914e-17 4.163336342344337e-17
		 1.1102230246251565e-16 0 -3.2323668003082275 -8.3267211914040331 4.7220973968505984 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.40247134790242234 -0.35497156861833118 -0.082338296552528834 0.8397811646560529 1
		 1 1 yes;
	setAttr ".xm[115]" -type "matrix" "xform" 1 1 1 -3.469446951953613e-17 4.4408920985006262e-16
		 5.8980598183211429e-17 0 -1.1389973275363445 -4.1690155863765028 12.32993435859688 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.077808752997641284 -0.1601308337930652 0.037879433399091125 0.98329500280996718 1
		 1 1 yes;
	setAttr ".xm[116]" -type "matrix" "xform" 1 1 1 5.8980598183211441e-17 -3.4694469519536134e-18
		 -2.0816681711721685e-17 0 -6.453498363494873 4.5612950325008796 7.4409055709839063 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.19405880798787045 0.094232943552212026 -0.062509402879856762 0.97445056618764203 1
		 1 1 yes;
	setAttr ".xm[117]" -type "matrix" "xform" 1 1 1 -1.8214596497756474e-17 2.1328169501319585e-34
		 2.3418766925686896e-17 0 -3.6539125442504883 1.5530524253841804 10.600840568542562 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.022271436555334249 -0.13975629904335413 0.022271434205425059 0.9896848706582817 1
		 1 1 yes;
	setAttr ".xm[118]" -type "matrix" "xform" 1 1 1 -4.163336342344337e-17 0 0 0 -0.04152233898639679
		 4.208777904510157 11.755763053893986 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.043619387365335972 0 0 0.9990482215818578 1
		 1 1 yes;
	setAttr ".xm[119]" -type "matrix" "xform" 1 1 1 -5.5771359752654348e-16 2.810252031082427e-16
		 -2.3592239273284586e-16 0 0.94366935640573502 -5.4540907490984978 12.185562280680266 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.092741417509509039 0.12948762296653127 0.027254036873643608 0.98685824840799419 1
		 1 1 yes;
	setAttr ".xm[120]" -type "matrix" "xform" 1 1 1 4.3801767768414369e-16 -1.1015494072452725e-16
		 1.1796119636642283e-16 0 -0.87462571822106838 -1.793634983111275 12.995929770228077 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.11223473830961643 0.12909248240885507 -0.019293003783118538 0.98507171033743313 1
		 1 1 yes;
	setAttr ".xm[121]" -type "matrix" "xform" 1 1 1 0 0 0 0 2.5318711884319782 -4.9253413975242211
		 11.625378727912736 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0.20791169081775937 0 0.97814760073380558 1
		 1 1 yes;
	setAttr ".xm[122]" -type "matrix" "xform" 1 1 1 -1.3877787807814466e-17 2.2854981795994433e-16
		 -9.0205620750793981e-17 0 3.6288182735443115 4.797499656676905 11.052979469299153 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.071178512566487204 0.17570400657198948 -0.020647364948590589 0.98164933033342028 1
		 1 1 yes;
	setAttr ".xm[123]" -type "matrix" "xform" 1 1 1 -5.5511151231257827e-17 0 0 0 -0.0070071611553430557
		 -4.0882932245734764 12.620753049850459 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.087155751038367382 0 0 0.99619469736640243 1
		 1 1 yes;
	setAttr ".xm[124]" -type "matrix" "xform" 1 1 1 -4.7357950894166824e-16 3.5822039778921066e-16
		 -8.6736173798840429e-17 0 -3.4990818500518799 3.2022020816799568 11.465617179870531 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.048688015940537878 -0.084257614797766528 0.064552940820740229 0.99315811897389183 1
		 1 1 yes;
	setAttr ".xm[125]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.12973727285861975
		 3.5528411865231533 2.3468577861785738 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.25881907725772157 0 0 0.96592581767310759 1
		 1 1 yes;
	setAttr ".xm[126]" -type "matrix" "xform" 1 1 1 -1.6657411127524171e-16 3.4694469519536042e-18
		 -1.2489331400675208e-16 0 6.4929141998291016 0.6071298122428459 3.1924161911010924 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.026167979711321621 0.00068525136350062077 -0.026167977630727021 0.99931476733565505 1
		 1 1 yes;
	setAttr ".xm[127]" -type "matrix" "xform" 1 1 1 6.6174449004242214e-24 0 0 0 -0.046215998008847237
		 -2.3841999376848548 12.77912678863459 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[128]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.28401531278527992 0 0 0.95881974432292516 1
		 1 1 yes;
	setAttr ".xm[129]" -type "matrix" "xform" 1 1 1 1.7347234759768071e-18 5.5511151231257827e-17
		 4.8148248609680896e-35 0 1.6931652203202248 -5.3096357930437819 11.88332000162753 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.091272470475058903 0.23220797725209505 0.031839841846571057 0.9678507198452948 1
		 1 1 yes;
	setAttr ".xm[130]" -type "matrix" "xform" 1 1 1 -1.1102230246251565e-16 0 0 0 -0.01823798380792141
		 0.86898654699550093 12.442914962768659 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.13052620047123084 0 0 0.99144486028752199 1
		 1 1 yes;
	setAttr ".xm[131]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.32556812298130305 0 0 0.94551858643732178 1
		 1 1 yes;
	setAttr ".xm[132]" -type "matrix" "xform" 1 1 1 1.040834085586084e-16 -2.7946395197986366e-15
		 3.4694469519536e-17 0 4.277468204498291 -4.1524758338931633 7.5401496887206267 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.034549684938575846 0.42696043074251805 0.057742631408790664 0.90176321635382595 1
		 1 1 yes;
	setAttr ".xm[133]" -type "matrix" "xform" 1 1 1 1.3877787807814457e-16 -5.8980598183211429e-17
		 -1.3183898417423734e-16 0 -2.5622284412384033 -2.7924189567569329 11.653219223022379 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.033311153148157684 -0.12584862638501892 0.36380196993723207 0.92233433037198231 1
		 1 1 yes;
	setAttr ".xm[134]" -type "matrix" "xform" 1 1 1 -4.4408920985006262e-16 0 0 0 0.0019831359386444092
		 -9.0985696860677194 9.2095410626842007 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.57357636817811142 0 0 0.81915209202419037 1
		 1 1 yes;
	setAttr ".xm[135]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.31730462483585864 0 0 0.94832366576911653 1
		 1 1 yes;
	setAttr ".xm[136]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 3.1149156093597412
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.28401531278527992 0 0 0.95881974432292516 1
		 1 1 yes;
	setAttr ".xm[137]" -type "matrix" "xform" 1 1 1 -2.0816681711721688e-16 9.9052710478275705e-16
		 6.2450045135164969e-17 0 -4.1865205764770508 -4.384348392484327 7.6321048736571449 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.034549677433761368 -0.42696043026196123 -0.057742634962116887 0.90176321664136194 1
		 1 1 yes;
	setAttr ".xm[138]" -type "matrix" "xform" 1 1 1 -4.7357950894166824e-16 -3.5822039778921066e-16
		 8.6736173798840429e-17 0 3.4597868919372559 3.2305223941799568 11.471049308776783 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.048688015940537878 0.084257614797766528 -0.064552940820740229 0.99315811897389183 1
		 1 1 yes;
	setAttr ".xm[139]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.092498280107975006
		 -1.9120391607287957 3.9833073616027934 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.34202014332566871 0 0 0.93969262078590843 1
		 1 1 yes;
	setAttr ".xm[140]" -type "matrix" "xform" 1 1 1 6.8695049648681561e-16 -1.7000290064572714e-16
		 1.7347234759768066e-16 0 4.8904542922973633 4.3403892517060569 9.6624298095701793 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.12153639277857145 0.25566065364290941 -0.079230638128372111 0.95581851906678605 1
		 1 1 yes;
	setAttr ".xm[141]" -type "matrix" "xform" 1 1 1 -2.4286128663675289e-16 -5.5858095926453188e-16
		 -2.7755575615628909e-16 0 3.6374962329864502 -4.7317919731143547 9.3467216491699396 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.057876522835979549 0.37741837096939301 0.023799599429366942 0.92392600376124667 1
		 1 1 yes;
	setAttr ".xm[142]" -type "matrix" "xform" 1 1 1 -3.469446951953613e-17 -4.4408920985006262e-16
		 -5.8980598183211429e-17 0 1.1656378395855427 -4.2119233012202528 12.274085283279499 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.077808752997641284 0.1601308337930652 -0.037879433399091125 0.98329500280996718 1
		 1 1 yes;
	setAttr ".xm[143]" -type "matrix" "xform" 1 1 1 -4.8572257327350592e-17 -1.1535911115245767e-16
		 -9.8879238130678004e-17 0 3.5397021770477295 3.241327047345095 11.46135139465324 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.030105921179207983 0.15086672707386009 -0.079693557372086193 0.98487654103717726 1
		 1 1 yes;
	setAttr ".xm[144]" -type "matrix" "xform" 1 1 1 -4.5102810375396984e-16 -3.4694469519536234e-17
		 -3.8857805861880479e-16 0 -4.6797485128045082 -5.6976862235851797 6.9723996070561256 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.20921603833075894 0.15779925921442625 0.054662713017402921 0.96350403782347371 1
		 1 1 yes;
	setAttr ".xm[145]" -type "matrix" "xform" 1 1 1 -6.9388939039072284e-17 0 0 0 0.00038016863982193172
		 2.7032170295711921 12.56087779998788 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.043619387365336028 0 0 0.9990482215818578 1
		 1 1 yes;
	setAttr ".xm[146]" -type "matrix" "xform" 1 1 1 1.1102230246251565e-16 1.5612511283791245e-17
		 3.2612801348363973e-16 0 -4.2024707794189453 -0.42095842957530749 8.5212326049804865 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.055087313299523107 -0.37702881501127433 -0.10034908400644255 0.91909995207469253 1
		 1 1 yes;
	setAttr ".xm[147]" -type "matrix" "xform" 1 1 1 -4.9613091412936693e-16 2.567390744445674e-16
		 -1.2490009027033018e-16 0 6.4542584419250488 4.5612950325008796 7.4409055709839063 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.19405880759574962 -0.094232944359727552 0.062509398824983659 0.9744505664477553 1
		 1 1 yes;
	setAttr ".xm[148]" -type "matrix" "xform" 1 1 1 4.4669129506402763e-16 -4.1633363423443358e-17
		 -3.8163916471489756e-17 0 -1.0101616010069847 -5.4769331563250319 12.202840951944912 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.092741417404700252 -0.12948761514777815 -0.027254041836092514 0.98685824930671007 1
		 1 1 yes;
	setAttr ".xm[149]" -type "matrix" "xform" 1 1 1 0 0 0 0 0.00038016863982193172
		 -9.6698760986331536 6.4196476936340634 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.50000002882956418 0 0 0.86602538713968136 1
		 1 1 yes;
	setAttr ".xm[150]" -type "matrix" "xform" 1 1 1 -2.8275992658421951e-16 3.3566899260151222e-16
		 1.7347234759768068e-16 0 -1.7153305634856224 -5.4175001729240364 11.802785066629834 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.0912724698860016 -0.23220796194943097 -0.031839851858947485 0.967850723242898 1
		 1 1 yes;
	setAttr ".xm[151]" -type "matrix" "xform" 1 1 1 -4.7791631763161035e-16 -2.7755575615628914e-17
		 3.4694469519536211e-18 0 6.8350648880004883 -1.7054594755150276 5.1711883544922008 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.069308069194843905 -0.11292743993126493 0.0078966558553356606 0.99115156645255609 1
		 1 1 yes;
	setAttr ".xm[152]" -type "matrix" "xform" 1 1 1 -7.6327832942979512e-17 -6.9388939039072284e-18
		 -1.3877787807814457e-17 0 1.8003116734325886 -4.4092042744163109 11.817525744438248 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.098332641213754554 0.22938535412478414 -0.098332670992946125 0.96335026693325188 1
		 1 1 yes;
	setAttr ".xm[153]" -type "matrix" "xform" 1 1 1 -6.3837823915946501e-16 0 0 0 -0.052734427154064178
		 -7.2931647581895334 10.698521219114586 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.087155709584821286 0 0 0.99619470099311724 1
		 1 1 yes;
	setAttr ".xm[154]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 0.00038016863982193172
		 -13.67730619508643 4.3428690594748662 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.2588190692189215 0 0 0.96592581982709791 1
		 1 1 yes;
	setAttr ".xm[155]" -type "matrix" "xform" 1 1 1 0 0 0 0 -2.5753642432391644
		 -4.9651058018210961 11.522259831428451 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 -0.20791169081775937 0 0.97814760073380558 1
		 1 1 yes;
	setAttr ".xm[156]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 4.1633363423443352e-17
		 -1.5265566588595902e-16 0 2.9998846277594566 -6.6451650637811497 10.59611716793683 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.1002294214815517 0.3342720775669995 0.17482165919613274 0.9206810678538071 1
		 1 1 yes;
	setAttr ".xm[157]" -type "matrix" "xform" 1 1 1 -1.736485304507096e-16 -2.1684043449710089e-18
		 -6.0986372202309432e-20 0 -6.9114284515380859 0.60449951887355269 3.1931614875793626 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.026167980651632221 -0.00068521545448785217 0.026167978571037753 0.99931476731103219 1
		 1 1 yes;
	setAttr ".xm[158]" -type "matrix" "xform" 1 1 1 -2.2529721144248782e-16 2.4849913793367762e-16
		 -3.8163916471489787e-17 0 -6.8343048095703125 -1.7054594755150276 5.1711883544922008 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.069308068997686906 0.11292746467747997 -0.0078966575857595724 0.9911515636330811 1
		 1 1 yes;
	setAttr ".xm[159]" -type "matrix" "xform" 1 1 1 -2.1857515797307767e-16 1.8301332671555317e-16
		 1.5092094240998219e-16 0 -3.5514810085296631 3.215692281722653 11.487589836120527 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.030105922434777888 -0.15086672682330721 0.079693549175570949 0.98487654170041727 1
		 1 1 yes;
	setAttr ".xm[160]" -type "matrix" "xform" 1 1 1 1.8117018302232779e-16 5.5294310796760726e-17
		 8.6736173798840401e-18 0 -1.7924996614456177 4.2614459991451383 11.368327140808031 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.060899828360838924 -0.069626363859212809 -0.0042585308451804482 0.99570339221899073 1
		 1 1 yes;
	setAttr ".xm[161]" -type "matrix" "xform" 1 1 1 1.387778780781446e-17 -1.2143064331837647e-16
		 -1.1969591984239966e-16 0 2.5629889965057373 -2.7924189567569329 11.653219223022379 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.033311160824172889 0.12584862941271666 -0.3638019688898721 0.9223343300947543 1
		 1 1 yes;
	setAttr ".xm[162]" -type "matrix" "xform" 1 1 1 -1.8214596497756474e-17 -2.1328169501319585e-34
		 -2.3418766925686896e-17 0 3.5847868919372559 1.5587592124961418 10.550768852233968 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.022271436555334249 0.13975629904335413 -0.022271434205425059 0.9896848706582817 1
		 1 1 yes;
	setAttr ".xm[163]" -type "matrix" "xform" 1 1 1 -1.1102230246175835e-16 -6.3527471044072516e-22
		 1.4823076576950256e-21 0 0.012007030658423901 -3.9921574744150234 5.7776615852276985 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.41895411128867305 -4.9243318443396159e-07 2.3205130541345381e-07 0.90800740780790001 1
		 1 1 yes;
	setAttr ".xm[164]" -type "matrix" "xform" 1 1 1 -3.3306690738512348e-16 -2.46168950295781e-21
		 -2.0117032497289626e-21 0 0.00037983186003789395 -5.4348876341216226 6.1524729873327644 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.1696689694871952 1.5797512067899606e-06 -2.7029024870752511e-07 0.9855011115115927 1
		 1 1 yes;
	setAttr ".xm[165]" -type "matrix" "xform" 1 1 1 -8.3266726842847748e-17 -8.4703294725430015e-22
		 -1.6940658945086003e-21 0 0.00038399903946963095 -5.3725827339102352 8.2971817317656438 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.039583728734186432 2.6756443302910299e-06 -8.3001873204433293e-07 0.99921625707934236 1
		 1 1 yes;
	setAttr ".xm[166]" -type "matrix" "xform" 1 1 1 -1.9949319974541075e-16 9.9741438261644077e-21
		 -9.8599929016320993e-22 0 0.00038599556033056508 -5.3807680642292155 10.034170056793725 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.004039159667283217 2.6368927893606113e-06 -9.4593873754117839e-07 0.99999184255739504 1
		 1 1 yes;
	setAttr ".xm[167]" -type "matrix" "xform" 1 1 1 -2.2204460492503131e-16 0 0 0 -0.0013050809502601624
		 -5.4069351109430386 9.2501585716168435 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[168]" -type "matrix" "xform" 1 1 1 0 0 0 0 -0.0013050809502601624
		 -3.4473664760567146 9.2501583099363867 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[169]" -type "matrix" "xform" 1 1 1 0 0 0 0 3.1149156093597412 2.5526888370510221
		 9.4461641311645685 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[170]" -type "matrix" "xform" 1 1 1 0 0 0 0 -3.1141550540924072
		 2.5526888370484642 9.446165084838885 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1
		 1 1 yes;
	setAttr ".xm[171]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[172]" -type "matrix" "xform" 1 1 1 5.5511151231257839e-17 -5.5511151231257839e-17
		 -5.5511151231257839e-17 0 10.250824075415883 9.2384958469890677 -2.4498587588346212 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.50000000000000011 -0.50000000000000011 -0.50000000000000011 0.50000000000000011 1
		 1 1 yes;
	setAttr ".xm[173]" -type "matrix" "xform" 1 1 1 1.110223024625156e-16 2.7755575615628914e-16
		 -4.4408920985006262e-16 0 -10.250824075415798 9.2384958469891103 -2.4498587588346052 0
		 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.5 -0.50000000000000011 0.5 0.49999999999999989 1
		 1 1 yes;
	setAttr ".xm[174]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[175]" -type "matrix" "xform" 1 1 1 0 0 0 0 76.892426183969576 152.46379243127296
		 -5.6183477607361212 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 -0.70710678118654724 0 0 0.70710678118654779 1
		 1 1 yes;
	setAttr ".xm[176]" -type "matrix" "xform" 1 1 1 0 0 0 0 -76.892426183968894
		 152.46379243127274 -5.6183477607361239 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0.70710678118654757 0 0 0.70710678118654757 1
		 1 1 yes;
	setAttr ".xm[177]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr -s 55 ".m";
	setAttr -s 178 ".p";
createNode nodeGraphEditorInfo -n "t_pose:hyperShadePrimaryNodeEditorSavedTabsInfo1";
	rename -uid "B5964AC7-4712-E3BC-A8F6-1DB755517E36";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "t_pose:hyperShadePrimaryNodeEditorSavedTabsInfo2";
	rename -uid "84D8BAF1-45F3-083C-378D-B6BA61C79410";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "t_pose:hyperShadePrimaryNodeEditorSavedTabsInfo3";
	rename -uid "03040681-419A-7BA3-06A7-20B16007DB73";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "t_pose:hyperShadePrimaryNodeEditorSavedTabsInfo4";
	rename -uid "3DDFA059-4A20-F03F-1F47-CCBB4E0C23A1";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "t_pose:hyperShadePrimaryNodeEditorSavedTabsInfo5";
	rename -uid "ED94D6A0-43E1-F7CB-FF9F-A2BB6CD58C6D";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.444442678380966 -476.98410803048142 ;
	setAttr ".tgi[0].vh" -type "double2" 1039.6824983692691 44.444442678380966 ;
createNode nodeGraphEditorInfo -n "RIG_MDR_AssaultRifle:MDR_AssaultRifle_Base_A:hyperShadePrimaryNodeEditorSavedTabsInfo";
	rename -uid "4C739924-4AAA-BA77-474F-25B88B7506F0";
	setAttr ".def" no;
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -102.38094831269902 -152.3809463258776 ;
	setAttr ".tgi[0].vh" -type "double2" 103.57142445586992 152.3809463258776 ;
createNode skinCluster -n "skinCluster1";
	rename -uid "6A794151-4BB4-D30B-0568-D1B0C403AEE3";
	setAttr -s 42 ".wl";
	setAttr ".wl[0:41].w"
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1
		1 0 1;
	setAttr ".pm[0]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".gm" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".dpf[0]"  4;
	setAttr ".mmi" yes;
	setAttr ".mi" 5;
	setAttr ".ucm" yes;
createNode dagPose -n "bindPose2";
	rename -uid "BD6D4EED-4F2E-7B26-66C2-54B7E72CDE14";
	setAttr -s 3 ".wm";
	setAttr ".wm[0]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr ".wm[1]" -type "matrix" 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1;
	setAttr -s 3 ".xm";
	setAttr ".xm[0]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[1]" -type "matrix" "xform" 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr ".xm[2]" -type "matrix" "xform" 1 1 1 0 0 0 3 0 0 0 0 0 0 0 0 0 0 0
		 0 0 0 0 0 0 0 0 0 0 1 0 0 0 1 1 1 1 yes;
	setAttr -s 3 ".m";
	setAttr -s 3 ".p";
	setAttr -s 3 ".g[0:2]" yes yes no;
	setAttr ".bp" yes;
createNode nodeGraphEditorInfo -n "hyperShadePrimaryNodeEditorSavedTabsInfo";
	rename -uid "1CED311D-40BD-A543-8BC3-5F8B8A267DB9";
	setAttr ".tgi[0].tn" -type "string" "Untitled_1";
	setAttr ".tgi[0].vl" -type "double2" -44.047617297323988 -235.17146291375397 ;
	setAttr ".tgi[0].vh" -type "double2" 1040.4761491313832 335.94472234319824 ;
select -ne :time1;
	setAttr -av -k on ".cch";
	setAttr -av -k on ".fzn";
	setAttr -av -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".o" 8;
	setAttr -av -k on ".unw" 8;
	setAttr -av -k on ".etw";
	setAttr -av -k on ".tps";
	setAttr -av -k on ".tms";
select -ne :hardwareRenderingGlobals;
	setAttr -av -k on ".cch";
	setAttr -av -k on ".fzn";
	setAttr -av -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -av -k on ".rm";
	setAttr -av -k on ".lm";
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr -av -k on ".hom";
	setAttr -av -k on ".hodm";
	setAttr -av -k on ".xry";
	setAttr -av -k on ".jxr";
	setAttr -av -k on ".sslt";
	setAttr -av -k on ".cbr";
	setAttr -av -k on ".bbr";
	setAttr -av -k on ".mhl";
	setAttr -k on ".cons";
	setAttr -k on ".vac";
	setAttr -av -k on ".hwi";
	setAttr -k on ".csvd";
	setAttr -av -k on ".ta";
	setAttr -av -k on ".tq";
	setAttr -k on ".ts";
	setAttr -av -k on ".etmr";
	setAttr -av -k on ".tmr";
	setAttr -av -k on ".aoon";
	setAttr -av -k on ".aoam";
	setAttr -av -k on ".aora";
	setAttr -k on ".aofr";
	setAttr -av -k on ".aosm";
	setAttr -av -k on ".hff";
	setAttr -av -k on ".hfd";
	setAttr -av -k on ".hfs";
	setAttr -av -k on ".hfe";
	setAttr -av ".hfc";
	setAttr -av -k on ".hfcr";
	setAttr -av -k on ".hfcg";
	setAttr -av -k on ".hfcb";
	setAttr -av -k on ".hfa";
	setAttr -av -k on ".mbe";
	setAttr -av -k on ".mbt";
	setAttr -av -k on ".mbsof";
	setAttr -k on ".mbsc";
	setAttr -k on ".mbc";
	setAttr -k on ".mbfa";
	setAttr -k on ".mbftb";
	setAttr -k on ".mbftg";
	setAttr -k on ".mbftr";
	setAttr -av -k on ".mbfta";
	setAttr -k on ".mbfe";
	setAttr -k on ".mbme";
	setAttr -av -k on ".mbcsx";
	setAttr -av -k on ".mbcsy";
	setAttr -av -k on ".mbasx";
	setAttr -av -k on ".mbasy";
	setAttr -av -k on ".blen";
	setAttr -av -k on ".blth";
	setAttr -av -k on ".blfr";
	setAttr -av -k on ".blfa";
	setAttr -av -k on ".blat";
	setAttr -av -k on ".msaa" yes;
	setAttr -av -k on ".aasc";
	setAttr -av -k on ".aasq";
	setAttr -k on ".laa";
	setAttr -k on ".fprt" yes;
	setAttr -k on ".rtfm";
select -ne :renderPartition;
	setAttr -av -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".st";
	setAttr -cb on ".an";
	setAttr -cb on ".pt";
select -ne :renderGlobalsList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :defaultShaderList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 5 ".s";
select -ne :postProcessList1;
	setAttr -k on ".cch";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
	setAttr -av -k on ".cch";
	setAttr -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
select -ne :initialShadingGroup;
	setAttr -av -k on ".cch";
	setAttr -k on ".fzn";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".bbx";
	setAttr -k on ".vwm";
	setAttr -k on ".tpv";
	setAttr -k on ".uit";
	setAttr -k on ".mwc";
	setAttr -av -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr -k on ".ro" yes;
	setAttr -k on ".hio";
	setAttr -cb on ".ai_override";
	setAttr -cb on ".ai_surface_shader";
	setAttr -cb on ".ai_surface_shaderr";
	setAttr -cb on ".ai_surface_shaderg";
	setAttr -cb on ".ai_surface_shaderb";
	setAttr -cb on ".ai_volume_shader";
	setAttr -cb on ".ai_volume_shaderr";
	setAttr -cb on ".ai_volume_shaderg";
	setAttr -cb on ".ai_volume_shaderb";
select -ne :initialParticleSE;
	setAttr -av -k on ".cch";
	setAttr -k on ".fzn";
	setAttr -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -k on ".bbx";
	setAttr -k on ".vwm";
	setAttr -k on ".tpv";
	setAttr -k on ".uit";
	setAttr -k on ".mwc";
	setAttr -av -cb on ".an";
	setAttr -cb on ".il";
	setAttr -cb on ".vo";
	setAttr -cb on ".eo";
	setAttr -cb on ".fo";
	setAttr -cb on ".epo";
	setAttr -k on ".ro" yes;
	setAttr -k on ".hio";
	setAttr -cb on ".ai_override";
	setAttr -cb on ".ai_surface_shader";
	setAttr -cb on ".ai_surface_shaderr";
	setAttr -cb on ".ai_surface_shaderg";
	setAttr -cb on ".ai_surface_shaderb";
	setAttr -cb on ".ai_volume_shader";
	setAttr -cb on ".ai_volume_shaderr";
	setAttr -cb on ".ai_volume_shaderg";
	setAttr -cb on ".ai_volume_shaderb";
select -ne :defaultRenderGlobals;
	addAttr -ci true -h true -sn "dss" -ln "defaultSurfaceShader" -dt "string";
	setAttr -av -k on ".cch";
	setAttr -av -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -av -k on ".macc";
	setAttr -av -k on ".macd";
	setAttr -av -k on ".macq";
	setAttr -av -k on ".mcfr" 30;
	setAttr -cb on ".ifg";
	setAttr -av -k on ".clip";
	setAttr -av -k on ".edm";
	setAttr -av -k on ".edl";
	setAttr -av -k on ".ren" -type "string" "arnold";
	setAttr -av -k on ".esr";
	setAttr -av -k on ".ors";
	setAttr -cb on ".sdf";
	setAttr -av -k on ".outf" 51;
	setAttr -av -cb on ".imfkey" -type "string" "exr";
	setAttr -av -k on ".gama";
	setAttr -av -k on ".exrc";
	setAttr -av -k on ".expt";
	setAttr -av -cb on ".an";
	setAttr -cb on ".ar";
	setAttr -av -k on ".fs";
	setAttr -av -k on ".ef";
	setAttr -av -k on ".bfs";
	setAttr -av -cb on ".me";
	setAttr -cb on ".se";
	setAttr -av -k on ".be";
	setAttr -av -cb on ".ep";
	setAttr -av -k on ".fec";
	setAttr -av -k on ".ofc";
	setAttr -cb on ".ofe";
	setAttr -cb on ".efe";
	setAttr -cb on ".oft";
	setAttr -cb on ".umfn";
	setAttr -cb on ".ufe";
	setAttr -av -cb on ".pff";
	setAttr -av -cb on ".peie";
	setAttr -av -cb on ".ifp";
	setAttr -k on ".rv";
	setAttr -av -k on ".comp";
	setAttr -av -k on ".cth";
	setAttr -av -k on ".soll";
	setAttr -av -cb on ".sosl";
	setAttr -av -k on ".rd";
	setAttr -av -k on ".lp";
	setAttr -av -k on ".sp";
	setAttr -av -k on ".shs";
	setAttr -av -k on ".lpr";
	setAttr -cb on ".gv";
	setAttr -cb on ".sv";
	setAttr -av -k on ".mm";
	setAttr -av -k on ".npu";
	setAttr -av -k on ".itf";
	setAttr -av -k on ".shp";
	setAttr -cb on ".isp";
	setAttr -av -k on ".uf";
	setAttr -av -k on ".oi";
	setAttr -av -k on ".rut";
	setAttr -av -k on ".mot";
	setAttr -av -k on ".mb";
	setAttr -av -k on ".mbf";
	setAttr -av -k on ".mbso";
	setAttr -av -k on ".mbsc";
	setAttr -av -k on ".afp";
	setAttr -av -k on ".pfb";
	setAttr -av -k on ".pram";
	setAttr -av -k on ".poam";
	setAttr -av -k on ".prlm";
	setAttr -av -k on ".polm";
	setAttr -av -cb on ".prm";
	setAttr -av -cb on ".pom";
	setAttr -cb on ".pfrm";
	setAttr -cb on ".pfom";
	setAttr -av -k on ".bll";
	setAttr -av -k on ".bls";
	setAttr -av -k on ".smv";
	setAttr -av -k on ".ubc";
	setAttr -av -k on ".mbc";
	setAttr -cb on ".mbt";
	setAttr -av -k on ".udbx";
	setAttr -av -k on ".smc";
	setAttr -av -k on ".kmv";
	setAttr -cb on ".isl";
	setAttr -cb on ".ism";
	setAttr -cb on ".imb";
	setAttr -av -k on ".rlen";
	setAttr -av -k on ".frts";
	setAttr -av -k on ".tlwd";
	setAttr -av -k on ".tlht";
	setAttr -av -k on ".jfc";
	setAttr -cb on ".rsb";
	setAttr -av -k on ".ope";
	setAttr -av -k on ".oppf";
	setAttr -av -k on ".rcp";
	setAttr -av -k on ".icp";
	setAttr -av -k on ".ocp";
	setAttr -cb on ".hbl";
	setAttr ".dss" -type "string" "lambert1";
select -ne :defaultResolution;
	setAttr -av -k on ".cch";
	setAttr -av -k on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -k on ".bnm";
	setAttr -av -k on ".w";
	setAttr -av -k on ".h";
	setAttr -av -k on ".pa" 1;
	setAttr -av -k on ".al";
	setAttr -av -k on ".dar";
	setAttr -av -k on ".ldar";
	setAttr -av -k on ".dpi";
	setAttr -av -k on ".off";
	setAttr -av -k on ".fld";
	setAttr -av -k on ".zsl";
	setAttr -av -k on ".isu";
	setAttr -av -k on ".pdu";
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
	setAttr -av -k on ".cch";
	setAttr -av -cb on ".ihi";
	setAttr -av -k on ".nds";
	setAttr -cb on ".bnm";
	setAttr -av -k off -cb on ".ctrs" 256;
	setAttr -av -k off -cb on ".btrs" 512;
	setAttr -av -k off -cb on ".fbfm";
	setAttr -av -k off -cb on ".ehql";
	setAttr -av -k off -cb on ".eams";
	setAttr -av -k off -cb on ".eeaa";
	setAttr -av -k off -cb on ".engm";
	setAttr -av -k off -cb on ".mes";
	setAttr -av -k off -cb on ".emb";
	setAttr -av -k off -cb on ".mbbf";
	setAttr -av -k off -cb on ".mbs";
	setAttr -av -k off -cb on ".trm";
	setAttr -av -k off -cb on ".tshc";
	setAttr -av -k off -cb on ".enpt";
	setAttr -av -k off -cb on ".clmt";
	setAttr -av -k off -cb on ".tcov";
	setAttr -av -k off -cb on ".lith";
	setAttr -av -k off -cb on ".sobc";
	setAttr -av -k off -cb on ".cuth";
	setAttr -av -k off -cb on ".hgcd";
	setAttr -av -k off -cb on ".hgci";
	setAttr -av -k off -cb on ".mgcs";
	setAttr -av -k off -cb on ".twa";
	setAttr -av -k off -cb on ".twz";
	setAttr -av -k on ".hwcc";
	setAttr -av -k on ".hwdp";
	setAttr -av -k on ".hwql";
	setAttr -av -k on ".hwfr" 30;
	setAttr -av -k on ".soll";
	setAttr -av -k on ".sosl";
	setAttr -av -k on ".bswa";
	setAttr -av -k on ".shml";
	setAttr -av -k on ".hwel";
connectAttr "skinCluster1.og[0]" "test_cylinderShape.i";
connectAttr "male_average.root_bone" "C_root_JNT.male_average_root_bone";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":defaultRenderGlobals.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr ":defaultArnoldDisplayDriver.msg" ":defaultArnoldRenderOptions.drivers"
		 -na;
connectAttr ":defaultArnoldFilter.msg" ":defaultArnoldRenderOptions.filt";
connectAttr ":defaultArnoldDriver.msg" ":defaultArnoldRenderOptions.drvr";
connectAttr "C_root_JNT.msg" "tpose.m[0]";
connectAttr "tpose.w" "tpose.p[0]";
connectAttr "tpose.m[0]" "tpose.p[1]";
connectAttr "tpose.m[1]" "tpose.p[2]";
connectAttr "tpose.m[2]" "tpose.p[3]";
connectAttr "tpose.m[3]" "tpose.p[4]";
connectAttr "tpose.m[3]" "tpose.p[5]";
connectAttr "tpose.m[3]" "tpose.p[6]";
connectAttr "tpose.m[3]" "tpose.p[7]";
connectAttr "tpose.m[7]" "tpose.p[8]";
connectAttr "tpose.m[2]" "tpose.p[9]";
connectAttr "tpose.m[2]" "tpose.p[10]";
connectAttr "tpose.m[2]" "tpose.p[11]";
connectAttr "tpose.m[1]" "tpose.p[12]";
connectAttr "tpose.m[12]" "tpose.p[13]";
connectAttr "tpose.m[13]" "tpose.p[14]";
connectAttr "tpose.m[13]" "tpose.p[15]";
connectAttr "tpose.m[13]" "tpose.p[16]";
connectAttr "tpose.m[13]" "tpose.p[17]";
connectAttr "tpose.m[17]" "tpose.p[18]";
connectAttr "tpose.m[12]" "tpose.p[19]";
connectAttr "tpose.m[12]" "tpose.p[20]";
connectAttr "tpose.m[12]" "tpose.p[21]";
connectAttr "tpose.m[1]" "tpose.p[22]";
connectAttr "tpose.m[22]" "tpose.p[23]";
connectAttr "tpose.m[23]" "tpose.p[24]";
connectAttr "tpose.m[24]" "tpose.p[25]";
connectAttr "tpose.m[25]" "tpose.p[26]";
connectAttr "tpose.m[26]" "tpose.p[27]";
connectAttr "tpose.m[27]" "tpose.p[28]";
connectAttr "tpose.m[28]" "tpose.p[29]";
connectAttr "tpose.m[29]" "tpose.p[30]";
connectAttr "tpose.m[30]" "tpose.p[31]";
connectAttr "tpose.m[28]" "tpose.p[32]";
connectAttr "tpose.m[32]" "tpose.p[33]";
connectAttr "tpose.m[33]" "tpose.p[34]";
connectAttr "tpose.m[34]" "tpose.p[35]";
connectAttr "tpose.m[28]" "tpose.p[36]";
connectAttr "tpose.m[36]" "tpose.p[37]";
connectAttr "tpose.m[37]" "tpose.p[38]";
connectAttr "tpose.m[38]" "tpose.p[39]";
connectAttr "tpose.m[28]" "tpose.p[40]";
connectAttr "tpose.m[40]" "tpose.p[41]";
connectAttr "tpose.m[41]" "tpose.p[42]";
connectAttr "tpose.m[42]" "tpose.p[43]";
connectAttr "tpose.m[28]" "tpose.p[44]";
connectAttr "tpose.m[44]" "tpose.p[45]";
connectAttr "tpose.m[45]" "tpose.p[46]";
connectAttr "tpose.m[46]" "tpose.p[47]";
connectAttr "tpose.m[28]" "tpose.p[48]";
connectAttr "tpose.m[48]" "tpose.p[49]";
connectAttr "tpose.m[27]" "tpose.p[50]";
connectAttr "tpose.m[27]" "tpose.p[51]";
connectAttr "tpose.m[27]" "tpose.p[52]";
connectAttr "tpose.m[26]" "tpose.p[53]";
connectAttr "tpose.m[26]" "tpose.p[54]";
connectAttr "tpose.m[26]" "tpose.p[55]";
connectAttr "tpose.m[24]" "tpose.p[56]";
connectAttr "tpose.m[56]" "tpose.p[57]";
connectAttr "tpose.m[57]" "tpose.p[58]";
connectAttr "tpose.m[58]" "tpose.p[59]";
connectAttr "tpose.m[59]" "tpose.p[60]";
connectAttr "tpose.m[60]" "tpose.p[61]";
connectAttr "tpose.m[61]" "tpose.p[62]";
connectAttr "tpose.m[59]" "tpose.p[63]";
connectAttr "tpose.m[63]" "tpose.p[64]";
connectAttr "tpose.m[64]" "tpose.p[65]";
connectAttr "tpose.m[65]" "tpose.p[66]";
connectAttr "tpose.m[59]" "tpose.p[67]";
connectAttr "tpose.m[67]" "tpose.p[68]";
connectAttr "tpose.m[68]" "tpose.p[69]";
connectAttr "tpose.m[69]" "tpose.p[70]";
connectAttr "tpose.m[59]" "tpose.p[71]";
connectAttr "tpose.m[71]" "tpose.p[72]";
connectAttr "tpose.m[72]" "tpose.p[73]";
connectAttr "tpose.m[73]" "tpose.p[74]";
connectAttr "tpose.m[59]" "tpose.p[75]";
connectAttr "tpose.m[75]" "tpose.p[76]";
connectAttr "tpose.m[76]" "tpose.p[77]";
connectAttr "tpose.m[77]" "tpose.p[78]";
connectAttr "tpose.m[59]" "tpose.p[79]";
connectAttr "tpose.m[79]" "tpose.p[80]";
connectAttr "tpose.m[58]" "tpose.p[81]";
connectAttr "tpose.m[58]" "tpose.p[82]";
connectAttr "tpose.m[58]" "tpose.p[83]";
connectAttr "tpose.m[57]" "tpose.p[84]";
connectAttr "tpose.m[57]" "tpose.p[85]";
connectAttr "tpose.m[57]" "tpose.p[86]";
connectAttr "tpose.m[24]" "tpose.p[87]";
connectAttr "tpose.m[87]" "tpose.p[88]";
connectAttr "tpose.m[88]" "tpose.p[89]";
connectAttr "tpose.m[89]" "tpose.p[90]";
connectAttr "tpose.m[89]" "tpose.p[91]";
connectAttr "tpose.m[91]" "tpose.p[92]";
connectAttr "tpose.m[91]" "tpose.p[93]";
connectAttr "tpose.m[91]" "tpose.p[94]";
connectAttr "tpose.m[91]" "tpose.p[95]";
connectAttr "tpose.m[91]" "tpose.p[96]";
connectAttr "tpose.m[91]" "tpose.p[97]";
connectAttr "tpose.m[91]" "tpose.p[98]";
connectAttr "tpose.m[91]" "tpose.p[99]";
connectAttr "tpose.m[91]" "tpose.p[100]";
connectAttr "tpose.m[91]" "tpose.p[101]";
connectAttr "tpose.m[91]" "tpose.p[102]";
connectAttr "tpose.m[91]" "tpose.p[103]";
connectAttr "tpose.m[91]" "tpose.p[104]";
connectAttr "tpose.m[91]" "tpose.p[105]";
connectAttr "tpose.m[91]" "tpose.p[106]";
connectAttr "tpose.m[91]" "tpose.p[107]";
connectAttr "tpose.m[91]" "tpose.p[108]";
connectAttr "tpose.m[91]" "tpose.p[109]";
connectAttr "tpose.m[91]" "tpose.p[110]";
connectAttr "tpose.m[91]" "tpose.p[111]";
connectAttr "tpose.m[91]" "tpose.p[112]";
connectAttr "tpose.m[91]" "tpose.p[113]";
connectAttr "tpose.m[91]" "tpose.p[114]";
connectAttr "tpose.m[91]" "tpose.p[115]";
connectAttr "tpose.m[91]" "tpose.p[116]";
connectAttr "tpose.m[91]" "tpose.p[117]";
connectAttr "tpose.m[91]" "tpose.p[118]";
connectAttr "tpose.m[91]" "tpose.p[119]";
connectAttr "tpose.m[91]" "tpose.p[120]";
connectAttr "tpose.m[91]" "tpose.p[121]";
connectAttr "tpose.m[91]" "tpose.p[122]";
connectAttr "tpose.m[91]" "tpose.p[123]";
connectAttr "tpose.m[91]" "tpose.p[124]";
connectAttr "tpose.m[91]" "tpose.p[125]";
connectAttr "tpose.m[91]" "tpose.p[126]";
connectAttr "tpose.m[91]" "tpose.p[127]";
connectAttr "tpose.m[91]" "tpose.p[128]";
connectAttr "tpose.m[91]" "tpose.p[129]";
connectAttr "tpose.m[91]" "tpose.p[130]";
connectAttr "tpose.m[91]" "tpose.p[131]";
connectAttr "tpose.m[91]" "tpose.p[132]";
connectAttr "tpose.m[91]" "tpose.p[133]";
connectAttr "tpose.m[91]" "tpose.p[134]";
connectAttr "tpose.m[91]" "tpose.p[135]";
connectAttr "tpose.m[91]" "tpose.p[136]";
connectAttr "tpose.m[91]" "tpose.p[137]";
connectAttr "tpose.m[91]" "tpose.p[138]";
connectAttr "tpose.m[91]" "tpose.p[139]";
connectAttr "tpose.m[91]" "tpose.p[140]";
connectAttr "tpose.m[91]" "tpose.p[141]";
connectAttr "tpose.m[91]" "tpose.p[142]";
connectAttr "tpose.m[91]" "tpose.p[143]";
connectAttr "tpose.m[91]" "tpose.p[144]";
connectAttr "tpose.m[91]" "tpose.p[145]";
connectAttr "tpose.m[91]" "tpose.p[146]";
connectAttr "tpose.m[91]" "tpose.p[147]";
connectAttr "tpose.m[91]" "tpose.p[148]";
connectAttr "tpose.m[91]" "tpose.p[149]";
connectAttr "tpose.m[91]" "tpose.p[150]";
connectAttr "tpose.m[91]" "tpose.p[151]";
connectAttr "tpose.m[91]" "tpose.p[152]";
connectAttr "tpose.m[91]" "tpose.p[153]";
connectAttr "tpose.m[91]" "tpose.p[154]";
connectAttr "tpose.m[91]" "tpose.p[155]";
connectAttr "tpose.m[91]" "tpose.p[156]";
connectAttr "tpose.m[91]" "tpose.p[157]";
connectAttr "tpose.m[91]" "tpose.p[158]";
connectAttr "tpose.m[91]" "tpose.p[159]";
connectAttr "tpose.m[91]" "tpose.p[160]";
connectAttr "tpose.m[91]" "tpose.p[161]";
connectAttr "tpose.m[91]" "tpose.p[162]";
connectAttr "tpose.m[91]" "tpose.p[163]";
connectAttr "tpose.m[91]" "tpose.p[164]";
connectAttr "tpose.m[91]" "tpose.p[165]";
connectAttr "tpose.m[91]" "tpose.p[166]";
connectAttr "tpose.m[91]" "tpose.p[167]";
connectAttr "tpose.m[91]" "tpose.p[168]";
connectAttr "tpose.m[91]" "tpose.p[169]";
connectAttr "tpose.m[91]" "tpose.p[170]";
connectAttr "tpose.m[0]" "tpose.p[171]";
connectAttr "tpose.m[171]" "tpose.p[172]";
connectAttr "tpose.m[171]" "tpose.p[173]";
connectAttr "tpose.m[0]" "tpose.p[174]";
connectAttr "tpose.m[174]" "tpose.p[175]";
connectAttr "tpose.m[174]" "tpose.p[176]";
connectAttr "tpose.m[0]" "tpose.p[177]";
connectAttr "C_root_JNT.msg" "apose.m[0]";
connectAttr "apose.w" "apose.p[0]";
connectAttr "apose.m[0]" "apose.p[1]";
connectAttr "apose.m[1]" "apose.p[2]";
connectAttr "apose.m[2]" "apose.p[3]";
connectAttr "apose.m[3]" "apose.p[4]";
connectAttr "apose.m[3]" "apose.p[5]";
connectAttr "apose.m[3]" "apose.p[6]";
connectAttr "apose.m[3]" "apose.p[7]";
connectAttr "apose.m[7]" "apose.p[8]";
connectAttr "apose.m[2]" "apose.p[9]";
connectAttr "apose.m[2]" "apose.p[10]";
connectAttr "apose.m[2]" "apose.p[11]";
connectAttr "apose.m[1]" "apose.p[12]";
connectAttr "apose.m[12]" "apose.p[13]";
connectAttr "apose.m[13]" "apose.p[14]";
connectAttr "apose.m[13]" "apose.p[15]";
connectAttr "apose.m[13]" "apose.p[16]";
connectAttr "apose.m[13]" "apose.p[17]";
connectAttr "apose.m[17]" "apose.p[18]";
connectAttr "apose.m[12]" "apose.p[19]";
connectAttr "apose.m[12]" "apose.p[20]";
connectAttr "apose.m[12]" "apose.p[21]";
connectAttr "apose.m[1]" "apose.p[22]";
connectAttr "apose.m[22]" "apose.p[23]";
connectAttr "apose.m[23]" "apose.p[24]";
connectAttr "apose.m[24]" "apose.p[25]";
connectAttr "apose.m[25]" "apose.p[26]";
connectAttr "apose.m[26]" "apose.p[27]";
connectAttr "apose.m[27]" "apose.p[28]";
connectAttr "apose.m[28]" "apose.p[29]";
connectAttr "apose.m[29]" "apose.p[30]";
connectAttr "apose.m[30]" "apose.p[31]";
connectAttr "apose.m[28]" "apose.p[32]";
connectAttr "apose.m[32]" "apose.p[33]";
connectAttr "apose.m[33]" "apose.p[34]";
connectAttr "apose.m[34]" "apose.p[35]";
connectAttr "apose.m[28]" "apose.p[36]";
connectAttr "apose.m[36]" "apose.p[37]";
connectAttr "apose.m[37]" "apose.p[38]";
connectAttr "apose.m[38]" "apose.p[39]";
connectAttr "apose.m[28]" "apose.p[40]";
connectAttr "apose.m[40]" "apose.p[41]";
connectAttr "apose.m[41]" "apose.p[42]";
connectAttr "apose.m[42]" "apose.p[43]";
connectAttr "apose.m[28]" "apose.p[44]";
connectAttr "apose.m[44]" "apose.p[45]";
connectAttr "apose.m[45]" "apose.p[46]";
connectAttr "apose.m[46]" "apose.p[47]";
connectAttr "apose.m[28]" "apose.p[48]";
connectAttr "apose.m[48]" "apose.p[49]";
connectAttr "apose.m[27]" "apose.p[50]";
connectAttr "apose.m[27]" "apose.p[51]";
connectAttr "apose.m[27]" "apose.p[52]";
connectAttr "apose.m[26]" "apose.p[53]";
connectAttr "apose.m[26]" "apose.p[54]";
connectAttr "apose.m[26]" "apose.p[55]";
connectAttr "apose.m[24]" "apose.p[56]";
connectAttr "apose.m[56]" "apose.p[57]";
connectAttr "apose.m[57]" "apose.p[58]";
connectAttr "apose.m[58]" "apose.p[59]";
connectAttr "apose.m[59]" "apose.p[60]";
connectAttr "apose.m[60]" "apose.p[61]";
connectAttr "apose.m[61]" "apose.p[62]";
connectAttr "apose.m[59]" "apose.p[63]";
connectAttr "apose.m[63]" "apose.p[64]";
connectAttr "apose.m[64]" "apose.p[65]";
connectAttr "apose.m[65]" "apose.p[66]";
connectAttr "apose.m[59]" "apose.p[67]";
connectAttr "apose.m[67]" "apose.p[68]";
connectAttr "apose.m[68]" "apose.p[69]";
connectAttr "apose.m[69]" "apose.p[70]";
connectAttr "apose.m[59]" "apose.p[71]";
connectAttr "apose.m[71]" "apose.p[72]";
connectAttr "apose.m[72]" "apose.p[73]";
connectAttr "apose.m[73]" "apose.p[74]";
connectAttr "apose.m[59]" "apose.p[75]";
connectAttr "apose.m[75]" "apose.p[76]";
connectAttr "apose.m[76]" "apose.p[77]";
connectAttr "apose.m[77]" "apose.p[78]";
connectAttr "apose.m[59]" "apose.p[79]";
connectAttr "apose.m[79]" "apose.p[80]";
connectAttr "apose.m[58]" "apose.p[81]";
connectAttr "apose.m[58]" "apose.p[82]";
connectAttr "apose.m[58]" "apose.p[83]";
connectAttr "apose.m[57]" "apose.p[84]";
connectAttr "apose.m[57]" "apose.p[85]";
connectAttr "apose.m[57]" "apose.p[86]";
connectAttr "apose.m[24]" "apose.p[87]";
connectAttr "apose.m[87]" "apose.p[88]";
connectAttr "apose.m[88]" "apose.p[89]";
connectAttr "apose.m[89]" "apose.p[90]";
connectAttr "apose.m[89]" "apose.p[91]";
connectAttr "apose.m[91]" "apose.p[92]";
connectAttr "apose.m[91]" "apose.p[93]";
connectAttr "apose.m[91]" "apose.p[94]";
connectAttr "apose.m[91]" "apose.p[95]";
connectAttr "apose.m[91]" "apose.p[96]";
connectAttr "apose.m[91]" "apose.p[97]";
connectAttr "apose.m[91]" "apose.p[98]";
connectAttr "apose.m[91]" "apose.p[99]";
connectAttr "apose.m[91]" "apose.p[100]";
connectAttr "apose.m[91]" "apose.p[101]";
connectAttr "apose.m[91]" "apose.p[102]";
connectAttr "apose.m[91]" "apose.p[103]";
connectAttr "apose.m[91]" "apose.p[104]";
connectAttr "apose.m[91]" "apose.p[105]";
connectAttr "apose.m[91]" "apose.p[106]";
connectAttr "apose.m[91]" "apose.p[107]";
connectAttr "apose.m[91]" "apose.p[108]";
connectAttr "apose.m[91]" "apose.p[109]";
connectAttr "apose.m[91]" "apose.p[110]";
connectAttr "apose.m[91]" "apose.p[111]";
connectAttr "apose.m[91]" "apose.p[112]";
connectAttr "apose.m[91]" "apose.p[113]";
connectAttr "apose.m[91]" "apose.p[114]";
connectAttr "apose.m[91]" "apose.p[115]";
connectAttr "apose.m[91]" "apose.p[116]";
connectAttr "apose.m[91]" "apose.p[117]";
connectAttr "apose.m[91]" "apose.p[118]";
connectAttr "apose.m[91]" "apose.p[119]";
connectAttr "apose.m[91]" "apose.p[120]";
connectAttr "apose.m[91]" "apose.p[121]";
connectAttr "apose.m[91]" "apose.p[122]";
connectAttr "apose.m[91]" "apose.p[123]";
connectAttr "apose.m[91]" "apose.p[124]";
connectAttr "apose.m[91]" "apose.p[125]";
connectAttr "apose.m[91]" "apose.p[126]";
connectAttr "apose.m[91]" "apose.p[127]";
connectAttr "apose.m[91]" "apose.p[128]";
connectAttr "apose.m[91]" "apose.p[129]";
connectAttr "apose.m[91]" "apose.p[130]";
connectAttr "apose.m[91]" "apose.p[131]";
connectAttr "apose.m[91]" "apose.p[132]";
connectAttr "apose.m[91]" "apose.p[133]";
connectAttr "apose.m[91]" "apose.p[134]";
connectAttr "apose.m[91]" "apose.p[135]";
connectAttr "apose.m[91]" "apose.p[136]";
connectAttr "apose.m[91]" "apose.p[137]";
connectAttr "apose.m[91]" "apose.p[138]";
connectAttr "apose.m[91]" "apose.p[139]";
connectAttr "apose.m[91]" "apose.p[140]";
connectAttr "apose.m[91]" "apose.p[141]";
connectAttr "apose.m[91]" "apose.p[142]";
connectAttr "apose.m[91]" "apose.p[143]";
connectAttr "apose.m[91]" "apose.p[144]";
connectAttr "apose.m[91]" "apose.p[145]";
connectAttr "apose.m[91]" "apose.p[146]";
connectAttr "apose.m[91]" "apose.p[147]";
connectAttr "apose.m[91]" "apose.p[148]";
connectAttr "apose.m[91]" "apose.p[149]";
connectAttr "apose.m[91]" "apose.p[150]";
connectAttr "apose.m[91]" "apose.p[151]";
connectAttr "apose.m[91]" "apose.p[152]";
connectAttr "apose.m[91]" "apose.p[153]";
connectAttr "apose.m[91]" "apose.p[154]";
connectAttr "apose.m[91]" "apose.p[155]";
connectAttr "apose.m[91]" "apose.p[156]";
connectAttr "apose.m[91]" "apose.p[157]";
connectAttr "apose.m[91]" "apose.p[158]";
connectAttr "apose.m[91]" "apose.p[159]";
connectAttr "apose.m[91]" "apose.p[160]";
connectAttr "apose.m[91]" "apose.p[161]";
connectAttr "apose.m[91]" "apose.p[162]";
connectAttr "apose.m[91]" "apose.p[163]";
connectAttr "apose.m[91]" "apose.p[164]";
connectAttr "apose.m[91]" "apose.p[165]";
connectAttr "apose.m[91]" "apose.p[166]";
connectAttr "apose.m[91]" "apose.p[167]";
connectAttr "apose.m[91]" "apose.p[168]";
connectAttr "apose.m[91]" "apose.p[169]";
connectAttr "apose.m[91]" "apose.p[170]";
connectAttr "apose.m[0]" "apose.p[171]";
connectAttr "apose.m[171]" "apose.p[172]";
connectAttr "apose.m[171]" "apose.p[173]";
connectAttr "apose.m[0]" "apose.p[174]";
connectAttr "apose.m[174]" "apose.p[175]";
connectAttr "apose.m[174]" "apose.p[176]";
connectAttr "apose.m[0]" "apose.p[177]";
connectAttr "test_cylinderShapeOrig.w" "skinCluster1.ip[0].ig";
connectAttr "test_cylinderShapeOrig.o" "skinCluster1.orggeom[0]";
connectAttr "bindPose2.msg" "skinCluster1.bp";
connectAttr "C_root_JNT.wm" "skinCluster1.ma[0]";
connectAttr "C_root_JNT.liw" "skinCluster1.lw[0]";
connectAttr "C_root_JNT.obcc" "skinCluster1.ifcl[0]";
connectAttr "rig.msg" "bindPose2.m[0]";
connectAttr "skeleton.msg" "bindPose2.m[1]";
connectAttr "C_root_JNT.msg" "bindPose2.m[2]";
connectAttr "bindPose2.w" "bindPose2.p[0]";
connectAttr "bindPose2.m[0]" "bindPose2.p[1]";
connectAttr "bindPose2.m[1]" "bindPose2.p[2]";
connectAttr "C_root_JNT.bps" "bindPose2.wm[2]";
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
connectAttr "test_cylinderShape.iog" ":initialShadingGroup.dsm" -na;
// End of cylinder_rig.ma
