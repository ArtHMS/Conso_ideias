import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Nome do arquivo Excel
ARQUIVO_EXCEL = "ideias_Teste.xlsx"

# Colunas padrão
COLUNAS = ["Nome", "Área", "Título", "Descrição", "Impacto", "Data de Envio"]

# Função para salvar os dados no Excel
def salvar_ideia_excel(nova_ideia):
    if os.path.exists(ARQUIVO_EXCEL):
        df_existente = pd.read_excel(ARQUIVO_EXCEL)
        for col in COLUNAS:
            if col not in df_existente.columns:
                df_existente[col] = ""
        df_atualizado = pd.concat([df_existente, pd.DataFrame([nova_ideia])], ignore_index=True)
    else:
        df_atualizado = pd.DataFrame([nova_ideia], columns=COLUNAS)
    df_atualizado.to_excel(ARQUIVO_EXCEL, index=False)

# Função para excluir uma ideia
def excluir_ideia(indice):
    df = pd.read_excel(ARQUIVO_EXCEL)
    df = df.drop(indice).reset_index(drop=True)
    df.to_excel(ARQUIVO_EXCEL, index=False)

def editar_ideia(indice, dados_editados):
    df = pd.read_excel(ARQUIVO_EXCEL)
    for col, valor in dados_editados.items():
        df.at[indice, col] = valor
    df.to_excel(ARQUIVO_EXCEL, index=False)

# --- Configuração da página ---
st.set_page_config(page_title="Cadastro de Ideias", page_icon="💡", layout="centered")

st.title("💡 Sistema de Ideias dos Operadores")
st.write("Preencha o formulário abaixo para registrar sua ideia!")

# --- Formulário ---
with st.form("form_ideia"):
    nome = st.text_input("👤 Nome do operador")
    area = st.text_input("🏭 Área / Setor")
    titulo = st.text_input("🧠 Título da ideia")
    descricao = st.text_area("📝 Descrição detalhada da ideia")
    impacto = st.selectbox("📈 Nível de impacto esperado", ["Baixo", "Médio", "Alto"])
    data_envio = datetime.now().strftime("%d/%m/%Y %H:%M")

    enviar = st.form_submit_button("🚀 Enviar ideia")

    if enviar:
        if nome and area and titulo and descricao:
            nova_ideia = {
                "Nome": nome,
                "Área": area,
                "Título": titulo,
                "Descrição": descricao,
                "Impacto": impacto,
                "Data de Envio": data_envio
            }
            salvar_ideia_excel(nova_ideia)
            st.success("✅ Ideia registrada com sucesso!")
            st.balloons()
        else:
            st.warning("⚠️ Preencha todos os campos obrigatórios antes de enviar.")

# --- Visualização das ideias cadastradas ---
st.markdown("---")
st.subheader("📊 Ideias registradas")

if os.path.exists(ARQUIVO_EXCEL):
    df = pd.read_excel(ARQUIVO_EXCEL)
    st.dataframe(df, use_container_width=True)

    # --- Edição de ideias ---
    st.markdown("---")
    st.subheader("✏️ Alterar Ideia")
    indice_editar = st.number_input(
        "Selecione o índice da ideia que deseja editar",
        min_value=0, max_value=len(df) - 1, step=1
    )

    with st.expander("Clique para editar os dados da ideia selecionada"):
        nome_edit = st.text_input(" Nome", df.loc[indice_editar, "Nome"])
        area_edit = st.text_input(" Área / Setor", df.loc[indice_editar, "Área"])
        titulo_edit = st.text_input(" Título", df.loc[indice_editar, "Título"])
        descricao_edit = st.text_area(" Descrição", df.loc[indice_editar, "Descrição"])
        impacto_edit = st.selectbox(
            "📈 Impacto",
            ["Baixo", "Médio", "Alto"],
            index=["Baixo", "Médio", "Alto"].index(df.loc[indice_editar, "Impacto"])
            if df.loc[indice_editar, "Impacto"] in ["Baixo", "Médio", "Alto"] else 0
        )
        if st.button("💾 Salvar alterações"):
            dados_editados = {
                "Nome": nome_edit,
                "Área": area_edit,
                "Título": titulo_edit,
                "Descrição": descricao_edit,
                "Impacto": impacto_edit,
                "Data de Envio": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            editar_ideia(indice_editar, dados_editados)
            st.success("✅ Ideia atualizada com sucesso!")
            st.experimental_rerun()

    # --- Exclusão de ideias ---
    st.markdown("---")
    st.subheader("🗑️ Excluir uma ideia")
    indice_excluir = st.number_input(
        "Digite o índice da ideia que deseja excluir (começa em 0)",
        min_value=0, max_value=len(df)-1, step=1
    )
    if st.button("❌ Excluir ideia selecionada"):
        excluir_ideia(indice_excluir)
        st.success(f"Ideia no índice {indice_excluir} excluída com sucesso!")
        st.experimental_rerun()  # Recarrega a página para atualizar a tabela
else:
    st.info("Nenhuma ideia cadastrada ainda.")
