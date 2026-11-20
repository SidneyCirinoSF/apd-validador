# Arquitetura e contratos do projeto

Este documento é o **contrato** entre os módulos. Cada integrante implementa o seu
módulo seguindo exatamente os nomes, assinaturas e convenções abaixo; assim todos
podem trabalhar em paralelo sem esperar o código dos outros.

> Se algo aqui precisar mudar, abra uma issue com o rótulo `contrato` e avise o grupo
> **antes** de alterar o código: uma mudança de contrato quebra o trabalho dos colegas.

## 1. Visão geral do fluxo

```
texto de entrada ──► tokenizador ──► fita (lista de Token, termina em "$")
                                          │
automatos/*.json ──► carregador ──► APD ──┤ APD.executar(fita)
                                          ▼
                                    Resultado (passos + aceita/rejeita + Falha)
                                          │
                       ┌──────────────────┴──────────────────┐
                       ▼                                     ▼
                 apd/cli.py (terminal)                 apd/gui.py (tkinter)
```

- O **tokenizador** transforma texto bruto (XML ou expressão) na **fita de entrada**:
  uma sequência de símbolos do alfabeto Σ.
- O **carregador** lê a definição formal M = (Q, Σ, Γ, δ, q0, Z0, F) de um arquivo JSON,
  valida e devolve um objeto `APD`.
- O **APD** executa a fita, um passo de cada vez, e registra cada movimento
  (configuração antes ⊢ configuração depois).
- Quando o APD trava, o **diagnóstico** explica o motivo exato da rejeição.
- As **interfaces** (CLI e GUI) apenas **reexibem** os passos registrados no `Resultado`.
  Elas **nunca** reimplementam a lógica de δ.

## 2. Estrutura de pastas

```
apd-validador/
├── README.md
├── docs/                      documentação (este arquivo, definição formal etc.)
├── apd/                       pacote Python principal
│   ├── __init__.py
│   ├── __main__.py            ponto de entrada: python -m apd        (Fabrício)
│   ├── modelos.py             dataclasses e exceções (contratos)      (Sidney)
│   ├── automato.py            classe APD e execução                    (Sidney)
│   ├── carregador.py          leitura e validação dos JSON             (Sidney)
│   ├── tokenizador.py         texto → fita de tokens                   (Pedro)
│   ├── diagnostico.py         motivo exato da rejeição                 (Pedro)
│   ├── cli.py                 interface de terminal                    (Fabrício)
│   └── gui.py                 interface gráfica tkinter                (Wagner)
├── automatos/
│   ├── xml_tags.json          APD das tags XML/HTML                    (Joalison)
│   └── expressoes.json        APD de ( ) [ ] { }                       (Joalison)
├── ferramentas/
│   └── gerar_automatos.py     gera os JSON a partir da definição       (Joalison)
├── exemplos/
│   ├── xml/                   entradas válidas e inválidas             (Fabrício)
│   └── expressoes/
└── tests/                     testes com unittest (biblioteca padrão)
```

## 3. Regras técnicas

- **Python 3.10 ou superior** (usamos `X | None` nas anotações de tipo).
- **Somente a biblioteca padrão**: `json`, `dataclasses`, `enum`, `argparse`, `tkinter`,
  `unittest`, `pathlib`, `os`, `sys`, `time`. Nada de `pip install`.
- Nomes de variáveis, funções e comentários **em português**.
- Toda função pública tem *docstring* ligando o código à teoria (por exemplo:
  "Aplica δ(q, a, X) = (p, γ): troca o topo X pela cadeia γ").
- Testes com `unittest`. Para rodar todos: `python -m unittest discover -s tests -v`.
- Rodar o programa: `python -m apd` (terminal) ou `python -m apd --gui` (janela).

## 4. Convenções formais (valem para todos os módulos)

| Conceito | Convenção no código |
|---|---|
| ε (palavra vazia) | `None` em Python; `null` no JSON |
| Topo da pilha | **primeiro** elemento: `pilha[0]` é o topo, `pilha[-1]` é o fundo (Z0) |
| γ em δ(q, a, X) = (p, γ) | tupla `empilha`; `empilha[0]` vira o **novo topo**; `()` significa só desempilhar |
| Marcador de fim de entrada | símbolo `"$"`, sempre o último token da fita (constante `MARCADOR_FIM`) |
| Símbolo inicial da pilha | `"Z0"`, que nunca é desempilhado nos nossos autômatos |
| Critério de aceitação | **por estado final**: aceita se, após consumir a fita inteira (incluindo `$`), o estado atual ∈ F |

