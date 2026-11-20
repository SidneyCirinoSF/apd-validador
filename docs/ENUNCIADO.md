# Enunciado da AV2

Resumo fiel do enunciado entregue pelo professor (arquivo PDF
"AV-2 Linguagens Formais e Autômatos, 6P-CC, 2026.2, Projetos"). Quando houver dúvida,
vale o PDF original.

| | |
|---|---|
| Instituição | Centro Universitário Maurício de Nassau (UNINASSAU), unidade Paulista |
| Curso | Graduação em Ciência da Computação |
| Disciplina | Linguagens Formais e Autômatos |
| Professor | Alamy Veríssimo Pereira Jr. |
| Turma | 6º período, CC, manhã |
| Avaliação | AV2, tipo Projetos |
| Data da prova (apresentação) | 03/12/2026 (quinta-feira) |
| Desafio escolhido pelo grupo | **Desafio 4: Validador de Sintaxe e XML/JSON com Autômato com Pilha (AP)** |

## Regras gerais para todos os desafios

1. **Linguagem:** Python 3.x, usando apenas bibliotecas padrão (ou explicitadas no enunciado).
2. **Entregável 1 (Código):** aplicação executável via terminal (CLI) ou interface gráfica
   simples (tkinter), com código limpo, modularizado e comentários explicando a lógica
   formal (estados, transições, pilha ou fita).
