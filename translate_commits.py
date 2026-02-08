#!/usr/bin/env python3
import sys
import os

filepath = sys.argv[1]
with open("/tmp/debug_git.log", "a") as f:
    f.write(f"Processing: {filepath}\n")

try:
    # If we are in sequence editor (git-rebase-todo), replace pick with reword
    if "git-rebase-todo" in str(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace all 'pick' with 'reword' for lines that contain commit hashes
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith('pick '):
                new_lines.append(line.replace('pick ', 'reword ', 1))
            else:
                new_lines.append(line)
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(new_lines) + '\n')
        
        sys.exit(0)

    # If we are editing COMMIT_EDITMSG
    with open(filepath, 'r') as f:
        original_msg = f.read().strip()
    
    with open("/tmp/debug_git.log", "a") as f:
        f.write(f"Original msg: {original_msg[:50]}...\n")

    # Check first line only for mapping
    first_line = original_msg.split('\n')[0]

    mapping = {
        "feat: introduce a tabbed ToolsPanel": "feat: introduz painel de Ferramentas com abas no Dock de Biblioteca para ferramentas de criação de itens e blocos.",
        "refactor: Connect `itemAdded`": "refactor: conecta sinais de cena `itemAdded` e `itemRemoved` a manipuladores específicos.",
        "fix: Make alignment guides red": "fix: torna guias de alinhamento vermelhas e mais espessas, melhora precisão da grade com coordenadas float e adiciona logs/tratamento de erros na criação de itens.",
        "feat: Implement internationalization": "feat: implementa internacionalização para menus e ações, e adiciona seleção de idioma.",
        "feat: expand codebase and API": "feat: expande documentação da codebase e API com arquitetura detalhada e descrições de componentes.",
        "feat: ignore .agent/ directory": "feat: ignora diretório .agent/ no .gitignore",
        "fix: resolve editor stability issues": "fix: resolve problemas de estabilidade do editor e bugs na funcionalidade de snap"
    }

    new_msg = original_msg

    for k, v in mapping.items():
        if first_line.startswith(k):
            new_msg = v
            break

    if new_msg != original_msg:
        with open(filepath, 'w') as f:
            f.write(new_msg + "\n")
        with open("/tmp/debug_git.log", "a") as f:
            f.write(f"Replaced with: {new_msg[:50]}...\n")

except Exception as e:
    with open("/tmp/debug_git.log", "a") as f:
        f.write(f"Error: {e}\n")
    sys.exit(1)
