import os
import yaml
import yaml.loader


# =====
def load_file(file_path):
    with open(file_path) as yaml_file:
        try:
            return yaml.load(yaml_file, _YamlLoader)
        except Exception:
            # Reraise internal exception as standard ValueError and show the incorrect file
            raise ValueError("Incorrect YAML syntax in file '{}'".format(file_path))


# =====
class _YamlLoader(yaml.loader.Loader):  # pylint: disable=too-many-ancestors
    def __init__(self, yaml_file):
        yaml.loader.Loader.__init__(self, yaml_file)
        self._root = os.path.dirname(yaml_file.name)

    def include(self, node):
        # Logger which supports include-files
        file_path = os.path.join(self._root, self.construct_scalar(node))  # pylint: disable=no-member
        return load_file(file_path)
_YamlLoader.add_constructor("!include", _YamlLoader.include)  # pylint: disable=no-member
