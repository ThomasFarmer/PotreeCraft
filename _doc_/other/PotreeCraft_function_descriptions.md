# PotreeCraft Function Descriptions

## Class Summary

`PotreeCraft` is the main QGIS plugin entrypoint. It registers the plugin in the QGIS UI, manages toolbar and menu actions, and opens the main dialog when the user starts the plugin.

## Methods

### `__init__(self, iface)`

- Purpose: Initialize the plugin instance and store the QGIS interface reference.
- Inputs:
  - `iface`: The active QGIS interface object used to add menus, toolbars, and dialogs.
- Output:
  - None.
- Notes:
  - Loads translation resources when available.
  - Creates the plugin toolbar and stores basic plugin state.

### `tr(self, message)`

- Purpose: Translate a UI string through the Qt translation system.
- Inputs:
  - `message`: The source string to translate.
- Output:
  - The translated string returned by `QCoreApplication.translate(...)`.

### `add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True, add_to_toolbar=True, status_tip=None, whats_this=None, parent=None)`

- Purpose: Create a QAction and optionally add it to the plugin toolbar and QGIS plugin menu.
- Inputs:
  - `icon_path`: Path or Qt resource identifier for the action icon.
  - `text`: Visible label for the action.
  - `callback`: Function called when the action is triggered.
  - `enabled_flag`: Whether the action starts enabled.
  - `add_to_menu`: Whether to add the action to the plugin menu.
  - `add_to_toolbar`: Whether to add the action to the plugin toolbar.
  - `status_tip`: Optional tooltip/status-bar text.
  - `whats_this`: Optional help text for Qt's "What's This" system.
  - `parent`: Optional parent widget for the action.
- Output:
  - A configured `QAction` instance.

### `initGui(self)`

- Purpose: Register the plugin's main action in the QGIS GUI.
- Inputs:
  - None.
- Output:
  - None.
- Notes:
  - Uses `add_action(...)` to wire the main toolbar/menu command to `run()`.

### `unload(self)`

- Purpose: Remove the plugin menu items and toolbar icons from QGIS during unload.
- Inputs:
  - None.
- Output:
  - None.

### `run(self)`

- Purpose: Open the main PotreeCraft dialog and refresh project-aware state.
- Inputs:
  - None.
- Output:
  - None.
- Notes:
  - Lazily creates the dialog the first time it is opened.
  - Refreshes vector layers when the dialog already exists.
