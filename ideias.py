import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials

# Oculta o rodapé de menu
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# --- Configuração da Página e Fuso Horário (Apenas uma vez) ---
try:
    fuso_horario_sp = pytz.timezone('America/Sao_Paulo')
except pytz.UnknownTimeZoneError:
    st.error("Fuso horário 'America/Sao_Paulo' não encontrado.")
    st.stop()


# Função para conectar ao Google Sheets
@st.cache_resource
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
@st.cache_data(ttl=60)
def carregar_dados():
    """Carrega os dados da planilha e retorna um DataFrame."""
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=get_column_order())
    # Garante que a coluna ID seja numérica para a busca funcionar corretamente
    if 'ID' in df.columns:
        df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
    return df


def salvar_ideia(nova_ideia):
    """Salva uma nova ideia na planilha, garantindo a ordem das colunas."""
    colunas_ordenadas = get_column_order()
    dados_para_adicionar = [nova_ideia.get(col, "") for col in colunas_ordenadas]
    worksheet.append_row(dados_para_adicionar)
    st.cache_data.clear()


def excluir_ideia(indice_real_df):
    """Exclui uma linha da planilha com base no índice REAL do DataFrame."""
    linha_para_excluir = int(indice_real_df) + 2
    worksheet.delete_rows(linha_para_excluir)
    st.cache_data.clear()


def editar_ideia(indice_real_df, dados_editados):
    """Atualiza uma linha existente na planilha."""
    linha_para_editar = int(indice_real_df) + 2
    colunas_ordenadas = get_column_order()
    valores_para_atualizar = [dados_editados.get(col, "") for col in colunas_ordenadas]
    valores_formatados = [str(valor) for valor in valores_para_atualizar]
    worksheet.update(f'A{linha_para_editar}:W{linha_para_editar}', [valores_formatados])
    st.cache_data.clear()


# --- INTERFACE STREAMLIT ---

st.set_page_config(layout="wide")
st.title(" Sistema de Ideias dos Operadores")

# Carrega todos os dados uma vez
df = carregar_dados()

# Cria a barra lateral para os filtros
st.sidebar.header(" Filtros do Painel")

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

# Formulário de cadastro dentro de um expander para economizar espaço
with st.expander(" Clique aqui para registrar uma nova ideia"):
    with st.form("form_ideia", clear_on_submit=True):
        # ... (código do formulário de cadastro, sem alterações) ...
        st.subheader("1. Identificação do Colaborador")
        col1, col2 = st.columns(2)
        with col1:
            dono_da_ideia = st.text_input("👤 Dono da ideia *")
            area_do_operador = st.selectbox("🏭 Área do operador *",
                                            ["Alcoolização", "Almoxerifado", "Área Ácida", "Àrea Àcida",
                                             "Excelência Operacional", "Fábrica de Barricas", "Laboratório",
                                             "Manutenção", "Nitrocelulose", "PCP", "Planta de Soluções",
                                             "Preparação", "Processos", "Produção", "Qualidade", "Segurança"])
        with col2:
            matricula = st.text_input("🔢 Matrícula *")
            turno_do_operador = st.selectbox("☀️ Turno do operador que deu a ideia",
                                             ["1", "2", "3", "A", "ADM", "B", "Escala", "Turno A"])
        st.markdown("---")
        st.subheader("2. Detalhes da Ideia")
        # ... (restante do formulário)
        col3, col4 = st.columns(2)
        with col3:
            nome_da_ideia = st.text_input("🧠 Nome da ideia *")
            descricao_de_problema = st.text_area("❓ Descrição de problema *", height=150)
            descricao_da_solucao = st.text_area("💡 Descrição da solução *", height=150)
        with col4:
            area = st.selectbox("🏭 Área (da ideia)",
                                ["Adm", "Alcoolização", "Almoxerifado", "Àrea Externa",
                                 "Caldeira", "Cobre", "Digestão", "Estabilização",
                                 "Estocagem", "Extração Química", "Fábrica de Barricas",
                                 "Flocadora", "Homogeinização", "Laboratório", "Lixiviação",
                                 "Manutenção", "Nitração", "Nitrocelulose", "Planta de Soluções",
                                 "Portaria - EQ", "Produção", "Qualidade", "Recuperação de fibras",
                                 "Refino", "Rotulagem", "Segurança", "Torres de Resfriamento", "Torres de Vidro",
                                 "USE", "Zinco"])
            local = st.selectbox("📍 Local",
                                 ["Alccolização", "Área Ácida", "Envase Cobre FI", "Extração Química",
                                  "Fábrica de Barricas", "Lixiviação", "Manutenção", "Nitrocelulose",
                                  "Planta de Soluções", "Portaria - EQ", "Preparação", "Sulfato de Cobre Cristalização",
                                  "Sulfato de Cobre Reação", "Sulfato de Cobre Secagem", "Sulfato de Zinco Evaporador",
                                  "Sulfato de Zinco Reação", "Sulfato de Zinco Tratamento"])
            unidade = st.selectbox("🏢 Unidade",
                                   ["CL", "SMP"])
            bl = st.selectbox("📦 BL",
                               ["EQ"])

        st.markdown("---")
        st.subheader("3. Detalhes de Gestão e Acompanhamento")
        col5, col6 = st.columns(2)
        with col5:
            lider = st.text_input("🧑‍💼 Líder")
            equipe = st.text_input("🤝 Equipe")
            metodologia = st.selectbox("🛠️ Metodologia",
                                       ["Green Belt", "Kaizen", "PDCA", "Yellow Belt"])
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
st.subheader(" Painel de Ideias Registradas")

