import os

from hw import core
from hw.utils import print_center

# Create the HWUI class object for the user interface.
hw = core.HWUI(
    config_dir = os.path.expanduser(os.path.join("~", ".config", "hw"))
)


print_center("================================================================================")
print_center("Welcome to the Howling Wolf program V%s"%(core.__version__), '|', '|')
print_center("================================================================================")
