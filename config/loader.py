import yaml
import platform

class Configuration:
    def __init__(self, filepath):
        self.data = {}
        with open(filepath, "r") as yamlfile:
            data_loaded = yaml.safe_load(yamlfile)
            
            self.data = data_loaded

    def getConfiguration(self):
        return self.data

if platform.system() == 'Windows':
    c = Configuration("/Users/apple/Desktop/cymmetri/cymmetri-microservices-rolemining/config.yaml")
else:
    c = Configuration("config.yaml")

ConfObject = c.getConfiguration()

def getConfigObject():
    return ConfObject