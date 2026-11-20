# Como contribuir (guia de Git e GitHub da equipe)

Este guia é para quem nunca trabalhou em equipe com Git e GitHub. Siga na ordem.

> **Por que isto importa:** o professor vai conferir no GitHub se **cada integrante fez
> pelo menos 1 commit**. Um commit só aparece com o seu nome e a sua foto se o Git estiver
> configurado com um **e-mail da sua conta GitHub** (Passo 2). Faça esse passo com calma
> e confira o resultado depois do primeiro push (Passo 11).

## Resumo do fluxo

```text
issue no Kanban ─► branch ─► commits ─► push ─► pull request ─► revisão ─► merge na main
```

1. Pegue uma issue e mova o cartão para **Em andamento**.
2. Atualize a `main` e crie uma branch para a issue.
3. Faça commits pequenos, rode os testes e dê push.
4. Abra um pull request (PR) para a `main` com `Closes #N` e peça revisão ao Sidney.
5. Depois do merge, confira se o commit aparece com a sua foto.

Repositório: https://github.com/SidneyCirinoSF/apd-validador

Quadro Kanban: aba Projects do repositório.

---

## Passo 0: aceitar o convite de colaborador

O Sidney adicionou cada um como colaborador. Sem aceitar o convite você **não consegue
dar push**.

1. Entre no GitHub com a **sua** conta.
2. Abra https://github.com/SidneyCirinoSF/apd-validador/invitations
3. Clique em **Accept invitation**.

O convite também chega por e-mail e expira em 7 dias. Se expirou, peça ao Sidney para
reenviar.

## Passo 1: instalar Git e Python

- **Git:** https://git-scm.com/downloads. No Windows, o instalador "Git for Windows"
  já traz o **Git Credential Manager**, que cuida do login no push. Pode aceitar as
  opções padrão.
- **Python 3.10 ou superior:** https://www.python.org/downloads/. No Windows, marque
  **"Add python.exe to PATH"** na primeira tela do instalador.

Confira no terminal (Git Bash, PowerShell ou o terminal do VS Code):

```bash
git --version
python --version     # precisa ser 3.10 ou maior (no Windows, também vale: py --version)
```

## Passo 2: configurar nome e e-mail no Git

O Git grava em cada commit um nome e um e-mail. **O GitHub usa o e-mail para ligar o
commit à sua conta.** Se o e-mail não estiver cadastrado na sua conta, o commit aparece
sem foto, sem link para o seu perfil e **não conta** como contribuição sua.

### 2.1 Descubra qual e-mail usar

1. Abra https://github.com/settings/emails
2. Veja a lista de e-mails da sua conta. Use um que esteja **verificado** (sem o aviso
   "Unverified"). Se estiver como não verificado, clique em reenviar a verificação e
   confirme pelo e-mail.
3. Se a opção **"Keep my email addresses private"** estiver marcada, a própria página
   mostra um endereço do tipo `12345678+seu-usuario@users.noreply.github.com`. Você pode
   usar esse endereço no Git: ele também liga o commit à sua conta. Se a opção
   **"Block command line pushes that expose my email"** estiver marcada, você **precisa**
   usar esse endereço `noreply`.

### 2.2 Configure o Git

Troque pelos seus dados (o nome pode ter espaço; mantenha as aspas):

```bash
git config --global user.name "Seu Nome"
git config --global user.email "o-email-da-sua-conta-github@exemplo.com"
```

Duas configurações que evitam dor de cabeça:

```bash
git config --global init.defaultBranch main     # repositórios novos começam em main
git config --global pull.rebase false           # "git pull" faz merge (o que este guia usa)
```

Opcional, para o Git abrir o VS Code em vez do editor Vim quando precisar de uma mensagem:

```bash
git config --global core.editor "code --wait"
```

Confira:

```bash
git config --global user.name
git config --global user.email
```

## Passo 3: autenticação para o push

Desde 2021 o GitHub **não aceita a senha da conta** no terminal. Escolha **uma** opção:

### Opção A: HTTPS com o Git Credential Manager (padrão no Windows)

Não precisa fazer nada agora. No seu primeiro `git push`, abre uma janela do navegador
pedindo para entrar no GitHub e autorizar. Depois disso o Windows guarda a credencial.

