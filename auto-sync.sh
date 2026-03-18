#!/usr/bin/env bash
# auto-sync.sh — Watch → commit + push senza loop né sovrascritture

REPO="$(cd "$(dirname "$0")" && pwd)"
LOCK="/tmp/autosync-$(echo "$REPO" | md5).lock"
DELAY=8   # secondi di latenza fswatch (debounce nativo)

commit_and_push() {
  # ── Impedisce esecuzioni concorrenti ──
  if [ -f "$LOCK" ]; then return; fi
  touch "$LOCK"

  cd "$REPO" || { rm -f "$LOCK"; return; }

  # ── Niente da committare → esci ──
  if [ -z "$(git status --porcelain)" ]; then
    rm -f "$LOCK"; return
  fi

  TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
  CHANGED=$(git status --porcelain | awk '{print $2}' | head -4 | tr '\n' ',' | sed 's/,$//')

  # ── Stage solo file tracciati o nuovi (no binari grandi) ──
  git add -A -- ':!*.log' ':!*.lock' ':!node_modules' ':!*.pyc'

  # ── Commit solo se lo staging non è vuoto ──
  if git diff --cached --quiet; then
    rm -f "$LOCK"; return
  fi

  git commit -m "auto: $CHANGED [$TIMESTAMP]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

  # ── Push: se rejected, fetch+rebase (non pull) per evitare merge commit ──
  if ! git push origin main 2>/dev/null; then
    git fetch origin main 2>/dev/null
    # Rebase locale sopra remote (non tocca i file se non ci sono conflitti)
    if git rebase origin/main 2>/dev/null; then
      git push origin main 2>/dev/null
    else
      # Conflitto reale: abort e avvisa senza sovrascrivere
      git rebase --abort 2>/dev/null
      echo "⚠️  [$TIMESTAMP] Conflitto rilevato — push saltato. Risolvi manualmente."
      rm -f "$LOCK"; return
    fi
  fi

  echo "✅ [$TIMESTAMP] → $CHANGED"
  rm -f "$LOCK"
}

# ── Cleanup lock se lo script viene interrotto ──
trap "rm -f '$LOCK'; echo ''; echo '🛑 Auto-sync fermato.'; exit 0" INT TERM

echo "👀 Auto-sync attivo: $REPO"
echo "   Latenza: ${DELAY}s — Lock: $LOCK"
echo "   Premi Ctrl+C per fermare."
echo ""

# ── fswatch con debounce nativo (-l DELAY) e un solo evento per batch ──
# Escludi .git, node_modules, cache e il log stesso per evitare loop
fswatch -r -l "$DELAY" --one-per-batch \
  --exclude="\.git/" \
  --exclude="node_modules/" \
  --exclude="__pycache__/" \
  --exclude="\.pyc$" \
  --exclude="\.DS_Store$" \
  --exclude="\.log$" \
  --exclude="\.lock$" \
  "$REPO" | while read -r _; do
    commit_and_push
  done
