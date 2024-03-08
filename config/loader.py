import yaml
import platform
import os

# class Configuration:
#     def __init__(self, filepath):
#         self.data = {}
#         with open(filepath, "r") as yamlfile:
#             data_loaded = yaml.safe_load(yamlfile)
            
#             self.data = data_loaded

#     def getConfiguration(self):
#         return self.data

# if platform.system() != 'Windows':
#     c = Configuration("/Users/apple/Desktop/cymmetri/cymmetri-microservices-generativeAI/config.yaml")
# else:
#     #c = Configuration("config.yaml")
#     c = Configuration(os.environ.get("/Users/apple/Desktop/cymmetri/cymmetri-microservices-generativeAI/config.yaml", "config.yaml"))

# ConfObject = c.getConfiguration()




import os

class Configuration:
    def __init__(self, filepath=None):
        self.data = {}
        if filepath is None:
            filepath = os.environ.get('CONFIG_FILE_PATH', 'config.yaml')
        with open(filepath, "r") as yamlfile:
            data_loaded = yaml.safe_load(yamlfile)
            self.data = data_loaded

    def getConfiguration(self):
        return self.data
    