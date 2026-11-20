"""Carregador das definições de APD guardadas em ``automatos/*.json``.

Cada arquivo JSON é a 7-tupla M = (Q, Σ, Γ, δ, q0, Z0, F) serializada
(docs/ARQUITETURA.md §7):

    Componente   Campo do JSON              Tipo no JSON           Tipo no APD
    Q            "estados"                  lista de strings       set[str]
    Σ            "alfabeto_entrada"         lista de strings       set[str]
    Γ            "alfabeto_pilha"           lista de strings       set[str]
    δ            "transicoes"               lista de objetos       list[Transicao]
    q0           "estado_inicial"           string                 str
    Z0           "simbolo_inicial_pilha"    string                 str
    F            "estados_finais"           lista de strings       set[str]

Cada objeto de "transicoes" representa δ(origem, le, topo) = (destino, empilha);
``"le": null`` é ε (``None`` em Python) e ``"empilha"`` é a cadeia γ, com o novo
topo em primeiro lugar (``[]`` significa só desempilhar).

Além da 7-tupla, o JSON traz metadados para as interfaces: "nome" (obrigatório),
"descricao", "tokenizador" e "rotulos_pilha" (opcionais).

Este módulo cuida só da forma do arquivo (campos presentes, tipos corretos). As
regras formais (símbolos de δ pertencem a Q, Σ e Γ; q0 ∈ Q; Z0 ∈ Γ; F ⊆ Q;
determinismo) são verificadas pelo próprio ``APD`` ao ser construído. Qualquer
problema, de forma ou formal, chega a quem chamou como ``DefinicaoInvalidaError``
com uma mensagem em português que cita o arquivo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apd.automato import APD
from apd.modelos import DefinicaoInvalidaError, Transicao

_RAIZ_PROJETO = Path(__file__).resolve().parent.parent
"""Pasta raiz do projeto, usada para achar ``automatos/`` fora do diretório atual."""

CAMPOS_OBRIGATORIOS = (
    "nome",
    "estados",
    "alfabeto_entrada",
    "alfabeto_pilha",
    "estado_inicial",
    "simbolo_inicial_pilha",
    "estados_finais",
    "transicoes",
)
"""Campos sem os quais a 7-tupla (mais o nome) não pode ser montada."""

CAMPOS_TRANSICAO = ("origem", "le", "topo", "destino", "empilha")
"""Chaves de cada objeto de "transicoes": δ(origem, le, topo) = (destino, empilha)."""

TOKENIZADORES_VALIDOS = ("xml", "expressao")
"""Valores aceitos em "tokenizador" (as funções de ``apd.tokenizador``)."""


def carregar_apd(caminho: str | Path) -> APD:
    """Lê um arquivo JSON e devolve o APD M = (Q, Σ, Γ, δ, q0, Z0, F) que ele descreve.

    As listas de Q, Σ, Γ e F viram ``set``; cada transição vira
    ``Transicao(origem, le, topo, destino, tuple(empilha))``, com ``"le": null``
    convertido em ``None`` (ε). O ``APD`` construído se autovalida (pertinência a
    Q, Σ e Γ e determinismo).

    Levanta ``DefinicaoInvalidaError``, citando o arquivo, se ele não existir, não
    puder ser lido, não for JSON válido (inclusive com chave repetida num objeto),
    faltar campo obrigatório, algum campo tiver tipo errado, "tokenizador" não for
    "xml" nem "expressao", "rotulos_pilha" citar símbolo fora de Γ ou o autômato
    não for um APD válido.
    """
    caminho = Path(caminho)
    dados = _ler_json(caminho)
    try:
        return _montar_apd(dados)
    except DefinicaoInvalidaError as erro:
        # Prefixa o arquivo tanto nos erros de forma quanto nos erros formais do APD.
        raise DefinicaoInvalidaError(f"Arquivo '{caminho}': {erro}") from erro


def listar_automatos(pasta: str | Path = "automatos") -> list[Path]:
    """Lista, em ordem alfabética, os arquivos ``*.json`` de definição de APD.

    Uma pasta relativa é procurada primeiro no diretório atual e, se não existir
    ali, a partir da raiz do projeto (assim a GUI funciona mesmo aberta de outra
    pasta). Se a pasta não existir em nenhum dos dois lugares, devolve ``[]``.
    """
    pasta = Path(pasta)
    candidatas = [pasta] if pasta.is_absolute() else [pasta, _RAIZ_PROJETO / pasta]
    for candidata in candidatas:
        if candidata.is_dir():
            return sorted(candidata.glob("*.json"))
    return []


# ---------------------------------------------------------------------------
# Leitura do arquivo
# ---------------------------------------------------------------------------

def _ler_json(caminho: Path) -> dict[str, Any]:
    """Lê o arquivo em UTF-8 e devolve o objeto JSON da raiz (um ``dict``).

    O encoding "utf-8-sig" aceita também arquivos com BOM (como os salvos pelo
    Bloco de Notas do Windows). Chaves repetidas num mesmo objeto são rejeitadas.
    """
    try:
        with caminho.open(encoding="utf-8-sig") as arquivo:
            dados = json.load(arquivo, object_pairs_hook=_objeto_sem_chave_repetida)
    except _ChaveRepetidaError as erro:
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}': chave '{erro.chave}' repetida num mesmo objeto "
            f"do JSON."
        ) from erro
    except FileNotFoundError as erro:
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}' não encontrado."
        ) from erro
    except json.JSONDecodeError as erro:
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}': JSON malformado na linha {erro.lineno}, "
            f"coluna {erro.colno} ({erro.msg})."
        ) from erro
    except UnicodeDecodeError as erro:
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}': o conteúdo não está codificado em UTF-8."
        ) from erro
    except OSError as erro:
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}' não pôde ser lido: {erro.strerror or erro}."
        ) from erro
    except ValueError as erro:
        # Vem depois de JSONDecodeError e UnicodeDecodeError (subclasses de
        # ValueError). Ex.: inteiro com mais dígitos que o limite do Python.
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}': valor inválido no JSON ({erro})."
        ) from erro
    except RecursionError as erro:
        # Ex.: listas ou objetos aninhados em milhares de níveis.
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}': JSON aninhado em níveis demais para ser lido."
        ) from erro

    if not isinstance(dados, dict):
        raise DefinicaoInvalidaError(
            f"Arquivo '{caminho}': a raiz do JSON deve ser um objeto {{...}} "
            f"com a 7-tupla do APD, mas é {_nome_tipo(dados)}."
        )
    return dados


class _ChaveRepetidaError(ValueError):
    """Sinaliza, de dentro de ``json.load``, uma chave repetida num objeto."""

    def __init__(self, chave: str) -> None:
        super().__init__(chave)
        self.chave = chave


def _objeto_sem_chave_repetida(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    """``object_pairs_hook`` do ``json.load``: monta o objeto recusando chave repetida.

    Sem isso, ``{"le": "a", "le": null}`` ficaria silenciosamente com o último valor.
    """
    objeto: dict[str, Any] = {}
    for chave, valor in pares:
        if chave in objeto:
            raise _ChaveRepetidaError(chave)
        objeto[chave] = valor
    return objeto


# ---------------------------------------------------------------------------
# Conversão JSON -> APD
# ---------------------------------------------------------------------------

def _montar_apd(dados: dict[str, Any]) -> APD:
    """Valida a forma dos campos e constrói o ``APD`` (que valida as regras formais)."""
    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in dados:
            raise DefinicaoInvalidaError(f"campo obrigatório '{campo}' ausente.")

    alfabeto_pilha = set(
        _exigir_lista_de_strings(dados["alfabeto_pilha"], "alfabeto_pilha")
    )
    return APD(
        nome=_exigir_string(dados["nome"], "nome"),
        estados=set(_exigir_lista_de_strings(dados["estados"], "estados")),
        alfabeto_entrada=set(
            _exigir_lista_de_strings(dados["alfabeto_entrada"], "alfabeto_entrada")
        ),
        alfabeto_pilha=alfabeto_pilha,
        transicoes=_converter_transicoes(dados["transicoes"]),
        estado_inicial=_exigir_string(dados["estado_inicial"], "estado_inicial"),
        simbolo_inicial_pilha=_exigir_string(
            dados["simbolo_inicial_pilha"], "simbolo_inicial_pilha"
        ),
        estados_finais=set(
            _exigir_lista_de_strings(dados["estados_finais"], "estados_finais")
        ),
        descricao=_ler_descricao(dados),
        tokenizador=_ler_tokenizador(dados),
        rotulos_pilha=_ler_rotulos_pilha(dados, alfabeto_pilha),
    )


def _converter_transicoes(valor: Any) -> list[Transicao]:
    """Converte a lista "transicoes" em δ, preservando a ordem do JSON."""
    if not isinstance(valor, list):
        raise DefinicaoInvalidaError(
            f"o campo 'transicoes' deve ser uma lista, mas é {_nome_tipo(valor)}."
        )
    return [_converter_transicao(indice, bruta) for indice, bruta in enumerate(valor)]


def _converter_transicao(indice: int, bruta: Any) -> Transicao:
    """Converte um objeto do JSON em δ(origem, le, topo) = (destino, empilha).

    ``"le": null`` vira ``None`` (ε) e a lista ``"empilha"`` vira a tupla γ.
    """
    local = f"transicoes[{indice}]"
    if not isinstance(bruta, dict):
        raise DefinicaoInvalidaError(
            f"{local} deve ser um objeto, mas é {_nome_tipo(bruta)}."
        )
    for chave in CAMPOS_TRANSICAO:
        if chave not in bruta:
            raise DefinicaoInvalidaError(f"{local}: chave obrigatória '{chave}' ausente.")

    return Transicao(
        origem=_exigir_string(bruta["origem"], f"{local}.origem"),
        le=_ler_simbolo_lido(bruta["le"], f"{local}.le"),
        topo=_exigir_string(bruta["topo"], f"{local}.topo"),
        destino=_exigir_string(bruta["destino"], f"{local}.destino"),
        empilha=tuple(_exigir_lista_de_strings(bruta["empilha"], f"{local}.empilha")),
    )


def _ler_simbolo_lido(valor: Any, local: str) -> str | None:
    """Símbolo ``a`` de δ(q, a, X): uma string de Σ ou ``null`` (ε → ``None``)."""
    if valor is None:
        return None
    if valor == "":
        raise DefinicaoInvalidaError(f"'{local}' é uma string vazia; para ε use null.")
    if not isinstance(valor, str):
        raise DefinicaoInvalidaError(
            f"'{local}' deve ser uma string ou null (ε), mas é {_nome_tipo(valor)}."
        )
    return valor


def _ler_descricao(dados: dict[str, Any]) -> str:
    """Campo opcional "descricao"; padrão ``""``."""
    if "descricao" not in dados:
        return ""
    descricao = dados["descricao"]
    if not isinstance(descricao, str):
        raise DefinicaoInvalidaError(
            f"o campo 'descricao' deve ser uma string, mas é {_nome_tipo(descricao)}."
        )
    return descricao


def _ler_tokenizador(dados: dict[str, Any]) -> str:
    """Campo opcional "tokenizador" ("xml" ou "expressao"); padrão ``"xml"``."""
    tokenizador = dados.get("tokenizador", "xml")
    if tokenizador not in TOKENIZADORES_VALIDOS:
        aceitos = " ou ".join(f"'{nome}'" for nome in TOKENIZADORES_VALIDOS)
        raise DefinicaoInvalidaError(
            f"o campo 'tokenizador' deve ser {aceitos}, "
            f"mas é {_descrever_valor(tokenizador)}."
        )
    return tokenizador


def _ler_rotulos_pilha(
    dados: dict[str, Any], alfabeto_pilha: set[str]
) -> dict[str, str] | None:
    """Campo opcional "rotulos_pilha": objeto símbolo de Γ → texto amigável.

    Toda chave precisa pertencer a Γ (``alfabeto_pilha``).
    """
    if "rotulos_pilha" not in dados:
        return None
    rotulos = dados["rotulos_pilha"]
    if not isinstance(rotulos, dict):
        raise DefinicaoInvalidaError(
            f"o campo 'rotulos_pilha' deve ser um objeto, mas é {_nome_tipo(rotulos)}."
        )
    for simbolo, rotulo in rotulos.items():
        if simbolo not in alfabeto_pilha:
            raise DefinicaoInvalidaError(
                f"rotulos_pilha['{simbolo}']: o símbolo '{simbolo}' não pertence "
                f"ao alfabeto da pilha Γ."
            )
        if not isinstance(rotulo, str):
            raise DefinicaoInvalidaError(
                f"rotulos_pilha['{simbolo}'] deve ser uma string, "
                f"mas é {_nome_tipo(rotulo)}."
            )
    return dict(rotulos)


# ---------------------------------------------------------------------------
# Verificações de tipo
# ---------------------------------------------------------------------------

def _exigir_string(valor: Any, local: str) -> str:
    """Garante que ``valor`` é uma string não vazia (nome de estado ou símbolo)."""
    if not isinstance(valor, str):
        raise DefinicaoInvalidaError(
            f"'{local}' deve ser uma string, mas é {_nome_tipo(valor)}."
        )
    if not valor:
        raise DefinicaoInvalidaError(f"'{local}' não pode ser uma string vazia.")
    return valor


def _exigir_lista_de_strings(valor: Any, local: str) -> list[str]:
    """Garante que ``valor`` é uma lista de strings não vazias (um conjunto do APD)."""
    if not isinstance(valor, list):
        raise DefinicaoInvalidaError(
            f"'{local}' deve ser uma lista, mas é {_nome_tipo(valor)}."
        )
    return [_exigir_string(item, f"{local}[{i}]") for i, item in enumerate(valor)]


def _nome_tipo(valor: Any) -> str:
    """Nome do tipo JSON de ``valor``, para as mensagens de erro."""
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "um booleano"
    if isinstance(valor, (int, float)):
        return "um número"
    if isinstance(valor, str):
        return "uma string"
    if isinstance(valor, list):
        return "uma lista"
    if isinstance(valor, dict):
        return "um objeto"
    return type(valor).__name__


def _descrever_valor(valor: Any) -> str:
    """Descreve ``valor`` como no JSON: a string entre aspas ou o nome do tipo."""
    if isinstance(valor, str):
        return f"'{valor}'"
    return _nome_tipo(valor)
