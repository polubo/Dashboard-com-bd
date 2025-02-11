import sqlite3
import pymysql  # Para MySQL
import psycopg2  # Para PostgreSQL
import pyodbc  # Para SQL Server
import pandas as pd
import streamlit as st
import plotly.express as px
import os

# Função para conectar a bancos de dados
def connect_db(db_type, db_params):
    if db_type == "SQLite":
        return sqlite3.connect(db_params["db_path"])
    elif db_type == "MySQL":
        return pymysql.connect(
            host=db_params["host"],
            user=db_params["user"],
            password=db_params["password"],
            database=db_params["database"]
        )
    elif db_type == "PostgreSQL":
        return psycopg2.connect(
            host=db_params["host"],
            user=db_params["user"],
            password=db_params["password"],
            dbname=db_params["database"]
        )
    elif db_type == "SQL Server":
        conn_str = (
            f"DRIVER={{{db_params['driver']}}};"
            f"SERVER={db_params['server']};"
            f"DATABASE={db_params['database']};"
            f"UID={db_params['user']};"
            f"PWD={db_params['password']}"
        )
        return pyodbc.connect(conn_str)
    
# Função corrigida para realizar INNER JOIN entre tabelas
def perform_inner_join(connection, tables, join_conditions, select_columns=None):
    if len(tables) < 2 or len(join_conditions) < 1:
        return None

    # Obter os nomes das colunas de cada tabela para evitar duplicação
    table_columns = {}
    for table in tables:
        query = f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'"
        columns = pd.read_sql(query, connection)["COLUMN_NAME"].tolist()
        table_columns[table] = columns

    # Se não forem especificadas colunas, selecionar todas com alias
    if select_columns is None:
        select_columns = []
        for table, columns in table_columns.items():
            for column in columns:
                select_columns.append(f"{table}.{column} AS {table}_{column}")
    else:
        # Caso contrário, incluir apenas as colunas especificadas
        select_columns = [f"{col}" for col in select_columns]

    # Construção da query
    query = f"SELECT {', '.join(select_columns)} FROM {tables[0]}"
    for i in range(1, len(tables)):
        query += f" INNER JOIN {tables[i]} ON {join_conditions[i - 1]}"
    # Exibir a query gerada
    st.write("Query gerada para INNER JOIN:")
    st.code(query)

    return pd.read_sql(query, connection)


# Função para carregar dados de uma tabela com paginação
def load_data_paginated(connection, table_name, page, page_size):
    offset = page * page_size
    if db_type == "SQL Server":
        query = f"SELECT * FROM {table_name} ORDER BY (SELECT NULL) OFFSET {page_size} ROWS FETCH NEXT {page} ROWS ONLY"
    else:
        query = f"SELECT * FROM {table_name} LIMIT {page} OFFSET {page_size}"
    return pd.read_sql(query, connection)

# Função para gerar relatório em Excel
def generate_excel_report(data, filters_applied, file_name="relatorio.xlsx"):
    with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="Dados Filtrados", index=False)
        filters_df = pd.DataFrame(list(filters_applied.items()), columns=["Coluna", "Filtro Aplicado"])
        filters_df.to_excel(writer, sheet_name="Filtros Aplicados", index=False)
    return file_name

# Configuração do Streamlit
st.title("Dashboard Interativo com Banco de Dados")
st.sidebar.header("Configurações")

# Escolher tipo de banco de dados
db_type = st.sidebar.selectbox("Selecione o Tipo de Banco de Dados", ["SQLite", "MySQL", "PostgreSQL", "SQL Server"])

# Configurações para conexão
db_params = {}
skip_validation = False  # Define se a validação deve ser ignorada

