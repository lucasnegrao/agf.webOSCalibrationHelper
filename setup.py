from setuptools import setup
APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True, 
    'site_packages': True,
    #'iconfile': 'appicon.icns',
    'packages': ['aiopylgtv', 'PySide2'],
    'plist': {
        'CFBundleName': 'agf.webOSCalibrationHelper',
    }
}
setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)