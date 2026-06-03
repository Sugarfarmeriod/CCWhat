"""setup subcommand — first-run onboarding wizard for recording configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import click

from ccwhat.config import (
    DEFAULT_CONFIG_PATH,
    PRESETS,
    RecordingConfig,
    load_config,
    normalize_path,
    save_config,
    validate_config,
    validate_domain,
)

_GATEWAY_ENV_VARS = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_BEDROCK_BASE_URL",
    "ANTHROPIC_VERTEX_BASE_URL",
    "ANTHROPIC_AWS_BASE_URL",
]


def _detect_gateway_hosts() -> list[str]:
    """Return candidate gateway hosts from environment variables."""
    hosts: list[str] = []
    for var in _GATEWAY_ENV_VARS:
        value = os.environ.get(var, "").strip()
        if not value:
            continue
        try:
            parsed = urlparse(value if "://" in value else f"https://{value}")
            if parsed.hostname:
                hosts.append(parsed.hostname)
        except Exception:
            pass
    return list(dict.fromkeys(hosts))


def _print_config_summary(cfg: RecordingConfig, config_path: Path | None = None) -> None:
    path = config_path or DEFAULT_CONFIG_PATH
    domains = cfg.effective_domains()
    paths = cfg.effective_paths()
    click.echo(f"\nConfig file   : {path}")
    click.echo(f"Domains       : {', '.join(domains) if domains else '(none)'}")
    click.echo(f"Path filters  : {', '.join(paths) if paths else '(all paths)'}")
    click.echo(f"Redaction     : {len(cfg.redact_headers)} sensitive headers redacted by default")
    click.echo(f"Body size cap : {cfg.max_body_bytes // 1024} KB")
    click.echo(
        "\nOnly the domains and paths listed above will have request/response payloads recorded.\n"
        "Login, updater, GitHub, telemetry, and other traffic is proxied but NOT recorded."
    )


def _run_setup_wizard(config_path: Path | None = None) -> RecordingConfig | None:
    """Run the interactive wizard and return the saved config, or None on cancel."""
    existing = load_config(config_path)
    if existing:
        click.echo(f"\nExisting configuration found at {config_path or DEFAULT_CONFIG_PATH}:")
        _print_config_summary(existing, config_path)
        if not click.confirm("\nReconfigure recording settings?", default=False):
            click.echo("No changes made.")
            return existing

    click.echo("\n=== ccwhat setup ===\n")
    click.echo("Choose your Claude API setup:")
    click.echo("  1) Official Claude API  (api.anthropic.com)")
    click.echo("  2) Gateway / base URL   (custom or corporate proxy)")
    click.echo("  3) Not sure             (run discovery to detect endpoints)")

    choice = click.prompt("Select [1/2/3]", default="1")

    if choice == "1":
        cfg = RecordingConfig(preset="claude", onboarding_complete=True)
        click.echo("\nWill record:")
        click.echo("  Domain : api.anthropic.com")
        click.echo("  Paths  : /v1/messages, /v1/messages/count_tokens")

    elif choice == "2":
        gateway_hosts = _detect_gateway_hosts()
        if gateway_hosts:
            click.echo(f"\nDetected gateway candidate(s): {', '.join(gateway_hosts)}")
            host = click.prompt("Use this host? (press Enter to accept or type a different one)", default=gateway_hosts[0])
        else:
            host = click.prompt("\nEnter your gateway URL or hostname (e.g. gateway.example.com or https://gateway.example.com/anthropic)")
            # Extract hostname if a full URL was given
            if "://" in host:
                parsed = urlparse(host)
                host = parsed.hostname or host

        try:
            host = validate_domain(host)
        except ValueError as exc:
            click.echo(f"Invalid domain: {exc}", err=True)
            return None

        path_input = click.prompt("Path filter (press Enter for /v1/messages)", default="/v1/messages")
        paths = [normalize_path(p.strip()) for p in path_input.split(",") if p.strip()]

        cfg = RecordingConfig(domains=[host], paths=paths, onboarding_complete=True)

        click.echo(f"\nWill record:")
        click.echo(f"  Domain : {host}")
        click.echo(f"  Paths  : {', '.join(paths)}")

    elif choice == "3":
        click.echo(
            "\nStarting metadata-only discovery.\n"
            "Launch or use your AI coding CLI in another terminal and ccwhat will\n"
            "observe traffic to suggest which endpoints to record.\n"
            "Run: ccwhat discover -- claude   (or any AI CLI command)"
        )
        return None

    else:
        click.echo("Invalid choice.", err=True)
        return None

    _print_config_summary(cfg, config_path)

    if not click.confirm("\nSave this configuration?", default=True):
        click.echo("No changes made.")
        return None

    save_config(cfg, config_path)
    click.echo(f"\nConfiguration saved to {config_path or DEFAULT_CONFIG_PATH}")
    click.echo("You can now run: ccwhat -- claude")
    return cfg


@click.command("setup")
@click.option("--preset", default=None, help="Named preset (e.g. claude) for non-interactive setup.")
@click.option("--domain", default=None, help="Record this domain (non-interactive).")
@click.option("--path", "path_filter", default=None, help="Path filter (non-interactive).")
@click.option("--yes", is_flag=True, help="Accept without prompting (non-interactive mode).")
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to config.toml (defaults to ~/.ccwhat/config.toml).",
)
def setup(
    preset: str | None,
    domain: str | None,
    path_filter: str | None,
    yes: bool,
    config_path: Path | None,
) -> None:
    """Configure which model API endpoints ccwhat records."""
    if yes:
        # Non-interactive mode
        if not preset and not domain:
            click.echo(
                "Error: --yes requires --preset or --domain.\n"
                "Examples:\n"
                "  ccwhat setup --preset claude --yes\n"
                "  ccwhat setup --domain gateway.example.com --path /v1/messages --yes",
                err=True,
            )
            sys.exit(1)

        try:
            if domain:
                domain_validated = validate_domain(domain)
            paths = [normalize_path(path_filter)] if path_filter else []
        except ValueError as exc:
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)

        if preset and preset not in PRESETS:
            click.echo(f"Error: unknown preset {preset!r}. Available: {', '.join(PRESETS)}", err=True)
            sys.exit(1)

        cfg = RecordingConfig(
            preset=preset,
            domains=[domain_validated] if domain else [],
            paths=paths,
            onboarding_complete=True,
        )
        errors = validate_config(cfg)
        if errors:
            for err in errors:
                click.echo(f"Error: {err}", err=True)
            sys.exit(1)

        save_config(cfg, config_path)
        click.echo(f"Configuration saved to {config_path or DEFAULT_CONFIG_PATH}")
        click.echo(f"Domains: {', '.join(cfg.effective_domains())}")
        return

    # Interactive mode
    result = _run_setup_wizard(config_path)
    if result is None and not load_config(config_path):
        sys.exit(1)
