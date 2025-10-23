import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
from utils import (
    carregar_dados,
    salvar_ideia,
    fuso_horario_sp,
    upload_to_drive,
    DRIVE_FOLDER_ID,
    service_drive
)

# --- CONFIGURAÇÃO DA PÁGINA ---
# CORREÇÃO 1: 'st.set_page_config' DEVE ser o primeiro comando Streamlit
st.set_page_config(layout="centered", page_title="Cadastro de Ideias")

# CORREÇÃO 2: Removido o uploader e título duplicado que estavam aqui

# --- Estilos ---
hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Título Principal ---
st.title("📝 Formulário de Registro de Ideias")
st.write("Preencha todos os campos abaixo para registrar sua ideia no sistema.")
st.markdown("---")

# --- FORMULÁRIO DE CADASTRO ---
with st.form("form_ideia", clear_on_submit=True):
    st.subheader("1. Identificação do Colaborador")
    col1, col2 = st.columns(2)
    with col1:
        dono_da_ideia = st.text_input("👤 Seu Nome Completo *")
        area_do_operador = st.selectbox("🏭 Sua Área / Setor *",
                                        ["Adm", "Alcoolização", "Almoxerifado", "Área Externa",
                                         "Caldeira", "Cobre", "Digestão", "Estabilização", "Estocagem",
                                         "Extração Química", "Fábrica de Barricas", "Flocadora", "Homogeneização",
                                         "Laboratório", "Lixiviação", "Manutenção", "Nitração", "Nitrocelulose",
                                         "Planta de Soluções", "Portaria - EQ", "Produção", "Qualidade",
                                         "Recuperação de fibras",
                                         "Refino", "Rotulagem", "Segurança", "Torres de Resfriamento",
                                         "Torres de Vidro", "USE", "Zinco"])
    with col2:
        matricula = st.text_input("🔢 Sua Matrícula *")
        turno_do_operador = st.selectbox("☀️ Seu Turno", ["1", "2", "3", "A", "ADM", "B", "Escala", "Turno A"])

    st.markdown("---")
    st.subheader("2. Detalhes da Ideia")
    nome_da_ideia = st.text_input("🧠 Dê um nome para a sua Ideia *")
    descricao_de_problema = st.text_area("❓ Qual problema ou oportunidade você identificou? *", height=150)
    descricao_da_solucao = st.text_area("💡 Descreva sua solução ou melhoria *", height=150)

    st.markdown("---")
    st.subheader("3. Informações Adicionais (Opcional)")
    area_aplicacao = st.text_input("🏭 Em qual área ou setor a ideia seria aplicada?")
    local_aplicacao = st.text_input("📍 Em qual local/equipamento específico?")

    # CORREÇÃO 3: Uploader de imagem MOVIDO PARA DENTRO do formulário
    st.markdown("---")
    st.subheader("4. Anexo (Opcional)")
    # Renomeei a variável para 'imagem_para_enviar' para ficar claro
    imagem_para_enviar = st.file_uploader("Escolha uma imagem (JPG, PNG)", type=["jpg", "jpeg", "png"])

    enviar = st.form_submit_button("🚀 Enviar Minha Ideia")

if enviar:
    campos_obrigatorios = [dono_da_ideia, matricula, area_do_operador, nome_da_ideia, descricao_de_problema,
                           descricao_da_solucao]
    if all(campos_obrigatorios):

        # CORREÇÃO 4: LÓGICA DE UPLOAD que estava faltando
        imagem_url = ""  # Começa como string vazia

        # 'imagem_para_enviar' é a variável do file_uploader de DENTRO do form
        if imagem_para_enviar is not None:
            if service_drive:
                try:
                    with st.spinner("Enviando imagem para o Google Drive..."):
                        imagem_url = upload_to_drive(service_drive, imagem_para_enviar, DRIVE_FOLDER_ID)
                except Exception as e:
                    st.error(f"Falha no upload da imagem: {e}")
                    st.stop()  # Para a execução se o upload falhar
            else:
                st.error("Conexão com Google Drive falhou. Não é possível salvar a imagem.")
                st.stop()
        # Fim da lógica de upload

        df_existente = carregar_dados()
        novo_id = (pd.to_numeric(df_existente['ID'],
                                 errors='coerce').max() + 1) if not df_existente.empty and 'ID' in df_existente else 1
        data_ideia = datetime.now(fuso_horario_sp).strftime("%d/%m/%Y")

        # Monta o dicionário com os dados para salvar
        nova_ideia = {
            "ID": int(novo_id), "Nome da ideia": nome_da_ideia, "Descrição da solução": descricao_da_solucao,
            "Descrição de problema": descricao_de_problema, "Área": area_aplicacao, "Local": local_aplicacao,
            "Dono da ideia": dono_da_ideia, "Matrícula": matricula, "Área do operador": area_do_operador,
            "Turno do operador que deu a ideia": turno_do_operador, "Data ideia": data_ideia,
            "Status": "Nova",

            # CORREÇÃO 5: Adiciona a 'imagem_url' (vazia ou com o link) ao dicionário
            "Imagem URL": imagem_url
        }

        salvar_ideia(nova_ideia)
        st.success("✅ Ideia registrada com sucesso! Agradecemos sua colaboração.")
        st.balloons()
    else:
        st.warning("⚠️ Por favor, preencha todos os campos marcados com *.")
