import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import tempfile
import json
import re
import time

# 1. 페이지 설정
st.set_page_config(page_title="AI 건강상담 및 1차 스크리닝 보조 도구", layout="centered")

# 2. Secrets API 키 로드
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_api_key = ""

# 3. 16개 다국어 UI 사전
LANG_PACK = {
    "한국어 (Korean)": {
        "code": "ko", "name": "Korean",
        "title": "🩺 AI 건강상담 및 1차 스크리닝 보조 도구",
        "caption": "의료 접근성 격차 해소를 위한 다국어·음성 지원 문진 및 적정 진료과 안내 시스템",
        "warning": "⚠️ **이용 전 필독 (보조 도구 역할 명시)**\n본 서비스는 질환의 최종 진단이나 처방을 내리지 않는 1차 스크리닝 보조 도구입니다. 실제 진료는 전문 의료진을 통해 진행되어야 합니다.",
        "sec1": "1. 음성으로 환자 정보 말하기 (스마트 음성 문진)",
        "voice_guide": "🎙️ 마이크를 켜고 **나이, 성별, 통증 정도, 발병 시점, 증상**을 말씀해 주세요.",
        "start_rec": "🔴 마이크 켜기 (녹음 시작)", "stop_rec": "⏹️ 녹음 완료",
        "sec2": "2. 인식된 문진 정보 (확인 및 수정)",
        "age_label": "연령대", "gender_label": "성별", "gender_opt": ["여성", "남성"],
        "pain_label": "통증/불편도 (NRS: 0 무통 ~ 10 극심한 통증)", "onset_label": "증상 발현 시점",
        "symptom_label": "증상 상세 설명", "meds_label": "기저질환 및 복용 약물",
        "sec3": "3. 1차 스크리닝 결과 안내",
        "btn_run": "🚀 AI 1차 스크리닝 시작", "tts_header": "🔊 모국어 음성으로 결과 듣기",
        "dl_btn": "📲 의료진 전달용 한국어 문진표(SOAP) 다운로드",
        "map_btn": "📍 내 주변 야간·휴일 진료기관 찾기 (응급의료포털)"
    },
    "English (영어)": {
        "code": "en", "name": "English",
        "title": "🩺 AI Health Consultation & Primary Screening Tool",
        "caption": "Multilingual & Voice-supported Pre-screening System for Reducing Medical Accessibility Gaps",
        "warning": "⚠️ **Notice (Auxiliary Tool Only)**\nThis service is an auxiliary pre-screening tool and does not provide a definitive diagnosis.",
        "sec1": "1. Voice Patient Registration (Smart Audio Triage)",
        "voice_guide": "🎙️ Press the mic and describe your **age, gender, pain level, onset time, and symptoms**.",
        "start_rec": "🔴 Start Recording", "stop_rec": "⏹️ Stop Recording",
        "sec2": "2. Extracted Patient Profile (Review & Edit)",
        "age_label": "Age Group", "gender_label": "Gender", "gender_opt": ["Female", "Male"],
        "pain_label": "Pain Scale (NRS: 0 No pain ~ 10 Severe pain)", "onset_label": "Onset Time",
        "symptom_label": "Detailed Symptoms", "meds_label": "Underlying Conditions & Medications",
        "sec3": "3. Screening Assessment Results",
        "btn_run": "🚀 Start AI Pre-screening", "tts_header": "🔊 Listen to Results (Audio)",
        "dl_btn": "📲 Download Korean SOAP Note for Local Doctors",
        "map_btn": "📍 Find Nearby Open Hospitals / Clinics in Korea"
    },
    "Tiếng Việt (베트남어)": {
        "code": "vi", "name": "Vietnamese",
        "title": "🩺 Công cụ Hỗ trợ Tư vấn Sức khỏe & Sàng lọc Ban đầu AI",
        "caption": "Hệ thống hỗ trợ giọng nói & đa ngôn ngữ giúp thu hẹp khoảng cách tiếp cận y tế",
        "warning": "⚠️ **Lưu ý quan trọng**\nDịch vụ này chỉ là công cụ hỗ trợ sàng lọc ban đầu.",
        "sec1": "1. Khai báo thông tin bằng giọng nói",
        "voice_guide": "🎙️ Bấm nút micro và nói về **tuổi, giới tính, mức độ đau, thời điểm bắt đầu và triệu chứng**.",
        "start_rec": "🔴 Bắt đầu ghi âm", "stop_rec": "⏹️ Hoàn tất",
        "sec2": "2. Thông tin bệnh nhân đã nhận diện",
        "age_label": "Độ tuổi", "gender_label": "Giới tính", "gender_opt": ["Nữ", "Nam"],
        "pain_label": "Mức độ đau (NRS: 0 Không đau ~ 10 Rất đau)", "onset_label": "Thời điểm bắt đầu",
        "symptom_label": "Mô tả chi tiết triệu chứng", "meds_label": "Bệnh lý nền & Thuốc đang dùng",
        "sec3": "3. Kết quả sàng lọc ban đầu",
        "btn_run": "🚀 Bắt đầu sàng lọc AI", "tts_header": "🔊 Nghe kết quả bằng giọng nói",
        "dl_btn": "📲 Tải phiếu khám tiếng Hàn (SOAP) nộp cho bác sĩ",
        "map_btn": "📍 Tìm bệnh viện / phòng khám gần nhất tại Hàn Quốc"
    },
    "中文 (중국어 간체)": {
        "code": "zh-CN", "name": "Simplified Chinese",
        "title": "🩺 AI健康咨询与初筛辅助工具",
        "caption": "支持多语言与语音的预问诊系统，致力于缩小医疗可及性差距",
        "warning": "⚠️ **使用须知（辅助工具声明）**\n本服务为初筛辅助工具，不提供最终诊断。",
        "sec1": "1. 语音智能问诊信息录入",
        "voice_guide": "🎙️ 请点击下方麦克风，说出您的**年龄、性别、疼痛程度、发病时间及症状**。",
        "start_rec": "🔴 开启麦克风（开始录音）", "stop_rec": "⏹️ 录音完成",
        "sec2": "2. 识别到的患者信息（可确认修改）",
        "age_label": "年龄段", "gender_label": "性别", "gender_opt": ["女性", "男性"],
        "pain_label": "疼痛等级（NRS: 0无痛 ~ 10极度剧痛）", "onset_label": "发病时间",
        "symptom_label": "症状详细描述", "meds_label": "既往病史及目前服药",
        "sec3": "3. 初步评估结果",
        "btn_run": "🚀 开始AI初步评估", "tts_header": "🔊 语音朗读评估结果",
        "dl_btn": "📲 下载供韩国医生参阅的韩语SOAP问诊单",
        "map_btn": "📍 查找韩国周边正在接诊的医疗机构"
    }
}

