# Application Global Variables
# This module serves as a way to share variables across different
# modules (global variables).

import os

# Flag that indicates to run in Debug mode or not. When running in Debug mode
# more information is written to the Text Command window. Generally, it's useful
# to set this to True while developing an add-in and set it to False when you
# are ready to distribute it.
DEBUG = True

# Gets the name of the add-in from the name of the folder the py file is in.
# This is used when defining unique internal names for various UI elements 
# that need a unique name. It's also recommended to use a company name as 
# part of the ID to better ensure the ID is unique.
ADDIN_NAME = os.path.basename(os.path.dirname(__file__))
COMPANY_NAME = 'Ironic Mango Designs'


# *********** Global Variables Unique to this Add-in **************

# Keep track of imported files
imported_filenames = []

# Keep track of imported files
imported_documents = {}

#This is for reporting export errors
export_Errors = []

#This is the airtable link given in the API documentation for the table you want to use.
at_api_url = ""

# For Export Type(s)
export_To_CSV = False
export_To_AirTable = False

# CSV filename
csv_File_Name = None

# Appearance Names
appearance_Names = []

# Keep track of material
custom_Appearance = None

# Names of ropes as imported
body_Name_IDs = []

# For getting API key
at_key = ""
API_Key_Good = False

# Extension types that will be processed for import
EXTENSION_TYPES = ['.step', '.stp', '.STEP','.STP']

custom_event_id_import = 'custom_event_import'
custom_event_id_save = 'custom_event_id_save'
custom_event_id_close = 'custom_event_id_close'

target_data_folder = None

results = []
run_finished = False
