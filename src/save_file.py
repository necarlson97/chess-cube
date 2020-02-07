import yaml

# TODO could change for multiple players, concurrent games
SAVE_FILE_NAME = 'assets/save.yaml'


def load():
    """
    Load the save file dictionary from yaml
    """
    with open(SAVE_FILE_NAME, 'r+') as save_file:
        dikt = yaml.safe_load(save_file)
        if dikt is None:
            dikt = {}
        return dikt


def save(dikt):
    """
    Save a given dictionary to the yaml save file
    """
    with open(SAVE_FILE_NAME, 'r+') as save_file:
        yaml.safe_dump(dikt, save_file)
