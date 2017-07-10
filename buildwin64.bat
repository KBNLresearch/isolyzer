:
:: Build 64 bit Windows isolyzer binaries from Python script, and pack them in ZIP file
::
:: ZIP file includes license file, PDF User Manual and example files 
::
:: Johan van der Knijff, 25 april 2013
::
:: Dependencies:
:: 
:: - Python 3.x, 64-bit version 
:: - PyInstaller: http://www.pyinstaller.org/
:: - PyWin32 (needed by PyInstaller): http://sourceforge.net/projects/pywin32/files/

::
@echo off
setlocal

::::::::: CONFIGURATION :::::::::: 

:: Python
:: Note that to produce a 32-bit binary we need a 32-bit Python version!
set python=c:\python36\python

:: Script base name (i.e. script name minus .py extension)
set scriptBaseName=isolyzer

:: PyInstaller spec file that defines build options
set specFile=win64.spec

:: Directory where build is created (should be identical to 'name' in 'coll' in spec file!!)
set distDir=.\dist_win64\

:: Executes isolyzer with -v option and stores output to 
:: env variable 'version'
set vCommand=%python% .\%scriptBaseName%\%scriptBaseName%.py -v
%vCommand% > temp.txt
set /p version= < temp.txt
del temp.txt 

::::::::: BUILD :::::::::::::::::: 

:: Build binaries
pyinstaller %specFile%

:: Generate name for ZIP file
set zipName=%scriptBaseName%_%version%_win64.zip

:: Create ZIP file
%python% zipdir.py %distDir%\isolyzer %distDir%\%zipName% 

::::::::: CLEANUP ::::::::::::::::: 

:: Delete build directory
rmdir build /S /Q

:: Delete isolyzer directory in distdir
rmdir %distDir%\isolyzer /S /Q

::::::::: PARTY TIME! ::::::::::::::::: 

echo /
echo Done! Created %zipName% in directory %distDir%!
echo / 

