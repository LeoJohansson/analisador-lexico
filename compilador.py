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
# 4. TABELA DE SÍMBOLOS
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

        # --- GERAÇÃO DE CÓDIGO (feita junto com o parsing, tradução dirigida pela sintaxe) ---
        self.codigo_gerado = []   # lista de instruções emitidas durante o parsing
        self.contador_temp = 0    # contador para nomear temporários T1, T2, T3...

    # --- GERAÇÃO DE CÓDIGO ---
    def novo_temp(self):
        """ Gera o nome de um novo registrador/variável temporária """
        self.contador_temp += 1
        return f"T{self.contador_temp}"

    def emitir(self, instrucao):
        """ Adiciona uma instrução à lista de código gerado, na hora em que a regra gramatical é reduzida """
        self.codigo_gerado.append(instrucao)

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
            expr_nodo, _, local = self.expressao()
            self.emitir(f"RETURN {local}")           # <-- código emitido assim que o 'return' é reduzido
            return ('RETURN', expr_nodo)
        
        if (self.verificar_tipo(TipoToken.IDENTIFICADOR) and 
            self.atual + 1 < len(self.tokens) and 
            self.tokens[self.atual + 1].lexema == '='):
            return self.atribuicao()

        expr_nodo, _, _ = self.expressao()
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

        self.emitir("")
        self.emitir(f"FUNC {nome}:")             # <-- cabeçalho emitido assim que 'def nome' é reconhecido

        parametros = []
        if self.verificar('('):
            self.avancar()
            if not self.verificar(')'):
                if self.verificar_tipo(TipoToken.IDENTIFICADOR):
                    param = self.avancar().lexema
                    parametros.append(param)
                    self.tabela.declarar(param, 'int')
                    self.emitir(f"  PARAM {param}")       # <-- cada parâmetro emitido ao ser reconhecido
                while self.verificar(','):
                    self.avancar()
                    if self.verificar_tipo(TipoToken.IDENTIFICADOR):
                        param = self.avancar().lexema
                        parametros.append(param)
                        self.tabela.declarar(param, 'int')
                        self.emitir(f"  PARAM {param}")
            self.consumir(')', "Esperado ')'")
        if self.verificar(':'): self.avancar()
        corpo = [self.declaracao()] if not self.no_final() else []   # corpo já emite seu próprio código ao ser parseado

        self.emitir(f"ENDFUNC {nome}")            # <-- fim da função emitido após o corpo ser totalmente parseado

        self.tabela.simbolos = escopo_anterior 
        return ('FUNCAO', nome, parametros, corpo)

    def atribuicao(self):
        nome = self.avancar()
        self.consumir('=', "Esperado '='")
        expr_nodo, expr_tipo, local = self.expressao()
        
        if self.tabela.existe(nome.lexema):
            self.warnings.append(f"[Linha {nome.linha}] Aviso Semântico: Reatribuição/Redeclaração da variável '{nome.lexema}'.")
        
        self.tabela.declarar(nome.lexema, expr_tipo) 

        self.emitir(f"STORE {nome.lexema}, {local}")   # <-- código emitido assim que a atribuição é reduzida

        return ('ATRIBUICAO', nome.lexema, expr_nodo)

    def expressao(self): return self.termo()

    # Cada regra devolve (nó_da_arvore, tipo_inferido, local_onde_o_valor_esta)
    # 'local' é um temporário (T1, T2...) ou o nome de uma variável já existente

    def termo(self):
        expr, tipo_esq, local_esq = self.fator()
        while self.verificar('+') or self.verificar('-'):
            operador = self.avancar()
            prox_expr, tipo_dir, local_dir = self.fator()
            tipo_esq = self.inferir_tipo_binario(tipo_esq, tipo_dir)
            expr = ('BINARIA', operador.lexema, expr, prox_expr)

            # --- código emitido assim que esta regra (termo -> termo +- fator) é reduzida ---
            temp = self.novo_temp()
            instrucao = 'ADD' if operador.lexema == '+' else 'SUB'
            self.emitir(f"{instrucao} {temp}, {local_esq}, {local_dir}")
            local_esq = temp

        return expr, tipo_esq, local_esq

    def fator(self):
        expr, tipo_esq, local_esq = self.primario()
        while self.verificar('*') or self.verificar('/'):
            operador = self.avancar()
            prox_expr, tipo_dir, local_dir = self.primario()
            tipo_esq = self.inferir_tipo_binario(tipo_esq, tipo_dir)
            expr = ('BINARIA', operador.lexema, expr, prox_expr)

            # --- código emitido assim que esta regra (fator -> fator */ primario) é reduzida ---
            temp = self.novo_temp()
            instrucao = 'MUL' if operador.lexema == '*' else 'DIV'
            self.emitir(f"{instrucao} {temp}, {local_esq}, {local_dir}")
            local_esq = temp

        return expr, tipo_esq, local_esq

    def primario(self):
        token = self.token_atual()
        if token.tipo == TipoToken.PALAVRA_RESERVADA:
            self.avancar()
            temp = self.novo_temp()
            self.emitir(f"MOV {temp}, {token.lexema}")
            return ('KEYWORD', token.lexema), 'keyword', temp

        if token.tipo == TipoToken.NUMERO:
            self.avancar()
            temp = self.novo_temp()
            self.emitir(f"MOV {temp}, {token.lexema}")     # <-- constante carregada assim que é reconhecida
            return ('NUMERO', token.lexema), ('float' if '.' in token.lexema else 'int'), temp

        if token.tipo == TipoToken.STRING:
            self.avancar()
            temp = self.novo_temp()
            self.emitir(f"MOV {temp}, {token.lexema}")
            return ('STRING', token.lexema), 'string', temp
        
        if token.tipo == TipoToken.IDENTIFICADOR:
            self.avancar()
            if not self.tabela.existe(token.lexema):
                self.erros.append(f"[Linha {token.linha}] Erro Semântico: A variável '{token.lexema}' não foi declarada.")
                return ('VARIAVEL', token.lexema), 'unknown', token.lexema
            
            self.variaveis_usadas[token.lexema] = True

            # variável já tem endereço próprio: não precisa de MOV, seu local é o próprio nome
            return ('VARIAVEL', token.lexema), self.tabela.obter_tipo(token.lexema), token.lexema
            
        if token.lexema == '(':
            self.avancar()
            expr, tipo, local = self.expressao()
            self.consumir(')', "Esperado ')'")
            return expr, tipo, local
        raise Exception(f"[Linha {token.linha}] Token inesperado: {token.lexema}")


