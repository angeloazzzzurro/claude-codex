#!/usr/bin/env bash
# auto-sync.sh — Osserva modifiche e fa commit+push su GitHub automaticamente

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
COOLDOWN=8   # secondi di attesa dopo l'ultima modifica prima di committare

echo "👀 Auto-sync attivo su: $REPO_DIR"
echo "   Ogni modifica ai file verrà committata e pushata su GitHub."
echo "   Premi Ctrl+C per fermare."
echo ""

last_change=0

fswatch -r --exclude="\.git" --exclude="node_modules" --exclude="__pycache__" \
  --exclude="\.pyc$" --exclude="\.DS_Store" \
  "$REPO_DIR" | while read -r changed_file; do

  now=$(date +%s)
  last_change=$now

  sleep "$COOLDOWN"

  # Verifica che non siano arrivate altre modifiche nel frattempo
  current=$(date +%s)
  if (( current - last_change < COOLDOWN )); then
    continue
  fi

  cd "$REPO_DIR" || exit 1

  # Controlla se ci sono modifiche reali
  if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
    continue
  fi

  TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
  CHANGED=$(git status --porcelain | head -5 | awk '{print $2}' | tr '\n' ', ' | sed 's/,$//')

  git add -A

  git commit -m "auto: $CHANGED [$TIMESTAMP]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>" 2>/dev/null

  if git push origin main 2>&1 | grep -q "rejected\|error"; then
    git pull --rebase origin main 2>/dev/null && git push origin main 2>/dev/null
  fi

  echo "✅ [$TIMESTAMP] Pushato: $CHANGED"
done
