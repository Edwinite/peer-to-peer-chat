#!/usr/bin/env bash
# setup-git.sh
# ---------------------------------------------------------------------------
# Bootstraps a clean git repo with two branches:
#
#   original  - snapshot of the 2024 code (before the DH rewrite)
#   main      - current code (DH handshake, macOS UI fixes, etc.)
#
# Run this ONCE from the project folder on your Mac:
#
#   cd ~/Desktop/"CMP2204 Computer Network's Project"
#   bash setup-git.sh
#
# After it finishes, follow the printed instructions to create a GitHub repo
# and push both branches.
# ---------------------------------------------------------------------------

set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
echo ">>> Working in: $PROJECT_DIR"

BACKUP_DIR=".original-backup"
if [ ! -d "$BACKUP_DIR" ]; then
  echo "ERROR: $BACKUP_DIR not found. This script expects the 2024 code snapshot"
  echo "       to live in that hidden folder. Re-run the Cowork session or"
  echo "       restore the folder from a backup before running this script."
  exit 1
fi

# ---------------------------------------------------------------------------
# 1. Wipe any half-initialised repo from previous attempts.
# ---------------------------------------------------------------------------
if [ -d ".git" ]; then
  echo ">>> Removing existing .git directory"
  rm -rf .git
fi

# The old duplicate file — the backup has it, the main code drops it.
if [ -e "responder.py" ]; then
  echo ">>> Removing duplicate responder.py from working tree (still preserved in $BACKUP_DIR)"
  rm -f responder.py
fi

# Drop __pycache__ so it doesn't pollute either branch.
rm -rf __pycache__

# ---------------------------------------------------------------------------
# 2. Save the "new" (fixed) files so we can swap the working tree between
#    "original" and "new" states while building the two branches.
# ---------------------------------------------------------------------------
NEW_STASH="$(mktemp -d -t cmp2204_new.XXXXXX)"
echo ">>> Saving current (fixed) files to $NEW_STASH"

NEW_FILES=(
  eha_app.py
  eha_ui.py
  eha_announcer.py
  eha_discovery.py
  eha_initiator.py
  eha_responder.py
  encryption.py
  dh.py
  README.md
  requirements.txt
  .gitignore
)
for f in "${NEW_FILES[@]}"; do
  if [ -e "$f" ]; then
    cp -a "$f" "$NEW_STASH/$f"
  fi
done

# ---------------------------------------------------------------------------
# 3. Put the ORIGINAL 2024 files back into the working tree.
# ---------------------------------------------------------------------------
echo ">>> Restoring the 2024 files from $BACKUP_DIR for the 'original' branch"
# Remove the fixed versions of the files we're about to replace.
for f in "${NEW_FILES[@]}"; do
  rm -f "$f"
done
# And copy the originals in.
cp -a "$BACKUP_DIR"/. ./
# NOTE: dh.py, .gitignore don't exist in the original — that's correct.

# ---------------------------------------------------------------------------
# 4. git init on the `original` branch and commit the 2024 code.
# ---------------------------------------------------------------------------
git init -b original
git config user.email  "emreko1337@gmail.com"
git config user.name   "Emre"

# Give the original branch a .gitignore too so chat.log / venv / __pycache__
# don't get committed.
cat > .gitignore <<'EOF'
__pycache__/
*.py[cod]
venv/
.venv/
chat.log
*.log
.DS_Store
.idea/
.vscode/
EOF

# Don't commit the hidden backup dir on the original branch
echo ".original-backup/" >> .gitignore

git add -A
git commit -m "Initial snapshot: CMP2204 P2P chat project (May 2024)

This is the original submission as written for the Computer Networks
course. Encryption uses a single static Fernet key (see encryption.py);
there is no key exchange between peers. Kept on this branch for
reference; see the main branch for the 2026 rewrite." >/dev/null

# ---------------------------------------------------------------------------
# 5. Switch to a fresh `main` branch with the FIXED code.
# ---------------------------------------------------------------------------
echo ">>> Swapping to the fixed code for the 'main' branch"

# Remove the 2024 files from the working tree (git will pick up the deletion)
for f in $(ls -A "$BACKUP_DIR"); do
  rm -f "$f"
done

# Drop the backup directory from the main branch entirely.
rm -rf "$BACKUP_DIR"

# Restore the fixed files.
cp -a "$NEW_STASH"/. ./
rm -rf "$NEW_STASH"

# Create main as an orphan branch so main and original don't share history.
# Two independent branches, one per era.
git checkout --orphan main
git rm -rf --cached . >/dev/null 2>&1 || true
git add -A
git commit -m "Switch to per-message Diffie-Hellman key exchange; fix macOS UI

Changes relative to the 2024 version (see the 'original' branch):

  * Replaced the single static Fernet key (encryption.py) with per-message
    Diffie-Hellman: RFC 3526 Group 14 parameters, HKDF-SHA256 to derive a
    fresh 32-byte Fernet key for every encrypted message. Perfect forward
    secrecy — compromising one session does not leak any other.

  * New dh.py module: parameters, keypair generation, HKDF key derivation,
    base64 wire-format helpers for the public key.

  * Rewrote eha_initiator.py and eha_responder.py to run the handshake
    over newline-delimited JSON on the same TCP connection, with proper
    message framing so payloads larger than 1024 bytes (like DH public
    keys) aren't truncated.

  * Removed the broken polling loop in eha_ui.py that opened a TCP
    connection to every known peer once per second. That loop was the
    reason the UI didn't appear on macOS — it triggered the Incoming
    Connection firewall prompt every few seconds. The responder now
    pushes received messages straight into the UI via master.after().

  * macOS Tk fixes: explicit geometry, lift() + -topmost pulse at
    startup so the window pops to the front, selectcolor matched to the
    background to avoid the white-box glitch on Aqua, Enter-to-send
    bindings on the username and message entries.

  * Thread safety: the peer dictionary in eha_discovery.py is now
    protected by a lock, and every UI update from a background thread
    goes through master.after(0, ...).

  * Removed duplicate responder.py (kept only on the 'original' branch).

  * Updated README.md with architecture diagrams, the wire protocol, and
    setup notes for macOS / Linux / Windows.

  * Modernised requirements.txt (cryptography >= 42); dropped unused
    paramiko dependency." >/dev/null

# ---------------------------------------------------------------------------
# 6. Done — print next steps.
# ---------------------------------------------------------------------------
echo
echo "============================================================"
echo "Local repo ready. Branches:"
git --no-pager branch -a
echo
echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
echo
echo "Log:"
git --no-pager log --all --oneline --decorate --graph
echo
echo "============================================================"
echo "Next — push to GitHub:"
echo
echo "  1. Create an empty repo on github.com (no README, no .gitignore,"
echo "     no license) named e.g.  cmp2204-p2p-chat"
echo
echo "  2. From this folder, run:"
echo
echo "       git remote add origin git@github.com:<your-username>/cmp2204-p2p-chat.git"
echo "       # or HTTPS:"
echo "       # git remote add origin https://github.com/<your-username>/cmp2204-p2p-chat.git"
echo
echo "       git push -u origin main"
echo "       git push -u origin original"
echo
echo "  3. On GitHub, the repo page will default to 'main'. In the"
echo "     branch dropdown you can switch to 'original' to see the 2024"
echo "     code snapshot."
echo "============================================================"
