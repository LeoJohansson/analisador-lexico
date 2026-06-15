from enum import Enum
import os

# ==========================================
# 1. DEFINIÇÕES DE TOKENS
# ==========================================

class TipoToken(Enum):
    PALAVRA_RESERVADA = 'PALAVRA_RESERVADA'
    IDENTIFICADOR     = 'IDENTIFICADOR'
    NUMERO            = 'NUMERO'
    STRING            = 'STRING'
    OPERADOR          = 'OPERADOR'
    DELIMITADOR       = 'DELIMITADOR'
    EOF               = 'FIM_DE_ARQUIVO'
    ERRO              = 'ERRO_LEXICO'

# ==========================================
# 2. TOKEN
# ==========================================

class Token:
    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha
        self.coluna = coluna

    def __repr__(self):
        return f"{self.tipo.value}('{self.lexema}')"

# ==========================================
# 3. LEXER
# ==========================================

class AnalisadorLexico:
    def __init__(self, codigo_fonte):
        self.codigo = codigo_fonte
        self.inicio = 0
        self.atual = 0
        self.linha = 1
        self.coluna = 1
        self.inicio_coluna = 1
        self.tokens = []
        self.reservadas = {
            'if', 'else', 'elif', 'while', 'for', 'def', 'return',
            'class', 'import', 'from', 'as', 'with', 'in', 'try',
            'except', 'finally', 'pass', 'break', 'continue',
            'and', 'or', 'not', 'True', 'False', 'None'
        }

    # --- NAVEGAÇÃO ---

    def no_final(self):
        return self.atual >= len(self.codigo)

    def avancar(self):
        char = self.codigo[self.atual]
        self.atual += 1
        if char == '\n':
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return char

    def espiar(self):
        return '\0' if self.no_final() else self.codigo[self.atual]

    def espiar_proximo(self):
        if self.atual + 1 >= len(self.codigo):
            return '\0'
        return self.codigo[self.atual + 1]

    def combinar(self, esperado):
        if self.no_final() or self.codigo[self.atual] != esperado:
            return False
        self.atual += 1
        self.coluna += 1
        return True

    def adicionar_token(self, tipo, lexema_custom=None):
        texto = lexema_custom if lexema_custom else self.codigo[self.inicio:self.atual]
        self.tokens.append(Token(tipo, texto, self.linha, self.inicio_coluna))

    # --- COMENTÁRIOS ---

    def tratar_comentario_linha(self):
        while self.espiar() != '\n' and not self.no_final():
            self.avancar()

    def tratar_comentario_bloco(self):
        while not self.no_final():
            if self.codigo[self.atual:self.atual+3] == '"""':
                for _ in range(3): self.avancar()
                return
            self.avancar()

    # --- STRING E NÚMERO ---

    def tratar_string(self, delimitador):
        while self.espiar() != delimitador and not self.no_final():
            self.avancar()
        if self.no_final():
            self.adicionar_token(TipoToken.ERRO, "String não finalizada")
            return
        self.avancar()
        self.adicionar_token(TipoToken.STRING)

    def tratar_numero(self):
        while self.espiar().isdigit():
            self.avancar()

        if self.espiar() == '.':
            if not self.espiar_proximo().isdigit():
                self.adicionar_token(TipoToken.NUMERO)
                return
            self.avancar()
            while self.espiar().isdigit():
                self.avancar()
            if self.espiar() == '.':
                while self.espiar().isdigit() or self.espiar() == '.':
                    self.avancar()
                self.adicionar_token(TipoToken.ERRO, "Número mal formado")
                return
        self.adicionar_token(TipoToken.NUMERO)

    # --- TOKENIZAÇÃO ---

    def escanear_token(self):
        c = self.avancar()
        if c in [' ', '\r', '\t', '\n']: return
        
        if c == '#':
            self.tratar_comentario_linha()
        elif c == '"' and self.espiar() == '"' and self.espiar_proximo() == '"':
            for _ in range(2): self.avancar()
            self.tratar_comentario_bloco()
        elif c in '()[]{},.:':
            self.adicionar_token(TipoToken.DELIMITADOR)
        elif c in '+-*/%':
            self.adicionar_token(TipoToken.OPERADOR)
        elif c in '=!<>':
            if c == '!' and not self.combinar('='):
                self.adicionar_token(TipoToken.ERRO)
            else:
                self.combinar('=')
                self.adicionar_token(TipoToken.OPERADOR)
        elif c in '"\'':
            self.tratar_string(c)
        elif c.isdigit():
            self.tratar_numero()
        elif c.isalpha() or c == '_':
            while self.espiar().isalnum() or self.espiar() == '_':
                self.avancar()
            texto = self.codigo[self.inicio:self.atual]
            if texto in self.reservadas:
                self.adicionar_token(TipoToken.PALAVRA_RESERVADA)
            else:
                self.adicionar_token(TipoToken.IDENTIFICADOR)
        else:
            self.adicionar_token(TipoToken.ERRO)

    def analisar(self):
        while not self.no_final():
            self.inicio = self.atual
            self.inicio_coluna = self.coluna
            self.escanear_token()
        self.tokens.append(Token(TipoToken.EOF, 'EOF', self.linha, self.coluna))
        return self.tokens

