from qgis.PyQt.QtWidgets import QAction

from .copernicus_downloader_dialog import CopernicusDownloaderWindow


class CopernicusDownloaderPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.menu = "&Copernicus Downloader"
        self.window = None

    def initGui(self):
        action = QAction("Copernicus Downloader", self.iface.mainWindow())
        action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.menu, action)
        self.iface.addToolBarIcon(action)
        self.actions.append(action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        self.actions.clear()
        if self.window is not None:
            self.window.close()
            self.window = None

    def run(self):
        if self.window is None:
            self.window = CopernicusDownloaderWindow(self.iface, self.iface.mainWindow())
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
