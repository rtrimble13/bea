"""Runtime configuration, sourced from environment variables.

The API key (BEA calls it the *UserID*) is **only** read from the environment
(``BEA_API_KEY``); it is never accepted on the command line so it cannot leak
into shell history or process listings (see
``docs/adr/0003-api-key-from-environment.md``).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_BASE_URL = "https://apps.bea.gov/api/data"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3
API_KEY_LENGTH = 36  # BEA issues 36-character UserIDs

ENV_API_KEY = "BEA_API_KEY"
ENV_BASE_URL = "BEA_API_BASE_URL"
ENV_TIMEOUT = "BEA_TIMEOUT"
ENV_MAX_RETRIES = "BEA_MAX_RETRIES"
ENV_CACHE_DIR = "BEA_CACHE_DIR"
ENV_USER_AGENT = "BEA_USER_AGENT"
ENV_FORMAT = "BEA_FORMAT"
ENV_NO_COLOR = "NO_COLOR"

SIGNUP_URL = "https://apps.bea.gov/API/signup/"


def default_cache_dir(env: Mapping[str, str] | None = None) -> Path:
    """Return the XDG-style cache directory used for metadata caches."""
    env = os.environ if env is None else env
    xdg = env.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "bea"


def default_user_agent() -> str:
    from bea import __version__

    return f"bea-cli/{__version__} (+https://github.com/rtrimble13/bea)"


@dataclass(frozen=True)
class Settings:
    """Effective configuration for one CLI invocation or client instance."""

    api_key: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    cache_dir: Path = field(default_factory=default_cache_dir)
    user_agent: str = field(default_factory=default_user_agent)
    default_format: str | None = None
    no_color: bool = False

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env

        def _float(name: str, default: float) -> float:
            raw = env.get(name)
            if raw is None or raw.strip() == "":
                return default
            try:
                return float(raw)
            except ValueError as exc:
                raise ValueError(f"{name} must be a number, got {raw!r}") from exc

        def _int(name: str, default: int) -> int:
            raw = env.get(name)
            if raw is None or raw.strip() == "":
                return default
            try:
                return int(raw)
            except ValueError as exc:
                raise ValueError(f"{name} must be an integer, got {raw!r}") from exc

        api_key = (env.get(ENV_API_KEY) or "").strip() or None
        cache_dir_raw = env.get(ENV_CACHE_DIR)
        return cls(
            api_key=api_key,
            base_url=(env.get(ENV_BASE_URL) or DEFAULT_BASE_URL).rstrip("/"),
            timeout=_float(ENV_TIMEOUT, DEFAULT_TIMEOUT),
            max_retries=_int(ENV_MAX_RETRIES, DEFAULT_MAX_RETRIES),
            cache_dir=Path(cache_dir_raw).expanduser() if cache_dir_raw else default_cache_dir(env),
            user_agent=env.get(ENV_USER_AGENT) or default_user_agent(),
            default_format=(env.get(ENV_FORMAT) or "").strip().lower() or None,
            no_color=bool(env.get(ENV_NO_COLOR)),
        )

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    @property
    def api_key_looks_valid(self) -> bool:
        """True when the key has the length BEA issues (a weak, offline sanity check)."""
        return bool(self.api_key) and len(self.api_key or "") == API_KEY_LENGTH

    def masked_api_key(self) -> str:
        """Return the key with all but the last four characters hidden."""
        if not self.api_key:
            return "(not set)"
        if len(self.api_key) <= 4:
            return "*" * len(self.api_key)
        return "*" * (len(self.api_key) - 4) + self.api_key[-4:]