### Opção B: GitHub CLI (`gh`)

Instale em https://cli.github.com e rode:

```bash
gh auth login
```

Responda: `GitHub.com` → `HTTPS` → `Yes` (autenticar o Git com as credenciais do GitHub)
→ `Login with a web browser`. Copie o código que aparece, cole no navegador e autorize.
Confira com `gh auth status`.

## Passo 4: clonar o repositório

Escolha uma pasta (ex.: `Documentos/faculdade`) e rode:

```bash
git clone https://github.com/SidneyCirinoSF/apd-validador.git
cd apd-validador
```

Você só clona **uma vez**. Nos próximos dias, basta entrar na pasta e atualizar
(Passo 6).

## Passo 5: pegar uma tarefa no Kanban

1. Abra o repositório no GitHub → aba **Projects** → quadro da equipe.
2. Escolha uma issue da coluna **A fazer** que seja sua (veja [TAREFAS.md](TAREFAS.md)).
3. Abra a issue, clique em **Assignees** e atribua a você.
4. Arraste o cartão para **Em andamento**.
5. Anote o **número** da issue (ex.: `#4`). Ele vai no nome da branch, nas mensagens
   de commit e no PR.

### As colunas do quadro

| Coluna | Quando o cartão fica aqui | Quem move |
|---|---|---|
| **A fazer** | Tarefa ainda não começou | (estado inicial) |
| **Em andamento** | Você começou a trabalhar nela | Você, ao criar a branch |
| **Em revisão** | Você abriu o PR e está esperando revisão | Você, ao abrir o PR |
| **Concluído** | O PR foi aceito (merge) na `main` | Pode mudar sozinho quando a issue fecha pelo `Closes #N`; se não mudar, quem fez o merge move |

Para mover: arraste o cartão de uma coluna para outra, ou abra o cartão e mude o campo
**Status**. Não conte com automações do quadro: mova o cartão manualmente se ele não mudar
sozinho.

## Passo 6: atualizar a main e criar a sua branch

**Nunca trabalhe direto na `main`.** Cada issue tem a sua branch.

```bash
git switch main
git pull origin main
git switch -c feat/4-tokenizador
```

Padrão do nome da branch: `feat/<numero-da-issue>-<descricao-curta>`, tudo minúsculo,
sem acento e com hífens. Troque `feat/` por `fix/`, `docs/` ou `chore/` conforme o tipo
do trabalho. Exemplos:

| Issue | Branch |
|---|---|
| #4 Tokenizador | `feat/4-tokenizador` |
| #6 Interface de terminal (CLI) | `feat/6-cli` |
| #4 Correção na coluna do token `$` | `fix/4-coluna-marcador-fim` |
| #9 Roteiro da demonstração | `docs/9-roteiro-demo` |

> Use o número real da **sua** issue (veja [TAREFAS.md](TAREFAS.md)) e, se ela sugerir um
> nome de branch na seção "Como entregar", use esse nome.

Se o seu Git for antigo e não conhecer `git switch`, use `git checkout main` e
`git checkout -b feat/4-tokenizador`.

## Passo 7: trabalhar e commitar

Edite os arquivos da sua tarefa. Depois:

```bash
git status                       # mostra o que mudou
git add apd/tokenizador.py       # escolhe o que vai no commit
git status                       # confira: os arquivos certos estão em verde
git commit -m "feat(tokenizador): reconhece tags de abertura e fechamento (#4)"
```

Prefira `git add <arquivo>` a `git add .`, para não incluir arquivos por engano.
O `.gitignore` já impede `__pycache__`, `.venv`, `.vscode` e afins.

**Commits pequenos e frequentes:** um commit por passo lógico (ex.: "reconhece tags",
depois "ignora comentários", depois "testes de erro léxico"). Não acumule tudo para um
commit gigante no último dia.

### Padrão das mensagens de commit

Usamos **Conventional Commits em português**: `tipo(escopo): descrição (#N)`.

- Tipo em minúsculas; o escopo (opcional) é o módulo ou a área: `modelos`, `automato`,
  `tokenizador`, `diagnostico`, `cli`, `gui`, `exemplos`, `demo`, `apresentacao`...
  Depois, dois-pontos e espaço.
