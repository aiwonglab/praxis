#!/usr/bin/env bash
# praxis setup — register clinical research skills with Claude Code
#
# Install globally (recommended):
#   git clone https://github.com/aiwonglab/praxis.git ~/.claude/skills/praxis
#   cd ~/.claude/skills/praxis && bash scripts/setup.sh
#
# Install to a single project:
#   cp -Rf ~/.claude/skills/praxis .claude/skills/praxis
#   cd .claude/skills/praxis && bash scripts/setup.sh
#
set -e

PRAXIS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$(dirname "$PRAXIS_DIR")"
SKILLS_BASENAME="$(basename "$SKILLS_DIR")"

echo "praxis setup"
echo "  source: $PRAXIS_DIR"

# ─── 1. Link skill directories into the skills parent ───────────────
if [ "$SKILLS_BASENAME" = "skills" ]; then
  linked=()
  for skill_dir in "$PRAXIS_DIR"/plan-*/; do
    if [ -f "$skill_dir/SKILL.md" ]; then
      skill_name="$(basename "$skill_dir")"
      target="$SKILLS_DIR/$skill_name"
      if [ -L "$target" ] || [ ! -e "$target" ]; then
        ln -snf "praxis/$skill_name" "$target"
        linked+=("$skill_name")
      fi
    fi
  done
  if [ ${#linked[@]} -gt 0 ]; then
    echo "  linked skills: ${linked[*]}"
  else
    echo "  skills already linked"
  fi
else
  echo "  (skipped skill symlinks — not inside .claude/skills/)"
  echo "  to enable: move or clone praxis into ~/.claude/skills/praxis"
fi

# ─── 2. Check Python environment ────────────────────────────────────
if command -v uv >/dev/null 2>&1; then
  echo "  uv: $(uv --version)"
else
  echo "  warning: uv not found — install it: https://docs.astral.sh/uv/"
fi

# ─── 3. Done ────────────────────────────────────────────────────────
echo ""
echo "praxis ready."
echo ""
echo "Available skills:"
for skill_dir in "$PRAXIS_DIR"/plan-*/; do
  if [ -f "$skill_dir/SKILL.md" ]; then
    echo "  /$(basename "$skill_dir")"
  fi
done
echo ""
echo "Add this to your project's CLAUDE.md:"
echo ""
echo '  ## praxis'
echo '  Clinical research skills from praxis. Available skills:'
echo '  /plan-pi-review, /plan-ds-review, /plan-ai-review, /plan-clinical-review'
echo '  See ETHOS.md for foundational principles.'
