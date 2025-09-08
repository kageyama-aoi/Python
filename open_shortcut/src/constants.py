from enum import Enum

class Action(str, Enum):
    OPEN_DIRECTORY = "open_directory"
    OPEN_URL = "open_url"
    SHOW_PAGE = "show_page"
    OPEN_PARAMETERIZED_URL = "open_parameterized_url"

class ConfigKey(str, Enum):
    # Top level
    SETTINGS = "settings"
    STYLES = "styles"
    PAGES = "pages"

    # Settings
    WINDOW_TITLE = "window_title"
    GEOMETRY = "geometry"
    RESIZABLE = "resizable"
    ICON_FOLDER = "icon_folder"
    WINDOW_ICON = "window_icon"
    DEFAULT_BUTTON_ICON = "default_button_icon"
    INITIAL_PAGE = "initial_page"

    # Page entry
    TYPE = "type"
    NAME = "name"
    ACTION = "action"
    PATH = "path"
    URL = "url"
    TARGET = "target"
    BASE_URL = "base_url"
    PARAMETERS = "parameters"
    ICON = "icon"
    BACKGROUND = "background"
    FOREGROUND = "foreground"
    ENTRIES = "entries"
    TITLE = "title"

    # Parameter definition
    LABEL = "label"
    OPTIONS = "options"
    DEFAULT_VALUE = "default_value"

class EntryType(str, Enum):
    SEPARATOR = "separator"

class ParamType(str, Enum):
    TEXT = "text"
    PULLDOWN = "pulldown"