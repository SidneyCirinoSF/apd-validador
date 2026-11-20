"""Contratos de dados do projeto: a tradução direta da teoria do APD para Python.

Um Autômato com Pilha Determinístico é a 7-tupla M = (Q, Σ, Γ, δ, q0, Z0, F).
Este módulo não executa nada; ele só define os "tijolos" que os outros módulos
trocam entre si:

    Teoria                                  Classe
    δ(q, a, X) = (p, γ)                     Transicao
    símbolo da fita de entrada              Token
    descrição instantânea (q, w, γ)         Configuracao
    movimento ⊢ entre duas configurações    Passo (+ Acao)
    motivo da rejeição                      Falha (+ TipoFalha)
    resultado da computação                 Resultado

Convenções fixadas para o projeto inteiro (docs/ARQUITETURA.md §4):

* ε é ``None`` em Python (constante ``EPSILON``) e ``null`` no JSON;
* o topo da pilha é ``pilha[0]`` e o fundo (Z0) é ``pilha[-1]``, a mesma leitura
  da notação Xβ, em que o topo é escrito à esquerda;
* em δ(q, a, X) = (p, γ), ``empilha[0]`` vira o novo topo e ``()`` significa só
  desempilhar;
* ``MARCADOR_FIM`` ("$") é sempre o último token da fita;
* a aceitação é por estado final.

Todas as dataclasses são ``frozen=True``: uma configuração registrada em um passo é
um valor e não pode mudar depois, senão o histórico da execução (que a CLI e a GUI
reexibem) seria corrompido. Isso também permite usá-las como chave de dicionário.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

MARCADOR_FIM = "$"
"""Marcador de fim de entrada. Com ele, o APD sabe que a fita acabou sem precisar
de uma ε-transição, que entraria em conflito com o determinismo."""

EPSILON = None  # ε
"""A palavra vazia ε. Em uma transição, ``le=EPSILON`` significa "não consome entrada"."""

_SIMBOLO_EPSILON = "ε"


@dataclass(frozen=True)
class Transicao:
    """δ(origem, le, topo) = (destino, empilha).

    Lida assim: "no estado ``origem``, lendo ``le`` com ``topo`` no topo da pilha,
    vá para ``destino`` e troque o topo pela cadeia ``empilha``" (γ).

    ``le`` é ``None`` numa ε-transição (não consome entrada). ``empilha[0]`` vira o
    novo topo e ``()`` significa apenas desempilhar.
    """

    origem: str
    le: str | None              # None = ε (não consome entrada)
    topo: str
    destino: str
    empilha: tuple[str, ...]    # empilha[0] = novo topo; () = desempilhar

    def __str__(self) -> str:
        """Notação matemática da transição.

        Ex.: ``δ(q0, <div>, Z0) = (q0, DIV Z0)`` e ``δ(q0, </p>, P) = (q0, ε)``.
        """
        simbolo = _SIMBOLO_EPSILON if self.le is None else self.le
        gama = " ".join(self.empilha) if self.empilha else _SIMBOLO_EPSILON
        return f"δ({self.origem}, {simbolo}, {self.topo}) = ({self.destino}, {gama})"


@dataclass(frozen=True)
class Token:
    """Um símbolo da fita de entrada, com a posição no texto original.

    ``simbolo`` é o elemento de Σ que o APD lê. ``lexema``, ``linha`` e ``coluna``
    existem só para apontar ao usuário onde, no texto, está cada símbolo.
    """

    simbolo: str    # símbolo de Σ: "<div>", "</div>", "#texto", "(", "x", "$"
    lexema: str     # trecho original: "<div class='a'>", "Olá mundo", "2+3"
    linha: int      # começa em 1
    coluna: int     # começa em 1


@dataclass(frozen=True)
class Configuracao:
    """Descrição instantânea (q, w, γ) do APD.

    * ``estado``: o estado atual q;
    * ``posicao``: quanto da fita já foi lido; a parte que falta, w, começa no token
      de índice ``posicao``;
    * ``pilha``: o conteúdo γ da pilha, com o TOPO em ``pilha[0]``.
    """

    estado: str
    posicao: int                # índice do próximo token a ser lido na fita
    pilha: tuple[str, ...]      # pilha[0] é o TOPO


class Acao(Enum):
    """Efeito de um movimento sobre a pilha, olhando γ em δ(q, a, X) = (p, γ)."""

    EMPILHA = "empilha"         # γ = Y X  (cresce 1)
    DESEMPILHA = "desempilha"   # γ = ε    (diminui 1)
    MANTEM = "mantém"           # γ = X    (não muda)
    SUBSTITUI = "substitui"     # qualquer outro caso


@dataclass(frozen=True)
class Passo:
    """Um movimento ⊢ do APD: configuração antes → configuração depois.

    Formalmente, (q, aw, Xβ) ⊢ (p, w, γβ) quando δ(q, a, X) = (p, γ). Guardar o
    "antes" e o "depois" permite que as interfaces reexibam a computação inteira
    sem recalcular nada.
    """

    numero: int                 # 1, 2, 3...
    antes: Configuracao
    depois: Configuracao
    transicao: Transicao
    token: Token | None         # None quando foi ε-transição
    acao: Acao


class TipoFalha(Enum):
    """Motivos pelos quais o APD pode rejeitar uma entrada."""

    SIMBOLO_FORA_DO_ALFABETO = "símbolo fora do alfabeto"
    FECHAMENTO_INCOMPATIVEL = "fechamento incompatível com o topo da pilha"
    FECHAMENTO_SEM_ABERTURA = "fechamento sem abertura correspondente"
    PILHA_NAO_VAZIA = "pilha não vazia ao fim da entrada"
    SEM_TRANSICAO = "nenhuma transição definida"
    ESTADO_NAO_FINAL = "entrada terminou fora de estado final"
    LIMITE_DE_PASSOS = "limite de passos excedido"


@dataclass(frozen=True)
class Falha:
    """Por que a computação foi rejeitada e em que configuração o APD travou.

    Um APD rejeita quando fica numa configuração sem movimento possível (δ não
    definida para o estado, o símbolo e o topo atuais) ou quando a entrada acaba fora
    de um estado final.
    """

    tipo: TipoFalha
    mensagem: str               # texto pronto para exibir, em português
    configuracao: Configuracao  # onde o APD travou
    token: Token | None         # token que não pôde ser lido (None se a fita acabou)


@dataclass(frozen=True)
class Resultado:
    """Resultado de uma computação completa do APD sobre uma fita.

    ``passos`` traz todos os movimentos ⊢ feitos, inclusive quando a entrada é
    rejeitada (as interfaces mostram os passos até o travamento). ``falha`` é
    ``None`` quando a entrada é aceita.
    """

    aceita: bool
    entrada: tuple[Token, ...]
    passos: tuple[Passo, ...]
    configuracao_final: Configuracao
    falha: Falha | None         # None quando aceita


class DefinicaoInvalidaError(Exception):
    """JSON malformado ou autômato que NÃO é determinístico."""


class ErroLexico(Exception):
    """Erro no tokenizador (ex.: '<div' sem '>'), com posição exata.

    Acontece antes do APD: o texto nem chegou a virar uma fita de símbolos de Σ.
    """

    def __init__(self, mensagem: str, linha: int, coluna: int):
        super().__init__(f"Linha {linha}, coluna {coluna}: {mensagem}")
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
