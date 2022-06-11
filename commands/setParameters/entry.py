import adsk.core
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface
import sys

#This cleans up the inclusion of the 'requests' library
def remove_from_path(name):
    if name in sys.path:
        sys.path.remove(name)
        remove_from_path(name)

# Set Command name and description
CMD_NAME = 'Set Parameters'
CMD_Description = 'Sets necessary options before importing'

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

    # Get the command that was created.
    cmd = adsk.core.Command.cast(args.command)

    # Add handler for the destroy event of the command
    futil.add_handler(cmd.destroy, command_destroy, local_handlers=local_handlers)

    # *******************Add handler for the Change event of the command
    #futil.add_handler(cmd.destroy, command_destroy, local_handlers=local_handlers)

    # Get the CommandInputs collection associated with the command.
    inputs = cmd.commandInputs

    # Create a tab input.
    tabCmdInput1 = inputs.addTabCommandInput('API_Usage', 'API')
    tab1ChildInputs = tabCmdInput1.children

    # Create a string value input.
    key_Input = tab1ChildInputs.addStringValueInput('APIKeyInput', 'Your API Key', 'Key*************')
    key_Input.isPassword = False
    
    # Add handler for the execute event of the command
    futil.add_handler(cmd.execute, command_execute, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # Get the values from the command inputs.
    eventArgs = adsk.core.CommandEventArgs.cast(args) 
    inputs = eventArgs.command.commandInputs
    
    config.at_key = inputs.itemById('APIKeyInput').value

    # *********We will now do a basic get request from airtable to ensure that the API key is good
    # Setup for test post to AirTable
    post_url = config.at_api_url
    post_headers = {
        'Authorization' : 'Bearer ' + config.at_key,
        'Content-Type': 'application/json'
    }

    # Dummy Data for blank Post
    data = {
        "fields": {
            "Name": "Auth Test",
            "URN": "Auth Test",
            "Link": "Auth Test"
        }
    }

    # write to Airtable
    app_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    # app_path = app_path[0:101]
    sys.path.insert(0, os.path.join(app_path, 'lib'))
    # The following line may register an error in VSCode. If your file structure is correct, this should
    #  be inconsequential and will run correctly
    import requests
    post_airtable_request = requests.post(post_url, headers = post_headers, json = data)
    print(post_airtable_request.status_code)
    if post_airtable_request.status_code != 200 :
        config.API_Key_Good = False
        ui.messageBox(f'API Key unauthorized or invalid.\nError Code:   {post_airtable_request.status_code}')
        return
    
    # Get the post ID from the authorization post
    post_airtable_request.raise_for_status
    request_Result = post_airtable_request.json()
    post_ID = request_Result["id"]

    # Setup for deleting from AirTable
    delete_url = config.at_api_url + '/' + post_ID
    delete_headers = {
        'Authorization' : 'Bearer ' + config.at_key,
    }

    # Delete the test post
    delete_airtable_request = requests.delete(delete_url, headers = delete_headers)
    print(delete_airtable_request.status_code)
    if delete_airtable_request.status_code != 200 :
        ui.messageBox(f'Post request succeeded, but the post was unable to be removed.\nError Code:   {delete_airtable_request.status_code}')


    remove_from_path(os.path.join(app_path, 'lib'))

    config.API_Key_Good = True

    


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    # Clean up event handlers
    global local_handlers
    local_handlers = []
