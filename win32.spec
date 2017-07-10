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
               [('./testFiles/minimal.iso','./testFiles/minimal.iso','DATA')],
               [('./testFiles/minimal_trunc.iso','./testFiles/minimal_trunc.iso','DATA')],
               [('./testFiles/minimal_trunc_nopvd.iso','./testFiles/minimal_trunc_nopvd.iso','DATA')],
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist_win32', 'isolyzer'))