Exemplo: δ(q0, `<div>`, BODY) = (q0, DIV BODY) significa: "no estado q0, lendo `<div>`
com BODY no topo, vá para q0 e troque BODY por DIV BODY", ou seja, **empilha DIV**.

### Por que o marcador `$`?

Um APD **determinístico** não pode ter, no mesmo estado e com o mesmo topo, uma
ε-transição e uma transição que lê um símbolo. Para saber que a entrada acabou sem usar
ε, o tokenizador acrescenta `$` ao fim da fita. Assim a transição de aceitação
δ(q0, `$`, Z0) = (qf, Z0) só acontece no fim **e** com a pilha vazia (só Z0). Se chegar
`$` e o topo não for Z0, sabemos exatamente o erro: "pilha não vazia ao fim da entrada".

## 5. Contratos de dados: `apd/modelos.py`

```python
from dataclasses import dataclass
from enum import Enum

MARCADOR_FIM = "$"
EPSILON = None  # ε


@dataclass(frozen=True)
class Transicao:
    """δ(origem, le, topo) = (destino, empilha)."""
    origem: str
    le: str | None              # None = ε (não consome entrada)
    topo: str
    destino: str
    empilha: tuple[str, ...]    # empilha[0] = novo topo; () = desempilhar

    def __str__(self) -> str:
        # Ex.: "δ(q0, <div>, Z0) = (q0, DIV Z0)" e "δ(q0, </p>, P) = (q0, ε)"
        ...


@dataclass(frozen=True)
class Token:
    """Um símbolo da fita de entrada, com a posição no texto original."""
    simbolo: str    # símbolo de Σ: "<div>", "</div>", "#texto", "(", "x", "$"
    lexema: str     # trecho original: "<div class='a'>", "Olá mundo", "2+3"
    linha: int      # começa em 1
    coluna: int     # começa em 1


@dataclass(frozen=True)
class Configuracao:
    """Descrição instantânea (q, w, γ) do APD."""
    estado: str
    posicao: int                # índice do próximo token a ser lido na fita
    pilha: tuple[str, ...]      # pilha[0] é o TOPO


class Acao(Enum):
    EMPILHA = "empilha"         # γ = Y X  (cresce 1)
    DESEMPILHA = "desempilha"   # γ = ε    (diminui 1)
    MANTEM = "mantém"           # γ = X    (não muda)
    SUBSTITUI = "substitui"     # qualquer outro caso


@dataclass(frozen=True)
class Passo:
    """Um movimento ⊢ do APD: configuração antes → configuração depois."""
    numero: int                 # 1, 2, 3...
    antes: Configuracao
    depois: Configuracao
    transicao: Transicao
    token: Token | None         # None quando foi ε-transição
    acao: Acao


class TipoFalha(Enum):
    SIMBOLO_FORA_DO_ALFABETO = "símbolo fora do alfabeto"
    FECHAMENTO_INCOMPATIVEL = "fechamento incompatível com o topo da pilha"
    FECHAMENTO_SEM_ABERTURA = "fechamento sem abertura correspondente"
    PILHA_NAO_VAZIA = "pilha não vazia ao fim da entrada"
    SEM_TRANSICAO = "nenhuma transição definida"
    ESTADO_NAO_FINAL = "entrada terminou fora de estado final"
    LIMITE_DE_PASSOS = "limite de passos excedido"


@dataclass(frozen=True)
class Falha:
    tipo: TipoFalha
    mensagem: str               # texto pronto para exibir, em português
    configuracao: Configuracao  # onde o APD travou
    token: Token | None         # token que não pôde ser lido (None se a fita acabou)


@dataclass(frozen=True)
class Resultado:
    aceita: bool
    entrada: tuple[Token, ...]
    passos: tuple[Passo, ...]
    configuracao_final: Configuracao
    falha: Falha | None         # None quando aceita


class DefinicaoInvalidaError(Exception):
    """JSON malformado ou autômato que NÃO é determinístico."""


class ErroLexico(Exception):
    """Erro no tokenizador (ex.: '<div' sem '>'), com posição exata."""
    def __init__(self, mensagem: str, linha: int, coluna: int):
        super().__init__(f"Linha {linha}, coluna {coluna}: {mensagem}")
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
```

## 6. Núcleo: `apd/automato.py` e `apd/carregador.py`

