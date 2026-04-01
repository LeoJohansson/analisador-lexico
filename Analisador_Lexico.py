from enum import Enum
import os

# ==========================================
# 1. DEFINIÇÕES DE CATEGORIAS DE TOKENS
# ==========================================

class TipoToken(Enum):

    PALAVRA_RESERVADA = 'PALAVRA_RESERVADA' # if, while, return...
    IDENTIFICADOR     = 'IDENTIFICADOR'     # Nomes de variáveis, funções...
    LITERAL           = 'LITERAL'           # Textos ("ola") e Números (10, 3.14)
    OPERADOR          = 'OPERADOR'          # +, -, *, /, ==, !=, =
    DELIMITADOR       = 'DELIMITADOR'       # (, ), {, }, [, ], ,, ., :
    EOF               = 'FIM_DE_ARQUIVO'    # Avisa que o código acabou
    ERRO              = 'ERRO_LEXICO'       # Símbolos inválidos ou strings abertas

# ==========================================
# 2. ESTRUTURA DO TOKEN
# ==========================================

class Token:

    """
    Representa a 'caixinha' final onde guardamos o fragmento de código reconhecido.
    """

    def __init__(self, tipo, lexema, linha, coluna):
        self.tipo = tipo      # A categoria (ex: TipoToken.OPERADOR)
        self.lexema = lexema  # O texto exato recortado do código (ex: "==")
        self.linha = linha    # Linha onde o token começou
        self.coluna = coluna  # Coluna onde o token começou

# ==========================================
# 3. O ANALISADOR LÉXICO
# ==========================================

