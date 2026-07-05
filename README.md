# 🧠 Compilador Completo em Python (End-to-End)

Este projeto implementa um **compilador didático completo** desenvolvido em Python como parte da disciplina de **Compiladores**. 

O sistema cobre desde a leitura dos caracteres do código-fonte até a geração final de código de baixo nível, operando de forma resiliente mesmo diante de erros estruturais na entrada.

O compilador realiza quatro etapas principais:
- 🔎 **Análise Léxica** → Transforma o código-fonte em uma sequência de tokens.
- 🌳 **Análise Sintática** → Organiza os tokens em uma árvore através de um *Recursive Descent Parser* que gera uma AST (*Abstract Syntax Tree*).
- 🧬 **Análise Semântica** → Gerencia o escopo através de uma Tabela de Símbolos, realiza a inferência dinâmica de tipos e gera diagnósticos (avisos/erros).
- ⚙️ **Geração de Código Target** → Traduz de forma linear a AST resultante para **Assembly Baseado em Pilha (P-Code)**.

---

# 🚀 Funcionalidades Reconhecidas

O sistema reconhece e processa os seguintes elementos da linguagem (baseada na sintaxe do Python):
- 🔑 **Palavras Reservadas** (`if`, `while`, `return`, `class`, `def`, `import`, etc.)
- 🏷️ **Identificadores** (nomes de variáveis, funções e classes)
- 🔢 **Literais Numéricos e Strings** (suporte nativo a inteiros e ponto flutuante)
- ➕ **Operadores Matemáticos** (`+`, `-`, `*`, `/`) com precedência rigorosa.
- 📌 **Delimitadores** (`()`, `{}`, `[]`, `:`, `,`, `.`)
- 📄 **Recuperação de Falhas (Panic Mode)** que permite continuar a compilação mesmo sob erros sintáticos graves.

---

# 🛠️ Como Funciona cada Fase

### 1. Analisador Léxico
Utiliza a técnica de **dois ponteiros** (`inicio` e `atual`) para percorrer o arquivo caractere por caractere. Conta com um mecanismo de **Lookahead** (espiar próximo caractere) para capturar perfeitamente tokens compostos (como `==`, `!=`) e validar constantes de ponto flutuante, acusando erros específicos como números mal formados (`0.0.0`).

### 2. Analisador Sintático (Parser)
Implementado por meio da técnica de **Parser Descendente Recursivo**. Cada regra gramatical é mapeada em um método específico. O parser respeita a precedência matemática (multiplicação e divisão aninhadas abaixo da soma e subtração) e isola o corpo de funções e classes. Ele captura erros de sintaxe (como a falta de termos à direita de uma atribuição) e avança para a próxima linha de forma segura sem abortar o processo.

### 3. Analisador Semântico (Single-Pass com Tipagem)
Operando de forma integrada à sintaxe (Tradução Dirigida pela Sintaxe), ele gerencia uma **Tabela de Símbolos** dinâmica e um mapa de uso. Suas funções incluem:
* **Verificação de Declaração Prévia:** Bloqueia a leitura de variáveis que nunca foram criadas no escopo.
* **Inferência Dinâmica de Tipos:** Promove tipos de dados em expressões binárias automaticamente (ex: $int + float = float$).
* **Gerador de Warnings:** Identifica e avisa no terminal sobre reatribuições de variáveis ou identificadores que foram declarados mas estão ociosos consumindo memória.
* **Controle de Escopo Local:** Copia, isola e destrói o contexto de variáveis locais ao encerrar o processamento de funções.

### 4. Gerador de Código Target
Caminha recursivamente pela AST gerada e mapeia as estruturas hierárquicas em instruções de um **Assembly Linear Baseado em Pilha**. Ele simula o comportamento físico de uma máquina virtual gerando rótulos estruturados (`LABEL`), desvios de sub-rotinas (`RET`), manipulações diretas de empilhamento (`PUSH`, `POP`, `LOAD`) e instruções matemáticas de máquina (`ADD`, `SUB`, `MUL`, `DIV`).

---

# 📂 Estrutura das Classes do Projeto

- `TipoToken` → Enum com as categorias lexicais.
- `Token` → Estrutura do objeto que armazena tipo, lexema, linha e coluna.
- `AnalisadorLexico` → Responsável pelo fatiamento do texto em tokens.
- `TabelaSimbolos` → Dicionário interno encarregado do armazenamento de tipos e escopo do programa.
- `Parser` → Motor sintático e semântico encarregado da montagem da AST e geração de alertas.
- `GeradorCodigo` → O back-end do compilador que produz as instruções Assembly.
- `processar()` → Orquestrador central que gerencia o fluxo de arquivos de entrada e saída.

---

# ▶️ Como Executar

### 1. Prepare o arquivo de entrada
Crie o arquivo de testes contendo seu código-fonte na mesma pasta do script (ex: `teste.py`).

### 2. Execute o Compilador
```bash
python compilador.py