import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import os
import pytesseract
import mysql.connector
import sys
import datetime
import cv2
import numpy as np
import threading
import gc
import logging
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR

# Configuração para o PaddleOCR

#as vezes esse "os" manda para a pasta raiz do usuario
#current_dir = "C:/Users/0045063/Downloads/leitorComplementar/Nova pasta"
current_dir = os.getcwd()

CONFIG = {
    "diretorio": '',  # Será substituído pelo argumento de linha de comando
    "log_file": os.path.join(current_dir, "CAMINHOS", "mudancas.txt"),
    "progress_file": os.path.join(current_dir, "CAMINHOS", "progress.txt"),
    "batch_size": 500  # Processar imagens em lotes de 500
}

log_dir = os.path.dirname(CONFIG['log_file'])
os.makedirs(log_dir, exist_ok=True)

logging.getLogger("ppocr").setLevel(logging.WARNING)

# Configuração do banco de dados, leitura do arquivo de configuração e tesseract
#caminho_arquivo = "C:/Users/0045063/Documents/leitor 2.2 (atual)/caminhos.txt"
caminho_arquivo = os.path.join(current_dir, "CAMINHOS", "caminhos.txt")
pytesseract.pytesseract.tesseract_cmd = ''
pasta, database, host, saida = '', '', '', ''
connection = None
social = False


## PARTE 1 - TESSERACT

# Função para ler os caminhos do arquivo caminhos.txt
def ler_caminhos():
    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, "r") as file:
            linhas = file.readlines()
            if len(linhas) >= 5:
                pytesseract.pytesseract.tesseract_cmd = linhas[0].strip()
                global pasta, database, host, saida
                pasta, database, host, saida = [linha.strip() for linha in linhas[1:5]]
            else:
                messagebox.showwarning("Erro", "Arquivo caminhos.txt não contém informações suficientes.")
                sys.exit()
    else:
        messagebox.showwarning("Erro", "Arquivo caminhos.txt não encontrado.")
        sys.exit()

# Função para adicionar um usuário ao banco de dados MYSQL
def adicionar_usuario(cursor, nome, cpf, rg, data_nas, caixa, numero, connection, alterador):
    global social
    data = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f" {alterador}"
    nome = nome.upper()
    secao = ''
    contador = ''.join(c for c in numero if c.isdigit())
    if int(contador) <= 666:
        secao = 1
    elif int(contador) <= 1332:
        secao = 2
    else:
        secao = 3

    # Ensure CPF, CAIXA, and NUMERO are padded with leading zeros if necessary
    cpf = cpf.zfill(11)
    caixa = caixa.zfill(6)
    numero = numero.zfill(10)

    try:
        if not social:
            cursor.execute(
                "INSERT INTO usuarios (NOME, CPF, RG, CAIXA, SECAO, DATA_NAS, NUMERO, DATA_ADD) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (nome, cpf, rg, caixa, secao, data_nas, numero, data)
            )
        else:
            nome_social = 'Possui nome social'
            cursor.execute(
                "INSERT INTO usuarios (NOME, CPF, RG, CAIXA, SECAO, DATA_NAS, NUMERO, DATA_ADD, NOME_SOCIAL) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (nome, cpf, rg, caixa, secao, data_nas, numero, data, nome_social)
            )
            social = False

        connection.commit()
    except mysql.connector.Error as err:
        print(f"Erro ao inserir dados no banco: {err}")
        
# Função para extrair o nome da imagem
def extrair_nome(imagem, texto_imagem):
    def extrair_nome_texto(texto):
        global social
        if "NOME SOCIAL" in texto:
            in_nome_social = texto.find("NOME SOCIAL")
            nome_social = texto[in_nome_social + len("NOME SOCIAL"):texto.find('\n', in_nome_social)]
            social = True
            return nome_social      
        elif "NOME" in texto:
            in_nome = texto.find("NOME")
            nome = texto[in_nome + len("NOME"):texto.find('\n', in_nome)]
            return nome
    nome_texto = extrair_nome_texto(texto_imagem)
    if nome_texto:
        return nome_texto

    texto_imagem = pytesseract.image_to_string(imagem, lang='por', config='--psm 1 --oem 3')
    nome_texto = extrair_nome_texto(texto_imagem)
    if nome_texto:
        return nome_texto
    return ''

