#!/bin/bash

# Build 64 and 32 bit Windows binaries using Wine and WinPython. If the required Wine environment 
# (WinPython + PyInstaller) cannot be found it is set up quasi-automatically (the WinPython installer
# needs some manual input)
# Precondition: 64-bit version of Wine is already installed. 

# WinPython download URLS
downloadURL64bit=https://www.python.org/ftp/python/3.10.4/python-3.10.4-embed-amd64.zip
downloadURL32bit=https://sourceforge.net/projects/winpython/files/WinPython_2.7/2.7.13.1/WinPython-32bit-2.7.13.1Zero.exe/download

# PyInstaller spec files that defines build options
specFile64bit=win64.spec
specFile32bit=win32.spec

# Script base name (i.e. script name minus .py extension)
scriptBaseName=isolyzer

# Wine debug variable (suppresses garbage debugging messages)
WineDebug="-msvcrt"
#WineDebug="fixme-all"

installPython(){
    # Installs Python. Arguments:
    # - $1: bitness (32 or 64)
    # - $2: download URL
    echo "Downloading installer"
    wget $2 -O pyTemp.zip
    echo ""
    echo "Installing Python."
    echo ""

    unzip pyTemp.zip -d /home/johan/.wine/drive_c/Python3_64

    echo "Removing installer"
    rm pyTemp.zip
}

installPyInstaller(){
    # Installs pyInstaller if it is not installed already. Argument:
    # - $1: python (full path of python interpreter)
    echo "Checking for pyinstaller" 
    WINEDEBUG=$WineDebug wine $1 -m pip show pyinstaller

    if [ $? -eq 0 ]; then
        echo "Pyinstaller already installed"
    else
        echo "Installing pyinstaller"
        WINEDEBUG=$WineDebug wine $1 -m pip install pyinstaller
    fi
}

buildBinaries(){
    # Builds Windows binaries. 
    
    # Read arguments:
    bitness=$1
    pyRoot=$2
    pyInstallerWine=$pyRoot"/Scripts/pyinstaller.exe"
    pythonWine=$3
    specFile=$4

    # Working directory
    workDir=$PWD

    # Directory where build is created (should be identical to 'name' in 'coll' in spec file!!)
    distDir=$workDir"/dist/win"$bitness"/"

    # Executes jpylyzer with -v option and stores output to 
    # env variable 'version'
    # Also trim trailing EOL character and replace '.' by '_' 
    WINEDEBUG=$WineDebug wine $pythonWine -m $scriptBaseName -v 2> temp.txt
    version=$(head -n 1 temp.txt | tr -d '\r')
    rm temp.txt

    echo "Building binaries"
    WINEDEBUG=$WineDebug wine $pyInstallerWine $specFile --distpath=$distDir

    # Generate name for ZIP file
    zipName=$scriptBaseName"_"$version"_win"$bitness".zip"
    echo zipName

    echo "Creating ZIP file"
    cd $distDir
    zip -r $zipName $scriptBaseName
    cd $workDir

    echo "Deleting build directory"
    rm -r $workDir"/build"
    rm -r  $distDir/$scriptBaseName
}

echo "64 bit Python"

if [ -d $HOME"/.wine/drive_c/Python3_64" ]; then  
    echo "Python (64 bit) already installed"
else
    echo "Python (64 bit) not yet installed, installing now"
    echo ""
    installPython 64 $downloadURL64bit
fi

# Get path to Python root
pyRoot64=$(ls -d ~/.wine/drive_c/Python3_64)

# Python interpreter
python64=$pyRoot64"/python.exe" 

# Install PyInstaller (if not installed already)
installPyInstaller $python64

echo "32 bit Python"

if [ -d $HOME"/.wine/drive_c/Python27_32" ]; then  
    echo "Python (32 bit) already installed"
else
    echo "Python (32 bit) not yet installed, installing now"
    echo ""
    #installPython 32 $downloadURL32bit
fi

# Get path to Python root
#pyRoot32=$(ls -d ~/.wine/drive_c/Python27_32/python-*)

# Python interpreter
#python32=$pyRoot32"/python.exe" 

# Install PyInstaller (if not installed already)
#installPyInstaller $python32

echo "Building binaries, 64 bit"
buildBinaries 64 $pyRoot64 $python64 $specFile64bit

#echo "Building binaries, 32 bit"
#buildBinaries 32 $pyRoot32 $python32 $specFile32bit