# ==========================================
# 6. PROCESSAMENTO E EXECUÇÃO
# ==========================================

def processar(entrada, saida_tokens, saida_ast, saida_tabela, saida_codigo):
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
            
    print(f"Árvore Sintática gravada com sucesso em: '{saida_ast}'")

    if parser.warnings:
        print("\n" + "="*50)
        print(f"⚠️  AVISOS SEMÂNTICOS (WARNINGS): {len(parser.warnings)}")
        print("="*50)
        for aviso in parser.warnings:
            print(f" - {aviso}")

    if parser.erros:
        print("\n" + "="*50)
        print(f"❌ ERROS ENCONTRADOS (Sintáticos e Semânticos): {len(parser.erros)}")
        print("="*50)
        for erro in parser.erros:
            print(f" - {erro}")

    # 4. EXIBIR E GRAVAR TABELA DE SÍMBOLOS
    
    cabecalho = f"{'IDENTIFICADOR':<20} | {'TIPO INFERIDO'}\n" + "-" * 45
    
    with open(saida_tabela, 'w', encoding='utf-8') as f:
        f.write("="*45 + "\n")
        f.write("  TABELA DE SÍMBOLOS COM INFERÊNCIA DE TIPOS  \n")
        f.write("="*45 + "\n\n")
        f.write(cabecalho + "\n")
        
        if not parser.tabela.simbolos:
            f.write("Nenhum símbolo registrado.\n")
        else:
            # Grava a tabela silenciosamente apenas no arquivo txt
            for simbolo, tipo in sorted(parser.tabela.simbolos.items()):
                linha_formatada = f"{simbolo:<20} | {tipo}"
                f.write(linha_formatada + "\n")
                
    print(f"\nTabela de Símbolos gravada com sucesso em: '{saida_tabela}'")

    # 5. GRAVAR CÓDIGO GERADO
    # O código NÃO é gerado aqui: ele já foi produzido instrução por instrução
    # dentro do próprio Parser (em atribuicao, termo, fator, primario, etc.),
    # à medida que cada regra da gramática era reduzida durante o parsing.
    # Aqui só pegamos o resultado acumulado em parser.codigo_gerado.
    with open(saida_codigo, 'w', encoding='utf-8') as f:
        f.write("; ===== CÓDIGO GERADO (durante o parsing) =====\n")
        f.write("\n".join(parser.codigo_gerado))
        f.write("\n; ===== FIM =====\n")

    print(f"Código gerado gravado com sucesso em: '{saida_codigo}'")
    if parser.erros:
        print("⚠️  Atenção: o código foi gerado mesmo havendo erros sintáticos/semânticos.")


if __name__ == "__main__":
    processar('teste.py', 'saida_tokens.txt', 'saida_ast.txt', 'saida_tabela.txt', 'saida_codigo.asm')