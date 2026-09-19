#!/bin/sh
# Install the email/credential guard for EVERY repo on this machine, not just
# this one. Run once:
#
#     sh tools/protect-email.sh
#
# What it does:
#   1. Sets your global commit identity to your GitHub noreply address, so a
#      fresh clone anywhere can't default back to a personal address.
#   2. Installs .githooks/pre-commit as a GLOBAL hook via core.hooksPath.
#
# Caveat worth knowing: core.hooksPath is global, so a project that installs
# its own hooks (husky, pre-commit, lefthook) will have them bypassed. The hook
# chains to a repo's own .git/hooks/pre-commit and .githooks/pre-commit to
# soften that, but if you live in husky repos, install per-repo instead:
#     git config core.hooksPath .githooks
set -eu

NOREPLY="${1:-270181089+yhtomitn64@users.noreply.github.com}"
DEST="${HOME}/.githooks"

git config --global user.email "$NOREPLY"
git config --global user.name "$(git config --global user.name || echo yhtomitn64)"

mkdir -p "$DEST"
cp "$(dirname "$0")/../.githooks/pre-commit" "$DEST/pre-commit"
chmod +x "$DEST/pre-commit"
git config --global core.hooksPath "$DEST"

echo "Global commit email : $(git config --global user.email)"
echo "Global hooks path   : $(git config --global core.hooksPath)"
echo
echo "Still do this in the GitHub web UI - it is the only layer that can stop a"
echo "push from a machine you forgot to set up:"
echo "  Settings -> Emails -> [x] Keep my email address private"
echo "                       [x] Block command line pushes that expose my email"
