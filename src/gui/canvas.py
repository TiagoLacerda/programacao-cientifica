from PyQt5 import QtGui
from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPainterPath
from PyQt5.QtWidgets import QOpenGLWidget, qApp
from OpenGL.GL import *

from multipledispatch import *
import json
import math
import os

from hetool.hetool import HeController, HeModel, HeView, Tesselation, Point
from utility import normalized, collision
from gui.inputdialog import InputDialog

# https://doc.qt.io/qt-5/qopenglwidget.html
# https://doc.qt.io/qt-5/coordsys.html


class Canvas(QOpenGLWidget):
    cursorSignal = pyqtSignal(QPointF, QPointF)

    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.keyStates = {'lmb': False, 'mmb': False, 'rmb': False, 'ctrl': False, 'shift': False}

        self.rawCursorV = QPointF(0.0, 0.0)  # Cursor position in viewport coordinates before any processing
        self.rawCursorU = QPointF(0.0, 0.0)  # Cursor position in universe coordinates before any processing

        self.cursorV = QPointF(0.0, 0.0)  # Cursor position in viewport coordinates after processing (snap, align, ...)
        self.cursorU = QPointF(0.0, 0.0)  # Cursor position in universe coordinates after processing (snap, align, ...)

        self.lmbDown = QPointF(0.0, 0.0)  # Universe coordinates of last LMB press
        self.mmbDown = QPointF(0.0, 0.0)  # Viewport coordinates of last MMB press
        self.rmbDown = QPointF(0.0, 0.0)  # Universe coordinates of last RMB press

        self.center = QPointF(0.0, 0.0)  # Universe coordinates at center of viewport
        self.factor = 100 / min(self.width(), self.height())  # Universe to Viewport units ratio

        self.interval = 1.0  # Canvas grid interval

        self.debug = False

        self.heM = HeModel()
        self.heV = HeView(self.heM)
        self.heC = HeController(self.heM)

        self.tol = 10e-6
        self.snapTol = 10  # Viewport units

        self.data = {}
        self.selection = []

    # ----- UNIVERSE-VIEWPORT CONVERSIONS -----

    @dispatch(QPoint)
    def universeToViewport(self, u):
        return self.universeToViewport(u.x(), u.y())

    @dispatch(QPointF)
    def universeToViewport(self, u):
        return self.universeToViewport(u.x(), u.y())

    @dispatch(int, int)
    def universeToViewport(self, ux, uy):
        return self.universeToViewport(float(ux), float(uy))

    @dispatch(float, int)
    def universeToViewport(self, ux, uy):
        return self.universeToViewport(ux, float(uy))

    @dispatch(int, float)
    def universeToViewport(self, ux, uy):
        return self.universeToViewport(float(ux), uy)

    @dispatch(float, float)
    def universeToViewport(self, ux, uy):
        w = self.width()
        h = self.height()

        vx = (ux - self.center.x()) / self.factor + w / 2
        vy = -(uy - self.center.y()) / self.factor + h / 2
        return QPointF(vx, vy)

    @dispatch(QPoint)
    def viewportToUniverse(self, v):
        return self.viewportToUniverse(v.x(), v.y())

    @dispatch(QPointF)
    def viewportToUniverse(self, v):
        return self.viewportToUniverse(v.x(), v.y())

    @dispatch(int, int)
    def viewportToUniverse(self, vx, vy):
        return self.viewportToUniverse(float(vx), float(vy))

    @dispatch(float, int)
    def viewportToUniverse(self, vx, vy):
        return self.viewportToUniverse(vx, float(vy))

    @dispatch(int, float)
    def viewportToUniverse(self, vx, vy):
        return self.viewportToUniverse(float(vx), vy)

    @dispatch(float, float)
    def viewportToUniverse(self, vx, vy):
        w = self.width()
        h = self.height()

        ux = self.center.x() + (vx - w / 2) * self.factor
        uy = self.center.y() - (vy - h / 2) * self.factor
        return QPointF(ux, uy)

    # ----------

    def initializeGL(self):
        glClearColor(0.058, 0.058, 0.058, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.updateInterval()

    # Chooses appropriate interval for gridlines

    def updateInterval(self):
        utl = self.viewportToUniverse(0, 0)
        ubr = self.viewportToUniverse(self.width(), self.height())

        uw = ubr.x() - utl.x()
        uh = ubr.y() - utl.y()

        mantissa, exponent = normalized(uw)
        i = 2.0 if int(mantissa) <= 4.0 else 5.0
        xi = i * 10.0 ** (exponent - 1)

        mantissa, exponent = normalized(uh)
        i = 2.0 if int(mantissa) <= 4.0 else 5.0
        yi = i * 10.0 ** (exponent - 1)

        self.interval = max(xi, yi)

    def paintGL(self):
        self.updateInterval()

        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont('Consolas', 12))

        # Gridlines

        painter.setPen(QPen(QColor('#2f2f2f'), 1))
        painter.setBrush(QBrush())

        tl = self.viewportToUniverse(0, 0)
        br = self.viewportToUniverse(self.width(), self.height())

        i = int(tl.y() / self.interval) * self.interval
        while i >= br.y():
            v = self.universeToViewport(0, i)
            painter.drawLine(0, v.y(), self.width(), v.y())
            i -= self.interval

        j = int(tl.x() / self.interval) * self.interval
        while j <= br.x():
            v = self.universeToViewport(j, 0)
            painter.drawLine(v.x(), 0, v.x(), self.height())
            j += self.interval

        painter.setPen(QPen(QColor('#2f2f2f'), 4))
        painter.setBrush(QBrush())

        origin = self.universeToViewport(0.0, 0.0)
        painter.drawLine(0, origin.y(), self.width(), origin.y())
        painter.drawLine(origin.x(), 0, origin.x(), self.height())

        # He Tools Data

        if not self.heV.isEmpty():
            painter.setPen(QPen(QColor('#286ed2'), 1))
            painter.setBrush(QBrush(QColor('#286ed2')))

            patches = self.heV.getPatches()
            for patch in patches:
                triangles = Tesselation.tessellate(patch.getPoints())
                for triangle in triangles:
                    a = self.universeToViewport(triangle[0].getX(), triangle[0].getY())
                    b = self.universeToViewport(triangle[1].getX(), triangle[1].getY())
                    c = self.universeToViewport(triangle[2].getX(), triangle[2].getY())
                    path = QPainterPath()
                    path.moveTo(a.x(), a.y())
                    path.lineTo(b.x(), b.y())
                    path.lineTo(c.x(), c.y())
                    painter.drawPath(path)

            painter.setPen(QPen(QColor('#d72337'), 3))
            painter.setBrush(QBrush(QColor('#d72337')))

            segments = self.heV.getSegments()
            for curve in segments:
                points = curve.getPointsToDraw()
                a = self.universeToViewport(points[0].getX(), points[0].getY())
                b = self.universeToViewport(points[1].getX(), points[1].getY())
                painter.drawLine(a.x(), a.y(), b.x(), b.y())

            vertices = self.heV.getPoints()
            for vertex in vertices:
                a = self.universeToViewport(vertex.getX(), vertex.getY())
                painter.drawEllipse(a.x() - 4, a.y() - 4, 8, 8)

        # Regular Mesh of Particles

        if self.data:
            if self.debug:
                tl = self.universeToViewport(self.data['minx'] - self.data['dx'] / 2.0, self.data['maxy'] + self.data['dy'] / 2.0)
                br = self.universeToViewport(self.data['maxx'] + self.data['dx'] / 2.0, self.data['miny'] - self.data['dy'] / 2.0)

                painter.setPen(QPen(QColor('#ffffff'), 1, Qt.DashLine))
                painter.setBrush(QBrush())
                painter.drawRect(QRectF(tl, br))

            dx = self.data['dx'] / self.factor
            dy = self.data['dy'] / self.factor
            mint = self.data['mint']
            maxt = self.data['maxt']

            for index in range(self.data['n']):
                x = self.data['x'][index]
                y = self.data['y'][index]
                t = self.data['t'][index]
                v = self.universeToViewport(x, y)
                
                if not t or maxt == mint:
                    color = QColor('#ffffff')
                else:
                    scale = (t - mint) / (maxt - mint)
                    r = int((1 - scale) *   0) + int(scale * 255)
                    g = int((1 - scale) *   0) + int(scale *   0)
                    b = int((1 - scale) * 255) + int(scale *   0)
                    color = QColor.fromRgb(r, g, b)

                painter.setPen(QPen(color, 1))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(v.x() - dx / 2.0, v.y() - dy / 2.0, dx, dy)

                if index in self.selection:                    
                    painter.setPen(QPen(QColor('#ffffff'), 2))
                    painter.setBrush(QBrush(QColor('#5582af69')))
                    painter.drawEllipse(v.x() - dx / 2.0, v.y() - dy / 2.0, dx, dy)

        # Area selection

        if self.keyStates['rmb']:
            a = self.universeToViewport(self.rmbDown)
            b = self.universeToViewport(self.cursorU)

            painter.setPen(QPen(QColor('#ffffff'), 1, Qt.DashLine))
            painter.setBrush(QBrush(QColor('#55286ed2')))
            painter.drawRect(QRectF(a, b).normalized())

        # New Segment Creation

        painter.setPen(QPen(QColor('#82af69'), 3))
        painter.setBrush(QBrush(QColor('#82af69')))
        b = self.cursorV

        if self.keyStates['lmb']:
            a = self.universeToViewport(self.lmbDown)
            painter.drawEllipse(a.x() - 4, a.y() - 4, 8, 8)
            painter.drawLine(a.x(), a.y(), b.x(), b.y())

        if not self.keyStates['rmb']:
            painter.drawEllipse(b.x() - 4, b.y() - 4, 8, 8)

        # Debug

        if not self.debug:
            return

        text = '''
        center  = ({},{})\n
        cursorU = ({},{})\n
        cursorV = ({},{})\n
        lmbDown = ({},{})\n
        mmbDown = ({},{})\n
        rmbDown = ({},{})\n
        interval   = {}\n
        lmb     = {}\n
        mmb     = {}\n
        rmb     = {}\n
        ctrl    = {}\n
        shift   = {}\n
        '''.format(
            '{:.2f}'.format(self.center.x()).rjust(8),
            '{:.2f}'.format(self.center.y()).rjust(8),
            '{:.2f}'.format(self.cursorU.x()).rjust(8),
            '{:.2f}'.format(self.cursorU.y()).rjust(8),
            '{:.2f}'.format(self.cursorV.x()).rjust(8),
            '{:.2f}'.format(self.cursorV.y()).rjust(8),
            '{:.2f}'.format(self.lmbDown.x()).rjust(8),
            '{:.2f}'.format(self.lmbDown.y()).rjust(8),
            '{:.2f}'.format(self.mmbDown.x()).rjust(8),
            '{:.2f}'.format(self.mmbDown.y()).rjust(8),
            '{:.2f}'.format(self.rmbDown.x()).rjust(8),
            '{:.2f}'.format(self.rmbDown.y()).rjust(8),
            self.interval,
            self.keyStates['lmb'],
            self.keyStates['mmb'],
            self.keyStates['rmb'],
            self.keyStates['ctrl'],
            self.keyStates['shift']
        )

        painter.setPen(QPen(QColor('#ffffff'), 1))
        painter.drawText(QRectF(0, 0, self.width(), self.height()), text)

    # ----- Input Processing -----

    def resetCursor(self):
        self.cursorV = self.rawCursorV
        self.cursorU = self.rawCursorU
        self.cursorSignal.emit(self.cursorU, self.cursorV)

    # Processes the cursor for snapping, straight lines and whatnot
    def parseCursor(self):
        if self.keyStates['rmb']:
            return

        if self.keyStates['ctrl']:
            # If drawing new segments...
            if self.keyStates['lmb']:
                # Force straight horizontal or vertical lines

                dx = self.cursorU.x() - self.lmbDown.x()
                dy = self.cursorU.y() - self.lmbDown.y()
                if dx != 0:
                    if -1 < dy / dx < 1:
                        self.cursorU = QPointF(self.cursorU.x(), self.lmbDown.y())
                    else:
                        self.cursorU = QPointF(self.lmbDown.x(), self.cursorU.y())
                    self.cursorV = self.universeToViewport(self.cursorU)

            # Align to existing Hetool points

            x = (self.snapTol, self.cursorV.x())
            y = (self.snapTol, self.cursorV.y())

            for point in self.heV.getPoints():
                pointV = self.universeToViewport(point.getX(), point.getY())

                dx = abs(pointV.x() - self.cursorV.x())
                dy = abs(pointV.y() - self.cursorV.y())
                if dx < x[0]:
                    x = (dx, pointV.x())
                if dy < y[0]:
                    y = (dy, pointV.y())

            self.cursorV = QPointF(x[1], y[1])
            self.cursorU = self.viewportToUniverse(self.cursorV)

        if self.keyStates['shift']:
            # Snap to gridlines
            dx = self.cursorU.x() % self.interval
            if dx < self.interval / 2.0:
                x = self.cursorU.x() - dx
            else:
                x = self.cursorU.x() - dx + self.interval

            dy = self.cursorU.y() % self.interval
            if dy < self.interval / 2.0:
                y = self.cursorU.y() - dy
            else:
                y = self.cursorU.y() - dy + self.interval

            self.cursorU = QPointF(x, y)
            self.cursorV = self.universeToViewport(self.cursorU)
        else:
            # Snap to pre-existing Hetool points

            new = (self.snapTol, self.cursorV)
            for point in self.heV.getPoints():
                pointV = self.universeToViewport(point.getX(), point.getY())
                dx = pointV.x() - self.cursorV.x()
                dy = pointV.y() - self.cursorV.y()
                distance = math.sqrt(dx * dx + dy * dy)
                if distance < new[0]:
                    new = (distance, pointV)

            self.cursorV = new[1]
            self.cursorU = self.viewportToUniverse(self.cursorV)

        self.cursorSignal.emit(self.cursorU, self.cursorV)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        self.rawCursorV = event.pos()
        self.rawCursorU = self.viewportToUniverse(self.rawCursorV)
        self.cursorV = self.rawCursorV
        self.cursorU = self.rawCursorU

        self.parseCursor()

        if self.keyStates['lmb']:
            pass

        if self.keyStates['mmb']:
            src = self.viewportToUniverse(self.mmbDown)
            dst = self.viewportToUniverse(self.cursorV)
            self.center -= dst - src
            self.mmbDown = self.cursorV

        if self.keyStates['rmb']:
            pass

        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.keyStates['rmb']:
                self.keyStates['lmb'] = True
                self.lmbDown = self.cursorU

        if event.button() == Qt.MouseButton.MidButton:
            self.keyStates['mmb'] = True
            self.mmbDown = self.cursorV

        if event.button() == Qt.MouseButton.RightButton:
            self.keyStates['rmb'] = True
            self.keyStates['lmb'] = False
            self.rmbDown = self.cursorU
            if not self.keyStates['ctrl']:
                self.selection.clear()

        self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.keyStates['lmb']:  # Pressing RMB can cancel adding a segment
                fst = self.lmbDown
                snd = self.cursorU

                dx = fst.x() - snd.x()
                dy = fst.y() - snd.y()

                try:
                    if not (dx * dx + dy * dy < self.tol):
                        self.heC.insertSegment([fst.x(), fst.y(), snd.x(), snd.y()], self.tol)
                except Exception as e:
                    print(str(e))

            self.keyStates['lmb'] = False

        if event.button() == Qt.MouseButton.MidButton:
            self.keyStates['mmb'] = False

        if event.button() == Qt.MouseButton.RightButton:
            self.keyStates['rmb'] = False
            # Check for bounding box collision and only then for individual datapoints
            if self.data:
                l1 = self.data['minx'] - self.data['dx'] / 2.0
                r1 = self.data['maxx'] + self.data['dx'] / 2.0
                b1 = self.data['miny'] - self.data['dy'] / 2.0
                t1 = self.data['maxy'] + self.data['dy'] / 2.0

                l2 = min(self.rmbDown.x(), self.cursorU.x())
                r2 = max(self.rmbDown.x(), self.cursorU.x())
                b2 = min(self.rmbDown.y(), self.cursorU.y())
                t2 = max(self.rmbDown.y(), self.cursorU.y())

                if collision(l1, r1, b1, t1, l2, r2, b2, t2):
                    for index in range(self.data['n']):
                        x = self.data['x'][index]
                        y = self.data['y'][index]

                        if collision(l2, r2, b2, t2, x, y) and index not in self.selection:
                            self.selection.append(index)

        self.update()

    def wheelEvent(self, event: QtGui.QWheelEvent):
        old = self.viewportToUniverse(event.pos())
        if event.angleDelta().y() > 0:
            self.factor *= 0.9
        else:
            self.factor *= 1.1
        new = self.viewportToUniverse(event.pos())
        self.center += old - new

        self.resetCursor()
        self.parseCursor()
        self.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == Qt.Key_Escape:
            qApp.quit()

        if event.key() == Qt.Key_D:
            self.debug = not self.debug

        if event.key() == Qt.Key.Key_Control:
            self.keyStates['ctrl'] = True

        if event.key() == Qt.Key.Key_Shift:
            self.keyStates['shift'] = True

        if event.key() == Qt.Key.Key_Delete:
            self.deleteSelection()

        self.resetCursor()
        self.parseCursor()
        self.update()

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        #print('keyReleaseEvent: event.key() = {}'.format(event.key()))

        if event.key() == Qt.Key.Key_Control:
            self.keyStates['ctrl'] = False

        if event.key() == Qt.Key.Key_Shift:
            self.keyStates['shift'] = False

        self.resetCursor()
        self.parseCursor()
        self.update()


