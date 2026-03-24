# Guia de Contribuição - WGI (Web Gesture Interpreter)

Este documento estabelece as diretrizes para garantir que o desenvolvimento do nosso interpretador de gestos seja organizado, documentado e integrado ao nosso fluxo no Jira.

## Fluxo de Trabalho (Git Flow)

Para manter a `main` estável, **nenhum código deve ser enviado diretamente para ela**. Siga os passos:

1. **Sincronização:** Garanta que sua `main` local está atualizada (`git pull origin main`).
2. **Branch:** Crie uma branch a partir da chave da tarefa no Jira:
   - Funcionalidades: `feature/IIDGW-XX-nome-breve`
   - Correções: `bugfix/IIDGW-XX-descricao-erro`
   - Documentação: `docs/IIDGW-XX-descricao`
3. **Desenvolvimento:** Realize suas alterações e commits.
4. **Pull Request (PR):** Abra um PR para a `main` solicitando a revisão de pelo menos um colega.

## Padrões de Commits e Integração Jira

A integração entre GitHub e Jira depende das chaves das tarefas (**IIDGW-XX**). Sem a chave, a tarefa não será atualizada automaticamente no board.

- **Formato Sugerido:** `CHAVE-XX: Descrição curta e clara (em português ou inglês)`
- **Exemplo:** `IIDGW-18: Implementando integração inicial com MediaPipe Hands`

## Processo de Revisão (Pull Request)

Ao abrir um Pull Request:
1. Descreva brevemente **o que** foi feito.
2. Mencione a **tarefa do Jira** correspondente.
3. Aguarde a aprovação de um par antes de realizar o **Merge**.

---
*Este CONTRIBUTING.md foi realizado com auxílio do Gemini.*
