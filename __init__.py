# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PotreeCraft
                                 A QGIS plugin
 A project building tool for Potree
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-10-07
        copyright            : (C) 2019 by Béres Tamás
        email                : berestamasbela@protonmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PotreeCraft class from file PotreeCraft.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .potreecraft import PotreeCraft
    from .potreecraft_util import PotreeCraftSupport
    return PotreeCraft(iface,PotreeCraftSupport)
