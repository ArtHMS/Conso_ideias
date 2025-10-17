import streamlit as st
import pandas as pd
from datetime import datetime
from utils import carregar_dados, salvar_ideia, fuso_horario_sp
from PIL import Image

st.title("Importar Imagem")

uploaded_file = st.file_uploader("Escolha uma imagem", type="jpg")
if uploaded_file is not None:
    st.subheader("Imagem carregada")
    image = Image.open(uploaded_file)

    st.image(image, caption="Imagem carregada", use_column_width=True)
else:
    st.info("Faça o uploada de uma imagem")


hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(layout="centered", page_title="Cadastro de Ideias")

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
                                         "Planta de Soluções", "Portaria - EQ", "Produção", "Qualidade", "Recuperação de fibras",
                                         "Refino", "Rotulagem", "Segurança", "Torres de Resfriamento", "Torres de Vidro", "USE", "Zinco"])
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

    enviar = st.form_submit_button("🚀 Enviar Minha Ideia")

if enviar:
    campos_obrigatorios = [dono_da_ideia, matricula, area_do_operador, nome_da_ideia, descricao_de_problema,
                           descricao_da_solucao]
    if all(campos_obrigatorios):
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
            "Status": "Nova"  # Define o status inicial sempre como "Nova"
        }
        salvar_ideia(nova_ideia)
        st.success("✅ Ideia registrada com sucesso! Agradecemos sua colaboração.")
        st.balloons()
    else:
        st.warning("⚠️ Por favor, preencha todos os campos marcados com *.")
