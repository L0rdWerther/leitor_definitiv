# API for Data Consultation from the Ficha Bank WITH HTML

## How to Run

1. Open the terminal and navigate to the folder containing the script.
2. Run the following command:

python apifichas.py


## Testing with Postman

1. Open Postman.
2. Create a new request.
3. Select the **POST** method.
4. Enter the URL: `http://10.93.48.230:5000/pesquisa`.
5. Go to the **Body** tab, select **raw**, and then choose **JSON** (application/json).
6. Enter the following request body:

```json
{
"user": "root",
"password": "2511",
"nome": "JOÃO",
"cpf": "",
"rg": ""
}

    nome: The name you wish to search for.

    cpf: The CPF you wish to search for (optional).

    rg: The RG you wish to search for (optional).

By sending this request, you can directly access the search page and authenticate automatically, skipping the authentication page.

