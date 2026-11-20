"""Testes do núcleo (apd/automato.py): validação do determinismo e a relação ⊢.

Os APDs são montados aqui mesmo, sem depender dos JSON de automatos/. O principal é
o de parênteses, com Σ = {(, ), x, $} e Γ = {Z0, PAR}.

Os tipos de falha detalhados (FECHAMENTO_INCOMPATIVEL etc.) são do diagnóstico
(#5); aqui só se testam ``aceita``, os passos, a configuração onde o APD travou e os
dois tipos que o núcleo garante sozinho: ESTADO_NAO_FINAL e LIMITE_DE_PASSOS. Nenhum
teste depende do texto das mensagens do diagnóstico.
"""

from __future__ import annotations

import unittest
from unittest import mock

from apd.automato import APD, _classificar_acao
from apd.modelos import (
    Acao,
    Configuracao,
    DefinicaoInvalidaError,
    Falha,
    TipoFalha,
    Token,
    Transicao,
)

TRANSICOES_PARENTESES = [
    Transicao("q0", "(", "Z0", "q0", ("PAR", "Z0")),
    Transicao("q0", "(", "PAR", "q0", ("PAR", "PAR")),
    Transicao("q0", ")", "PAR", "q0", ()),
    Transicao("q0", "x", "Z0", "q0", ("Z0",)),
    Transicao("q0", "x", "PAR", "q0", ("PAR",)),
    Transicao("q0", "$", "Z0", "qf", ("Z0",)),
]


def apd_parenteses(transicoes: list[Transicao] | None = None, **alteracoes) -> APD:
    """APD de parênteses balanceados; ``alteracoes`` troca componentes da 7-tupla."""
    componentes = dict(
        nome="parênteses",
        estados={"q0", "qf"},
        alfabeto_entrada={"(", ")", "x", "$"},
        alfabeto_pilha={"Z0", "PAR"},
        transicoes=list(TRANSICOES_PARENTESES if transicoes is None else transicoes),
        estado_inicial="q0",
        simbolo_inicial_pilha="Z0",
        estados_finais={"qf"},
        tokenizador="expressao",
        rotulos_pilha={"PAR": "("},
    )
    componentes.update(alteracoes)
    return APD(**componentes)


def fita(*simbolos: str) -> list[Token]:
    """Fita de entrada com um token por símbolo, todos na linha 1."""
    return [Token(s, s, 1, i + 1) for i, s in enumerate(simbolos)]


