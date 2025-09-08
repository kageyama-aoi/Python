classDiagram
    direction LR

    class RunBat
    class MainPy {
        +main()
    }
    class ConstantsFile

    class DirectoryOpenerApp {
        -config: dict
        -pages: dict
        +__init__()
        +_load_config()
        +_create_widgets()
        +reload_ui()
        +open_settings_window()
    }

    class SettingsEditor {
        -config: dict
        -on_save_callback: Callable
        +__init__()
        +save_config()
        +open_parameter_editor_window()
    }

    class ParameterEditor {
        +__init__()
        +save_parameter()
    }

    class Action
    class ConfigKey

    RunBat ..> MainPy : executes
    MainPy ..> DirectoryOpenerApp : creates
    DirectoryOpenerApp ..> SettingsEditor : creates & passes callback
    SettingsEditor ..> ParameterEditor : creates

    DirectoryOpenerApp ..> Action : uses
    DirectoryOpenerApp ..> ConfigKey : uses
    SettingsEditor ..> Action : uses
    SettingsEditor ..> ConfigKey : uses

    ConstantsFile ..> Action
    ConstantsFile ..> ConfigKey
