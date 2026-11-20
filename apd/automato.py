"""Núcleo do projeto: a classe ``APD``, M = (Q, Σ, Γ, δ, q0, Z0, F).

Este módulo é a **única implementação de δ** do projeto (docs/ARQUITETURA.md §6):

* ``APD.__init__`` guarda os sete componentes da tupla e chama ``validar()``, que
  garante que M é bem formado e **determinístico**;
* ``APD.executar`` simula a relação de movimento ⊢ sobre uma fita de tokens,
  partindo da configuração inicial (q0, w, Z0), e registra cada movimento como um
  ``Passo`` (configuração antes ⊢ configuração depois);
* quando o APD trava, a rejeição é explicada por ``diagnosticar`` (apd/diagnostico.py).

As interfaces (CLI e GUI) apenas reexibem os passos registrados no ``Resultado``;
nenhuma delas mantém uma pilha própria nem reaplica δ. Também não há aqui nenhuma
regra específica de XML: o núcleo conhece só a 7-tupla.
"""

from __future__ import annotations

from apd.modelos import (
    EPSILON,
    Acao,
    Configuracao,
    DefinicaoInvalidaError,
    Falha,
    Passo,
    Resultado,
    TipoFalha,
    Token,
    Transicao,
)

try:
    from apd.diagnostico import diagnosticar
except ModuleNotFoundError as erro:
    if erro.name != "apd.diagnostico":
        raise  # o módulo existe mas tem outro problema: não esconda o erro

    # PROVISÓRIO até a issue #5: remover logo depois do merge do #5 (ver #11).
    def diagnosticar(apd: APD, configuracao: Configuracao, token: Token | None) -> Falha:
        """Diagnóstico mínimo usado só enquanto apd/diagnostico.py não existe."""
        tipo = TipoFalha.ESTADO_NAO_FINAL if token is None else TipoFalha.SEM_TRANSICAO
        return Falha(tipo, f"[diagnóstico provisório] {tipo.value}", configuracao, token)


__all__ = ["APD"]

_SIMBOLO_EPSILON = "ε"

Chave = tuple[str, str | None, str]
"""Chave de δ: (estado q, símbolo lido a ou ε=None, topo X)."""


