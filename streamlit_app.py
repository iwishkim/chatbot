import streamlit as st
from openai import OpenAI
import tempfile
import os
import hashlib

st.set_page_config(page_title="AI 챗봇", page_icon="💬")
st.title("💬 AI 챗봇")

with st.sidebar:
    st.header("설정")

    try:
        openai_api_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        openai_api_key = ""
    if not openai_api_key:
        openai_api_key = st.text_input("OpenAI API Key", type="password")

    st.divider()

    model = st.selectbox(
        "모델 선택",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
    )

    temperature = st.slider("창의성 (Temperature)", 0.0, 2.0, 0.7, 0.1)

    st.divider()

    st.subheader("🎙️ 음성 설정")
    tts_enabled = st.toggle("AI 응답 음성으로 듣기", value=False)
    tts_voice = "nova"
    if tts_enabled:
        tts_voice = st.selectbox(
            "음성 선택",
            ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            index=4,
        )

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

if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

audio_value = st.audio_input("🎤 음성 입력 (클릭하여 녹음 시작)")
text_prompt = st.chat_input("메시지를 입력하세요...")

prompt = None

if audio_value:
    audio_bytes = audio_value.getvalue()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()

    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("음성을 텍스트로 변환 중..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file_path = tmp_file.name
            try:
                with open(tmp_file_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                    )
                prompt = transcript.text
            finally:
                os.unlink(tmp_file_path)

if text_prompt:
    prompt = text_prompt

if prompt:
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

    if tts_enabled and response:
        with st.spinner("음성 생성 중..."):
            tts_response = client.audio.speech.create(
                model="tts-1",
                voice=tts_voice,
                input=response,
            )
        st.audio(tts_response.content, format="audio/mp3", autoplay=True)
