"""Análise léxica: converte texto bruto em uma fita de ``Token`` para o APD.

O Autômato com Pilha Determinístico M = (Q, Σ, Γ, δ, q0, Z0, F) não opera sobre
caracteres isolados do arquivo, mas sobre uma **fita de símbolos do alfabeto de
entrada Σ** (docs/ARQUITETURA.md §1 e §8). Este módulo faz a ponte entre o texto
escrito pelo usuário e essa fita formal:

* ``tokenizar_xml`` transforma um documento XML/HTML na sequência de aberturas
  ``<nome>``, fechamentos ``</nome>``, tags auto-fechadas ``<nome/>`` e trechos
  ``#texto``, descartando espaços em branco e comentários ``<!-- ... -->``;
* toda fita gerada termina obrigatoriamente com ``Token("$", "", linha, coluna)``
  (constante ``MARCADOR_FIM``), permitindo que o APD reconheça o fim da entrada de
  forma determinística por estado final, sem precisar de ε-transições que violariam
  o determinismo em q0 (docs/DEFINICAO_FORMAL.md §3).

Ligação com a teoria (divisão léxico × sintático de um compilador):

* **Análise léxica (este módulo)** é uma tarefa **regular**: reconhecer tags,
  atributos entre aspas e comentários não exige memória ilimitada, bastando um
  Autômato Finito Determinístico (AFD) que varre o texto caractere a caractere
  transitando entre estados finitos ("fora de tag", "lendo nome", "lendo
  atributos", "dentro de aspas" e "dentro de comentário").
* **Análise sintática (``apd/automato.py``)** verifica o aninhamento balanceado das
  estruturas, linguagem livre de contexto determinística que não é regular (pelo
  Lema do Bombeamento) e requer a pilha Γ* do APD.

Diferença entre erro léxico e rejeição pelo APD:

* **Erro léxico (``ErroLexico``)**: o texto é malformado no nível dos caracteres
  (por exemplo, ``<div`` sem ``>``, ``<>`` sem nome ou ``<!--`` sem ``-->``) e nem
  sequer chega a formar uma fita válida de símbolos.
* **Rejeição pelo APD (``Resultado(aceita=False)``)**: construções bem formadas
  como ``<table>`` ou ``<br/>`` viram tokens normalmente na fita, mas são rejeitadas
  depois por ``APD.executar`` (``SIMBOLO_FORA_DO_ALFABETO``) por não pertencerem ao
  subconjunto Σ do autômato carregado.

Limitação conhecida: um ``<`` solto no meio do texto (como em ``2 < 3``) é lido
como início de tag e provoca ``ErroLexico``; em XML real ele deve ser grafado como
a entidade ``&lt;``.
"""

from __future__ import annotations

from apd.modelos import MARCADOR_FIM, ErroLexico, Token

__all__ = ["tokenizar_xml"]

_PONTUACAO_NOME_TAG = frozenset("-_:.")


def tokenizar_xml(texto: str) -> list[Token]:
    """Converte um texto XML/HTML em uma fita de ``Token`` terminada por ``$``.

    Opera como um autômato finito determinístico (sem expressões regulares), lendo
    caractere por caractere a partir do estado "fora de tag" e mantendo o índice
    ``i`` e os contadores 1-indexados ``linha`` e ``coluna``:

    * tags ``<nome ...>`` geram o símbolo ``<nome>`` (nome convertido para
      minúsculas e atributos ignorados, respeitando ``>`` dentro de ``"..."`` ou
      ``'...'``);
    * tags ``</nome>`` geram ``</nome>``;
    * tags auto-fechadas ``<nome .../>`` geram ``<nome/>`` (rejeitadas adiante pelo
      APD quando não pertencem a Σ);
    * comentários ``<!-- ... -->`` e espaços fora de conteúdo textual são ignorados,
      preservando a contagem de linhas e colunas dos tokens seguintes;
    * cada trecho contínuo entre tags ou comentários que contenha ao menos um
      caractere não branco gera um único ``Token("#texto", lexema, linha, coluna)``,
      com ``lexema`` sem espaços nas pontas e posição no primeiro caractere visível;
    * ao final, acrescenta ``Token("$", "", linha, coluna)`` imediatamente após o
      último caractere da entrada.

    Limitação conhecida: ``<`` literal no texto (ex.: ``2 < 3``) é interpretado
    como abertura de tag; em XML deve-se escrever ``&lt;``.

    Levanta ``ErroLexico`` com linha e coluna exatas nos quatro casos previstos no
    contrato: ``'<' sem '>' correspondente``, ``tag sem nome``,
    ``caractere inválido '...' no nome da tag`` e ``comentário não fechado``.
    """
    texto = _normalizar_quebras(texto)
    tokens: list[Token] = []
    tamanho = len(texto)
    i = 0
    linha = 1
    coluna = 1

    inicio_texto: int | None = None
    fim_texto = 0
    linha_texto = 1
    coluna_texto = 1

    while i < tamanho:
        caractere = texto[i]

        if caractere == "<":
            if inicio_texto is not None:
                tokens.append(
                    Token(
                        "#texto",
                        texto[inicio_texto:fim_texto],
                        linha_texto,
                        coluna_texto,
                    )
                )
                inicio_texto = None

            if texto.startswith("<!--", i):
                i, linha, coluna = _ler_comentario(texto, i, linha, coluna)
            else:
                token_tag, i, linha, coluna = _ler_tag(texto, i, linha, coluna)
                tokens.append(token_tag)
            continue

        if not caractere.isspace():
            if inicio_texto is None:
                inicio_texto = i
                linha_texto = linha
                coluna_texto = coluna
            fim_texto = i + 1

        linha, coluna = _avancar_posicao(caractere, linha, coluna)
        i += 1

    if inicio_texto is not None:
        tokens.append(
            Token("#texto", texto[inicio_texto:fim_texto], linha_texto, coluna_texto)
        )

    tokens.append(Token(MARCADOR_FIM, "", linha, coluna))
    return tokens