class APD:
    """Autômato com Pilha Determinístico M = (Q, Σ, Γ, δ, q0, Z0, F).

    * Q = ``estados``, Σ = ``alfabeto_entrada``, Γ = ``alfabeto_pilha``;
    * δ = ``delta``, dicionário ``(q, a, X) -> Transicao`` (a = ``None`` é ε);
    * q0 = ``estado_inicial``, Z0 = ``simbolo_inicial_pilha``, F = ``estados_finais``.

    O APD é **determinístico**: para cada configuração há no máximo um movimento
    possível. Isso vale porque ``validar()`` exige que

    1. cada (q, a, X) tenha no máximo uma transição; e
    2. se existe δ(q, ε, X), não exista δ(q, a, X) para nenhum a ∈ Σ.

    A aceitação é **por estado final**, como na definição formal: M aceita w se
    (q0, w, Z0) ⊢* (p, ε, α) com p ∈ F, para alguma pilha α. Basta, portanto, que
    *alguma* configuração alcançada com a fita inteira consumida (incluindo o
    marcador ``$``) esteja num estado de F, ainda que existam ε-transições a partir
    dela; ``executar`` aceita assim que isso acontece.

    Os atributos ``nome``, ``descricao``, ``tokenizador`` e ``rotulos_pilha`` não
    fazem parte da 7-tupla: servem às interfaces e às mensagens de diagnóstico.
    """

    def __init__(self, nome: str, estados: set[str], alfabeto_entrada: set[str],
                 alfabeto_pilha: set[str], transicoes: list[Transicao],
                 estado_inicial: str, simbolo_inicial_pilha: str,
                 estados_finais: set[str], descricao: str = "",
                 tokenizador: str = "xml",
                 rotulos_pilha: dict[str, str] | None = None):
        """Guarda a 7-tupla e valida M; levanta ``DefinicaoInvalidaError`` se M for
        inconsistente ou não determinístico."""
        self.nome = nome
        self.descricao = descricao
        self.tokenizador = tokenizador
        self.estados: set[str] = set(estados)                    # Q
        self.alfabeto_entrada: set[str] = set(alfabeto_entrada)  # Σ
        self.alfabeto_pilha: set[str] = set(alfabeto_pilha)      # Γ
        self.estado_inicial = estado_inicial                     # q0
        self.simbolo_inicial_pilha = simbolo_inicial_pilha       # Z0
        self.estados_finais: set[str] = set(estados_finais)      # F
        self.rotulos_pilha: dict[str, str] = dict(rotulos_pilha or {})
        # Ordem original das transições (a do JSON), usada por tabela_transicoes().
        self._transicoes: tuple[Transicao, ...] = tuple(transicoes)
        # δ: (q, a, X) -> Transicao. Preenchida por validar(), que verifica a
        # unicidade de cada chave no momento da inserção.
        self.delta: dict[Chave, Transicao] = {}
        self.validar()

    # ------------------------------------------------------------------ validação

    def validar(self) -> None:
        """Confere que M = (Q, Σ, Γ, δ, q0, Z0, F) é bem formado e determinístico.

        Regras, nesta ordem (levanta ``DefinicaoInvalidaError`` na primeira violada):

        1. toda transição δ(q, a, X) = (p, γ) tem q, p ∈ Q, a ∈ Σ ∪ {ε}, X ∈ Γ e
           γ ∈ Γ* (representada como tupla);
        2. ε ∉ Σ (nem ``None`` nem ``""``), q0 ∈ Q, Z0 ∈ Γ e F ⊆ Q;
        3. não há duas transições para a mesma chave (q, a, X) (não determinismo);
        4. se existe δ(q, ε, X), não existe δ(q, a, X) para nenhum a ∈ Σ
           (não determinismo: o APD poderia ler ``a`` ou não ler nada).

        Ao final, ``self.delta`` contém δ como dicionário ``(q, a, X) -> Transicao``.
        """
        for transicao in self._transicoes:
            self._validar_simbolos(transicao)                    # regra 1
        self._validar_componentes()                              # regra 2
        self.delta = _montar_delta(self._transicoes)             # regra 3
        _validar_epsilon(self.delta)                             # regra 4

    def _validar_simbolos(self, transicao: Transicao) -> None:
        """Regra 1: cada componente de δ(q, a, X) = (p, γ) pertence a Q, Σ ou Γ.

        γ precisa ser uma ``tuple``: ``_aplicar`` concatena γ com o resto da pilha
        (também uma tupla), e uma lista ali causaria ``TypeError`` em ``executar``.
        """
        problema = None
        if transicao.origem not in self.estados:
            problema = f"o estado '{transicao.origem}' não pertence a Q"
        elif transicao.destino not in self.estados:
            problema = f"o estado '{transicao.destino}' não pertence a Q"
        elif transicao.le is not EPSILON and transicao.le not in self.alfabeto_entrada:
            problema = f"'{transicao.le}' não pertence a Σ"
        elif transicao.topo not in self.alfabeto_pilha:
            problema = f"o topo '{transicao.topo}' não pertence a Γ"
        elif not isinstance(transicao.empilha, tuple):
            problema = (f"γ deve ser uma tupla de símbolos de Γ, mas é "
                        f"{type(transicao.empilha).__name__}")
        else:
            fora_de_gama = [s for s in transicao.empilha if s not in self.alfabeto_pilha]
            if fora_de_gama:
                problema = f"o símbolo empilhado '{fora_de_gama[0]}' não pertence a Γ"
        if problema is not None:
            raise DefinicaoInvalidaError(f"Transição {transicao}: {problema}.")

    def _validar_componentes(self) -> None:
        """Regra 2: ε ∉ Σ, q0 ∈ Q, Z0 ∈ Γ e F ⊆ Q.

        ε é a palavra vazia, não um símbolo: se estivesse em Σ, δ(q, ε, X) e
        δ(q, a, X) deixariam de ser distinguíveis. Aqui ε é ``None`` e a cadeia
        ``""`` também representaria a palavra vazia, então ambos são recusados.
        """
        vazios = [repr(s) for s in (EPSILON, "") if s in self.alfabeto_entrada]
        if vazios:
            raise DefinicaoInvalidaError(
                f"ε não pode pertencer a Σ: Σ contém {' e '.join(vazios)}, que "
                "representa a palavra vazia.")
        if self.estado_inicial not in self.estados:
            raise DefinicaoInvalidaError(
                f"O estado inicial q0 = '{self.estado_inicial}' não pertence a Q.")
        if self.simbolo_inicial_pilha not in self.alfabeto_pilha:
            raise DefinicaoInvalidaError(
                f"O símbolo inicial da pilha Z0 = '{self.simbolo_inicial_pilha}' "
                "não pertence a Γ.")
        fora_de_q = self.estados_finais - self.estados
        if fora_de_q:
            raise DefinicaoInvalidaError(
                f"F ⊄ Q: os estados finais {_conjunto(fora_de_q)} não pertencem a Q.")

    # ------------------------------------------------------------------ consulta

    def transicao(self, estado: str, simbolo: str | None, topo: str) -> Transicao | None:
        """Consulta δ(q, a, X); ``simbolo=None`` consulta a ε-transição δ(q, ε, X).

        Devolve ``None`` quando δ não está definida para (q, a, X): é aí que o APD trava.
        """
        return self.delta.get((estado, simbolo, topo))

    def tabela_transicoes(self) -> list[Transicao]:
        """Todas as transições de δ, numa lista nova, na ordem em que foram dadas.

        A ordem é a do JSON (aberturas, fechamentos, conteúdo, aceitação) e é estável
        entre execuções, pois a GUI numera as linhas da tabela δ por ela.
        """
        return list(self._transicoes)

    def tupla_formal(self) -> str:
        """Texto da 7-tupla M = (Q, Σ, Γ, δ, q0, Z0, F), com conjuntos ordenados."""
        quantidade = len(self._transicoes)
        transicoes = "transição" if quantidade == 1 else "transições"
        return "\n".join([
            f"M = (Q, Σ, Γ, δ, q0, Z0, F)  —  {self.nome}",
            f"  Q  = {_conjunto(self.estados)}",
            f"  Σ  = {_conjunto(self.alfabeto_entrada)}",
            f"  Γ  = {_conjunto(self.alfabeto_pilha)}",
            f"  δ  = {quantidade} {transicoes} (ver tabela δ)",
            f"  q0 = {self.estado_inicial}",
            f"  Z0 = {self.simbolo_inicial_pilha}",
            f"  F  = {_conjunto(self.estados_finais)}",
        ])

    # ------------------------------------------------------------------ execução

    def executar(self, fita: list[Token], limite_epsilon: int = 1_000) -> Resultado:
        """Simula a computação (q0, w, Z0) ⊢* (q, ε, γ) sobre a fita ``w``.

        Pela definição, M aceita w se (q0, w, Z0) ⊢* (p, ε, α) com p ∈ F: basta que
        **alguma** configuração alcançada com a fita inteira consumida esteja em F,
        mesmo que dela ainda saiam ε-transições. Por isso, a cada iteração, olhando a
        configuração (q, w, Xβ):

        0. se w = ε (fita inteira consumida) e q ∈ F, para e **aceita**, antes de
           tentar qualquer ε-transição; assim um laço de ε a partir de um estado
           final não gera ``LIMITE_DE_PASSOS``, e uma ε-transição que sai de F não
           desfaz a aceitação;
        1. se existe δ(q, ε, X), aplica essa ε-transição sem consumir entrada (pelo
           determinismo, nesse caso não há δ(q, a, X) concorrente);
        2. senão, se ainda há tokens, lê o token ``a``; se ``a ∉ Σ`` ou δ(q, a, X) não
           está definida, o APD **trava** e a rejeição é explicada por
           ``diagnosticar``; senão aplica δ(q, a, X) e consome ``a``;
        3. se não há tokens nem ε-transição, para;
        4. mais de ``limite_epsilon`` ε-transições **seguidas** (sem consumir entrada)
           rejeitam com ``LIMITE_DE_PASSOS``. Só ε-transições podem gerar laço
           infinito, pois cada leitura consome um token; o contador zera a cada
           leitura, então o limite não restringe o tamanho da entrada.

        Ao parar com a fita consumida, aceita se q ∈ F (aceitação por estado final);
        senão rejeita com ``diagnosticar(apd, configuracao, None)``.

        Se a pilha ficar vazia, não existe topo X e, portanto, nenhum movimento: o APD
        trava. Restando tokens, rejeita com ``diagnosticar`` sobre o token atual; com a
        fita lida, vale o critério de estado final.

        Nunca levanta exceção por entrada rejeitada: a rejeição é um ``Resultado``
        com ``aceita=False``, que traz os passos feitos até o travamento.
        """
        entrada = tuple(fita)
        config = Configuracao(self.estado_inicial, 0, (self.simbolo_inicial_pilha,))
        passos: list[Passo] = []
        epsilon_seguidas = 0

        while config.pilha:
            if config.posicao == len(entrada) and config.estado in self.estados_finais:
                # (q0, w, Z0) ⊢* (p, ε, α) com p ∈ F: w é aceita (definição formal).
                return _resultado(entrada, passos, config, None)

            topo = config.pilha[0]

            movimento_epsilon = self.transicao(config.estado, EPSILON, topo)
            if movimento_epsilon is not None:
                epsilon_seguidas += 1
                if epsilon_seguidas > limite_epsilon:
                    falha = Falha(
                        TipoFalha.LIMITE_DE_PASSOS,
                        f"Limite de {limite_epsilon} ε-transições seguidas excedido "
                        f"em {config.estado} (possível laço infinito).",
                        config, None)
                    return _resultado(entrada, passos, config, falha)
                config = self._mover(passos, config, movimento_epsilon, None)
                continue

            if config.posicao >= len(entrada):
                break  # não há mais tokens nem ε-transição: o APD para

            token = entrada[config.posicao]
            movimento = None
            if token.simbolo in self.alfabeto_entrada:
                movimento = self.transicao(config.estado, token.simbolo, topo)
            if movimento is None:
                return _resultado(entrada, passos, config,
                                  diagnosticar(self, config, token))
            config = self._mover(passos, config, movimento, token)
            epsilon_seguidas = 0

        if not config.pilha and config.posicao < len(entrada):
            # Pilha vazia com entrada por ler: sem topo não há δ(q, a, X) aplicável.
            token = entrada[config.posicao]
            return _resultado(entrada, passos, config, diagnosticar(self, config, token))

        if config.estado in self.estados_finais:
            return _resultado(entrada, passos, config, None)
        return _resultado(entrada, passos, config, diagnosticar(self, config, None))

    def _mover(self, passos: list[Passo], antes: Configuracao,
               transicao: Transicao, token: Token | None) -> Configuracao:
        """Faz um movimento ``antes ⊢ depois``, registra o ``Passo`` e devolve ``depois``.

        ``token`` é ``None`` numa ε-transição (nenhum símbolo é consumido).
        """
        depois = self._aplicar(antes, transicao, consumiu=token is not None)
        passos.append(Passo(len(passos) + 1, antes, depois, transicao, token,
                            _classificar_acao(transicao)))
        return depois

    def _aplicar(self, config: Configuracao, transicao: Transicao,
                 consumiu: bool) -> Configuracao:
        """Aplica δ(q, a, X) = (p, γ): troca o topo X pela cadeia γ.

        Formalmente, (q, aw, Xβ) ⊢ (p, w, γβ). Com o topo em ``pilha[0]``, β é
        ``pilha[1:]`` e a nova pilha é ``γ + β``, com ``γ[0]`` no novo topo; γ = ε
        (tupla vazia) apenas desempilha X. A posição na fita avança 1 se o movimento
        consumiu um símbolo; numa ε-transição, ela não muda.
        """
        nova_pilha = transicao.empilha + config.pilha[1:]
        nova_posicao = config.posicao + 1 if consumiu else config.posicao
        return Configuracao(transicao.destino, nova_posicao, nova_pilha)