class TestExecucao(unittest.TestCase):
    """executar(): a computação (q0, w, Z0) ⊢* (q, ε, γ)."""

    def setUp(self):
        self.apd = apd_parenteses()

    def test_aceita_entrada_balanceada(self):
        resultado = self.apd.executar(fita("(", "x", ")", "$"))
        self.assertTrue(resultado.aceita)
        self.assertEqual(len(resultado.passos), 4)
        self.assertEqual(resultado.configuracao_final, Configuracao("qf", 4, ("Z0",)))
        self.assertIsNone(resultado.falha)
        self.assertEqual(resultado.entrada, tuple(fita("(", "x", ")", "$")))

    def test_acoes_registradas(self):
        resultado = self.apd.executar(fita("(", "(", ")", ")", "$"))
        self.assertEqual(
            [passo.acao for passo in resultado.passos],
            [Acao.EMPILHA, Acao.EMPILHA, Acao.DESEMPILHA, Acao.DESEMPILHA, Acao.MANTEM],
        )

    def test_pilha_a_cada_passo(self):
        resultado = self.apd.executar(fita("(", "(", ")", ")", "$"))
        self.assertEqual(
            [" ".join(passo.depois.pilha) for passo in resultado.passos],
            ["PAR Z0", "PAR PAR Z0", "PAR Z0", "Z0", "Z0"],
        )

    def test_passos_encadeados(self):
        """Cada passo começa onde o anterior terminou e consome um token."""
        entrada = fita("(", "x", ")", "$")
        resultado = self.apd.executar(entrada)
        anterior = Configuracao("q0", 0, ("Z0",))
        for numero, passo in enumerate(resultado.passos, start=1):
            self.assertEqual(passo.numero, numero)
            self.assertEqual(passo.antes, anterior)
            self.assertEqual(passo.depois.posicao, passo.antes.posicao + 1)
            self.assertIs(passo.token, entrada[numero - 1])
            self.assertEqual(passo.transicao, self.apd.transicao(
                passo.antes.estado, passo.token.simbolo, passo.antes.pilha[0]))
            anterior = passo.depois

    def test_pilha_nao_vazia_no_fim_rejeita(self):
        resultado = self.apd.executar(fita("(", "$"))
        self.assertFalse(resultado.aceita)
        self.assertEqual(len(resultado.passos), 1)
        self.assertIsNotNone(resultado.falha)
        self.assertEqual(resultado.falha.configuracao.pilha, ("PAR", "Z0"))
        self.assertEqual(resultado.falha.token.simbolo, "$")
        self.assertEqual(resultado.configuracao_final, Configuracao("q0", 1, ("PAR", "Z0")))

    def test_primeiro_token_sem_transicao_rejeita_sem_passos(self):
        resultado = self.apd.executar(fita(")", "$"))
        self.assertFalse(resultado.aceita)
        self.assertEqual(resultado.passos, ())
        self.assertEqual(resultado.falha.configuracao, Configuracao("q0", 0, ("Z0",)))
        self.assertEqual(resultado.falha.token.simbolo, ")")

    def test_simbolo_fora_do_alfabeto_rejeita(self):
        resultado = self.apd.executar(fita("[", "$"))
        self.assertFalse(resultado.aceita)
        self.assertEqual(resultado.passos, ())
        self.assertEqual(resultado.falha.configuracao, Configuracao("q0", 0, ("Z0",)))
        self.assertEqual(resultado.falha.token.simbolo, "[")

    def test_so_marcador_de_fim_aceita(self):
        resultado = self.apd.executar(fita("$"))
        self.assertTrue(resultado.aceita)
        self.assertEqual(len(resultado.passos), 1)
        self.assertEqual(resultado.passos[0].acao, Acao.MANTEM)

    def test_fita_vazia_rejeita_estado_nao_final(self):
        resultado = self.apd.executar([])
        self.assertFalse(resultado.aceita)
        self.assertEqual(resultado.passos, ())
        self.assertEqual(resultado.falha.tipo, TipoFalha.ESTADO_NAO_FINAL)
        self.assertIsNone(resultado.falha.token)
        self.assertEqual(resultado.configuracao_final, Configuracao("q0", 0, ("Z0",)))

    def test_rejeicao_chama_diagnosticar(self):
        """O núcleo delega a explicação da rejeição a diagnosticar(apd, config, token)."""
        entrada = fita("(", ")", ")", "$")
        falha_falsa = Falha(TipoFalha.SEM_TRANSICAO, "teste", Configuracao("q0", 2, ("Z0",)),
                            entrada[2])
        with mock.patch("apd.automato.diagnosticar", return_value=falha_falsa) as falso:
            resultado = self.apd.executar(entrada)
        falso.assert_called_once_with(self.apd, Configuracao("q0", 2, ("Z0",)), entrada[2])
        self.assertIs(resultado.falha, falha_falsa)
        self.assertEqual(len(resultado.passos), 2)


