# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PotreeCraft
                                 A QGIS plugin
 Description
                             -------------------
        copyright            : (C) 2026 by Béres Tamás
        email                : orksmile@gmail.com
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
    return PotreeCraft(iface)
