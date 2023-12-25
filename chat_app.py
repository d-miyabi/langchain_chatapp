import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import extra_streamlit_components as stx
import time
from datetime import datetime, timedelta
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)

test_mode = True

cookie_manager = stx.CookieManager(key="cookie")

def get_expire_date():
    today = datetime.now()

    # 30日後の日付を計算
    future_date = today + timedelta(days=30)

    return future_date


def set_cookie():
    cleared_questions = st.session_state.cleared_questions
    # st.subheader("Set Cookie:")
    # cookie = st.text_input("Cookie", key="1")
    val = list_to_string(cleared_questions)
    # if st.button("Add"):
    cookie_manager.set("cleared_questions", val, expires_at=get_expire_date())


def list_to_string(list):
    return ', '.join(str(x) for x in list)


def string_to_list(s):
    # 数値が直接渡された場合、その数値を含むリストを返す
    if isinstance(s, int):
        return [s]

    # 文字列が渡された場合の処理
    try:
        # 文字列をカンマで分割し、空白を削除した後に整数に変換
        return [int(x.strip()) for x in s.split(',') if x.strip().isdigit()]
    except ValueError:
        # 数値以外の文字が含まれている場合、エラーメッセージを返す
        return "入力された文字列は数値に変換できません。"


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
        cookie_expiry_days=0
    )

    # ログインページの表示
    name, authentication_status, username = authenticator.login('Login', 'main')

    if st.session_state['authentication_status']:
        st.sidebar.title("テーマ一覧")
        return True
    elif st.session_state['authentication_status'] == False:
        st.error("Username/password is incorrect")
        return False
    elif st.session_state['authentication_status'] == None:
        st.warning("Please enter your username and password")
        return False


def init_page():
    print("===== init_page start =====")
    st.header("面接対策100本ノック")
    st.write("このアプリは、面接時によく聞かれるWebアプリに関連する専門用語について、回答の仕方を練習するものです。")
    st.write("左のサイドバーから、取り組みたいテーマを選択してください。")


def init_messages():
    role = "あなたはエンジニア採用を行う面接官です。あなたの問いに対して入社希望者が回答したら、その回答に対して内容が妥当か判断してください。正しい場合は、「よく理解されていますね」と答えた上で、必要に応じて補足を行ってください。不足や誤りがある場合は、正解は提示せずに、再度考えるよう促してください"

    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=role),
        ]
        st.session_state.costs = []

    # if 'current_question_id' in st.session_state:
        # # if st.session_state.current_question_id != 9999:
        # question_id = st.session_state.current_question_id
        # question_dict = find_dictionary_by_id(question_id)
        # st.session_state.messages = [
        #     SystemMessage(content=role),
        #     AIMessage(content=question_dict['content'])
        # ]

def find_dictionary_by_id(id_to_find):
    for dictionary in st.session_state.questions_list:
        if dictionary['id'] == id_to_find:
            return dictionary
    return None


def select_model():
    model_name = "gpt-4"
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
    if test_mode:
        print("===== display_questions開始 =====")

    for item in st.session_state.questions_list:
        if item['id'] % 100 == 0:
            with st.sidebar:
                st.header(item['title'] + "に関するテーマ")
        else:
            if item['id'] in st.session_state.cleared_questions:
                item_name = "[ ○ ] " + item['title']
                st.sidebar.button(item_name, on_click=set_current_question, args=(item['id'],))

            else:
                item_name = "[ - ] " + item['title']
                st.sidebar.button(item_name, on_click=set_current_question, args=(item['id'],))


