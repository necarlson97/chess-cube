import yaml

# TODO could change for multiple players, concurrent games
SAVE_FILE_NAME = 'assets/save.yaml'


def load():
    """
    Load the save file dictionary from yaml
    """
    with open(SAVE_FILE_NAME, 'r') as save_file:
        dikt = yaml.safe_load(save_file)
        if dikt is None:
            dikt = {}
        return dikt


def save(dikt):
    """
    Save a given dictionary to the yaml save file
    """
    with open(SAVE_FILE_NAME, 'w') as save_file:
        yaml.safe_dump(dikt, save_file)


def read_config_file():
    """
    Read in config file (primarily for email player),
    return as an object which has data accessed like variables,
    but is pulled from the yaml dict
    """
    # Read in the config file to get sensative (non-git) email info
    with open('assets/config.yaml', 'r') as f:
        dikt = yaml.safe_load(f)['email_config']

    # Allows to access this dict as if it were an object
    # TODO do we need this? Is there a better way?
    class ObjectView():
        def __init__(self, d):
            self.__dict__ = d
    return ObjectView(dikt)
