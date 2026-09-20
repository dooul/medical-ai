import streamlit as st
import google.generativeai as genai
from streamlit_mic_recorder import mic_recorder
from gtts import gTTS
import tempfile
import json
import re

# 1. 페이지 설정
st.set_page_config(page_title="AI 건강상담 및 1차 스크리닝 보조 도구", layout="centered")

# 2. Secrets API 키 자동 로드
if "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_api_key = ""

# 3. 16개 다국어 UI 사전 및 gTTS 매핑
LANG_PACK = {
    "한국어 (Korean)": {
        "code": "ko", "name": "Korean",
        "title": "🩺 AI 건강상담 및 1차 스크리닝 보조 도구",
        "caption": "의료 접근성 격차 해소를 위한 다국어·음성 지원 문진 및 적정 진료과 안내 시스템",
        "warning": "⚠️ **이용 전 필독 (보조 도구 역할 명시)**\n본 서비스는 확정 진단을 내리지 않는 1차 스크리닝 보조 도구입니다. 실제 진료는 반드시 전문 의료진을 통해 진행되어야 합니다.",
        "sec1": "1. 기본 문진 정보", "sec2": "2. 증상 호소 (음성 또는 텍스트)", "sec3": "3. 1차 스크리닝 결과 안내",
        "voice_guide": "🎙️ 아래 마이크 버튼을 누르고 편하게 말씀해 주세요.",
        "start_rec": "🔴 마이크 켜기 (녹음 시작)", "stop_rec": "⏹️ 녹음 완료",
        "age_label": "연령대", "gender_label": "성별", "gender_opt": ["여성", "남성"],
        "pain_label": "통증/불편도 (NRS: 0 무통 ~ 10 극심한 통증)", "onset_label": "증상 발현 시점",
        "symptom_label": "증상 상세 설명", "meds_label": "기저질환 및 복용 약물",
        "btn_run": "🚀 AI 1차 스크리닝 시작", "tts_header": "🔊 음성으로 결과 듣기",
        "dl_btn": "📲 의료진 전달용 한국어 문진표(SOAP) 다운로드"
    },
    "English (영어)": {
        "code": "en", "name": "English",
        "title": "🩺 AI Health Consultation & Primary Screening Tool",
        "caption": "Multilingual & Voice-supported Pre-screening System for Reducing Medical Accessibility Gaps",
        "warning": "⚠️ **Notice (Auxiliary Tool Only)**\nThis service is a primary pre-screening auxiliary tool and does not provide a definitive diagnosis. Always consult a qualified medical professional.",
        "sec1": "1. Basic Patient Information", "sec2": "2. Symptoms (Voice or Text)", "sec3": "3. Screening Assessment Results",
        "voice_guide": "🎙️ Press the microphone button below and speak in your preferred language.",
        "start_rec": "🔴 Start Recording", "stop_rec": "⏹️ Stop Recording",
        "age_label": "Age Group", "gender_label": "Gender", "gender_opt": ["Female", "Male"],
        "pain_label": "Pain Scale (NRS: 0 No pain ~ 10 Severe pain)", "onset_label": "Symptom Onset Time",
        "symptom_label": "Detailed Symptoms", "meds_label": "Underlying Conditions & Medications",
        "btn_run": "🚀 Start AI Pre-screening", "tts_header": "🔊 Listen to Results (Audio)",
        "dl_btn": "📲 Download Korean SOAP Note for Local Doctors"
    },
    "Tiếng Việt (베트남어)": {
        "code": "vi", "name": "Vietnamese",
        "title": "🩺 Công cụ Hỗ trợ Tư vấn Sức khỏe & Sàng lọc Ban đầu AI",
        "caption": "Hệ thống hỗ trợ giọng nói & đa ngôn ngữ giúp thu hẹp khoảng cách tiếp cận y tế",
        "warning": "⚠️ **Lưu ý quan trọng**\nDịch vụ này chỉ là công cụ hỗ trợ sàng lọc ban đầu và không thay thế chẩn đoán y tế chính thức. Hãy luôn thăm khám bác sĩ chuyên khoa.",
        "sec1": "1. Thông tin bệnh nhân cơ bản", "sec2": "2. Triệu chứng (Giọng nói hoặc Văn bản)", "sec3": "3. Kết quả sàng lọc ban đầu",
        "voice_guide": "🎙️ Nhấn nút micro bên dưới và nói bằng tiếng mẹ đẻ của bạn.",
        "start_rec": "🔴 Bắt đầu ghi âm", "stop_rec": "⏹️ Hoàn tất",
        "age_label": "Độ tuổi", "gender_label": "Giới tính", "gender_opt": ["Nữ", "Nam"],
        "pain_label": "Mức độ đau (NRS: 0 Không đau ~ 10 Rất đau)", "onset_label": "Thời điểm bắt đầu triệu chứng",
        "symptom_label": "Mô tả chi tiết triệu chứng", "meds_label": "Bệnh lý nền & Thuốc đang dùng",
        "btn_run": "🚀 Bắt đầu sàng lọc AI", "tts_header": "🔊 Nghe kết quả bằng giọng nói",
        "dl_btn": "📲 Tải phiếu khám tiếng Hàn (SOAP) nộp cho bác sĩ"
    },
    "中文 (중국어 간체)": {
        "code": "zh-CN", "name": "Simplified Chinese",
        "title": "🩺 AI健康咨询与初筛辅助工具",
        "caption": "支持多语言与语音的预问诊系统，致力于缩小医疗可及性差距",
        "warning": "⚠️ **使用须知（辅助工具声明）**\n本服务为初筛辅助工具，不提供最终诊断。如需确诊与治疗，请务必前往正规医疗机构就诊。",
        "sec1": "1. 基本问诊信息", "sec2": "2. 症状描述（语音或文字）", "sec3": "3. 初步评估结果",
        "voice_guide": "🎙️ 请点击下方麦克风按钮并直接用母语陈述症状。",
        "start_rec": "🔴 开启麦克风（开始录音）", "stop_rec": "⏹️ 录音完成",
        "age_label": "年龄段", "gender_label": "性别", "gender_opt": ["女性", "男性"],
        "pain_label": "疼痛等级（NRS: 0无痛 ~ 10极度剧痛）", "onset_label": "发病时间",
        "symptom_label": "症状详细描述", "meds_label": "既往病史及目前服药",
        "btn_run": "🚀 开始AI初步评估", "tts_header": "🔊 语音朗读评估结果",
        "dl_btn": "📲 下载供韩国医生参阅的韩语SOAP问诊单"
    },
    "Русский (러시아어)": {
        "code": "ru", "name": "Russian",
        "title": "🩺 AI-инструмент предварительного скрининга здоровья",
        "caption": "Многоязычная система поддержки для устранения барьеров в доступности медицины",
        "warning": "⚠️ **Важное уведомление**\nДанная система является вспомогательным инструментом и не ставит окончательный диагноз. Обратитесь к врачу.",
        "sec1": "1. Основные данные пациента", "sec2": "2. Симптомы (Голос или текст)", "sec3": "3. Результаты предварительной оценки",
        "voice_guide": "🎙️ Нажмите кнопку микрофона ниже и опишите симптомы голосом.",
        "start_rec": "🔴 Начать запись", "stop_rec": "⏹️ Завершить",
        "age_label": "Возраст", "gender_label": "Пол", "gender_opt": ["Женский", "Мужской"],
        "pain_label": "Шкала боли (0 - нет боли ~ 10 - нестерпимая боль)", "onset_label": "Когда начались симптомы",
        "symptom_label": "Подробное описание симптомов", "meds_label": "Хронические заболевания и лекарства",
        "btn_run": "🚀 Начать первичный скрининг AI", "tts_header": "🔊 Прослушать результат голосом",
        "dl_btn": "📲 Скачать корейскую форму SOAP для врача"
    },
    "O'zbekcha (우즈베크어)": {
        "code": "uz", "name": "Uzbek",
        "title": "🩺 AI Sog'liqni Saqlash va Dastlabki Skrining Yordamchisi",
        "caption": "Tibbiy yordamdan foydalanish imkoniyatini oshirish uchun ko'p tilli tizim",
        "warning": "⚠️ **Muhim eslatma**\nBu xizmat yordamchi vosita bo'lib, yakuniy tashxis qo'ymaydi. Shifokor bilan maslahatlashing.",
        "sec1": "1. Asosiy ma'lumotlar", "sec2": "2. Belgilar (Ovoz yoki Matn)", "sec3": "3. Skrining xulosasi",
        "voice_guide": "🎙️ Mikrofon tugmasini bosing va o'z tilingizda gapiring.",
        "start_rec": "🔴 Ovoz yozish", "stop_rec": "⏹️ Tugatish",
        "age_label": "Yosh guruhi", "gender_label": "Jinsi", "gender_opt": ["Ayol", "Erkak"],
        "pain_label": "Og'riq darajasi (0 dan 10 gacha)", "onset_label": "Qachon boshlangan",
        "symptom_label": "Belgilar tavsifi", "meds_label": "Surunkali kasalliklar va dorilar",
        "btn_run": "🚀 Skriningni boshlash", "tts_header": "🔊 Ovozli eshitish",
        "dl_btn": "📲 Shifokor uchun koreyscha SOAP varaqasini yuklab olish"
    },
    "Tagalog (필리핀어)": {
        "code": "tl", "name": "Tagalog",
        "title": "🩺 AI Konsultasyon sa Kalusugan at Pangunahing Screening",
        "caption": "Multilingual na sistema para mapabuti ang serbisyong medikal",
        "warning": "⚠️ **Mahalagang Paunawa**\nIto ay gabay lamang at hindi pinal na diagnosis. Kumonsulta sa doktor.",
        "sec1": "1. Impormasyon ng Pasyente", "sec2": "2. Mga Sintomas (Boses o Teksto)", "sec3": "3. Resulta ng Screening",
        "voice_guide": "🎙️ Pindutin ang mikropono at sabihin ang nararamdaman.",
        "start_rec": "🔴 Simulan ang Voice", "stop_rec": "⏹️ Tapusin",
        "age_label": "Edad", "gender_label": "Kasarian", "gender_opt": ["Babae", "Lalaki"],
        "pain_label": "Antas ng Sakit (0 hanggang 10)", "onset_label": "Kailan nagsimula",
        "symptom_label": "Detalye ng Sintomas", "meds_label": "Karamdaman at Iniinom na Gamot",
        "btn_run": "🚀 Simulan ang AI Screening", "tts_header": "🔊 Pakinggan ang Boses",
        "dl_btn": "📲 I-download ang Korean SOAP Note para sa doktor"
    },
    "日本語 (일본어)": {
        "code": "ja", "name": "Japanese",
        "title": "🩺 AI健康相談および一次スクリーニング補助ツール",
        "caption": "医療アクセス格差解消のための多言語・音声支援問診システム",
        "warning": "⚠️ **利用規約（補助ツールとしての明記）**\n本サービスは確定診断を下すものではありません。必ず医療機関を受診してください。",
        "sec1": "1. 基本問診情報", "sec2": "2. 症状の訴え（音声またはテキスト）", "sec3": "3. スクリーニング結果案内",
        "voice_guide": "🎙️ マイクボタンを押して、症状をお話しください。",
        "start_rec": "🔴 録音開始", "stop_rec": "⏹️ 完了",
        "age_label": "年代", "gender_label": "性別", "gender_opt": ["女性", "男性"],
        "pain_label": "痛みの強さ (NRS: 0 痛まない ~ 10 激痛)", "onset_label": "症状の発現時期",
        "symptom_label": "症状の詳細", "meds_label": "基礎疾患および服用薬",
        "btn_run": "🚀 AI一次スクリーニング開始", "tts_header": "🔊 音声で結果を聞く",
        "dl_btn": "📲 医師提示用韓国語問診票(SOAP)のダウンロード"
    }
}

