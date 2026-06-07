from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("spine.proxy")


def build_proxy_config(cfg: Any) -> dict | None:
    """Build a nono ProxyConfig from the Spine config and environment.

    Reads GITHUB_TOKEN and TELEGRAM_BOT_TOKEN from the Spine's environment
    and configures credential-injection routes.  The Cortex never sees the
    real tokens — it talks to the proxy which injects them on matching
    outbound requests.

    Returns a ``nono_py.ProxyConfig``, or ``None`` if nono_py is not installed.
    """
    try:
        from nono_py import InjectMode, ProxyConfig, RouteConfig
    except ImportError:
        return None

    allowed_hosts = [
        # LLM / API
        "api.telegram.org",
        "api.github.com",
        "github.com",
        "*.githubusercontent.com",
        # Package registries (for uv/pip/apt at runtime)
        "pypi.org",
        "files.pythonhosted.org",
        "deb.debian.org",
        "security.debian.org",
        "archive.ubuntu.com",
        "packages.debian.org",
    ]

    routes: list[RouteConfig] = []

    # ------------------------------------------------------------------
    # GitHub routes — swap dummy token for real GITHUB_TOKEN
    # ------------------------------------------------------------------
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        # api.github.com (REST / GraphQL)
        routes.append(
            RouteConfig(
                prefix="/github",
                upstream="https://api.github.com",
                credential_key="github-token",
                env_var="GITHUB_TOKEN",
                inject_mode=InjectMode.HEADER,
                inject_header="Authorization",
                credential_format="Bearer {credential}",
            )
        )
        # github.com (git over HTTPS — smart-HTTP protocol)
        routes.append(
            RouteConfig(
                prefix="/git",
                upstream="https://github.com",
                credential_key="github-token",
                env_var="GITHUB_TOKEN",
                inject_mode=InjectMode.HEADER,
                inject_header="Authorization",
                credential_format="Bearer {credential}",
            )
        )

    # ------------------------------------------------------------------
    # Telegram route
    # ------------------------------------------------------------------
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if telegram_token:
        routes.append(
            RouteConfig(
                prefix="/telegram",
                upstream="https://api.telegram.org",
                credential_key="telegram-token",
                env_var="TELEGRAM_BOT_TOKEN",
                # Telegram tokens go in the URL path: /bot<token>/method
                inject_mode=InjectMode.URL_PATH,
            )
        )

    return ProxyConfig(
        allowed_hosts=allowed_hosts,
        routes=routes,
        bind_addr="127.0.0.1",
        bind_port=0,  # OS picks a free port
    )


def start_credential_proxy(cfg: Any):
    """Start the nono network credential proxy.

    The proxy intercepts outbound HTTP from the Cortex, enforces a host
    allowlist, and swaps dummy credentials for real API keys loaded from
    the Spine's environment.

    Returns a ``nono_py.ProxyHandle``, or ``None`` if nono is unavailable
    or the proxy fails to start.
    """
    config = build_proxy_config(cfg)
    if config is None:
        logger.warning("[Proxy] nono_py not available — credential proxy disabled")
        return None

    try:
        from nono_py import start_proxy

        proxy = start_proxy(config)
        logger.info(
            "[Proxy] Started credential proxy on port %d — %d hosts allowed, %d credential routes",
            proxy.port,
            len(config.allowed_hosts),
            len(config.routes),
        )
        return proxy
    except Exception:
        logger.exception("[Proxy] Failed to start credential proxy")
        return None
