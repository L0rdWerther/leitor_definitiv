📄 Leitor de Documentos com OCR e Registro em Banco de Dados

Este projeto é uma aplicação Python que utiliza OCR (Reconhecimento Óptico de Caracteres) para extrair informações de documentos digitalizados (como nome, CPF, RG e data de nascimento) e registrá-las automaticamente em um banco de dados MySQL. Projeto realizado durante estágio na seção de perícia documentoscópica na Polícia Civil do DF. Ele utiliza bibliotecas como pytesseract, PaddleOCR e OpenCV, com interface gráfica em Tkinter.
⚙️ Funcionalidades

    Extração de texto de imagens com Tesseract OCR e PaddleOCR

    Correção de inclinação de imagens para melhorar a leitura

    Identificação e salvamento de assinaturas manuscritas

    Cadastro automático no banco de dados MySQL

    Organização dos arquivos processados em diretórios por status (imagens, erros, assinaturas)

    Interface gráfica com Tkinter

    Log de progresso e alterações

🧰 Tecnologias utilizadas

    Python 3.x

    Tesseract OCR

    PaddleOCR

    OpenCV

    Pillow (PIL)

    MySQL Connector

    Tkinter

🗂️ Estrutura esperada

seu_projeto/
│
├── CAMINHOS/
│   ├── caminhos.txt         # Caminhos de execução e configuração
│   ├── progress.txt         # Log de progresso
│   └── mudancas.txt         # Log de alterações
├── arquivos/
│   ├── imagens/
│   ├── erros/
│   └── assinaturas/
├── leitor.py                # Arquivo principal (o código fornecido)

📝 Formato do arquivo caminhos.txt

Este arquivo deve conter 5 linhas com as seguintes informações:

    Caminho do executável do Tesseract OCR (por exemplo: C:/Program Files/Tesseract-OCR/tesseract.exe)

    Nome da pasta de entrada das imagens

    Nome do banco de dados MySQL

    Host do banco de dados (ex: localhost)

    Caminho da pasta de saída para arquivos processados

🚀 Como executar

    Clone o repositório

git clone https://github.com/seu-usuario/leitor-ocr.git
cd leitor-ocr

Crie um ambiente virtual e instale as dependências

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

Configure o Tesseract OCR e PaddleOCR

    Baixe o Tesseract OCR e instale.

    Configure o caminho do executável no caminhos.txt.

    Baixe os modelos do PaddleOCR e coloque-os no diretório indicado em os.environ['PADDLEOCR'].

Execute a aplicação

    python leitor.py

📌 Observações

    As imagens devem estar em uma pasta com nome que representa o número da "caixa" a ser registrada.

    O programa reconhece nomes sociais quando presentes.

    Erros de leitura são registrados e armazenados separadamente para revisão manual.

    Assinaturas são extraídas da metade inferior da imagem.

🧠 Sugestões futuras

    Implementar uma interface para correção manual dos dados extraídos

    Utilizar reconhecimento facial para validação extra

    Suporte para múltiplos idiomas além de por e eng

🛠️ Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e enviar pull requests.
📄 Licença

Este projeto está licenciado sob a MIT License.