# ---------------------------------------------------------------------- auxiliares


def _classificar_acao(transicao: Transicao) -> Acao:
    """Classifica o efeito de δ(q, a, X) = (p, γ) sobre a pilha.

    * γ = ε        → ``DESEMPILHA`` (a pilha diminui 1);
    * γ = X        → ``MANTEM`` (a pilha não muda; ex.: δ(q0, $, Z0) = (qf, Z0));
    * γ = Y X      → ``EMPILHA`` (Y é empilhado sobre X; a pilha cresce 1);
    * outro caso   → ``SUBSTITUI``.
    """
    topo, gama = transicao.topo, transicao.empilha
    if gama == ():
        return Acao.DESEMPILHA
    if gama == (topo,):
        return Acao.MANTEM
    if len(gama) == 2 and gama[1] == topo:
        return Acao.EMPILHA
    return Acao.SUBSTITUI


def _montar_delta(transicoes: tuple[Transicao, ...]) -> dict[Chave, Transicao]:
    """Monta δ como dicionário ``(q, a, X) -> Transicao`` (regra 3 de ``validar``).

    A chave repetida é detectada **antes** de ser sobrescrita. Se a transição repetida
    é idêntica à anterior, é só uma duplicata (erro de digitação na definição); se o
    resultado (p, γ) difere, duas transições para o mesmo (q, a, X) dariam dois
    movimentos possíveis na mesma configuração: não determinismo.
    """
    delta: dict[Chave, Transicao] = {}
    for transicao in transicoes:
        chave = (transicao.origem, transicao.le, transicao.topo)
        if chave in delta:
            if delta[chave] == transicao:
                raise DefinicaoInvalidaError(
                    f"Transição duplicada: {transicao} aparece mais de uma vez.")
            raise DefinicaoInvalidaError(
                f"Não determinismo: há duas transições para "
                f"δ({_formatar_chave(chave)}): {delta[chave]} e {transicao}.")
        delta[chave] = transicao
    return delta