3. **Entregável 2 (Apresentação):** slides feitos no **Prezi** (https://prezi.com),
   aproveitando o recurso de **zoom** para navegar entre a definição formal do modelo
   (M = (Q, Σ, δ, q0, F)), o diagrama de estados/transições e a demonstração prática do código.

## Critérios de avaliação

| Critério | Peso | O que é avaliado |
|---|---|---|
| 1. Corretude Formal | **35%** | O algoritmo respeita fielmente a definição matemática do modelo (ex.: não usa pilhas auxiliares em um AFD). |
| 2. Qualidade do Código em Python | **25%** | Código executável sem falhas, organizado em funções/classes e com comentários claros associando o código à teoria. |
| 3. Interface e Usabilidade | **15%** | Clareza na exibição dos passos (tabela de transição, pilha ou fita) e facilidade para testar novas entradas durante a apresentação. |
| 4. Apresentação no Prezi | **25%** | Uso adequado da narrativa visual não linear do Prezi, clareza na explicação formal e domínio técnico na demonstração ao vivo. |

## Desafio 4: Validador de Sintaxe e XML/JSON com Autômato com Pilha (AP)

**Tópico da ementa:** Linguagens Livres de Contexto (LLC) e Autômatos com Pilha.

**O problema:** Construir um simulador de Autômato com Pilha Determinístico (APD) para
validar estruturas aninhadas, como tags de abertura e fechamento de um subconjunto de
HTML/XML ou expressões matemáticas balanceadas.

**Requisitos funcionais:**

- Exibir visualmente no console o estado da pilha (empilha/desempilha) a cada símbolo
  consumido da entrada.
- Identificar o motivo exato da falha em caso de rejeição (ex.: "pilha não vazia ao fim
  da entrada" ou "tag de fechamento incompatível com o topo da pilha").

**Foco no Prezi:** Utilizar o movimento de zoom para ilustrar o crescimento e o
esvaziamento da pilha em paralelo à leitura da fita de entrada.

## Os outros desafios (para referência)

O enunciado oferecia seis desafios; o grupo escolheu o 4.

1. Simulador Universal de AFD e Conversor AFN → AFD (construção de subconjuntos).
2. Motor de Expressões Regulares "do zero" (Construção de Thompson, ε-AFN).
3. Analisador Léxico para uma Mini-Linguagem.
4. **Validador de Sintaxe e XML/JSON com Autômato com Pilha (AP).** ← escolhido
5. Gerador de Árvores de Derivação e Detector de Ambiguidade (CYK).
6. Simulador de Máquina de Turing (reconhecedor e transdutor).

## Decisões de escopo

- **Dois autômatos em vez de um.** O problema cita "tags de um subconjunto de HTML/XML
  **ou** expressões matemáticas balanceadas". O projeto faz os dois: tags `html`, `body`,
  `div`, `p`, `ul` e `li`, e expressões com `( )`, `[ ]` e `{ }`.
- **JSON.** O título do desafio fala em "XML/JSON", mas o texto do problema pede
  tags HTML/XML ou expressões balanceadas. No projeto, o JSON é usado como **formato
  de definição dos autômatos** (`automatos/*.json`). As chaves e colchetes de um
  documento JSON são cobertos estruturalmente pelo autômato de expressões, mas validar
  a gramática completa do JSON está fora do escopo.
- **Tupla formal.** O enunciado mostra a tupla de 5 elementos M = (Q, Σ, δ, q0, F), que
  é a de autômatos finitos. Para um autômato com pilha usamos a tupla de 7 elementos
  M = (Q, Σ, Γ, δ, q0, Z0, F), que acrescenta o alfabeto da pilha Γ e o símbolo inicial
  da pilha Z0. Detalhes em [DEFINICAO_FORMAL.md](DEFINICAO_FORMAL.md).
- **Interface.** As regras pedem CLI **ou** tkinter. O projeto entrega as duas; o
  requisito "exibir no console" é atendido pela CLI, e a GUI serve de apoio visual
  para a demonstração.

## Como este projeto atende a cada requisito e critério

Os nomes de arquivos e funções seguem o contrato de [ARQUITETURA.md](ARQUITETURA.md).

### Regras gerais

| Requisito | Onde é atendido |
|---|---|
| Python 3.x só com biblioteca padrão | Todo o projeto. Python 3.10+, sem `pip install` ([ARQUITETURA.md](ARQUITETURA.md) §3) |
| Executável via CLI ou tkinter | `apd/__main__.py` e `apd/cli.py` (`python -m apd`); `apd/gui.py` (`python -m apd --gui`) |
| Código limpo e modularizado | Pacote `apd/` dividido por responsabilidade: `modelos.py`, `automato.py`, `carregador.py`, `tokenizador.py`, `diagnostico.py`, `cli.py`, `gui.py` |
| Comentários explicando a lógica formal | Docstrings em toda função pública ligando o código à teoria, ex.: "Aplica δ(q, a, X) = (p, γ)" ([ARQUITETURA.md](ARQUITETURA.md) §3) |
| Apresentação no Prezi com zoom | Apresentação montada no Prezi (link a ser adicionado ao README); roteiro da demonstração ao vivo |

### Desafio 4

| Requisito | Onde é atendido |
|---|---|
| Simulador de APD | `apd/automato.py`: classe `APD`, método `executar`, a única implementação de δ do projeto |
| Ser **determinístico** | `APD.validar()` rejeita duas transições para o mesmo (q, a, X) e a coexistência de δ(q, ε, X) com δ(q, a, X); o marcador de fim `$` evita ε-transições de aceitação ([ARQUITETURA.md](ARQUITETURA.md) §4 e §6) |
| Definição formal lida de arquivo | `automatos/xml_tags.json` e `automatos/expressoes.json`, lidos e validados por `apd/carregador.py`; gerados por `ferramentas/gerar_automatos.py` |
| Validar tags de um subconjunto de HTML/XML | `automatos/xml_tags.json` + `tokenizar_xml` em `apd/tokenizador.py` |
| Validar expressões matemáticas balanceadas | `automatos/expressoes.json` + `tokenizar_expressao` em `apd/tokenizador.py` |
| Exibir no console a pilha (empilha/desempilha) a cada símbolo consumido | Cada movimento vira um `Passo` (configuração antes ⊢ depois, com a `Acao`) em `apd/modelos.py`; `apd/cli.py` exibe passo a passo, com `--passo` e `--atraso` |
| Identificar o motivo exato da falha | `apd/diagnostico.py` (`diagnosticar`), com os tipos de `TipoFalha`: pilha não vazia ao fim da entrada, fechamento incompatível com o topo da pilha, fechamento sem abertura, símbolo fora do alfabeto etc., sempre com linha e coluna |
| Foco no Prezi: crescimento e esvaziamento da pilha em paralelo à fita | `apd/gui.py` desenha a fita com o cabeçote e a pilha crescendo e diminuindo; capturas e o roteiro da demonstração alimentam o Prezi |

### Critérios de avaliação

| Critério | Peso | Como o projeto atende |
|---|---|---|
| Corretude Formal | 35% | O APD usa **uma única pilha** e segue M = (Q, Σ, Γ, δ, q0, Z0, F) à risca; δ fica nos JSON, não espalhada em `if`s; aceitação por estado final; o diagnóstico se baseia somente em δ; o determinismo é verificado ao carregar ([DEFINICAO_FORMAL.md](DEFINICAO_FORMAL.md), `apd/automato.py`) |
| Qualidade do Código | 25% | Módulos pequenos com contratos fixos ([ARQUITETURA.md](ARQUITETURA.md)); docstrings ligadas à teoria; testes com `unittest` em `tests/` (`python -m unittest discover -s tests -v`) |
| Interface e Usabilidade | 15% | CLI com menu interativo para testar novas entradas, exibição passo a passo, tabela δ (`--definicao`) e cores; GUI com fita, pilha, tabela δ com a transição usada destacada e log de passos; entradas prontas em `exemplos/` |
| Apresentação no Prezi | 25% | Narrativa não linear: definição formal → diagrama de estados → zoom na pilha durante a leitura da fita → demonstração ao vivo (Joalison monta o Prezi; Wagner prepara o roteiro da demonstração) |
