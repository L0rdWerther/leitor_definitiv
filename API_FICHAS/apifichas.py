from flask import Flask, request, jsonify
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

@app.route("/autenticacao", methods=["POST"])
def autenticacao():
    data = request.get_json()
    user = data.get("user")
    password = data.get("password")
    
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user=user,
            password=password,
            database='fichas'
        )
        connection.close()
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400

    return jsonify({"message": "Autenticação bem-sucedida", "user": user, "password": password}), 200

@app.route("/pesquisa", methods=["POST"])
def pesquisa():
    data = request.get_json()
    nome = data.get("nome")
    cpf = data.get("cpf")
    rg = data.get("rg")
    user = data.get("user")
    password = data.get("password")
    
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

    return jsonify({"resultados": resultados}), 200

if __name__ == "__main__":
    app.run(host='10.93.49.83', port=5000, debug=True)  # ESSA VERSÃO RODA NA REDE
