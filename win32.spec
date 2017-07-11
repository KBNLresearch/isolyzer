# -*- mode: python -*-
a = Analysis(['.\isolyzer\isolyzer.py'],
             pathex=['.\isolyzer'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\isolyzer', 'isolyzer.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries +
               [('./license/LICENSE.txt','LICENSE.txt','DATA')],
               [('./testFiles/hfs.iso','./testFiles/hfs.iso','DATA')],
               [('./testFiles/hfsplus.iso','./testFiles/hfsplus.iso','DATA')],
               [('./testFiles/iso9660.iso','./testFiles/iso9660.iso','DATA')],
               [('./testFiles/iso9660_hfs.iso','./testFiles/iso9660_hfs.iso','DATA')],
               [('./testFiles/iso9660_nopvd.iso','./testFiles/iso9660_nopvd.iso','DATA')],
               [('./testFiles/iso9660_trunc.iso','./testFiles/iso9660_trunc.iso','DATA')],
               [('./testFiles/iso9660_udf.iso','./testFiles/iso9660_udf.iso','DATA')],
               [('./testFiles/multisession.iso','./testFiles/multisession.iso','DATA')],
               [('./testFiles/udf.iso','./testFiles/udf.iso','DATA')],
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist_win32', 'isolyzer'))
