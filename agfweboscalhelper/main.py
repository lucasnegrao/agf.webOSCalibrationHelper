# This Python file uses the following encoding: utf-8
import asyncio
import os
import sys

from aiopylgtv import WebOsClient
from PySide2.QtCore import QFile, QObject, Qt
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget

from displaycalink import get1DLUTPath, get3DLUTPath, get3DLUTSize

class webOSCalHelperWidget(QWidget):
    objs = []
    def __init__(self):
        super(webOSCalHelperWidget, self).__init__()
        self.load_ui()

    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        
        # Widget Initialization
        self.objs = loader.load(ui_file, self)
        self.objs.calibrationModeComboBox.addItems(["expert1","expert2","cinema","game","technicolorExpert"])

        # PushButton Callbacks
        self.objs.pB.clicked.connect(LUT1DBrowseClicked)
        self.objs.pB2.clicked.connect(LUT3D709BrowseClicked)
        self.objs.connectPB.clicked.connect(lambda: connectClicked(self.objs.connectPB))
        self.objs.ddcResetPB.clicked.connect(lambda: ddcResetClicked(self.objs.calibrationModeComboBox))
        self.objs.upload1D.clicked.connect(lambda: uploadLUTClicked("1D",self.objs.LutEdit1))
        self.objs.upload3D709.clicked.connect(lambda: uploadLUTClicked("3D709",self.objs.LutEdit2))
        self.objs.upload3D2020.clicked.connect(lambda: uploadLUTClicked("3D2020",self.objs.LutEdit3))
        self.objs.loadDisplayCalLUTPB.clicked.connect(loadLutsFromDisplayCal)
        self.objs.powerButton.clicked.connect(powerButtonClicked)


        # Slider Callbacks
        self.objs.contrastSlider.valueChanged.connect(lambda: setImageSetting("contrast",self.objs.contrastSlider))
        self.objs.brightnessSlider.valueChanged.connect(lambda: setImageSetting("brightness",self.objs.brightnessSlider))
        self.objs.oledLightSlider.valueChanged.connect(lambda: setImageSetting("backlight",self.objs.oledLightSlider))

        #ComboBox Callbacks
        self.objs.calibrationModeComboBox.currentIndexChanged.connect(lambda: setModeComboChanged(self.objs.calibrationModeComboBox))

        ui_file.close()

def setImageSetting(operationStr, obj):
    asyncio.get_event_loop().run_until_complete(setImageSettingAsync(operationStr,obj))

# webOS async functions
# async def send_message(self, message, icon_path=None)
async def webOSshowMessage(infoStr):
    await webosClientGlobalObj.send_message(message=infoStr)

async def uploadLut(typeStr, fileStr,modeStr):

    try:
        await webosClientGlobalObj.start_calibration(picMode=modeStr)
    except Exception as error:
        alertBox("Uploading LUT", "Client Disconnected", error)
    else:
        try:
            if typeStr == "1D":
                await webosClientGlobalObj.upload_1d_lut_from_file(picMode=modeStr, filename=fileStr)
            elif typeStr == "3D709":
                await webosClientGlobalObj.upload_3d_lut_bt709_from_file(picMode=modeStr, filename=fileStr)
            elif typeStr == "3D2020":
                await webosClientGlobalObj.upload_3d_lut_bt2020_from_file(picMode=modeStr, filename=fileStr)
        except Exception as error:
                alertBox("Uploading LUT", "Wrong LUT", error)
        else:
            successBox("Uploaded LUT succesfully")
            await webOSshowMessage(typeStr + " LUT uploaded and active on "+modeStr)
            await webosClientGlobalObj.end_calibration(picMode=modeStr)

async def setImageSettingAsync(operationStr, obj):
    try:
        if operationStr == "contrast":
            await webosClientGlobalObj.set_contrast(picMode=mainWidgetObj.objs.calibrationModeComboBox.currentText(), value=obj.value())
        elif operationStr == "backlight":
            await webosClientGlobalObj.set_oled_light(picMode=mainWidgetObj.objs.calibrationModeComboBox.currentText(), value=obj.value())
        elif operationStr == "brightness":
            await webosClientGlobalObj.set_brightness(picMode=mainWidgetObj.objs.calibrationModeComboBox.currentText(), value=obj.value())
    except:
        print("Error setting image settings")
        

async def loadImageSettingsAsync():
    try:
        settings = await webosClientGlobalObj.get_picture_settings()
    except Exception as error:
        alertBox("Loading Image Settings", "Couldn't load picture settings\n" ,error)
    else:
        mainWidgetObj.objs.contrastSlider.setValue(int(settings['contrast']))
        mainWidgetObj.objs.brightnessSlider.setValue(int(settings['brightness']))
        mainWidgetObj.objs.oledLightSlider.setValue(int(settings['backlight']))

async def on_state_change():
    print("State changed:")
    # print(webosClientGlobalObj.current_appId)
    # print(webosClientGlobalObj.muted)
    # print(webosClientGlobalObj.volume)
    # print(webosClientGlobalObj.current_channel)
    # print(webosClientGlobalObj.apps)
    # print(webosClientGlobalObj.inputs)
    print(webosClientGlobalObj.system_info)
    print(webosClientGlobalObj.software_info)

    if webosClientGlobalObj.system_info==None: activateGUI(False)