# 4. 사이드바 (언어 선택)
with st.sidebar:
    st.header("⚙️ Language / 언어")
    selected_lang_name = st.selectbox("Select Language", list(LANG_PACK.keys()))
    t = LANG_PACK[selected_lang_name]

st.title(t["title"])
st.caption(t["caption"])
st.warning(t["warning"])

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
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# Quota 429 방어용 안전 호출 함수
def call_gemini_safe(model_name, contents, system_instruction=None):
    genai.configure(api_key=gemini_api_key)
    kwargs = {"model_name": model_name}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction
    
    # 1차 시도 모델, 실패 시 더 여유로운 정식 플래시 모델로 자동 폴백
    models_to_try = [model_name, "gemini-2.5-flash", "gemini-1.5-flash"]
    
    for m in models_to_try:
        kwargs["model_name"] = m
        model = genai.GenerativeModel(**kwargs)
        for attempt in range(3):
            try:
                res = model.generate_content(
                    contents,
                    generation_config=genai.types.GenerationConfig(temperature=0.1)
                )
                return res
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    time.sleep(1.5 * (attempt + 1))  # 429 발생 시 잠시 대기 후 재시도
                    continue
                else:
                    break
    raise Exception("현재 무료 API 요청 한도(분당 5회)를 초과했습니다. 약 30초 뒤 다시 시도해 주세요.")

# 5. 음성으로 환자 정보 일괄 자동 추출
st.subheader(t["sec1"])
st.write(t["voice_guide"])

audio_rec = mic_recorder(
    start_prompt=t["start_rec"],
    stop_prompt=t["stop_rec"],
    key=f"rec_{t['code']}"
)

# 음성 입력 처리 (동일 음성 중복 호출 차단 캐싱)
if audio_rec is not None and gemini_api_key:
    audio_bytes = audio_rec.get("bytes", b"")
    if len(audio_bytes) > 0 and audio_bytes != st.session_state.last_processed_audio:
        with st.spinner("음성을 분석하여 환자 정보를 자동 입력 중입니다..."):
            try:
                audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
                extract_prompt = f"""
                Listen to this audio speaking in {t['name']}.
                Extract information into a JSON object:
                - age_group: one of ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"] (default "20대")
                - gender: "여성" or "남성" (default "여성")
                - pain_scale: integer 0 to 10 (default 4)
                - onset_time: when symptoms started
                - chronic_meds: any mentioned medications/illnesses
                - symptom_text: full transcription of symptoms

                Output ONLY raw JSON without markdown.
                """
                
                # 모델 호출 (요청하신 3.6-flash 우선 시도 후 429 발생 시 안전 폴백)
                resp = call_gemini_safe("gemini-3.6-flash", [audio_part, extract_prompt])
                
                if resp and resp.text:
                    clean_json = re.sub(r'```json|```', '', resp.text).strip()
                    extracted = json.loads(clean_json)
                    st.session_state.patient_data.update(extracted)
                    st.session_state.last_processed_audio = audio_bytes
                    st.success("음성 인식 및 문진 정보 자동 입력 성공!")
            except Exception as e:
                st.warning(f"안내: {e}")

