import imgui as im
import configparser
import logging

log = logging.getLogger("Config Settings")


class ConfigTab:

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.load_config()

        self.log_level_options = ["Debug", "Info", "Warning", "Error"]
        self.log_level_index = self.get_log_level_index()
        self.notify_options = ["Console", "Email"]
        self.notify_index = self.get_notify_index()
        self.timeframe_options = ["second", "daily"]
        self.timeframe_index = self.get_timeframe_index()
        self.timeframe_value = self.config["Alpaca"].get("Timeframe_value", "60")

        # Initialize fields
        self.live_api_key_ref = im.StrRef(self.config.get('Alpaca', 'Live_API_Key', fallback=""), 256)
        self.live_api_secret_ref = im.StrRef(self.config.get('Alpaca', 'Live_API_Secret', fallback=""), 256)
        self.paper_api_key_ref = im.StrRef(self.config.get('Alpaca', 'Paper_API_Key', fallback=""), 256)
        self.paper_api_secret_ref = im.StrRef(self.config.get('Alpaca', 'Paper_API_Secret', fallback=""), 256)
        self.timeframe_value_ref = im.StrRef(self.timeframe_value, 64)

    def load_config(self):
        """Loads the configuration from file."""
        try:
            with open(self.config_path, 'r') as config_file:
                self.config.read_file(config_file)
        except FileNotFoundError:
            log.warning(f"Config file {self.config_path} not found")
        except configparser.Error as e:
            log.warning("Error reading config file")

    def save_config(self):
        """Manually writes the configuration to the file with custom formatting."""
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
    
    def get_log_level_index(self):
        try:
            return self.log_level_options.index(self.config["System"].get("LogLevel", "Debug"))
        except ValueError:
            return 0

    def get_notify_index(self):
        try:
            return self.notify_options.index(self.config["System"].get("Notify", "Console"))
        except ValueError:
            return 0

    def get_timeframe_index(self):
        try:
            return self.timeframe_options.index(self.config["Alpaca"].get("Timeframe", "second"))
        except ValueError:
            return 0


    def render(self):
        
        # Log Level Dropdown
        im.Text("System Settings")
        if im.BeginCombo("Log Level", self.log_level_options[self.log_level_index]):
            for idx, option in enumerate(self.log_level_options):
                if im.Selectable(option, self.log_level_index == idx):
                    self.log_level_index = idx
            im.EndCombo()
            
        if im.BeginCombo("Notify", self.notify_options[self.notify_index]):
            for idx, option in enumerate(self.notify_options):
                if im.Selectable(option, self.notify_index == idx):
                    self.notify_index = idx
            im.EndCombo()

        # Alpaca API Key Inputs
        im.Separator()
        im.Text("Alpaca API Keys")

        im.InputText("Live_API_Key", self.live_api_key_ref, 256)
        im.InputText("Live_API_Secret", self.live_api_secret_ref, 256)
        im.InputText("Paper_API_Key", self.paper_api_key_ref, 256)
        im.InputText("Paper_API_Secret", self.paper_api_secret_ref, 256)

        # Timeframe Dropdown
        im.Separator()
        im.Text("Timeframe")
        if im.BeginCombo("Timeframe", self.timeframe_options[self.timeframe_index]):
            for idx, option in enumerate(self.timeframe_options):
                if im.Selectable(option, self.timeframe_index == idx):
                    self.timeframe_index = idx
            im.EndCombo()

        # Conditional input based on selected timeframe
        if self.timeframe_options[self.timeframe_index] == "second":
            im.InputText("Timeframe_value", self.timeframe_value_ref, 256)
        elif self.timeframe_options[self.timeframe_index] == "daily":
            # daily_timeframe_ref = im.StrRef(self.config["Alpaca"].get("Daily_Timeframe", "open"))
            im.InputText("Timeframe_value", self.timeframe_value_ref, 256)
            self.config["Alpaca"]["Timeframe_value"] = str(self.timeframe_value_ref)

        # Save all settings on button click
        if im.Button("Save Config"):
            # Update the configuration from the current input values
            self.config["System"]["LogLevel"] = self.log_level_options[self.log_level_index]
            self.config["System"]["Notify"] = self.notify_options[self.notify_index]
            self.config["Alpaca"]["Live_API_Key"] = str(self.live_api_key_ref)
            self.config["Alpaca"]["Live_API_Secret"] = str(self.live_api_secret_ref)
            self.config["Alpaca"]["Paper_API_Key"] = str(self.paper_api_key_ref)
            self.config["Alpaca"]["Paper_API_Secret"] = str(self.paper_api_secret_ref)
            self.config["Alpaca"]["Timeframe"] = self.timeframe_options[self.timeframe_index]
            self.config["Alpaca"]["Timeframe_value"] = str(self.timeframe_value_ref)

            # Save to file
            self.save_config()
            log.info("Config saved successfully.")