# 4. 사이드바 (언어 선택)
with st.sidebar:
    st.header("⚙️ Language / 언어")
    selected_lang_name = st.selectbox(
        "Select Language",
        list(LANG_PACK.keys())
    )
    t = LANG_PACK[selected_lang_name]

# 5. 메인 헤더 및 고지문 (선택된 언어로 즉각 변경)
st.title(t["title"])
st.caption(t["caption"])
st.warning(t["warning"])

# 세션 상태
if "symptom_text_val" not in st.session_state:
    st.session_state.symptom_text_val = ""

# 6. 기본 문진 정보
st.subheader(t["sec1"])
col1, col2 = st.columns(2)
with col1:
    age_group = st.selectbox(t["age_label"], ["10s", "20s", "30s", "40s", "50s", "60s", "70+"])
    gender = st.radio(t["gender_label"], t["gender_opt"], horizontal=True)
with col2:
    pain_scale = st.slider(t["pain_label"], 0, 10, 3)
    onset_time = st.text_input(t["onset_label"], placeholder="e.g. 2 days ago")

# 7. 증상 입력 (음성 및 텍스트)
st.subheader(t["sec2"])
st.write(t["voice_guide"])

audio_rec = mic_recorder(
    start_prompt=t["start_rec"],
    stop_prompt=t["stop_rec"],
    key=f"rec_{t['code']}"
)