class TestEpsilon(unittest.TestCase):
    """ε-transições: prioridade, laço infinito e o contador de ε seguidas."""

    def test_laco_epsilon_gera_limite_de_passos(self):
        laco = APD("laço", {"q0", "qf"}, {"$"}, {"Z0"},
                   [Transicao("q0", None, "Z0", "q0", ("Z0",))], "q0", "Z0", {"qf"})
        resultado = laco.executar(fita("$"), limite_epsilon=50)
        self.assertFalse(resultado.aceita)
        self.assertEqual(resultado.falha.tipo, TipoFalha.LIMITE_DE_PASSOS)
        self.assertIn("50", resultado.falha.mensagem)
        self.assertEqual(len(resultado.passos), 50)
        self.assertTrue(all(passo.token is None for passo in resultado.passos))

    def test_limite_nao_restringe_entrada_longa_sem_epsilon(self):
        """Sem ε-transições, nenhuma entrada (por longa que seja) atinge o limite."""
        simbolos = ["("] * 2_500 + ["x"] + [")"] * 2_500 + ["$"]
        resultado = apd_parenteses().executar(fita(*simbolos), limite_epsilon=10)
        self.assertGreater(len(simbolos), 1_000)
        self.assertTrue(resultado.aceita)
        self.assertEqual(len(resultado.passos), len(simbolos))

    def test_epsilon_nao_consome_entrada_e_contador_zera_a_cada_leitura(self):
        # q0 lê "a" e vai para q1; q1 volta a q0 por ε. Com limite 1, cada ε é a
        # única desde a última leitura, então a entrada inteira é aceita.
        alterna = APD("alterna", {"q0", "q1", "qf"}, {"a", "$"}, {"Z0"},
                      [Transicao("q0", "a", "Z0", "q1", ("Z0",)),
                       Transicao("q1", None, "Z0", "q0", ("Z0",)),
                       Transicao("q0", "$", "Z0", "qf", ("Z0",))],
                      "q0", "Z0", {"qf"})
        resultado = alterna.executar(fita(*(["a"] * 20 + ["$"])), limite_epsilon=1)
        self.assertTrue(resultado.aceita)
        self.assertEqual(len(resultado.passos), 41)
        passo_epsilon = resultado.passos[1]
        self.assertIsNone(passo_epsilon.token)
        self.assertIsNone(passo_epsilon.transicao.le)
        self.assertEqual(passo_epsilon.depois.posicao, passo_epsilon.antes.posicao)

    def test_epsilon_depois_do_fim_da_fita(self):
        """Sem tokens, uma ε-transição ainda pode levar a um estado final."""
        fim = APD("fim", {"q0", "qf"}, {"$"}, {"Z0"},
                  [Transicao("q0", None, "Z0", "qf", ("Z0",))], "q0", "Z0", {"qf"})
        resultado = fim.executar([])
        self.assertTrue(resultado.aceita)
        self.assertEqual(resultado.configuracao_final, Configuracao("qf", 0, ("Z0",)))


class TestAceitacaoFormal(unittest.TestCase):
    """M aceita w se (q0, w, Z0) ⊢* (p, ε, α) com p ∈ F, mesmo havendo ε depois."""

    def test_aceita_ao_passar_por_final_mesmo_com_epsilon_saindo_de_f(self):
        # δ(q0, $, Z0) = (qf, Z0) e δ(qf, ε, Z0) = (q1, Z0): com "$" lido, a
        # configuração (qf, ε, Z0) já está em F, então w é aceita ali.
        apd = APD("sai de F", {"q0", "qf", "q1"}, {"$"}, {"Z0"},
                  [Transicao("q0", "$", "Z0", "qf", ("Z0",)),
                   Transicao("qf", None, "Z0", "q1", ("Z0",))],
                  "q0", "Z0", {"qf"})
        resultado = apd.executar(fita("$"))
        self.assertTrue(resultado.aceita)
        self.assertIsNone(resultado.falha)
        self.assertEqual(len(resultado.passos), 1)
        self.assertEqual(resultado.configuracao_final, Configuracao("qf", 1, ("Z0",)))

    def test_laco_epsilon_em_estado_final_aceita_sem_limite(self):
        # δ(qf, ε, Z0) = (qf, Z0) é um laço, mas (qf, ε, Z0) já satisfaz a definição.
        apd = APD("laço em F", {"q0", "qf"}, {"$"}, {"Z0"},
                  [Transicao("q0", "$", "Z0", "qf", ("Z0",)),
                   Transicao("qf", None, "Z0", "qf", ("Z0",))],
                  "q0", "Z0", {"qf"})
        resultado = apd.executar(fita("$"), limite_epsilon=5)
        self.assertTrue(resultado.aceita)
        self.assertIsNone(resultado.falha)
        self.assertEqual(len(resultado.passos), 1)

    def test_estado_final_com_fita_restante_nao_aceita_cedo(self):
        # Passar por F antes do fim da fita não basta: w precisa ser consumida.
        apd = APD("final no meio", {"q0", "qf"}, {"a", "$"}, {"Z0"},
                  [Transicao("q0", "a", "Z0", "qf", ("Z0",))],
                  "q0", "Z0", {"qf"})
        resultado = apd.executar(fita("a", "$"))
        self.assertFalse(resultado.aceita)
        self.assertEqual(resultado.falha.token.simbolo, "$")


