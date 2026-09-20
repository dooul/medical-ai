import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import tempfile
import json
import re
import time

# 1. 페이지 기본 설정
st.set_page_config(page_title="AI 건강상담 및 1차 스크리닝 보조 도구", layout="centered")

# 2. Secrets API 키 로드
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_api_key = ""

# 3. 16개 다국어 UI 사전 정의
LANG_PACK = {
    "한국어 (Korean)": {
        "code": "ko", "name": "Korean",
        "title": "🩺 AI 건강상담 및 1차 스크리닝 보조 도구",
        "caption": "의료 접근성 격차 해소를 위한 다국어·음성 지원 문진 및 적정 진료과 안내 시스템",
        "warning": "⚠️ **이용 전 필독 (보조 도구 역할 명시)**\n본 서비스는 질환의 최종 진단이나 처방을 내리지 않는 1차 스크리닝 보조 도구입니다. 실제 진료와 치료는 반드시 전문 의료진과의 상담을 통해 진행되어야 합니다.",
        "sec1": "1. 음성으로 환자 정보 말하기 (스마트 음성 문진)",
        "voice_guide": "🎙️ 아래 마이크 버튼을 누르고 **나이, 성별, 통증 정도, 발병 시점, 증상**을 편하게 모국어로 말씀해 주세요.",
        "start_rec": "🔴 마이크 켜기 (녹음 시작)", "stop_rec": "⏹️ 녹음 완료",
        "sec2": "2. 인식된 문진 정보 (수정 및 확인)",
        "age_label": "연령대", "gender_label": "성별", "gender_opt": ["여성", "남성"],
        "pain_label": "통증/불편도 (NRS: 0 무통 ~ 10 극심한 통증)", "onset_label": "증상 발현 시점",
        "symptom_label": "증상 상세 설명", "meds_label": "기저질환 및 복용 약물",
        "sec3": "3. 1차 스크리닝 결과 안내",
        "btn_run": "🚀 AI 1차 스크리닝 시작", "tts_header": "🔊 모국어 음성으로 결과 듣기",
        "dl_btn": "📲 의료진 전달용 한국어 문진표(SOAP) 다운로드",
        "map_btn": "📍 내 주변 야간·휴일 진료기관 찾기 (공공 응급의료포털)"
    },
    "English (영어)": {
        "code": "en", "name": "English",
        "title": "🩺 AI Health Consultation & Primary Screening Tool",
        "caption": "Multilingual & Voice-supported Pre-screening System for Reducing Medical Accessibility Gaps",
        "warning": "⚠️ **Notice (Auxiliary Tool Only)**\nThis service is a primary pre-screening auxiliary tool and does not provide a definitive diagnosis. Always consult a qualified medical professional.",
        "sec1": "1. Voice Patient Registration (Smart Audio Triage)",
        "voice_guide": "🎙️ Press the microphone below and describe your **age, gender, pain level, onset time, and symptoms**.",
        "start_rec": "🔴 Start Recording", "stop_rec": "⏹️ Stop Recording",
        "sec2": "2. Extracted Patient Profile (Review & Edit)",
        "age_label": "Age Group", "gender_label": "Gender", "gender_opt": ["Female", "Male"],
        "pain_label": "Pain Scale (NRS: 0 No pain ~ 10 Severe pain)", "onset_label": "Symptom Onset Time",
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
        "warning": "⚠️ **Lưu ý quan trọng**\nDịch vụ này chỉ là công cụ hỗ trợ sàng lọc ban đầu và không thay thế chẩn đoán y tế chính thức. Hãy luôn thăm khám bác sĩ chuyên khoa.",
        "sec1": "1. Khai báo thông tin bằng giọng nói",
        "voice_guide": "🎙️ Bấm nút micro và nói về **tuổi, giới tính, mức độ đau, thời điểm bắt đầu và triệu chứng** bằng tiếng mẹ đẻ.",
        "start_rec": "🔴 Bắt đầu ghi âm", "stop_rec": "⏹️ Hoàn tất",
        "sec2": "2. Thông tin bệnh nhân đã nhận diện (Kiểm tra & Sửa)",
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
        "warning": "⚠️ **使用须知（辅助工具声明）**\n本服务为初筛辅助工具，不提供最终诊断。如需确诊与治疗，请务必前往正规医疗机构就诊。",
        "sec1": "1. 语音智能问诊信息录入",
        "voice_guide": "🎙️ 请点击下方麦克风，直接说出您的**年龄、性别、疼痛程度、发病时间及具体症状**。",
        "start_rec": "🔴 开启麦克风（开始录音）", "stop_rec": "⏹️ 录音完成",
        "sec2": "2. 识别到的患者信息（可确认并修改）",
        "age_label": "年龄段", "gender_label": "性别", "gender_opt": ["女性", "男性"],
        "pain_label": "疼痛等级（NRS: 0无痛 ~ 10极度剧痛）", "onset_label": "发病时间",
        "symptom_label": "症状详细描述", "meds_label": "既往病史及目前服药",
        "sec3": "3. 初步评估结果",
        "btn_run": "🚀 开始AI初步评估", "tts_header": "🔊 语音朗读评估结果",
        "dl_btn": "📲 下载供韩国医生参阅的韩语SOAP问诊单",
        "map_btn": "📍 查找韩国周边正在接诊的医疗机构"
    },
    "Русский (러시아어)": {
        "code": "ru", "name": "Russian",
        "title": "🩺 AI-инструмент предварительного скрининга здоровья",
        "caption": "Многоязычная система поддержки для устранения барьеров в доступности медицины",
        "warning": "⚠️ **Важное уведомление**\nДанная система является вспомогательным инструментом и не ставит окончательный диагноз. Обратитесь к врачу.",
        "sec1": "1. Голосовой ввод данных пациента",
        "voice_guide": "🎙️ Нажмите на микрофон и назовите свой **возраст, пол, уровень боли, когда началось и симптомы**.",
        "start_rec": "🔴 Начать запись", "stop_rec": "⏹️ Завершить",
        "sec2": "2. Распознанные данные (Проверка и редактирование)",
        "age_label": "Возраст", "gender_label": "Пол", "gender_opt": ["Женский", "Мужской"],
        "pain_label": "Шкала боли (0 - нет боли ~ 10 - нестерпимая боль)", "onset_label": "Когда начались симптомы",
        "symptom_label": "Подробное описание симптомов", "meds_label": "Хронические заболевания и лекарства",
        "sec3": "3. Результаты предварительной оценки",
        "btn_run": "🚀 Начать первичный скрининг AI", "tts_header": "🔊 Прослушать результат голосом",
        "dl_btn": "📲 Скачать корейскую форму SOAP для врача",
        "map_btn": "📍 Найти ближайшие клиники и больницы в Корее"
    },
    "O'zbekcha (우즈베크어)": {
        "code": "uz", "name": "Uzbek",
        "title": "🩺 AI Sog'liqni Saqlash va Dastlabki Skrining Yordamchisi",
        "caption": "Tibbiy yordamdan foydalanish imkoniyatini oshirish uchun ko'p tilli tizim",
        "warning": "⚠️ **Muhim eslatma**\nBu xizmat yordamchi vosita bo'lib, yakuniy tashxis qo'ymaydi. Shifokor bilan maslahatlashing.",
        "sec1": "1. Ovozli bemor ma'lumotlarini kiritish",
        "voice_guide": "🎙️ Mikrofoni yoqing va **yoshingiz, jinsingiz, og'riq darajasi va alomatlarni** ayting.",
        "start_rec": "🔴 Ovoz yozish", "stop_rec": "⏹️ Tugatish",
        "sec2": "2. Aniqlangan ma'lumotlar",
        "age_label": "Yosh guruhi", "gender_label": "Jinsi", "gender_opt": ["Ayol", "Erkak"],
        "pain_label": "Og'riq darajasi (0 dan 10 gacha)", "onset_label": "Qachon boshlangan",
        "symptom_label": "Belgilar tavsifi", "meds_label": "Surunkali kasalliklar va dorilar",
        "sec3": "3. Skrining xulosasi",
        "btn_run": "🚀 Skriningni boshlash", "tts_header": "🔊 Ovozli eshitish",
        "dl_btn": "📲 Shifokor uchun koreyscha SOAP varaqasini yuklab olish",
        "map_btn": "📍 Koreyadagi yaqin shifoxonani topish"
    },
    "Tagalog (필리핀어)": {
        "code": "tl", "name": "Tagalog",
        "title": "🩺 AI Konsultasyon sa Kalusugan at Pangunahing Screening",
        "caption": "Multilingual na sistema para mapabuti ang serbisyong medikal",
        "warning": "⚠️ **Mahalagang Paunawa**\nIto ay gabay lamang at hindi pinal na diagnosis. Kumonsulta sa doktor.",
        "sec1": "1. Voice Triage (Sabihin ang Impormasyon)",
        "voice_guide": "🎙️ Pindutin ang mikropono at sabihin ang iyong **edad, kasarian, antas ng sakit, at mga sintomas**.",
        "start_rec": "🔴 Simulan ang Voice", "stop_rec": "⏹️ Tapusin",
        "sec2": "2. Nakuhang Impormasyon ng Pasyente",
        "age_label": "Edad", "gender_label": "Kasarian", "gender_opt": ["Babae", "Lalaki"],
        "pain_label": "Antas ng Sakit (0 hanggang 10)", "onset_label": "Kailan nagsimula",
        "symptom_label": "Detalye ng Sintomas", "meds_label": "Karamdaman at Iniinom na Gamot",
        "sec3": "3. Resulta ng Screening",
        "btn_run": "🚀 Simulan ang AI Screening", "tts_header": "🔊 Pakinggan ang Boses",
        "dl_btn": "📲 I-download ang Korean SOAP Note para sa doktor",
        "map_btn": "📍 Hanapin ang pinakamalapit na ospital sa Korea"
    },
    "日本語 (일본어)": {
        "code": "ja", "name": "Japanese",
        "title": "🩺 AI健康相談および一次スクリーニング補助ツール",
        "caption": "医療アクセス格差解消のための多言語・音声支援問診システム",
        "warning": "⚠️ **利用規約（補助ツールとしての明記）**\n本サービスは確定診断を下すものではありません。必ず医療機関を受診してください。",
        "sec1": "1. 音声による問診情報入力",
        "voice_guide": "🎙️ マイクボタンを押して、**年齢、性別、痛みの強さ、いつから痛むか、症状**をお話しください。",
        "start_rec": "🔴 録音開始", "stop_rec": "⏹️ 完了",
        "sec2": "2. 認識された問診情報（確認・修正）",
        "age_label": "年代", "gender_label": "性別", "gender_opt": ["女性", "男性"],
        "pain_label": "痛みの強さ (NRS: 0 痛まない ~ 10 激痛)", "onset_label": "症状の発現時期",
        "symptom_label": "症状の詳細", "meds_label": "基礎疾患および服用薬",
        "sec3": "3. スクリーニング結果案内",
        "btn_run": "🚀 AI一次スクリーニング開始", "tts_header": "🔊 音声で結果を聞く",
        "dl_btn": "📲 医師提示用韓国語問診票(SOAP)のダウンロード",
        "map_btn": "📍 韓国の周辺診療機関を探す"
    }
}

