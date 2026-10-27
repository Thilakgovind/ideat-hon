"""Set one value in the project .env without showing it on screen.

    .venv\\Scripts\\python -m backend.set_env SUPABASE_DB_URL
    .venv\\Scripts\\python -m backend.set_env RAZORPAY_KEY_SECRET

The value is typed (or pasted) at a hidden prompt, then written to .env:
the existing NAME= line is replaced, or a new line is added. Nothing is printed
except the name and the value's length, so you can confirm the paste worked.
"""
import getpass
import re
import sys

from backend import config

NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def set_value(name: str, value: str, path=None) -> str:
    path = path or (config.ROOT / ".env")
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    new = f"{name}={value}"
    for i, line in enumerate(lines):
        if line.strip().split("=", 1)[0].strip() == name:
            lines[i] = new
            action = "replaced"
            break
    else:
        lines.append(new)
        action = "added"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return action


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1 or not NAME_RE.match(argv[0]):
        print("usage: python -m backend.set_env NAME   (eg SUPABASE_DB_URL)")
        return 2
    name = argv[0]
    value = getpass.getpass(f"{name} (input hidden, paste then Enter): ").strip()
    if not value or any(c.isspace() for c in value):
        print(f"{name}: not saved (empty or contains spaces)")
        return 1
    action = set_value(name, value)
    print(f"{name}: {action} in .env ({len(value)} characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
