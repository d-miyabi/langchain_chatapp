import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import extra_streamlit_components as stx
import time
import logging
import traceback
from langchain.agents import AgentType, initialize_agent, load_tools
from datetime import datetime, timedelta
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage
)


# 初期設定
test_mode = True
del_mode = False
logging.basicConfig(level=logging.INFO)
cookie_manager = stx.CookieManager(key="cookie")
role = "あなたは優秀な家庭教師です。あなたの問いに対して生徒が回答したら、内容が妥当か判断してください。正しい場合は、「よく理解されていますね」と答え、返事の最後に「では、次の問題に進みましょう！」と必ず言ってください。また、必要に応じて補足の解説を行ってください。回答に不足や誤りがある場合は、正解は提示せずに、再度考えるよう促してください。ヒントが欲しいと言われたら、直接解答を教えることはせず、解答に至るようなヒントを提示してください。ヒントは、直接答えがわかってしまう内容ではなく、思考のきっかけを与えるだけにとどめてください。また、いつでも生徒がポジティブに取り組めるよう励ます言葉をかけてください。"


def get_expire_date():
    today = datetime.now()

    # 30日後の日付を計算
    future_date = today + timedelta(days=30)

    return future_date


def set_cookie():
    cleared_questions = st.session_state.cleared_questions
    val = list_to_string(cleared_questions)
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
        cookie_expiry_days=30
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
    if test_mode:
        logging.info("===== init_page start =====")

    st.header("面接対策100本ノック")
    st.write("このアプリは、面接時によく聞かれるWebアプリに関連する専門用語について、回答の仕方を練習するものです。")
    st.markdown("**使い方**")
    st.write("① 左のサイドバーから、取り組みたいテーマを選択してください。クリックすると面接官からの質問が行われます。")
    st.write("② 質問に対して回答を行なってください。")
    st.write("③ 回答が十分でない場合は追加を求められので、再度回答を行なってください。合格の場合は、「よく理解されていますね」と伝えられます。")



def init_messages():
    # role = "あなたは優秀な家庭教師です。あなたの問いに対して生徒が回答したら、内容が妥当か判断してください。正しい場合は、「よく理解されていますね」と答え、返事の最後に「次の問題に進みましょう」と必ず言ってください。また、必要に応じて補足を行ってください。不足や誤りがある場合は、正解は提示せずに、再度考えるよう促してください。ヒントが欲しいと言われたら、直接解答を教えることはせず、解答に至るようなヒントを提示してください。また、いつでも生徒がポジティブに取り組めるよう励ます言葉をかけてください。"

    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessage(content=role),
        ]
        st.session_state.costs = []


def find_dictionary_by_id(id_to_find):
    for dictionary in st.session_state.questions_list:
        if dictionary['id'] == id_to_find:
            return dictionary
    return None


def select_model():
    model_name = "gpt-4"
    temperature = 0
    # return ChatOpenAI(temperature=temperature, model_name=model_name, streaming=True)
    return ChatOpenAI(temperature=temperature, model_name=model_name, )


def create_dict_from_excel():
    file_path = './questions.xlsx'
    df = pd.read_excel(file_path)

    # Transform the DataFrame into the desired dictionary format
    dict_list = []
    for index, row in df.iterrows():
        # Check if the ID is not NaN and if the content is a string
        if pd.notna(row['ID']) and isinstance(row['内容'], str):
            content_with_newlines = row['内容'].replace('\r\n', '\n').strip()
            dict_list.append({
                "id": int(row['ID']),
                "title": row['タイトル'],
                "content": content_with_newlines
            })

    st.session_state.questions_list = dict_list


def display_questions():
    if test_mode:
        logging.info("===== display_questions開始 =====")

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
        logging.info("===== set_current_question開始 =====")

    st.session_state.current_question_id = id

    question_dict = find_dictionary_by_id(id)
    st.session_state.messages = [
        SystemMessage(content=role),
        AIMessage(content=question_dict['content'])
    ]

    if test_mode:
        logging.info("question_dict: " + question_dict['content'])