```python
class APD:
    def __init__(self, nome: str, estados: set[str], alfabeto_entrada: set[str],
                 alfabeto_pilha: set[str], transicoes: list[Transicao],
                 estado_inicial: str, simbolo_inicial_pilha: str,
                 estados_finais: set[str], descricao: str = "",
                 tokenizador: str = "xml",
                 rotulos_pilha: dict[str, str] | None = None): ...
        # Guarda δ como dicionário: (origem, le, topo) -> Transicao
        # Chama self.validar(), que levanta DefinicaoInvalidaError se:
        #   - algum estado/símbolo de uma transição não pertence a Q, Σ ou Γ;
        #   - q0 ∉ Q, Z0 ∉ Γ, F ⊄ Q;
        #   - há duas transições para o mesmo (q, a, X)            (não determinismo);
        #   - existe δ(q, ε, X) e também δ(q, a, X) para algum a    (não determinismo).

    def transicao(self, estado: str, simbolo: str | None, topo: str) -> Transicao | None: ...
    def executar(self, fita: list[Token], limite_epsilon: int = 1_000) -> Resultado: ...
    def tupla_formal(self) -> str: ...            # texto de M = (Q, Σ, Γ, δ, q0, Z0, F)
    def tabela_transicoes(self) -> list[Transicao]: ...  # δ ordenada para exibir
```

**Algoritmo de `executar`** (a única implementação de δ do projeto):

1. Configuração inicial: `(q0, posicao=0, pilha=(Z0,))`.
2. Repetir:
   1. Se existe δ(q, ε, X) para o topo X: aplicar sem consumir entrada.
   2. Senão, se ainda há tokens: ler o token `a`. Se `a ∉ Σ` ou não existe δ(q, a, X),
      chamar `diagnostico.diagnosticar(...)` e retornar rejeição com essa `Falha`.
      Senão, aplicar δ(q, a, X), consumir o token e registrar o `Passo`.
   3. Se não há mais tokens e nem ε-transição: parar.
   4. Se houver mais de `limite_epsilon` ε-transições **seguidas** (sem consumir entrada),
      rejeitar com `LIMITE_DE_PASSOS`: "Limite de N ε-transições seguidas excedido em q (possível laço infinito)."
      Só ε-transições podem causar laço infinito num APD, pois cada leitura consome um token;
      por isso o limite não restringe o tamanho de entradas válidas.
3. Aceita se o estado atual ∈ F. Senão, rejeita com a `Falha` de
   `diagnosticar(apd, configuracao, None)`, que é o caso `ESTADO_NAO_FINAL`.

`apd/carregador.py`:

```python
def carregar_apd(caminho: str | Path) -> APD: ...        # levanta DefinicaoInvalidaError
def listar_automatos(pasta: str | Path = "automatos") -> list[Path]: ...
```

## 7. Formato dos arquivos `automatos/*.json`

```json
{
  "nome": "Tags XML/HTML (subconjunto)",
  "descricao": "Valida o aninhamento de html, body, div, p, ul e li.",
  "tokenizador": "xml",
  "estados": ["q0", "qf"],
  "alfabeto_entrada": ["<html>", "</html>", "...", "#texto", "$"],
  "alfabeto_pilha": ["Z0", "HTML", "BODY", "DIV", "P", "UL", "LI"],
  "estado_inicial": "q0",
  "simbolo_inicial_pilha": "Z0",
  "estados_finais": ["qf"],
  "rotulos_pilha": {"Z0": "fundo da pilha", "DIV": "<div>", "P": "<p>"},
  "transicoes": [
    {"origem": "q0", "le": "<div>", "topo": "Z0", "destino": "q0", "empilha": ["DIV", "Z0"]},
    {"origem": "q0", "le": "</div>", "topo": "DIV", "destino": "q0", "empilha": []},
    {"origem": "q0", "le": "$", "topo": "Z0", "destino": "qf", "empilha": ["Z0"]}
  ]
}
```

- `"tokenizador"` diz às interfaces qual função do tokenizador usar: `"xml"` ou `"expressao"`.
- `"rotulos_pilha"` traduz símbolos da pilha para texto amigável nas mensagens de erro
  (ex.: DIV → `<div>`).
- `"le": null` representa ε.
- A definição completa de δ dos dois autômatos está em [DEFINICAO_FORMAL.md](DEFINICAO_FORMAL.md).

## 8. Tokenizador: `apd/tokenizador.py`

```python
def tokenizar_xml(texto: str) -> list[Token]: ...
def tokenizar_expressao(texto: str) -> list[Token]: ...
def tokenizar(texto: str, tipo: str) -> list[Token]: ...   # tipo: "xml" | "expressao"
```