if not df_filtrado.empty:
    st.dataframe(df_filtrado.reset_index(drop=True), use_container_width=True)  # Reset index para visualização
    st.markdown("---")

    st.header(" Gerenciar Ideias Existentes")
    col_edit, col_delete = st.columns(2)

    with col_edit:
        st.subheader(" Alterar Ideia")

        # --- ALTERAÇÃO AQUI: Popula a lista com ID - Nome da ideia ---
        lista_ideias_filtrada = [f"{row['ID']} - {row['Nome da ideia']}" for index, row in df_filtrado.iterrows()]

        if lista_ideias_filtrada:
            ideia_selecionada_str = st.selectbox("Selecione a ideia para editar", options=lista_ideias_filtrada,
                                                 key="editor_idx")

            # --- ALTERAÇÃO AQUI: Extrai o ID da string selecionada ---
            id_selecionado = int(ideia_selecionada_str.split(" - ")[0])

            with st.expander("Clique para carregar e editar os dados", expanded=False):
                # --- ALTERAÇÃO AQUI: Busca a ideia na tabela original (df) pelo ID e pega seu índice real ---
                ideia_para_editar_linha = df[df['ID'] == id_selecionado]
                if not ideia_para_editar_linha.empty:
                    indice_real = ideia_para_editar_linha.index[0]
                    ideia_para_editar = ideia_para_editar_linha.iloc[0]

                    with st.form("form_edicao"):
                        dados_editados = {}
                        c1, c2 = st.columns(2)
                        with c1:
                            dados_editados["Nome da ideia"] = st.text_input("Nome da ideia",
                                                                            value=ideia_para_editar.get("Nome da ideia",
                                                                                                        ""),
                                                                            key=f"edit_nome_{id_selecionado}")
                            dados_editados["Dono da ideia"] = st.text_input("Dono da ideia",
                                                                            value=ideia_para_editar.get("Dono da ideia",
                                                                                                        ""),
                                                                            key=f"edit_dono_{id_selecionado}")
                            # ... (restante dos campos de edição)
                            dados_editados["Matrícula"] = st.text_input("Matrícula",
                                                                        value=ideia_para_editar.get("Matrícula", ""),
                                                                        key=f"edit_mat_{id_selecionado}")
                            dados_editados["Descrição de problema"] = st.text_area("Descrição de problema",
                                                                                   value=ideia_para_editar.get(
                                                                                       "Descrição de problema", ""),
                                                                                   height=100,
                                                                                   key=f"edit_prob_{id_selecionado}")
                            dados_editados["Descrição da solução"] = st.text_area("Descrição da solução",
                                                                                  value=ideia_para_editar.get(
                                                                                      "Descrição da solução", ""),
                                                                                  height=100,
                                                                                  key=f"edit_sol_{id_selecionado}")
                            dados_editados["Área"] = st.text_input("Área (da ideia)",
                                                                   value=ideia_para_editar.get("Área", ""),
                                                                   key=f"edit_area_{id_selecionado}")
                            dados_editados["Local"] = st.text_input("Local", value=ideia_para_editar.get("Local", ""),
                                                                    key=f"edit_local_{id_selecionado}")
                            dados_editados["Líder"] = st.text_input("Líder", value=ideia_para_editar.get("Líder", ""),
                                                                    key=f"edit_lider_{id_selecionado}")
                        with c2:
                            status_options = ["Nova", "Em análise", "Aprovada", "Em implementação", "Concluída",
                                              "Rejeitada"]
                            status_idx = status_options.index(
                                ideia_para_editar.get("Status", "Nova")) if ideia_para_editar.get(
                                "Status") in status_options else 0
                            dados_editados["Status"] = st.selectbox("Status", status_options, index=status_idx,
                                                                    key=f"edit_status_{id_selecionado}")
                            # ... (restante dos campos de edição)
                            dados_editados["Investimento"] = st.text_input("Investimento (R$)",
                                                                           value=ideia_para_editar.get("Investimento",
                                                                                                       ""),
                                                                           key=f"edit_inv_{id_selecionado}")
                            dados_editados["Ganho financeiro"] = st.text_input("Ganho financeiro (R$)",
                                                                               value=ideia_para_editar.get(
                                                                                   "Ganho financeiro", ""),
                                                                               key=f"edit_ganho_{id_selecionado}")
                            dados_editados["Data conclusão"] = st.text_input("Data conclusão",
                                                                             value=ideia_para_editar.get(
                                                                                 "Data conclusão", ""),
                                                                             key=f"edit_data_conc_{id_selecionado}")
                            dados_editados["Link"] = st.text_input("Link", value=ideia_para_editar.get("Link", ""),
                                                                   key=f"edit_link_{id_selecionado}")

                        if st.form_submit_button("💾 Salvar Alterações"):
                            for col in get_column_order():
                                if col not in dados_editados:
                                    dados_editados[col] = ideia_para_editar.get(col)

                            # --- ALTERAÇÃO AQUI: Passa o índice REAL para a função de edição ---
                            editar_ideia(indice_real, dados_editados)
                            st.success("✅ Ideia atualizada com sucesso!")
                            st.rerun()

    with col_delete:
        st.subheader(" Excluir Ideia")
        if 'lista_ideias_filtrada' in locals() and lista_ideias_filtrada:
            ideia_excluir_str = st.selectbox("Selecione a ideia para excluir", options=lista_ideias_filtrada,
                                             key="excluir_idx")
            if st.button("❌ Excluir Ideia Selecionada"):
                # --- ALTERAÇÃO AQUI: Mesma lógica de busca pelo ID para exclusão ---
                id_excluir = int(ideia_excluir_str.split(" - ")[0])
                linha_excluir = df[df['ID'] == id_excluir]
                if not linha_excluir.empty:
                    indice_real_excluir = linha_excluir.index[0]
                    excluir_ideia(indice_real_excluir)
                    st.success(f"Ideia '{ideia_excluir_str.split(' - ')[1]}' excluída com sucesso!")
                    st.rerun()
else:
    st.info("Nenhuma ideia encontrada com os filtros selecionados ou nenhuma ideia foi cadastrada ainda.")

