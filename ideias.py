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
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/1CEu8e_LgTq4NQxm8SWpSsLXYWcGjwJd4YseNUsXm0RQ/edit?usp=sharing"
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

    # --- CORREÇÃO APLICADA AQUI ---
    # Converte todos os valores para string antes de enviar para a API do Google.
    # Isso evita o erro 'not JSON serializable' causado por tipos de dados do NumPy/Pandas.
    valores_formatados = [str(valor) for valor in valores_para_atualizar]

    # Atualiza o intervalo correto de colunas (A até W para 23 colunas)
    worksheet.update(f'A{linha_para_editar}:W{linha_para_editar}', [valores_formatados])
    st.cache_data.clear()


# --- INTERFACE STREAMLIT ---

st.set_page_config(layout="wide")
st.title("💡 Sistema de Ideias dos Operadores")
st.title("💡 Sistema de Ideias dos Operadores")

# --- INÍCIO DA SEÇÃO DE ALTERAÇÕES: FILTROS ---

# Carrega todos os dados uma vez
df = carregar_dados()

# Cria a barra lateral para os filtros
st.sidebar.header("🔍 Filtros do Painel")

# Filtro por Status
status_disponiveis = ["Todos"] + df["Status"].unique().tolist()
status_selecionado = st.sidebar.selectbox("Filtrar por Status", status_disponiveis)

# Filtro por Área
areas_disponiveis = ["Todas"] + df["Área"].unique().tolist()
area_selecionada = st.sidebar.selectbox("Filtrar por Área da Ideia", areas_disponiveis)

# Aplica os filtros ao DataFrame
df_filtrado = df.copy()
if status_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Status"] == status_selecionado]

if area_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Área"] == area_selecionada]

# --- FIM DA SEÇÃO DE ALTERAÇÕES: FILTROS ---


# Formulário de cadastro dentro de um expander para economizar espaço
with st.expander("📝 Clique aqui para registrar uma nova ideia"):
    with st.form("form_ideia", clear_on_submit=True):
        st.subheader("1. Identificação do Colaborador")
        col1, col2 = st.columns(2)
        with col1:
            dono_da_ideia = st.text_input("👤 Dono da ideia *")
            area_do_operador = st.text_input("🏭 Área do operador *")
        with col2:
            matricula = st.text_input("🔢 Matrícula *")
            turno_do_operador = st.selectbox("☀️ Turno do operador que deu a ideia", ["Manhã", "Tarde", "Noite", "Geral"])

        st.markdown("---")
        st.subheader("2. Detalhes da Ideia")
        col3, col4 = st.columns(2)
        with col3:
            nome_da_ideia = st.text_input("🧠 Nome da ideia *")
            descricao_de_problema = st.text_area("❓ Descrição de problema *", height=150)
            descricao_da_solucao = st.text_area("💡 Descrição da solução *", height=150)
        with col4:
            area = st.text_input("🏭 Área (da ideia)")
            local = st.text_input("📍 Local")
            unidade = st.text_input("🏢 Unidade")
            bl = st.text_input("📦 BL")

        st.markdown("---")
        st.subheader("3. Detalhes de Gestão e Acompanhamento")
        col5, col6 = st.columns(2)
        with col5:
            lider = st.text_input("🧑‍💼 Líder")
            equipe = st.text_input("🤝 Equipe")
            metodologia = st.text_input("🛠️ Metodologia")
            status = st.selectbox("📊 Status",
                                  ["Nova", "Em análise", "Aprovada", "Em implementação", "Concluída", "Rejeitada"])
            investimento = st.text_input("💰 Investimento (R$)")
            ganho_financeiro = st.text_input("💸 Ganho financeiro (R$)")
        with col6:
            observacoes = st.text_area("📋 Observações", height=150)
            data_conclusao = st.text_input("🗓️ Data conclusão (dd/mm/aaaa)")
            link = st.text_input("🔗 Link")
            apresentou_em_rotina = st.selectbox("🗣️ Apresentou em alguma rotina?", ["Não", "Sim"])

        enviar = st.form_submit_button("🚀 Enviar Ideia Completa")

    if enviar:
        campos_obrigatorios = [dono_da_ideia, matricula, area_do_operador, nome_da_ideia, descricao_de_problema,
                               descricao_da_solucao]
        if all(campos_obrigatorios):
            df_existente = carregar_dados()
            novo_id = (pd.to_numeric(df_existente['ID'],
                                     errors='coerce').max() + 1) if not df_existente.empty and 'ID' in df_existente else 1
            data_ideia = datetime.now(fuso_horario_sp).strftime("%d/%m/%Y")

            nova_ideia = {
                "ID": int(novo_id), "Nome da ideia": nome_da_ideia, "Descrição da solução": descricao_da_solucao,
                "Descrição de problema": descricao_de_problema, "Área": area, "Local": local, "BL": bl,
                "Unidade": unidade, "Dono da ideia": dono_da_ideia, "Matrícula": matricula,
                "Área do operador": area_do_operador, "Turno do operador que deu a ideia": turno_do_operador,
                "Data ideia": data_ideia, "Metodologia": metodologia, "Líder": lider, "Equipe": equipe,
                "Status": status, "Observações": observacoes, "Data conclusão": data_conclusao,
                "Investimento": investimento, "Ganho financeiro": ganho_financeiro, "Link": link,
                "Apresentou em alguma rotina?": apresentou_em_rotina
            }
            salvar_ideia(nova_ideia)
            st.success("✅ Ideia registrada com sucesso!")
            st.rerun()
        else:
            st.warning("⚠️ Por favor, preencha todos os campos marcados com *.")

