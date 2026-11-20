# Tarefas e cronograma

Divisão do trabalho da AV2 (Desafio 4) em **11 issues** no GitHub, a ordem em que elas
precisam ficar prontas e quem faz o quê. Os detalhes de cada tarefa (passo a passo,
especificação, testes e como entregar) estão **na própria issue**; este arquivo é o mapa geral.

- **Apresentação:** quinta-feira, **03/12/2026**, com slides no Prezi.
- **Contrato técnico:** [ARQUITETURA.md](ARQUITETURA.md) (nomes, assinaturas e convenções).
- **Definição formal:** [DEFINICAO_FORMAL.md](DEFINICAO_FORMAL.md).
- **Como usar Git e GitHub no grupo:** [CONTRIBUINDO.md](CONTRIBUINDO.md).
- **Quadro Kanban:** aba Projects do repositório.

> ## ⚠️ Regra obrigatória: todos precisam ter commits
>
> O professor vai verificar no GitHub se **cada integrante fez pelo menos 1 commit**. Por isso
> cada pessoa tem entregas em **arquivos próprios** (o que também evita conflitos de merge).
>
> - Configure o Git com o **mesmo e-mail da sua conta GitHub** antes do primeiro commit
>   (`git config --global user.email "..."`; confira em GitHub → Settings → Emails). Commit com
>   outro e-mail **não aparece** em Insights → Contributors.
> - Faça commits **você mesmo**, na sua máquina, na sua branch. Ninguém commita pelo colega.
> - Os PRs entram com **"Create a merge commit"** (não "Squash"), para preservar os commits de cada um.
> - Na integração final (#11) o Sidney confere em **Insights → Contributors** que os 5 aparecem.

## Issues

| Nº | Título | Responsável | Prazo | Depende de |
|---|---|---|---|---|
| #1 | [Núcleo] Contratos de dados (`apd/modelos.py`) | Sidney (@SidneyCirinoSF) | dom 22/11 | nada (**bloqueante**) |
| #2 | [Núcleo] Classe APD e carregador (`apd/automato.py`, `apd/carregador.py`) | Sidney (@SidneyCirinoSF) | qui 26/11 | #1 (integra o #5) |
| #3 | [Autômatos] Gerador e definições JSON dos dois APDs | Joalison (@Joalison7) | qua 25/11 | nada |
| #4 | [Tokenizador] Texto para fita de tokens (`apd/tokenizador.py`) | Pedro Valença (@PedroValencav2) | qua 25/11 | #1 |
| #5 | [Núcleo] Diagnóstico das rejeições (`apd/diagnostico.py`) | Pedro Valença (@PedroValencav2) | sex 27/11 | #1, #2 (interface do APD) |
| #6 | [Interface] CLI com menu e passo a passo (`apd/cli.py`) | Fabrício (@Cibr0) | sáb 28/11 | #1, #2, #4 (#5 para as mensagens) |
| #7 | [Testes] Exemplos e teste ponta a ponta | Fabrício (@Cibr0) | dom 29/11 | #2, #3, #4, #5 |
| #8 | [Interface] GUI tkinter com fita, pilha e tabela δ (`apd/gui.py`) | Wagner Daniel (@WagnerDaniell) | dom 29/11 | #1, #2, #4 |
| #9 | [Documentação] Roteiro da demonstração ao vivo | Wagner Daniel (@WagnerDaniell) | seg 30/11 | #6, #7, #8 |
| #10 | [Apresentação] Prezi e `docs/APRESENTACAO.md` | Joalison (@Joalison7) + **todos** | ter 01/12 | nada para começar; conteúdo de #3, #6, #8, #9 |
| #11 | [Integração] Revisão final, README e release v1.0 | Sidney (@SidneyCirinoSF) | qua 02/12 | #1 a #10 |

"Depende de" não significa "esperar parado": quase todas as tarefas podem começar já, usando
o contrato do ARQUITETURA.md e dados montados à mão. Cada issue explica como.

## Diagrama de dependências

```mermaid
graph LR
    I1["#1 Contratos<br/>Sidney · 22/11"]
    I2["#2 Núcleo APD<br/>Sidney · 26/11"]
    I3["#3 Gerador e JSON<br/>Joalison · 25/11"]
    I4["#4 Tokenizador<br/>Pedro · 25/11"]
    I5["#5 Diagnóstico<br/>Pedro · 27/11"]
    I6["#6 CLI<br/>Fabrício · 28/11"]
    I7["#7 Exemplos e integração<br/>Fabrício · 29/11"]
    I8["#8 GUI<br/>Wagner · 29/11"]
    I9["#9 Roteiro da demo<br/>Wagner · 30/11"]
    I10["#10 Prezi<br/>Joalison + todos · 01/12"]
    I11["#11 Integração e v1.0<br/>Sidney · 02/12"]

    I1 --> I2
    I1 --> I4
    I1 --> I5
    I1 --> I6
    I1 --> I8
    I2 -->|interface do APD| I5
    I5 -.->|substitui o diagnóstico provisório| I2
    I2 --> I6
    I2 --> I7
    I2 --> I8
    I3 --> I7
    I4 --> I6
    I4 --> I7
    I4 --> I8
    I5 --> I7
    I6 --> I9
    I7 --> I9
    I8 --> I9
    I9 --> I10
    I3 --> I10
    I10 --> I11
    I9 --> I11
    I7 --> I11

    classDef bloqueante fill:#ffd6d6,stroke:#c00,color:#000
    class I1,I2 bloqueante
```

Caminho crítico: **#1 → #2 → #5 → #7 → #9 → #11**. Atraso em qualquer uma delas atrasa o grupo todo.

## Cronograma (20/11 a 03/12)

| Dia | Data | O que acontece | Marco |
|---|---|---|---|
| sex | 20/11 | Issues publicadas. Todos aceitam o convite, configuram o Git e leem ARQUITETURA.md e CONTRIBUINDO.md. Joalison começa o #3; Pedro começa o #4; Fabrício começa os arquivos de exemplo (#7); Wagner esboça a GUI (#8) | |
| sáb | 21/11 | Sidney abre o PR do #1. Fabrício e Wagner começam as funções puras (formatação da CLI, `NavegadorPassos`) com dados montados à mão | |
| dom | 22/11 | Merge do #1. Todos dão `git pull` | **Contratos prontos** |
| seg | 23/11 | Sidney no #2; Pedro no #4; Joalison no #3; Fabrício abre PR parcial dos exemplos (`Parte de #7`) | |
| ter | 24/11 | Desenvolvimento; dúvidas de contrato vão para comentários nas issues | |
| qua | 25/11 | PRs do #3 (JSON) e do #4 (tokenizador) | Autômatos e tokenizador prontos |
| qui | 26/11 | Merge do #2. Pedro troca o `APDFalso` pelo `APD` real nos testes do #5 | **Núcleo pronto** |
| sex | 27/11 | PR do #5 (diagnóstico). Joalison compartilha o Prezi e cria o `APRESENTACAO.md` (#10) | |
| sáb | 28/11 | PR do #6 (CLI). Sidney remove o diagnóstico provisório | |
| dom | 29/11 | PRs do #7 (exemplos e integração) e do #8 (GUI) | **Interfaces prontas** |
| seg | 30/11 | PR do #9 (roteiro). Todos preenchem a sua seção no Prezi e as falas no `APRESENTACAO.md` | |
| ter | 01/12 | Prezi final (#10). Depois disso só correção de bug e documentação | **Congelamento do código** |
| qua | 02/12 | Ensaio geral cronometrado no notebook do projetor (ou ter 01/12 à noite). Tag `v1.0` e release (#11) | **Ensaio** |
| qui | 03/12 | Apresentação | **Apresentação** |

## Quem faz o quê

| Integrante | Issues | Arquivos próprios (commits garantidos) | Seção no Prezi |
|---|---|---|---|
| **Sidney** (@SidneyCirinoSF), líder | #1, #2, #11 | `apd/__init__.py`, `apd/modelos.py`, `apd/automato.py`, `apd/carregador.py`, `tests/test_modelos.py`, `tests/test_automato.py`, `tests/test_carregador.py`, `README.md` | 1. Abertura e por que um AFD não basta; 7. Conclusão e limitações |
| **Joalison** (@Joalison7) | #3, #10 | `ferramentas/gerar_automatos.py`, `automatos/xml_tags.json`, `automatos/expressoes.json`, `tests/test_automatos_json.py`, `docs/APRESENTACAO.md` | 2. Definição formal e diagrama; montagem do Prezi |
| **Pedro Valença** (@PedroValencav2) | #4, #5 | `apd/tokenizador.py`, `apd/diagnostico.py`, `tests/test_tokenizador.py`, `tests/test_diagnostico.py` | 3. Do texto à fita; 4. Diagnóstico das rejeições |
| **Fabrício** (@Cibr0) | #6, #7 | `apd/cli.py`, `apd/__main__.py`, `tests/test_cli.py`, `exemplos/`, `tests/test_integracao.py` | 6. Demonstração ao vivo na CLI e casos de erro |
| **Wagner Daniel** (@WagnerDaniell) | #8, #9 | `apd/gui.py`, `tests/test_gui_navegacao.py`, `docs/ROTEIRO_DEMO.md` | 5. Zoom na pilha: crescimento e esvaziamento em paralelo à fita |

Além disso, **todos** adicionam as próprias falas em `docs/APRESENTACAO.md` por PR (#10).

Revisão e merge dos PRs: **Sidney**. Os PRs do Sidney são revisados por outro integrante.

## Como cada tarefa é entregue (resumo)

1. Mover o cartão da issue para **Em andamento** no Kanban.
2. `git checkout main && git pull && git checkout -b feat/N-descricao` (ou `docs/N-...`,
   `fix/N-...`, `chore/N-...`, conforme o tipo).
3. Commits pequenos, em pt-BR, no padrão Conventional Commits:
   `feat(tokenizador): ...`, `test(cli): ...`, `docs(exemplos): ...`.
4. `git push -u origin feat/N-descricao` e abrir o Pull Request para a `main`, com o título da
   issue e `Closes #N` na descrição (ou `Parte de #N` se for um PR parcial).
5. Pedir revisão do **@SidneyCirinoSF** e mover o cartão para **Em revisão**.
6. O merge é feito com **"Create a merge commit"**. Depois dele, a issue fecha pelo `Closes #N`
   e o cartão deve ir para **Concluído**; mova o cartão manualmente se ele não mudar sozinho.

Passo a passo completo, com os comandos: [CONTRIBUINDO.md](CONTRIBUINDO.md) e a seção
"Como entregar" de cada issue.

## Convenções que todas as issues seguem

Resumo do [ARQUITETURA.md](ARQUITETURA.md) §3 e §4 (em caso de dúvida, vale o ARQUITETURA.md):

- Python 3.10+, **só biblioteca padrão**; nomes, comentários e docstrings em português.
- ε = `None` (Python) / `null` (JSON); **topo da pilha = `pilha[0]`**; `empilha[0]` vira o novo topo;
  `()` = desempilhar; `"$"` é sempre o último token da fita; aceitação **por estado final**.
- Testes com `unittest`: `python -m unittest discover -s tests -v`.
- CLI e GUI **só reexibem** `Resultado.passos`; a única implementação de δ é `APD.executar`.
