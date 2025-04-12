import os
import logging
import mysql.connector
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR
from contextlib import contextmanager
import gc
import threading

# Configuration
current_dir = os.getcwd()
CONFIG = {
    "diretorio": '',  # Será substituído pelo argumento de linha de comando
    "log_file": os.path.join(current_dir, "ERROS", "mudancas.txt"),
    "progress_file": os.path.join(current_dir, "ERROS", "progress.txt"),
    "batch_size": 500  # Processar imagens em lotes de 500
}

# Ensure the log directory exists
log_dir = os.path.dirname(CONFIG['log_file'])
os.makedirs(log_dir, exist_ok=True)

# Set logging level to WARNING to suppress DEBUG messages
logging.getLogger("ppocr").setLevel(logging.WARNING)

def read_db_config(file_path):
    db_config = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)  # Dividir apenas na primeira ocorrência de '='
                db_config[key] = value
            else:
                logging.warning(f"Linha malformada no arquivo de configuração: {line}")
    return db_config

@contextmanager
def get_db_connection(config):
    connection = mysql.connector.connect(**config)
    try:
        yield connection
    finally:
        connection.close()

def log_changes(caixa, numero, campo, valor_antigo, valor_novo):
    with open(CONFIG['log_file'], 'a') as f:
        f.write(f"CAIXA: {caixa}, NUMERO: {numero}, CAMPO: {campo}, ANTIGO: {valor_antigo}, NOVO: {valor_novo}\n")

def log_progress(pasta_pai, file_index, cont):
    ultima = ultima_pasta(CONFIG['diretorio'])
    with open(CONFIG['progress_file'], 'w') as f:
        if pasta_pai == ultima:
            cont = 1
        if pasta_pai == " " and file_index == 0 and cont == 1:
            f.write("finalizado")
        else:
            f.write(f"{pasta_pai},{file_index}\n")

def load_progress():
    if os.path.exists(CONFIG['progress_file']):
        with open(CONFIG['progress_file'], 'r') as f:
            content = f.read().strip()
            if content:
                return content.split(',')
    return None, 0

def ultima_pasta(diretorio):
    pastas = [nome for nome in os.listdir(diretorio) if os.path.isdir(os.path.join(diretorio, nome))]
    
    if not pastas:
        return None
    
    ultima = sorted(pastas)[-1]
    return ultima

def adicionar_usuario(cursor, cpf, rg, pasta_pai, file, connection):
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

def extract_text(txts, scores, key, score_threshold=0.94):
    for txt, score in zip(txts, scores):
        if key in txt.upper() and score > score_threshold:
            start_index = txt.upper().find(key) + len(key)
            extracted_text = txt[start_index:].strip()
            extracted_text = extracted_text.replace("o", "0").replace("O", "0")
            extracted_text = ''.join(c for c in extracted_text if c.isdigit())
            return extracted_text
    return ''

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

def processar_imagem(files, caminho_pasta, pasta_pai, cursor, connection, start_index=0, end_index=None, progress_callback=None, total_files=1):
    cont = 0
    end_index = end_index or len(files)
    for file_index, file in enumerate(files[start_index:end_index], start=start_index):
        caminho_imagem = os.path.join(caminho_pasta, file)
        try:
            img = cv2.imread(caminho_imagem, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError("Error reading image")

            cpf, rg = pad_teste(caminho_imagem, '', '')
            if cpf or rg:
                adicionar_usuario(cursor, cpf, rg, pasta_pai, file, connection)
        
        except Exception as e:
            with open(CONFIG['log_file'], 'a') as f:
                f.write(f"Error processing image {caminho_imagem}: {e}\n")
            continue
        
        print(file)
        del img, cpf, rg, caminho_imagem
        gc.collect()
        
        # Update progress
        cont += 1
        if progress_callback:
            progress_callback(cont / total_files * 100)
    
    log_progress(" ", 0, cont)  # Reset progress to indicate completion
    return True  # Indicate that processing is complete

def contar_arquivos(cursor, connection, diretorio, start_index, end_index, progress_callback):
    CONFIG['diretorio'] = diretorio
    total_files = sum(len(files) for _, _, files in os.walk(CONFIG['diretorio']))
    processed_files = 0

    for root, dirs, files in os.walk(CONFIG['diretorio']):
        pasta_pai = os.path.basename(root)
        if not processar_imagem(files, root, pasta_pai, cursor, connection, start_index, end_index, progress_callback, total_files):
            return  # Stop processing if the batch is incomplete
        processed_files += len(files)
        progress_callback(processed_files / total_files * 100)
        gc.collect()

def main(diretorio, start_index, end_index, progress_callback):
    try:
        with get_db_connection(CONFIG['db_config']) as connection:
            cursor = connection.cursor()
            contar_arquivos(cursor, connection, diretorio, start_index, end_index, progress_callback)
            cursor.close()
    except mysql.connector.Error as err:
        with open(CONFIG['log_file'], 'a') as f:
            f.write(f"Database error: {err}\n")
    except Exception as e:
        with open(CONFIG['log_file'], 'a') as f:
            f.write(f"Unexpected error: {e}\n")

def start_processing(diretorio, start_index, end_index, progress_callback):
    threading.Thread(target=main, args=(diretorio, start_index, end_index, progress_callback)).start()

# Example usage
diretorio = "seu_diretorio"
start_index = 0
end_index = None
progress_callback = lambda progress: print(f"Progresso: {progress:.2f}%")

start_processing(diretorio, start_index, end_index, progress_callback)