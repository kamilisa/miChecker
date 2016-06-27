from PySide import QtCore, QtGui
from collections import OrderedDict
from . import widget
from cmd import checkCmd
from maya import OpenMayaUI
import maya.cmds as cmds
import textwrap
import shiboken

reload(checkCmd)


def getMayaWindow():
    ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)


class ModelChecker(QtGui.QDialog):
    """ Main UI class """

    def closeExistingWindow(self):
        for qt in QtGui.QApplication.topLevelWidgets():
            try:
                if qt.__class__.__name__ == self.__class__.__name__:
                    qt.close()
            except:
                pass

    def __init__(self, initialSelection, parent=getMayaWindow()):
        self.closeExistingWindow()
        super(ModelChecker, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.initialSelection = initialSelection

        self.setWindowTitle('Model Checker')
        self.setWindowFlags(QtCore.Qt.Tool)

        self.functionList = [
            checkCmd.get_history,
            checkCmd.get_transform,
            checkCmd.get_triangles,
            checkCmd.get_ngons,
            checkCmd.get_nonmanifold_vertices,
            checkCmd.get_nonmanifold_edges,
            checkCmd.get_lamina_faces,
            checkCmd.get_concave_faces,
            checkCmd.get_badextraordianry_vtx,
            checkCmd.get_opposite,
            checkCmd.get_doublesided,
            checkCmd.get_intermediate_obj,
            checkCmd.get_bad_shapenames,
            checkCmd.get_duplicated_names,
            checkCmd.get_smooth_mesh,
            checkCmd.get_shader,
            checkCmd.get_geo_suffix,
            checkCmd.get_locked_channels,
            checkCmd.get_keyframes]

        # Default check state
        self.checkListDict = [
            ('history', True),
            ('transform', True),
            ('triangles', True),
            ('nGons', True),
            ('nonManifoldVtx', True),
            ('nonManifoldEdges', True),
            ('laminaFaces', True),
            ('concaveFaces', True),
            ('badExtraordinaryVtx', True),
            ('opposite', True),
            ('doubleSided', True),
            ('intermediateObj', True),
            ('shapeNames', True),
            ('duplicateNames', True),
            ('smoothPreview', True),
            ('defaultShader', True),
            ('geoSuffix', True),
            ('lockedChannels', False),
            ('keyframes', False)]

        self.checkList = OrderedDict(self.checkListDict)

        # Create bad node list var to store path to error nodes.
        self.badNodeList = []

        # Create GUI
        self.createUI()
        self.layoutUI()

    def createUI(self):
        """ Create UI """

        # Top Area Widgets
        self.selectedLE = QtGui.QLineEdit()
        self.selectedLE.setText(self.initialSelection)
        self.selectBTN = QtGui.QPushButton('Select')
        self.selectBTN.clicked.connect(self.select)

        for i in self.checkList:
            # Create checkbox
            exec("self.%sCheckBox = QtGui.QCheckBox('%s')" % (i, i))

            # Set checkstate and name object to save check state
            exec("self.%sCheckBox.setCheckState(QtCore.Qt.Checked)" % i)
            exec("self.%sCheckBox.setObjectName('%sCheckBox')" % (i, i))
            exec(
                "self.%sCheckBox.stateChanged.connect(self.toggleCheckState)"
                % i)

            # Chnage chack state base on current state
            if self.checkList[i] is False:
                exec("self.%sCheckBox.setCheckState(QtCore.Qt.Unchecked)" % i)

            exec("self.%sListWidget = QtGui.QListWidget()" % i)
            exec(
                ("self.%sListWidget.currentItemChanged"
                 ".connect(self.errorClicked)" % i)
                )
            exec(
                "self.%sListWidget.itemClicked"
                ".connect(self.errorClicked)" % i)
            exec(
                "self.%sListWidget.setSelectionMode"
                "(QtGui.QAbstractItemView.ExtendedSelection)" % i)

            exec("self.%sResultLabel = widget.CustomLabel('%s')" % (i, i))

        self.presetCB = QtGui.QComboBox()
        self.presetCB.addItem("All")
        self.presetCB.addItem("Topology")
        self.presetCB.addItem("Mesh")
        self.presetCB.currentIndexChanged.connect(self.changePreset)

        self.geoSuffixLineEdit01 = QtGui.QLineEdit("_GEP")
        self.geoSuffixLineEdit02 = QtGui.QLineEdit("_GES")
        self.geoSuffixLineEdit03 = QtGui.QLineEdit("_NRB")
        self.geoSuffixLineEdit04 = QtGui.QLineEdit("_GRP")
        self.geoSuffixLineEdit05 = QtGui.QLineEdit("_LOC")
        self.geoSuffixLineEdit06 = QtGui.QLineEdit("_PLY")
        self.resetButton = QtGui.QPushButton("Reset")
        self.resetButton.setFixedHeight(40)
        self.resetButton.clicked.connect(self.resetSetting)

        # Bad nodes list widget
        self.badNodeListWidget = QtGui.QListWidget()
        self.badNodeListWidget.currentItemChanged.connect(self.itemClicked)

        self.searchButton = QtGui.QPushButton('SEARCH')
        self.searchButton.setFixedHeight(150)
        self.searchButton.clicked.connect(self.search)

        # progress bar
        self.progressBar = QtGui.QProgressBar()

    def layoutUI(self):
        # Layout for the selected object.
        topLayout = widget.CustomBoxLayout(QtGui.QBoxLayout.LeftToRight)
        topLayout.addWidget(self.selectedLE)

        # midLayout = widget.CustomBoxLayout(QtGui.QBoxLayout.LeftToRight)

        checkBoxLayout = widget.CustomBoxLayout(QtGui.QBoxLayout.TopToBottom)
        checkBoxLayout.addWidget(self.presetCB)
        for i in self.checkList:
            exec("checkBoxLayout.addWidget(self.%sCheckBox)" % i)
        for num in range(6):
            exec(
                "checkBoxLayout.addWidget(self.geoSuffixLineEdit0%s)"
                % str(num + 1))
        checkBoxLayout.addWidget(self.resetButton)

        scrollArea = QtGui.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        scrollAreaWidgetContents = QtGui.QWidget(scrollArea)
        scrollArea.setWidget(scrollAreaWidgetContents)
        errorListLayout = QtGui.QVBoxLayout(scrollAreaWidgetContents)
        for i in self.checkList:
            errorListLayout.addWidget(QtGui.QLabel(i))
            exec("errorListLayout.addWidget(self.%sListWidget)" % i)

        rightLayout = widget.CustomBoxLayout(QtGui.QBoxLayout.TopToBottom)
        rightLayout.addWidget(self.searchButton)
        for i in self.checkList:
            subLayout = widget.CustomBoxLayout(QtGui.QBoxLayout.LeftToRight)
            exec("subLayout.addWidget(self.%sResultLabel)" % i)
            exec("rightLayout.addLayout(subLayout)")

        # Set splitter
        midSplitter = QtGui.QSplitter()
        midWidgetA = QtGui.QWidget()
        midWidgetB = QtGui.QWidget()
        midWidgetA.setLayout(checkBoxLayout)
        midWidgetB.setLayout(rightLayout)
        midSplitter.addWidget(midWidgetA)
        midSplitter.addWidget(self.badNodeListWidget)
        midSplitter.addWidget(scrollArea)
        midSplitter.addWidget(midWidgetB)

        topLayout.addWidget(self.selectBTN)

        mainLayout = widget.CustomBoxLayout(QtGui.QBoxLayout.TopToBottom)
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(midSplitter)
        mainLayout.addWidget(self.progressBar)

        self.setLayout(mainLayout)

    def initData(self):

        sel = self.selectedLE.text()
        self.allDagnodes = cmds.listRelatives(
            sel,
            ad=True,
            fullPath=True,
            type="transform")

        if self.allDagnodes is None:
            self.allDagnodes = []
        self.allDagnodes.append(sel)

        self.dataDict = {}
        for item in self.allDagnodes:
            self.dataDict[item] = {}
            for check in self.checkList:
                self.dataDict[item][check] = []

    def select(self):
        sel = cmds.ls(sl=True, fl=True, long=True)[0]
        self.selectedLE.setText(sel)

    def toggleCheckState(self):
        currentState = self.sender().checkState()
        checkBox = self.sender().objectName()
        checkItem = checkBox.split("CheckBox")[0]
        if currentState == QtCore.Qt.CheckState.Unchecked:
            state = False
        elif currentState == QtCore.Qt.CheckState.Checked:
            state = True
        else:
            pass

        self.checkList[checkItem] = state

    def itemClicked(self, index):
        if index is None:
            return

        currentItem = str(index.text())
        cmds.select(currentItem, r=True)

        for check in self.checkList:
            exec("self.%sListWidget.clear()" % check)
            exec(
                "self.%sListWidget.addItems(self.dataDict[currentItem][check])"
                % check)

    def errorClicked(self, *args):
        if args[0] is None:
            return
        try:
            selectedItems = ["*" + i.text() for i
                             in args[0].listWidget().selectedItems()]
            cmds.select(selectedItems, r=True)
            cmds.setFocus("MayaWindow")
        except ValueError:
            """ When channels/attributes/etc are selected,
                do not try to select """
            pass

    def resetSetting(self):
        self.badNodeListWidget.clear()
        for i in self.checkList:
            exec("self.%sListWidget.clear()" % i)
            exec("self.%sCheckBox.setCheckState(QtCore.Qt.Checked)" % i)
            exec("self.%sResultLabel.toDefault()" % i)
        self.badExtraordinaryVtxCheckBox.setCheckState(QtCore.Qt.Unchecked)
        self.lockedChannelsCheckBox.setCheckState(QtCore.Qt.Unchecked)
        self.keyframesCheckBox.setCheckState(QtCore.Qt.Unchecked)
        self.geoSuffixLineEdit01.setText("_GEP")
        self.geoSuffixLineEdit02.setText("_GES")
        self.geoSuffixLineEdit03.setText("_NRB")
        self.geoSuffixLineEdit04.setText("_GRP")
        self.geoSuffixLineEdit05.setText("_LOC")
        self.geoSuffixLineEdit06.setText("_PLY")
        self.progressBar.reset()

    def getSuffixList(self):
        suffix1 = str(self.geoSuffixLineEdit01.text())
        suffix2 = str(self.geoSuffixLineEdit02.text())
        suffix3 = str(self.geoSuffixLineEdit03.text())
        suffix4 = str(self.geoSuffixLineEdit04.text())
        suffix5 = str(self.geoSuffixLineEdit05.text())
        suffix6 = str(self.geoSuffixLineEdit06.text())
        suffixList = [
            suffix1,
            suffix2,
            suffix3,
            suffix4,
            suffix5,
            suffix6,
            suffix1 + "Shape",
            suffix2 + "Shape",
            suffix3 + "Shape",
            suffix4 + "Shape",
            suffix5 + "Shape",
            suffix6 + "Shape"]
        return suffixList

    def changeLabelColorbyResult(self):
        """ Check each and make labels green if it's ok, otherwise red """

        for i in self.checkList:
            ifblock = """\
            %sResult = [self.dataDict[child]['%s'] for child
                        in self.allDagnodes]\n
            if self.%sCheckBox.checkState() == 2:
                if %sResult.count([]) == len(%sResult):\n
                    self.%sResultLabel.toGreen()\n
                else:\n
                    self.%sResultLabel.toRed()\n
            else:
                self.%sResultLabel.toDefault()\n
            """ % (i, i, i, i, i, i, i, i)
            exec(textwrap.dedent(ifblock))

    def incrementProgressbar(self):
        # current value
        value = self.progressBar.value()

        # increment
        value += 1

        # Update
        self.progressBar.setValue(value)
        QtCore.QCoreApplication.processEvents()

    def initProgressbar(self, list, word):
        self.progressBar.reset()
        self.progressBar.setRange(1, len(list))

    def clear(self):
        """ Clear all list widgets """

        self.badNodeListWidget.clear()
        for i in self.checkList:
            c = "self.%sListWidget" % i
            exec("%s.clear()" % c)

    def search(self):
        """ Search all error """

        self.initData()
        self.badNodeListWidget.clear()

        # List for adding to badnodelistwidget
        self.badNodeList = []

        # Number of checks
        num = len([i for i in self.checkList if self.checkList[i] is True])

        self.progressBar.reset()
        self.progressBar.setRange(1, num)

        for name, func in zip(self.checkList, self.functionList):
            if self.checkList[name] is True:
                suffix = self.getSuffixList()
                func(self.dataDict, self.allDagnodes, self.badNodeList, suffix)
                self.incrementProgressbar()

        # Remove duplicate items and add to list widget
        self.badNodeList = list(set(self.badNodeList))

        for item in self.badNodeList:

            # Add icons based on node type
            nt = cmds.nodeType(item)
            if nt == "transform":
                iconPath = r":/transform.svg"
            elif nt == "mesh":
                iconPath = r":/mesh.svg"
            else:
                iconPath = r":/menuIconHelp.png"
            widgetItem = QtGui.QListWidgetItem(item)
            widgetItem.setIcon(QtGui.QIcon(iconPath))

            self.badNodeListWidget.addItem(widgetItem)

        self.changeLabelColorbyResult()

    def checkAll(self, status):
        if status is True:
            for i in self.checkList:
                exec("self.%sCheckBox.setCheckState(QtCore.Qt.Checked)" % i)
        elif status is False:
            for i in self.checkList:
                exec("self.%sCheckBox.setCheckState(QtCore.Qt.Unchecked)" % i)
        else:
            pass

    def changePreset(self, *args):
        idx = args[0]

        if idx == 0:
            self.checkAll(True)
        elif idx == 1:
            self.checkAll(False)
            self.trianglesCheckBox.setCheckState(QtCore.Qt.Checked)
            self.nGonsCheckBox.setCheckState(QtCore.Qt.Checked)
            self.nonManifoldVtxCheckBox.setCheckState(QtCore.Qt.Checked)
            self.nonManifoldEdgesCheckBox.setCheckState(QtCore.Qt.Checked)
            self.laminaFacesCheckBox.setCheckState(QtCore.Qt.Checked)
            self.concaveFacesCheckBox.setCheckState(QtCore.Qt.Checked)
            self.badExtraordinaryVtxCheckBox.setCheckState(QtCore.Qt.Checked)
        elif idx == 2:
            self.checkAll(True)
            self.trianglesCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.nGonsCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.nonManifoldVtxCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.nonManifoldEdgesCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.laminaFacesCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.concaveFacesCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.badExtraordinaryVtxCheckBox.setCheckState(QtCore.Qt.Unchecked)
        else:
            pass


def main(dock=False):
    """ main """

    global checkerWin
    try:
        checkerWin.close()
    except:
        pass

    sel = cmds.ls(sl=True, long=True)
    if len(sel) == 0:
        sel = ""
    else:
        sel = sel[0]

    checkerWin = ModelChecker(sel)
    checkerWin.setObjectName("checker_mainWindow")

    if dock is True:
        from pymel import all as pm

        if pm.dockControl('model_checker_dock', q=True, ex=1):
            pm.deleteUI('model_checker_dock')

        floatingLayout = pm.paneLayout(configuration='single', w=700)

        pm.dockControl(
            'model_checker_dock',
            aa=['right', 'left'],
            a='right',
            fl=False,
            con=floatingLayout,
            label="Model Checker",
            w=300)

        pm.control('checker_mainWindow', e=True, parent=floatingLayout)
    else:
        checkerWin.show()
        checkerWin.raise_()
