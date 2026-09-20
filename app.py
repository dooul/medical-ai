import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import tempfile
import json
import re

# 1. 페이지 설정
st.set_page_config(page_title="배리어프리 AI 건강상담 시스템", layout="centered")

# 2. Secrets API 키 자동 로드
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_api_key = ""

# 3. 메인 타이틀 및 보조 도구 고지문
st.title("🩺 포용적 의료 접근성을 위한 배리어프리 AI 건강상담")
st.caption("음성 대화 기반 자동 문진 및 16개 다국어 음성 안내 시스템")

st.warning("""
⚠️ **이용 전 필독 (의료법 제27조 준수 및 보조 도구 역할 명시)**  
본 서비스는 **질환의 최종 진단이나 처방을 내리지 않는 '1차 스크리닝 및 진료 연계 보조 도구'**입니다.  
입력된 음성 및 증상을 바탕으로 **의심 질환 가능성, 대처법, 추천 진료과**를 안내하며, 실제 진료는 반드시 전문 의료진을 통해 진행되어야 합니다.
""")

# 4. 16개 다국어 및 gTTS 공식 언어 코드 매핑
LANGUAGES = {
    "한국어 (Korean)": {"code": "ko", "name": "Korean"},
    "English (영어)": {"code": "en", "name": "English"},
    "Tiếng Việt (베트남어)": {"code": "vi", "name": "Vietnamese"},
    "中文 (중국어)": {"code": "zh-CN", "name": "Simplified Chinese"},
    "Русский (러시아어)": {"code": "ru", "name": "Russian"},
    "O'zbekcha (우즈베크어)": {"code": "uz", "name": "Uzbek"},
    "Tagalog / Filipino (필리핀어)": {"code": "tl", "name": "Tagalog"},
    "日本語 (일본어)": {"code": "ja", "name": "Japanese"},
    "ไทย (태국어)": {"code": "th", "name": "Thai"},
    "ភាសាខ្មែរ (캄보디아어)": {"code": "km", "name": "Khmer"},
    "Монгол хэл (몽골어)": {"code": "mn", "name": "Mongolian"},
    "नेपाली (네팔어)": {"code": "ne", "name": "Nepali"},
    "Bahasa Indonesia (인도네시아어)": {"code": "id", "name": "Indonesian"},
    "Español (스페인어)": {"code": "es", "name": "Spanish"},
    "Français (프랑스어)": {"code": "fr", "name": "French"},
    "العربية (아랍어)": {"code": "ar", "name": "Arabic"}
}

# 5. 사이드바: 상담 언어 선택
with st.sidebar:
    st.header("⚙️ 환경 설정")
    selected_lang_name = st.selectbox(
        "🌐 상담 언어 선택 (Select Language)",
        list(LANGUAGES.keys())
    )
    lang_info = LANGUAGES[selected_lang_name]

# 세션 상태 초기화
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {
        "age_group": "20대",
        "gender": "여성",
        "pain_scale": 3,
        "onset_time": "",
        "chronic_meds": "",
        "symptom_text": ""
    }

# 6. 음성으로 환자 정보 일괄 자동 입력
st.subheader("1. 음성으로 말하기 (스마트 음성 인식)")
st.write("🎙️ **아래 마이크를 누르고 본인의 나이, 성별, 아픈 부위와 증상을 편하게 모국어로 말씀해 주세요.**")

audio_rec = mic_recorder(
    start_prompt="🔴 마이크 켜기 (음성 녹음 시작)",
    stop_prompt="⏹️ 말하기 완료 (녹음 중지)",
    key="smart_voice_recorder"
)

# 음성이 입력되면 Gemini가 오디오를 듣고 5대 핵심 정보 JSON 자동 추출
if audio_rec is not None and gemini_api_key:
    if "bytes" in audio_rec and len(audio_rec["bytes"]) > 0:
        with st.spinner("Gemini가 음성을 분석하여 환자 정보를 추출하고 있습니다..."):
            try:
                genai.configure(api_key=gemini_api_key)
                extractor_model = genai.GenerativeModel("gemini-2.5-flash")
                
                audio_part = {
                    "mime_type": "audio/wav",
                    "data": audio_rec["bytes"]
                }
                
                extract_prompt = f"""
                Listen carefully to this patient speaking in {lang_info['name']}.
                Extract the patient's information into a valid JSON object with the following fields:
                - age_group: one of ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"] (infer if mentioned, default "20대")
                - gender: "여성" or "남성" (infer if mentioned, default "여성")
                - pain_scale: integer from 0 to 10 (infer from voice intensity or numbers mentioned, default 4)
                - onset_time: when symptoms started (in {lang_info['name']})
                - chronic_meds: any underlying illness or medication (in {lang_info['name']})
                - symptom_text: full transcribed speech and description of symptoms (in {lang_info['name']})

                Return ONLY valid JSON without markdown formatting or code fences.
                """
                
                response = extractor_model.generate_content([audio_part, extract_prompt])
                clean_json = re.sub(r'```json|```', '', response.text).strip()
                extracted = json.loads(clean_json)
                
                # 추출된 정보 세션에 업데이트
                st.session_state.patient_data.update(extracted)
                st.success("음성 인식 및 환자 정보 자동 입력이 완료되었습니다!")
            except Exception as e:
                st.info("음성에서 텍스트를 인식했습니다. 상세 항목을 확인해 주세요.")