def set_current_question(id):
    if test_mode:
        print("===== set_current_question開始 =====")

    st.session_state.current_question_id = id
    role = "あなたはエンジニア採用を行う面接官です。あなたの問いに対して入社希望者が回答したら、その回答に対して内容が妥当か判断してください。正しい場合は、「よく理解されていますね」と答えた上で、必要に応じて補足を行ってください。不足や誤りがある場合は、正解は提示せずに、再度考えるよう促してください"

    question_dict = find_dictionary_by_id(id)
    st.session_state.messages = [
        SystemMessage(content=role),
        AIMessage(content=question_dict['content'])
    ]

    if test_mode:
        print("question_dict: " + question_dict['content'])

def register_cookie_to_state():
    if not "cleared_questions" in st.session_state:
        value = cookie_manager.get(cookie="cleared_questions")
        if value:
            st.session_state.cleared_questions = string_to_list(value)
            if test_mode:
                print("===== クッキーの内容 =====")
                print(value)
        else:
            st.session_state.cleared_questions = []
            if test_mode:
                print("===== クッキーなし =====")


def main():
    if test_mode:
        print("===== main start =====")
        current_time = datetime.now()
        print(current_time.strftime("%Y-%m-%d %H:%M:%S"))
        print("\n")

    # 検証用のボタン
    if test_mode:
        if st.button("Delete"):
            cookie_manager.delete("cleared_questions")

    # 初期設定
    init_page()

    if test_mode:
        print("===== init_page終了 =====")
        if "messages" in st.session_state:
            print(st.session_state.messages)
            print("\n")
        else:
            print("messagesなし")
            print("\n")

    register_cookie_to_state()
    create_dict_from_excel()
    display_questions()

    if test_mode:
        print("===== display_questions終了 =====")
        if "messages" in st.session_state:
            print(st.session_state.messages)
            print("\n")
        else:
            print("messagesなし")
            print("\n")


    llm = select_model()
    # init_messages()

    role = "あなたはエンジニア採用を行う面接官です。あなたの問いに対して入社希望者が回答したら、その回答に対して内容が妥当か判断してください。正しい場合は、「よく理解されていますね」と答えた上で、必要に応じて補足を行ってください。不足や誤りがある場合は、正解は提示せずに、再度考えるよう促してください"

    if "messages" not in st.session_state:
        print("messagesは存在しない")
        print("\n")

        st.session_state.messages = [
            SystemMessage(content=role),
        ]
        # st.session_state.costs = []
    
    messages = st.session_state.get('messages', [])
    for message in messages:
        if isinstance(message, AIMessage):
            with st.chat_message('assistant'):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message('user'):
                st.markdown(message.content)


    # ユーザーの入力を監視
    user_input = st.chat_input("こちらに回答を入力してください")
    if user_input:
        if test_mode:
            print("===== ユーザー入力あり =====")
            print("\n")

        st.session_state.messages.append(HumanMessage(content=user_input))
        st.chat_message("user").markdown(user_input)

        messages = st.session_state.get('messages', [])

        if test_mode:
            print("===== api使用直前 =====")
            print('messages')

        response = llm(messages)

        if test_mode:
            print("===== api使用直後 =====")
            print(response)

        st.session_state.messages.append(AIMessage(content=response.content))
        st.chat_message("assistant").markdown(response.content)

        # with st.chat_message("assistant"):
            # st_callback = StreamlitCallbackHandler(st.container())
            # response = llm(st.session_state.messages, callbacks=[st_callback])



        if test_mode:
            print("===== レスポンスのwith終了 =====")
            print(response)

        # st.session_state.messages.append(AIMessage(content=response.content))

        if test_mode:
            print("====== コールバック後にメッセージをアペンド =====")
            print(st.session_state.messages)
            print("\n")

        last_response = st.session_state.messages[-1]

        if test_mode:
            print("===== 最後のメッセージ =====")
            print(last_response)
            print('\n')


        if "よく理解されていますね" in last_response.content:
            print("含まれている")
            st.session_state.cleared_questions.append(st.session_state.current_question_id)
            set_cookie()
            print("ifおわり")
            print(st.session_state.messages)


if __name__ == '__main__':
    if authenticate_user():
        main()
