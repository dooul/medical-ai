import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import tempfile

# 1. 페이지 기본 설정
st.set_page_config(page_title="AI 건강상담 및 진료 연계 보조 도구", layout="centered")

# 2. API 키 자동 로드 (Secrets 연동)
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_api_key = ""

# 3. 메인 타이틀 및 보조 도구 고지문
st.title("🩺 AI 건강상담 및 1차 스크리닝 보조 도구")
st.caption("의료 접근성 격차 해소를 위한 다국어·음성 지원 문진 및 적정 진료과 안내 시스템")

# 보조 도구 역할 명시 배너
st.warning("""
⚠️ **이용 전 필독 (의료법 제27조 준수 및 보조 도구 역할 명시)**  
본 서비스는 **질환의 최종 진단이나 처방을 내리지 않는 '1차 스크리닝 및 진료 연계 보조 도구'**입니다.  
입력된 증상을 바탕으로 **의심 가능한 가능성, 대처법, 추천 진료과**를 안내하며, 실제 진료와 치료는 반드시 전문 의료진과의 상담을 통해 진행되어야 합니다.
""")

# 4. 지원 언어 사전 정의 (16개 다국어)
LANGUAGES = {
    "한국어 (Korean)": {"code": "ko", "prompt": "Korean"},
    "English (영어)": {"code": "en", "prompt": "English"},
    "Tiếng Việt (베트남어)": {"code": "vi", "prompt": "Vietnamese"},
    "中文 (중국어 간체)": {"code": "zh-CN", "prompt": "Simplified Chinese"},
    "Русский (러시아어)": {"code": "ru", "prompt": "Russian"},
    "O'zbekcha (우즈베크어)": {"code": "uz", "prompt": "Uzbek"},
    "Tagalog / Filipino (필리핀어)": {"code": "tl", "prompt": "Tagalog"},
    "日本語 (일본어)": {"code": "ja", "prompt": "Japanese"},
    "ไทย (태국어)": {"code": "th", "prompt": "Thai"},
    "ភាសាខ្មែរ (캄보디아어)": {"code": "km", "prompt": "Khmer"},
    "Монгол хэл (몽골어)": {"code": "mn", "prompt": "Mongolian"},
    "नेपाली (네팔어)": {"code": "ne", "prompt": "Nepali"},
    "Bahasa Indonesia (인도네시아어)": {"code": "id", "prompt": "Indonesian"},
    "Español (스페인어)": {"code": "es", "prompt": "Spanish"},
    "Français (프랑스어)": {"code": "fr", "prompt": "French"},
    "العربية (아랍어)": {"code": "ar", "prompt": "Arabic"}
}

# 5. 사이드바: 언어 선택만 깔끔하게 유지
with st.sidebar:
    st.header("⚙️ 환경 설정")
    
    selected_lang_name = st.selectbox(
        "🌐 상담 언어 선택 (Language)",
        list(LANGUAGES.keys())
    )
    lang_info = LANGUAGES[selected_lang_name]

# 음성 변환 텍스트 보관용
if "symptom_text_val" not in st.session_state:
    st.session_state.symptom_text_val = ""