# 4. 사이드바 (언어 선택)
with st.sidebar:
    st.header("⚙️ Language / 언어")
    selected_lang_name = st.selectbox("Select Language", list(LANG_PACK.keys()))
    t = LANG_PACK[selected_lang_name]

# 5. 헤더 및 경고 고지 (선택 언어 연동)
st.title(t["title"])
st.caption(t["caption"])
st.warning(t["warning"])

# 환자 프로필 세션 초기화
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {
        "age_group": "20대",
        "gender": "여성",
        "pain_scale": 3,
        "onset_time": "",
        "chronic_meds": "",
        "symptom_text": ""
    }

# 6. 음성으로 나이, 성별, 통증, 증상 일괄 자동 추출
st.subheader(t["sec1"])
st.write(t["voice_guide"])

audio_rec = mic_recorder(
    start_prompt=t["start_rec"],
    stop_prompt=t["stop_rec"],
    key=f"rec_{t['code']}"
)

# 음성 입력 시 Gemini 3.6-flash로 환자 정보 일괄 자동 파싱
if audio_rec is not None and gemini_api_key:
    if "bytes" in audio_rec and len(audio_rec["bytes"]) > 0:
        with st.spinner("Gemini가 음성을 분석하여 나이, 성별, 통증, 증상을 추출 중입니다..."):
            try:
                genai.configure(api_key=gemini_api_key)
                extractor_model = genai.GenerativeModel("gemini-3.6-flash")
                
                audio_part = {
                    "mime_type": "audio/wav",
                    "data": audio_rec["bytes"]
                }
                
                extract_prompt = f"""
                Listen carefully to this patient speaking in {t['name']}.
                Extract the patient's information into a valid JSON object with the following fields:
                - age_group: one of ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"] (infer age if mentioned, default "20대")
                - gender: "여성" (female) or "남성" (male) (infer gender if mentioned, default "여성")
                - pain_scale: integer from 0 to 10 (infer intensity of pain or number mentioned, default 4)
                - onset_time: when symptoms started (in {t['name']})
                - chronic_meds: any mentioned underlying diseases or medications (in {t['name']})
                - symptom_text: full transcription and description of symptoms (in {t['name']})

                Output ONLY valid JSON text without markdown fences or any explanation.
                """
                
                # Quota 방지: 재시도 로직
                max_retries = 3
                response = None
                for attempt in range(max_retries):
                    try:
                        response = extractor_model.generate_content([audio_part, extract_prompt])
                        break
                    except Exception as err:
                        if "429" in str(err) and attempt < max_retries - 1:
                            time.sleep(2)
                        else:
                            raise err

                if response and response.text:
                    clean_json = re.sub(r'```json|```', '', response.text).strip()
                    extracted = json.loads(clean_json)
                    st.session_state.patient_data.update(extracted)
                    st.success("음성 인식 및 환자 정보 자동 입력 완료!")
            except Exception as e:
                st.warning(f"음성 인식 중 안내: {e} (잠시 후 다시 시도하거나 직접 수정해 주세요)")

