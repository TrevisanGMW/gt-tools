"""
 GT Generate Icons - Generates icons used by GT Tools menu
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-11-03 - github.com/TrevisanGMW
 
 1.0 - 2020-11-03
 Initial Release
 Creates Maya to Discord Icon
 
 1.1 - 2020-12-11
 Creates fSpy Importer Icon
 
 1.2 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022)
 
""" 
import maya.cmds as cmds
import base64
import os

def gt_generate_icons():

    icons_folder_dir = cmds.internalVar(userBitmapsDir=True) 
    
    # GT Maya to Discord Icon
    gt_mtod_icon_image = icons_folder_dir + 'gt_maya_to_discord_icon.png'
    gt_fspy_icon_image = icons_folder_dir + 'gt_fspy_importer.png'

    if os.path.isdir(icons_folder_dir):
        # Maya to Discord
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOmRjPSJodHRwOi8vcHVybC5vcmcvZGMvZWxlbWVudHMvMS4xLyIgeG1sbnM6cGhvdG9zaG9wPSJodHRwOi8vbnMuYWRvYmUuY29tL3Bob3Rvc2hvcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTA3LTA1VDE5OjU2OjQwLTA3OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0wNy0wN1QxNToyNToyOS0wNzowMCIgeG1wOk1ldGFkYXRhRGF0ZT0iMjAyMC0wNy0wN1QxNToyNToyOS0wNzowMCIgZGM6Zm9ybWF0PSJpbWFnZS9wbmciIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo3ZGNlNzRhMi04YTE3LTI4NDItOGEwMy1lZWZmYzRjNGVkYWEiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDpkNjdiM2JkNy1iMjk3LWI3NDItOTNkOC0wYTYyZjZhYzUzMmYiIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDplOTM5YzQ0Yi1lNjdkLWJjNGMtYWMyZS00YmY3ZjcwYzgzODAiPiA8eG1wTU06SGlzdG9yeT4gPHJkZjpTZXE+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJjcmVhdGVkIiBzdEV2dDppbnN0YW5jZUlEPSJ4bXAuaWlkOmU5MzljNDRiLWU2N2QtYmM0Yy1hYzJlLTRiZjdmNzBjODM4MCIgc3RFdnQ6d2hlbj0iMjAyMC0wNy0wNVQxOTo1Njo0MC0wNzowMCIgc3RFdnQ6c29mdHdhcmVBZ2VudD0iQWRvYmUgUGhvdG9zaG9wIDIxLjAgKFdpbmRvd3MpIi8+IDxyZGY6bGkgc3RFdnQ6YWN0aW9uPSJzYXZlZCIgc3RFdnQ6aW5zdGFuY2VJRD0ieG1wLmlpZDo3ZGNlNzRhMi04YTE3LTI4NDItOGEwMy1lZWZmYzRjNGVkYWEiIHN0RXZ0OndoZW49IjIwMjAtMDctMDdUMTU6MjU6MjktMDc6MDAiIHN0RXZ0OnNvZnR3YXJlQWdlbnQ9IkFkb2JlIFBob3Rvc2hvcCAyMS4wIChXaW5kb3dzKSIgc3RFdnQ6Y2hhbmdlZD0iLyIvPiA8L3JkZjpTZXE+IDwveG1wTU06SGlzdG9yeT4gPC9yZGY6RGVzY3JpcHRpb24+IDwvcmRmOlJERj4gPC94OnhtcG1ldGE+IDw/eHBhY2tldCBlbmQ9InIiPz7Q7fCFAAAIwklEQVR4nO3bf6xlVXUH8M/a5755w/BDfmaYCunAkyq22hFQbClia1sZMBicaIc2bWJqajQpwR9pY6TYKkk1jiBNbZpQq40mVCI60USjERqIP+LQoQRSx6hjfxEjTQpl+DXMu3cv/zjn3nnvdWbefe/O64Uw32TlnZx7ztrfvc7aa+299n6RmZ7PKNMmMG0cM8C0CUwbxwwwbQLTxjEDTJvAtPG8N0Dvpk8v/1AmOUBQGhI5TwZlFgOikuEkXCRskd6LH0f6taGe2iCJbHXp5mAR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'
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(gt_mtod_icon_image, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
        
        # fSpy Importer
        image_enconded = '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'
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(gt_fspy_icon_image, 'wb')
        image_result.write(image_64_decode)
        image_result.close()

# Generate Icons Without Imports
if __name__ == '__main__':
    gt_generate_icons()