def register_cookie_to_state():
    if not "cleared_questions" in st.session_state:
        value = cookie_manager.get(cookie="cleared_questions")
        if value:
            st.session_state.cleared_questions = string_to_list(value)

            if test_mode:
                logging.info("===== クッキーの内容 =====")
                logging.info(value)
        else:
            st.session_state.cleared_questions = []

            if test_mode:
                logging.info("===== クッキーなし =====")


# 未使用の関数
# ストリームに変更するなら使う可能性あり
def create_agent_chain():
    chat = ChatOpenAI(
        model_name='gpt-4',
        temperature=0,
        streaming=True,
)
    tools = load_tools(["ddg-search"])
    return initialize_agent(tools, chat, agent=AgentType.OPENAI_FUNCTIONS)


def main():
    if test_mode:
        logging.info("===== main start =====")

        if "cleared_questions" in st.session_state:
            logging.info(st.session_state.cleared_questions)
        else:
            logging.info("cleared_questionsはありません")

        if "messages" in st.session_state:
            logging.info(st.session_state.messages)
        else:
            logging.info("messagesはありません")

        current_time = datetime.now()
        logging.info(current_time.strftime("%Y-%m-%d %H:%M:%S"))
        logging.info("\n")

    # 検証用のボタン
    if del_mode:
        if st.button("Delete"):
            cookie_manager.delete("cleared_questions")

        if st.button("Delete session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

    # 初期設定
    init_page()

    if test_mode:
        logging.info("===== init_page終了 =====")
        if "messages" in st.session_state:
            logging.info(st.session_state.messages)
            logging.info("\n")
        else:
            logging.info("messagesなし")
            logging.info("\n")

    register_cookie_to_state()
    display_questions()

    if test_mode:
        logging.info("===== display_questions終了 =====")
        if "messages" in st.session_state:
            logging.info(st.session_state.messages)
            logging.info("\n")
        else:
            logging.info("messagesなし")
            logging.info("\n")
    
    init_messages()

    messages = st.session_state.messages
    for message in messages:
        if isinstance(message, AIMessage):
            with st.chat_message('assistant'):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message('user'):
                st.markdown(message.content)

    # ユーザーの入力を監視
    if "current_question_id" in st.session_state:
        user_input = st.chat_input("こちらに回答を入力してください")
        if user_input:
            if test_mode:
                logging.info("===== ユーザー入力あり =====")
                logging.info("\n")

            with st.chat_message("user"):
                logging.info("セッション追加前")
                logging.info(st.session_state.messages)
                st.session_state.messages.append(HumanMessage(content=user_input))

                logging.info("セッション追加後")
                logging.info(st.session_state.messages)

                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner('考え中です...'):

                    if test_mode:
                        logging.info("llm実行直前")

                    response = llm(st.session_state.messages)

                    if test_mode:
                        logging.info("APIからのレスポンス直後")
                        logging.info(messages)

                    # container = st.container()
                    # st_callback = StreamlitCallbackHandler(container)


                    # agent_chain = create_agent_chain()
                    # response = agent_chain.run(messages, callbacks=[st_callback])
                    # st.markdown(response)
                    # st.chat_message("assistant").markdown(response)

                    st.session_state.messages.append(AIMessage(content=response.content))
                    st.markdown(response.content)
                    response.content = ""

            # ユーザーの回答が正しい場合の分岐
            if "では、次の問題に進みましょう" in response.content:
                if test_mode:
                    logging.info("正解の場合")
                    logging.info(st.session_state.messages)

                # 回答が正しい場合、問題idを追加
                if not st.session_state.current_question_id in st.session_state.cleared_questions:
                    st.session_state.cleared_questions.append(st.session_state.current_question_id)
                    set_cookie()


        # st.session_state.messages.append(AIMessage(content=response))
        # st.chat_message("assistant").markdown(response.content)
        # st.session_state.messages.append(AIMessage(content=response.content))

            if test_mode:
                logging.info("===== レスポンスのwith終了 =====")
                logging.info(response.content)


        # last_response = st.session_state.messages[-1]


if __name__ == '__main__':
    if authenticate_user():
        create_dict_from_excel()
        llm = select_model()
        
        main()
