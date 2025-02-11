# Dashboard Interativo com Banco de Dados

Este projeto é um **dashboard interativo** desenvolvido com **Streamlit** e **Plotly**, permitindo a conexão com diferentes bancos de dados (**SQLite, MySQL, PostgreSQL e SQL Server**) para exibição e análise de dados.

## 📌 Funcionalidades

- Conexão com bancos de dados SQLite, MySQL, PostgreSQL e SQL Server.
- Exibição paginada de dados das tabelas do banco.
- Aplicação de filtros em colunas numéricas e de data.
- Realização de **INNER JOIN** entre tabelas.
- Geração de gráficos interativos (barras, linhas, dispersão, pizza, área).
- Exportação de relatórios em **Excel** com os dados filtrados.

## 🛠 Tecnologias Utilizadas

- **Linguagem:** Python
- **Frameworks e Bibliotecas:**
  - `streamlit` (para a interface web)
  - `pandas` (manipulação de dados)
  - `plotly.express` (gráficos interativos)
  - `sqlite3`, `pymysql`, `psycopg2`, `pyodbc` (conexões com bancos de dados)
  - `openpyxl` (exportação para Excel)

## 🚀 Como Executar o Projeto

### 1️⃣ Instale as dependências
```bash
pip install streamlit pandas plotly pymysql psycopg2 pyodbc openpyxl
```

### 2️⃣ Execute o Dashboard
```bash
streamlit run app.py
```

## 🎯 Como Utilizar

1. **Selecione o tipo de banco de dados** no menu lateral.
2. **Informe as credenciais** (se necessário) para conexão.
3. **Escolha a tabela** para exibição dos dados.
4. **Aplique filtros** para visualizar apenas os dados desejados.
5. **Gere gráficos** personalizados a partir dos dados filtrados.
6. **Exporte os dados filtrados** para um relatório Excel.
7. **Realize INNER JOINs** entre tabelas para cruzamento de dados.

## 🔍 Observações

- Para bancos **SQLite**, você pode fazer upload de um arquivo `.db` diretamente na interface.
- Para bancos **SQL Server**, é necessário fornecer o driver ODBC corretamente configurado.
- As queries geradas são exibidas para transparência e depuração.
- Projeto ainda não finalizado.

## 📄 Licença

Este projeto está sob a licença **MIT**. Sinta-se à vontade para modificar e utilizar conforme necessário.

---

🎉 **Desenvolvido para facilitar a análise de dados e visualização interativa!**
