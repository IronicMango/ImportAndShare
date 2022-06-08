# Here you define the commands that will be added to your add-in.

# If you want to add an additional command, duplicate one of the existing directories and import it here.
# You need to use aliases (import "entry" as "my_module") assuming you have the default module named "entry".
from .importFolder import entry as import_folder
from .dataFileComplete import entry as complete
from .closeAll import entry as close
from .processRemaining import entry as remaining
from .setParameters import entry as parameters

# Fusion will automatically call the start() and stop() functions.
commands = [
    import_folder,
    complete,
    close,
    remaining,
    parameters,
]


# Assumes you defined a "start" function in each of your modules.
# The start function will be run when the add-in is started.
def start():
    for command in commands:
        command.start()


# Assumes you defined a "stop" function in each of your modules.
# The stop function will be run when the add-in is stopped.
def stop():
    for command in commands:
        command.stop()
