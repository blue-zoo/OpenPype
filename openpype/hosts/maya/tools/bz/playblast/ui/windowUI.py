# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'windowUI.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from openpype.hosts.maya.tools.bz.playblast.ui.viewportWindow import ViewportWidget


class Ui_PlayblasterWidget(object):
    def setupUi(self, PlayblasterWidget):
        if not PlayblasterWidget.objectName():
            PlayblasterWidget.setObjectName(u"PlayblasterWidget")
        PlayblasterWidget.resize(1330, 732)
        self.gridLayout = QGridLayout(PlayblasterWidget)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(PlayblasterWidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.gridLayout_3 = QGridLayout(self.frame)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.groupBox_2 = QGroupBox(self.frame)
        self.groupBox_2.setObjectName(u"groupBox_2")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.gridLayout_4 = QGridLayout(self.groupBox_2)
        self.gridLayout_4.setSpacing(4)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(4, 4, 4, 4)
        self.groupBox_3 = QGroupBox(self.groupBox_2)
        self.groupBox_3.setObjectName(u"groupBox_3")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.gridLayout_5 = QGridLayout(self.groupBox_3)
        self.gridLayout_5.setSpacing(4)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(4, 4, 4, 4)
        self.label_2 = QLabel(self.groupBox_3)
        self.label_2.setObjectName(u"label_2")
        font1 = QFont()
        font1.setPointSize(7)
        font1.setBold(False)
        font1.setWeight(50)
        self.label_2.setFont(font1)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.gridLayout_5.addWidget(self.label_2, 0, 3, 1, 1)

        self.playblastEndLineEdit = QLineEdit(self.groupBox_3)
        self.playblastEndLineEdit.setObjectName(u"playblastEndLineEdit")
        font2 = QFont()
        font2.setPointSize(7)
        font2.setBold(True)
        font2.setWeight(75)
        self.playblastEndLineEdit.setFont(font2)
        self.playblastEndLineEdit.setReadOnly(True)

        self.gridLayout_5.addWidget(self.playblastEndLineEdit, 0, 4, 1, 1)

        self.playblastStartLineEdit = QLineEdit(self.groupBox_3)
        self.playblastStartLineEdit.setObjectName(u"playblastStartLineEdit")
        self.playblastStartLineEdit.setFont(font2)
        self.playblastStartLineEdit.setReadOnly(True)

        self.gridLayout_5.addWidget(self.playblastStartLineEdit, 0, 2, 1, 1)

        self.label = QLabel(self.groupBox_3)
        self.label.setObjectName(u"label")
        self.label.setFont(font1)
        self.label.setAlignment(Qt.AlignCenter)

        self.gridLayout_5.addWidget(self.label, 0, 1, 1, 1)

        self.updateTimesFromAyonButton = QPushButton(self.groupBox_3)
        self.updateTimesFromAyonButton.setObjectName(u"updateTimesFromAyonButton")
        font3 = QFont()
        font3.setPointSize(9)
        font3.setBold(False)
        font3.setWeight(50)
        self.updateTimesFromAyonButton.setFont(font3)

        self.gridLayout_5.addWidget(self.updateTimesFromAyonButton, 2, 1, 1, 2)

        self.updateTimesFromMayaButton = QPushButton(self.groupBox_3)
        self.updateTimesFromMayaButton.setObjectName(u"updateTimesFromMayaButton")
        self.updateTimesFromMayaButton.setFont(font3)

        self.gridLayout_5.addWidget(self.updateTimesFromMayaButton, 2, 3, 1, 2)


        self.gridLayout_4.addWidget(self.groupBox_3, 6, 0, 1, 1)

        self.groupBox_7 = QGroupBox(self.groupBox_2)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.groupBox_7.setFont(font)
        self.gridLayout_8 = QGridLayout(self.groupBox_7)
        self.gridLayout_8.setSpacing(4)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(4, 4, 4, 4)
        self.label_8 = QLabel(self.groupBox_7)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setFont(font1)

        self.gridLayout_8.addWidget(self.label_8, 1, 0, 1, 1)

        self.commentBurnInLineEdit = QLineEdit(self.groupBox_7)
        self.commentBurnInLineEdit.setObjectName(u"commentBurnInLineEdit")
        self.commentBurnInLineEdit.setMaxLength(40)

        self.gridLayout_8.addWidget(self.commentBurnInLineEdit, 1, 1, 1, 1)

        self.setCommentToSceneButton = QPushButton(self.groupBox_7)
        self.setCommentToSceneButton.setObjectName(u"setCommentToSceneButton")
        self.setCommentToSceneButton.setFont(font1)

        self.gridLayout_8.addWidget(self.setCommentToSceneButton, 1, 2, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_7, 2, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_4.addItem(self.verticalSpacer, 0, 0, 1, 1)

        self.groupBox_6 = QGroupBox(self.groupBox_2)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setFont(font)
        self.gridLayout_7 = QGridLayout(self.groupBox_6)
        self.gridLayout_7.setSpacing(4)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.gridLayout_7.setContentsMargins(4, 4, 4, 4)
        self.cameraLineEdit = QLineEdit(self.groupBox_6)
        self.cameraLineEdit.setObjectName(u"cameraLineEdit")
        self.cameraLineEdit.setReadOnly(True)

        self.gridLayout_7.addWidget(self.cameraLineEdit, 0, 1, 1, 1)

        self.label_7 = QLabel(self.groupBox_6)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font1)

        self.gridLayout_7.addWidget(self.label_7, 0, 0, 2, 1)

        self.setCameraButton = QPushButton(self.groupBox_6)
        self.setCameraButton.setObjectName(u"setCameraButton")
        self.setCameraButton.setFont(font1)

        self.gridLayout_7.addWidget(self.setCameraButton, 0, 2, 1, 1)


        self.gridLayout_4.addWidget(self.groupBox_6, 3, 0, 1, 1)

        self.groupBox_5 = QGroupBox(self.groupBox_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.groupBox_5.setFont(font)
        self.groupBox_5.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.gridLayout_6 = QGridLayout(self.groupBox_5)
        self.gridLayout_6.setSpacing(4)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.gridLayout_6.setContentsMargins(4, 4, 4, 4)
        self.ayonEndLineEdit = QLineEdit(self.groupBox_5)
        self.ayonEndLineEdit.setObjectName(u"ayonEndLineEdit")
        self.ayonEndLineEdit.setMaximumSize(QSize(80, 16777215))
        self.ayonEndLineEdit.setFont(font)
        self.ayonEndLineEdit.setReadOnly(True)

        self.gridLayout_6.addWidget(self.ayonEndLineEdit, 2, 5, 1, 1)

        self.label_5 = QLabel(self.groupBox_5)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font1)
        self.label_5.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_6.addWidget(self.label_5, 0, 0, 1, 1)

        self.label_3 = QLabel(self.groupBox_5)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setFont(font1)
        self.label_3.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_6.addWidget(self.label_3, 2, 0, 1, 1)

        self.ayonStartLineEdit = QLineEdit(self.groupBox_5)
        self.ayonStartLineEdit.setObjectName(u"ayonStartLineEdit")
        self.ayonStartLineEdit.setMaximumSize(QSize(80, 16777215))
        self.ayonStartLineEdit.setFont(font)
        self.ayonStartLineEdit.setReadOnly(True)

        self.gridLayout_6.addWidget(self.ayonStartLineEdit, 2, 3, 1, 1)

        self.ayonShotNameLineEdit = QLineEdit(self.groupBox_5)
        self.ayonShotNameLineEdit.setObjectName(u"ayonShotNameLineEdit")
        self.ayonShotNameLineEdit.setFont(font)
        self.ayonShotNameLineEdit.setReadOnly(True)

        self.gridLayout_6.addWidget(self.ayonShotNameLineEdit, 0, 3, 1, 3)

        self.label_4 = QLabel(self.groupBox_5)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font1)
        self.label_4.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_6.addWidget(self.label_4, 2, 4, 1, 1)

        self.ayonResolutionWidthLineEdit = QLineEdit(self.groupBox_5)
        self.ayonResolutionWidthLineEdit.setObjectName(u"ayonResolutionWidthLineEdit")
        self.ayonResolutionWidthLineEdit.setMaximumSize(QSize(80, 16777215))
        self.ayonResolutionWidthLineEdit.setFont(font)
        self.ayonResolutionWidthLineEdit.setReadOnly(True)

        self.gridLayout_6.addWidget(self.ayonResolutionWidthLineEdit, 1, 4, 1, 1)

        self.ayonResolutionHeightLineEdit = QLineEdit(self.groupBox_5)
        self.ayonResolutionHeightLineEdit.setObjectName(u"ayonResolutionHeightLineEdit")
        self.ayonResolutionHeightLineEdit.setMaximumSize(QSize(80, 16777215))
        self.ayonResolutionHeightLineEdit.setFont(font)
        self.ayonResolutionHeightLineEdit.setReadOnly(True)

        self.gridLayout_6.addWidget(self.ayonResolutionHeightLineEdit, 1, 5, 1, 1)

        self.label_6 = QLabel(self.groupBox_5)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font1)
        self.label_6.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout_6.addWidget(self.label_6, 1, 0, 1, 2)


        self.gridLayout_4.addWidget(self.groupBox_5, 4, 0, 1, 1)

        self.groupBox_4 = QGroupBox(self.groupBox_2)
        self.groupBox_4.setObjectName(u"groupBox_4")

        self.gridLayout_4.addWidget(self.groupBox_4, 5, 0, 1, 1)

        self.groupBox_8 = QGroupBox(self.groupBox_2)
        self.groupBox_8.setObjectName(u"groupBox_8")
        self.groupBox_8.setFont(font)
        self.gridLayout_9 = QGridLayout(self.groupBox_8)
        self.gridLayout_9.setSpacing(4)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.gridLayout_9.setContentsMargins(4, 4, 4, 4)
        self.playblastVideoFolderLineEdit = QLineEdit(self.groupBox_8)
        self.playblastVideoFolderLineEdit.setObjectName(u"playblastVideoFolderLineEdit")
        self.playblastVideoFolderLineEdit.setFont(font1)
        self.playblastVideoFolderLineEdit.setReadOnly(True)

        self.gridLayout_9.addWidget(self.playblastVideoFolderLineEdit, 0, 1, 1, 1)

        self.setPlayblastVideoFolderButton = QPushButton(self.groupBox_8)
        self.setPlayblastVideoFolderButton.setObjectName(u"setPlayblastVideoFolderButton")
        self.setPlayblastVideoFolderButton.setFont(font1)

        self.gridLayout_9.addWidget(self.setPlayblastVideoFolderButton, 0, 2, 1, 1)

        self.label_9 = QLabel(self.groupBox_8)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font1)

        self.gridLayout_9.addWidget(self.label_9, 0, 0, 1, 1)

        self.label_10 = QLabel(self.groupBox_8)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setFont(font1)

        self.gridLayout_9.addWidget(self.label_10, 1, 0, 1, 1)

        self.videoFileNameLineEdit = QLineEdit(self.groupBox_8)
        self.videoFileNameLineEdit.setObjectName(u"videoFileNameLineEdit")
        self.videoFileNameLineEdit.setFont(font1)

        self.gridLayout_9.addWidget(self.videoFileNameLineEdit, 1, 1, 1, 2)


        self.gridLayout_4.addWidget(self.groupBox_8, 1, 0, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox_2, 0, 1, 1, 1)

        self.groupBox = QGroupBox(self.frame)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setSpacing(4)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(4, 4, 4, 4)
        self.viewport = ViewportWidget(self.groupBox)
        self.viewport.setObjectName(u"viewport")
        sizePolicy1 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.viewport.sizePolicy().hasHeightForWidth())
        self.viewport.setSizePolicy(sizePolicy1)
        self.viewport.setMinimumSize(QSize(200, 200))

        self.gridLayout_2.addWidget(self.viewport, 1, 0, 1, 1)


        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 1)

        self.progressBar = QProgressBar(self.frame)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(0)

        self.gridLayout_3.addWidget(self.progressBar, 1, 0, 1, 1)

        self.playblastButton = QPushButton(self.frame)
        self.playblastButton.setObjectName(u"playblastButton")
        self.playblastButton.setMinimumSize(QSize(0, 68))
        palette = QPalette()
        brush = QBrush(QColor(240, 0, 0, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Button, brush)
        brush1 = QBrush(QColor(255, 255, 127, 255))
        brush1.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Light, brush1)
        brush2 = QBrush(QColor(170, 85, 127, 255))
        brush2.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Midlight, brush2)
        brush3 = QBrush(QColor(170, 170, 127, 255))
        brush3.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Dark, brush3)
        brush4 = QBrush(QColor(85, 170, 127, 255))
        brush4.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Text, brush4)
        brush5 = QBrush(QColor(255, 0, 127, 255))
        brush5.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.BrightText, brush5)
        palette.setBrush(QPalette.Active, QPalette.Base, brush5)
        brush6 = QBrush(QColor(85, 170, 0, 255))
        brush6.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Window, brush6)
        brush7 = QBrush(QColor(0, 170, 255, 255))
        brush7.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.Shadow, brush7)
        brush8 = QBrush(QColor(85, 85, 255, 255))
        brush8.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.HighlightedText, brush8)
        brush9 = QBrush(QColor(85, 0, 0, 255))
        brush9.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.AlternateBase, brush9)
        brush10 = QBrush(QColor(190, 191, 255, 255))
        brush10.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.ToolTipBase, brush10)
        palette.setBrush(QPalette.Active, QPalette.ToolTipText, brush4)
        brush11 = QBrush(QColor(85, 85, 0, 128))
        brush11.setStyle(Qt.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush11)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.Button, brush)
        palette.setBrush(QPalette.Inactive, QPalette.Light, brush1)
        palette.setBrush(QPalette.Inactive, QPalette.Midlight, brush2)
        brush12 = QBrush(QColor(160, 160, 160, 255))
        brush12.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Inactive, QPalette.Dark, brush12)
        palette.setBrush(QPalette.Inactive, QPalette.Text, brush4)
        palette.setBrush(QPalette.Inactive, QPalette.BrightText, brush5)
        brush13 = QBrush(QColor(85, 255, 0, 255))
        brush13.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Inactive, QPalette.Base, brush13)
        palette.setBrush(QPalette.Inactive, QPalette.Window, brush6)
        palette.setBrush(QPalette.Inactive, QPalette.Shadow, brush7)
        palette.setBrush(QPalette.Inactive, QPalette.HighlightedText, brush4)
        palette.setBrush(QPalette.Inactive, QPalette.AlternateBase, brush9)
        palette.setBrush(QPalette.Inactive, QPalette.ToolTipBase, brush10)
        palette.setBrush(QPalette.Inactive, QPalette.ToolTipText, brush4)
        brush14 = QBrush(QColor(37, 50, 170, 128))
        brush14.setStyle(Qt.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush14)
