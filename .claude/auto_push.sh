#!/usr/bin/env bash
# Hook executado pelo Claude Code após cada edição de arquivo.
# Faz commit e push automático para o GitHub se houver alterações.

REPO=/Users/yuri/Projetos_Cloude/ProjetoClaudeCode_1/stock_analyzer
GH=/Users/yuri/.local/bin/gh
export PATH="$PATH:/usr/bin:/usr/local/bin:/Users/yuri/.local/bin"

cd "$REPO" || exit 0

# Ignora se não for um repositório git
git rev-parse --is-inside-work-tree &>/dev/null || exit 0

# Verifica se há algo para commitar
git add -A
if git diff --cached --quiet; then
  exit 0
fi

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
git commit -m "auto: atualização automática $TIMESTAMP" --no-verify &>/dev/null

git push origin main &>/dev/null

exit 0