if db_type == "SQLite":
    skip_validation = True  # Ignorar validação para bancos locais
    db_directory = "./"  # Diretório padrão
    db_files = [f for f in os.listdir(db_directory) if f.endswith(".db")]
    uploaded_file = st.sidebar.file_uploader("Faça upload do Banco de Dados SQLite (.db)", type=["db"])
    selected_db = st.sidebar.selectbox("Selecione um Banco de Dados Disponível", ["Nenhum"] + db_files)

    if uploaded_file:
        db_params["db_path"] = f"./temp_{uploaded_file.name}"
        with open(db_params["db_path"], "wb") as f:
            f.write(uploaded_file.getbuffer())
    elif selected_db != "Nenhum":
        db_params["db_path"] = os.path.join(db_directory, selected_db)
    else:
        db_params["db_path"] = None

elif db_type in ["MySQL", "PostgreSQL", "SQL Server"]:
    if db_type == "SQL Server":
        db_params["driver"] = st.sidebar.text_input("Driver ODBC", "ODBC Driver 17 for SQL Server")
        db_params["server"] = st.sidebar.text_input("Servidor", "localhost")
    else:
        db_params["host"] = st.sidebar.text_input("Host", "localhost")

    db_params["user"] = st.sidebar.text_input("Usuário", "root")
    db_params["password"] = st.sidebar.text_input("Senha", type="password")
    db_params["database"] = st.sidebar.text_input("Nome do Banco de Dados")

# Conectar ao banco de dados (se necessário)
conn = None
if skip_validation:
    if db_params.get("db_path"):
        conn = connect_db(db_type, db_params)
else:
    if all(db_params.values()):
        try:
            conn = connect_db(db_type, db_params)
        except Exception as e:
            st.error(f"Erro ao conectar ao banco de dados: {e}")