# 6. 확인 및 수정 영역
st.subheader(t["sec2"])
col1, col2 = st.columns(2)
with col1:
    age_options = ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"]
    cur_age = st.session_state.patient_data.get("age_group", "20대")
    age_idx = age_options.index(cur_age) if cur_age in age_options else 1
    selected_age = st.selectbox(t["age_label"], age_options, index=age_idx)
    
    gender_options = ["여성", "남성"]
    cur_gender = st.session_state.patient_data.get("gender", "여성")
    gender_idx = gender_options.index(cur_gender) if cur_gender in gender_options else 0
    selected_gender = st.radio(t["gender_label"], t["gender_opt"], index=gender_idx, horizontal=True)

with col2:
    selected_pain = st.slider(
        t["pain_label"], 0, 10,
        int(st.session_state.patient_data.get("pain_scale", 3))
    )
    selected_onset = st.text_input(
        t["onset_label"],
        value=st.session_state.patient_data.get("onset_time", ""),
        placeholder="예: 어제 밤부터"
    )

selected_symptoms = st.text_area(
    t["symptom_label"],
    value=st.session_state.patient_data.get("symptom_text", ""),
    height=90
)
selected_meds = st.text_input(
    t["meds_label"],
    value=st.session_state.patient_data.get("chronic_meds", "")
)

# 7. AI 건강상담 분석 실행
if st.button(t["btn_run"], type="primary"):
    if not gemini_api_key:
        st.error("API 키가 없습니다. Streamlit Secrets를 확인해 주세요.")
    elif not selected_symptoms:
        st.warning("증상을 음성 또는 텍스트로 입력해 주세요.")
    else:
        system_instruction = f"""
        You are a public healthcare pre-screening AI assistant designed to reduce medical accessibility gaps.
        
        CRITICAL RULES:
        1. [LANGUAGE]: All explanations, triage, and advice MUST be strictly in **{t['name']}**.
        2. [SOAP NOTE]: At the very end, provide '### 🏥 의료진 전달용 사전 문진표 (SOAP Note)' written in KOREAN for local healthcare providers in Korea.
        3. [NO DEFINITIVE DIAGNOSIS]: Suggest possible conditions only.
        4. [EMERGENCY TRIAGE]: Warn to call 119/emergency immediately if life-threatening signs appear.
        5. [APPROPRIATE CLINIC]: Recommend the most appropriate primary clinic to visit in Korea.
        """
        
        user_prompt = f"""
        Respond completely in {t['name']}.
        
        Patient Profile:
        - Target Language: {t['name']}
        - Age / Gender: {selected_age} / {selected_gender}
        - Pain Scale: {selected_pain} / 10
        - Onset Time: {selected_onset}
        - Chronic Illness / Meds: {selected_meds}
        - Symptoms: {selected_symptoms}
        
        Response Format:
        1. [Triage / Urgency Level]
        2. [Possible Suspected Conditions]
        3. [Recommended Clinic / Department to visit in Korea]
        4. [First-aid & Home Care Advice]
        5. [의료진 전달용 사전 문진표 (SOAP Note in Korean)]
        """
        
        with st.spinner(f"{t['name']} 언어로 증상을 분석 중입니다..."):
            try:
                response = call_gemini_safe("gemini-3.6-flash", user_prompt, system_instruction=system_instruction)
                result_text = response.text
                
                st.success("스크리닝이 완료되었습니다.")
                st.markdown("---")
                
                # 결과 출력
                st.subheader(t["sec3"])
                st.markdown(result_text)
                
                # 음성 재생 (TTS)
                st.markdown("---")
                st.subheader(t["tts_header"])
                try:
                    spoken_part = result_text.split("의료진 전달용")[0].split("SOAP Note")[0]
                    clean_text = re.sub(r'[#*_\-`]', '', spoken_part).strip()[:350]
                    tts = gTTS(text=clean_text, lang=t["code"])
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                        tts.save(fp.name)
                        st.audio(fp.name, format="audio/mp3")
                except Exception:
                    st.info("음성 합성 엔진(TTS) 로딩 중입니다.")
                
                # 병원 연계 버튼
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.link_button(
                        t["map_btn"],
                        "https://www.e-gen.or.kr/egen/search_hospital.do"
                    )
                with col_btn2:
                    st.download_button(
                        label=t["dl_btn"],
                        data=result_text,
                        file_name="medical_soap_note.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                st.error(f"결과 생성 중 오류: {e}")
