# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['app.py'],
             pathex=['e:/salle_attente - Copy'], # Ensure this points to your project root
             binaries=[],
             datas=[
                 ('app_icon.ico', '.'),
                 ('services.json', '.'),
                 ('transactions.json', '.'),
                 ('user_credentials.json', '.'),
                 ('user_theme_config.json', '.'),
                 ('patient_records.json', '.'),
                 ('icon.png', '.'), # Include the png icon as data if needed elsewhere
                 ('migrations', 'migrations'), # Include the migrations directory
                 # Add other necessary data files or directories here
             ],
             hiddenimports=[
                 # Add any modules PyInstaller might miss, e.g., specific database drivers
                 'sqlalchemy.dialects.sqlite',
                 'babel.numbers', # Often needed for libraries that handle localization/formatting
                 # Add other hidden imports if runtime errors occur
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name="salle_attente_cabinet_medical", # Updated application name
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False, # Set to False for GUI applications
          icon='icon.png') # Use the .png file for the executable

# If you want a single executable file, uncomment the 'coll' line below
# and comment out the 'exe' line above. Single-file executables might start slower.
# coll = COLLECT(exe,
#                a.binaries,
#                a.zipfiles,
#                a.datas,
#                strip=False,
#                upx=True,
#                upx_exclude=[],
#                name='salle_attente_cabinet_medical') # Update name here too if using COLLECT
