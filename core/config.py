"""
配置管理器 - 加载和管理 YAML 配置
"""
import yaml
import os
from pathlib import Path


class Config:
    """加载和访问框架配置"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "default.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    def get(self, key: str, default=None):
        """用点号路径获取配置 e.g. 'browser.headless'"""
        keys = key.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    @property
    def browser(self) -> dict:
        return self._data.get("browser", {})

    @property
    def launch_args(self) -> list:
        return self._data.get("launch_args", [])

    @property
    def proxy(self) -> dict:
        return self._data.get("proxy", {})

    @property
    def behavior(self) -> dict:
        return self._data.get("behavior", {})

    @property
    def webrtc(self) -> dict:
        return self._data.get("webrtc", {})