# Função para limpar o início do nome
def limpar_inicio(vez):
    vez_list = list(vez)
    for i in range(len(vez_list)):
        if vez_list[i].isalpha():
            if i == 0 or vez_list[i-1].isalpha():
                return ''.join(vez_list[i:])
            else:
                vez_list.pop(i-1)
                return ''.join(vez_list[i-1:])
        else:
            vez_list.pop(i)
    return ''.join(vez_list)

# Função para limpar o fim do nome
def limpar_fim(vez):
    vez_list = list(vez)
    for i in range(len(vez_list) - 1, -1, -1):
        if vez_list[i].isalpha():
            if i == 0 or vez_list[i-1].isalpha():
                return ''.join(vez_list[:i+1])
            else:
                vez_list.pop(i)
        else:
            vez_list.pop(i)
    return ''.join(vez_list)

# Função para extrair o CPF da imagem
def extrair_cpf(texto_imagem, imagem):
    def extrair_cpf_texto(texto):
        if "CPF" in texto:
            index_cpf = texto.find("CPF")
            cpf = ''.join(c for c in texto[index_cpf + len("CPF"):index_cpf + len("CPF") + 17] if c.isdigit())[:11]#ou 12
            cpf = cpf.replace(" ", "")
            if len(cpf) == 11:
                return cpf
            else:
                cpf = ''
                return cpf

    cpf_texto = extrair_cpf_texto(texto_imagem)
    if cpf_texto:
        return cpf_texto
    
    texto_imagem = pytesseract.image_to_string(imagem, lang='eng', config='--psm 1 --oem 3')
    cpf_texto = extrair_cpf_texto(texto_imagem)
    if cpf_texto:
        return cpf_texto
    return ''

# Função para extrair o RG da imagem             
def extrair_rg(texto_imagem, imagem):
    def extrair_rg_texto(texto):
        if "RG" in texto:
            index_rg = texto.find("RG")
            rg_candidate = ''.join(c for c in texto[index_rg + len("RG"): index_rg + len("RG") + 9 or " "] if c.isdigit())[:7]#ou 8
            rg_candidate = rg_candidate.replace(" ", "")
            if len(rg_candidate) in [4, 5, 6, 7]:
                return rg_candidate

    rg_texto = extrair_rg_texto(texto_imagem)
    if rg_texto:
        return rg_texto

    texto_imagem = pytesseract.image_to_string(imagem, lang='eng', config='--psm 1 --oem 3')
    rg_texto = extrair_rg_texto(texto_imagem)
    if rg_texto:
        return rg_texto
    return ''

# Função para extrair a data de nascimento da imagem
def extrair_data_nas(texto_imagem, imagem):
    def extrair_data_texto(texto):
        if "DATA DE NASCIMENTO" in texto:
            index_data = texto.find("DATA DE NASCIMENTO")
            data_candidate = ''.join(c for c in texto[index_data + len("DATA DE NASCIMENTO"): index_data + len("DATA DE NASCIMENTO") + 13] if c.isdigit() or c == "/")[:10]
            if " " in data_candidate:
                data_candidate = data_candidate.replace(" ", "")
            if len(data_candidate) == 10:
                return data_candidate

    data_texto = extrair_data_texto(texto_imagem)
    if data_texto:
        return data_texto

    texto_imagem = pytesseract.image_to_string(imagem, lang='eng', config='--psm 1 --oem 3')
    data_texto = extrair_data_texto(texto_imagem)
    if data_texto:
        return data_texto
    return ''

# Função para corrigir a inclinação da imagem
def corrigir_inclinacao(img):
    # Conversão para escala de cinza
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicação de filtro de Canny para detectar bordas
    edges = cv2.Canny(img, 50, 150, apertureSize=3)
    
    # Uso da Transformada de Hough para detectar linhas
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is not None:
        # Calcula o ângulo médio das linhas detectadas
        angles = []
        for line in lines:
            for rho, theta in line:
                angle = np.degrees(theta)
                if 45 < angle < 135:  # Considera apenas linhas aproximadamente horizontais
                    angles.append(angle)
        
        if len(angles) > 0:
            median_angle = np.median(angles)
            angle_to_rotate = median_angle - 90  # Calcula o ângulo necessário para rotacionar

            # Rotaciona a imagem para corrigir a inclinação
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle_to_rotate, 1.0)
            img_corrigida = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return img_corrigida
    
    # Retorna a imagem original se não houver linhas detectadas
    return img

