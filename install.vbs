'xcopy .\download\PowerCycle\* .\ /s /h /y
''set current_dir=..\
''pushd %current_dir% 
'rd /s /Q .\download\PowerCycle\ 
'del .\download\PowerCycle.zip
'del .\download\downVer.ini
'start .\PowerCycle.exe
'--------------------------------- 
'set objShell = createobject("wscript.shell")
'objShell.exec("ipconfig")
'function-->has return or sub -->no return
'--------------------------------- 
function delete(path)
	dim name
	Set fso = CreateObject("scripting.filesystemobject") 
	Set f = fso.getfolder(path)
	Set oSubFolders = f.SubFolders 
	Set ff = f.Files 
    for each file in ff
        'name = file.name
		file.delete
    next

    For Each oSubFolder In oSubFolders   
		folderName = oSubFolder.name
        if folderName <> "download" then
			oSubFolder.delete
        end if
    Next   
end function
'---------------------------------
'---------------------------------
function deleteFile(pathName)
	Set fso = CreateObject("scripting.filesystemobject") 
	if(fso.FileExists(pathName)) Then
		fso.deleteFile pathName
	end if
end function

function deleteFolder(path)
	Set fso = CreateObject("scripting.filesystemobject") 
	if(fso.FolderExists(path)) Then
		fso.deleteFolder path
	end if
end function

function copy(source, dest)
	dim cmd
	Set objShell = createobject("wscript.shell")
	cmd = "xcopy "&source&" "&dest&" /s /h /y"
	objShell.exec(cmd) 'objShell.Run('')
end function

function run(pathName)
	Set objShell = createobject("wscript.shell")
	Set fso = CreateObject("scripting.filesystemobject") 
	if(fso.FileExists(pathName)) Then
		objShell.Run(pathName)
	end if
end function

delete(".\")
copy ".\download\PowerCycle\", ".\"
msgbox "New version PowerCycle installed!",vbOKOnly,"Tips"
deleteFile(".\download\PowerCycle.zip")
deleteFile(".\download\downVer.ini")
deleteFolder ".\download\PowerCycle"
run(".\PowerCycle.exe")
