import math
from PyQt5 import QtGui
from PyQt5.QtCore import QPointF, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, qApp
import sys, os

from gui.mainwindow import MainWindow

# TODO:
# Selection for forces and restraints


class MyMainWindow(MainWindow):
    def __init__(self):
        super().__init__()
        # print('MyMainWindow()')

        self.setWindowTitle('Modelador Gráfico')

        self.navbar.button1.clicked.connect(lambda: self.canvas.fit())
        self.navbar.button2.clicked.connect(lambda: self.canvas.showRegularMeshDialog())
        self.navbar.button3.clicked.connect(lambda: self.canvas.clear())

        self.navbar.button4.clicked.connect(lambda: self.canvas.updateSelection())
        self.navbar.button5.clicked.connect(lambda: self.canvas.solve())

        self.navbar.button6.clicked.connect(lambda: self.canvas.showSaveDialog())
        self.navbar.button7.clicked.connect(lambda: self.canvas.showLoadDialog())
        self.navbar.button8.clicked.connect(lambda: qApp.quit())

        self.canvas.cursorSignal.connect(self.setLabel)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        #print('keyPressEvent: event.key() = {}'.format(event.key()))
        self.canvas.keyPressEvent(event)

        if event.key() == Qt.Key.Key_P:
            print('screenshot!')
            screenshot = qApp.primaryScreen().grabWindow(self.winId())

            path = 'screenshot.png'
            count = 1
            while os.path.exists(path):
                path = 'screenshot({}).png'.format(count)
                count += 1

            screenshot.save(path, 'png')

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        #print('keyReleaseEvent: event.key() = {}'.format(event.key()))
        self.canvas.keyReleaseEvent(event)

    @pyqtSlot(QPointF, QPointF)
    def setLabel(self, u, v):
        self.status.label.setText('Universe: ({},{}) Viewport: ({},{})'.format(
            '{:.2f}'.format(u.x()).rjust(8),
            '{:.2f}'.format(u.y()).rjust(8),
            '{:.2f}'.format(v.x()).rjust(8),
            '{:.2f}'.format(v.y()).rjust(8)))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MyMainWindow()
    gui.show()
    sys.exit(app.exec_())
