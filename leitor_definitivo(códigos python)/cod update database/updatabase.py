import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
import re
import os
import datetime
import sys

current_dir = os.getcwd()
caminho_arquivo = os.path.join(current_dir, "CAMINHOS", "caminhos.txt")

if os.path.exists(caminho_arquivo):
    with open(caminho_arquivo, "r") as file:
        linhas = file.readlines()
        if len(linhas) >= 5:
            pasta, database, host, saida = [linha.strip() for linha in linhas[1:5]]
        else:
            messagebox.showwarning("Erro", "Arquivo caminhos.txt não contém informações suficientes.")
            sys.exit()
else:
    messagebox.showwarning("Erro", "Arquivo caminhos.txt não encontrado.")
    sys.exit()

class UserSearchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pesquisa de Usuários")
        self.connection = None
        self.page_size = 10
        self.current_page = 1

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.label_user = tk.Label(self, text="USUÁRIO:")
        self.label_user.grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)
        self.entry_user = tk.Entry(self)
        self.entry_user.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        self.label_password = tk.Label(self, text="SENHA:")
        self.label_password.grid(row=1, column=0, padx=10, pady=5, sticky=tk.E)
        self.entry_password = tk.Entry(self, show="*")
        self.entry_password.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        self.validar_button = tk.Button(self, text="Validar", command=self.validar)
        self.validar_button.grid(row=2, column=0, columnspan=2, pady=5)

        self.frame_pesquisa = ttk.Frame(self, padding="10")
        self.frame_pesquisa.grid(row=3, column=0, columnspan=2, pady=10)



        self.label_pesquisa_caixa = ttk.Label(self.frame_pesquisa, text="Pesquisar por Caixa:")
        self.label_pesquisa_caixa.grid(row=0, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_caixa = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_caixa.grid(row=0, column=1, pady=5, sticky=tk.W)

        self.label_pesquisa_numero = ttk.Label(self.frame_pesquisa, text="Pesquisar por Numero:")
        self.label_pesquisa_numero.grid(row=1, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_numero = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_numero.grid(row=1, column=1, pady=5, sticky=tk.W)



        self.label_pesquisa_nome = ttk.Label(self.frame_pesquisa, text="Pesquisar por Nome:")
        self.label_pesquisa_nome.grid(row=2, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_nome = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_nome.grid(row=2, column=1, pady=5, sticky=tk.W)

        self.label_pesquisa_cpf = ttk.Label(self.frame_pesquisa, text="Pesquisar por CPF:")
        self.label_pesquisa_cpf.grid(row=3, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_cpf = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_cpf.grid(row=3, column=1, pady=5, sticky=tk.W)
        self.entry_pesquisa_cpf.bind('<KeyRelease>', self.formatar_cpf)

        self.label_pesquisa_rg = ttk.Label(self.frame_pesquisa, text="Pesquisar por RG:")
        self.label_pesquisa_rg.grid(row=4, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_rg = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_rg.grid(row=4, column=1, pady=5, sticky=tk.W)

        self.botao_pesquisar = ttk.Button(self.frame_pesquisa, text="Pesquisar", command=self.buscar_usuarios)
        self.botao_pesquisar.grid(row=5, column=0, columnspan=2, pady=10)

        self.lista_pesquisa = ttk.Treeview(self.frame_pesquisa, columns=("ID", "NOME", "CPF", "RG", "CAIXA", "SECAO", "DATA_NAS", "NUMERO", "DATA"), show="headings")
        self.lista_pesquisa.grid(row=6, column=0, columnspan=2, pady=5)
        self.lista_pesquisa.heading("ID", text="ID")
        self.lista_pesquisa.heading("NOME", text="Nome")
        self.lista_pesquisa.heading("CPF", text="CPF")
        self.lista_pesquisa.heading("RG", text="RG")
        self.lista_pesquisa.heading("CAIXA", text="Caixa")
        self.lista_pesquisa.heading("SECAO", text="Seção")
        self.lista_pesquisa.heading("DATA_NAS", text="DATA NASCIMENTO")
        self.lista_pesquisa.heading("NUMERO", text="N° da Imagem da caixa")
        self.lista_pesquisa.heading("DATA", text="Data/Usuário")
        self.lista_pesquisa.column("NOME", width=325)

        self.prev_button = ttk.Button(self.frame_pesquisa, text="Anterior", command=self.prev_page)
        self.prev_button.grid(row=7, column=0, padx=5, pady=5)
        self.next_button = ttk.Button(self.frame_pesquisa, text="Próximo", command=self.next_page)
        self.next_button.grid(row=7, column=1, padx=5, pady=5)

        self.status_pesquisa = ttk.Label(self.frame_pesquisa, text="")
        self.status_pesquisa.grid(row=8, column=0, columnspan=2)

        self.status_pesquisa1 = ttk.Label(self.frame_pesquisa, text="Selecione um usuário para alterar", foreground="green")
        self.status_pesquisa1.grid(row=9, column=0, columnspan=2)

        self.label_pesquisa_novo_nome = ttk.Label(self.frame_pesquisa, text="Novo nome:")
        self.label_pesquisa_novo_nome.grid(row=10, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_novo_nome = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_novo_nome.grid(row=10, column=1, pady=5, sticky=tk.W)

        self.label_pesquisa_novo_rg = ttk.Label(self.frame_pesquisa, text="Novo rg:")
        self.label_pesquisa_novo_rg.grid(row=11, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_novo_rg = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_novo_rg.grid(row=11, column=1, pady=5, sticky=tk.W)

        self.label_pesquisa_novo_cpf = ttk.Label(self.frame_pesquisa, text="Novo cpf:")
        self.label_pesquisa_novo_cpf.grid(row=12, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_novo_cpf = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_novo_cpf.grid(row=12, column=1, pady=5, sticky=tk.W)

        self.label_pesquisa_novo_data = ttk.Label(self.frame_pesquisa, text="Novo data de nascimento:")
        self.label_pesquisa_novo_data.grid(row=13, column=0, pady=5, sticky=tk.E)
        self.entry_pesquisa_novo_data = ttk.Entry(self.frame_pesquisa)
        self.entry_pesquisa_novo_data.grid(row=13, column=1, pady=5, sticky=tk.W)

        self.botao_pesquisar1 = ttk.Button(self.frame_pesquisa, text="TROCAR", command=self.salvar_e_imprimir_dados_e_atualizar)
        self.botao_pesquisar1.grid(row=14, column=0, columnspan=2, pady=10)

    def validar(self):
        global database
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=self.entry_user.get(),
                password=self.entry_password.get(),
                database=database
            )
            messagebox.showinfo("Sucesso", "Conexão com o banco de dados estabelecida com sucesso!")
            self.buscar_usuarios()

        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro de validação. Erro: {err}")

    def salvar_e_imprimir_dados_e_atualizar(self):
        alterador = self.entry_user.get()
        self.atualizar_usuario(alterador)

    def atualizar_usuario(self, alterador):
        if self.connection is None:
            return

        cursor = self.connection.cursor()
        item_selecionado = self.lista_pesquisa.selection()

        if item_selecionado:
            if messagebox.askyesno("Confirmação", "Tem certeza que deseja atualizar o usuário?"):
                novo_nome = self.entry_pesquisa_novo_nome.get()
                novo_cpf = self.entry_pesquisa_novo_cpf.get()
                novo_rg = self.entry_pesquisa_novo_rg.get()
                novo_data = self.entry_pesquisa_novo_data.get()

                usuario_id = self.lista_pesquisa.item(item_selecionado, "values")[0]

                cursor.execute("SELECT NOME, CPF, RG, DATA_NAS FROM usuarios WHERE ID=%s", (usuario_id,))
                dados_originais = cursor.fetchone()
                nome_original, cpf_original, rg_original, data_original = dados_originais

                if novo_nome.strip():
                    cursor.execute("UPDATE usuarios SET NOME=%s WHERE ID=%s", (novo_nome, usuario_id))
                    self.connection.commit()
                    mensagem_log = f"ID {usuario_id} atualizado: Nome={nome_original} -> {novo_nome}"
                    self.registrar_log(mensagem_log, alterador)
                    self.buscar_usuarios()

                if novo_cpf.strip():
                    cursor.execute("UPDATE usuarios SET CPF=%s WHERE ID=%s", (novo_cpf, usuario_id))
                    self.connection.commit()
                    mensagem_log = f"ID {usuario_id} atualizado: CPF={cpf_original} -> {novo_cpf}"
                    self.registrar_log(mensagem_log, alterador)
                    self.buscar_usuarios()

                if novo_rg.strip():
                    cursor.execute("UPDATE usuarios SET RG=%s WHERE ID=%s", (novo_rg, usuario_id))
                    self.connection.commit()
                    mensagem_log = f"ID {usuario_id} atualizado: RG={rg_original} -> {novo_rg}"
                    self.registrar_log(mensagem_log, alterador)
                    self.buscar_usuarios()

                if novo_data.strip():
                    cursor.execute("UPDATE usuarios SET DATA_NAS=%s WHERE ID=%s", (novo_data, usuario_id))
                    self.connection.commit()
                    mensagem_log = f"ID {usuario_id} atualizado: DATA={data_original} -> {novo_data}"
                    self.registrar_log(mensagem_log, alterador)
                    self.buscar_usuarios()
                
                # Limpar os campos de entrada
                self.entry_pesquisa_novo_nome.delete(0, tk.END)
                self.entry_pesquisa_novo_cpf.delete(0, tk.END)
                self.entry_pesquisa_novo_rg.delete(0, tk.END)
                self.entry_pesquisa_novo_data.delete(0, tk.END)

                messagebox.showinfo("Sucesso", "Dados do usuário atualizados com sucesso!")
            else:
                messagebox.showwarning("Aviso", "Por favor, preencha todos os campos antes de atualizar.")
        else:
            messagebox.showwarning("Aviso", "Selecione um usuário para atualizar.")

    def registrar_log(self, mensagem, alterador):
        with open("log.txt", "a") as arquivo_log:
            data_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            arquivo_log.write(f"{alterador}: [{data_hora}] {mensagem}\n")

    def formatar_cpf(self, event):
        cpf = self.entry_pesquisa_cpf.get()
        cpf = re.sub(r'\D', '', cpf)
        formatted_cpf = ''
        for i, char in enumerate(cpf):
            if i in [3, 6]:
                formatted_cpf += '.'
            elif i == 9:
                formatted_cpf += '-'
            formatted_cpf += char
        self.entry_pesquisa_cpf.delete(0, tk.END)
        self.entry_pesquisa_cpf.insert(0, formatted_cpf)
        if len(cpf) >= 12:
            self.entry_pesquisa_cpf.delete(14, tk.END)

    def buscar_usuarios(self):
        if self.connection is None:
            return

        cursor = self.connection.cursor()

        cpf = ''.join(c for c in self.entry_pesquisa_cpf.get() if c.isdigit())
        nome = self.entry_pesquisa_nome.get().upper()
        rg = self.entry_pesquisa_rg.get()

        caixa = self.entry_pesquisa_caixa.get()
        numero =self.entry_pesquisa_numero.get()

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

        if caixa and numero:
            query_conditions.append("CAIXA LIKE %s AND NUMERO LIKE %s")
            parametros.extend(['%' + caixa + '%', '%' + numero + '%'])
        
        #if caixa:
            #query_conditions.append("CAIXA LIKE %s")
            #parametros.append('%' + caixa + '%')

        #if numero:
            #query_conditions.append("NUMERO LIKE %s")
            #parametros.append('%' + numero + '%')

        if query_conditions:
            query = "SELECT * FROM usuarios WHERE " + " OR ".join(query_conditions)
        else:
            query = "SELECT * FROM usuarios"

        try:
            cursor.execute(query, parametros)
            all_results = cursor.fetchall()

            total_pages = len(all_results) // self.page_size
            if len(all_results) % self.page_size != 0:
                total_pages += 1

            self.prev_button["state"] = "disabled" if self.current_page == 1 else "normal"
            self.next_button["state"] = "disabled" if self.current_page == total_pages else "normal"

            start_index = (self.current_page - 1) * self.page_size
            end_index = start_index + self.page_size
            results = all_results[start_index:end_index]

            self.lista_pesquisa.delete(*self.lista_pesquisa.get_children())

            for resultado in results:
                cpf = resultado[2]
                if cpf is not None:
                    formatted_cpf = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
                    resultado = list(resultado)
                    resultado[2] = formatted_cpf
                self.lista_pesquisa.insert("", "end", values=resultado)

            self.status_pesquisa.config(text=f"Página {self.current_page} de {total_pages}")

        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao buscar usuários: {err}")

    def on_closing(self):
        if messagebox.askyesno("Fechar", "Tem certeza que deseja fechar a aplicação?"):
            if self.connection is not None:
                self.connection.close()
            self.destroy()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.buscar_usuarios()

    def next_page(self):
        if self.connection is None:
            return

        cursor = self.connection.cursor()
        cpf = ''.join(c for c in self.entry_pesquisa_cpf.get() if c.isdigit())
        nome = self.entry_pesquisa_nome.get().upper()
        rg = self.entry_pesquisa_rg.get()

        caixa = self.entry_pesquisa_caixa.get()
        numero =self.entry_pesquisa_numero.get()

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
        
        if caixa and numero:
            query_conditions.append("CAIXA LIKE %s AND NUMERO LIKE %s")
            parametros.extend(['%' + caixa + '%', '%' + numero + '%'])
        
        #if caixa:
            #query_conditions.append("CAIXA LIKE %s")
            #parametros.append('%' + caixa + '%')

        #if numero:
            #query_conditions.append("NUMERO LIKE %s")
            #parametros.append('%' + numero + '%')

        if query_conditions:
            query = "SELECT * FROM usuarios WHERE " + " OR ".join(query_conditions)
        else:
            query = "SELECT * FROM usuarios"

        try:
            cursor.execute(query, parametros)
            all_results = cursor.fetchall()

            total_pages = len(all_results) // self.page_size
            if len(all_results) % self.page_size != 0:
                total_pages += 1

            if self.current_page < total_pages:
                self.current_page += 1
                self.buscar_usuarios()

        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao buscar usuários: {err}")

if __name__ == "__main__":
    app = UserSearchApp()
    app.mainloop()