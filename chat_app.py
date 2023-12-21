import streamlit as st
import streamlit_authenticator as stauth
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

questions = [
    'HTTPはどのようなものか答えてください',
    'HTTPメソッドPOSTとは何か答えてください'
]

def authenticate_user():
    credentials = {
        "usernames": {
            "test": {
                "name": "test",
                "password": "$2b$12$QEOjDRZvNatRI.CkimSgd.eYWAgEw7.NqCrZ1Nh4XexmS0Tdkxjp6"
            }
        }
    }

    authenticator = stauth.Authenticate(
        credentials=credentials,
        cookie_name="cookie_name",
        key="some_signature_key",
        cookie_expiry_days=30
    )

    # ログインページの表示
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        st.sidebar.success(f'Welcome {name}')
        return True
    elif authentication_status == False:
        st.error("Username/password is incorrect")
        return False
    elif authentication_status == None:
        st.warning("Please enter your username and password")
        return False

def init_page():
    st.set_page_config(
        page_title="Webアプリ用語100本ノック"
    )
    st.header("Webアプリ用語100本ノック")
    st.sidebar.title("Options")


def init_messages():
    clear_button = st.sidebar.button("Clear Conversation", key="clear")
    if clear_button or "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content="あなたは優秀な家庭教師です。出題した後に、生徒が回答するので正解まで導いてください。回答が誤っていた場合でも、すぐに答えを教えるのではなく、ヒントのみを出してください。また、回答が正解だった場合は、必ず「正解です」と言ってください"),
            AIMessage(content=questions[0])
        ]
        st.session_state.costs = []


def init_correct_num():
    st.sidebar.write("正解数: ", st.session_state.correct_answers_num)

def select_model():
    model = st.sidebar.radio("Choose a model:", ("GPT-3.5", "GPT-4"))
    if model == "GPT-3.5":
        model_name = "gpt-3.5-turbo"
    else:
        model_name = "gpt-4"

    # サイドバーにスライダーを追加し、temperatureを0から2までの範囲で選択可能にする
    # 初期値は0.0、刻み幅は0.1とする
    temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=2.0, value=0.0, step=0.01)

    return ChatOpenAI(temperature=temperature, model_name=model_name, streaming=True)


def main():
    if not authenticate_user():
        return

    llm = select_model()
    init_messages()

    if 'correct_answers_num' not in st.session_state:
        st.session_state.correct_answers_num = 0

    messages = st.session_state.get('messages', [])
    for message in messages:
        if isinstance(message, AIMessage):
            with st.chat_message('assistant'):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message('user'):
                st.markdown(message.content)
        # else:  # isinstance(message, SystemMessage):
            # st.write(f"System message: {message.content}")

    # ユーザーの入力を監視
    user_input = st.chat_input("こちらに回答を入力してください")
    if user_input:
        st.session_state.messages.append(HumanMessage(content=user_input))
        st.chat_message("user").markdown(user_input)
        with st.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            response = llm(messages, callbacks=[st_callback])
            if "正解です" in response.content:
                st.session_state.correct_answers_num += 1
        st.session_state.messages.append(AIMessage(content=response.content))

    init_correct_num()

if __name__ == '__main__':
    main()