def _validar_epsilon(delta: dict[Chave, Transicao]) -> None:
    """Regra 4 de ``validar``: δ(q, ε, X) exclui qualquer δ(q, a, X) com a ∈ Σ.

    Com as duas definidas, na configuração (q, aw, Xβ) o APD poderia tanto ler ``a``
    quanto não ler nada: dois movimentos possíveis, ou seja, não determinismo.
    """
    com_epsilon = {(q, topo) for (q, a, topo) in delta if a is EPSILON}
    for (q, a, topo) in delta:
        if a is not EPSILON and (q, topo) in com_epsilon:
            raise DefinicaoInvalidaError(
                f"Não determinismo: existe δ({q}, {_SIMBOLO_EPSILON}, {topo}) "
                f"e também δ({q}, {a}, {topo}).")


def _formatar_chave(chave: Chave) -> str:
    """Texto ``q, a, X`` de uma chave de δ, escrevendo ε quando a = ``None``."""
    estado, simbolo, topo = chave
    return f"{estado}, {_SIMBOLO_EPSILON if simbolo is EPSILON else simbolo}, {topo}"


def _conjunto(elementos: set[str]) -> str:
    """Notação de conjunto ``{a, b, c}``, ordenada com ``sorted()`` para ser estável.

    O conjunto vazio é escrito ∅ (ex.: F = ∅).
    """
    if not elementos:
        return "∅"
    return "{" + ", ".join(sorted(elementos)) + "}"


def _resultado(entrada: tuple[Token, ...], passos: list[Passo],
               configuracao_final: Configuracao, falha: Falha | None) -> Resultado:
    """Monta o ``Resultado``: aceita exatamente quando não há ``Falha``."""
    return Resultado(aceita=falha is None, entrada=entrada, passos=tuple(passos),
                     configuracao_final=configuracao_final, falha=falha)
