# -*- coding: utf-8 -*-
"""Ponto de entrada do plugin para o QGIS."""


def classFactory(iface):  # pylint: disable=invalid-name
    from .plugin import CopernicusDownloaderPlugin
    return CopernicusDownloaderPlugin(iface)
