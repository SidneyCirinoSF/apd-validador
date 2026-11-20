"""Testes dos contratos de dados (apd/modelos.py).

Garantem que as classes representam fielmente os elementos de
M = (Q, Σ, Γ, δ, q0, Z0, F) e que as convenções do projeto (ε = None,
topo = pilha[0], dataclasses imutáveis) valem.
"""

import dataclasses
import unittest

from apd.modelos import (
    EPSILON,
    MARCADOR_FIM,
    Acao,
    Configuracao,
    ErroLexico,
    Falha,
    Passo,
    Resultado,
    TipoFalha,
    Token,
    Transicao,
)


class TestTransicaoStr(unittest.TestCase):
    """``str(Transicao)`` deve sair na notação δ(q, a, X) = (p, γ)."""

    def test_str_empilha(self):
        t = Transicao("q0", "<div>", "Z0", "q0", ("DIV", "Z0"))
        self.assertEqual(str(t), "δ(q0, <div>, Z0) = (q0, DIV Z0)")

    def test_str_desempilha_mostra_epsilon(self):
        t = Transicao("q0", "</p>", "P", "q0", ())
        self.assertEqual(str(t), "δ(q0, </p>, P) = (q0, ε)")

    def test_str_mantem(self):
        t = Transicao("q0", "#texto", "P", "q0", ("P",))
        self.assertEqual(str(t), "δ(q0, #texto, P) = (q0, P)")

    def test_str_epsilon_transicao(self):
        t = Transicao("q0", None, "Z0", "q1", ("Z0",))
        self.assertTrue(str(t).startswith("δ(q0, ε, "))
        self.assertEqual(str(t), "δ(q0, ε, Z0) = (q1, Z0)")

    def test_str_aceitacao(self):
        t = Transicao("q0", "$", "Z0", "qf", ("Z0",))
        self.assertEqual(str(t), "δ(q0, $, Z0) = (qf, Z0)")


class TestImutabilidadeEIgualdade(unittest.TestCase):
    def test_configuracao_imutavel(self):
        c = Configuracao("q0", 0, ("Z0",))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            c.estado = "qf"

    def test_transicao_imutavel(self):
        t = Transicao("q0", "(", "Z0", "q0", ("PAR", "Z0"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            t.destino = "qf"

    def test_todas_as_dataclasses_sao_frozen(self):
        for classe in (Transicao, Token, Configuracao, Passo, Falha, Resultado):
            with self.subTest(classe=classe.__name__):
                self.assertTrue(classe.__dataclass_params__.frozen)

    def test_transicoes_iguais_servem_de_chave_de_dicionario(self):
        a = Transicao("q0", "(", "Z0", "q0", ("PAR", "Z0"))
        b = Transicao("q0", "(", "Z0", "q0", ("PAR", "Z0"))
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertEqual({a: "ok"}[b], "ok")


class TestConvencoes(unittest.TestCase):
    def test_constantes(self):
        self.assertEqual(MARCADOR_FIM, "$")
        self.assertIsNone(EPSILON)

    def test_topo_e_o_primeiro_elemento(self):
        c = Configuracao("q0", 1, ("DIV", "Z0"))
        self.assertEqual(c.pilha[0], "DIV")
        self.assertEqual(c.pilha[-1], "Z0")
        self.assertEqual(Configuracao("q0", 0, ("Z0",)).pilha[0], "Z0")

    def test_ordem_dos_campos_do_contrato(self):
        def campos(classe):
            return [f.name for f in dataclasses.fields(classe)]

        self.assertEqual(campos(Transicao), ["origem", "le", "topo", "destino", "empilha"])
        self.assertEqual(campos(Token), ["simbolo", "lexema", "linha", "coluna"])
        self.assertEqual(campos(Configuracao), ["estado", "posicao", "pilha"])
        self.assertEqual(campos(Passo), ["numero", "antes", "depois", "transicao", "token", "acao"])
        self.assertEqual(campos(Falha), ["tipo", "mensagem", "configuracao", "token"])
        self.assertEqual(
            campos(Resultado),
            ["aceita", "entrada", "passos", "configuracao_final", "falha"],
        )


class TestEnums(unittest.TestCase):
    def test_tipo_falha_tem_sete_membros(self):
        self.assertEqual(len(TipoFalha), 7)
        self.assertEqual(
            TipoFalha.PILHA_NAO_VAZIA.value, "pilha não vazia ao fim da entrada"
        )

    def test_acao_mantem_com_acento(self):
        self.assertEqual(Acao.MANTEM.value, "mantém")
        self.assertEqual({a.name for a in Acao}, {"EMPILHA", "DESEMPILHA", "MANTEM", "SUBSTITUI"})


class TestErroLexico(unittest.TestCase):
    def test_mensagem_com_posicao(self):
        erro = ErroLexico("'<' sem '>' correspondente", 2, 7)
        self.assertEqual(str(erro), "Linha 2, coluna 7: '<' sem '>' correspondente")
        self.assertEqual(erro.mensagem, "'<' sem '>' correspondente")
        self.assertEqual(erro.linha, 2)
        self.assertEqual(erro.coluna, 7)

    def test_e_uma_excecao(self):
        with self.assertRaises(ErroLexico):
            raise ErroLexico("tag sem nome", 1, 1)


if __name__ == "__main__":
    unittest.main()
