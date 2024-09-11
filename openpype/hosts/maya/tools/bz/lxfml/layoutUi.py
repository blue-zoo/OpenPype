# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layout.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from openpype.hosts.maya.tools.bz.lxfml.iconbutton import PromotedIconButton
from openpype.hosts.maya.tools.bz.lxfml.iconbutton import PromotedIcon


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(666, 691)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.menuDocs = QAction(MainWindow)
        self.menuDocs.setObjectName(u"menuDocs")
        self.menuClose = QAction(MainWindow)
        self.menuClose.setObjectName(u"menuClose")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_3 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.geoGrp = QGroupBox(self.centralwidget)
        self.geoGrp.setObjectName(u"geoGrp")
        self.geoGrp.setCheckable(True)
        self.verticalLayout_4 = QVBoxLayout(self.geoGrp)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.geoPathLayout = QGridLayout()
        self.geoPathLayout.setObjectName(u"geoPathLayout")
        self.xmlOpen = PromotedIconButton(self.geoGrp)
        self.xmlOpen.setObjectName(u"xmlOpen")

        self.geoPathLayout.addWidget(self.xmlOpen, 0, 2, 1, 1)

        self.xmlPath = QLineEdit(self.geoGrp)
        self.xmlPath.setObjectName(u"xmlPath")

        self.geoPathLayout.addWidget(self.xmlPath, 0, 1, 1, 1)

        self.geoPathLabel = QLabel(self.geoGrp)
        self.geoPathLabel.setObjectName(u"geoPathLabel")
        self.geoPathLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.geoPathLayout.addWidget(self.geoPathLabel, 1, 0, 1, 1)

        self.geoOpen = PromotedIconButton(self.geoGrp)
        self.geoOpen.setObjectName(u"geoOpen")

        self.geoPathLayout.addWidget(self.geoOpen, 1, 2, 1, 1)

        self.xmlLabel = QLabel(self.geoGrp)
        self.xmlLabel.setObjectName(u"xmlLabel")
        self.xmlLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.geoPathLayout.addWidget(self.xmlLabel, 0, 0, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.geoPath = QLineEdit(self.geoGrp)
        self.geoPath.setObjectName(u"geoPath")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.geoPath.sizePolicy().hasHeightForWidth())
        self.geoPath.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.geoPath)

        self.geoBrick = QLabel(self.geoGrp)
        self.geoBrick.setObjectName(u"geoBrick")
        font = QFont()
        font.setItalic(False)
        self.geoBrick.setFont(font)

        self.horizontalLayout.addWidget(self.geoBrick)

        self.geoExt = QLineEdit(self.geoGrp)
        self.geoExt.setObjectName(u"geoExt")
        sizePolicy.setHeightForWidth(self.geoExt.sizePolicy().hasHeightForWidth())
        self.geoExt.setSizePolicy(sizePolicy)
        self.geoExt.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout.addWidget(self.geoExt)


        self.geoPathLayout.addLayout(self.horizontalLayout, 1, 1, 1, 1)

        self.geoParentLabel = QLabel(self.geoGrp)
        self.geoParentLabel.setObjectName(u"geoParentLabel")
        self.geoParentLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.geoPathLayout.addWidget(self.geoParentLabel, 2, 0, 1, 1)

        self.geoParent = QLineEdit(self.geoGrp)
        self.geoParent.setObjectName(u"geoParent")

        self.geoPathLayout.addWidget(self.geoParent, 2, 1, 1, 1)


        self.verticalLayout_4.addLayout(self.geoPathLayout)

        self.optionsLayout = QGridLayout()
        self.optionsLayout.setObjectName(u"optionsLayout")
        self.optionsLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.deleteColourSets = QCheckBox(self.geoGrp)
        self.deleteColourSets.setObjectName(u"deleteColourSets")

        self.optionsLayout.addWidget(self.deleteColourSets, 0, 1, 1, 1, Qt.AlignHCenter)

        self.deleteHistory = QCheckBox(self.geoGrp)
        self.deleteHistory.setObjectName(u"deleteHistory")

        self.optionsLayout.addWidget(self.deleteHistory, 0, 2, 1, 1, Qt.AlignHCenter)

        self.setTexelDensity = QCheckBox(self.geoGrp)
        self.setTexelDensity.setObjectName(u"setTexelDensity")

        self.optionsLayout.addWidget(self.setTexelDensity, 1, 1, 1, 1, Qt.AlignHCenter)

        self.softenEdges = QCheckBox(self.geoGrp)
        self.softenEdges.setObjectName(u"softenEdges")

        self.optionsLayout.addWidget(self.softenEdges, 1, 2, 1, 1, Qt.AlignHCenter)

        self.updateDisplayEdges = QCheckBox(self.geoGrp)
        self.updateDisplayEdges.setObjectName(u"updateDisplayEdges")

        self.optionsLayout.addWidget(self.updateDisplayEdges, 1, 0, 1, 1, Qt.AlignHCenter)

        self.updateUVs = QCheckBox(self.geoGrp)
        self.updateUVs.setObjectName(u"updateUVs")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.updateUVs.sizePolicy().hasHeightForWidth())
        self.updateUVs.setSizePolicy(sizePolicy2)

        self.optionsLayout.addWidget(self.updateUVs, 0, 0, 1, 1, Qt.AlignHCenter)

        self.updateDisplayColourChannel = QCheckBox(self.geoGrp)
        self.updateDisplayColourChannel.setObjectName(u"updateDisplayColourChannel")

        self.optionsLayout.addWidget(self.updateDisplayColourChannel, 2, 0, 1, 1, Qt.AlignHCenter)


        self.verticalLayout_4.addLayout(self.optionsLayout)


        self.verticalLayout_3.addWidget(self.geoGrp)

        self.scaleGrp = QGroupBox(self.centralwidget)
        self.scaleGrp.setObjectName(u"scaleGrp")
        self.scaleGrp.setCheckable(True)
        self.horizontalLayout_3 = QHBoxLayout(self.scaleGrp)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.scaleValue = QDoubleSpinBox(self.scaleGrp)
        self.scaleValue.setObjectName(u"scaleValue")
        self.scaleValue.setMaximum(100000.000000000000000)
        self.scaleValue.setValue(20.000000000000000)

        self.horizontalLayout_3.addWidget(self.scaleValue)


        self.verticalLayout_3.addWidget(self.scaleGrp)

        self.shdGrp = QGroupBox(self.centralwidget)
        self.shdGrp.setObjectName(u"shdGrp")
        self.shdGrp.setCheckable(True)
        self.verticalLayout_5 = QVBoxLayout(self.shdGrp)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.shaderPathLayout = QGridLayout()
        self.shaderPathLayout.setObjectName(u"shaderPathLayout")
        self.shdPath = QLineEdit(self.shdGrp)
        self.shdPath.setObjectName(u"shdPath")

        self.shaderPathLayout.addWidget(self.shdPath, 0, 2, 1, 1)

        self.shdOpen = PromotedIconButton(self.shdGrp)
        self.shdOpen.setObjectName(u"shdOpen")

        self.shaderPathLayout.addWidget(self.shdOpen, 0, 3, 1, 1)

        self.nsLabel = QLabel(self.shdGrp)
        self.nsLabel.setObjectName(u"nsLabel")
        self.nsLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.shaderPathLayout.addWidget(self.nsLabel, 1, 0, 1, 1)

        self.nsInput = QLineEdit(self.shdGrp)
        self.nsInput.setObjectName(u"nsInput")

        self.shaderPathLayout.addWidget(self.nsInput, 1, 2, 1, 1)

        self.shdPathLabel = QLabel(self.shdGrp)
        self.shdPathLabel.setObjectName(u"shdPathLabel")
        self.shdPathLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.shaderPathLayout.addWidget(self.shdPathLabel, 0, 0, 1, 1)

        self.sgLabel = QLabel(self.shdGrp)
        self.sgLabel.setObjectName(u"sgLabel")
        self.sgLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.shaderPathLayout.addWidget(self.sgLabel, 2, 0, 1, 1)

        self.sgInput = QLineEdit(self.shdGrp)
        self.sgInput.setObjectName(u"sgInput")

        self.shaderPathLayout.addWidget(self.sgInput, 2, 2, 1, 1)


        self.verticalLayout_5.addLayout(self.shaderPathLayout)


        self.verticalLayout_3.addWidget(self.shdGrp)

        self.paletteGrp = QGroupBox(self.centralwidget)
        self.paletteGrp.setObjectName(u"paletteGrp")
        self.paletteGrp.setCheckable(True)
        self.verticalLayout_6 = QVBoxLayout(self.paletteGrp)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.palettePath = QLineEdit(self.paletteGrp)
        self.palettePath.setObjectName(u"palettePath")

        self.gridLayout.addWidget(self.palettePath, 0, 1, 1, 1)

        self.paletteLabel = QLabel(self.paletteGrp)
        self.paletteLabel.setObjectName(u"paletteLabel")

        self.gridLayout.addWidget(self.paletteLabel, 0, 0, 1, 1)

        self.paletteOpen = PromotedIconButton(self.paletteGrp)
        self.paletteOpen.setObjectName(u"paletteOpen")

        self.gridLayout.addWidget(self.paletteOpen, 0, 2, 1, 1)


        self.verticalLayout_6.addLayout(self.gridLayout)

        self.vertexColours = QCheckBox(self.paletteGrp)
        self.vertexColours.setObjectName(u"vertexColours")

        self.verticalLayout_6.addWidget(self.vertexColours)


        self.verticalLayout_3.addWidget(self.paletteGrp)

        self.decalGrp = QGroupBox(self.centralwidget)
        self.decalGrp.setObjectName(u"decalGrp")
        self.decalGrp.setCheckable(True)
        self.decalGrp.setChecked(False)
        self.verticalLayout = QVBoxLayout(self.decalGrp)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.decalShadingNetwork = QGroupBox(self.decalGrp)
        self.decalShadingNetwork.setObjectName(u"decalShadingNetwork")
        self.decalShadingNetwork.setCheckable(True)
        self.horizontalLayout_2 = QHBoxLayout(self.decalShadingNetwork)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.decalDoubleSided = QCheckBox(self.decalShadingNetwork)
        self.decalDoubleSided.setObjectName(u"decalDoubleSided")

        self.horizontalLayout_2.addWidget(self.decalDoubleSided)

        self.decalStickers = QCheckBox(self.decalShadingNetwork)
        self.decalStickers.setObjectName(u"decalStickers")

        self.horizontalLayout_2.addWidget(self.decalStickers)


        self.verticalLayout.addWidget(self.decalShadingNetwork)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.decalPath = QLineEdit(self.decalGrp)
        self.decalPath.setObjectName(u"decalPath")

        self.gridLayout_2.addWidget(self.decalPath, 0, 2, 1, 1)

        self.decalLabel = QLabel(self.decalGrp)
        self.decalLabel.setObjectName(u"decalLabel")

        self.gridLayout_2.addWidget(self.decalLabel, 0, 0, 1, 1, Qt.AlignRight)

        self.maskLabel = QLabel(self.decalGrp)
        self.maskLabel.setObjectName(u"maskLabel")

        self.gridLayout_2.addWidget(self.maskLabel, 2, 0, 1, 1, Qt.AlignRight)

        self.maskInput = QLineEdit(self.decalGrp)
        self.maskInput.setObjectName(u"maskInput")

        self.gridLayout_2.addWidget(self.maskInput, 2, 2, 1, 1)

        self.decalOpen = PromotedIconButton(self.decalGrp)
        self.decalOpen.setObjectName(u"decalOpen")

        self.gridLayout_2.addWidget(self.decalOpen, 0, 3, 1, 1)

        self.switchLabel = QLabel(self.decalGrp)
        self.switchLabel.setObjectName(u"switchLabel")

        self.gridLayout_2.addWidget(self.switchLabel, 1, 0, 1, 1, Qt.AlignRight)

        self.switchInput = QLineEdit(self.decalGrp)
        self.switchInput.setObjectName(u"switchInput")

        self.gridLayout_2.addWidget(self.switchInput, 1, 2, 1, 1)

        self.shaderSwitchValidation = QHBoxLayout()
        self.shaderSwitchValidation.setObjectName(u"shaderSwitchValidation")
        self.shaderSwitchValid = PromotedIcon(self.decalGrp)
        self.shaderSwitchValid.setObjectName(u"shaderSwitchValid")

        self.shaderSwitchValidation.addWidget(self.shaderSwitchValid)

        self.shaderSwitchInvalid = PromotedIcon(self.decalGrp)
        self.shaderSwitchInvalid.setObjectName(u"shaderSwitchInvalid")

        self.shaderSwitchValidation.addWidget(self.shaderSwitchInvalid)


        self.gridLayout_2.addLayout(self.shaderSwitchValidation, 1, 3, 1, 1)

        self.maskSwitchValidation = QHBoxLayout()
        self.maskSwitchValidation.setObjectName(u"maskSwitchValidation")
        self.maskSwitchValid = PromotedIcon(self.decalGrp)
        self.maskSwitchValid.setObjectName(u"maskSwitchValid")

        self.maskSwitchValidation.addWidget(self.maskSwitchValid)

        self.maskSwitchInvalid = PromotedIcon(self.decalGrp)
        self.maskSwitchInvalid.setObjectName(u"maskSwitchInvalid")

        self.maskSwitchValidation.addWidget(self.maskSwitchInvalid)


        self.gridLayout_2.addLayout(self.maskSwitchValidation, 2, 3, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)


        self.verticalLayout_3.addWidget(self.decalGrp)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.runImport = QPushButton(self.centralwidget)
        self.runImport.setObjectName(u"runImport")

        self.verticalLayout_3.addWidget(self.runImport)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 666, 21))
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuHelp.addAction(self.menuDocs)
        self.menuFile.addAction(self.menuClose)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"LEGO Importer", None))
        self.menuDocs.setText(QCoreApplication.translate("MainWindow", u"Documentation", None))
