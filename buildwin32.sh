# Build Windows isolyzer binaries from Python script, and pack them in ZIP file

#
# Dependencies:
# - Wine environment with Python, pyInstaller and all isolyzer dependencies
# - a spec file

# CONFIGURATION 

# Python
# Note that to produce a 32-bit binary we need a 32-bit Python version!
pythonWine=~/.wine/drive_c/Python27/python.exe
pyInstallerWine=~/.wine/drive_c/Python27/Scripts/pyinstaller.exe

# Script base name (i.e. script name minus .py extension)
scriptBaseName=isolyzer

# PyInstaller spec file that defines build options
specFile=win32.spec

# Directory where build is created (should be identical to 'name' in 'coll' in spec file!!)
# TOSO is this even used, as default name seems to be 'dist'?!
distDir=./dist_win32/

# Executes isolyzer with -v option and stores output to 
# env variable 'version'
wine $pythonWine ./$scriptBaseName/$scriptBaseName.py -v 2> temp.txt
version=$(head -n 1 temp.txt)
rm temp.txt

# BUILD

# Build binaries
$pyInstallerWine $specFile

# Generate name for ZIP file
zipName="$scriptBaseName"_"$version"_win32.zip

# Create ZIP file
cd ./dist
zip -r $zipName isolyzer
cd ..
mv ./dist/$zipName .

# CLEANUP 

# Delete build directory
#rmdir build /S /Q

# Delete isolyzer directory in distdir
#rmdir %distDir%\isolyzer /S /Q

# PARTY TIME! 

echo "Done!"


