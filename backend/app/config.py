"""
配置管理模块
从 config.json 文件读取配置，支持环境变量覆盖
"""

import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """配置类"""
    
    def __init__(self):
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 配置文件路径
        config_path = Path(__file__).parent.parent / "config.json"
        
        # 如果配置文件存在，读取它
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                print(f"✅ 配置文件加载成功: {config_path}")
            except Exception as e:
                print(f"⚠️  配置文件加载失败: {e}")
                self._config = {}
        else:
            print(f"⚠️  配置文件不存在: {config_path}")
            self._config = {}
    
    def get(self, key: str, default=None):
        """
        获取配置值，支持点号分隔的嵌套键
        例如: config.get("llm.dashscope_api_key")
        
        优先级：环境变量 > 配置文件 > 默认值
        """
        # 将点号分隔的键转换为大写下划线格式的环境变量名
        # 例如: llm.dashscope_api_key -> LLM_DASHSCOPE_API_KEY
        env_key = key.upper().replace('.', '_')
        
        # 1. 首先检查环境变量
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
        
        # 2. 然后检查配置文件
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value if value != "" else default
    
    @property
    def dashscope_api_key(self) -> Optional[str]:
        """获取 DashScope API Key"""
        # 支持多种环境变量名
        key = (
            self.get("llm.dashscope_api_key") or
            os.getenv("DASHSCOPE_API_KEY") or
            os.getenv("QWEN_API_KEY")
        )
        return key if key else None
    
    @property
    def deepseek_api_key(self) -> Optional[str]:
        """获取 DeepSeek API Key"""
        key = (
            self.get("llm.deepseek_api_key") or
            os.getenv("DEEPSEEK_API_KEY")
        )
        return key if key else None
    
    @property
    def server_host(self) -> str:
        """获取服务器主机"""
        return self.get("server.host", "0.0.0.0")
    
    @property
    def server_port(self) -> int:
        """获取服务器端口"""
        return int(self.get("server.port", 8000))
    
    @property
    def log_level(self) -> str:
        """获取日志级别"""
        return self.get("server.log_level", "INFO")
    
    @property
    def max_upload_size_mb(self) -> int:
        """获取最大上传大小（MB）"""
        return int(self.get("detection.max_upload_size_mb", 10))
    
    @property
    def session_expire_seconds(self) -> int:
        """获取会话过期时间（秒）"""
        return int(self.get("detection.session_expire_seconds", 3600))


# 全局配置实例
config = Config()


# 便捷函数
def get_config(key: str, default=None):
    """获取配置值"""
    return config.get(key, default)


def reload_config():
    """重新加载配置"""
    global config
    config = Config()
    return config