#if QT_CONFIG(tooltip)
        self.menuDocs.setToolTip(QCoreApplication.translate("MainWindow", u"Opens a web browser to view the documentation.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.menuDocs.setStatusTip(QCoreApplication.translate("MainWindow", u"View the documentation.", None))
#endif // QT_CONFIG(statustip)
        self.menuClose.setText(QCoreApplication.translate("MainWindow", u"Close", None))
#if QT_CONFIG(tooltip)
        self.menuClose.setToolTip(QCoreApplication.translate("MainWindow", u"Close the window.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.menuClose.setStatusTip(QCoreApplication.translate("MainWindow", u"Close the window.", None))
#endif // QT_CONFIG(statustip)
        self.geoGrp.setTitle(QCoreApplication.translate("MainWindow", u"Import/Update Geometry", None))
#if QT_CONFIG(tooltip)
        self.xmlOpen.setToolTip(QCoreApplication.translate("MainWindow", u"Navigate to LEGO XML file.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.xmlOpen.setStatusTip(QCoreApplication.translate("MainWindow", u"Navigate to LEGO XML file.", None))
#endif // QT_CONFIG(statustip)
        self.xmlOpen.setText("")
#if QT_CONFIG(tooltip)
        self.xmlPath.setToolTip(QCoreApplication.translate("MainWindow", u"Set the path to the LEGO XML file.\n"
"This is typically saved with a .lxfml extension.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.xmlPath.setStatusTip(QCoreApplication.translate("MainWindow", u"Set the path to the LEGO XML file.", None))
#endif // QT_CONFIG(statustip)
        self.xmlPath.setText("")
        self.xmlPath.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Y:\\LEGO\\1686s_LegoCitySeries1\\Libraries\\Model_Library\\_importingTestA\\legoExample.lxfml", None))
        self.geoPathLabel.setText(QCoreApplication.translate("MainWindow", u"Geo Path:", None))
#if QT_CONFIG(tooltip)
        self.geoOpen.setToolTip(QCoreApplication.translate("MainWindow", u"Navigate to LEGO geometry file.\n"
"\n"
"Some processing is done on the path to determine where the brick ID can be found.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.geoOpen.setStatusTip(QCoreApplication.translate("MainWindow", u"Navigate to LEGO geometry file.", None))
#endif // QT_CONFIG(statustip)
        self.geoOpen.setText("")
        self.xmlLabel.setText(QCoreApplication.translate("MainWindow", u"XML Path:", None))
#if QT_CONFIG(tooltip)
        self.geoPath.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Set the path to the lego geometry.</p><p>This is everything in the path before the brick ID.<br/>For example, for <span style=\" font-weight:600;\">C:/bricks/brick_1234.ma</span>, then this value would be <span style=\" font-weight:600;\">C:/bricks/brick_</span>.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.geoPath.setStatusTip(QCoreApplication.translate("MainWindow", u"Set the path to the lego geometry.", None))
#endif // QT_CONFIG(statustip)
        self.geoPath.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Y:\\LEGO\\1686s_LegoCitySeries1\\Libraries\\Model_Library\\_legoLibrary\\High_processed\\m", None))
        self.geoBrick.setText(QCoreApplication.translate("MainWindow", u"[brickID]", None))
        self.geoExt.setText("")
        self.geoExt.setPlaceholderText(QCoreApplication.translate("MainWindow", u".mb", None))
        self.geoParentLabel.setText(QCoreApplication.translate("MainWindow", u"Group Name:", None))
#if QT_CONFIG(tooltip)
        self.geoParent.setToolTip(QCoreApplication.translate("MainWindow", u"Define a group to parent the bricks under.\n"
"If left empty, no group will be used.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.geoParent.setStatusTip(QCoreApplication.translate("MainWindow", u"Set the brick geometry group name.", None))
#endif // QT_CONFIG(statustip)
        self.geoParent.setText("")
        self.geoParent.setPlaceholderText(QCoreApplication.translate("MainWindow", u"LEGO_Build", None))
#if QT_CONFIG(tooltip)
        self.deleteColourSets.setToolTip(QCoreApplication.translate("MainWindow", u"Delete all colour sets.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.deleteColourSets.setStatusTip(QCoreApplication.translate("MainWindow", u"Delete all colour sets.", None))
#endif // QT_CONFIG(statustip)
        self.deleteColourSets.setText(QCoreApplication.translate("MainWindow", u"Delete Colour Sets", None))
#if QT_CONFIG(tooltip)
        self.deleteHistory.setToolTip(QCoreApplication.translate("MainWindow", u"Delete the construction history from all nodes.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.deleteHistory.setStatusTip(QCoreApplication.translate("MainWindow", u"Delete the construction history from all nodes.", None))
#endif // QT_CONFIG(statustip)
        self.deleteHistory.setText(QCoreApplication.translate("MainWindow", u"Delete History", None))
#if QT_CONFIG(tooltip)
        self.setTexelDensity.setToolTip(QCoreApplication.translate("MainWindow", u"Set the texel density to 25 | 512.\n"
"\n"
"This is a heavy operation and will add considerable processing time to the import.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.setTexelDensity.setStatusTip(QCoreApplication.translate("MainWindow", u"Set a uniform texel density on all nodes.", None))
#endif // QT_CONFIG(statustip)
        self.setTexelDensity.setText(QCoreApplication.translate("MainWindow", u"Set Texel Density", None))
#if QT_CONFIG(tooltip)
        self.softenEdges.setToolTip(QCoreApplication.translate("MainWindow", u"Apply the soften edge modifier.\n"
"\n"
"This is a heavy operation and will add considerable processing time to the import.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.softenEdges.setStatusTip(QCoreApplication.translate("MainWindow", u"Apply the soften edge modifier.", None))
#endif // QT_CONFIG(statustip)
        self.softenEdges.setText(QCoreApplication.translate("MainWindow", u"Soften Edges", None))
#if QT_CONFIG(tooltip)
        self.updateDisplayEdges.setToolTip(QCoreApplication.translate("MainWindow", u"Ensure \"Mesh Component Display Edges\" is set to \"Standard\".", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.updateDisplayEdges.setStatusTip(QCoreApplication.translate("MainWindow", u"Ensure Display Edges is set to the default value.", None))
#endif // QT_CONFIG(statustip)
        self.updateDisplayEdges.setText(QCoreApplication.translate("MainWindow", u"Set Standard Display Edges", None))
#if QT_CONFIG(tooltip)
        self.updateUVs.setToolTip(QCoreApplication.translate("MainWindow", u"Rename UV sets to include map1 and bumpSet.\n"
"\n"
"If map1 or bumpSet already exists, it will be deleted.\n"
"If any UV set contains the text \"3DP\", then the first instance will be renamed to bumpSet.\n"
"The very first UV set will be set to map1. If this clases with bumpSet, then bumpSet will be duplicated.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.updateUVs.setStatusTip(QCoreApplication.translate("MainWindow", u"Add map1 and bumpSet UV sets.", None))
#endif // QT_CONFIG(statustip)
        self.updateUVs.setText(QCoreApplication.translate("MainWindow", u"Rename UV Sets", None))
#if QT_CONFIG(tooltip)
        self.updateDisplayColourChannel.setToolTip(QCoreApplication.translate("MainWindow", u" Set the display colour channel to diffuse.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.updateDisplayColourChannel.setStatusTip(QCoreApplication.translate("MainWindow", u" Set the display colour channel to diffuse.", None))
#endif // QT_CONFIG(statustip)
        self.updateDisplayColourChannel.setText(QCoreApplication.translate("MainWindow", u"Set Diffuse Colour Channel", None))
        self.scaleGrp.setTitle(QCoreApplication.translate("MainWindow", u"Set Scale", None))
        self.scaleValue.setSuffix(QCoreApplication.translate("MainWindow", u"x", None))
        self.shdGrp.setTitle(QCoreApplication.translate("MainWindow", u"Assign Shaders", None))
#if QT_CONFIG(tooltip)
        self.shdPath.setToolTip(QCoreApplication.translate("MainWindow", u"Path to the shaders file.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.shdPath.setStatusTip(QCoreApplication.translate("MainWindow", u"Path to the shaders file.", None))
#endif // QT_CONFIG(statustip)
        self.shdPath.setText("")
        self.shdPath.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Y:\\LEGO\\1686s_LegoCitySeries1\\Libraries\\Shader_Library\\shaders\\master\\published\\master_shader.ma", None))
#if QT_CONFIG(tooltip)
        self.shdOpen.setToolTip(QCoreApplication.translate("MainWindow", u"Navigate to a shader file.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.shdOpen.setStatusTip(QCoreApplication.translate("MainWindow", u"Navigate to a shader file.", None))
#endif // QT_CONFIG(statustip)
        self.shdOpen.setText("")
        self.nsLabel.setText(QCoreApplication.translate("MainWindow", u"Namespace:", None))
#if QT_CONFIG(tooltip)
        self.nsInput.setToolTip(QCoreApplication.translate("MainWindow", u"Set the shader namespace.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.nsInput.setStatusTip(QCoreApplication.translate("MainWindow", u"Set the shader namespace.", None))
#endif // QT_CONFIG(statustip)
        self.nsInput.setText("")
        self.nsInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"shaders", None))
        self.shdPathLabel.setText(QCoreApplication.translate("MainWindow", u"Shader Path:", None))
        self.sgLabel.setText(QCoreApplication.translate("MainWindow", u"Shading Group:", None))
#if QT_CONFIG(tooltip)
        self.sgInput.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>Name of the shadingGroup node.</p><p><br/></p><p>A wildcard (<span style=\" font-weight:600;\">*</span>) may be used, and in the case of multiple shaders, use curly brackets (<span style=\" font-weight:600;\">{}</span>) to determine where in the name to put the material ID.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.sgInput.setStatusTip(QCoreApplication.translate("MainWindow", u"Name of the shadingGroup node.", None))
#endif // QT_CONFIG(statustip)
        self.sgInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"PLASTIC_MASTER_SG", None))
        self.paletteGrp.setTitle(QCoreApplication.translate("MainWindow", u"Load Palette Colours", None))
#if QT_CONFIG(tooltip)
        self.palettePath.setToolTip(QCoreApplication.translate("MainWindow", u"Path to the palette colour list file.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.palettePath.setStatusTip(QCoreApplication.translate("MainWindow", u"Path to the palette colour list file.", None))
#endif // QT_CONFIG(statustip)
        self.palettePath.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Y:/LEGO/1880s_LegoCity2025/Libraries/Shader_Library/Color_ID_List_BZ.json", None))
        self.paletteLabel.setText(QCoreApplication.translate("MainWindow", u"Colour Palette:", None))
#if QT_CONFIG(tooltip)
        self.paletteOpen.setToolTip(QCoreApplication.translate("MainWindow", u"Navigate to a palette colour file.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.paletteOpen.setStatusTip(QCoreApplication.translate("MainWindow", u"Navigate to a palette colour file.", None))
#endif // QT_CONFIG(statustip)
        self.paletteOpen.setText("")
#if QT_CONFIG(tooltip)
        self.vertexColours.setToolTip(QCoreApplication.translate("MainWindow", u"Set brick vertex colours.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.vertexColours.setStatusTip(QCoreApplication.translate("MainWindow", u"Set brick vertex colours.", None))
#endif // QT_CONFIG(statustip)
        self.vertexColours.setText(QCoreApplication.translate("MainWindow", u"Set Vertex Colours", None))
        self.decalGrp.setTitle(QCoreApplication.translate("MainWindow", u"Decals", None))
        self.decalShadingNetwork.setTitle(QCoreApplication.translate("MainWindow", u"Create and assign local shading network", None))
        self.decalDoubleSided.setText(QCoreApplication.translate("MainWindow", u"Double Sided", None))
        self.decalStickers.setText(QCoreApplication.translate("MainWindow", u"Stickers", None))
#if QT_CONFIG(tooltip)
        self.decalPath.setToolTip(QCoreApplication.translate("MainWindow", u"Path to the decals directory.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.decalPath.setStatusTip(QCoreApplication.translate("MainWindow", u"Path to the decals directory.", None))
#endif // QT_CONFIG(statustip)
        self.decalPath.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Y:\\LEGO\\1686s_LegoCitySeries1\\Libraries\\Texture_Library\\Decorations", None))
        self.decalLabel.setText(QCoreApplication.translate("MainWindow", u"Decal Files:", None))
        self.maskLabel.setText(QCoreApplication.translate("MainWindow", u"Mask Switch:", None))
#if QT_CONFIG(tooltip)
        self.maskInput.setToolTip(QCoreApplication.translate("MainWindow", u"Name of the mask switch.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.maskInput.setStatusTip(QCoreApplication.translate("MainWindow", u"Name of the mask switch.", None))
#endif // QT_CONFIG(statustip)
        self.maskInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"DECAL_MASK_SWITCH_00_09", None))
#if QT_CONFIG(tooltip)
        self.decalOpen.setToolTip(QCoreApplication.translate("MainWindow", u"Open the directory containing LEGO decal PNG files.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.decalOpen.setStatusTip(QCoreApplication.translate("MainWindow", u"Open the directory containing LEGO decal files.", None))
#endif // QT_CONFIG(statustip)
        self.decalOpen.setText("")
        self.switchLabel.setText(QCoreApplication.translate("MainWindow", u"Shader Switch:", None))
#if QT_CONFIG(tooltip)
        self.switchInput.setToolTip(QCoreApplication.translate("MainWindow", u"Name of the shader switch.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.switchInput.setStatusTip(QCoreApplication.translate("MainWindow", u"Name of the shader switch.", None))
#endif // QT_CONFIG(statustip)
        self.switchInput.setPlaceholderText(QCoreApplication.translate("MainWindow", u"DECAL_COL_SWITCH_00_09", None))
#if QT_CONFIG(tooltip)
        self.shaderSwitchValid.setToolTip(QCoreApplication.translate("MainWindow", u"Matching shader switch found in the scene.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.shaderSwitchValid.setStatusTip(QCoreApplication.translate("MainWindow", u"Matching shader switch found in the scene.", None))
#endif // QT_CONFIG(statustip)
        self.shaderSwitchValid.setText("")
#if QT_CONFIG(tooltip)
        self.shaderSwitchInvalid.setToolTip(QCoreApplication.translate("MainWindow", u"Matching shader switch not found in the scene.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.shaderSwitchInvalid.setStatusTip(QCoreApplication.translate("MainWindow", u"Matching shader switch not found in the scene.", None))
#endif // QT_CONFIG(statustip)
        self.shaderSwitchInvalid.setText("")
#if QT_CONFIG(tooltip)
        self.maskSwitchValid.setToolTip(QCoreApplication.translate("MainWindow", u"Matching mask switch found in the scene.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.maskSwitchValid.setStatusTip(QCoreApplication.translate("MainWindow", u"Matching mask switch found in the scene.", None))
#endif // QT_CONFIG(statustip)
        self.maskSwitchValid.setText("")
#if QT_CONFIG(tooltip)
        self.maskSwitchInvalid.setToolTip(QCoreApplication.translate("MainWindow", u"Matching mask switch not found in the scene.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.maskSwitchInvalid.setStatusTip(QCoreApplication.translate("MainWindow", u"Matching mask switch not found in the scene.", None))
#endif // QT_CONFIG(statustip)
        self.maskSwitchInvalid.setText("")
#if QT_CONFIG(tooltip)
        self.runImport.setToolTip(QCoreApplication.translate("MainWindow", u"Run the imports and updates.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.runImport.setStatusTip(QCoreApplication.translate("MainWindow", u"Run the imports and updates.", None))
#endif // QT_CONFIG(statustip)
        self.runImport.setText(QCoreApplication.translate("MainWindow", u"Import/Update", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
    # retranslateUi