- Descrição em português, começando com verbo no presente (`adiciona`, `corrige`,
  `remove`), letra minúscula, sem ponto final, com até uns 72 caracteres.
- O número da issue entre parênteses no fim é recomendado, mas opcional: o vínculo oficial
  com a issue é o `Closes #N` (ou `Parte de #N`) do PR.

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Funcionalidade nova | `feat(automato): adiciona a classe APD com execução passo a passo (#2)` |
| `feat` | | `feat(tokenizador): ignora comentários <!-- --> no XML (#4)` |
| `feat` | | `feat(cli): adiciona a opção --passo (#6)` |
| `fix` | Correção de erro | `fix(tokenizador): corrige a coluna do marcador $ no fim da fita (#4)` |
| `fix` | | `fix(diagnostico): aponta o fechamento esperado a partir de δ (#5)` |
| `docs` | Só documentação | `docs(demo): adiciona o roteiro da demonstração ao vivo (#9)` |
| `test` | Só testes | `test(diagnostico): cobre fechamento incompatível com o topo da pilha (#5)` |
| `refactor` | Reorganiza sem mudar o comportamento | `refactor(tokenizador): extrai a leitura do nome da tag para uma função (#4)` |
| `chore` | Manutenção (integração, configuração) | `chore: adiciona .gitignore (#11)` |

Mensagens que **não** usamos: `update`, `ajustes`, `aaa`, `versão final agora vai`.

## Passo 8: rodar os testes antes do PR

Na raiz do repositório:

```bash
python -m unittest discover -s tests -v
```

Todos precisam passar (`OK` no final). Se um teste de outra pessoa quebrou por causa
da sua mudança, corrija antes de abrir o PR ou avise no PR.

## Passo 9: enviar a branch (push)

Na primeira vez, com `-u` para ligar a sua branch local à do GitHub:

```bash
git push -u origin feat/4-tokenizador
```

Nas próximas vezes, na mesma branch, basta `git push`.

## Passo 10: abrir o pull request

### Pelo site

1. Abra o repositório no GitHub. Vai aparecer o aviso da sua branch com o botão
   **Compare & pull request**. (Ou: aba **Pull requests** → **New pull request**.)
2. Confira: **base: `main`** ← **compare: `feat/4-tokenizador`**.
3. Título: o mesmo da issue, no formato `[Área] Descrição`:
   `[Tokenizador] Texto para fita de tokens (apd/tokenizador.py)`.
4. Na descrição, escreva o que foi feito, como testar e, **numa linha própria**:

   ```text
   Closes #4
   ```

   Isso liga o PR à issue e fecha a issue automaticamente no merge.
5. Em **Reviewers**, escolha **SidneyCirinoSF**.
6. Clique em **Create pull request**.
7. No Kanban, mova o cartão para **Em revisão**.

### Pelo terminal (se você usa `gh`)

```bash
gh pr create --base main --title "[Tokenizador] Texto para fita de tokens (apd/tokenizador.py)" \
  --body "Implementa tokenizar_xml e tokenizar_expressao conforme ARQUITETURA.md §8.

Closes #4" --reviewer SidneyCirinoSF
```

### Durante a revisão

- Se o Sidney pedir ajustes, faça na **mesma branch**, commite e dê `git push`.
  O PR se atualiza sozinho; não abra outro PR.
- Quem faz o merge é o Sidney, depois de aprovar. Para que o commit de cada pessoa
  continue visível no histórico, o merge é feito com **"Create a merge commit"**.

## Passo 11: conferir se o seu commit conta

Depois do push (e de novo depois do merge):

1. Abra a lista de commits: na página do PR, aba **Commits**; ou, depois do merge,
   https://github.com/SidneyCirinoSF/apd-validador/commits/main
2. Ao lado do seu commit deve aparecer **a sua foto e o seu usuário com link** para
   o seu perfil.
