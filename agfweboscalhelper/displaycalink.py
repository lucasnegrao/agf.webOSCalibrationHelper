import sys
import os



import configparser
configparser.DEFAULTSECT = "Default"

from displaycal.defaultpaths import appdata, commonappdata
from displaycal.util_os import (expanduseru, expandvarsu, getenvu, is_superuser,
					 listdir_re, which)

if sys.platform == "win32":
	from displaycal.defaultpaths import commonprogramfiles
elif sys.platform == "darwin":
	from displaycal.defaultpaths import library, library_home, prefs, prefs_home
else:
	from displaycal.defaultpaths import (xdg_config_dir_default, xdg_config_home, 
							  xdg_data_home, xdg_data_home_default, 
							  xdg_data_dirs)

from displaycal.encoding import get_encoding, get_encodings

enc, fs_enc = get_encodings()

exe = str(sys.executable) + fs_enc
exedir = os.path.dirname(exe)
exename = os.path.basename(exe)

isexe = sys.platform != "darwin" and getattr(sys, "frozen", False)

if isexe and os.getenv("_MEIPASS2"):
	os.environ["_MEIPASS2"] = os.getenv("_MEIPASS2").replace("/", os.path.sep)

pyfile = (exe if isexe else (os.path.isfile(sys.argv[0]) and sys.argv[0]) or
		  os.path.join(os.path.dirname(__file__), "main.py"))
pypath = exe if isexe else os.path.abspath(str(pyfile)+ fs_enc)
# Mac OS X: isapp should only be true for standalone, not 0install
isapp = sys.platform == "darwin" and \
		exe.split(os.path.sep)[-3:-1] == ["Contents", "MacOS"] and \
		os.path.exists(os.path.join(exedir, "..", "Resources", "xrc"))
if isapp:
	pyname, pyext = os.path.splitext(exe.split(os.path.sep)[-4])
	pydir = os.path.normpath(os.path.join(exedir, "..", "Resources"))
else:
	pyname, pyext = os.path.splitext(os.path.basename(pypath))
	pydir = os.path.dirname(exe if isexe
							else os.path.abspath(str(__file__)+ fs_enc))

appbasename = "DisplayCal"
appname = "DisplayCal"
data_dirs = [pydir]

# If old user data directory exists, use its basename
if os.path.isdir(os.path.join(appdata, "dispcalGUI")):
	appbasename = "dispcalGUI"
	data_dirs.append(os.path.join(appdata, appname))
datahome = os.path.join(appdata, appbasename)
if sys.platform == "win32":
	if pydir.lower().startswith(exedir.lower()) and pydir != exedir:
		# We are installed in a subfolder of the executable directory (e.g. 
		# C:\Python26\Lib\site-packages\DisplayCAL) - we nee to add 
		# the executable directory to the data directories so files in
		# subfolders of the executable directory which are not in 
		# Lib\site-packages\DisplayCAL can be found
		# (e.g. Scripts\displaycal-apply-profiles)
		data_dirs.append(exedir)
	script_ext = ".cmd"
	scale_adjustment_factor = 1.0
	config_sys = os.path.join(commonappdata[0], appbasename)
	confighome = os.path.join(appdata, appbasename)
	logdir = os.path.join(datahome, "logs")
	if appbasename != appname:
		data_dirs.extend(os.path.join(dir_, appname) for dir_ in commonappdata)
		data_dirs.append(os.path.join(commonprogramfiles, appname))
	data_dirs.append(datahome)
	data_dirs.extend(os.path.join(dir_, appbasename) for dir_ in commonappdata)
	data_dirs.append(os.path.join(commonprogramfiles, appbasename))
	exe_ext = ".exe"
	profile_ext = ".icm"
else:
	if sys.platform == "darwin":
		script_ext = ".command"
		mac_create_app = True
		scale_adjustment_factor = 1.0
		config_sys = os.path.join(prefs, appbasename)
		confighome = os.path.join(prefs_home, appbasename)
		logdir = os.path.join(expanduseru("~"), "Library", 
							  "Logs", appbasename)
		if appbasename != appname:
			data_dirs.append(os.path.join(commonappdata[0], appname))
		data_dirs.append(datahome)
		data_dirs.append(os.path.join(commonappdata[0], appbasename))
	else:
		script_ext = ".sh"
		scale_adjustment_factor = 1.0
		config_sys = os.path.join(xdg_config_dir_default, appbasename)
		confighome = os.path.join(xdg_config_home, appbasename)
		logdir = os.path.join(datahome, "logs")
		if appbasename != appname:
			datahome_default = os.path.join(xdg_data_home_default, appname)
			if not datahome_default in data_dirs:
				data_dirs.append(datahome_default)
			data_dirs.extend(os.path.join(dir_, appname) for dir_ in xdg_data_dirs)
		data_dirs.append(datahome)
		datahome_default = os.path.join(xdg_data_home_default, appbasename)
		if not datahome_default in data_dirs:
			data_dirs.append(datahome_default)
		data_dirs.extend(os.path.join(dir_, appbasename) for dir_ in xdg_data_dirs)
		extra_data_dirs.extend(os.path.join(dir_, "argyllcms") for dir_ in
							   xdg_data_dirs)
		extra_data_dirs.extend(os.path.join(dir_, "color", "argyll") for dir_ in
							   xdg_data_dirs)
	exe_ext = ""
	profile_ext = ".icc"

cfg = configparser.RawConfigParser()

def get1DLUTPath():
	cfg.read(confighome+"/DisplayCal.ini")
	return (cfg['Default']['last_cal_path'])

def get3DLUTPath():
#	cfg.read(confighome+"/DisplayCal.ini")
#	(cfg['Default']['last_3dlut_path'])
	files=listdir_re(getLUTSPath(),"([a-zA-Z0-9\s_\\.\-\(\):])+(.cube)$")
	return(getLUTSPath()+"/"+next(files,None))

def get3DLUTSize():
	cfg.read(confighome+"/DisplayCal.ini")
	return int(cfg['Default']['3dlut.size'])

def getLUTSPath():
	return os.path.dirname(get1DLUTPath())


