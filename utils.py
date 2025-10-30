import streamlit as st
import pandas as pd
import gspread
import pytz
from google.oauth2.service_account import Credentials

try:
    fuso_horario_sp = pytz.timezone('America/Sao_Paulo')
except pytz.UnknownTimeZoneError:
    fuso_horario_sp = pytz.utc



# Esta é a função de conexão original, apenas para o Google Sheets
@st.cache_resource(ttl=3600)
def connect_to_google_sheets():
    """Conecta à Planilha Google e retorna o objeto da aba"""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Escopo apenas para o Sheets
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

        client = gspread.authorize(creds)
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1CEu8e_LgTq4NQxm8SWpSsLXYWcGjwJd4YseNUsXm0RQ/edit?usp=sharing"
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet("Ideias")
        return worksheet
    except Exception as e:
        st.error(f"Falha na conexão com a Planilha Google: {str(e)}")
        return None


# Inicia a conexão
worksheet = connect_to_google_sheets()


# Lista de colunas revertida
def get_column_order():
    """Retorna a lista de colunas na ordem exata da planilha."""
    return [
        "ID", "Nome da ideia", "Descrição da solução", "Descrição de problema",
        "Área", "Local", "BL", "Unidade", "Dono da ideia", "Matrícula",
        "Área do operador", "Turno do operador que deu a ideia", "Data ideia",
        "Metodologia", "Líder", "Equipe", "Status", "Observações", "Data conclusão",
        "Investimento", "Ganho financeiro", "Link", "Apresentou em alguma rotina?"
    ]


@st.cache_data(ttl=300)
def carregar_dados():
    """Carrega os dados da planilha e retorna um DataFrame."""
    if worksheet is None:
        return pd.DataFrame(columns=get_column_order())
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=get_column_order())
    if 'ID' in df.columns:
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
    return df


def salvar_ideia(nova_ideia):
    """Salva uma nova ideia na planilha."""
    if worksheet:
        colunas_ordenadas = get_column_order()
        dados_para_adicionar = [nova_ideia.get(col, "") for col in colunas_ordenadas]
        worksheet.append_row(dados_para_adicionar)
        st.cache_data.clear()


def excluir_ideia(indice_real_df):
    """Exclui uma linha da planilha com base no índice REAL do DataFrame."""
    if worksheet:
        linha_para_excluir = int(indice_real_df) + 2
        worksheet.delete_rows(linha_para_excluir)
        st.cache_data.clear()


# Função de edição revertida (atualizando apenas até a coluna W)
def editar_ideia(indice_real_df, dados_editados):
    """Atualiza uma linha existente na planilha."""
    if worksheet:
        linha_para_editar = int(indice_real_df) + 2
        colunas_ordenadas = get_column_order()
        valores_para_atualizar = [dados_editados.get(col, "") for col in colunas_ordenadas]
        valores_formatados = [str(valor) for valor in valores_para_atualizar]
        # Atualiza de A até W (as 23 colunas originais)
        worksheet.update(f'A{linha_para_editar}:W{linha_para_editar}', [valores_formatados])
        st.cache_data.clear()