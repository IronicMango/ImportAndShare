import adsk.core
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface

# Set Command name and description
CMD_NAME = 'Import Folder'
CMD_Description = 'Import a folder of STEP files and create share links'

# Command ID must be unique relative to other commands in Fusion 360
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_{CMD_NAME}'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
# Typically don't need to change anything here.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
# Typically don't need to change anything here.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # This command will auto-execute.
    # Meaning it will not create a command dialog for user input
    args.command.isAutoExecute = True

    # Add handlers for the execute and destroy events of the command
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # Have User select a folder containing STEP Files to be imported
    folder_dialog = ui.createFolderDialog()
    folder_dialog.title = "Select Folder"
    dialog_result = folder_dialog.showDialog()
    if dialog_result == adsk.core.DialogResults.DialogOK:
        folder = folder_dialog.folder
    else:
        return

    # For this script we are simply choosing the root folder of the currently active project
    # You can see this in the in the data panel
    # Here you could do something more complete to determine the proper location
    try:
        target_data_folder = app.data.activeProject.rootFolder
    except:
        ui.messageBox("You probably are navigated to a project in the data panel. "
                      "For example, can't be in recent documents.")
        return

    # Iterate over all STEP files in user selected directory
    for full_file_name in os.listdir(folder):
        file_path = os.path.join(folder, full_file_name)
        if os.path.isfile(file_path):
            split_tup = os.path.splitext(full_file_name)
            file_name = split_tup[0]
            file_extension = split_tup[1]
            if file_extension in config.EXTENSION_TYPES:

                # Execute the Fusion 360 import into a new document
                import_manager = app.importManager
                step_options = import_manager.createSTEPImportOptions(file_path)
                new_document = import_manager.importToNewDocument(step_options)

                # Save the new document and record name
                new_document.saveAs(file_name, target_data_folder, 'Imported from script', 'tag')
                config.imported_filenames.append(file_name)


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    # Clean up event handlers
    global local_handlers
    local_handlers = []
