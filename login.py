"""
Módulo de autenticación para Music Usage AI Detector.
Gestiona el login usando credenciales almacenadas en secrets/env.
"""

import hashlib
import streamlit as st
from config import config


def _hash_password(password: str) -> str:
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        config.login_salt.encode('utf-8'),
        100000
    )
    return key.hex()


def check_credentials(username: str, password: str) -> bool:
    expected_hash = config.login_users.get(username)
    if not expected_hash:
        return False
    return _hash_password(password) == expected_hash


def show_login():
    """Muestra el formulario de login. Retorna True si el usuario está autenticado."""
    if st.session_state.get('authenticated'):
        return True

    st.markdown("""
    <div style="max-width: 400px; margin: 80px auto 0 auto;">
        <h2 style="text-align:center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 2rem; font-weight: 700;">
            🎵 Music Usage Detector
        </h2>
        <p style="text-align:center; color:#6b7280; margin-bottom: 2rem;">
            Ingresa tus credenciales para continuar
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

    if submitted:
        if check_credentials(username.strip(), password):
            st.session_state['authenticated'] = True
            st.session_state['username'] = username.strip()
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    return st.session_state.get('authenticated', False)


def logout():
    """Cierra la sesión del usuario."""
    st.session_state['authenticated'] = False
    st.session_state['username'] = None
    st.rerun()
