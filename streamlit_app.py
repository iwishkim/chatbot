import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI 챗봇", page_icon="💬")
st.title("💬 AI 챗봇")

with st.sidebar:
    st.header("설정")

    openai_api_key = st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, "secrets") else ""
    if not openai_api_key:
        openai_api_key = st.text_input("OpenAI API Key", type="password")

    st.divider()

    model = st.selectbox(
        "모델 선택",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
    )

    temperature = st.slider("창의성 (Temperature)", 0.0, 2.0, 0.7, 0.1)

    st.divider()

    system_prompt = st.text_area(
        "시스템 프롬프트 (AI 역할 설정)",
        value="당신은 친절하고 유능한 AI 어시스턴트입니다. 한국어로 답변해주세요.",
        height=120,
    )

    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if "messages" in st.session_state:
        st.caption(f"메시지 수: {len(st.session_state.messages)}개")

if not openai_api_key:
    st.info("왼쪽 사이드바에 OpenAI API Key를 입력하세요.", icon="🗝️")
    st.stop()

client = OpenAI(api_key=openai_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    stream = client.chat.completions.create(
        model=model,
        messages=api_messages,
        temperature=temperature,
        stream=True,
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
