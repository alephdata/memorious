import os
from memorious.core import manager


def init():
    file_path = os.path.dirname(__file__)
    config_path = os.path.join(file_path, "..", "..", "config")
    manager.load_path(config_path)
