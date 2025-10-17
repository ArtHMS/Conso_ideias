import streamlit as st
import pandas as pd
from utils import carregar_dados, editar_ideia, excluir_ideia, get_column_order

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="wide", page_title="Painel de Ideias")

st.title("💡 Painel de Consulta de Ideias")
st.write("Use os filtros na barra lateral para encontrar ideias específicas.")

# Carrega todos os dados uma vez
df = carregar_dados()

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("🔍 Filtros do Painel")

# Filtro por Status
if 'Status' in df.columns:
    status_disponiveis = ["Todos"] + df["Status"].unique().tolist()
    status_selecionado = st.sidebar.selectbox("Filtrar por Status", status_disponiveis)
else:
    status_selecionado = "Todos"

# Filtro por Área
if 'Área' in df.columns:
    areas_disponiveis = ["Todos"] + df["Área"].unique().tolist()
    area_selecionada = st.sidebar.selectbox("Filtrar por Área da Ideia", areas_disponiveis)
else:
    area_selecionada = "Todos"

# Botão para limpar o cache na barra lateral
if st.sidebar.button("🔄 Limpar Cache e Recarregar Dados"):
    st.cache_data.clear()
    st.rerun()

# Aplica os filtros ao DataFrame
df_filtrado = df.copy()
if status_selecionado != "Todos" and 'Status' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Status"] == status_selecionado]

if area_selecionada != "Todos" and 'Área' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Área"] == area_selecionada]

# --- PAINEL DE IDEIAS REGISTRADAS ---
st.header("📊 Ideias Registradas")

if not df_filtrado.empty:
    st.dataframe(df_filtrado.reset_index(drop=True), use_container_width=True)
    st.markdown("---")

    # --- GERENCIAMENTO DE IDEIAS ---
    st.header("⚙️ Gerenciar Ideias Existentes")
    col_edit, col_delete = st.columns(2)

    with col_edit:
        st.subheader("✏️ Alterar Ideia")
        lista_ideias_filtrada = [f"{row['ID']} - {row['Nome da ideia']}" for index, row in df_filtrado.iterrows()]

        if lista_ideias_filtrada:
            ideia_selecionada_str = st.selectbox("Selecione a ideia para editar", options=lista_ideias_filtrada,
                                                 key="editor_idx")
            id_selecionado = int(ideia_selecionada_str.split(" - ")[0])

            with st.expander("Clique para carregar e editar os dados"):
                ideia_para_editar_linha = df[df['ID'] == id_selecionado]
                if not ideia_para_editar_linha.empty:
                    indice_real = ideia_para_editar_linha.index[0]
                    ideia_para_editar = ideia_para_editar_linha.iloc[0]

                    with st.form(f"form_edicao_{id_selecionado}"):
                        # Formulário de edição completo...
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
                            # Adicione outros campos de edição aqui...
                        with c2:
                            status_options = ["Nova", "Em análise", "Aprovada", "Em implementação", "Concluída",
                                              "Rejeitada"]
                            status_idx = status_options.index(
                                ideia_para_editar.get("Status", "Nova")) if ideia_para_editar.get(
                                "Status") in status_options else 0
                            dados_editados["Status"] = st.selectbox("Status", status_options, index=status_idx,
                                                                    key=f"edit_status_{id_selecionado}")
                            # Adicione outros campos de edição aqui...

                        if st.form_submit_button("💾 Salvar Alterações"):
                            for col in get_column_order():
                                if col not in dados_editados:
                                    dados_editados[col] = ideia_para_editar.get(col)

                            editar_ideia(indice_real, dados_editados)
                            st.success("✅ Ideia atualizada com sucesso!")
                            st.rerun()

    with col_delete:
        st.subheader("🗑️ Excluir Ideia")
        if 'lista_ideias_filtrada' in locals() and lista_ideias_filtrada:
            ideia_excluir_str = st.selectbox("Selecione a ideia para excluir", options=lista_ideias_filtrada,
                                             key="excluir_idx")
            if st.button("❌ Excluir Ideia Selecionada"):
                id_excluir = int(ideia_excluir_str.split(" - ")[0])
                linha_excluir = df[df['ID'] == id_excluir]
                if not linha_excluir.empty:
                    indice_real_excluir = linha_excluir.index[0]
                    excluir_ideia(indice_real_excluir)
                    st.success(f"Ideia '{ideia_excluir_str.split(' - ')[1]}' excluída com sucesso!")
                    st.rerun()
else:
    st.info("Nenhuma ideia encontrada com os filtros selecionados ou nenhuma ideia foi cadastrada ainda.")


