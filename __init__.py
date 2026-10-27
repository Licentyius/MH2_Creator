from .mh2_creator import MH2CreatorUI

def load_as_mh2_plugin(parent_notebook):
    # Initializes the clean UI layout variable matching your main file class name
    plugin_tab = MH2CreatorUI()
    parent_notebook.addTab(plugin_tab, "MH2 Creator Sync")
    return plugin_tab
