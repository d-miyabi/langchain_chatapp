import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

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
    st.header("面接対策100本ノック")
    st.write("このアプリは、面接時によく聞かれるWebアプリに関連する専門用語について、回答の仕方を練習するものです。")
    st.write("左のサイドバーから、取り組みたいテーマを選択してください。")


def init_messages():
    role = "あなたはエンジニア採用を行う面接官です。あなたの問いに対して入社希望者が回答したら、その回答に対して内容が妥当か判断してください。正しい場合は、「よく理解されていますね」と答えた上で、必要に応じて補足を行ってください。不足や誤りがある場合は、正解は提示せずに、再度考えるよう促してください"
    # clear_button = st.sidebar.button("Clear Conversation", key="clear")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=role),
        ]
        st.session_state.costs = []

    if 'current_question_id' in st.session_state:
        question_id = st.session_state.current_question_id
        question_dict = find_dictionary_by_id(question_id)
        st.session_state.messages = [
            SystemMessage(content=role),
            AIMessage(content=question_dict['content'])
        ]

def find_dictionary_by_id(id_to_find):
    for dictionary in st.session_state.questions_list:
        if dictionary['id'] == id_to_find:
            return dictionary
    return None


# def init_correct_num():
    # st.sidebar.write("正解数: ", st.session_state.correct_answers_num)


def select_model():
    model_name = "gpt-4"
    # temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=2.0, value=0.0, step=0.01)
    temperature = 0
    return ChatOpenAI(temperature=temperature, model_name=model_name, streaming=True)


def create_dict_from_excel():
    # Excelファイルを読み込む
    df = pd.read_excel('./questions.xlsx')

    # 辞書のリストを作成
    list_of_dicts = [
        {
            "id": int(row["ID"]),
            "title": row["タイトル"],
            "content": row["内容"]
        }
        for _, row in df.iterrows()
    ]

    st.session_state.questions_list = list_of_dicts


def display_questions():
    for item in st.session_state.questions_list:
        if item['id'] % 100 == 0:
            # idが100で割り切れる場合、サイドバーにH2を追加
            with st.sidebar:
                st.header(item['title'] + "に関するテーマ")
        else:
            st.sidebar.button(item['title'], on_click=set_current_question, args=(item['id'],))


def set_current_question(id):
    st.session_state.current_question_id = id


def main():
    if not authenticate_user():
        return

    create_dict_from_excel()
    display_questions()

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
            # if "正解です" in response.content:
            #     st.session_state.correct_answers_num += 1

        st.session_state.messages.append(AIMessage(content=response.content))

        if response:
            st.session_state.messages.append(AIMessage(content=response.content))




    # init_correct_num()

if __name__ == '__main__':
    init_page()
    main()
