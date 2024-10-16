from pydantic import Field
from ayon_server.settings import BaseSettingsModel


class ScriptsmenuSubmodel(BaseSettingsModel):
    """Item Definition"""
    _isGroup = True

    type: str = Field(title="Type")
    command: str = Field(title="Command")
    sourcetype: str = Field(title="Source Type")
    title: str = Field(title="Title")
    tooltip: str = Field(title="Tooltip")


class ScriptsmenuSettings(BaseSettingsModel):
    """Nuke script menu project settings."""
    _isGroup = True

    name: str = Field(title="Menu Name")
    definition: list[ScriptsmenuSubmodel] = Field(
        default_factory=list,
        title="Definition",
        description="Scriptmenu Items Definition"
    )


DEFAULT_SCRIPTSMENU_SETTINGS = {
    "name": "Custom Tools",
    "definition": [
        {
            "type": "action",
            "sourcetype": "python",
            "title": "Ayon Nuke Docs",
            "command": "import webbrowser;webbrowser.open(url='https://ayon.ynput.io/docs/addon_nuke_artist')",  # noqa
            "tooltip": "Open the Ayon Nuke user doc page"
        },
        {
            "type": "action",
            "sourcetype": "python",
            "title": "Set Frame Start (Read Node)",
            "command": "from openpype.hosts.nuke.startup.frame_setting_for_read_nodes import main;main();",  # noqa
            "tooltip": "Set frame start for read node(s)"
        },
        {
            "type": "action",
            "sourcetype": "python",
            "title": "Set non publish output for Write Node",
            "command": "from openpype.hosts.nuke.startup.custom_write_node import main;main();",  # noqa
            "tooltip": "Open the OpenPype Nuke user doc page"
        }
    ]
}