# ---------------------------------------------------------------------- auxiliares


def _normalizar_quebras(texto: str) -> str:
    """Converte ``\\r\\n`` (Windows) e ``\\r`` isolado para ``\\n``."""
    return texto.replace("\r\n", "\n").replace("\r", "\n")


def _avancar_posicao(caractere: str, linha: int, coluna: int) -> tuple[int, int]:
    """Atualiza ``(linha, coluna)`` após ler um caractere (tabulação = 1 coluna)."""
    if caractere == "\n":
        return linha + 1, 1
    return linha, coluna + 1


def _eh_letra_ascii(caractere: str) -> bool:
    """Indica se ``caractere`` é letra ASCII (``a-z`` ou ``A-Z``)."""
    return ("a" <= caractere <= "z") or ("A" <= caractere <= "Z")


def _eh_caractere_nome_tag(caractere: str) -> bool:
    """Indica se ``caractere`` pode continuar o nome de uma tag XML."""
    return (
        _eh_letra_ascii(caractere)
        or ("0" <= caractere <= "9")
        or caractere in _PONTUACAO_NOME_TAG
    )


def _ler_comentario(
    texto: str, i: int, linha: int, coluna: int
) -> tuple[int, int, int]:
    """Estado 'dentro de comentário': consome de ``<!--`` até o primeiro ``-->``.

    Devolve ``(novo_i, nova_linha, nova_coluna)`` logo após o ``>`` de ``-->``, ou
    levanta ``ErroLexico`` na posição do ``<`` inicial se o comentário não fechar.
    """
    linha_inicio = linha
    coluna_inicio = coluna
    tamanho = len(texto)

    # Consome o prefixo "<!--" (4 caracteres na mesma linha).
    i += 4
    coluna += 4

    while i < tamanho:
        if texto.startswith("-->", i):
            return i + 3, linha, coluna + 3
        linha, coluna = _avancar_posicao(texto[i], linha, coluna)
        i += 1

    raise ErroLexico("comentário não fechado", linha_inicio, coluna_inicio)


def _ler_tag(
    texto: str, i: int, linha: int, coluna: int
) -> tuple[Token, int, int, int]:
    """Estados 'lendo nome', 'lendo atributos' e 'dentro de aspas' para uma tag XML.

    Consome desde ``<`` até o ``>`` de fechamento correspondente (fora de aspas) e
    devolve ``(token, novo_i, nova_linha, nova_coluna)``.
    """
    inicio_lexema = i
    linha_tag = linha
    coluna_tag = coluna
    tamanho = len(texto)

    # Consome '<' e verifica barra opcional de fechamento '</'.
    i += 1
    coluna += 1
    fechamento = False
    if i < tamanho and texto[i] == "/":
        fechamento = True
        i += 1
        coluna += 1

    # Estado: lendo o primeiro caractere do nome da tag.
    if i >= tamanho:
        raise ErroLexico("'<' sem '>' correspondente", linha_tag, coluna_tag)

    primeiro = texto[i]
    if primeiro == ">" or primeiro.isspace():
        raise ErroLexico("tag sem nome", linha_tag, coluna_tag)
    if not _eh_letra_ascii(primeiro):
        raise ErroLexico(
            f"caractere inválido '{primeiro}' no nome da tag", linha, coluna
        )

    # Estado: lendo os demais caracteres do nome da tag.
    inicio_nome = i
    i += 1
    coluna += 1
    while i < tamanho and _eh_caractere_nome_tag(texto[i]):
        i += 1
        coluna += 1

    if i >= tamanho:
        raise ErroLexico("'<' sem '>' correspondente", linha_tag, coluna_tag)

    separador = texto[i]
    if separador not in (">", "/") and not separador.isspace():
        raise ErroLexico(
            f"caractere inválido '{separador}' no nome da tag", linha, coluna
        )

    nome = texto[inicio_nome:i].lower()

    # Estados: lendo atributos (aspas=None) e dentro de aspas (aspas='"' ou "'").
    aspas: str | None = None
    ultimo_nao_branco = ""

    while i < tamanho:
        caractere = texto[i]
        linha, coluna = _avancar_posicao(caractere, linha, coluna)
        i += 1

        if aspas is not None:
            if caractere == aspas:
                aspas = None
                ultimo_nao_branco = caractere
        elif caractere == ">":
            lexema = texto[inicio_lexema:i]
            if fechamento:
                simbolo = f"</{nome}>"
            elif ultimo_nao_branco == "/":
                simbolo = f"<{nome}/>"
            else:
                simbolo = f"<{nome}>"
            return Token(simbolo, lexema, linha_tag, coluna_tag), i, linha, coluna
        elif caractere in ('"', "'"):
            aspas = caractere
            ultimo_nao_branco = caractere
        elif not caractere.isspace():
            ultimo_nao_branco = caractere

    raise ErroLexico("'<' sem '>' correspondente", linha_tag, coluna_tag)
