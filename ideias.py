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
        "ID", "Nome da ideia", "Descrição da Solução", "Descrição de problema",
        "Área", "Local", "BL", "Unidade", "Dono da Ideia", "Matrícula",
        "Área do operador", "Turno do operador que deu a ideia", "Data ideia",
        "Metodologia", "Líder", "Equipe", "Status", "Observações", "Data Conclusão",
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
        # Se a planilha estiver vazia, cria um DataFrame com a estrutura correta
        df = pd.DataFrame(columns=get_column_order())
    return df


def salvar_ideia(nova_ideia):
    """Salva uma nova ideia na planilha, garantindo a ordem das colunas."""
    colunas_ordenadas = get_column_order()
    # Cria uma lista de valores na ordem correta, usando get() para evitar erros
    dados_para_adicionar = [nova_ideia.get(col, "") for col in colunas_ordenadas]
    worksheet.append_row(dados_para_adicionar)


def excluir_ideia(indice_df):
    """Exclui uma linha da planilha com base no índice do DataFrame."""
    # O índice do DataFrame é 0-based, e a planilha é 1-based, com 1 linha de cabeçalho
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
st.write("Preencha o formulário abaixo para registrar sua ideia!")

# Formulário para registrar uma nova ideia
with st.form("form_ideia", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Informações do Operador")
        dono_da_ideia = st.text_input("👤 Dono da Ideia *")
        matricula = st.text_input("🔢 Matrícula *")
        area_operador = st.text_input("🏭 Área do operador *")
        turno_operador = st.selectbox("☀️ Turno", ["Manhã", "Tarde", "Noite", "Geral"])

    with col2:
        st.subheader("Detalhes da ideia")
        nome_ideia = st.text_input("🧠 Nome da ideia *")
        descricao_problema = st.text_area("❓ Descrição do Problema *")
        descricao_solucao = st.text_area("💡 Descrição da Solução Proposta *")
        area_aplicacao = st.text_input("🏭 Área de aplicação da ideia")
        local = st.text_input("📍 Local de aplicação")

    enviar = st.form_submit_button("🚀 Enviar Ideia")

if enviar:
    # Verifica se os campos obrigatórios foram preenchidos
    if all([dono_da_ideia, matricula, area_operador, nome_ideia, descricao_problema, descricao_solucao]):
        df_existente = carregar_dados()
        # Calcula o próximo ID disponível
        novo_id = (pd.to_numeric(df_existente['ID'],
                                 errors='coerce').max() + 1) if not df_existente.empty and 'ID' in df_existente else 1
        data_ideia = datetime.now(fuso_horario_sp).strftime("%d/%m/%Y")

        nova_ideia = {
            "ID": int(novo_id),
            "Nome da ideia": nome_ideia,
            "Descrição da solução": descricao_solucao,
            "Descrição de problema": descricao_problema,
            "Área": area_aplicacao,
            "Local": local,
            "Dono da ideia": dono_da_ideia,
            "Matrícula": matricula,
            "Área do operador": area_operador,
            "Turno do operador que deu a ideia": turno_operador,
            "Data ideia": data_ideia,
            "Status": "Nova",  # Status padrão para novas ideias
            "Apresentou em alguma rotina?": "Não"
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
    col_edit, col_delete = st.columns(2)

    with col_edit:
        st.subheader("✏️ Alterar Ideia")
        # Seleciona a ideia para editar de uma forma mais amigável
        lista_ideias = [f"{idx} - {row['Nome da ideia']}" for idx, row in df.iterrows()]
        if lista_ideias:
            ideia_selecionada_str = st.selectbox("Selecione a ideia", options=lista_ideias, key="editor_idx")
            indice_editar = int(ideia_selecionada_str.split(" - ")[0])
            ideia_para_editar = df.loc[indice_editar]

            with st.expander("Clique para editar os dados da ideia selecionada", expanded=False):
                with st.form("form_edicao"):
                    dados_editados = {}

                    # Organiza o formulário de edição em colunas
                    c1, c2 = st.columns(2)

                    with c1:
                        st.text_input("ID", value=ideia_para_editar.get("ID", ""), disabled=True)
                        dados_editados["Nome da ideia"] = st.text_input("Nome da ideia",
                                                                        value=ideia_para_editar.get("Nome da ideia",
                                                                                                    ""))
                        dados_editados["Dono da Ideia"] = st.text_input("Dono da Ideia",
                                                                        value=ideia_para_editar.get("Dono da ideia",
                                                                                                    ""))
                        dados_editados["Matrícula"] = st.text_input("Matrícula",
                                                                    value=ideia_para_editar.get("Matrícula", ""))
                        dados_editados["Descrição de problema"] = st.text_area("Descrição de problema",
                                                                               value=ideia_para_editar.get(
                                                                                   "Descrição de problema", ""),
                                                                               height=100)
                        dados_editados["Descrição da solução"] = st.text_area("Descrição da solução",
                                                                              value=ideia_para_editar.get(
                                                                                  "Descrição da solução", ""),
                                                                              height=100)
                        dados_editados["Área"] = st.text_input("Área de Aplicação",
                                                               value=ideia_para_editar.get("Área", ""))
                        dados_editados["Local"] = st.text_input("Local", value=ideia_para_editar.get("Local", ""))
                        dados_editados["Líder"] = st.text_input("Líder", value=ideia_para_editar.get("Líder", ""))
                        dados_editados["Equipe"] = st.text_input("Equipe", value=ideia_para_editar.get("Equipe", ""))
                        dados_editados["Investimento"] = st.text_input("Investimento (R$)",
                                                                       value=ideia_para_editar.get("Investimento", ""))
                        dados_editados["Ganho financeiro"] = st.text_input("Ganho Financeiro (R$)",
                                                                           value=ideia_para_editar.get(
                                                                               "Ganho financeiro", ""))

                    with c2:
                        st.text_input("Data da ideia", value=ideia_para_editar.get("Data ideia", ""), disabled=True)
                        status_options = ["Nova", "Em análise", "Aprovada", "Em implementação", "Concluída",
                                          "Rejeitada"]
                        status_atual = ideia_para_editar.get("Status", "Nova")
                        status_idx = status_options.index(status_atual) if status_atual in status_options else 0
                        dados_editados["Status"] = st.selectbox("Status", status_options, index=status_idx)
                        dados_editados["Data Conclusão"] = st.text_input("Data conclusão",
                                                                         value=ideia_para_editar.get("Data conclusão",
                                                                                                     ""))
                        dados_editados["Observações"] = st.text_area("Observações",
                                                                     value=ideia_para_editar.get("Observações", ""),
                                                                     height=100)
                        dados_editados["Metodologia"] = st.text_input("Metodologia",
                                                                      value=ideia_para_editar.get("Metodologia", ""))
                        dados_editados["BL"] = st.text_input("BL", value=ideia_para_editar.get("BL", ""))
                        dados_editados["Unidade"] = st.text_input("Unidade", value=ideia_para_editar.get("Unidade", ""))
                        dados_editados["Link"] = st.text_input("Link", value=ideia_para_editar.get("Link", ""))

                        apresentou_options = ["Sim", "Não"]
                        apresentou_atual = ideia_para_editar.get("Apresentou em alguma rotina?", "Não")
                        apresentou_idx = apresentou_options.index(
                            apresentou_atual) if apresentou_atual in apresentou_options else 1
                        dados_editados["Apresentou em alguma rotina?"] = st.selectbox("Apresentou em rotina?",
                                                                                      apresentou_options,
                                                                                      index=apresentou_idx)

                        # Campos do operador (não editáveis aqui ou editáveis?)
                        dados_editados["Área do operador"] = st.text_input("Área do operador",
                                                                           value=ideia_para_editar.get(
                                                                               "Área do operador", ""))
                        turno_options = ["Manhã", "Tarde", "Noite", "Geral"]
                        turno_atual = ideia_para_editar.get("Turno do operador que deu a ideia", "Manhã")
                        turno_idx = turno_options.index(turno_atual) if turno_atual in turno_options else 0
                        dados_editados["Turno do operador que deu a ideia"] = st.selectbox("Turno do operador",
                                                                                           turno_options,
                                                                                           index=turno_idx)

                    if st.form_submit_button("💾 Salvar Alterações"):
                        # Mantém os valores não editáveis
                        dados_editados["ID"] = ideia_para_editar.get("ID")
                        dados_editados["Data ideia"] = ideia_para_editar.get("Data ideia")

                        editar_ideia(indice_editar, dados_editados)
                        st.success("✅ Ideia atualizada com sucesso!")
                        st.rerun()

    with col_delete:
        st.subheader("🗑️ Excluir Ideia")
        if lista_ideias:
            ideia_excluir_str = st.selectbox("Selecione a ideia", options=lista_ideias, key="excluir_idx")
            indice_excluir = int(ideia_excluir_str.split(" - ")[0])

            if st.button("❌ Excluir Ideia Selecionada"):
                excluir_ideia(indice_excluir)
                st.success(f"Ideia '{ideia_excluir_str.split(' - ')[1]}' excluída com sucesso!")
                st.rerun()

else:
    st.info("Nenhuma ideia cadastrada ainda.")

