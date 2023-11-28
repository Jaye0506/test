import streamlit as st
from streamlit.logger import get_logger
import hmac

LOGGER = get_logger(__name__)

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

def run():
    st.set_page_config(
        page_title="Hello",
        page_icon="👋",
    )

    st.write("# Leiting-Localization! 👋")
    st.markdown(
    """
        欢迎使用本地化工具网页端服务！！！
    """
    )
    data = {
        "序号": ["1", "2"],
        "工具": ["Format_String", "Similar_Extract"],
        "说明": ["文本参数格式化", "同质化文本抽取"],
    }
    # 在 Streamlit 应用中创建一个表格
    st.table(data)


if __name__ == "__main__":
    if not check_password():
        st.stop()
    run()
    st.session_state['Auth'] = True
