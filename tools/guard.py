"""A guard that runs before every tool call of an AI assistant and refuses to touch secrets.

Claude Code hands each planned call to this script as JSON on stdin (see .claude/settings.json).
Exit code 2 refuses the call and passes the message on stderr back to the assistant; exit code
0 lets it run. The rules themselves are in AGENTS.md — this file is the part a machine can
enforce. It runs on the system Python, so it uses the standard library only.
"""

import json
import re
import sys

# .env and every .env.<name>, except the committed template .env.example; `*` counts as part of
# a name, so the search pattern `.env.*` is caught too. The look-behind keeps `process.env` and
# `os.environ` out; the look-ahead keeps `.envrc` out.
ENV_FILE = re.compile(r"(?<![\w.$])\.env(?:\.(?!example\b)[\w.*-]+)?(?![\w.-])")
# A folder called secrets/, wherever it is.
SECRETS_DIR = re.compile(r"(?<![\w.-])secrets(?=/|\s*$)")
# Private keys and certificates: server.key, client.pem.
KEY_FILE = re.compile(r"[\w-]\.(?:pem|key)(?![\w.-])")
# Commands that print the whole environment, or the Compose file with .env filled in.
PRINTS_ENVIRONMENT = re.compile(
    r"\bprintenv\b|(?:^|[;&|]\s*)env\s*(?:$|[;&|])|\bdocker[ -]compose\b.*\bconfig\b"
)

# Which fields of a tool call name a path. Grep's `pattern` is searched *inside* files, so it is
# not a path; Glob's `pattern` is one.
PATH_FIELDS = {
    "Glob": ("pattern", "path"),
    "Grep": ("path", "glob"),
}

REFUSAL = "Refused by tools/guard.py — secrets are off limits (AGENTS.md): {what}. "
HINT = "If you need a variable, add its name to .env.example and ask a person to set it."


def touches_secret(text: str) -> str | None:
    """Name the kind of secret a path or command refers to, or None."""
    if ENV_FILE.search(text):
        return "an environment file"
    if SECRETS_DIR.search(text):
        return "the secrets folder"
    if KEY_FILE.search(text):
        return "a key file"
    return None


def check(tool: str, args: dict[str, object]) -> str | None:
    """Return why a tool call is refused, or None when it may run."""
    if tool == "Bash":
        command = str(args.get("command", ""))
        if PRINTS_ENVIRONMENT.search(command):
            return REFUSAL.format(what="a command that prints the environment") + HINT
        texts = [command]
    else:
        keys = PATH_FIELDS.get(tool, ("file_path", "notebook_path"))
        texts = [str(args[key]) for key in keys if key in args]

    for text in texts:
        what = touches_secret(text)
        if what:
            return REFUSAL.format(what=what) + HINT
    return None


def main() -> int:
    # A guard that cannot read its input refuses: a gate that silently opens is no gate.
    try:
        call = json.load(sys.stdin)
        reason = check(call.get("tool_name", ""), call.get("tool_input") or {})
    except Exception as error:
        reason = f"Refused by tools/guard.py — it could not check this call: {error}"
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
