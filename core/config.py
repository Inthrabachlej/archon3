"""Configuration management"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.GPT5_MODEL: str = os.getenv("GPT5_MODEL", "gpt-5")
        self.GPT4O_MODEL: str = os.getenv("GPT4O_MODEL", "gpt-4o")
        self.CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        self.INPUT_DIR: str = "input"
        self.OUTPUT_DIR: str = "output"
        self.MAX_RETRIES: int = 3
        self.TEMPERATURE_ARCHITECT: float = 0.7
        self.TEMPERATURE_BUILDER: float = 0.3
        self.TEMPERATURE_VALIDATOR: float = 0.1
        self.TEMPERATURE_INTEGRATOR: float = 0.5

    def validate(self) -> bool:
        if not self.OPENAI_API_KEY:
            print("⚠️  OPENAI_API_KEY not set")
            return False
        if not self.ANTHROPIC_API_KEY:
            print("⚠️  ANTHROPIC_API_KEY not set")
            return False
        return True

config = Config()
