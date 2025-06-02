import re
import sys
import webbrowser
from pathlib import Path

from clideps.env_vars.dotenv_utils import (
    check_env_vars,
    load_dotenv_paths,
    update_env_file,
)
from clideps.ui.inputs import input_confirm, input_simple_string
from clideps.ui.rich_output import (
    format_failure,
    format_success,
    print_heading,
)
from dotenv import load_dotenv
from prettyfmt import fmt_lines, fmt_path
from rich import print as rprint
from strif import abbrev_str

from textpress.api.textpress_env import LOGIN_URL, Env

REQUIRED_ENV_VARS = [Env.TEXTPRESS_API_KEY.value]


class CancelSetup(RuntimeError):
    pass


def _cli_name() -> str:
    """The actual CLI command name."""
    return Path(sys.argv[0]).stem


def _env_config_path() -> Path:
    return Path.home() / ".config" / "textpress" / "env"


def _validate_api_key(api_key: str) -> bool | str:
    """
    Validate API key format: tp_ followed by 32 hexadecimal characters.
    """
    api_key = api_key.strip()
    if not api_key:
        return False
    if re.match(r"^tp_[a-fA-F0-9]*$", api_key) and len(api_key) != 32 + 3:
        return "The API isn't the expected length. It should look something like: tp_1234567890abcdef1234567890abcdef"

    if not re.match(r"^tp_[a-fA-F0-9]{32}$", api_key):
        return "The API key doesn't look right. It should look something like: tp_1234567890abcdef1234567890abcdef"

    return True


def read_env_vars(verbose: bool = False) -> bool:
    env_vars = check_env_vars(*REQUIRED_ENV_VARS)

    if len(env_vars) == len(REQUIRED_ENV_VARS):
        if verbose:
            rprint(format_success("Found required environment variables:"))
            rprint(fmt_lines([f"{k} = {repr(abbrev_str(v, 8))}" for k, v in env_vars.items()]))
            rprint()
        return True

    return False


def load_env(verbose: bool = False) -> bool:
    """
    Check env vars, then the standard config env path, then look for .env files.
    """
    if read_env_vars(verbose=verbose):
        return True

    load_dotenv(_env_config_path())

    if read_env_vars(verbose=verbose):
        return True

    load_dotenv_paths()

    if read_env_vars(verbose=verbose):
        return True

    return False


def show_setup() -> bool:
    rprint()
    if _env_config_path().exists():
        rprint(format_success(f"Found config file at {fmt_path(_env_config_path())}"))
    else:
        rprint(format_failure(f"No config file at {fmt_path(_env_config_path())}"))

    if not load_env(verbose=True):
        rprint(format_failure("Required environment variables not found."))
        return False

    return True


def interactive_setup() -> None:
    try:
        print_heading("Configuring environment variables")

        found = show_setup()
        if found:
            rprint(
                "You already have an API key configured. But you can continue to "
                "use a different account or retrieve your API key again."
            )

        rprint()
        rprint(
            "You will need a Textpress account to get an API key. "
            "Visit `app.textpress.md` to create an account or log in."
        )
        rprint("[bright_black](Hit Ctrl-C to cancel.)[/bright_black]")
        rprint()

        if input_confirm(
            "Visit `app.textpress.md` now?",
            default=True,
        ):
            webbrowser.open(LOGIN_URL)
            rprint()
            rprint("After you log in you will get your API key and username.")
        else:
            rprint()
            if input_confirm("Do you already have an API key?", default=True):
                pass
            else:
                raise CancelSetup

        rprint()
        api_key = input_simple_string("Enter your API key: ", validate=_validate_api_key)
        if not api_key:
            raise CancelSetup

        update_env_file(
            _env_config_path(),
            {Env.TEXTPRESS_API_KEY.value: api_key},
            create_if_missing=True,
        )
        rprint()
        rprint(format_success(f"Settings saved to: {fmt_path(_env_config_path())}"))
        rprint()
        rprint(
            f"You're all set! Run `[bold cyan]{_cli_name()} --help[/bold cyan]` for the list of commands."
        )
        rprint()

        load_dotenv(_env_config_path(), override=True)

        if not read_env_vars(verbose=False):
            raise RuntimeError("Failed to load configuration after setup.")

    except CancelSetup:
        rprint()
        rprint("[yellow]Cancelling.[/yellow]")
        rprint()
