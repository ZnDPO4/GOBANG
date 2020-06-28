# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_GobangClientWindow.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Gobang_Mainwindow(object):
    def setupUi(self, Gobang_Mainwindow):
        Gobang_Mainwindow.setObjectName("Gobang_Mainwindow")
        Gobang_Mainwindow.resize(520, 570)
        Gobang_Mainwindow.setMinimumSize(QtCore.QSize(320, 370))
        Gobang_Mainwindow.setMaximumSize(QtCore.QSize(667, 720))
        self.centralwidget = QtWidgets.QWidget(Gobang_Mainwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.chess_board = ChessBoard(self.centralwidget)
        self.chess_board.setMinimumSize(QtCore.QSize(300, 300))
        self.chess_board.setFrameShape(QtWidgets.QFrame.Box)
        self.chess_board.setFrameShadow(QtWidgets.QFrame.Plain)
        self.chess_board.setLineWidth(2)
        self.chess_board.setObjectName("chess_board")
        self.horizontalLayout.addWidget(self.chess_board)
        Gobang_Mainwindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Gobang_Mainwindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 520, 26))
        self.menubar.setObjectName("menubar")
        self.menu_local = QtWidgets.QMenu(self.menubar)
        self.menu_local.setObjectName("menu_local")
        self.menu_socket = QtWidgets.QMenu(self.menubar)
        self.menu_socket.setObjectName("menu_socket")
        Gobang_Mainwindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Gobang_Mainwindow)
        self.statusbar.setObjectName("statusbar")
        Gobang_Mainwindow.setStatusBar(self.statusbar)
        self.single_player = QtWidgets.QAction(Gobang_Mainwindow)
        self.single_player.setObjectName("single_player")
        self.two_player = QtWidgets.QAction(Gobang_Mainwindow)
        self.two_player.setObjectName("two_player")
        self.menu_local.addAction(self.single_player)
        self.menu_local.addAction(self.two_player)
        self.menubar.addAction(self.menu_local.menuAction())
        self.menubar.addAction(self.menu_socket.menuAction())

        self.retranslateUi(Gobang_Mainwindow)
        QtCore.QMetaObject.connectSlotsByName(Gobang_Mainwindow)

    def retranslateUi(self, Gobang_Mainwindow):
        _translate = QtCore.QCoreApplication.translate
        Gobang_Mainwindow.setWindowTitle(_translate("Gobang_Mainwindow", "五子棋-客户端"))
        self.menu_local.setTitle(_translate("Gobang_Mainwindow", "单机"))
        self.menu_socket.setTitle(_translate("Gobang_Mainwindow", "联机"))
        self.single_player.setText(_translate("Gobang_Mainwindow", "单人"))
        self.two_player.setText(_translate("Gobang_Mainwindow", "双人"))
from Gobang_chessboard import ChessBoard