Toda fita **termina com** `Token("$", "", linha, coluna)`, posicionado logo após o
último caractere do texto.

**XML** (`tokenizar_xml`):

| Texto | Símbolo gerado |
|---|---|
| `<div>` ou `<DIV class="x">` | `<div>` (nome em minúsculas, atributos ignorados) |
| `</div>` | `</div>` |
| texto entre tags (sem contar espaços) | `#texto`, um token por trecho contínuo |
| `<!-- comentário -->` | ignorado |
| espaços, tabulações, quebras de linha | ignorados |
| `<br/>` (auto-fechada) | `<br/>` (o APD rejeita: não pertence a Σ) |
| `<table>` (tag fora do subconjunto) | `<table>` (o APD rejeita: não pertence a Σ) |

Erros léxicos (levantam `ErroLexico` com linha e coluna exatas): `<` sem `>` correspondente,
tag sem nome (`<>`, `</>`), nome de tag com caractere inválido e comentário não fechado.

**Expressão** (`tokenizar_expressao`):

| Texto | Símbolo gerado |
|---|---|
| `(` `)` `[` `]` `{` `}` | o próprio caractere |
| trecho contínuo de outros caracteres que não são espaço (`2+3*a`) | `x` |
| espaços | ignorados |

## 9. Diagnóstico: `apd/diagnostico.py`

```python
def diagnosticar(apd: APD, configuracao: Configuracao, token: Token | None) -> Falha: ...
```

Chamada pelo núcleo quando o APD **trava**. As regras são aplicadas nesta ordem, e todas
se baseiam **somente em δ**, sem regra especial para XML:

1. `token is None` e estado ∉ F → `ESTADO_NAO_FINAL`:
   "A entrada terminou no estado q0, que não é de aceitação (F = {qf})." Com o tokenizador isso não
   ocorre, porque a fita sempre termina em `$`; só acontece com fitas montadas à mão, por exemplo nos testes.
2. `token.simbolo ∉ Σ` → `SIMBOLO_FORA_DO_ALFABETO`.
   Ex.: "Símbolo '<table>' (linha 3, coluna 5) não pertence ao alfabeto de entrada Σ."
3. `token.simbolo == "$"` e topo ≠ Z0 → `PILHA_NAO_VAZIA`.
   Ex.: "Pilha não vazia ao fim da entrada: '<div>' foi aberto e nunca fechado (2 símbolos pendentes)."
   O total de pendentes **não conta** o Z0 (é `len(pilha) - 1`).
4. Existe δ(q, a, Y) que **desempilha** para algum Y ≠ topo:
   - se topo == Z0 → `FECHAMENTO_SEM_ABERTURA`.
     Ex.: "'</p>' (linha 2, coluna 1) fecha algo que nunca foi aberto: a pilha está vazia."
   - senão → `FECHAMENTO_INCOMPATIVEL`, com o fechamento esperado obtido de δ
     (o símbolo b tal que δ(q, b, topo) desempilha).
     Ex.: "'</p>' (linha 4, coluna 7) é incompatível com o topo da pilha '<div>': era esperado '</div>'."
5. Qualquer outro caso → `SEM_TRANSICAO`: "Não existe transição δ(q0, x, Z0)."

Use `apd.rotulos_pilha` para trocar DIV por `<div>` nas mensagens, quando houver rótulo.

## 10. Interfaces

**CLI** (`apd/cli.py` + `apd/__main__.py`):

```
python -m apd                                   # menu interativo
python -m apd --gui                             # abre a interface gráfica
python -m apd -a automatos/xml_tags.json -e "<div><p>oi</p></div>"
python -m apd -a automatos/expressoes.json -f exemplos/expressoes/valida_01.txt
python -m apd ... --passo                       # pausa a cada passo (Enter)
python -m apd ... --atraso 0.4                  # animação automática
python -m apd ... --definicao                   # mostra M = (...) e a tabela δ
python -m apd ... --sem-cor                     # desliga cores ANSI
```

**GUI** (`apd/gui.py`): função `main()` abre a janela. Ela mostra a fita (com o cabeçote),
a pilha desenhada crescendo e diminuindo, a tabela δ com a transição usada destacada,
o log de passos e o resultado. Detalhes na issue da GUI.

As duas interfaces seguem o mesmo princípio: chamam `tokenizar` → `APD.executar` e só
**exibem** o `Resultado`.
