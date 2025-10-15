import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials

# --- Configuração da Página e Fuso Horário (Apenas uma vez) ---
try:
    fuso_horario_sp = pytz.timezone('America/Sao_Paulo')
except pytz.UnknownTimeZoneError:
    st.error("Fuso horário 'America/Sao_Paulo' não encontrado.")
    st.stop()


# Função para conectar ao Google Sheets
def connect_to_google_sheets():
    """Conecta-se à planilha Google e retorna o objeto da aba (worksheet)."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        client = gspread.service_account_from_dict(creds_dict)
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1CEu_LgTq4NQxm8SWpSsLXYWcGjwJd4YseNUsXm0RQ/edit?usp=sharing"
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet("Ideias")
        return worksheet
    except Exception as e:
        st.error(f"Falha na conexão com a Planilha Google: {e}")
        st.stop()


# Função auxiliar para manter a ordem correta das colunas
def get_column_order():
    """Retorna a lista de colunas na ordem exata da planilha."""
    return [
        "ID", "Nome da ideia", "Descrição da solução", "Descrição de problema",
        "Área", "Local", "BL", "Unidade", "Dono da ideia", "Matrícula",
        "Área do operador", "Turno do operador que deu a ideia", "Data ideia",
        "Metodologia", "Líder", "Equipe", "Status", "Observações", "Data conclusão",
        "Investimento", "Ganho financeiro", "Link", "Apresentou em alguma rotina?"
    ]


# Inicia a conexão com a planilha
worksheet = connect_to_google_sheets()


# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def carregar_dados():
    """Carrega os dados da planilha e retorna um DataFrame."""
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=get_column_order())
    return df


def salvar_ideia(nova_ideia):
    """Salva uma nova ideia na planilha, garantindo a ordem das colunas."""
    colunas_ordenadas = get_column_order()
    dados_para_adicionar = [nova_ideia.get(col, "") for col in colunas_ordenadas]
    worksheet.append_row(dados_para_adicionar)


def excluir_ideia(indice_df):
    """Exclui uma linha da planilha com base no índice do DataFrame."""
    linha_para_excluir = int(indice_df) + 2
    worksheet.delete_rows(linha_para_excluir)


def editar_ideia(indice_df, dados_editados):
    """Atualiza uma linha existente na planilha."""
    linha_para_editar = int(indice_df) + 2
    colunas_ordenadas = get_column_order()
    valores_para_atualizar = [dados_editados.get(col, "") for col in colunas_ordenadas]
    # Atualiza o intervalo correto de colunas (A até W para 23 colunas)
    worksheet.update(f'A{linha_para_editar}:W{linha_para_editar}', [valores_para_atualizar])


# --- INTERFACE STREAMLIT ---

st.set_page_config(layout="wide")
st.title("💡 Sistema de Ideias dos Operadores")
st.write("Preencha o formulário abaixo para registrar todos os detalhes da sua ideia!")

# Formulário completo para registrar uma nova ideia
with st.form("form_ideia", clear_on_submit=True):
    st.subheader("1. Identificação do Colaborador")
    col1, col2 = st.columns(2)
    with col1:
        dono_da_ideia = st.text_input("👤 Dono da ideia *")
        area_operador = st.text_input("🏭 Área do operador *")
    with col2:
        matricula = st.text_input("🔢 Matrícula *")
        turno_operador = st.selectbox("☀️ Turno do operador", ["Manhã", "Tarde", "Noite", "Geral"])

    st.markdown("---")
    st.subheader("2. Detalhes da Ideia")
    col3, col4 = st.columns(2)
    with col3:
        nome_ideia = st.text_input("🧠 Nome da Ideia *")
        descricao_problema = st.text_area("❓ Descrição do Problema *", height=150)
        descricao_solucao = st.text_area("💡 Descrição da Solução Proposta *", height=150)
    with col4:
        area_aplicacao = st.text_input("🏭 Área de Aplicação da Ideia")
        local = st.text_input("📍 Local de Aplicação")
        unidade = st.text_input("🏢 Unidade")
        bl = st.text_input("📦 BL (Business Line)")

    st.markdown("---")
    st.subheader("3. Detalhes de Gestão e Acompanhamento")
    col5, col6 = st.columns(2)
    with col5:
        lider = st.text_input("🧑‍💼 Líder Responsável")
        equipe = st.text_input("🤝 Equipe Envolvida")
        metodologia = st.text_input("🛠️ Metodologia Aplicada")
        status = st.selectbox("📊 Status Inicial",
                              ["Nova", "Em análise", "Aprovada", "Em implementação", "Concluída", "Rejeitada"])
        investimento = st.text_input("💰 Investimento Previsto (R$)")
        ganho_financeiro = st.text_input("💸 Ganho Financeiro Estimado (R$)")
    with col6:
        observacoes = st.text_area("📋 Observações Adicionais", height=150)
        data_conclusao = st.text_input("🗓️ Data de Conclusão (dd/mm/aaaa)")
        link = st.text_input("🔗 Link (documentos, vídeos, etc.)")
        apresentou = st.selectbox("🗣️ Apresentou em alguma rotina?", ["Não", "Sim"])

    enviar = st.form_submit_button("🚀 Enviar Ideia Completa")

if enviar:
    # Verifica se os campos obrigatórios foram preenchidos
    campos_obrigatorios = [dono_da_ideia, matricula, area_operador, nome_ideia, descricao_problema, descricao_solucao]
    if all(campos_obrigatorios):
        df_existente = carregar_dados()
        # Calcula o próximo ID disponível
        novo_id = (pd.to_numeric(df_existente['ID'],
                                 errors='coerce').max() + 1) if not df_existente.empty and 'ID' in df_existente else 1
        data_ideia = datetime.now(fuso_horario_sp).strftime("%d/%m/%Y")

        nova_ideia = {
            "ID": int(novo_id),
            "Nome da Ideia": nome_ideia,
            "Descrição da Solução": descricao_solucao,
            "Descrição de problema": descricao_problema,
            "Área": area_aplicacao,
            "Local": local,
            "BL": bl,
            "Unidade": unidade,
            "Dono da Ideia": dono_da_ideia,
            "Matrícula": matricula,
            "Área do operador": area_operador,
            "Turno do operador que deu a ideia": turno_operador,
            "Data ideia": data_ideia,
            "Metodologia": metodologia,
            "Líder": lider,
            "Equipe": equipe,
            "Status": status,
            "Observações": observacoes,
            "Data Conclusão": data_conclusao,
            "Investimento": investimento,
            "Ganho financeiro": ganho_financeiro,
            "Link": link,
            "Apresentou em alguma rotina?": apresentou
        }
        salvar_ideia(nova_ideia)
        st.success("✅ Ideia registrada com sucesso!")
        st.rerun()
    else:
        st.warning("⚠️ Por favor, preencha todos os campos marcados com *.")

st.markdown("---")
st.subheader("📊 Painel de Ideias Registradas")

df = carregar_dados()

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    # Seção para Editar e Excluir
    st.header("⚙️ Gerenciar Ideias Existentes")
    col_edit, col_delete = st.columns(2)

    with col_edit:
        st.subheader("✏️ Alterar Ideia")
        lista_ideias = [f"{idx} - {row['Nome da Ideia']}" for idx, row in df.iterrows()]
        if lista_ideias:
            ideia_selecionada_str = st.selectbox("Selecione a ideia para editar", options=lista_ideias,
                                                 key="editor_idx")
            indice_editar = int(ideia_selecionada_str.split(" - ")[0])

            if st.button("Carregar dados para edição"):
                st.session_state.ideia_para_editar = df.loc[indice_editar].to_dict()
                st.session_state.indice_editar = indice_editar

    # Formulário de edição aparece apenas quando uma ideia é carregada
    if 'ideia_para_editar' in st.session_state:
        st.subheader(f"Editando Ideia: {st.session_state.ideia_para_editar.get('Nome da Ideia', '')}")
        with st.form("form_edicao"):
            ideia_atual = st.session_state.ideia_para_editar
            dados_editados = {}

            c1, c2 = st.columns(2)
            with c1:
                dados_editados["Nome da ideia"] = st.text_input("Nome da ideia",
                                                                value=ideia_atual.get("Nome da ideia", ""))
                dados_editados["Dono da ideia"] = st.text_input("Dono da ideia",
                                                                value=ideia_atual.get("Dono da ideia", ""))
                dados_editados["Matrícula"] = st.text_input("Matrícula", value=ideia_atual.get("Matrícula", ""))
                dados_editados["Descrição de problema"] = st.text_area("Descrição de problema",
                                                                       value=ideia_atual.get("Descrição de problema",
                                                                                             ""), height=100)
                dados_editados["Descrição da solução"] = st.text_area("Descrição da Solução",
                                                                      value=ideia_atual.get("Descrição da solução", ""),
                                                                      height=100)
                dados_editados["Área"] = st.text_input("Área de Aplicação", value=ideia_atual.get("Área", ""))
                dados_editados["Local"] = st.text_input("Local", value=ideia_atual.get("Local", ""))
                dados_editados["Líder"] = st.text_input("Líder", value=ideia_atual.get("Líder", ""))
                dados_editados["Equipe"] = st.text_input("Equipe", value=ideia_atual.get("Equipe", ""))
                dados_editados["Investimento"] = st.text_input("Investimento (R$)",
                                                               value=ideia_atual.get("Investimento", ""))
                dados_editados["Ganho financeiro"] = st.text_input("Ganho Financeiro (R$)",
                                                                   value=ideia_atual.get("Ganho financeiro", ""))

            with c2:
                status_options = ["Nova", "Em análise", "Aprovada", "Em implementação", "Concluída", "Rejeitada"]
                status_atual_val = ideia_atual.get("Status", "Nova")
                status_idx = status_options.index(status_atual_val) if status_atual_val in status_options else 0
                dados_editados["Status"] = st.selectbox("Status", status_options, index=status_idx, key="edit_status")
                dados_editados["Data Conclusão"] = st.text_input("Data conclusão",
                                                                 value=ideia_atual.get("Data conclusão", ""))
                dados_editados["Observações"] = st.text_area("Observações", value=ideia_atual.get("Observações", ""),
                                                             height=100)
                dados_editados["Metodologia"] = st.text_input("Metodologia", value=ideia_atual.get("Metodologia", ""))
                dados_editados["BL"] = st.text_input("BL", value=ideia_atual.get("BL", ""))
                dados_editados["Unidade"] = st.text_input("Unidade", value=ideia_atual.get("Unidade", ""))
                dados_editados["Link"] = st.text_input("Link", value=ideia_atual.get("Link", ""))

                apresentou_options = ["Sim", "Não"]
                apresentou_atual_val = ideia_atual.get("Apresentou em alguma rotina?", "Não")
                apresentou_idx = apresentou_options.index(
                    apresentou_atual_val) if apresentou_atual_val in apresentou_options else 1
                dados_editados["Apresentou em alguma rotina?"] = st.selectbox("Apresentou em rotina?",
                                                                              apresentou_options, index=apresentou_idx,
                                                                              key="edit_apresentou")
                dados_editados["Área do operador"] = st.text_input("Área do operador",
                                                                   value=ideia_atual.get("Área do operador", ""))
                dados_editados["Turno do operador que deu a ideia"] = st.text_input("Turno do operador",
                                                                                    value=ideia_atual.get(
                                                                                        "Turno do operador que deu a ideia",
                                                                                        ""))

            if st.form_submit_button("💾 Salvar Alterações"):
                dados_editados["ID"] = ideia_atual.get("ID")
                dados_editados["Data ideia"] = ideia_atual.get("Data ideia")
                editar_ideia(st.session_state.indice_editar, dados_editados)
                st.success("✅ Ideia atualizada com sucesso!")
                del st.session_state.ideia_para_editar  # Limpa o estado para fechar o form
                st.rerun()

    with col_delete:
        st.subheader("🗑️ Excluir Ideia")
        if lista_ideias:
            ideia_excluir_str = st.selectbox("Selecione a ideia para excluir", options=lista_ideias, key="excluir_idx")
            if st.button("❌ Excluir Ideia Selecionada"):
                indice_excluir = int(ideia_excluir_str.split(" - ")[0])
                excluir_ideia(indice_excluir)
                st.success(f"Ideia '{ideia_excluir_str.split(' - ')[1]}' excluída com sucesso!")
                st.rerun()
else:
    st.info("Nenhuma ideia cadastrada ainda.")