# 7. 인식된 정보 확인 및 직접 수정
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
        placeholder="e.g. 2 days ago"
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

# 8. AI 건강상담 분석 실행
if st.button(t["btn_run"], type="primary"):
    if not gemini_api_key:
        st.error("API Key is missing in Streamlit Secrets.")
    elif not selected_symptoms:
        st.warning("Please provide symptoms either by speaking or typing.")
    else:
        genai.configure(api_key=gemini_api_key)
        
        system_instruction = f"""
        You are a public healthcare pre-screening AI assistant designed to reduce medical accessibility gaps.
        
        CRITICAL RULES:
        1. [LANGUAGE MANDATE]: The entire consultation, clinical triage, and home-care advice MUST be written strictly in **{t['name']}**.
        2. [EXCEPTION]: At the very end, provide a brief 'Medical Transfer Note (SOAP Note)' written in KOREAN for local healthcare providers in Korea.
        3. [NO DEFINITIVE DIAGNOSIS]: Never declare a final diagnosis. Only suggest possible conditions.
        4. [EMERGENCY TRIAGE]: If life-threatening red flags exist, warn them to call 119/emergency immediately.
        5. [APPROPRIATE CLINIC]: Recommend the most appropriate primary clinic/department to visit in Korea.
        6. [PUBLIC GUIDELINES]: Cite credible guidelines such as KDCA or HIRA.
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
        
        with st.spinner(f"Analyzing in {t['name']}..."):
            try:
                # gemini-3.6-flash 모델 호출
                model = genai.GenerativeModel(
                    model_name="gemini-3.6-flash",
                    system_instruction=system_instruction
                )
                
                # Quota 429 방지 재시도
                max_retries = 3
                response = None
                for attempt in range(max_retries):
                    try:
                        response = model.generate_content(
                            user_prompt,
                            generation_config=genai.types.GenerationConfig(temperature=0.1)
                        )
                        break
                    except Exception as err:
                        if "429" in str(err) and attempt < max_retries - 1:
                            time.sleep(2)
                        else:
                            raise err
                
                result_text = response.text
                st.success("Analysis Complete.")
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
                    st.info("Audio narration is being initialized.")
                
                # 병원 진료 연계 버튼군
                st.markdown("---")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    # 국립중앙의료원 응급의료포털 (E-Gen) 실시간 병의원/약국 지도 연동
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
                st.error(f"Error: {e}")