# ----- Data Manipulation -----

    # Updates self.data entries for min and max values of X, Y, I, J and T

    def updateMinMax(self):
        if 'n' not in self.data:
            return

        minx = None
        miny = None
        mini = None
        minj = None
        mint = None

        maxx = None
        maxy = None
        maxi = None
        maxj = None
        maxt = None

        for index in range(self.data['n']):
            x = self.data['x'][index]
            y = self.data['y'][index]
            i = self.data['i'][index]
            j = self.data['j'][index]
            t = self.data['t'][index]

            minx = x if minx is None else min(x, minx)
            miny = y if miny is None else min(y, miny)
            mini = i if mini is None else min(i, mini)
            minj = j if minj is None else min(j, minj)
            mint = t if mint is None else (mint if t is None else min(t, mint))

            maxx = x if maxx is None else max(x, maxx)
            maxy = y if maxy is None else max(y, maxy)
            maxi = i if maxi is None else max(i, maxi)
            maxj = j if maxj is None else max(j, maxj)
            maxt = t if maxt is None else (maxt if t is None else max(t, maxt))

        self.data['minx'] = minx
        self.data['miny'] = miny
        self.data['mini'] = mini
        self.data['minj'] = minj
        self.data['mint'] = mint

        self.data['maxx'] = maxx
        self.data['maxy'] = maxy
        self.data['maxi'] = maxi
        self.data['maxj'] = maxj
        self.data['maxt'] = maxt

    # Delete selected datapoints

    def deleteSelection(self):
        if self.selection:
            self.selection.sort()
            self.data['n'] -= len(self.selection)

            count = 0
            for index in self.selection:
                del self.data['x'][index - count]
                del self.data['y'][index - count]
                del self.data['i'][index - count]
                del self.data['j'][index - count]
                del self.data['t'][index - count]
                count += 1

            self.selection.clear()
            self.updateMinMax()

    # Set values (temperature) for selected datapoints

    def updateSelection(self):
        dialog = InputDialog(title='P4 - Entrada de Dados', labels=['Temperatura (K)'])
        dialog.exec()
        if dialog.result() == 1:
            try:
                t = float(dialog.lineEdits[0].text())
                for index in self.selection:
                    self.data['t'][index] = t

            except Exception:
                for index in self.selection:
                    self.data['t'][index] = None

            self.updateMinMax()

    # Adjuts screen to fit data, JSON first, then Hetool

    def fit(self):
        if 'n' in self.data and self.data['n'] > 0:
            L = self.data['minx']
            R = self.data['maxx']
            B = self.data['miny']
            T = self.data['maxy']
            W = max(10.0, R - L)
            H = max(10.0, T - B)

            self.factor = max(W / self.width(), H / self.height()) * 1.1
            self.center = QPointF(L + W / 2.0, B + H / 2.0)
            self.update()
            return

        if not(self.heV is None or self.heV.isEmpty()):
            L, R, B, T = self.heV.getBoundBox()
            W = R - L
            H = T - B

            self.factor = max(W / self.width(), H / self.height()) * 1.1
            self.center = QPointF(L + W / 2.0, B + H / 2.0)
            self.update()

    # Clears Hetool data, JSON data and selection

    def clear(self):
        self.data.clear()
        self.heM.clearAll()
        self.selection.clear()
        self.update()

    # Shows a dialog for saving self.data to JSON file

    def showSaveDialog(self):
        dialog = InputDialog(title='Salvar Arquivo', labels=['Nome do Arquivo'])
        dialog.exec()

        if dialog.result() == 1:
            try:
                filename = dialog.lineEdits[0].text()
                with open(filename, 'w') as outfile:
                    json.dump(self.data, outfile, indent=4)
            except Exception as e:
                pass

    # Shows a dialog for loading JSON file to self.data

    def showLoadDialog(self):
        dialog = InputDialog(title='Carregar Arquivo', labels=['Nome do Arquivo'])
        dialog.exec()

        if dialog.result() == 1:
            self.clear()

            try:
                filename = dialog.lineEdits[0].text()
                with open(filename) as infile:
                    self.data = json.load(infile)
            except Exception as e:
                pass

    # Show a dialog for creating a regular mesh of particles inside Hetool model's domain

    def showRegularMeshDialog(self):
        if (self.heV == None) or (self.heV.isEmpty()):
            return

        dx = 1.0
        dy = 1.0

        dialog = InputDialog(title='Criar Malha Regular', labels=['Largura da Partícula (m)', 'Altura da Partícula (m)'])
        dialog.exec()
        if dialog.result() == 1:
            try:
                dx = float(dialog.lineEdits[0].text())
                dy = float(dialog.lineEdits[1].text())
            except Exception as e:
                dx = 1.0
                dy = 1.0

        self.data.clear()
        self.selection.clear()

        L, R, B, T = self.heV.getBoundBox()

        n = 0
        minx = None
        miny = None
        mini = None
        minj = None
        maxx = None
        maxy = None
        maxi = None
        maxj = None

        X = []
        Y = []
        I = []
        J = []

        y = B + dy / 2.0
        i = 1
        while y <= T:
            x = L + dx / 2.0
            j = 1
            while x <= R:
                point = Point(x, y)
                for patch in self.heV.getPatches():
                    if patch.isPointInside(point):
                        n += 1

                        X.append(x)
                        Y.append(y)
                        I.append(i)
                        J.append(j)

                        minx = x if minx is None else min(x, minx)
                        miny = y if miny is None else min(y, miny)
                        mini = i if mini is None else min(i, mini)
                        minj = j if minj is None else min(j, minj)

                        maxx = x if maxx is None else max(x, maxx)
                        maxy = y if maxy is None else max(y, maxy)
                        maxi = i if maxi is None else max(i, maxi)
                        maxj = j if maxj is None else max(j, maxj)
                x += dx
                j += 1
            y += dy
            i += 1

        self.data['n'] = n
        self.data['dx'] = dx
        self.data['dy'] = dy

        self.data['minx'] = minx
        self.data['miny'] = miny
        self.data['mini'] = mini
        self.data['minj'] = minj
        self.data['mint'] = None

        self.data['maxx'] = maxx
        self.data['maxy'] = maxy
        self.data['maxi'] = maxi
        self.data['maxj'] = maxj
        self.data['maxt'] = None

        self.data['x'] = X
        self.data['y'] = Y
        self.data['i'] = I
        self.data['j'] = J
        self.data['t'] = [None] * n


    # Calls upon a Julia program to do some work using <filename> JSON file

    def solve(self):
        dialog = InputDialog(title='Solucionar PVC', labels=['Arquivo de Dados', 'Arquivo do Solucionador', 'Arquivo de saída'])
        dialog.exec()

        if dialog.result() == 1:
            try:
                infilename = dialog.lineEdits[0].text()
                solver = dialog.lineEdits[1].text()
                outfilename = dialog.lineEdits[2].text()
                os.system('julia {} "{}" "{}"'.format(solver, infilename, outfilename))
            except Exception as e:
                pass
