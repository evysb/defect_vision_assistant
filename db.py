import os
import re
import sqlite3
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "defeitos.db")

def get_db_path(db_path=None):
    return db_path if db_path else DEFAULT_DB_PATH

def init_db(db_path=None):
    """Inicializa o banco de dados criando a tabela de defeitos."""
    path = get_db_path(db_path)
    
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS defeitos (
                id          TEXT PRIMARY KEY,
                data        TEXT NOT NULL,
                tipo        TEXT NOT NULL,
                localizacao TEXT NOT NULL,
                severidade  TEXT NOT NULL,
                causa       TEXT,
                acao        TEXT,
                imagem_path TEXT
            )
        """)
        
        # Índices para otimização
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_defeitos_tipo ON defeitos(tipo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_defeitos_severidade ON defeitos(severidade)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_defeitos_data ON defeitos(data)")
        
        conn.commit()
    finally:
        conn.close()

def salvar_defeito(defeito_data: dict, imagem_path: str, db_path=None) -> str:
    """
    Salva um defeito no banco de dados SQLite.
    Garante o mapeamento dos campos JSON internos para as colunas do banco.
    Retorna o ID gerado ou fornecido.
    """
    path = get_db_path(db_path)
    
    # Mapeia e higieniza os campos
    id_inspecao = defeito_data.get("id_inspecao")
    if not id_inspecao:
        id_inspecao = str(uuid.uuid4())
        
    data_registro = defeito_data.get("data_registro")
    if not data_registro:
        data_registro = datetime.now().isoformat()
        
    tipo_defeito = defeito_data.get("tipo_defeito", "Não identificado").strip()
    localizacao = defeito_data.get("localizacao", "Não informada").strip()
    
    # Normalização de Severidade
    severidade = defeito_data.get("severidade", "BAIXO").strip().upper()
    if severidade not in ["CRÍTICO", "ALTO", "MÉDIO", "BAIXO"]:
        # Tenta tratar com e sem acento
        if severidade == "CRITICO":
            severidade = "CRÍTICO"
        elif severidade == "MEDIO":
            severidade = "MÉDIO"
        else:
            severidade = "BAIXO"
            
    causa_provavel = defeito_data.get("causa_provavel", "").strip()
    acao_recomendada = defeito_data.get("acao_recomendada", "").strip()
    
    conn = sqlite3.connect(path)
    try:
        cursor = conn.cursor()
        with conn:
            cursor.execute(
                """
                INSERT OR REPLACE INTO defeitos (id, data, tipo, localizacao, severidade, causa, acao, imagem_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id_inspecao, data_registro, tipo_defeito, localizacao, severidade, causa_provavel, acao_recomendada, imagem_path)
            )
        return id_inspecao
    finally:
        conn.close()

def obter_todos_defeitos(db_path=None) -> list:
    """Retorna todos os defeitos registrados ordenados por data decrescente."""
    path = get_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM defeitos ORDER BY data DESC, id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def executar_query_segura(query: str, params: tuple = (), db_path=None) -> list:
    """
    Executa uma consulta SQL SELECT de forma segura (modo leitura),
    bloqueando comandos modificadores ou potencialmente perigosos.
    """
    path = get_db_path(db_path)
    
    # 1. Limpar comentários para validação correta do início da query
    cleaned_query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    cleaned_query = re.sub(r'--.*$', '', cleaned_query, flags=re.MULTILINE)
    cleaned_query = cleaned_query.strip()
    
    # 2. Validar se começa com SELECT
    if not cleaned_query.upper().startswith("SELECT"):
        raise ValueError("Operação não permitida. Apenas consultas SELECT são autorizadas.")
        
    # 3. Bloqueio de comandos destrutivos ou de modificação
    forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "PRAGMA", "ATTACH", "REPLACE", "CREATE"]
    for kw in forbidden_keywords:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, cleaned_query, re.IGNORECASE):
            raise ValueError(f"Comando de segurança bloqueou a palavra-chave não autorizada: '{kw}'.")
            
    # 4. Abrir conexão somente leitura usando URI sqlite3
    if not os.path.exists(path):
        init_db(path)
        
    abs_path = os.path.abspath(path)
    uri = f"file:{abs_path}?mode=ro"
    
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
