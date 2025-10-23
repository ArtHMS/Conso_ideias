import streamlit as st
import pandas as pd
import gspread
import pytz
from google.oauth2.service_account import Credentials
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- CONFIGURAÇÕES GLOBAIS ---
DRIVE_FOLDER_ID = "1JO-kxRNkMdeyBTH4zmO2-tMio6wmbGNY"

# Escopos para AMBAS as APIs (Sheets e Drive)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
# =======================================================

# --- CONFIGURAÇÕES GLOBAIS ---
try:
    fuso_horario_sp = pytz.timezone('America/Sao_Paulo')
except pytz.UnknownTimeZoneError:
    fuso_horario_sp = pytz.utc


# =======================================================
# --- FUNÇÃO DE CONEXÃO ATUALIZADA ---
# =======================================================
@st.cache_resource(ttl=3600)
def connect_to_google_services():
    """Conecta-se ao Google Sheets E ao Google Drive."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Autoriza com AMBOS os escopos (Sheets e Drive)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

        # 1. Conectar ao Sheets
        client_sheets = gspread.authorize(creds)
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1CEu8e_LgTq4NQxm8SWpSsLXYWcGjwJd4YseNUsXm0RQ/edit?usp=sharing"
        worksheet = client_sheets.open_by_url(spreadsheet_url).worksheet("Ideias")

        # 2. Conectar ao Drive
        service_drive = build('drive', 'v3', credentials=creds)

        return worksheet, service_drive
    except Exception as e:
        st.error(f"Falha na conexão com os serviços Google: {e}")
        return None, None


# Inicia a conexão e obtém os dois objetos
worksheet, service_drive = connect_to_google_services()


# =======================================================
# --- NOVA FUNÇÃO PARA UPLOAD NO DRIVE ---
# =======================================================
def upload_to_drive(service, file_obj, folder_id):
    """Faz upload de um objeto de arquivo (do st.file_uploader) para o Google Drive."""
    if not service:
        st.error("Serviço do Google Drive não conectado.")
        return ""

    file_metadata = {
        'name': file_obj.name,
        'parents': [folder_id]
    }
    # Cria um buffer de bytes para o arquivo
    media = MediaIoBaseUpload(io.BytesIO(file_obj.getbuffer()),
                              mimetype=file_obj.type,
                              resumable=True)

    # Cria o arquivo no Drive
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id, webViewLink').execute()

    # Permissão crucial: Torna o arquivo público (qualquer pessoa com o link pode ver)
    service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()

    # Retorna o link de visualização (que será salvo na planilha)
    return file.get('webViewLink')

def get_column_order():
    """Retorna a lista de colunas na ordem exata da planilha."""
    return [
        "ID", "Nome da ideia", "Descrição da solução", "Descrição de problema",
        "Área", "Local", "BL", "Unidade", "Dono da ideia", "Matrícula",
        "Área do operador", "Turno do operador que deu a ideia", "Data ideia",
        "Metodologia", "Líder", "Equipe", "Status", "Observações", "Data conclusão",
        "Investimento", "Ganho financeiro", "Link", "Apresentou em alguma rotina?", "Imagem URL"
    ]

@st.cache_data(ttl=300) # Armazena os dados em cache por 5 minutos
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
    """Salva uma nova ideia na planilha e limpa o cache de dados."""
    if worksheet:
        colunas_ordenadas = get_column_order()
        dados_para_adicionar = [nova_ideia.get(col, "") for col in colunas_ordenadas]
        worksheet.append_row(dados_para_adicionar)
        st.cache_data.clear()

def excluir_ideia(indice_real_df):
    """Exclui uma linha da planilha com base no índice REAL do DataFrame."""
    if worksheet:
        # O índice + 2 corresponde à linha na planilha (cabeçalho + indexação base 1)
        linha_para_excluir = int(indice_real_df) + 2
        worksheet.delete_rows(linha_para_excluir)
        st.cache_data.clear()

def editar_ideia(indice_real_df, dados_editados):
    """Atualiza uma linha existente na planilha."""
    if worksheet:
        linha_para_editar = int(indice_real_df) + 2
        colunas_ordenadas = get_column_order()
        valores_para_atualizar = [dados_editados.get(col, "") for col in colunas_ordenadas]
        # Converte todos os valores para string para evitar erros de serialização JSON
        valores_formatados = [str(valor) for valor in valores_para_atualizar]
        worksheet.update(f'A{linha_para_editar}:W{linha_para_editar}', [valores_formatados])
        st.cache_data.clear()

