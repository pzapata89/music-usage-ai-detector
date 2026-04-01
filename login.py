"""
Módulo de autenticación para Music Usage AI Detector.
Gestiona el login usando credenciales almacenadas en secrets/env.
"""

import hashlib
import time
import streamlit as st
from config import config

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 60


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
    # Always compute hash to prevent timing-based username enumeration
    computed_hash = _hash_password(password)
    if not expected_hash:
        return False
    return computed_hash == expected_hash


def show_login():
    """Muestra el formulario de login. Retorna True si el usuario está autenticado."""
    if st.session_state.get('authenticated'):
        return True

    # Check lockout before showing the form
    lockout_until = st.session_state.get('login_lockout_until', 0)
    if lockout_until and time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        st.error(f"Demasiados intentos fallidos. Intenta de nuevo en {remaining} segundos.")
        return False

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
            st.session_state['login_attempts'] = 0
            st.session_state['login_lockout_until'] = 0
            st.rerun()
        else:
            attempts = st.session_state.get('login_attempts', 0) + 1
            st.session_state['login_attempts'] = attempts
            if attempts >= MAX_LOGIN_ATTEMPTS:
                st.session_state['login_lockout_until'] = time.time() + LOCKOUT_SECONDS
                st.error(f"Demasiados intentos fallidos. Bloqueado por {LOCKOUT_SECONDS} segundos.")
            else:
                remaining_attempts = MAX_LOGIN_ATTEMPTS - attempts
                st.error(f"Usuario o contraseña incorrectos. {remaining_attempts} intento(s) restante(s).")

    return st.session_state.get('authenticated', False)


def logout():
    """Cierra la sesión del usuario."""
    st.session_state['authenticated'] = False
    st.session_state['username'] = None
    st.rerun()
