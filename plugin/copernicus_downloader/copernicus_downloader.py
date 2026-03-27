# -*- coding: utf-8 -*-
"""Classe principal do plugin no QGIS."""

import os

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .resources import *  # noqa: F401,F403
from .copernicus_downloader_dialog import downloaderDialog


class downloader:
    """Implementação principal do plugin."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr('&Copernicus Downloader')
        self.first_start = True
        self.dlg = None

        locale = QSettings().value('locale/userLocale', 'pt_BR')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'downloader_{locale}.qm',
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

    def tr(self, message):
        return QCoreApplication.translate('downloader', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/copernicus_downloader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr('Baixar arquivo e adicionar camada'),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if self.dlg is None:
            self.dlg = downloaderDialog(self.iface, self.iface.mainWindow())

        self.dlg.reset_defaults()
        self.dlg.exec_()
