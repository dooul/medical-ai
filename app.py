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

# 3. 16개 다국어 UI 사전 (연령대 목록 및 플레이스홀더 예시 완벽 다국어화)
LANG_PACK = {
    "한국어 (Korean)": {
        "code": "ko", "name": "Korean",
        "title": "🩺 AI 건강상담 및 1차 스크리닝 보조 도구",
        "caption": "의료 접근성 격차 해소를 위한 다국어·음성 지원 문진 및 적정 진료과 안내 시스템",
        "warning": "⚠️ **이용 전 필독 (보조 도구 역할 명시)**\n본 서비스는 질환의 최종 진단이나 처방을 내리지 않는 1차 스크리닝 보조 도구입니다. 실제 진료와 치료는 반드시 전문 의료진과의 상담을 통해 진행되어야 합니다.",
        "sec1": "1. 음성으로 환자 정보 말하기 (스마트 음성 문진)",
        "voice_guide": "🎙️ 아래 마이크 버튼을 누르고 **나이, 성별, 통증 정도, 발병 시점, 증상**을 편하게 모국어로 말씀해 주세요.",
        "start_rec": "🔴 마이크 켜기 (녹음 시작)", "stop_rec": "⏹️ 녹음 완료",
        "sec2": "2. 인식된 문진 정보 (확인 및 수정)",
        "age_label": "연령대", "age_opts": ["10대", "20대", "30대", "40대", "50대", "60대", "70대 이상"],
        "gender_label": "성별", "gender_opt": ["여성", "남성"],
        "pain_label": "통증/불편도 (NRS: 0 무통 ~ 10 극심한 통증)",
        "onset_label": "증상 발현 시점", "onset_ph": "예: 어젯밤부터, 2일 전부터",
        "symptom_label": "증상 상세 설명", "symptom_ph": "예: 오른쪽 아랫배가 찌르듯이 아프고 미열이 납니다.",
        "meds_label": "기저질환 및 복용 약물", "meds_ph": "예: 혈압약 복용 중, 타이레놀",
        "sec3": "3. 1차 스크리닝 결과 안내",
        "btn_run": "🚀 AI 1차 스크리닝 시작", "tts_header": "🔊 모국어 음성으로 결과 듣기",
        "dl_btn": "📲 의료진 전달용 한국어 문진표(SOAP) 다운로드",
        "map_btn": "📍 내 주변 야간·휴일 진료기관 찾기 (응급의료포털)"
    },
    "English (영어)": {
        "code": "en", "name": "English",
        "title": "🩺 AI Health Consultation & Primary Screening Tool",
        "caption": "Multilingual & Voice-supported Pre-screening System for Reducing Medical Accessibility Gaps",
        "warning": "⚠️ **Notice (Auxiliary Tool Only)**\nThis service is a primary pre-screening auxiliary tool and does not provide a definitive diagnosis. Always consult a qualified medical professional.",
        "sec1": "1. Voice Patient Registration (Smart Audio Triage)",
        "voice_guide": "🎙️ Press the mic below and describe your **age, gender, pain level, onset time, and symptoms** in English.",
        "start_rec": "🔴 Start Recording", "stop_rec": "⏹️ Stop Recording",
        "sec2": "2. Extracted Patient Profile (Review & Edit)",
        "age_label": "Age Group", "age_opts": ["10s", "20s", "30s", "40s", "50s", "60s", "70s or older"],
        "gender_label": "Gender", "gender_opt": ["Female", "Male"],
        "pain_label": "Pain Scale (NRS: 0 No pain ~ 10 Severe pain)",
        "onset_label": "Symptom Onset Time", "onset_ph": "e.g., Since last night, 2 days ago",
        "symptom_label": "Detailed Symptoms", "symptom_ph": "e.g., Sharp pain in my lower right abdomen and mild fever.",
        "meds_label": "Underlying Conditions & Medications", "meds_ph": "e.g., Taking blood pressure pills, Tylenol",
        "sec3": "3. Screening Assessment Results",
        "btn_run": "🚀 Start AI Pre-screening", "tts_header": "🔊 Listen to Results (Audio)",
        "dl_btn": "📲 Download Korean SOAP Note for Local Doctors",
        "map_btn": "📍 Find Nearby Open Hospitals / Clinics in Korea"
    },
    "Tiếng Việt (베트남어)": {
        "code": "vi", "name": "Vietnamese",
        "title": "🩺 Công cụ Hỗ trợ Tư vấn Sức khỏe & Sàng lọc Ban đầu AI",
        "caption": "Hệ thống hỗ trợ giọng nói & đa ngôn ngữ giúp thu hẹp khoảng cách tiếp cận y tế",
        "warning": "⚠️ **Lưu ý quan trọng**\nDịch vụ này chỉ là công cụ hỗ trợ sàng lọc ban đầu và không thay thế chẩn đoán y tế chính thức.",
        "sec1": "1. Khai báo thông tin bằng giọng nói",
        "voice_guide": "🎙️ Bấm nút micro và nói về **tuổi, giới tính, mức độ đau, thời điểm bắt đầu và triệu chứng**.",
        "start_rec": "🔴 Bắt đầu ghi âm", "stop_rec": "⏹️ Hoàn tất",
        "sec2": "2. Thông tin bệnh nhân đã nhận diện",
        "age_label": "Độ tuổi", "age_opts": ["10-19 tuổi", "20-29 tuổi", "30-39 tuổi", "40-49 tuổi", "50-59 tuổi", "60-69 tuổi", "70 tuổi trở lên"],
        "gender_label": "Giới tính", "gender_opt": ["Nữ", "Nam"],
        "pain_label": "Mức độ đau (NRS: 0 Không đau ~ 10 Rất đau)",
        "onset_label": "Thời điểm bắt đầu", "onset_ph": "Ví dụ: Từ tối qua, 2 ngày trước",
        "symptom_label": "Mô tả chi tiết triệu chứng", "symptom_ph": "Ví dụ: Đau nhói bụng dưới bên phải và sốt nhẹ.",
        "meds_label": "Bệnh lý nền & Thuốc đang dùng", "meds_ph": "Ví dụ: Thuốc huyết áp, Panadol",
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
        "age_label": "年龄段", "age_opts": ["10多岁", "20多岁", "30多岁", "40多岁", "50多岁", "60多岁", "70岁以上"],
        "gender_label": "性别", "gender_opt": ["女性", "男性"],
        "pain_label": "疼痛等级（NRS: 0无痛 ~ 10极度剧痛）",
        "onset_label": "发病时间", "onset_ph": "例如：昨晚开始、两天前",
        "symptom_label": "症状详细描述", "symptom_ph": "例如：右下腹剧烈阵痛，伴有低烧。",
        "meds_label": "既往病史及目前服药", "meds_ph": "例如：正在服用降压药、泰诺",
        "sec3": "3. 初步评估结果",
        "btn_run": "🚀 开始AI初步评估", "tts_header": "🔊 语音朗读评估结果",
        "dl_btn": "📲 下载供韩国医生参阅的韩语SOAP问诊单",
        "map_btn": "📍 查找韩国周边正在接诊的医疗机构"
    },
    "Русский (러시아어)": {
        "code": "ru", "name": "Russian",
        "title": "🩺 AI-инструмент предварительного скрининга здоровья",
        "caption": "Многоязычная система поддержки для устранения барьеров в доступности медицины",
        "warning": "⚠️ **Важное уведомление**\nДанная система является вспомогательным инструментом и не ставит окончательный диагноз.",
        "sec1": "1. Голосовой ввод данных пациента",
        "voice_guide": "🎙️ Нажмите на микрофон и назовите свой **возраст, пол, уровень боли, когда началось и симптомы**.",
        "start_rec": "🔴 Начать запись", "stop_rec": "⏹️ Завершить",
        "sec2": "2. Распознанные данные (Проверка и редактирование)",
        "age_label": "Возраст", "age_opts": ["10-19 лет", "20-29 лет", "30-39 лет", "40-49 лет", "50-59 лет", "60-69 лет", "70+ лет"],
        "gender_label": "Пол", "gender_opt": ["Женский", "Мужской"],
        "pain_label": "Шкала боли (0 - нет боли ~ 10 - нестерпимая боль)",
        "onset_label": "Когда началось", "onset_ph": "например: со вчерашнего вечера, 2 дня назад",
        "symptom_label": "Подробное описание симптомов", "symptom_ph": "например: колющая боль внизу живота справа, температура.",
        "meds_label": "Хронические заболевания и лекарства", "meds_ph": "например: таблетки от давления",
        "sec3": "3. Результаты предварительной оценки",
        "btn_run": "🚀 Начать первичный скрининг AI", "tts_header": "🔊 Прослушать результат голосом",
        "dl_btn": "📲 Скачать корейскую форму SOAP для врача",
        "map_btn": "📍 Найти ближайшие клиники и больницы в Корее"
    },
    "O'zbekcha (우즈베크어)": {
        "code": "uz", "name": "Uzbek",
        "title": "🩺 AI Sog'liqni Saqlash va Dastlabki Skrining Yordamchisi",
        "caption": "Tibbiy yordamdan foydalanish imkoniyatini oshirish uchun ko'p tilli tizim",
        "warning": "⚠️ **Muhim eslatma**\nBu xizmat yordamchi vosita bo'lib, yakuniy tashxis qo'ymaydi.",
        "sec1": "1. Ovozli ma'lumotlarni kiritish",
        "voice_guide": "🎙️ Mikrofonni yoqing va **yoshingiz, jinsingiz, og'riq darajasi va alomatlarni** ayting.",
        "start_rec": "🔴 Ovoz yozish", "stop_rec": "⏹️ Tugatish",
        "sec2": "2. Aniqlangan ma'lumotlar",
        "age_label": "Yosh guruhi", "age_opts": ["10-19 yosh", "20-29 yosh", "30-39 yosh", "40-49 yosh", "50-59 yosh", "60-69 yosh", "70 yoshdan katta"],
        "gender_label": "Jinsi", "gender_opt": ["Ayol", "Erkak"],
        "pain_label": "Og'riq darajasi (0 dan 10 gacha)",
        "onset_label": "Qachon boshlangan", "onset_ph": "Masalan: kecha kechqurundan, 2 kun oldin",
        "symptom_label": "Belgilar tavsifi", "symptom_ph": "Masalan: qorinning o'ng pastki qismida sanchiq og'riq.",
        "meds_label": "Surunkali kasalliklar va dorilar", "meds_ph": "Masalan: qon bosimi dorilari",
        "sec3": "3. Skrining xulosasi",
        "btn_run": "🚀 Skriningni boshlash", "tts_header": "🔊 Ovozli eshitish",
        "dl_btn": "📲 Shifokor uchun koreyscha SOAP varaqasini yuklab olish",
        "map_btn": "📍 Koreyadagi yaqin shifoxonani topish"
    },
    "Tagalog / Filipino (필리핀어)": {
        "code": "tl", "name": "Tagalog",
        "title": "🩺 AI Konsultasyon sa Kalusugan at Pangunahing Screening",
        "caption": "Multilingual na sistema para mapabuti ang serbisyong medikal",
        "warning": "⚠️ **Mahalagang Paunawa**\nIto ay gabay lamang at hindi pinal na diagnosis.",
        "sec1": "1. Voice Triage (Sabihin ang Impormasyon)",
        "voice_guide": "🎙️ Pindutin ang mikropono at sabihin ang iyong **edad, kasarian, antas ng sakit, at mga sintomas**.",
        "start_rec": "🔴 Simulan ang Voice", "stop_rec": "⏹️ Tapusin",
        "sec2": "2. Nakuhang Impormasyon ng Pasyente",
        "age_label": "Edad", "age_opts": ["10-19 anyos", "20-29 anyos", "30-39 anyos", "40-49 anyos", "50-59 anyos", "60-69 anyos", "70 anyos pataas"],
        "gender_label": "Kasarian", "gender_opt": ["Babae", "Lalaki"],
        "pain_label": "Antas ng Sakit (0 hanggang 10)",
        "onset_label": "Kailan nagsimula", "onset_ph": "hal.: Kagabi pa, 2 araw na ang nakalipas",
        "symptom_label": "Detalye ng Sintomas", "symptom_ph": "hal.: Masakit ang kanang bahagi ng tiyan at may lagnat.",
        "meds_label": "Karamdaman at Iniinom na Gamot", "meds_ph": "hal.: Gamot sa altapresyon, Paracetamol",
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
        "age_label": "年代", "age_opts": ["10代", "20代", "30代", "40代", "50代", "60代", "70代以上"],
        "gender_label": "性別", "gender_opt": ["女性", "男性"],
        "pain_label": "痛みの強さ (NRS: 0 痛まない ~ 10 激痛)",
        "onset_label": "症状の発現時期", "onset_ph": "例：昨夜から、2日前から",
        "symptom_label": "症状の詳細", "symptom_ph": "例：右下腹部がズキズキ痛み、微熱があります。",
        "meds_label": "基礎疾患および服用薬", "meds_ph": "例：降圧薬を服用中、ロキソニン",
        "sec3": "3. スクリーニング結果案内",
        "btn_run": "🚀 AI一次スクリーニング開始", "tts_header": "🔊 音声で結果を聞く",
        "dl_btn": "📲 医師提示用韓国語問診票(SOAP)のダウンロード",
        "map_btn": "📍 韓国の周辺診療機関を探す"
    },
    "ไทย (태국어)": {
        "code": "th", "name": "Thai",
        "title": "🩺 เครื่องมือ AI คัดกรองและให้คำปรึกษาด้านสุขภาพเบื้องต้น",
        "caption": "ระบบคัดกรองเบื้องต้นหลายภาษาและรองรับเสียงเพื่อลดช่องว่างในการเข้าถึงการรักษาพยาบาล",
        "warning": "⚠️ **ข้อควรทราบ**\nบริการนี้เป็นเพียงเครื่องมือช่วยเหลือในการคัดกรองเบื้องต้น ไม่ใช่การวินิจฉัยโรคขั้นสุดท้าย",
        "sec1": "1. ระบุข้อมูลด้วยเสียง (Smart Voice)",
        "voice_guide": "🎙️ กดปุ่มไมโครโฟนแล้วแจ้ง **อายุ, เพศ, ระดับความเจ็บปวด, เวลาที่เริ่มเป็น และอาการ**",
        "start_rec": "🔴 เริ่มบันทึกเสียง", "stop_rec": "⏹️ สิ้นสุด",
        "sec2": "2. ข้อมูลที่ระบุได้ (ตรวจสอบและแก้ไข)",
        "age_label": "กลุ่มอายุ", "age_opts": ["10-19 ปี", "20-29 ปี", "30-39 ปี", "40-49 ปี", "50-59 ปี", "60-69 ปี", "70 ปีขึ้นไป"],
        "gender_label": "เพศ", "gender_opt": ["หญิง", "ชาย"],
        "pain_label": "ระดับความเจ็บปวด (0 ไม่ปวด ~ 10 ปวดมาก)",
        "onset_label": "เวลาที่เริ่มมีอาการ", "onset_ph": "เช่น: ตั้งแต่เมื่อคืน, 2 วันก่อน",
        "symptom_label": "รายละเอียดอาการ", "symptom_ph": "เช่น: ปวดท้องน้อยด้านขวาแปลบๆ และมีไข้ต่ำๆ",
        "meds_label": "โรคประจำตัวและยาที่รับประทาน", "meds_ph": "เช่น: ยาลดความดันโลหิต, พาราเซตามอล",
        "sec3": "3. ผลการคัดกรองเบื้องต้น",
        "btn_run": "🚀 เริ่มการคัดกรอง AI", "tts_header": "🔊 ฟังผลการประเมินด้วยเสียง",
        "dl_btn": "📲 ดาวน์โหลดแบบสอบถามภาษาเกาหลี (SOAP) สำหรับแพทย์",
        "map_btn": "📍 ค้นหาโรงพยาบาล/คลินิกใกล้เคียงในเกาหลี"
    },
    "ភាសាខ្មែរ (캄보디아어)": {
        "code": "km", "name": "Khmer",
        "title": "🩺 ឧបករណ៍ជំនួយពិគ្រោះយោបល់សុខភាព AI",
        "caption": "ប្រព័ន្ធពិនិត្យបឋមពហុភាសា និងសំឡេង ដើម្បីកាត់បន្ថយគម្លាតនៃការទទួលបានសេវាសុខាភិបាល",
        "warning": "⚠️ **សេចក្តីជូនដំណឹងសំខាន់**\nសេវាកម្មនេះគ្រាន់តែជាឧបករណ៍ជំនួយពិនិត្យបឋមប៉ុណ្ណោះ មិនមែនជាការធ្វើរោគវិនិច្ឆ័យចុងក្រោយទេ។",
        "sec1": "1. បញ្ចូលព័ត៌មានតាមរយៈសំឡេង",
        "voice_guide": "🎙️ ចុចមីក្រូហ្វូន ហើយប្រាប់ពី **អាយុ ភេទ កម្រិតការឈឺចាប់ ពេលវេលា និងរោគសញ្ញា**។",
        "start_rec": "🔴 ចាប់ផ្តើមថត", "stop_rec": "⏹️ បញ្ចប់",
        "sec2": "2. ព័ត៌មានដែលបានទទួលស្គាល់",
        "age_label": "ក្រុមអាយុ", "age_opts": ["10-19 ឆ្នាំ", "20-29 ឆ្នាំ", "30-39 ឆ្នាំ", "40-49 ឆ្នាំ", "50-59 ឆ្នាំ", "60-69 ឆ្នាំ", "70 ឆ្នាំឡើង"],
        "gender_label": "ភេទ", "gender_opt": ["ស្រី", "ប្រុស"],
        "pain_label": "កម្រិតឈឺចាប់ (0 គ្មានការឈឺចាប់ ~ 10 ឈឺខ្លាំង)",
        "onset_label": "ពេលចាប់ផ្តើម", "onset_ph": "ឧទាហរណ៍៖ តាំងពីយប់មិញ, ២ថ្ងៃមុន",
        "symptom_label": "រោគសញ្ញាលម្អិត", "symptom_ph": "ឧទាហរណ៍៖ ឈឺចុកចាប់នៅពោះផ្នែកខាងស្តាំក្រោម និងក្តៅខ្លួនបន្តិច។",
        "meds_label": "ជំងឺប្រចាំកាយ និងថ្នាំ", "meds_ph": "ឧទាហរណ៍៖ ថ្នាំលើសឈាម",
        "sec3": "3. លទ្ធផលពិនិត្យបឋម",
        "btn_run": "🚀 ចាប់ផ្តើមពិនិត្យ AI", "tts_header": "🔊 ស្តាប់លទ្ធផលជាសំឡេង",
        "dl_btn": "📲 ទាញយកទម្រង់ SOAP ជាភាសាកូរ៉េសម្រាប់វេជ្ជបណ្ឌិត",
        "map_btn": "📍 ស្វែងរកមន្ទីរពេទ្យនៅក្បែរក្នុងប្រទេសកូរ៉េ"
    },
    "Монгол хэл (몽골어)": {
        "code": "mn", "name": "Mongolian",
        "title": "🩺 AI Эрүүл мэндийн анхан шатны зөвлөгөө, тандалтын хэрэгсэл",
        "caption": "Эрүүл мэндийн хүртээмжийн ялгааг арилгах олон хэл, дуут систем",
        "warning": "⚠️ **Анхааруулга**\nЭнэхүү үйлчилгээ нь зөвхөн анхан шатны туслах хэрэгсэл бөгөөд эцсийн онош биш юм.",
        "sec1": "1. Дуут мэдээлэл оруулах",
        "voice_guide": "🎙️ Микрофон дээр дарж **нас, хүйс, өвдөлтийн зэрэг, эхэлсэн хугацаа, шинж тэмдгээ** ярина уу.",
        "start_rec": "🔴 Бичиж эхлэх", "stop_rec": "⏹️ Дуусгах",
        "sec2": "2. Бүртгэгдсэн мэдээлэл",
        "age_label": "Насны бүлэг", "age_opts": ["10-19 нас", "20-29 нас", "30-39 нас", "40-49 нас", "50-59 нас", "60-69 нас", "70+ нас"],
        "gender_label": "Хүйс", "gender_opt": ["Эмэгтэй", "Эрэгтэй"],
        "pain_label": "Өвдөлтийн түвшин (0-10)",
        "onset_label": "Шинж тэмдэг эхэлсэн хугацаа", "onset_ph": "Жишээ нь: өчигдөр оройноос, 2 хоногийн өмнө",
        "symptom_label": "Шинж тэмдгийн дэлгэрэнгүй", "symptom_ph": "Жишээ нь: баруун доод хэвлийгээр хатгаж өвдөж, бага зэрэг халуурч байна.",
        "meds_label": "Суурь өвчин болон эм", "meds_ph": "Жишээ нь: даралтын эм ууж байгаа",
        "sec3": "3. Анхан шатны үр дүн",
        "btn_run": "🚀 AI тандалт эхлүүлэх", "tts_header": "🔊 Үр дүнг дуугаар сонсох",
        "dl_btn": "📲 Солонгос эмчид өгөх SOAP маягт татах",
        "map_btn": "📍 Солонгос дахь ойролцоох эмнэлэг хайх"
    },
    "नेपाली (네팔어)": {
        "code": "ne", "name": "Nepali",
        "title": "🩺 AI स्वास्थ्य परामर्श तथा प्रारम्भिक जाँच उपकरण",
        "caption": "स्वास्थ्य सेवा पहुँचको खाडल कम गर्न बहुभाषी तथा आवाज समर्थन प्रणाली",
        "warning": "⚠️ **महत्वपूर्ण सूचना**\nयो सेवा केवल प्रारम्भिक जाँच सहायक उपकरण हो र यसले अन्तिम निदान प्रदान गर्दैन।",
        "sec1": "1. आवाज मार्फत जानकारी दिनुहोस्",
        "voice_guide": "🎙️ माइक थिच्नुहोस् र आफ्नो **उमेर, लिङ्ग, दुखाइको स्तर, सुरु भएको समय र लक्षणहरू** भन्नुहोस्।",
        "start_rec": "🔴 रेकर्डिङ सुरु", "stop_rec": "⏹️ सम्पन्न",
        "sec2": "2. पहिचान गरिएको जानकारी",
        "age_label": "उमेर समूह", "age_opts": ["१०-१९ वर्ष", "२०-२९ वर्ष", "३०-३९ वर्ष", "४०-४९ वर्ष", "५०-५९ वर्ष", "६०-६९ वर्ष", "७० वर्ष वा माथि"],
        "gender_label": "लिङ्ग", "gender_opt": ["महिला", "पुरुष"],
        "pain_label": "दुखाइको मात्रा (0 देखि 10 सम्म)",
        "onset_label": "सुरु भएको समय", "onset_ph": "जस्तै: हिजो रातीदेखि, २ दिन अघि",
        "symptom_label": "विस्तृत लक्षणहरू", "symptom_ph": "जस्तै: तल्लो दाहिने पेटमा तीव्र दुखाइ र हल्का ज्वरो छ।",
        "meds_label": "दीर्घरोग तथा सेवन गरिरहेको औषधि", "meds_ph": "जस्तै: रक्तचापको औषधि",
        "sec3": "3. प्रारम्भिक जाँच नतिजा",
        "btn_run": "🚀 AI जाँच सुरु गर्नुहोस्", "tts_header": "🔊 आवाजमा नतिजा सुन्नुहोस्",
        "dl_btn": "📲 डाक्टरका लागि कोरियन SOAP फारम डाउनलोड गर्नुहोस्",
        "map_btn": "📍 कोरियामा नजिकैको अस्पताल खोज्नुहोस्"
    },
    "Bahasa Indonesia (인도네시아어)": {
        "code": "id", "name": "Indonesian",
        "title": "🩺 Alat Bantu Skrining Awal & Konsultasi Kesehatan AI",
        "caption": "Sistem skrining multibahasa dan berbasis suara untuk mengurangi kesenjangan akses medis",
        "warning": "⚠️ **Pemberitahuan Penting**\nLayanan ini hanya alat bantu skrining awal dan bukan diagnosis akhir.",
        "sec1": "1. Pendaftaran Pasien via Suara",
        "voice_guide": "🎙️ Tekan mikrofon dan sebutkan **usia, jenis kelamin, tingkat nyeri, waktu mulai, dan gejala**.",
        "start_rec": "🔴 Mulai Rekam", "stop_rec": "⏹️ Selesai",
        "sec2": "2. Profil Pasien yang Terdeteksi",
        "age_label": "Kelompok Usia", "age_opts": ["10-19 tahun", "20-29 tahun", "30-39 tahun", "40-49 tahun", "50-59 tahun", "60-69 tahun", "70+ tahun"],
        "gender_label": "Jenis Kelamin", "gender_opt": ["Wanita", "Pria"],
        "pain_label": "Skala Nyeri (0 tidak sakit ~ 10 sangat sakit)",
        "onset_label": "Waktu Mulai", "onset_ph": "cth.: Sejak tadi malam, 2 hari yang lalu",
        "symptom_label": "Detail Gejala", "symptom_ph": "cth.: Perut kanan bawah terasa nyeri menusuk dan demam ringan.",
        "meds_label": "Penyakit Bawaan & Obat yang Diminum", "meds_ph": "cth.: Obat darah tinggi, Parasetamol",
        "sec3": "3. Hasil Skrining Awal",
        "btn_run": "🚀 Mulai Skrining AI", "tts_header": "🔊 Dengarkan Hasil Suara",
        "dl_btn": "📲 Unduh Lembar SOAP Bahasa Korea untuk Dokter",
        "map_btn": "📍 Cari Rumah Sakit / Klinik Terdekat di Korea"
    },
    "Español (스페인어)": {
        "code": "es", "name": "Spanish",
        "title": "🩺 Herramienta de Consulta y Triaje Inicial con IA",
        "caption": "Sistema multilingüe y de voz para reducir las brechas en el acceso médico",
        "warning": "⚠️ **Aviso Importante**\nEste servicio es solo una herramienta auxiliar de triaje preliminar y no constituye un diagnóstico definitivo.",
        "sec1": "1. Registro del Paciente por Voz",
        "voice_guide": "🎙️ Presione el micrófono e indique su **edad, género, nivel de dolor, inicio y síntomas**.",
        "start_rec": "🔴 Iniciar grabación", "stop_rec": "⏹️ Finalizar",
        "sec2": "2. Información Reconocida del Paciente",
        "age_label": "Grupo de Edad", "age_opts": ["10-19 años", "20-29 años", "30-39 años", "40-49 años", "50-59 años", "60-69 años", "70+ años"],
        "gender_label": "Género", "gender_opt": ["Femenino", "Masculino"],
        "pain_label": "Escala de Dolor (0 a 10)",
        "onset_label": "Inicio de los síntomas", "onset_ph": "ej.: Desde anoche, hace 2 días",
        "symptom_label": "Descripción de los Síntomas", "symptom_ph": "ej.: Dolor punzante en el abdomen inferior derecho y fiebre leve.",
        "meds_label": "Enfermedades previas y Medicamentos", "meds_ph": "ej.: Medicamento para la presión, Paracetamol",
        "sec3": "3. Resultados del Triaje Inicial",
        "btn_run": "🚀 Iniciar Evaluación con IA", "tts_header": "🔊 Escuchar Resultados por Voz",
        "dl_btn": "📲 Descargar Nota SOAP en coreano para el médico",
        "map_btn": "📍 Buscar Hospitales / Clínicas cercanos en Corea"
    },
    "Français (프랑스어)": {
        "code": "fr", "name": "French",
        "title": "🩺 Outil d'Évaluation Préliminaire et de Conseil Médical IA",
        "caption": "Système multilingue et vocal pour combler les disparités d'accès aux soins",
        "warning": "⚠️ **Avis Important**\nCe service est un outil d'orientation préliminaire et ne remplace pas un diagnostic médical.",
        "sec1": "1. Enregistrement Vocal du Patient",
        "voice_guide": "🎙️ Cliquez sur le micro et décrivez votre **âge, sexe, intensité de la douleur, début et symptômes**.",
        "start_rec": "🔴 Démarrer l'enregistrement", "stop_rec": "⏹️ Terminer",
        "sec2": "2. Profil du Patient Reconnu",
        "age_label": "Tranche d'Âge", "age_opts": ["10-19 ans", "20-29 ans", "30-39 ans", "40-49 ans", "50-59 ans", "60-69 ans", "70 ans et plus"],
        "gender_label": "Sexe", "gender_opt": ["Femme", "Homme"],
        "pain_label": "Échelle de Douleur (0 à 10)",
        "onset_label": "Début des symptômes", "onset_ph": "ex. : Depuis hier soir, il y a 2 jours",
        "symptom_label": "Détails des Symptômes", "symptom_ph": "ex. : Douleur aiguë en bas à droite de l'abdomen et fièvre légère.",
        "meds_label": "Antécédents et Traitements", "meds_ph": "ex. : Traitement pour l'hypertension, Paracétamol",
        "sec3": "3. Résultats de l'Évaluation",
        "btn_run": "🚀 Démarrer l'Évaluation IA", "tts_header": "🔊 Écouter les Résultats",
        "dl_btn": "📲 Télécharger la Fiche SOAP en coréen pour le médecin",
        "map_btn": "📍 Trouver un hôpital / une clinique en Corée"
    },
    "العربية (아랍어)": {
        "code": "ar", "name": "Arabic",
        "title": "🩺 أداة الاستشارة الصحية والفرز الأولي بالذكاء الاصطناعي",
        "caption": "نظام متعدد اللغات ويدعم الصوت للحد من الفجوات في الوصول إلى الرعاية الطبية",
        "warning": "⚠️ **إشعار هام**\nهذه الخدمة هي أداة مساعدة للفرز الأولي ولا تقدم تشخيصًا نهائيًا. استشر الطبيب دائمًا.",
        "sec1": "1. إدخال بيانات المريض صوتيًا",
        "voice_guide": "🎙️ اضغط على الميكروفون واذكر **عمرك وجنسك ومستوى الألم وبداية الأعراض وتفاصيلها**.",
        "start_rec": "🔴 بدء التسجيل", "stop_rec": "⏹️ إنهاء",
        "sec2": "2. معلومات المريض التي تم التعرف عليها",
        "age_label": "الفئة العمرية", "age_opts": ["10-19 سنة", "20-29 سنة", "30-39 سنة", "40-49 سنة", "50-59 سنة", "60-69 سنة", "70 سنة فما فوق"],
        "gender_label": "الجنس", "gender_opt": ["أنثى", "ذكر"],
        "pain_label": "مقياس الألم (من 0 إلى 10)",
        "onset_label": "وقت بداية الأعراض", "onset_ph": "مثال: منذ الليلة الماضية، منذ يومين",
        "symptom_label": "وصف الأعراض بالتفصيل", "symptom_ph": "مثال: ألم حاد في أسفل البطن من الجهة اليمنى مع حمى خفيفة.",
        "meds_label": "الأمراض المزمنة والأدوية", "meds_ph": "مثال: دواء ضغط الدم، باراسيتامول",
        "sec3": "3. نتائج التقييم الأولي",
        "btn_run": "🚀 بدء التقييم بالذكاء الاصطناعي", "tts_header": "🔊 الاستماع إلى النتائج صوتيًا",
        "dl_btn": "📲 تنزيل تقرير SOAP الطبي باللغة الكورية للطبيب",
        "map_btn": "📍 البحث عن المستشفيات والعيادات القريبة في كوريا"
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

# 환자 프로필 세션 초기화
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {
        "age_idx": 1,
        "gender_idx": 0,
        "pain_scale": 3,
        "onset_time": "",
        "chronic_meds": "",
        "symptom_text": ""
    }
if "last_processed_audio" not in st.session_state:
    st.session_state.last_processed_audio = None

# Quota 429 에러 방지 안전 호출 함수 (Exponential Backoff + Fallback)
def call_gemini_safe(model_name, contents, system_instruction=None):
    genai.configure(api_key=gemini_api_key)
    kwargs = {"model_name": model_name}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction
    
    # 3.6-flash 한도 초과 시 안정적인 2.5-flash로 자동 전환
    models_to_try = [model_name, "gemini-2.5-flash"]
    
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
                    time.sleep(2 * (attempt + 1))  # 2초, 4초 순차 대기 후 재시도
                    continue
                else:
                    break
    raise Exception("무료 API 분당 요청 한도를 초과했습니다. 약 15초 후 다시 시도해 주세요.")

# 5. 스마트 음성 인식
st.subheader(t["sec1"])
st.write(t["voice_guide"])

audio_rec = mic_recorder(
    start_prompt=t["start_rec"],
    stop_prompt=t["stop_rec"],
    key=f"rec_{t['code']}"
)

# 음성 입력 시 정보 일괄 자동 추출 (호출량 절약을 위해 2.5-flash 우선 활용)
if audio_rec is not None and gemini_api_key:
    audio_bytes = audio_rec.get("bytes", b"")
    if len(audio_bytes) > 0 and audio_bytes != st.session_state.last_processed_audio:
        with st.spinner("Analyzing speech and extracting patient info..."):
            try:
                audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
                extract_prompt = f"""
                Listen to this patient speaking in {t['name']}.
                Extract information into a JSON object with:
                - age_index: integer index from 0 to 6 corresponding to age groups: 0:10s, 1:20s, 2:30s, 3:40s, 4:50s, 5:60s, 6:70s+ (default 1)
                - gender_index: integer 0 for Female, 1 for Male (default 0)
                - pain_scale: integer from 0 to 10 (default 4)
                - onset_time: when symptoms started (in {t['name']})
                - chronic_meds: any medications or chronic diseases (in {t['name']})
                - symptom_text: full transcribed speech describing symptoms (in {t['name']})

                Output ONLY valid raw JSON text without markdown formatting.
                """
                
                resp = call_gemini_safe("gemini-2.5-flash", [audio_part, extract_prompt])
                
                if resp and resp.text:
                    clean_json = re.sub(r'```json|```', '', resp.text).strip()
                    extracted = json.loads(clean_json)
                    st.session_state.patient_data.update(extracted)
                    st.session_state.last_processed_audio = audio_bytes
                    st.success("Patient profile extracted successfully!")
            except Exception as e:
                st.warning(f"Voice Recognition Note: {e}")

# 6. 확인 및 수정 영역
st.subheader(t["sec2"])
col1, col2 = st.columns(2)
with col1:
    saved_age_idx = int(st.session_state.patient_data.get("age_index", 1))
    if saved_age_idx >= len(t["age_opts"]):
        saved_age_idx = 1
    selected_age = st.selectbox(t["age_label"], t["age_opts"], index=saved_age_idx)
    
    saved_gender_idx = int(st.session_state.patient_data.get("gender_index", 0))
    if saved_gender_idx >= len(t["gender_opt"]):
        saved_gender_idx = 0
    selected_gender = st.radio(t["gender_label"], t["gender_opt"], index=saved_gender_idx, horizontal=True)

with col2:
    selected_pain = st.slider(
        t["pain_label"], 0, 10,
        int(st.session_state.patient_data.get("pain_scale", 3))
    )
    selected_onset = st.text_input(
        t["onset_label"],
        value=st.session_state.patient_data.get("onset_time", ""),
        placeholder=t["onset_ph"]
    )

selected_symptoms = st.text_area(
    t["symptom_label"],
    value=st.session_state.patient_data.get("symptom_text", ""),
    placeholder=t["symptom_ph"],
    height=90
)
selected_meds = st.text_input(
    t["meds_label"],
    value=st.session_state.patient_data.get("chronic_meds", ""),
    placeholder=t["meds_ph"]
)

# 7. AI 건강상담 분석 실행
if st.button(t["btn_run"], type="primary"):
    if not gemini_api_key:
        st.error("API Key is missing in Streamlit Secrets.")
    elif not selected_symptoms:
        st.warning("Please provide symptoms either by speaking or typing.")
    else:
        system_instruction = f"""
        You are a public healthcare pre-screening AI assistant designed to reduce medical accessibility gaps.
        
        CRITICAL RULES:
        1. [LANGUAGE]: All explanations, clinical triage, and home-care advice MUST be written strictly in **{t['name']}**.
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
        
        with st.spinner(f"Analyzing in {t['name']}..."):
            try:
                response = call_gemini_safe("gemini-3.6-flash", user_prompt, system_instruction=system_instruction)
                result_text = response.text
                
                st.success("Screening Complete.")
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
                
                # 병원 연계 버튼군
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
                st.error(f"Error: {e}")
