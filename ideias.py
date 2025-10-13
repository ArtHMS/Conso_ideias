import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials

# --- Configuração da Página e Fuso Horário (Apenas uma vez) ---
st.set_page_config(page_title="Cadastro de Ideias", page_icon="💡", layout="centered")
fuso_horario_sp = pytz.timezone('America/Sao_Paulo')


# --- CONEXÃO COM GOOGLE SHEETS ---

# Autentica e retorna o cliente gspread. Usa o cache para não reconectar a cada ação.
def connect_to_google_sheets():
    # Converte os secrets para um dicionário Python puro
    creds_dict = dict(st.secrets["gcp_service_account"])
    # Autentica e cria o cliente
    client = gspread.service_account_from_dict(creds_dict)

    # URL da sua planilha
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1Bz5wBtRSSEz9Hj5TiACOw5V_Zztg2CS_BgrdRPpGt9c/edit?usp=sharing"
    spreadsheet = client.open_by_url(spreadsheet_url)

    # Nome da sua aba
    worksheet = spreadsheet.worksheet("Ideias")
    return worksheet


# --- Inicializa a conexão ---
try:
    worksheet = connect_to_google_sheets()
except Exception as e:
    st.error(f"Não foi possível conectar à Planilha Google. Verifique suas credenciais e permissões. Erro: {e}")
    st.stop()  # Interrompe a execução do app se a conexão falhar


# --- FUNÇÕES PARA MANIPULAR DADOS NA PLANILHA ---

def carregar_dados():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=["Nome", "Área", "Título", "Descrição", "Impacto", "Data de Envio"])
    return df


def salvar_ideia(nova_ideia):
    dados_para_adicionar = list(nova_ideia.values())
    worksheet.append_row(dados_para_adicionar)


def excluir_ideia(indice_df):
    linha_para_excluir = int(indice_df) + 2
    worksheet.delete_rows(linha_para_excluir)


def editar_ideia(indice_df, dados_editados):
    linha_para_editar = int(indice_df) + 2
    colunas_ordenadas = ["Nome", "Área", "Título", "Descrição", "Impacto", "Data de Envio"]
    valores_para_atualizar = [dados_editados.get(col) for col in colunas_ordenadas]
    worksheet.update(f'A{linha_para_editar}:F{linha_para_editar}', [valores_para_atualizar])


# --- INTERFACE DO STREAMLIT ---

st.title("💡 Sistema de Ideias dos Operadores")
st.write("Preencha o formulário abaixo para registrar sua ideia!")

with st.form("form_ideia", clear_on_submit=True):
    nome = st.text_input("👤 Nome do operador")
    area = st.text_input("🏭 Área / Setor")
    titulo = st.text_input("🧠 Título da ideia")
    descricao = st.text_area("📝 Descrição detalhada da ideia")
    impacto = st.selectbox("📈 Nível de impacto esperado", ["Baixo", "Médio", "Alto"])
    enviar = st.form_submit_button("🚀 Enviar ideia")
    if enviar:
        if nome and area and titulo and descricao:
            data_envio = datetime.now(fuso_horario_sp).strftime("%d/%m/%Y %H:%M")
            nova_ideia = {"Nome": nome, "Área": area, "Título": titulo, "Descrição": descricao, "Impacto": impacto,
                          "Data de Envio": data_envio}
            salvar_ideia(nova_ideia)
            st.success("✅ Ideia registrada com sucesso na Planilha Google!")
            st.rerun()  # Usamos rerun para recarregar os dados após o envio
        else:
            st.warning("⚠️ Preencha todos os campos obrigatórios antes de enviar.")

st.markdown("---")
st.subheader("📊 Ideias registradas")

df = carregar_dados()

if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.markdown("---")
    st.subheader("✏️ Alterar Ideia")
    indice_editar = st.number_input("Selecione o índice da ideia que deseja editar", min_value=0, max_value=len(df) - 1,
                                    step=1, key="editor_idx")
    ideia_selecionada = df.loc[indice_editar]
    with st.expander("Clique para editar os dados da ideia selecionada"):
        with st.form("form_edicao"):
            nome_edit = st.text_input("Nome", value=ideia_selecionada["Nome"])
            area_edit = st.text_input("Área / Setor", value=ideia_selecionada["Área"])
            titulo_edit = st.text_input("Título", value=ideia_selecionada["Título"])
            descricao_edit = st.text_area("Descrição", value=ideia_selecionada["Descrição"], height=150)
            opcoes_impacto = ["Baixo", "Médio", "Alto"]
            index_impacto = opcoes_impacto.index(ideia_selecionada["Impacto"]) if ideia_selecionada[
                                                                                      "Impacto"] in opcoes_impacto else 0
            impacto_edit = st.selectbox("Impacto", opcoes_impacto, index=index_impacto)
            if st.form_submit_button("💾 Salvar alterações"):
                data_edicao = datetime.now(fuso_horario_sp).strftime("%d/%m/%Y %H:%M")
                dados_editados = {"Nome": nome_edit, "Área": area_edit, "Título": titulo_edit,
                                  "Descrição": descricao_edit, "Impacto": impacto_edit, "Data de Envio": data_edicao}
                editar_ideia(indice_editar, dados_editados)
                st.success("✅ Ideia atualizada com sucesso!")
                st.rerun()
    st.markdown("---")
    st.subheader("🗑️ Excluir uma ideia")
    indice_excluir = st.number_input("Digite o índice da ideia que deseja excluir", min_value=0, max_value=len(df) - 1,
                                     step=1, key="excluir_idx")
    if st.button("❌ Excluir ideia selecionada"):
        excluir_ideia(indice_excluir)
        st.success(f"Ideia no índice {indice_excluir} excluída com sucesso!")
        st.rerun()
else:
    st.info("Nenhuma ideia cadastrada ainda.")

