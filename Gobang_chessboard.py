# -*- coding: utf-8 -*-

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from Gobang_ import *


class ChessBoard(QFrame):
    WIDTH = 100
    MARGIN = WIDTH // 2
    BOARD_WIDTH = WIDTH * 14 + MARGIN * 2
    CHESS_RADIUS = 43
    STARS = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]

    PEN_THIN = QPen(QColor("#333333"), 1, Qt.SolidLine)
    PEN_LINE = QPen(QColor("#666666"), 3, Qt.SolidLine)
    PEN_FRAME = QPen(QColor("#000000"), 8, Qt.SolidLine)
    PEN_STAR = QPen(QColor("#444444"), 20, Qt.SolidLine)
    PEN_HINT = QPen(QColor("#ee0000"), 25, Qt.SolidLine)
    BRUSH_BG = QBrush(QColor("#ffffff"), Qt.SolidPattern)
    BRUSH_1 = QBrush(QColor("#000000"), Qt.SolidPattern)
    BRUSH_2 = QBrush(QColor("#ffffff"), Qt.SolidPattern)

    sig_click = pyqtSignal(int, int)  # 点击棋盘信号  (x, y)
    sig_chess_down = pyqtSignal(int, int)  # 落子信号  (x, y)

    def __init__(self, parent):
        super().__init__(parent)
        self.field = None
        self.previous_chess = None
        self.sig_chess_down.connect(self.chess_down)

    def clear(self):
        self.previous_chess = None
        self.repaint()

    def chess_down(self, x, y):
        self.previous_chess = (x, y)
        self.repaint()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QPainter()
        painter.begin(self)
        painter.setWindow(0, 0, 1500, 1500)
        # painter.setViewport(0,0,600,600)
        self.draw_chess_board(painter)
        self.draw_chess(painter)
        painter.end()

    def draw_chess_board(self, painter):
        """绘制棋盘"""
        WIDTH = self.WIDTH
        MARGIN = self.MARGIN
        BOARD_WIDTH = self.BOARD_WIDTH
        # 画棋盘
        painter.setPen(self.PEN_FRAME)
        painter.setBrush(self.BRUSH_BG)
        painter.drawRect(MARGIN, MARGIN, BOARD_WIDTH - MARGIN * 2, BOARD_WIDTH - MARGIN * 2)
        # 画纵横线
        for line in range(15):
            painter.setPen(self.PEN_LINE)
            painter.drawLine(MARGIN, MARGIN + WIDTH * line, BOARD_WIDTH - MARGIN, MARGIN + WIDTH * line)
            painter.drawLine(MARGIN + WIDTH * line, MARGIN, MARGIN + WIDTH * line, BOARD_WIDTH - MARGIN)
        # 画星
        painter.setPen(self.PEN_STAR)
        for star in self.STARS:
            painter.drawPoint(MARGIN + star[0] * WIDTH, MARGIN + star[1] * WIDTH)

    def draw_chess(self, painter):
        """绘制所有棋子"""
        WIDTH = self.WIDTH
        MARGIN = self.MARGIN
        RADIUS = self.CHESS_RADIUS
        painter.setPen(self.PEN_THIN)
        for x in range(15):
            for y in range(15):
                if self.field.get_point(x, y) == ChessColor.black.value:
                    painter.setBrush(self.BRUSH_1)
                elif self.field.get_point(x, y) == ChessColor.white.value:
                    painter.setBrush(self.BRUSH_2)
                else:
                    continue
                painter.drawEllipse(MARGIN + x * WIDTH - RADIUS, MARGIN + y * WIDTH - RADIUS, RADIUS * 2, RADIUS * 2)
        # 画当前落子的标记
        if self.previous_chess:
            painter.setPen(self.PEN_HINT)
            painter.drawPoint(MARGIN + self.previous_chess[0] * WIDTH, MARGIN + self.previous_chess[1] * WIDTH)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        # 左键落子
        if event.button() == Qt.LeftButton:
            print("press", event.x(), event.y())
            self.sig_click.emit(event.x(), event.y())

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """保持等比缩放"""
        old_size = self.size()
        if old_size.width() > old_size.height():
            new_x = new_y = old_size.height()
        else:
            new_x = new_y = old_size.width()
        self.resize(new_x, new_y)