async def performWebOSConnection(text):
    if text=="Connect":
        global webosClientGlobalObj
        try:
            webosClientGlobalObj = await WebOsClient.create(mainWidgetObj.objs.IP.text())
            await webosClientGlobalObj.register_state_update_callback(on_state_change)
            await webosClientGlobalObj.connect()
        except Exception as error:
            alertBox("Connecting to TV", "Couldn't connect to TV with IP\n" + mainWidgetObj.objs.IP.text(),error)
            raise 
        else:
            activateGUI(True)
            await webOSshowMessage("agf.webOSCalibrationHelper connected!")
    else:
        await webosClientGlobalObj.disconnect()
        activateGUI(False)

async def performSetMode(modeStr):
    await webosClientGlobalObj.start_calibration(picMode=modeStr)
    await loadImageSettingsAsync()
    await webOSshowMessage("TV DDC Changed to "+modeStr)
#    await webosClientGlobalObj.end_calibration(picMode=modeStr)

async def performPowerOff():
    await webosClientGlobalObj.power_off()

async def performDDCReset(modeStr):
    if modeStr!="":
        try:
            await webosClientGlobalObj.ddc_reset(picMode=modeStr)
        except Exception as error:
            alertBox("Reseting DDC", "Couldn't reset DDC\n" + modeStr,error)
            raise
        else:
            successBox("DDC "+modeStr+" reseted succesfully")
            await webOSshowMessage(modeStr + " DDC reseted!")

# GUI signal handlers
def LUT3D709BrowseClicked():
    fileName = QFileDialog.getOpenFileName(None, "Open 3D LUT", "~/Library/Application\\ Support/DisplayCAL/storage", "3D LUT (*.cube)")
    mainWidgetObj.objs.LutEdit2.setText(fileName[0])
    return fileName[0]

def LUT1DBrowseClicked(self):
    fileName = QFileDialog.getOpenFileName(None, "Open 1D LUT", "~/Library/Application\\ Support/DisplayCAL/storage", "1D LUT (*.cal)")
    mainWidgetObj.objs.LutEdit1.setText(fileName[0])
    return fileName[0]

def powerButtonClicked():
    asyncio.get_event_loop().run_until_complete(performPowerOff())


def connectClicked(self):
    operationStr = self.text()

    print(operationStr)

    try:
        asyncio.get_event_loop().run_until_complete(performWebOSConnection(operationStr))
    except Exception as error:
        print(error)
        print("Error while connecting, probably wrong IP or TV turned off")
    else:
        if operationStr=="Connect": 
            loadImageSettings()

def loadLutsFromDisplayCal():
    try:
        lut1dpath = get1DLUTPath()
    except:
        alertBox("Load DisplayCAL configuration","Cannot load last displaycal configuration. Is it installed?")
    else:
        mainWidgetObj.objs.LutEdit1.setText(lut1dpath)
    try:
        lut3DSize = get3DLUTSize()
        lut3dpath = get3DLUTPath()
    except:
        alertBox("Load DisplayCAL configuration","Cannot load last displaycal configuration. Is it installed?")
    else:
        if lut3DSize==33 or lut3DSize==17:
            mainWidgetObj.objs.LutEdit2.setText(lut3dpath)
        else: 
            alertBox("Load DisplayCAL configuration","Last LUT 3D created was of wrong size. Sizes supported are 33 and 17, last was: "+str(lut3DSize))


def setModeComboChanged(self):
    asyncio.get_event_loop().run_until_complete(performSetMode(self.currentText()))

def ddcResetClicked(self):
    modeStr = self.currentText()
    try:
        asyncio.get_event_loop().run_until_complete(performDDCReset(modeStr))
    except:
        print("Error DCC Reset")
    else:
        loadImageSettings()

def uploadLUTClicked(uploadKindStr,editObj):
    modeStr  = mainWidgetObj.objs.calibrationModeComboBox.currentText()
    fileStr = editObj.text()
    asyncio.get_event_loop().run_until_complete(uploadLut(uploadKindStr,fileStr,modeStr))

# GUI General Helpers
def loadImageSettings():
    asyncio.get_event_loop().run_until_complete(loadImageSettingsAsync())

def activateGUI(condition):
    if condition:
        mainWidgetObj.objs.connectPB.setText("Disconnect")
    else:
        mainWidgetObj.objs.connectPB.setText("Connect")

    mainWidgetObj.objs.IP.setEnabled(not condition)
    mainWidgetObj.objs.connectedCheckbox.setChecked(condition)
    mainWidgetObj.objs.settingsBox.setEnabled(condition)
    mainWidgetObj.objs.uploadBox.setEnabled(condition)

def alertBox(text,descriptionStr,err=None):
    template = "{0} {1!r}:\n"
    message = template.format(type(err).__name__, err.args)
    QMessageBox.warning(mainWidgetObj, "Sorry, we couldn't complete your request", message+descriptionStr)
    
def successBox(descriptionStr):
    QMessageBox.information(mainWidgetObj, "Success!", descriptionStr) 

def main(): 
    app = QApplication([])
    global mainWidgetObj
    mainWidgetObj = webOSCalHelperWidget()
    mainWidgetObj.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()