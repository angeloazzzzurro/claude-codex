#!/bin/zsh
set -euo pipefail

CODEX_TXT="$HOME/codici.txt"
NOTE_NAME="codici"
ACCOUNT_NAME="On My Mac"

if [[ ! -f "$CODEX_TXT" ]]; then
  exit 0
fi

# Convert plain text to minimal HTML body for Notes
HTML_BODY=$(python3 - <<'PY'
import html
from pathlib import Path
text = Path.home().joinpath('codici.txt').read_text(encoding='utf-8', errors='replace')
print('<pre style="font-family: Menlo, monospace; font-size: 12px;">' + html.escape(text) + '</pre>')
PY
)

TMP_HTML=$(mktemp /tmp/codici_notes.XXXXXX.html)
trap 'rm -f "$TMP_HTML"' EXIT
printf "%s" "$HTML_BODY" > "$TMP_HTML"

/usr/bin/osascript <<APPLESCRIPT
on run
  set noteName to "$NOTE_NAME"
  set accountName to "$ACCOUNT_NAME"
  set noteBody to (read POSIX file "$TMP_HTML")
  tell application "Notes"
    set theAccount to account accountName
    set theFolder to first folder of theAccount
    set theNote to missing value
    repeat with n in notes of theFolder
      if name of n is noteName then
        set theNote to n
        exit repeat
      end if
    end repeat
    if theNote is missing value then
      make new note at theFolder with properties {name:noteName, body:noteBody}
    else
      set body of theNote to noteBody
    end if
  end tell
end run
APPLESCRIPT

rm -f "$TMP_HTML"
