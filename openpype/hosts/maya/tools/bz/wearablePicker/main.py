from .ui import WearablePicker
from .utils import _getMainMayaWindow

def show():
    for child in _getMainMayaWindow().children():
        if "WearablePicker" in str(child):
            child.deleteLater()

    w = WearablePicker(_getMainMayaWindow())
    w.show()