# 6. 환자 기본 문진 정보
st.subheader("1. 기본 문진 정보 입력")
col1, col2 = st.columns(2)
with col1:
    age_group = st.selectbox("연령대", ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"])
    gender = st.radio("성별", ["여성", "남성"], horizontal=True)
with col2:
    pain_scale = st.slider("통증/불편도 (NRS: 0 무통 ~ 10 극심한 통증)", 0, 10, 3)
    onset_time = st.text_input("증상 발현 시점", placeholder="예: 어제 밤부터, 3일 전부터")

# 7. 증상 입력 (음성 및 텍스트)
st.subheader("2. 증상 호소 (음성 또는 텍스트)")
st.write("🎙️ **타자 입력이 불편하시면 아래 마이크 버튼을 누르고 모국어로 말씀하세요.**")

# 음성 녹음 위젯
audio_rec = mic_recorder(
    start_prompt="🔴 마이크 켜기 (음성 녹음 시작)",
    stop_prompt="⏹️ 녹음 완료",
    key="mic_recorder"
)

# 음성 인식(STT) 처리
if audio_rec is not None and gemini_api_key:
    audio_bytes = audio_rec['bytes']
    if len(audio_bytes) > 0:
        with st.spinner("음성을 텍스트로 변환하고 있습니다..."):
            try:
                genai.configure(api_key=gemini_api_key)
                stt_model = genai.GenerativeModel("gemini-2.5-flash")
                audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
                stt_prompt = f"Listen to this audio carefully and transcribe exactly what the speaker says in {lang_info['prompt']}. Output only the transcribed sentence without any other explanation."
                transcription = stt_model.generate_content([audio_part, stt_prompt])
                
                st.session_state.symptom_text_val = transcription.text.strip()
                st.success(f"인식 완료: \"{st.session_state.symptom_text_val}\"")
            except Exception as e:
                st.error(f"음성 인식 중 오류 발생: {e}")

symptom_input = st.text_area(
    "증상 상세 설명",
    value=st.session_state.symptom_text_val,
    placeholder="예: 오른쪽 아랫배가 쥐어짜듯이 아프고 열이 나요.",
    height=90
)

chronic_meds = st.text_input("기저질환 및 복용 중인 약", placeholder="예: 당뇨약 복용 중, 고혈압")

# 8. 상담 실행 버튼
if st.button("🚀 AI 1차 스크리닝 시작", type="primary"):
    if not gemini_api_key:
        st.error("API 키 설정이 누락되었습니다. Streamlit Secrets 설정을 확인해 주세요.")
    elif not symptom_input:
        st.warning("증상을 음성 또는 텍스트로 입력해 주세요.")
    else:
        genai.configure(api_key=gemini_api_key)
        
        system_instruction = f"""
        당신은 의료 접근성 격차를 해소하기 위해 취약계층을 돕는 '공공 1차 건강상담 및 스크리닝 보조 AI'입니다.
        
        [역할 및 한계 준수]
        1. 당신은 의사가 아니며 최종 진단을 내릴 수 없습니다. 절대 특정 질환을 확정 진단하지 마십시오.
        2. '의심 가능한 질환 군(가능성)', '일반적인 대처 요령', '방문해야 할 적정 진료과'를 안내하는 보조 역할을 수행하십시오.
        
        [응답 작성 규칙]
        1. [언어 이원화]:
           - 환자용 안내 본문: 사용자가 선택한 언어 [{lang_info['prompt']}]로 알기 쉽고 친절하게 작성하십시오.
           - 의사용 사전 문진표 (SOAP Note): 상담 맨 마지막 섹션은 국내 병원 제출용이므로 반드시 [한국어 (Korean)]로 정돈하여 작성하십시오.
        2. [중증도 선별 (Triage)]: 흉통, 호흡곤란, 뇌졸중 의심 징후 등 응급 상황이 보이면 최상단에 즉시 응급실/119 방문을 알리는 경고를 표시하십시오.
        3. [권장 진료과]: 환자가 어느 진료과(내과, 이비인후과 등)로 가야 하는지 구체적으로 명시하십시오.
        4. [공공 근거 출처]: 질병관리청(KDCA), 건강보험심사평가원(HIRA) 등 공공 가이드라인을 근거로 제시하십시오.
        """
        
        user_content = f"""
        [환자 정보]
        - 선택 언어: {selected_lang_name}
        - 연령/성별: {age_group} / {gender}
        - 통증 점수 (NRS): {pain_scale} / 10
        - 발병 시점: {onset_time}
        - 기저질환 및 복용약: {chronic_meds}
        - 증상 호소 내용: {symptom_input}
        """
        
        with st.spinner("증상 분석 및 1차 스크리닝 결과를 생성 중입니다..."):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(
                    user_content,
                    generation_config=genai.types.GenerationConfig(temperature=0.2)
                )
                
                result_text = response.text
                st.success("1차 스크리닝이 완료되었습니다.")
                st.markdown("---")
                
                # 결과 출력
                st.subheader(f"3. 스크리닝 결과 안내 ({selected_lang_name})")
                st.markdown(result_text)
                
                # 음성 안내 (TTS)
                st.markdown("---")
                st.subheader("🔊 음성으로 결과 듣기")
                try:
                    clean_text = result_text.replace("#", "").replace("*", "").replace("-", "")[:250]
                    tts = gTTS(text=clean_text, lang=lang_info["code"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3")
                except Exception:
                    st.info("해당 언어 음성 재생(TTS)은 지원되지 않거나 본문이 너무 짧습니다.")
                
                # 병원 연계 버튼
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button("📍 내 주변 진료기관 안내 (공공 API 연동)")
                with col_btn2:
                    st.download_button(
                        label="📲 의료진 전달용 한국어 문진표(SOAP) 다운로드",
                        data=result_text,
                        file_name="pre_examination_note.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                st.error(f"결과 생성 실패: {e}")