# ==========================================
# 4. TABELA DE SÍMBOLOS (SEMÂNTICO COM TIPOS)
# ==========================================

class TabelaSimbolos:
    def __init__(self):
        self.simbolos = {} # Guarda pares chave-valor: { 'nome_da_variavel': 'tipo' }

    def declarar(self, nome, tipo):
        self.simbolos[nome] = tipo

    def existe(self, nome):
        return nome in self.simbolos

    def obter_tipo(self, nome):
        return self.simbolos.get(nome, 'unknown')

# ==========================================
# 5. PARSER + SEMÂNTICO INTEGRADO (COM WARNINGS)
# ==========================================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.atual = 0
        self.erros = []
        self.warnings = []
        self.variaveis_usadas = {}
        self.tabela = TabelaSimbolos()

    # --- NAVEGAÇÃO E AUXILIARES ---
    def token_atual(self): return self.tokens[self.atual]
    
    def no_final(self): return self.token_atual().tipo == TipoToken.EOF

    def avancar(self):
        if not self.no_final(): self.atual += 1
        return self.tokens[self.atual - 1]
    
    def verificar(self, lexema): return False if self.no_final() else self.token_atual().lexema == lexema

    def verificar_tipo(self, tipo): return False if self.no_final() else self.token_atual().tipo == tipo

    def consumir(self, lexema, mensagem):
        if self.verificar(lexema): return self.avancar()
        token = self.token_atual()
        raise Exception(f"[Linha {token.linha}] Erro Sintático: {mensagem}")
    
    def inferir_tipo_binario(self, tipo_esq, tipo_dir):
        if tipo_esq == 'float' or tipo_dir == 'float': return 'float'
        if tipo_esq == 'int' and tipo_dir == 'int': return 'int'
        return 'unknown'

    # --- LOOP PRINCIPAL ---
    def analisar(self):
        commands = []
        while not self.no_final():
            try:
                resultado = self.declaracao()
                if resultado is not None:
                    commands.append(resultado)
            except Exception as erro:
                self.erros.append(str(erro))
                self.avancar()
        
        self.verificar_variaveis_nao_utilizadas()
        
        return commands

    def verificar_variaveis_nao_utilizadas(self):
        """ Gera um warning para variáveis globais declaradas mas nunca lidas """
        for nome, tipo in self.tabela.simbolos.items():
            # Ignora funções e classes, foca apenas em variáveis numéricas/strings
            if tipo in ['int', 'float', 'string', 'unknown']:
                if nome not in self.variaveis_usadas:
                    self.warnings.append(f"A variável '{nome}' foi declarada, mas nunca foi utilizada.")

    # --- REGRAS DE GRAMÁTICA COM SEMÂNTICA ---
    def declaracao(self):
        token = self.token_atual()
        if token.tipo == TipoToken.DELIMITADOR: self.avancar(); return None
        if token.tipo == TipoToken.ERRO:
            self.avancar(); return ('ERRO', f"[Linha {token.linha}] Erro Léxico: {token.lexema}")
            
        if token.lexema == 'import': return self.declaracao_import()
        if token.lexema == 'from': return self.declaracao_from()
        if token.lexema == 'class': return self.declaracao_class()
        if token.lexema == 'def': return self.declaracao_funcao()
        if token.lexema == 'return':
            self.avancar()
            expr_nodo, _ = self.expressao()
            return ('RETURN', expr_nodo)
        
        if (self.verificar_tipo(TipoToken.IDENTIFICADOR) and 
            self.atual + 1 < len(self.tokens) and 
            self.tokens[self.atual + 1].lexema == '='):
            return self.atribuicao()

        expr_nodo, _ = self.expressao()
        return expr_nodo

    def declaracao_import(self):
        self.consumir('import', "Esperado 'import'")
        return ('IMPORT', self.avancar().lexema)

    def declaracao_from(self):
        self.consumir('from', "Esperado 'from'")
        origem = self.avancar().lexema
        self.consumir('import', "Esperado 'import'")
        return ('FROM_IMPORT', origem, self.avancar().lexema)

    def declaracao_class(self):
        self.consumir('class', "Esperado 'class'")
        nome = self.avancar().lexema
        self.tabela.declarar(nome, 'class') 
        if self.verificar(':'): self.avancar()
        return ('CLASS', nome, [self.declaracao()] if not self.no_final() else [])

    def declaracao_funcao(self):
        self.consumir('def', "Esperado 'def'")
        nome = self.avancar().lexema
        self.tabela.declarar(nome, 'function') 
        escopo_anterior = self.tabela.simbolos.copy() 
        parametros = []
        if self.verificar('('):
            self.avancar()
            if not self.verificar(')'):
                if self.verificar_tipo(TipoToken.IDENTIFICADOR):
                    param = self.avancar().lexema
                    parametros.append(param)
                    self.tabela.declarar(param, 'int')
                while self.verificar(','):
                    self.avancar()
                    if self.verificar_tipo(TipoToken.IDENTIFICADOR):
                        param = self.avancar().lexema
                        parametros.append(param)
                        self.tabela.declarar(param, 'int') 
            self.consumir(')', "Esperado ')'")
        if self.verificar(':'): self.avancar()
        corpo = [self.declaracao()] if not self.no_final() else []
        self.tabela.simbolos = escopo_anterior 
        return ('FUNCAO', nome, parametros, corpo)

    def atribuicao(self):
        nome = self.avancar()
        self.consumir('=', "Esperado '='")
        expr_nodo, expr_tipo = self.expressao()
        
        if self.tabela.existe(nome.lexema):
            self.warnings.append(f"[Linha {nome.linha}] Aviso Semântico: Reatribuição/Redeclaração da variável '{nome.lexema}'.")
        
        self.tabela.declarar(nome.lexema, expr_tipo) 
        return ('ATRIBUICAO', nome.lexema, expr_nodo)

    def expressao(self): return self.termo()

    def termo(self):
        expr, tipo_esq = self.fator()
        while self.verificar('+') or self.verificar('-'):
            operador = self.avancar()
            prox_expr, tipo_dir = self.fator()
            tipo_esq = self.inferir_tipo_binario(tipo_esq, tipo_dir)
            expr = ('BINARIA', operador.lexema, expr, prox_expr)
        return expr, tipo_esq

    def fator(self):
        expr, tipo_esq = self.primario()
        while self.verificar('*') or self.verificar('/'):
            operador = self.avancar()
            prox_expr, tipo_dir = self.primario()
            tipo_esq = self.inferir_tipo_binario(tipo_esq, tipo_dir)
            expr = ('BINARIA', operador.lexema, expr, prox_expr)
        return expr, tipo_esq

    def primario(self):
        token = self.token_atual()
        if token.tipo == TipoToken.PALAVRA_RESERVADA:
            self.avancar(); return ('KEYWORD', token.lexema), 'keyword'
        if token.tipo == TipoToken.NUMERO:
            self.avancar(); return ('NUMERO', token.lexema), 'float' if '.' in token.lexema else 'int'
        if token.tipo == TipoToken.STRING:
            self.avancar(); return ('STRING', token.lexema), 'string'
        
        if token.tipo == TipoToken.IDENTIFICADOR:
            self.avancar()
            if not self.tabela.existe(token.lexema):
                self.erros.append(f"[Linha {token.linha}] Erro Semântico: A variável '{token.lexema}' não foi declarada.")
                return ('VARIAVEL', token.lexema), 'unknown'
            
            self.variaveis_usadas[token.lexema] = True
            
            return ('VARIAVEL', token.lexema), self.tabela.obter_tipo(token.lexema)
            
        if token.lexema == '(':
            self.avancar()
            expr, tipo = self.expressao()
            self.consumir(')', "Esperado ')'")
            return expr, tipo
        raise Exception(f"[Linha {token.linha}] Token inesperado: {token.lexema}")