# Processar os dados e exibir no dashboard
if conn:
    try:
        # Listar tabelas disponíveis no banco de dados
        tables_query = {
            "SQLite": "SELECT name FROM sqlite_master WHERE type='table';",
            "MySQL": "SHOW TABLES;",
            "PostgreSQL": "SELECT table_name FROM information_schema.tables WHERE table_schema='public';",
            "SQL Server": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';"
        }[db_type]
        tables = pd.read_sql(tables_query, conn)
        tables_list = tables.iloc[:, 0].tolist()  # Extrair nome das tabelas

        # Selecionar tabela
        selected_table = st.sidebar.selectbox("Selecione a Tabela", tables_list)

        if selected_table:
            page_size = st.sidebar.number_input("Registros por Página", min_value=1, max_value=500, value=50, step=1)
            page = st.sidebar.number_input("Página", min_value=0, value=0, step=1)
            data = load_data_paginated(conn, selected_table, page, page_size)

            st.write(f"### Dados Carregados da Tabela: {selected_table} (Página {page + 1})")
            st.dataframe(data)

            total_rows_query = f"SELECT COUNT(*) FROM {selected_table}"
            total_rows = pd.read_sql(total_rows_query, conn).iloc[0, 0]
            total_pages = (total_rows // page_size) + (1 if total_rows % page_size else 0)

            st.sidebar.write(f"Total de Registros: {total_rows}")
            st.sidebar.write(f"Total de Páginas: {total_pages}")

            # Seleção de tabelas para INNER JOIN
            tables_to_join = st.sidebar.multiselect("Selecione as tabelas para INNER JOIN", tables_list)
            # Inserir condições de junção
            join_conditions = []
            if tables_to_join:
                st.sidebar.write("**Insira as condições de junção entre as tabelas, na ordem:**")
                for i in range(len(tables_to_join) - 1):
                    condition = st.sidebar.text_input(f"Condição para {tables_to_join[i]} e {tables_to_join[i + 1]}", key=f"join_cond_{i}")
                    join_conditions.append(condition)

            # Botão para executar INNER JOIN
            if st.sidebar.button("Executar INNER JOIN") and tables_to_join and all(join_conditions):
                try:
                    joined_data = perform_inner_join(conn, tables_to_join, join_conditions)
                    st.write("### Dados Após INNER JOIN")
                    st.dataframe(joined_data)
                except Exception as e:
                    st.error(f"Erro ao executar INNER JOIN: {e}")        

            # Filtros
            st.sidebar.subheader("Filtros")
            colunas = data.columns.tolist()
            filtros_aplicados = {}

            for coluna in colunas:
                valores_unicos = data[coluna].unique()

                if pd.api.types.is_numeric_dtype(data[coluna]):
                    col_min = float(data[coluna].min())
                    col_max = float(data[coluna].max())

                    with st.sidebar.expander(f"Filtrar {coluna} (Numérico)"):
                        if col_min < col_max:
                            min_val, max_val = st.slider(
                                f"Intervalo para {coluna}", min_value=col_min, max_value=col_max, value=(col_min, col_max)
                            )
                            filtros_aplicados[coluna] = (min_val, max_val)
                        else:
                            st.write(f"Coluna {coluna} tem um único valor ({col_min}). Filtro não necessário.")

                # Filtro por timestamp (permite escrever a data)
                elif pd.api.types.is_datetime64_any_dtype(data[coluna]):
                    min_date = data[coluna].min()
                    max_date = data[coluna].max()

                    with st.sidebar.expander(f"Filtrar {coluna} (Data)"):
                        start_date = st.date_input(
                            f"Data Inicial para {coluna}",
                            min_value=min_date.date(),  # Conversão para data
                            max_value=max_date.date(),  # Conversão para data
                            value=min_date.date()  # Valor padrão
                        )
                        end_date = st.date_input(
                            f"Data Final para {coluna}",
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            value=max_date.date()
                        )
                        filtros_aplicados[coluna] = (pd.to_datetime(start_date), pd.to_datetime(end_date))

            # Aplicar filtros
            data_filtrada = data.copy()
            for coluna, filtro in filtros_aplicados.items():
                if isinstance(filtro, list):
                    data_filtrada = data_filtrada[data_filtrada[coluna].isin(filtro)]
                elif isinstance(filtro, tuple):
                    if isinstance(filtro[0], pd.Timestamp):
                        # Aplicando filtro para intervalo de datas
                        data_filtrada = data_filtrada[(data_filtrada[coluna] >= filtro[0]) & (data_filtrada[coluna] <= filtro[1])]
                    else:
                        # Filtro numérico
                        data_filtrada = data_filtrada[(data_filtrada[coluna] >= filtro[0]) & (data_filtrada[coluna] <= filtro[1])]


            st.write("### Dados Filtrados")
            st.dataframe(data_filtrada)

            # Gráficos
            tipo_grafico = st.sidebar.selectbox("Tipo de Gráfico", ["Barra", "Linha", "Dispersão", "Pizza", "Área"])
            x_axis = st.selectbox("Eixo X", colunas)
            y_axis = st.selectbox("Eixo Y", colunas)

            if tipo_grafico == "Barra":
                fig = px.bar(data_filtrada, x=x_axis, y=y_axis, title="Gráfico de Barras")
            elif tipo_grafico == "Linha":
                fig = px.line(data_filtrada, x=x_axis, y=y_axis, title="Gráfico de Linha")
            elif tipo_grafico == "Dispersão":
                fig = px.scatter(data_filtrada, x=x_axis, y=y_axis, title="Gráfico de Dispersão")
            elif tipo_grafico == "Pizza":
                fig = px.pie(data_filtrada, names=x_axis, values=y_axis, title="Gráfico de Pizza")
            elif tipo_grafico == "Área":
                fig = px.area(data_filtrada, x=x_axis, y=y_axis, title="Gráfico de Área")

            st.plotly_chart(fig)

            # Gerar relatório Excel
            if st.sidebar.button("Gerar Relatório Excel"):
                excel_path = generate_excel_report(data_filtrada, filtros_aplicados)
                with open(excel_path, "rb") as excel_file:
                    st.download_button(
                        label="Baixar Relatório Excel",
                        data=excel_file,
                        file_name="relatorio.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

    finally:
        if conn:
            conn.close()