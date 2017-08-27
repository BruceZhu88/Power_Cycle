rd /s /Q .\UI\
xcopy .\download\PowerCycle\* .\ /s /h /y
::set current_dir=..\
::pushd %current_dir% 
rd /s /Q .\download\PowerCycle\ 
del .\download\PowerCycle.zip
del .\download\downVer.ini
COLOR 0A
CLS
@ECHO Off
@echo *******************************************************
@echo ***********New version install successfully!***********
@echo *******************************************************
ECHO.
ECHO Press any key to continue . . .
pause>nul
start .\PowerCycle.exe