import mysql.connector

def criar_tabela_usuarios(cursor):
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS usuarios (
                       id INTEGER AUTO_INCREMENT PRIMARY KEY,
                       NOME VARCHAR(100),
                       CPF VARCHAR(11),
                       RG INT,
                       CAIXA VARCHAR(6),
                       SECAO INT,
                       DATA_NAS TEXT,
                       NUMERO VARCHAR(10),
                       DATA_ADD TEXT,
                       NOME_SOCIAL BOOL
                   )
                   ''')
                   
#CPF, CAIXA e NUMERO PODEM COMEÇAR COM 0

connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password='2511',
    database='teste'
)

cursor = connection.cursor()

criar_tabela_usuarios(cursor)
connection.commit()
