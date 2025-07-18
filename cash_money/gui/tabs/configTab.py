import imgui as im
import logging

from configparser import ConfigParser
from cash_money.utils.run_utils import _configLoc

log = logging.getLogger("Config Settings")


class ConfigTab:

    def __init__(self, configs: ConfigParser) -> None:
        self.configs = configs
        self.log_level_options = ["Debug", "Info", "Warning", "Error"]
        self.log_level_index = self.get_log_level_index()
        self.notify_options = ["Console", "Email"]
        self.notify_index = self.get_notify_index()
        self.timeframe_options = ["second", "daily"]
        self.timeframe_index = self.get_timeframe_index()
        self.timeframe_value = self.configs["Alpaca"].get("Timeframe_value", "60")

        # Initialize fields
        self.live_api_key_ref = im.StrRef(self.configs.get('Alpaca', 'Live_API_Key', fallback=""), 256)
        self.live_api_secret_ref = im.StrRef(self.configs.get('Alpaca', 'Live_API_Secret', fallback=""), 256)
        self.paper_api_key_ref = im.StrRef(self.configs.get('Alpaca', 'Paper_API_Key', fallback=""), 256)
        self.paper_api_secret_ref = im.StrRef(self.configs.get('Alpaca', 'Paper_API_Secret', fallback=""), 256)
        self.timeframe_value_ref = im.StrRef(self.timeframe_value, 64)

        self.needSave = False

    def save_config(self):
        """Manually writes the configuration to the file with custom formatting."""
        with open(_configLoc, 'w') as f:
            self.configs.write(f)
        self.needSave = False

    def get_log_level_index(self):
        try:
            return self.log_level_options.index(self.configs["System"].get("LogLevel", "Debug"))
        except ValueError:
            return 0

    def get_notify_index(self):
        try:
            return self.notify_options.index(self.configs["System"].get("Notify", "Console"))
        except ValueError:
            return 0

    def get_timeframe_index(self):
        try:
            return self.timeframe_options.index(self.configs["Alpaca"].get("Timeframe", "second"))
        except ValueError:
            return 0

    def render(self):
        if im.BeginChild("settings", im.Vec2(500, 0)):
            # Save all settings on button click
            pushed = False
            if self.needSave:
                pushed = True
                im.PushStyleColor(im.Col.Button, im.Vec4(1.0, 0.2, 0.2, 1.0))
            if im.Button("Save Config"):
                # Update the configuration from the current input values
                self.configs["System"]["LogLevel"] = self.log_level_options[self.log_level_index]
                self.configs["System"]["Notify"] = self.notify_options[self.notify_index]
                self.configs["Alpaca"]["Live_API_Key"] = str(self.live_api_key_ref)
                self.configs["Alpaca"]["Live_API_Secret"] = str(self.live_api_secret_ref)
                self.configs["Alpaca"]["Paper_API_Key"] = str(self.paper_api_key_ref)
                self.configs["Alpaca"]["Paper_API_Secret"] = str(self.paper_api_secret_ref)
                self.configs["Alpaca"]["Timeframe"] = self.timeframe_options[self.timeframe_index]
                self.configs["Alpaca"]["Timeframe_value"] = str(self.timeframe_value_ref)

                # Save to file
                self.save_config()
                log.info("Config saved successfully.")
            if pushed:
                im.PopStyleColor(1)

            # Log Level Dropdown
            im.Text("System Settings")
            if im.BeginCombo("Log Level", self.log_level_options[self.log_level_index]):
                for idx, option in enumerate(self.log_level_options):
                    if im.Selectable(option, self.log_level_index == idx):
                        self.log_level_index = idx
                        self.needSave = True
                im.EndCombo()

            if im.BeginCombo("Notify", self.notify_options[self.notify_index]):
                for idx, option in enumerate(self.notify_options):
                    if im.Selectable(option, self.notify_index == idx):
                        self.notify_index = idx
                        self.needSave = True
                im.EndCombo()

            # Alpaca API Key Inputs
            im.Separator()
            im.Text("Alpaca API Keys")
            if im.InputText("Live_API_Key", self.live_api_key_ref, 256):
                self.needSave = True
            if im.InputText("Live_API_Secret", self.live_api_secret_ref, 256):
                self.needSave = True
            if im.InputText("Paper_API_Key", self.paper_api_key_ref, 256):
                self.needSave = True
            if im.InputText("Paper_API_Secret", self.paper_api_secret_ref, 256):
                self.needSave = True

            # Timeframe Dropdown
            im.Separator()
            im.Text("Timeframe")
            if im.BeginCombo("Timeframe", self.timeframe_options[self.timeframe_index]):
                for idx, option in enumerate(self.timeframe_options):
                    if im.Selectable(option, self.timeframe_index == idx):
                        self.timeframe_index = idx
                        self.needSave = True
                im.EndCombo()

            # Conditional input based on selected timeframe
            if self.timeframe_options[self.timeframe_index] == "second":
                if im.InputText("Timeframe_value", self.timeframe_value_ref, 256):
                    self.needSave = True
            elif self.timeframe_options[self.timeframe_index] == "daily":
                # daily_timeframe_ref = im.StrRef(self.config["Alpaca"].get("Daily_Timeframe", "open"))
                if im.InputText("Timeframe_value", self.timeframe_value_ref, 256):
                    self.configs["Alpaca"]["Timeframe_value"] = str(self.timeframe_value_ref)
                    self.needSave = True
        im.EndChild()