st.markdown("---")
st.subheader("📊 Painel de Ideias Registradas")

# --- ALTERAÇÃO AQUI: Usa o DataFrame filtrado para exibição ---
if not df_filtrado.empty:
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    st.markdown("---")

    st.header("⚙️ Gerenciar Ideias Existentes")
    col_edit, col_delete = st.columns(2)

    with col_edit:
        st.subheader("✏️ Alterar Ideia")
        # O seletor de edição/exclusão continua mostrando TODAS as ideias
        lista_ideias = [f"{idx} - {row['Nome da ideia']}" for idx, row in df.iterrows()]
        if lista_ideias:
            ideia_selecionada_str = st.selectbox("Selecione a ideia para editar", options=lista_ideias,
                                                 key="editor_idx")
            indice_editar = int(ideia_selecionada_str.split(" - ")[0])

            with st.expander("Clique para carregar e editar os dados", expanded=False):
                ideia_para_editar = df.loc[indice_editar]
                with st.form("form_edicao"):
                    dados_editados = {}
                    c1, c2 = st.columns(2)
                    with c1:
                        dados_editados["Nome da ideia"] = st.text_input("Nome da ideia",
                                                                        value=ideia_para_editar.get("Nome da ideia", ""),
                                                                        key="edit_nome")
                        # ... (restante do formulário de edição)
                        dados_editados["Dono da ideia"] = st.text_input("Dono da ideia",
                                                                        value=ideia_para_editar.get("Dono da ideia", ""),
                                                                        key="edit_dono")
                        dados_editados["Matrícula"] = st.text_input("Matrícula",
                                                                    value=ideia_para_editar.get("Matrícula", ""),
                                                                    key="edit_mat")
                        dados_editados["Descrição de problema"] = st.text_area("Descrição de problema",
                                                                               value=ideia_para_editar.get(
                                                                                   "Descrição de problema", ""),
                                                                               height=100, key="edit_prob")
                        dados_editados["Descrição da solução"] = st.text_area("Descrição da solução",
                                                                              value=ideia_para_editar.get(
                                                                                  "Descrição da solução", ""),
                                                                              height=100, key="edit_sol")
                        dados_editados["Área"] = st.text_input("Área (da ideia)",
                                                               value=ideia_para_editar.get("Área", ""), key="edit_area")
                        dados_editados["Local"] = st.text_input("Local", value=ideia_para_editar.get("Local", ""),
                                                                key="edit_local")
                        dados_editados["Líder"] = st.text_input("Líder", value=ideia_para_editar.get("Líder", ""),
                                                                key="edit_lider")
                    with c2:
                        status_options = ["Nova", "Em análise", "Aprovada", "Em implementação", "Concluída",
                                          "Rejeitada"]
                        status_idx = status_options.index(
                            ideia_para_editar.get("Status", "Nova")) if ideia_para_editar.get(
                            "Status") in status_options else 0
                        dados_editados["Status"] = st.selectbox("Status", status_options, index=status_idx,
                                                                key="edit_status")
                        dados_editados["Investimento"] = st.text_input("Investimento (R$)",
                                                                       value=ideia_para_editar.get("Investimento", ""),
                                                                       key="edit_inv")
                        dados_editados["Ganho financeiro"] = st.text_input("Ganho financeiro (R$)",
                                                                           value=ideia_para_editar.get(
                                                                               "Ganho financeiro", ""),
                                                                           key="edit_ganho")
                        dados_editados["Data conclusão"] = st.text_input("Data conclusão",
                                                                         value=ideia_para_editar.get("Data conclusão", ""),
                                                                         key="edit_data_conc")
                        dados_editados["Link"] = st.text_input("Link", value=ideia_para_editar.get("Link", ""),
                                                               key="edit_link")

                    if st.form_submit_button("💾 Salvar Alterações"):
                        for col in get_column_order():
                            if col not in dados_editados:
                                dados_editados[col] = ideia_para_editar.get(col)
                        editar_ideia(indice_editar, dados_editados)
                        st.success("✅ Ideia atualizada com sucesso!")
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
    # --- ALTERAÇÃO AQUI: Mensagem caso o filtro não retorne resultados ---
    st.info("Nenhuma ideia encontrada com os filtros selecionados ou nenhuma ideia foi cadastrada ainda.")