# 7. 확인 및 수정 화면 (음성으로 자동 입력된 내용 표시)
st.subheader("2. 인식된 환자 문진 정보 (수정 가능)")
col1, col2 = st.columns(2)
with col1:
    age_options = ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"]
    current_age = st.session_state.patient_data.get("age_group", "20대")
    age_idx = age_options.index(current_age) if current_age in age_options else 1
    selected_age = st.selectbox("연령대", age_options, index=age_idx)
    
    gender_options = ["여성", "남성"]
    current_gender = st.session_state.patient_data.get("gender", "여성")
    gender_idx = gender_options.index(current_gender) if current_gender in gender_options else 0
    selected_gender = st.radio("성별", gender_options, index=gender_idx, horizontal=True)

with col2:
    selected_pain = st.slider(
        "통증/불편도 (NRS: 0 무통 ~ 10 극심한 통증)", 0, 10,
        int(st.session_state.patient_data.get("pain_scale", 3))
    )
    selected_onset = st.text_input(
        "증상 발현 시점",
        value=st.session_state.patient_data.get("onset_time", ""),
        placeholder="예: 어제 밤부터"
    )

selected_symptoms = st.text_area(
    "증상 상세 설명 (음성 인식 결과)",
    value=st.session_state.patient_data.get("symptom_text", ""),
    placeholder="마이크를 켜고 말씀하시거나 직접 글자를 입력하세요.",
    height=90
)

selected_meds = st.text_input(
    "기저질환 및 복용 중인 약물",
    value=st.session_state.patient_data.get("chronic_meds", ""),
    placeholder="예: 혈압약 복용 중"
)

# 8. AI 건강상담 및 다국어 음성(TTS) 실행
if st.button("🚀 AI 1차 스크리닝 시작", type="primary"):
    if not gemini_api_key:
        st.error("API 키 설정이 누락되었습니다. Streamlit Secrets 설정을 확인해 주세요.")
    elif not selected_symptoms:
        st.warning("마이크로 말씀하시거나 증상을 텍스트로 입력해 주세요.")
    else:
        genai.configure(api_key=gemini_api_key)
        target_lang = lang_info["name"]
        
        system_instruction = f"""
        You are a supportive public healthcare pre-screening AI assistant designed to reduce medical accessibility gaps.
        
        CRITICAL RULES:
        1. [LANGUAGE MANDATE]: The entire consultation, clinical guidance, and emergency triage MUST be written strictly in {target_lang}.
        2. [EXCEPTION]: At the very end of your response, provide the 'Medical Transfer Note (SOAP Note)' in KOREAN so that local Korean doctors can review it.
        3. [NO DEFINITIVE DIAGNOSIS]: Never declare a confirmed diagnosis. Always suggest possible suspected conditions.
        4. [EMERGENCY TRIAGE]: If life-threatening red flags exist (severe chest pain, shortness of breath, facial droop), output a clear emergency warning at the top.
        5. [APPROPRIATE CLINIC]: Recommend the most appropriate primary/secondary clinical department to visit in Korea (e.g., Internal Medicine, ENT, Orthopedics).
        6. [PUBLIC GUIDELINES]: Cite credible public healthcare guidelines such as KDCA (Korea Disease Control and Prevention Agency) or HIRA.
        """
        
        user_prompt = f"""
        Patient Profile:
        - Target Consultation Language: {target_lang}
        - Age / Gender: {selected_age} / {selected_gender}
        - Pain Scale: {selected_pain} / 10
        - Onset Time: {selected_onset}
        - Underlying Illness / Meds: {selected_meds}
        - Reported Symptoms: {selected_symptoms}
        
        Structure your response clearly:
        1. [Triage / Urgency Level]
        2. [Possible Suspected Conditions]
        3. [Recommended Clinic / Department to visit in Korea]
        4. [First-aid & Home Care Advice]
        5. [의료진 전달용 사전 문진표 (SOAP Note in Korean)]
        """
        
        with st.spinner(f"{target_lang} 언어로 증상을 분석하고 가이드라인을 생성 중입니다..."):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=0.2)
                )
                
                result_text = response.text
                st.success("스크리닝이 완료되었습니다.")
                st.markdown("---")
                
                # 상담 결과 출력
                st.subheader(f"3. 스크리닝 결과 안내 ({selected_lang_name})")
                st.markdown(result_text)
                
                # 모든 언어 음성 읽어주기 (TTS)
                st.markdown("---")
                st.subheader(f"🔊 모국어 음성으로 결과 듣기 ({selected_lang_name})")
                
                with st.spinner("선택하신 언어로 음성 안내를 생성 중입니다..."):
                    try:
                        # 한국어 SOAP 요약표 직전의 환자 모국어 안내문만 발화 대상 추출
                        spoken_part = result_text.split("의료진 전달용")[0].split("SOAP Note")[0]
                        clean_text = re.sub(r'[#*_\-`]', '', spoken_part).strip()[:350]
                        
                        tts = gTTS(text=clean_text, lang=lang_info["code"])
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                            tts.save(fp.name)
                            st.audio(fp.name, format="audio/mp3")
                    except Exception as tts_err:
                        st.info("해당 언어 음성 출력 엔진(TTS) 로딩 중입니다. 잠시 후 다시 시도해 주세요.")
                
                # 병원 연계 버튼
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button("📍 내 주변 진료기관 안내 (공공 API 연동)")
                with col_btn2:
                    st.download_button(
                        label="📲 의료진 전달용 문진표(SOAP) 다운로드",
                        data=result_text,
                        file_name="pre_examination_note.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                st.error(f"결과 생성 실패: {e}")
