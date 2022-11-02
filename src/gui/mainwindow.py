from PyQt5.QtWidgets import QMainWindow, QStatusBar, QVBoxLayout, QWidget
from gui.navbar import Navbar
from gui.canvas import Canvas
from gui.status import Status

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        #print('MainWindow()')

        self.resize(800, 600)
        self.setStyleSheet('background: #0f0f0f; color: white;')

        self.navbar = Navbar()
        self.canvas = Canvas()
        self.status = Status()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.navbar)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.status)
        
        self.container = QWidget()
        self.container.setLayout(self.layout)

        self.setCentralWidget(self.container)

        # TODO: self.setCentralWidget()

    
