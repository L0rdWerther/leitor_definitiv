from flask import Flask, request, render_template
import mysql.connector

app = Flask(__name__)

class UserSearch:
    def __init__(self, connection):
        self.connection = connection

    def buscar_usuarios(self, cpf=None, nome=None, rg=None):
        cursor = self.connection.cursor()

        query_conditions = []
        parametros = []

        if cpf:
            query_conditions.append("CPF LIKE %s")
            parametros.append('%' + cpf + '%')

        if nome:
            query_conditions.append("NOME LIKE %s")
            parametros.append('%' + nome + '%')

        if rg:
            query_conditions.append("RG LIKE %s")
            parametros.append('%' + rg + '%')

        select_columns = "NOME, CPF, RG, CAIXA, SECAO"

        query = f"SELECT {select_columns} FROM usuarios"
        if query_conditions:
            query += " WHERE " + " OR ".join(query_conditions)

        cursor.execute(query, parametros)
        all_results = cursor.fetchall()
        cursor.close()
        return all_results

@app.route("/")
def autenticacao():
    return render_template("autenticacao.html")

@app.route("/index", methods=["POST"])
def index():
    user = request.form.get("user")
    password = request.form.get("password")
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user=user,
            password=password,
            database='fichas'
        )
        connection.close()
    except mysql.connector.Error as err:
        return render_template("erro_autenticacao.html", error=str(err))

    return render_template("pesquisa.html", user=user, password=password)

@app.route("/resultado", methods=["POST"])
def resultado():
    nome = request.form.get("nome")
    cpf = request.form.get("cpf")
    rg = request.form.get("rg")
    user = request.form.get("user")
    password = request.form.get("password")
    
    connection = mysql.connector.connect(
        host='localhost',
        user=user,
        password=password,
        database='fichas'
    )
    
    try:
        user_search = UserSearch(connection)
        resultados = user_search.buscar_usuarios(cpf, nome, rg)
    finally:
        connection.close()

    return render_template("resultado.html", resultados=resultados)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  # ESSA VERSÃO RODA NA REDE


"""
GET: Solicita os dados de um recurso especificado.
POST: Submete dados para serem processados ​​para um recurso especificado.
PUT: Atualiza os dados de um recurso especificado.
DELETE: Exclui um recurso especificado.
PATCH: Aplica modificações parciais a um recurso especificado.
OPTIONS: Descreve as opções de comunicação para o recurso alvo.
HEAD: Retorna apenas cabeçalhos HTTP sem o corpo da resposta.
"""
