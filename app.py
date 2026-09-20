import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import tempfile

# 1. 페이지 설정
st.set_page_config(page_title="Gemini 배리어프리 AI 건강상담 시스템", layout="centered")

st.title("🩺 포용적 의료 접근성을 위한 Gemini AI 건강상담")
st.caption("고령층·시각 취약계층(음성 입출력) 및 다문화·이주배경 주민(16개 다국어 지원)")

# 2. 지원 언어 사전 정의 (국내 다문화 가구 및 외국인 근로자 주요 사용 언어 망라)
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

# 3. 사이드바 설정 (API 키 입력 및 언어 선택)
with st.sidebar:
    st.header("⚙️ 환경 및 언어 설정")
    gemini_api_key = st.text_input("Google Gemini API 키 입력", type="password")
    
    selected_lang_name = st.selectbox(
        "🌐 상담 언어 선택 (Select Language)",
        list(LANGUAGES.keys())
    )
    lang_info = LANGUAGES[selected_lang_name]
    
    st.markdown("---")
    st.info("""
    💡 **학술제 핵심 가치 (의료 접근성 격차 해소)**
    1. **언어 장벽 제거**: 16개국 다국어 상담 지원
    2. **물리적 장벽 제거**: 음성 녹음(STT) 및 읽어주기(TTS)
    3. **임상 연계**: 환자 모국어 안내 + 국내 의료진용 한국어 문진표(SOAP) 동시 발행
    """)

# 음성 인식 결과 저장용 세션
if "symptom_text_val" not in st.session_state:
    st.session_state.symptom_text_val = ""

# 4. 환자 기본 상태 입력
st.subheader("1. 기본 문진 정보")
col1, col2 = st.columns(2)
with col1:
    age_group = st.selectbox("연령대", ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"])
    gender = st.radio("성별", ["여성", "남성"], horizontal=True)
with col2:
    pain_scale = st.slider("통증/불편도 (NRS: 0 무통 ~ 10 극심한 통증)", 0, 10, 3)
    onset_time = st.text_input("증상 발생 시점", placeholder="예: 어제 밤부터, 2일 전부터")

# 5. 증상 입력 (음성 및 텍스트)
st.subheader("2. 증상 호소 (음성 또는 텍스트 입력)")
st.write("🎙️ **타자 입력이 불편하시면 아래 마이크 버튼을 누르고 모국어로 말씀하세요.**")

# 음성 녹음기
audio_rec = mic_recorder(
    start_prompt="🔴 마이크 켜기 (음성 녹음 시작)",
    stop_prompt="⏹️ 녹음 완료",
    key="mic_recorder"
)

# 녹음된 음성을 Gemini에 전달하여 자동 텍스트 변환 (STT)
if audio_rec is not None and gemini_api_key:
    audio_bytes = audio_rec['bytes']
    if len(audio_bytes) > 0:
        with st.spinner("Gemini가 음성을 텍스트로 변환 중입니다..."):
            try:
                genai.configure(api_key=gemini_api_key)
                stt_model = genai.GenerativeModel("gemini-2.5-flash")
                audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
                stt_prompt = f"Listen to this audio carefully and transcribe exactly what the speaker says in {lang_info['prompt']}. Output only the transcribed sentence without any other text."
                transcription = stt_model.generate_content([audio_part, stt_prompt])
                
                st.session_state.symptom_text_val = transcription.text.strip()
                st.success(f"인식된 음성: \"{st.session_state.symptom_text_val}\"")
            except Exception as e:
                st.error(f"음성 처리 중 오류 발생: {e}")

symptom_input = st.text_area(
    "증상 상세 설명",
    value=st.session_state.symptom_text_val,
    placeholder="예: 오른쪽 아랫배가 쥐어짜듯이 아프고 열이 나요.",
    height=90
)

chronic_meds = st.text_input("기저질환 및 복용 중인 약", placeholder="예: 당뇨약 복용 중, 고혈압")

# 6. Gemini 상담 분석 실행
if st.button("🚀 Gemini 배리어프리 건강상담 시작", type="primary"):
    if not gemini_api_key:
        st.error("좌측 사이드바에 Google Gemini API 키를 입력해 주세요.")
    elif not symptom_input:
        st.warning("증상을 음성으로 말씀하시거나 텍스트로 입력해 주세요.")
    else:
        genai.configure(api_key=gemini_api_key)
        
        # 시스템 프롬프트: 설문 단점(오진, 출처 미흡, 맞춤형 결여) 보완 및 다국어-한국어 이원화
        system_instruction = f"""
        당신은 의료 접근성 격차를 해소하기 위해 취약계층(외국인 근로자, 다문화 가정, 고령자)을 돕는 공공 의료상담 전문 AI입니다.
        
        아래 5대 수칙을 철저히 준수하여 상담 보고서를 작성하십시오:
        1. [확정 진단 금지]: 절대 질환을 확정 진단하지 말고, 가능성이 있는 질환군(의심 소견)을 2~3개 제시하십시오.
        2. [언어 분리 원칙]:
           - 환자용 안내문: 반드시 사용자가 선택한 언어 [{lang_info['prompt']}]로 이해하기 쉽게 친절하게 작성하십시오.
           - 의사용 사전 문진표 (SOAP Note): 상담 맨 마지막 섹션은 반드시 [한국어 (Korean)]로 작성해야 합니다. (국내 의료진 전달 목적)
        3. [적정 1차 진료과 안내]: 환자가 가장 먼저 방문해야 할 병원 진료과(내과, 외과, 이비인후과 등)를 명확히 제시하십시오.
        4. [응급 징후 Triage]: 호흡 곤란, 흉통, 편마비 등 긴급 상황 징후가 보이면 맨 위에 강력한 응급실 안내 문구를 띄우십시오.
        5. [공공 가이드라인 출처]: 질병관리청(KDCA), 건강보험심사평가원(HIRA) 표준 지침을 근거로 표기하십시오.
        """
        
        user_content = f"""
        [환자 기초 프로필]
        - 선택 언어: {selected_lang_name}
        - 연령대 / 성별: {age_group} / {gender}
        - 통증 점수 (NRS): {pain_scale} / 10
        - 발병 시점: {onset_time}
        - 기저질환 및 복용약: {chronic_meds}
        - 호소 증상: {symptom_input}
        """
        
        with st.spinner("Gemini가 증상 분석 및 맞춤형 가이드라인을 생성 중입니다..."):
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
                st.success("상담 결과 생성이 완료되었습니다.")
                st.markdown("---")
                
                # 7. 환자용 안내 결과 출력
                st.subheader(f"3. AI 건강상담 결과 ({selected_lang_name})")
                st.markdown(result_text)
                
                # 8. 음성 안내 재생 (TTS)
                st.markdown("---")
                st.subheader("🔊 음성으로 결과 듣기 (TTS)")
                try:
                    # 마크다운 기호 제거 후 첫 250자 발화
                    clean_text = result_text.replace("#", "").replace("*", "").replace("-", "")[:250]
                    tts = gTTS(text=clean_text, lang=lang_info["code"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3")
                except Exception as tts_err:
                    st.info("해당 언어의 음성 합성 엔진(TTS)이 지원되지 않거나 텍스트가 너무 짧습니다.")
                
                # 9. 병원 진료 연계
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button("📍 내 주변 야간·휴일 진료기관 찾기 (공공 API)")
                with col_btn2:
                    st.download_button(
                        label="📲 병원 제출용 한국어 문진표(SOAP) 다운로드",
                        data=result_text,
                        file_name="medical_pre_examination.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                st.error(f"상담 생성 실패: {e}")
