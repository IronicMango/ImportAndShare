import csv
import json

import adsk.core, adsk.fusion

from ... import config
from ...lib import fusion360utils as futil

import os
import sys

def remove_from_path(name):
    if name in sys.path:
        sys.path.remove(name)
        remove_from_path(name)

app = adsk.core.Application.get()
ui = app.userInterface

NAME1 = 'Data_Handler'
NAME2 = "Custom Import Event"
NAME3 = "Custom Save Event"
NAME4 = "Custom Close Event"
# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []
my_data_handlers = []
my_custom_handlers = []


# Executed when add-in is run.  Create custom events so we don't disrupt the main application loop.
def start():
    app.unregisterCustomEvent(config.custom_event_id_import)
    custom_event_import = app.registerCustomEvent(config.custom_event_id_import)
    custom_event_handler_import = futil.add_handler(custom_event_import, handle_import, name=NAME2)
    my_custom_handlers.append({
        'custom_event_id': config.custom_event_id_import,
        'custom_event': custom_event_import,
        'custom_event_handler': custom_event_handler_import
    })

    app.unregisterCustomEvent(config.custom_event_id_save)
    custom_event_save = app.registerCustomEvent(config.custom_event_id_save)
    custom_event_handler_save = futil.add_handler(custom_event_save, handle_save, name=NAME3)
    my_custom_handlers.append({
        'custom_event_id': config.custom_event_id_save,
        'custom_event': custom_event_save,
        'custom_event_handler': custom_event_handler_save
    })

    app.unregisterCustomEvent(config.custom_event_id_close)
    custom_event_close = app.registerCustomEvent(config.custom_event_id_close)
    custom_event_handler_close = futil.add_handler(custom_event_close, handle_close, name=NAME4)
    my_custom_handlers.append({
        'custom_event_id': config.custom_event_id_close,
        'custom_event': custom_event_close,
        'custom_event_handler': custom_event_handler_close
    })

    # Create the event handler for when data files are complete.
    my_data_handlers.append(
        futil.add_handler(app.dataFileComplete, handle_data_file_complete, local_handlers=local_handlers,
                          name=NAME1))
    futil.log(f'**********local_handlers added: {len(local_handlers)}')
    futil.log(f'**********my_data_handlers added: {len(my_data_handlers)}')

# Executed when add-in is stopped.  Remove events.
def stop():
    futil.log(f'**********local_handlers stop: {len(local_handlers)}')
    futil.log(f'**********my_data_handlers stop: {len(my_data_handlers)}')

    for custom_item in my_custom_handlers:
        custom_item['custom_event'].remove(custom_item['custom_event_handler'])
        app.unregisterCustomEvent(custom_item['custom_event_id'])

    for data_handler in my_data_handlers:
        app.dataFileComplete.remove(data_handler)


# Import a document from the list
def handle_import(args: adsk.core.CustomEventArgs):
    event_data = json.loads(args.additionalInfo)
    file_name = event_data['file_name']
    file_path = event_data['file_path']

    futil.log(f'**********Importing: {file_name}')

    # Execute the Fusion 360 import into a new document
    import_manager = app.importManager
    step_options = import_manager.createSTEPImportOptions(file_path)
    new_document = import_manager.importToNewDocument(step_options)

    # Keep track of imported files
    config.imported_documents[file_name] = new_document
    config.imported_filenames.append(file_name)

    #Change the rope material
    design = new_document.design
    ##Get rope body
    for Q, name_ID in enumerate(config.body_Name_IDs) :
        add_appearances(name_ID, config.custom_Appearances[Q], design, config.body_Name_Match[Q])

    # Fire event to save the document
    event_data = {
        'file_name': file_name,
        'file_path': file_path
    }
    additional_info = json.dumps(event_data)
    app.fireCustomEvent(config.custom_event_id_save, additional_info)


# Save a specific Document
def handle_save(args: adsk.core.CustomEventArgs):
    event_data = json.loads(args.additionalInfo)
    file_name = event_data['file_name']

    futil.log(f'**********Saving: {file_name}')

    new_document = config.imported_documents[file_name]
    new_document.saveAs(file_name, config.target_data_folder, 'Imported from script', 'tag')


