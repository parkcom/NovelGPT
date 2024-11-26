import os
import uuid

import openai
import streamlit as st

from ch09_dalle import get_image_by_dalle
from ch09_gpt import get_llm

st.set_page_config(
    page_title="📚 NovelGPT", layout="wide", initial_sidebar_state="expanded"
)


@st.cache_data(show_spinner="Generating your story...")
def get_output(_pos: st.empty, oid="", genre="", prompt=""):
    if oid:
        st.session_state["genreBox_state"] = True  # 제목 입력칸
        st.session_state[f"expanded_{oid}"] = False  # 스토리
        st.session_state[f"radio_{oid}_disabled"] = True  # 라디오 버튼
        st.session_state[f"submit_{oid}_disabled"] = True  # 진행하기 버튼

        user_choice = st.session_state[f"radio_{oid}"]

    # 처음 시작할 때는 사용자의 선택이 없으므로 user_choice에 제목을 저장
    if genre:
        st.session_state["genreBox_state"] = False
        user_choice = genre

    with _pos:
        data = get_story_and_image(genre, user_choice)
        add_new_data(
            data["story"], data["decisionQuestion"], data["choices"], data["dalle_img"]
        )


def get_story_and_image(genre, user_choice):
    client = openai.OpenAI()
    llm_model = get_llm("test")

    llm_generation_result = llm_model.invoke(
        {"input": user_choice}, config={"configurable": {"session_id": "test"}}
    ).content

    response_list = llm_generation_result.split("\n")

    if len(response_list) != 1:
        img_prompt = response_list[-1]
        dalle_img = get_image_by_dalle(client, genre, img_prompt)
    else:
        dalle_img = None

    choices = []
    story = ""

    responses = list(filter(lambda x: x != "" and x != "-- -- --", response_list))
    responses = list(
        filter(lambda x: "Dalle Prompt" not in x and "Image prompt" not in x, responses)
    )
    responses = [s for s in responses if s.strip()]

    for response in responses:
        if response.startswith("선택지:"):
            decisionQuestion = "**" + response + "**"
        elif response[1] == ".":
            choices.append(response)
        else:
            story += response + "\n"

    story = story.replace(img_prompt, "")

    return {
        "story": story,
        "decisionQuestion": decisionQuestion,
        "choices": choices,
        "dalle_img": dalle_img,
    }


def add_new_data(*data):
    oid = str(uuid.uuid4())

    st.session_state["oid_list"].append(oid)
    st.session_state["data_dict"][oid] = data


def generate_content(story, decisionQuestion, choices: list, img, oid):
    if f"expanded_{oid}" not in st.session_state:
        st.session_state[f"expanded_{oid}"] = True
    if f"radio_{oid}_disabled" not in st.session_state:
        st.session_state[f"radio_{oid}_disabled"] = False
    if f"submit_{oid}_disabled" not in st.session_state:
        st.session_state[f"submit_{oid}_disabled"] = False

    story_pt = list(st.session_state["data_dict"].keys()).index(oid) + 1

    expander = st.expander(
        f"Part {story_pt}", expanded=st.session_state[f"expanded_{oid}"]
    )
    col1, col2 = expander.columns([0.65, 0.35])
    empty = st.empty()

    if img:
        col2.image(img, width=40, use_container_width=True)

    with col1:
        st.write(story)

        if decisionQuestion and choices:
            with st.form(key=f"user_choice_{oid}"):
                st.radio(
                    decisionQuestion,
                    choices,
                    disabled=st.session_state[f"radio_{oid}_disabled"],
                    key=f"radio_{oid}",
                )
                st.form_submit_button(
                    label="진행하기",
                    disabled=st.session_state[f"submit_{oid}_disabled"],
                    on_click=get_output,
                    args=[empty],
                    kwargs={"oid": oid},
                )


def main():
    st.title("📚 NovelGPT")
    if "data_dict" not in st.session_state:
        st.session_state["data_dict"] = {}

    if "oid_list" not in st.session_state:
        st.session_state["oid_list"] = []

    if "openai_api_key" not in st.session_state:
        st.session_state["openai_api_key"] = os.getenv("OPENAI_API_KEY")

    if "apiBox_state" not in st.session_state:
        st.session_state["apiBox_state"] = False

    if "genre_input" not in st.session_state:
        st.session_state["genre_input"] = "아기 펭귄 보물이의 모험"

    if "genreBox_state" not in st.session_state:
        st.session_state["genreBox_state"] = True

    def auth():
        os.environ["OPENAI_API_KEY"] = st.session_state["openai_api_key"]
        st.session_state.genreBox_state = False

        st.session_state.apiBox_state = True

    with st.sidebar:
        st.header("📚 NovelGPT")
        st.markdown("""
        NovelGPT는 소설을 작성하는 인공지능입니다. GPT-4와 Dall-E를 사용하여 스토리가 진행됩니다.
        """)

        st.info("**Note** OpenAI API Key 를 입력하세요.")

        with st.form(key="API Keys"):
            openai_key = st.text_input(
                label="OpenAI API Key",
                key="openai_api_key",
                type="password",
                disabled=st.session_state["apiBox_state"],
                help="OpenAI API 키는 https://platform.openai.com/account/api-keys 에서 발급 가능합니다.",
            )

            btn = st.form_submit_button(label="Submit", on_click=auth)

        with st.expander("사용 가이드"):
            st.markdown("""
            - 위의 입력 칸에 <OpenAI API Key>를 작성후 [Submit] 버튼을 누르세요.
            - 그 후 우측 화면에 주제나 주인공에 대한 서술을 묘사하고 [시작!] 버튼을 누르세요.
            - 스토리가 시작되면 선택지를 누르며 내용을 전개합니다.
            """)

        with st.expander("더 많은 예시 보러가기"):
            st.write(
                "[베스트셀러! 진짜 챗GPT API 활용법](https://www.yes24.com/Product/Goods/121773683)"
            )

    if not openai_key.startswith("sk-"):
        st.warning("OpenAI API Key가 입력되지 않았습니다.", icon="⚠️")

    with st.container():
        col_1, col_2, col_3 = st.columns([8, 1, 1], gap="small")

        col_1.text_input(
            label="Enter the theme/genre of your story",
            key="genre_input",
            placeholder="Enter the theme of which you want to the story to be",
            disabled=st.session_state["genreBox_state"],
        )

        col_2.write("")
        col_2.write("")
        col_2_cols = col_2.columns([0.5, 6, 0.5])
        col_2_cols[1].button(
            ":arrows_counterclockwise: &nbsp; Clear",
            key="clear_btn",
            on_click=lambda: setattr(st.session_state, "genre_input", ""),
            disabled=st.session_state["genreBox_state"],
        )

        col_3.write("")
        col_3.write("")
        begin = col_3.button(
            "시작!",
            on_click=get_output,
            args=[st.empty()],
            kwargs={"genre": st.session_state["genre_input"]},
            disabled=st.session_state["genreBox_state"],
        )

    for oid in st.session_state["oid_list"]:
        data = st.session_state["data_dict"][oid]
        story = data[0]
        decisionQuestion = data[1]
        choices = data[2]
        img = data[3]

        generate_content(story, decisionQuestion, choices, img, oid)


if __name__ == "__main__":
    main()