class AnalisadorLexico:
    def __init__(self, codigo_fonte):
        self.codigo = codigo_fonte
        
        #o primeiro caractere do token atual.
        self.inicio = 0  
        #explorador que avança caractere por caractere.
        self.atual = 0   
        
        # --- RASTREAMENTO DE POSIÇÃO ---

        self.linha = 1
        self.coluna = 1
        self.inicio_coluna = 1 # Memoriza a coluna exata onde o token atual começou
        
        self.tokens = [] # Lista que vai armazenar o resultado final
        
        # Dicionário de palavras reservadas.

        self.reservadas = {
            'if', 'else', 'elif', 'while', 'for', 'def', 'return', 
            'class', 'import', 'and', 'or', 'not', 'True', 'False', 'None'
        }

    # --- FUNÇÕES DE NAVEGAÇÃO ---

    def no_final(self):

        """Verifica se o ponteiro explorador ('atual') chegou ao fim do arquivo."""

        return self.atual >= len(self.codigo)

    def avancar(self):

        """
        Consome o caractere atual e move o ponteiro 'atual' um passo para frente.
        Também é responsável por manter a contagem correta de linhas e colunas.
        """

        char = self.codigo[self.atual]
        self.atual += 1
        
        if char == '\n':
            self.linha += 1
            self.coluna = 1 # Quebrou a linha, a coluna volta pro começo
        else:
            self.coluna += 1
            
        return char

    def espiar(self):

        # Retorna o caractere atual SEM mover o ponteiro.

        if self.no_final(): return '\0' # Retorna caractere nulo se acabou o arquivo
        return self.codigo[self.atual]

    def espiar_proximo(self):

        #Olha um caractere além do 'atual'.

        if self.atual + 1 >= len(self.codigo): return '\0'
        return self.codigo[self.atual + 1]

    def combinar(self, esperado):
        
        """
        Avanço condicional. Olha o caractere atual; se for o que estamos esperando,
        ele o consome e avança.
        """

        if self.no_final() or self.codigo[self.atual] != esperado:
            return False
        
        self.atual += 1
        self.coluna += 1
        return True

    def adicionar_token(self, tipo, lexema_custom=None):

        """
        Pega a distância entre o 'inicio' e o 'atual' e recorta o código-fonte.
        Cria o Token e adiciona na lista final.
        """


        texto = lexema_custom if lexema_custom else self.codigo[self.inicio:self.atual]
        self.tokens.append(Token(tipo, texto, self.linha, self.inicio_coluna))

    # --- FUNÇÕES DE TRATAMENTO ESPECÍFICO ---

    def tratar_comentario_linha(self):
        """Avança ignorando tudo até encontrar uma quebra de linha."""
        while self.espiar() != '\n' and not self.no_final():
            self.avancar()


    def tratar_comentario_bloco(self):
        """Avança ignorando tudo até encontrar a trinca de aspas de fechamento."""
        while not self.no_final():

            # Se achar uma aspa e as próximas 3 letras formarem '"""'

            if self.espiar() == '"' and self.codigo[self.atual:self.atual+3] == '"""':
                for _ in range(3): self.avancar() # Consome o """
                return
            self.avancar()

    def tratar_string(self, delimitador):
        """Lê caracteres até encontrar a aspa de fechamento correspondente (" ou ')."""
        while self.espiar() != delimitador and not self.no_final():
            self.avancar()
        
        # Se chegou no fim do arquivo e não fechou aspas, é um erro léxico!

        if self.no_final():
            self.adicionar_token(TipoToken.ERRO, "String não finalizada")
            return
            
        self.avancar() # Consome a aspa de fechamento
        self.adicionar_token(TipoToken.LITERAL)

    def tratar_numero(self):
        """Consome dígitos. Se encontrar um ponto seguido de dígitos, consome como float."""
        while self.espiar().isdigit():
            self.avancar()

        # Verifica parte decimal

        if self.espiar() == '.' and self.espiar_proximo().isdigit():
            self.avancar() # Consome o '.'
            while self.espiar().isdigit():
                self.avancar()
        
        self.adicionar_token(TipoToken.LITERAL)

    # --- O NÚCLEO DA TRIAGEM ---

    def escanear_token(self):

        """
        Lê o primeiro caractere do token e decide para qual "caminho" a análise vai.
        """

        c = self.avancar() # Dá o primeiro passo

        # 1. Ignorar espaços em branco (eles só servem para separar tokens)

        if c in [' ', '\r', '\t', '\n']:
            return
        
        # 2. Roteamento de Comentários

        if c == '#':
            self.tratar_comentario_linha()
            return
        
        # Verifica se é o início de um comentário de bloco """

        if c == '"' and self.espiar() == '"' and self.espiar_proximo() == '"':
            for _ in range(2): self.avancar() # Consome as outras duas aspas
            self.tratar_comentario_bloco()
            return

        # 3. Delimitadores (Simples, de 1 caractere só)

        elif c in '()[]{},.:':
            self.adicionar_token(TipoToken.DELIMITADOR)

        # 4. Operadores (Alguns precisam de lookahead)

        elif c in '+-*/%': 
            self.adicionar_token(TipoToken.OPERADOR)
            
        elif c in '=!<>':

            # Se for '!', precisa obrigatoriamente ter um '=' depois. Ex: '!='

            if c == '!' and not self.combinar('='):
                self.adicionar_token(TipoToken.ERRO)
            else:

                # Se for =, < ou >, ele tenta combinar com outro = para formar ==, <=, >=

                self.combinar('=') 
                self.adicionar_token(TipoToken.OPERADOR)

        # 5. Literais (Strings)

        elif c == '"' or c == "'":
            self.tratar_string(c)

        # 6. Literais (Numéricos)

        elif c.isdigit():
            self.tratar_numero()

        # 7. Identificadores e Palavras Reservadas
        # Nomes de variáveis começam com letra ou underline

        elif c.isalpha() or c == '_':

            # Continua lendo enquanto for letra, número ou underline

            while self.espiar().isalnum() or self.espiar() == '_':
                self.avancar()
            
            # Recorta a palavra encontrada

            texto = self.codigo[self.inicio:self.atual]
            
            # Consulta no dicionário

            if texto in self.reservadas:
                self.adicionar_token(TipoToken.PALAVRA_RESERVADA)
            else:

                # Se não for é um (Identificador)

                self.adicionar_token(TipoToken.IDENTIFICADOR)

        # 8. Caractere Desconhecido (Ex: @, $)

        else:
            self.adicionar_token(TipoToken.ERRO)

    # --- O LOOP PRINCIPAL ---

    def analisar(self):

        """
        Método principal que varre o código de ponta a ponta.
        """

        while not self.no_final():


            self.inicio = self.atual
            self.inicio_coluna = self.coluna
            
            self.escanear_token()

        self.tokens.append(Token(TipoToken.EOF, "EOF", self.linha, self.coluna))
        return self.tokens

# ==========================================
# 4. FUNÇÃO DE ARQUIVOS (I/O)
# ==========================================

def processar(entrada, saida):

    """
    Lê o arquivo .py de entrada, passa pelo Analisador e salva a tabela no .txt de saída.
    """

    if not os.path.exists(entrada): return
    
    # Lê todo o código fonte de uma vez como uma grande string

    with open(entrada, 'r', encoding='utf-8') as f:
        codigo = f.read()

    # Instancia o analisador e roda a máquina

    lexer = AnalisadorLexico(codigo)
    tokens = lexer.analisar()

    # Escreve o resultado no arquivo texto com formatação tabular (alinhamento à esquerda)
    with open(saida, 'w', encoding='utf-8') as f:
        f.write(f"{'LINHA':<6} | {'COL':<4} | {'CATEGORIA':<20} | {'LEXEMA'}\n")
        f.write("-" * 60 + "\n")
        
        for t in tokens:
            f.write(f"{t.linha:<6} | {t.coluna:<4} | {t.tipo.value:<20} | {t.lexema}\n")

# Ponto de execução do script

if __name__ == "__main__":
    processar('teste.py', 'saida_tokens.txt')