# Função para processar a imagem para o tesseract
def processar_imagem(filename, caminho_pasta, pasta_pai, cursor, connection, alterador):
    global saida

    caminho_imagem = os.path.join(caminho_pasta, filename)
    img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)

    if img is None:
        print(f"Error reading image: {caminho_imagem}")
        return
    
    img_corrigida = corrigir_inclinacao(img)

    texto_imagem = pytesseract.image_to_string(img_corrigida, lang='eng', config='--psm 6 --oem 3')
    texto_imagem_nome = pytesseract.image_to_string(img_corrigida, lang='por', config='--psm 6 --oem 3')

    nome = extrair_nome(img_corrigida, texto_imagem_nome)
    nome = limpar_fim(nome)
    nome = limpar_inicio(nome)

    cpf = extrair_cpf(texto_imagem, img_corrigida)
    rg = extrair_rg(texto_imagem, img_corrigida)
    data_nas = extrair_data_nas(texto_imagem, img_corrigida)

    if not nome or not cpf or not rg or not data_nas:
        destino_erro = os.path.join(saida, "arquivos", "erros", pasta_pai, filename)
        os.makedirs(os.path.dirname(destino_erro), exist_ok=True)
        cv2.imwrite(destino_erro, img_corrigida)

    destino_imagens = os.path.join(saida, "arquivos", "imagens", pasta_pai, filename)
    os.makedirs(os.path.dirname(destino_imagens), exist_ok=True)
    cv2.imwrite(destino_imagens, img_corrigida)

    adicionar_usuario(cursor, nome, cpf, rg, data_nas, pasta_pai, filename, connection, alterador)

# Função para extrair a assinatura da imagem
def extract_pen_drawing(image_path, assinaturas):
    app.after(0, lambda: app.status_label.config(text=f"Imagem atual: {image_path}"))

    if not os.path.isfile(image_path):
        print(f"Error: The path is not a file: {image_path}")
        return

    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error reading image: {image_path}")
        return

    height, width, _ = image.shape
    half_height = height // 2
    lower_half = image[half_height:, :]

    gray = cv2.cvtColor(lower_half, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:
            x, y, w, h = cv2.boundingRect(contour)
            area_interesse = lower_half[y:y+h, x:x+w]

            filename = os.path.basename(image_path)

            output_path = os.path.join(assinaturas, filename)

            cv2.imwrite(output_path, area_interesse)

    return

# Função para organização e levar a processar a pasta
def on_created(cursor, connection, alterador):
        
    new_folder_path = app.selected_folder

    if os.path.exists(new_folder_path):
        pasta_pai = os.path.basename(new_folder_path)

        assinaturas = os.path.join(saida, "arquivos", "assinaturas", pasta_pai)
    
        if os.path.exists(new_folder_path):
            if not os.path.exists(assinaturas):
                os.makedirs(assinaturas)
        
            todos = os.listdir(new_folder_path)
        
            for idx, filename in enumerate(todos, 1):
                file_path = os.path.join(new_folder_path, filename)
                if os.path.isfile(file_path):
                    carregamento = (idx / len(todos)) * 100
                    app.after(0, lambda: app.loading_label.config(text=f"{int(carregamento)}%"))
                
                    # Processa a imagem e extrai a assinatura
                    processar_imagem(filename, new_folder_path, pasta_pai, cursor, connection, alterador)
                    extract_pen_drawing(file_path, assinaturas)        


##PARTE 2 - PADDLEOCR


# Função para extrair o texto
def extract_text(txts, scores, key, score_threshold=0.94):
    for txt, score in zip(txts, scores):
        if key in txt.upper() and score > score_threshold:
            start_index = txt.upper().find(key) + len(key)
            extracted_text = txt[start_index:].strip()
            extracted_text = extracted_text.replace("o", "0").replace("O", "0")
            extracted_text = ''.join(c for c in extracted_text if c.isdigit())
            return extracted_text
    return ''

# Função para processar a imagem com o PaddleOCR
def pad_teste(img_path, cpf, rg):
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['PADDLEOCR'] = '/whl'

    ocr = PaddleOCR(
        det_model_dir=os.path.join(os.environ['PADDLEOCR'], 'det', 'en', 'en_PP-OCRv3_det_infer'),
        rec_model_dir=os.path.join(os.environ['PADDLEOCR'], 'rec', 'en', 'en_PP-OCRv3_rec_infer'),
        cls_model_dir=os.path.join(os.environ['PADDLEOCR'], 'cls', 'cls_infer'),
        use_angle_cls=True, lang='en'
    )

    image = Image.open(img_path).convert('RGB')
    img_array = np.array(image)
    img_array = img_array[:, :, ::-1].copy()  # Convert RGB to BGR

    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)  # Convert BGR back to RGB
    img_array = Image.fromarray(img_array)
    img_array = ImageEnhance.Contrast(img_array).enhance(1.5)
    img_array = ImageEnhance.Sharpness(img_array).enhance(2.0)

    img_array = np.array(img_array)
    img_array = img_array[:, :, ::-1].copy()  # Convert RGB to BGR for PaddleOCR

    result = ocr.ocr(img_array, cls=True)
    
    txts = [line[1][0] for line in result[0]]
    scores = [line[1][1] for line in result[0]]

    if not cpf:
        cpf = extract_text(txts, scores, "CPF")
    
    if not rg:
        rg = extract_text(txts, scores, "RG")
    
    del image, img_array, result, txts, scores
    gc.collect()
    
    return cpf, rg

