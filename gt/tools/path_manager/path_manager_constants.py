"""Constants used by the Path Manager tool."""

TOOL_NAME = "Path Manager"

WINDOW_MINIMUM_WIDTH = 720
WINDOW_MINIMUM_HEIGHT = 420
WINDOW_DEFAULT_WIDTH = 960
WINDOW_DEFAULT_HEIGHT = 560

TABLE_COLUMN_STATUS = 0
TABLE_COLUMN_NODE = 1
TABLE_COLUMN_TYPE = 2
TABLE_COLUMN_PATH = 3
TABLE_HEADERS = ["", "Node", "Node Type", "Path"]

STATUS_ICON_VALID = ":confirm.png"
STATUS_ICON_INVALID = ":error.png"

PATH_NODE_CONFIG = {
    "file": {
        "attribute": ".fileTextureName",
        "display_name": "File",
        "icon": ":file.svg",
    },
    "audio": {
        "attribute": ".filename",
        "display_name": "Audio",
        "icon": ":audio.svg",
    },
    "cacheFile": {
        "attribute": ".cachePath",
        "display_name": "Cache File",
        "icon": ":cachedPlayback.png",
    },
    "AlembicNode": {
        "attribute": ".abc_File",
        "display_name": "Alembic File",
        "icon": ":enableAllCaches.png",
    },
    "BifMeshImportNode": {
        "attribute": ".bifMeshDirectory",
        "display_name": "Bifrost Cache",
        "icon": ":bifrostContainer.svg",
        "is_directory": True,
    },
    "gpuCache": {
        "attribute": ".cacheFileName",
        "display_name": "GPU Cache",
        "icon": ":importCache.png",
    },
    "aiPhotometricLight": {
        "attribute": ".aiFilename",
        "display_name": "aiPhotometricLight",
        "icon": ":LM_spotLight.png",
    },
    "aiStandIn": {
        "attribute": ".dso",
        "display_name": "aiStandIn",
        "icon": ":envCube.svg",
    },
    "aiVolume": {
        "attribute": ".filename",
        "display_name": "aiVolume",
        "icon": ":cube.png",
    },
    "RedshiftProxyMesh": {
        "attribute": ".fileName",
        "display_name": "rsProxyMesh",
        "icon": ":envCube.svg",
    },
    "RedshiftVolumeShape": {
        "attribute": ".fileName",
        "display_name": "rsVolumeShape",
        "icon": ":cube.png",
    },
    "RedshiftNormalMap": {
        "attribute": ".tex0",
        "display_name": "rsNormalMap",
        "icon": ":normalDetails.svg",
    },
    "RedshiftDomeLight": {
        "attribute": ".tex0",
        "display_name": "rsDomeLight",
        "icon": ":ambientLight.svg",
    },
    "RedshiftIESLight": {
        "attribute": ".profile",
        "display_name": "rsIESLight",
        "icon": ":LM_spotLight.png",
    },
    "MASH_Audio": {
        "attribute": ".filename",
        "display_name": "MASH Audio",
        "icon": ":audio.svg",
    },
    "imagePlane": {
        "attribute": ".imageName",
        "display_name": "Image Plane",
        "icon": ":imagePlane.svg",
    },
    "reference": {
        "attribute": ".fileNames",
        "display_name": "Reference",
        "icon": ":reference.png",
    },
}