class TestPilhaVazia(unittest.TestCase):
    """Sem topo não há δ(q, a, X) aplicável: o APD trava sem IndexError."""

    def apd_que_esvazia(self) -> APD:
        return APD("esvazia", {"q0", "qf"}, {"a", "$"}, {"Z0"},
                   [Transicao("q0", "a", "Z0", "qf", ())], "q0", "Z0", {"qf"})

    def test_pilha_vazia_com_entrada_restante_rejeita(self):
        resultado = self.apd_que_esvazia().executar(fita("a", "$"))
        self.assertFalse(resultado.aceita)
        self.assertEqual(len(resultado.passos), 1)
        self.assertEqual(resultado.falha.configuracao, Configuracao("qf", 1, ()))
        self.assertEqual(resultado.falha.token.simbolo, "$")

    def test_pilha_vazia_com_tokens_restantes_nao_levanta_excecao(self):
        # δ(q0, a, Z0) = (q1, ε) esvazia a pilha em q1 ∉ F com "a $" ainda na fita.
        apd = APD("esvazia cedo", {"q0", "q1", "qf"}, {"a", "$"}, {"Z0"},
                  [Transicao("q0", "a", "Z0", "q1", ())], "q0", "Z0", {"qf"})
        resultado = apd.executar(fita("a", "a", "$"))
        self.assertFalse(resultado.aceita)
        self.assertIsNotNone(resultado.falha)
        self.assertEqual(resultado.configuracao_final.pilha, ())
        self.assertEqual(resultado.configuracao_final, Configuracao("q1", 1, ()))

    def test_pilha_vazia_no_fim_da_fita_usa_estado_final(self):
        resultado = self.apd_que_esvazia().executar(fita("a"))
        self.assertTrue(resultado.aceita)
        self.assertEqual(resultado.configuracao_final, Configuracao("qf", 1, ()))


class TestValidacao(unittest.TestCase):
    """validar(): consistência da 7-tupla e as duas condições de determinismo."""

    def test_chave_repetida(self):
        repetida = Transicao("q0", "(", "Z0", "qf", ("Z0",))
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [repetida])
        self.assertIn("Não determinismo", str(contexto.exception))

    def test_transicao_identica_repetida_e_duplicata(self):
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [TRANSICOES_PARENTESES[0]])
        mensagem = str(contexto.exception)
        self.assertIn("Transição duplicada", mensagem)
        self.assertNotIn("Não determinismo", mensagem)

    def test_epsilon_em_sigma(self):
        for vazio in (None, ""):
            with self.subTest(vazio=vazio):
                with self.assertRaises(DefinicaoInvalidaError) as contexto:
                    apd_parenteses(alfabeto_entrada={"(", ")", "x", "$", vazio})
                self.assertIn("ε não pode pertencer a Σ", str(contexto.exception))

    def test_gama_deve_ser_tupla(self):
        transicao = Transicao("q0", ")", "Z0", "q0", ["Z0"])
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [transicao])
        self.assertIn("γ deve ser uma tupla", str(contexto.exception))

    def test_epsilon_em_conflito_com_leitura(self):
        epsilon = Transicao("q0", None, "Z0", "q0", ("Z0",))
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [epsilon])
        self.assertIn("δ(q0, ε, Z0)", str(contexto.exception))

    def test_estado_fora_de_q(self):
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [Transicao("q9", "(", "Z0", "q0", ())])
        self.assertIn("'q9' não pertence a Q", str(contexto.exception))

    def test_destino_fora_de_q(self):
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [Transicao("q0", ")", "Z0", "q9", ())])
        self.assertIn("'q9' não pertence a Q", str(contexto.exception))

    def test_topo_fora_de_gama(self):
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [Transicao("q0", "(", "COL", "q0", ())])
        self.assertIn("o topo 'COL' não pertence a Γ", str(contexto.exception))

    def test_simbolo_fora_de_sigma(self):
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [Transicao("q0", "[", "Z0", "q0", ())])
        self.assertIn("'[' não pertence a Σ", str(contexto.exception))

    def test_empilha_fora_de_gama(self):
        transicao = Transicao("q0", ")", "Z0", "q0", ("COL", "Z0"))
        with self.assertRaises(DefinicaoInvalidaError) as contexto:
            apd_parenteses(TRANSICOES_PARENTESES + [transicao])
        self.assertIn("'COL' não pertence a Γ", str(contexto.exception))

    def test_estado_inicial_fora_de_q(self):
        with self.assertRaises(DefinicaoInvalidaError):
            apd_parenteses(estado_inicial="q9")

    def test_simbolo_inicial_fora_de_gama(self):
        with self.assertRaises(DefinicaoInvalidaError):
            apd_parenteses(simbolo_inicial_pilha="Z9")

    def test_finais_fora_de_q(self):
        with self.assertRaises(DefinicaoInvalidaError):
            apd_parenteses(estados_finais={"qf", "q9"})