# Close a specific document
def handle_close(args: adsk.core.CustomEventArgs):
    event_data = json.loads(args.additionalInfo)
    file_name = event_data['file_name']

    futil.log(f'**********Closing: {file_name}')

    new_document = config.imported_documents.pop(file_name, False)
    if new_document:
        new_document.close(False)


# Function to be executed by the dataFileComplete event.
def handle_data_file_complete(args: adsk.core.DataEventArgs):
    futil.log(f'***In application_data_file_complete event handler for: {args.file.name}')

    document: adsk.core.Document
    for file_name, document in config.imported_documents.items():
        if document.isValid:
            if document.dataFile.isComplete:
                process_data_file(document.dataFile)
                # document.close(False)


def process_data_file(data_file: adsk.core.DataFile):
    # Make sure we are processing a file imported from this script
    if data_file.name in config.imported_filenames:
        try:
            # Create the public link for the data file
            public_link = data_file.publicLink
            futil.log(f"**********Created public link for {data_file.name}: {public_link}")

            # Record Data
            if config.export_To_AirTable :
                data = {
                    "fields": {
                        "Name": data_file.name,
                        "URN": data_file.versionId,
                        "Link": public_link
                    }
                }

                # Write to Airtable
                app_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                sys.path.insert(0, os.path.join(app_path, 'lib'))

                # Post url and headers need to be here so that they pick up the changed API key
                post_url = config.at_api_url
                post_headers = {
                    'Authorization' : 'Bearer ' + config.at_key,
                    'Content-Type': 'application/json'
                }

                # The following line may register an error in VSCode. If your file structure is correct, this should
                #   be inconsequential and will run correctly
                import requests
                post_airtable_request = requests.post(post_url, headers = post_headers, json = data)
                print(post_airtable_request.status_code)
                if post_airtable_request.status_code != 200 :
                        config.export_Errors.append("Export error code: " + str(post_airtable_request.status_code) + "      File: " + data_file.name)
                remove_from_path(os.path.join(app_path, 'lib'))

            if config.export_To_CSV :
                config.results.append({
                    'Name': data_file.name,
                    'URN': data_file.versionId,
                    'Link': public_link
                })

            config.imported_filenames.remove(data_file.name)

            # Fire close event for this Document
            event_data = {
                'file_name': data_file.name,
            }
            additional_info = json.dumps(event_data)
            app.fireCustomEvent(config.custom_event_id_close, additional_info)

        except:
            futil.handle_error('process_data_file')

        # If all documents have been processed finalize results
        if len(config.imported_filenames) == 0:
            if not config.run_finished:
                config.run_finished = True
                if config.export_To_CSV :
                    write_results()
            if not config.export_Errors :
                ui.messageBox("Process Completed Succesfully. If files are left open, please use the 'Close All' function")
            else :
                error_Message = "The process completed with the following export errors: \n"
                for e_Error in config.export_Errors :
                    error_Message += str(e_Error)
                    error_Message += "\n"
                ui.messageBox(error_Message)
                config.export_Errors =[]

    else:
        # futil.log(f"**********Already processed: {data_file.name}")
        ...


def write_results():
    futil.log(f"Writing CSV")
    with open(config.csv_File_Name, mode='w') as csv_file:
        fieldnames = ['Name', 'URN', 'Link']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in config.results:
            writer.writerow(row)

def add_appearances(body_Name_ID, custom_Appearance,current_Design,name_Match):
    all_Components = current_Design.allComponents
    for component in all_Components:
        body_Name = component.name
        if name_Match == False :
            if body_Name_ID in body_Name:
                if component.bRepBodies.count != 0 :
                    comp_Bodies = component.bRepBodies
                    comp_Body = comp_Bodies.itemByName("Body1")
                    comp_Body.appearance = custom_Appearance
        else :
            if body_Name_ID == body_Name:
                if component.bRepBodies.count != 0 :
                    comp_Bodies = component.bRepBodies
                    comp_Body = comp_Bodies.itemByName("Body1")
                    comp_Body.appearance = custom_Appearance