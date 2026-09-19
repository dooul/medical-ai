import streamlit as st
from google import genai

# 페이지 기본 설정
st.set_page_config(page_title="AI 의료상담 & 문진 연계 프로토타입", layout="centered")

st.title("🩺 의료 접근성 개선을 위한 AI 건강상담 시스템")
st.caption("공공 의료 가이드라인 기반 1차 스크리닝 및 사전 문진표 발행 서비스")

# 사이드바: API 키 입력
with st.sidebar:
    st.header("⚙️ 환경 설정")
    api_key = st.text_input("Google Gemini API 키를 입력하세요", type="password")
    st.markdown("---")
    st.info("💡 **의료법 제27조 준수 고지**\n본 서비스는 질환의 확정 진단을 제공하지 않으며, 공공 의료 데이터 기반의 증상 스크리닝과 적정 진료과 안내를 돕는 보조 도구입니다.")

# 문진 입력 (설문조사 단점 보완: 맞춤형 상태 반영)
st.subheader("1. 기본 증상 및 환자 정보 입력")
col1, col2 = st.columns(2)
with col1:
    age_group = st.selectbox("연령대", ["10대", "20대", "30대", "40대", "50대", "60대 이상"])
    gender = st.radio("성별", ["여성", "남성"], horizontal=True)
with col2:
    pain_level = st.slider("통증/불편도 (NRS 척도: 0 무통 ~ 10 극심한 통증)", 0, 10, 3)
    duration = st.text_input("증상 발생 시점 / 지속 기간", placeholder="예: 어제 저녁부터, 3일 전부터")

symptom_text = st.text_area(
    "현재 느끼시는 구체적인 증상을 말씀해 주세요",
    placeholder="예: 오른쪽 아랫배가 찌르듯이 아프고 미열이 나요. 누를 때보다 손을 뗄 때 더 아픕니다.",
    height=100
)

underlying_disease = st.text_input("기저질환 및 복용 중인 약물", placeholder="예: 고혈압 약 복용 중, 알레르기 비염")

# AI 상담 시작 버튼
if st.button("AI 상담 및 분석 시작", type="primary"):
    if not api_key:
        st.error("좌측 사이드바에 Gemini API 키를 먼저 입력해 주세요.")
    elif not symptom_text:
        st.warning("증상을 입력해 주세요.")
    else:
        system_instruction = """
        당신은 의료 접근성 격차를 해소하기 위해 공공 보건 가이드라인을 기반으로 1차 스크리닝을 돕는 '의료상담 전문 AI'입니다.
        아래 지침을 엄격히 준수하십시오:
        1. [절대 원칙] 확정 진단을 내리지 말고, 가능 질환군을 제시하십시오.
        2. [중증도 분류] 즉시 응급실로 가야 하는 징후가 감지되면 상단에 굵은 경고 문구를 표시하십시오.
        3. [적정 진료과] 방문해야 할 가장 적합한 1·2차 진료과(내과, 외과, 정형외과 등)를 명확히 추천하십시오.
        4. [공공 출처 표기] 질병관리청 국가건강정보포털, 건강보험심사평가원, 식약처 DUR 가이드라인을 출처로 명시하십시오.
        5. [의사용 요약표 (SOAP Note)] 실제 의사에게 제출할 수 있도록 다음 4가지 항목으로 정리하십시오:
           - S(Subjective): 환자 호소 증상 및 기간
           - O(Objective): 통증 점수, 기저질환, 복용약
           - A(Assessment): AI 1차 추정 가능 소견
           - P(Plan): 권장 진료과 및 응급도 수준
        """
        
        user_prompt = f"""
        {system_instruction}

        [환자 정보]
        - 연령/성별: {age_group} / {gender}
        - 통증 정도: {pain_level} / 10
        - 지속 기간: {duration}
        - 기저질환 및 약물: {underlying_disease}
        - 증상 호소 내용: {symptom_text}
        """

        with st.spinner("임상 가이드라인 기반 증상 분석 및 Triage 분류 중..."):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=user_prompt
                )
                
                st.success("분석이 완료되었습니다.")
                st.markdown("---")
                st.subheader("2. AI 스크리닝 결과 및 권고 사항")
                st.markdown(response.text)
                
                st.markdown("---")
                st.subheader("3. 병원 진료 연계 (다음 단계)")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button("📍 내 주변 야간/휴일 진료기관 찾기 (공공 API 연동)")
                with col_btn2:
                    st.button("📲 병원 제출용 모바일 사전 문진표 다운로드")
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")