3. Se aparecer um ícone cinza genérico e o nome sem link, o e-mail do commit não está
   ligado à sua conta. Veja "Commit sem avatar" em [Problemas comuns](#problemas-comuns).

Para ver no terminal qual nome e e-mail foram usados no último commit:

```bash
git log -1 --format="%an <%ae>"
```

A contribuição aparece no gráfico do seu perfil quando o commit chega à `main` (depois
do merge), e pode levar alguns minutos.

## Passo 12: depois do merge

```bash
git switch main
git pull origin main
git branch -d feat/4-tokenizador     # apaga a branch local que já foi incorporada
```

Confira se o cartão está em **Concluído**; mova o cartão manualmente se ele não mudar
sozinho. Para a próxima tarefa, volte ao Passo 5.

---

## Atualizar a sua branch com a main

Se a `main` recebeu mudanças enquanto você trabalhava (outro PR foi aceito), traga essas
mudanças para a sua branch:

```bash
git status                     # precisa estar limpo: commite antes o que estiver pendente
git pull origin main           # estando na SUA branch
```

Se não houver conflito, o Git cria um commit de merge (pode abrir um editor com a
mensagem pronta: salve e feche). Depois, `git push`.

### Resolver um conflito básico

Conflito acontece quando você e outra pessoa mudaram as mesmas linhas. O Git avisa:

```text
CONFLICT (content): Merge conflict in apd/cli.py
Automatic merge failed; fix conflicts and then commit the result.
```

Abra o arquivo. O trecho em conflito fica assim:

```text
<<<<<<< HEAD
    print("Resultado: ACEITA")
=======
    print(f"Resultado: ACEITA (estado {estado} ∈ F)")
>>>>>>> 3f9c2ab
```

- Entre `<<<<<<< HEAD` e `=======`: a versão da **sua** branch.
- Entre `=======` e `>>>>>>>`: a versão que veio da **main**.

Para resolver:

1. Edite deixando o código como deve ficar (uma versão, a outra ou a combinação das duas).
2. **Apague as três linhas de marcação** (`<<<<<<<`, `=======`, `>>>>>>>`).
   No VS Code, os botões *Accept Current*, *Accept Incoming* e *Accept Both* fazem isso.
3. Rode os testes.
4. Finalize:

   ```bash
   git add apd/cli.py
   git commit                   # a mensagem de merge já vem pronta; salve e feche
   git push
   ```

Se ficar perdido no meio do conflito, `git merge --abort` desfaz a tentativa e volta a
branch para como estava. Depois peça ajuda no grupo.

---

## Regras da equipe

1. **Cada um commita do próprio computador e com a própria conta GitHub.** É assim que o
   professor vê a participação de cada integrante.
2. **Ninguém commita pelo outro.** Nada de mandar o código para um colega subir. Se
   alguém estiver com problema no Git, ajude a resolver a configuração dele.
3. **Commits pequenos e frequentes**, com mensagens no padrão acima.
4. **Nunca trabalhe direto na `main`** e **nunca dê `git push --force` na `main`.**
5. **Rode os testes antes de abrir o PR.**
6. **Todo código entra por pull request**, com `Closes #N` e revisão do Sidney.
7. **Mudança de contrato** (nomes, assinaturas e convenções de
   [ARQUITETURA.md](ARQUITETURA.md)) só depois de abrir uma issue com o rótulo
   `contrato` e avisar o grupo.
8. **Mantenha o Kanban em dia:** o cartão sempre na coluna que representa a situação real.

## Padrões de código

- **Python 3.10+, somente biblioteca padrão.** Nada de `pip install`. Os principais módulos
  usados estão em [ARQUITETURA.md](ARQUITETURA.md) §3; qualquer outro módulo da biblioteca
  padrão (ex.: `tempfile`, `subprocess` nos testes) também vale.
- **Nomes em português**: variáveis, funções, classes e comentários
  (`tokenizar_xml`, `estado_inicial`, `class Configuracao`). Nos identificadores, sem
  acento e sem cedilha (`configuracao`, `posicao`, `acao`); nos comentários e docstrings,
  português normal com acento.
- **Docstrings ligando o código à teoria** em toda função pública. Exemplo (o nome da
  função é só ilustrativo; os nomes oficiais estão em [ARQUITETURA.md](ARQUITETURA.md)):

  ```python
  def aplicar(self, transicao: Transicao) -> Configuracao:
      """Aplica δ(q, a, X) = (p, γ): vai para o estado p e troca o topo X por γ.

      γ = () significa desempilhar; γ = (Y, X) significa empilhar Y.
      """
  ```

- **Siga as convenções formais** de [ARQUITETURA.md](ARQUITETURA.md) §4: ε é `None`,
  `pilha[0]` é o topo, a fita termina em `"$"`.
- **Interfaces só exibem**: `cli.py` e `gui.py` chamam `tokenizar` e `APD.executar` e
  mostram o `Resultado`. Não reimplemente δ fora de `automato.py`.
- **Testes com `unittest`**, na pasta `tests/`, um arquivo por módulo
  (`tests/test_tokenizador.py`, `tests/test_automato.py`...):

  ```python
  import unittest

  from apd.tokenizador import tokenizar_expressao


  class TestTokenizarExpressao(unittest.TestCase):
      def test_fita_termina_com_marcador_de_fim(self):
          fita = tokenizar_expressao("(2+3)")
          self.assertEqual([t.simbolo for t in fita], ["(", "x", ")", "$"])


  if __name__ == "__main__":
      unittest.main()
  ```

---

## Problemas comuns

### Commit sem avatar (ícone cinza, nome sem link, não conta no perfil)

O e-mail gravado no commit não está ligado à sua conta GitHub.

1. Veja qual e-mail foi usado: `git log -1 --format="%an <%ae>"`.
2. Compare com https://github.com/settings/emails.
3. **Solução mais simples:** adicione **esse mesmo e-mail** à sua conta em
   https://github.com/settings/emails e verifique-o. O GitHub passa a reconhecer
   inclusive os commits antigos feitos com ele.
4. Ou corrija a configuração (Passo 2) para os **próximos** commits e faça um commit
   novo. O commit antigo continua sem avatar, mas o novo conta.

### Permissão negada no push (`403` ou `Permission ... denied to <usuario>`)

```text
remote: Permission to SidneyCirinoSF/apd-validador.git denied to fulano.
fatal: unable to access '...': The requested URL returned error: 403
```

- Você ainda **não aceitou o convite** (Passo 0). Aceite e tente de novo.
- O Windows guardou o login de **outra conta** (por exemplo, a de um colega que usou o
  computador). Abra **Painel de Controle → Gerenciador de Credenciais → Credenciais do
  Windows**, remova a entrada `git:https://github.com` e dê push de novo para entrar com
  a sua conta. Com `gh`, rode `gh auth login` novamente.
- O nome no erro mostra **qual conta** o Git usou; confira se é a sua.

### Conflito de merge

Veja [Resolver um conflito básico](#resolver-um-conflito-básico). Na dúvida,
`git merge --abort` e peça ajuda.

### `error: src refspec main does not match any`

O Git não encontrou uma branch local com o nome que você mandou enviar. Causas comuns:

- Você está tentando dar push de uma branch com outro nome. Rode `git branch` para ver
  o nome da sua branch (a marcada com `*`) e use esse nome:
  `git push -u origin feat/4-tokenizador`.
- Você ainda **não fez nenhum commit** nessa branch. Faça `git add` e `git commit`
  primeiro.
- Erro de digitação no nome da branch.

Lembre: o seu push deve ser da **sua branch**, nunca da `main`.

### `Please tell me who you are` ao commitar

Falta o Passo 2. Configure `user.name` e `user.email` e tente o commit de novo.

### `rejected ... (fetch first)` ou `non-fast-forward` no push

A branch no GitHub tem commits que você não tem localmente (por exemplo, você ajustou
algo pelo site). Rode `git pull origin <sua-branch>` e depois `git push`. **Não use
`--force`.**

### `You have divergent branches and need to specify how to reconcile them`

Falta a configuração `git config --global pull.rebase false` (Passo 2). Rode e repita o
`git pull`.

### Abriu uma tela estranha no terminal ao fazer merge (editor Vim)

É o editor pedindo a mensagem do commit de merge, que já vem pronta. Digite `:wq` e
Enter para salvar e sair. Para usar o VS Code no lugar, veja o Passo 2.

### Fiz commits na main sem querer (ainda não dei push)

```bash
git branch feat/4-tokenizador        # cria a branch guardando os seus commits
git switch feat/4-tokenizador        # continua o trabalho nela
```

A `main` local ainda fica com esses commits. Antes de mexer nela, peça ajuda ao Sidney
para limpá-la com segurança. **Não dê push da main.**