class TestClassificarAcao(unittest.TestCase):
    """_classificar_acao(): efeito de γ em δ(q, a, X) = (p, γ) sobre a pilha."""

    def test_cinco_casos_das_quatro_acoes(self):
        casos = {
            ("PAR", ()): Acao.DESEMPILHA,
            ("Z0", ("Z0",)): Acao.MANTEM,
            ("Z0", ("PAR", "Z0")): Acao.EMPILHA,
            ("PAR", ("COL",)): Acao.SUBSTITUI,
            ("PAR", ("A", "B", "PAR")): Acao.SUBSTITUI,
        }
        for (topo, gama), esperada in casos.items():
            with self.subTest(topo=topo, gama=gama):
                transicao = Transicao("q0", "a", topo, "q0", gama)
                self.assertEqual(_classificar_acao(transicao), esperada)


class TestConsultaEExibicao(unittest.TestCase):
    """transicao(), tabela_transicoes(), tupla_formal() e atributos expostos."""

    def setUp(self):
        self.apd = apd_parenteses()

    def test_tabela_preserva_ordem_e_devolve_lista_nova(self):
        tabela = self.apd.tabela_transicoes()
        self.assertEqual(tabela, TRANSICOES_PARENTESES)
        tabela.clear()
        self.assertEqual(self.apd.tabela_transicoes(), TRANSICOES_PARENTESES)
        self.assertIsNot(self.apd.tabela_transicoes(), self.apd.tabela_transicoes())

    def test_tupla_formal(self):
        texto = self.apd.tupla_formal()
        self.assertIn("M = (Q, Σ, Γ, δ, q0, Z0, F)", texto)
        self.assertIn("F  = {qf}", texto)
        self.assertEqual(texto, "\n".join([
            "M = (Q, Σ, Γ, δ, q0, Z0, F)  —  parênteses",
            "  Q  = {q0, qf}",
            "  Σ  = {$, (, ), x}",
            "  Γ  = {PAR, Z0}",
            "  δ  = 6 transições (ver tabela δ)",
            "  q0 = q0",
            "  Z0 = Z0",
            "  F  = {qf}",
        ]))

    def test_consulta_transicao(self):
        self.assertEqual(self.apd.transicao("q0", "(", "Z0"), TRANSICOES_PARENTESES[0])
        self.assertIsNone(self.apd.transicao("q0", ")", "Z0"))
        self.assertIsNone(self.apd.transicao("q0", None, "Z0"))

    def test_atributos_expostos(self):
        self.assertEqual(self.apd.nome, "parênteses")
        self.assertEqual(self.apd.descricao, "")
        self.assertEqual(self.apd.tokenizador, "expressao")
        self.assertEqual(self.apd.estados, {"q0", "qf"})
        self.assertEqual(self.apd.alfabeto_entrada, {"(", ")", "x", "$"})
        self.assertEqual(self.apd.alfabeto_pilha, {"Z0", "PAR"})
        self.assertEqual(self.apd.estado_inicial, "q0")
        self.assertEqual(self.apd.simbolo_inicial_pilha, "Z0")
        self.assertEqual(self.apd.estados_finais, {"qf"})
        self.assertEqual(self.apd.rotulos_pilha, {"PAR": "("})
        self.assertEqual(len(self.apd.delta), 6)
        self.assertIs(self.apd.delta[("q0", "$", "Z0")], TRANSICOES_PARENTESES[5])

    def test_rotulos_pilha_padrao_e_dict_vazio(self):
        self.assertEqual(apd_parenteses(rotulos_pilha=None).rotulos_pilha, {})


if __name__ == "__main__":
    unittest.main()