# Função para anotação
def ultima_pasta():
    if not CONFIG['diretorio'] or not os.path.exists(CONFIG['diretorio']):
        raise FileNotFoundError(f"Invalid directory path: '{CONFIG['diretorio']}'")
    
    pastas = [nome for nome in os.listdir(CONFIG['diretorio']) if os.path.isdir(os.path.join(CONFIG['diretorio'], nome))]
    return pastas[-1] if pastas else None

# Função para log do progresso
def log_progress(pasta_pai, file_index, cont):
    ultima = ultima_pasta()
    with open(CONFIG['progress_file'], 'w') as f:
        if pasta_pai == ultima:
            cont = 1
        if pasta_pai == " " and file_index == 0 and cont == 1:
            f.write("finalizado")
        else:
            f.write(f"{pasta_pai},{file_index}\n")

# Função para log de mudanças a serem feitas no banco de dados
def log_changes(caixa, numero, campo, valor_antigo, valor_novo):
    with open(CONFIG['log_file'], 'a') as f:
        f.write(f"CAIXA: {caixa}, NUMERO: {numero}, CAMPO: {campo}, ANTIGO: {valor_antigo}, NOVO: {valor_novo}\n")

# Função para adicionar o usuário ao log
def adicionar_usuario2(cursor, cpf, rg, pasta_pai, file, connection):
    cursor.execute("SELECT CPF, RG FROM usuarios WHERE CAIXA = %s AND NUMERO = %s", 
                   (pasta_pai, file))
    result = cursor.fetchone()
    
    if result:
        db_cpf, db_rg = result
        
        db_cpf = str(db_cpf).strip()
        db_rg = str(db_rg).strip()
        if rg is not None:
            rg = str(rg).strip()
        if cpf is not None:
            cpf = str(cpf).strip()

        if rg is not None and db_rg != rg:
            log_changes(pasta_pai, file, "RG", db_rg, rg)
        
        if cpf is not None and db_cpf != cpf:
            log_changes(pasta_pai, file, "CPF", db_cpf, cpf)

# Função para processar a imagem
def processar_imagem2(files, caminho_pasta, pasta_pai, cursor, connection, start_index=0, end_index=None, progress_callback=None, total_files=1, progresso_app=None):
    cont = 0
    end_index = end_index or len(files)
    for file_index, file in enumerate(files[start_index:end_index], start=start_index):
        caminho_imagem = os.path.join(caminho_pasta, file)
        try:
            # Check if the connection is still alive
            if not connection.is_connected():
                connection.reconnect(attempts=3, delay=5)
                cursor = connection.cursor()

            img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError("Error reading image")

            cpf, rg = pad_teste(caminho_imagem, '', '')
            if cpf or rg:
                adicionar_usuario2(cursor, cpf, rg, pasta_pai, file, connection)
        
        except Exception as e:
            with open(CONFIG['log_file'], 'a') as f:
                f.write(f"Error processing image {caminho_imagem}: {e}\n")
            continue
        
        # Update progress
        cont += 1
        progress = cont / total_files * 100
        if progress_callback:
            progress_callback(progress)
        if progresso_app:
            progresso_app.update_progress(progress, file)
    
    log_progress(" ", 0, cont)  # Reset progress to indicate completion
    return True  # Indicate that processing is complete