# ==========================================
# 6. PROCESSAMENTO E EXECUÇÃO
# ==========================================

def processar(entrada, saida_tokens, saida_ast, saida_tabela):
    if not os.path.exists(entrada):
        print("Arquivo não encontrado.")
        return

    with open(entrada, 'r', encoding='utf-8') as f:
        codigo = f.read()

    # 1. Analisador Léxico
    lexer = AnalisadorLexico(codigo)
    tokens = lexer.analisar()

    with open(saida_tokens, 'w', encoding='utf-8') as f:
        f.write(f"{'LINHA':<6} | {'COL':<4} | {'CATEGORIA':<20} | {'LEXEMA'}\n")
        f.write("-" * 70 + "\n")
        for t in tokens:
            f.write(f"{t.linha:<6} | {t.coluna:<4} | {t.tipo.value:<20} | {t.lexema}\n")

    # 2. Analisador Sintático + Semântico (Passagem Única)
    parser = Parser(tokens)
    ast = parser.analisar()

    # 3. Salvar Resultados da AST + Erros + Warnings Integrados
    with open(saida_ast, 'w', encoding='utf-8') as f:
        f.write("ÁRVORE SINTÁTICA:\n\n")
        for item in ast:
            f.write(f"{item}\n")
        
        if parser.warnings:
            f.write("\n\nAVISOS SEMÂNTICOS (WARNINGS):\n")
            print(f"\n⚠️  {len(parser.warnings)} AVISO(S) SEMÂNTICO(S) ENCONTRADO(S):")
            for aviso in parser.warnings:
                f.write(f"- {aviso}\n")
                print(f"   -> Aviso: {aviso}")
        
        if parser.erros:
            f.write("\n\nERROS ENCONTRADOS (Sintáticos e Semânticos):\n")
            for erro in parser.erros:
                f.write(f"- {erro}\n")

    # 4. EXIBIR E GRAVAR TABELA DE SÍMBOLOS
    
    cabecalho = f"{'IDENTIFICADOR':<20} | {'TIPO INFERIDO'}\n" + "-" * 45
    
    print("\n" + "="*45)
    print("  TABELA DE SÍMBOLOS COM INFERÊNCIA DE TIPOS  ")
    print("="*45)
    print(cabecalho)
    
    with open(saida_tabela, 'w', encoding='utf-8') as f:
        f.write("="*45 + "\n")
        f.write("  TABELA DE SÍMBOLOS COM INFERÊNCIA DE TIPOS  \n")
        f.write("="*45 + "\n\n")
        f.write(cabecalho + "\n")
        
        if not parser.tabela.simbolos:
            print("Nenhum símbolo registrado.")
            f.write("Nenhum símbolo registrado.\n")
        else:
            for simbolo, tipo in sorted(parser.tabela.simbolos.items()):
                linha_formatada = f"{simbolo:<20} | {tipo}"
                print(linha_formatada)
                f.write(linha_formatada + "\n")
                
    print("="*45 + "\n")
    print(f"Tabela de Símbolos gravada com sucesso em: '{saida_tabela}'")

if __name__ == "__main__":
    processar('teste.py', 'saida_tokens.txt', 'saida_ast.txt', 'saida_tabela.txt')