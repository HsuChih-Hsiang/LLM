import yaml
 
def get_yaml(file_name):
    with open(file_name, "r") as stream:
        data = yaml.load(stream)
    return data