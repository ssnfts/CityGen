macroScript CityGen_Open
category:"CityGen"
tooltip:"Open CityGen"
buttonText:"CityGen"
(
    on execute do
    (
        local script = (getDir #userScripts) + "\\CityGen\\citygen_max.py"
        if doesFileExist script then python.ExecuteFile script
        else messageBox "CityGen is not installed. Drag CityGen.mzp into 3ds Max first." title:"CityGen"
    )
)
