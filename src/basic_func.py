import yaml
import os

def read_yaml(file_path):
    with open(file_path, 'r') as f:
        return yaml.load(f, Loader=yaml.SafeLoader)

def get_value(file_name, key):
    file_path = os.path.join(os.getcwd(), file_name)
    data = read_yaml(file_path)
    for k in key.split("."):
        data = data[k]
    return data