#endif
        palette.setBrush(QPalette.Disabled, QPalette.Button, brush)
        palette.setBrush(QPalette.Disabled, QPalette.Light, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Midlight, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.Dark, brush12)
        brush15 = QBrush(QColor(85, 85, 0, 255))
        brush15.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush15)
        palette.setBrush(QPalette.Disabled, QPalette.BrightText, brush5)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush6)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush6)
        palette.setBrush(QPalette.Disabled, QPalette.Shadow, brush7)
        palette.setBrush(QPalette.Disabled, QPalette.HighlightedText, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.AlternateBase, brush9)
        palette.setBrush(QPalette.Disabled, QPalette.ToolTipBase, brush10)
        palette.setBrush(QPalette.Disabled, QPalette.ToolTipText, brush4)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush14)
#endif
        self.playblastButton.setPalette(palette)
        font4 = QFont()
        font4.setPointSize(14)
        font4.setBold(True)
        font4.setWeight(75)
        self.playblastButton.setFont(font4)

        self.gridLayout_3.addWidget(self.playblastButton, 1, 1, 1, 1)


        self.gridLayout.addWidget(self.frame, 0, 1, 1, 1)


        self.retranslateUi(PlayblasterWidget)
        self.updateTimesFromAyonButton.clicked.connect(PlayblasterWidget.updateTimesFromAyon)
        self.updateTimesFromMayaButton.clicked.connect(PlayblasterWidget.updateTimesFromMaya)
        self.playblastButton.clicked.connect(PlayblasterWidget.runPlayblast)
        self.setCameraButton.clicked.connect(PlayblasterWidget.setPlayblastCamera)
        self.setCommentToSceneButton.clicked.connect(PlayblasterWidget.setCommentToSceneName)
        self.setPlayblastVideoFolderButton.clicked.connect(PlayblasterWidget.setPlayblastFolder)

        QMetaObject.connectSlotsByName(PlayblasterWidget)
    # setupUi

    def retranslateUi(self, PlayblasterWidget):
        PlayblasterWidget.setWindowTitle(QCoreApplication.translate("PlayblasterWidget", u"Playblaster", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("PlayblasterWidget", u"GroupBox", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("PlayblasterWidget", u"Frame Range ", None))
        self.label_2.setText(QCoreApplication.translate("PlayblasterWidget", u"Playblast\n"
"End Frame", None))
        self.label.setText(QCoreApplication.translate("PlayblasterWidget", u"Playblast\n"
"Start Frame", None))
        self.updateTimesFromAyonButton.setText(QCoreApplication.translate("PlayblasterWidget", u"Update Times From \n"
"Ayon", None))
        self.updateTimesFromMayaButton.setText(QCoreApplication.translate("PlayblasterWidget", u"Update Times From \n"
"Maya Timeline", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("PlayblasterWidget", u"Comment ", None))
        self.label_8.setText(QCoreApplication.translate("PlayblasterWidget", u"Burn in \n"
"Comment", None))
        self.setCommentToSceneButton.setText(QCoreApplication.translate("PlayblasterWidget", u"Set \n"
"To Scene", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("PlayblasterWidget", u"Camera", None))
        self.label_7.setText(QCoreApplication.translate("PlayblasterWidget", u"Renderable\n"
" Camera", None))
        self.setCameraButton.setText(QCoreApplication.translate("PlayblasterWidget", u"Set Camera\n"
" From Selection", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("PlayblasterWidget", u"Ayon Shot Details", None))
        self.label_5.setText(QCoreApplication.translate("PlayblasterWidget", u"Ayon\n"
"Shot Name", None))
        self.label_3.setText(QCoreApplication.translate("PlayblasterWidget", u"Ayon\n"
"Start Frame", None))
        self.label_4.setText(QCoreApplication.translate("PlayblasterWidget", u"Ayon\n"
"End Frame", None))
        self.label_6.setText(QCoreApplication.translate("PlayblasterWidget", u"Ayon \n"
"Resolution", None))
        self.groupBox_4.setTitle("")
        self.groupBox_8.setTitle(QCoreApplication.translate("PlayblasterWidget", u"File Name", None))
        self.setPlayblastVideoFolderButton.setText(QCoreApplication.translate("PlayblasterWidget", u"Set Folder", None))
        self.label_9.setText(QCoreApplication.translate("PlayblasterWidget", u"Save Folder", None))
        self.label_10.setText(QCoreApplication.translate("PlayblasterWidget", u"Video Name", None))
        self.groupBox.setTitle("")
        self.playblastButton.setText(QCoreApplication.translate("PlayblasterWidget", u"PlayBlast", None))
    # retranslateUi