# 음성 인식 처리 (선택된 언어로 트랜스크립션 강제)
if audio_rec is not None and gemini_api_key:
    if "bytes" in audio_rec and len(audio_rec["bytes"]) > 0:
        with st.spinner("Processing speech..."):
            try:
                genai.configure(api_key=gemini_api_key)
                stt_model = genai.GenerativeModel("gemini-3.6-flash")
                audio_part = {"mime_type": "audio/wav", "data": audio_rec["bytes"]}
                prompt = f"Accurately transcribe the spoken words in {t['name']}. Output ONLY the transcribed text without quotes or explanations."
                response = stt_model.generate_content([audio_part, prompt])
                if response.text:
                    st.session_state.symptom_text_val = response.text.strip()
                    st.success(f"Recognized: \"{st.session_state.symptom_text_val}\"")
            except Exception as e:
                st.warning(f"Voice Recognition Error: {e}")

symptom_input = st.text_area(
    t["symptom_label"],
    value=st.session_state.symptom_text_val,
    height=90
)
chronic_meds = st.text_input(t["meds_label"])

# 8. 상담 실행
if st.button(t["btn_run"], type="primary"):
    if not gemini_api_key:
        st.error("API Key is missing in Streamlit Secrets.")
    elif not symptom_input:
        st.warning("Please provide symptoms either by speaking or typing.")
    else:
        genai.configure(api_key=gemini_api_key)
        
        # 시스템 프롬프트: 사용자가 선택한 언어로 본문 출력을 100% 강제
        system_instruction = f"""
        You are a public healthcare pre-screening AI assistant.
        
        CRITICAL MULTILINGUAL MANDATE:
        - The user has selected the language: **{t['name']}**.
        - You MUST write the ENTIRE medical consultation, explanations, red flag warnings, triage, and recommendations strictly in **{t['name']}**.
        - DO NOT write in Korean for the main consultation sections.
        - EXCEPTION: At the very end, provide a section titled "### 🏥 의료진 전달용 사전 문진표 (SOAP Note for Local Korean Doctors)" written in KOREAN so local healthcare providers in Korea can read it immediately.
        
        CLINICAL PROTOCOL:
        1. Never provide a final diagnosis. Only suggest possible conditions.
        2. Triage urgency (Emergency vs Routine outpatient clinic).
        3. Recommend clinical specialties to visit in Korea (e.g., Internal Medicine, ENT).
        4. Reference credible guidelines like KDCA or HIRA.
        """
        
        user_prompt = f"""
        Respond completely in {t['name']}.
        
        Patient Profile:
        - Language: {t['name']}
        - Age / Gender: {age_group} / {gender}
        - Pain Level: {pain_scale} / 10
        - Onset: {onset_time}
        - Underlying Illness / Meds: {chronic_meds}
        - Symptoms: {symptom_input}
        """
        
        with st.spinner(f"Analyzing in {t['name']}..."):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-3.6-flash",
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(temperature=0.1)
                )
                
                result_text = response.text
                st.success("Analysis Complete.")
                st.markdown("---")
                
                # 결과 출력
                st.subheader(t["sec3"])
                st.markdown(result_text)
                
                # TTS 음성 재생 (해당 언어 음성 출력)
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
                
                # 다운로드 버튼
                st.markdown("---")
                st.download_button(
                    label=t["dl_btn"],
                    data=result_text,
                    file_name="medical_soap_note.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error: {e}")