# Função para iniciar o processamento
def start_processing(diretorio, start_index, end_index, progress_callback, connection, cursor, progresso_app):
    CONFIG['diretorio'] = diretorio  # Set the directory path in the CONFIG dictionary
    threading.Thread(target=contar_arquivos, args=(CONFIG['diretorio'], start_index, end_index, progress_callback, connection, cursor, progresso_app)).start()

# Função para contar os arquivos e organizar
def contar_arquivos(diretorio, start_index, end_index, progress_callback, connection, cursor, progresso_app):

    total_files = sum(len(files) for _, _, files in os.walk(diretorio))
    processed_files = 0

    for root, dirs, files in os.walk(diretorio):
        pasta_pai = os.path.basename(root)
        if not processar_imagem2(files, root, pasta_pai, cursor, connection, start_index, end_index, progress_callback, total_files, progresso_app):
            return  # Stop processing if the batch is incomplete
        processed_files += len(files)
        progress_callback(processed_files / total_files * 100)
        gc.collect()


##PARTE 3 - TKINTER


# Classe para a janela de progresso  
class ProgressoApp(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Progresso")
        self.geometry("300x150")
        
        self.progress_label = tk.Label(self, text="Progresso: 0.00%")
        self.progress_label.pack(pady=10)
        
        self.file_label = tk.Label(self, text="Arquivo: Nenhum")
        self.file_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.pack(pady=10)
        
    def update_progress(self, progress, file):
        self.progress_label.config(text=f"Progresso: {progress:.2f}%")
        self.file_label.config(text=f"Arquivo: {file}")
        self.progress_bar['value'] = progress

# Classe para a aplicação principal
class ValidadorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Validador de Pasta")
        
        # Adicionando os widgets
        self.entry_user = tk.Entry(self)
        self.entry_password = tk.Entry(self, show="*")
        self.resultado_label = tk.Label(self, text="")
        self.status_label = tk.Label(self, text="")
        self.loading_label = tk.Label(self, text="")  # Adicionando o loading_label
        
        self.entry_user.pack()
        self.entry_password.pack()
        self.resultado_label.pack()
        self.status_label.pack()
        self.loading_label.pack()  # Empacotando o loading_label
        
        # Botão para selecionar pasta
        self.select_folder_button = tk.Button(self, text="Selecionar Pasta", command=self.selecionar_pasta)
        self.select_folder_button.pack()
        
        # Botão para iniciar processamento
        self.process_button = tk.Button(self, text="Validar e Iniciar Processamento", command=self.iniciar_processamento)
        self.process_button.pack()
        
        self.selected_folder = ""

    def selecionar_pasta(self):
        self.selected_folder = filedialog.askdirectory()
        self.status_label.config(text=f"Pasta selecionada: {self.selected_folder}")

    def iniciar_processamento(self):
        if self.selected_folder:
            threading.Thread(target=self.processar_pasta).start()
        else:
            self.status_label.config(text="Por favor, selecione uma pasta primeiro.")

    def processar_pasta(self):
        try:
            connection = mysql.connector.connect(
                host=host,
                user=self.entry_user.get(),
                password=self.entry_password.get(),
                database=database
            )
            cursor = connection.cursor()
            alterador = self.entry_user.get()
            
            on_created(cursor, connection, alterador)
            
        except mysql.connector.Error as err:
            error_message = "Erro durante o processamento. Error: {}".format(err)
            self.after(0, lambda: self.status_label.config(text=error_message))
        finally:
            start_index = 0
            end_index = None
            progresso_app = ProgressoApp(self)
            progresso_app.update()
            progress_callback = lambda progress: progresso_app.update_progress(progress, "")

            start_processing(self.selected_folder, start_index, end_index, progress_callback, connection, cursor, progresso_app)

            if connection.is_connected():
                cursor.close()
                connection.close()

# Função principal
if __name__ == "__main__":
    ler_caminhos()
    app = ValidadorApp()
    app.mainloop()
