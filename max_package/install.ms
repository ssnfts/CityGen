-- CityGen drag-and-drop installer for 3ds Max 2027.
local target = (getDir #userScripts) + "\\CityGen"
makeDir target all:true
copyFile (getFilenamePath getThisScriptFilename() + "scripts\\citygen_max.py") (target + "\\citygen_max.py")
copyFile (getFilenamePath getThisScriptFilename() + "scripts\\map_picker.py") (target + "\\map_picker.py")
copyFile (getFilenamePath getThisScriptFilename() + "core\\citygen.py") (target + "\\citygen.py")
copyFile (getFilenamePath getThisScriptFilename() + "scripts\\CityGen.mcr") ((getDir #userMacros) + "\\CityGen.mcr")
fileIn ((getDir #userMacros) + "\\CityGen.mcr")
messageBox "CityGen installed. Use Customize User Interface to place CityGen on a toolbar, then select a planar closed shape." title:"CityGen"
