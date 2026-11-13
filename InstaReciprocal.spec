# PyInstaller spec for a Windows onedir desktop build.
# The batch file uses equivalent command-line options and collects CustomTkinter assets.
# This spec is provided for users who prefer building with: pyinstaller InstaReciprocal.spec

from PyInstaller.utils.hooks import collect_all, collect_submodules

ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all("customtkinter")
dd_datas, dd_binaries, dd_hiddenimports = collect_all("darkdetect")
insta_hidden = collect_submodules("instareciprocal")

a = Analysis(
    ["run_gui.py"],
    pathex=[],
    binaries=ctk_binaries + dd_binaries,
    datas=ctk_datas + dd_datas,
    hiddenimports=ctk_hiddenimports + dd_hiddenimports + insta_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InstaReciprocal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="InstaReciprocal",
)

