# -*- mode: python -*-
a = Analysis(['.\cli.py'],
             pathex=['.\isolyzer'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win64\\isolyzer', 'isolyzer.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries +
               [('./license/LICENSE.txt','LICENSE.txt','DATA')],
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist_win64', 'isolyzer'))
