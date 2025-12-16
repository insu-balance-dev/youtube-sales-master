import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# --------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="유튜브 세일즈 마스터",
    page_icon="💼",
    layout="wide"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #0365DB;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 40px;
    }
    .stButton>button {
        background-color: #0365DB;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
        height: 50px;
    }
    .stButton>button:hover {
        background-color: #024bfa;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 2. 시스템 프롬프트 (수정 금지)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
당신은 최고의 보험 세일즈 마케팅 전문가이자 콘텐츠 기획자입니다.
사용자가 유튜브 영상 내용을 입력하면(자막), 해당 내용을 정밀 분석하여 영업 사원(FC, RC)의 실적 향상을 위한 5가지 핵심 세일즈 자료를 생성하십시오.

[필수 수행 절차]
1. 영상에서 상품의 특징, 고객의 문제점(Pain Point), 해결책(Solution), 혜택(Benefit)을 추출하십시오.
2. 아래 5가지 출력 형식을 엄격히 준수하십시오.

### [출력 형식]
#### 1. 📝 핵심 요약 (Executive Summary)
* 영상 전체 내용을 3~5줄 내외로 요약. 영업 사원이 10초 만에 파악 가능하도록 작성.
#### 2. 🎯 강력한 셀링 포인트 (Selling Points)
* 소구점 3가지. 고객이 얻게 될 이익(Benefit) 중심.
#### 3. 💬 카톡/문자 발송용 스크립트 (Chat Script)
* 버전 A (정보 전달형) / 버전 B (호기심 자극형). 이모지 사용.
#### 4. 📞 유선 상담 스크립트 (Tele-Sales Script)
* 도입-전개-제안-거절처리-클로징 흐름.
#### 5. 🎨 고객 발송용 PPT 제작 프롬프트 (For Canvas)
* 슬라이드 1: 위기감 조성 & 문제 제기 (공포 마케팅, 붉은색 강조)
* 슬라이드 2: 솔루션 제시 & 채팅 유도 (해결책, 파란색 강조, CTA)

[톤앤매너]
전문적, 신뢰감, 한국어 작성.
"""

# --------------------------------------------------------------------------
# 3. 로직 함수
# --------------------------------------------------------------------------
def get_video_id(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be': return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch': return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/embed/': return query.path.split('/')[2]
        if query.path[:3] == '/v/': return query.path.split('/')[2]
    return None

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        return " ".join([entry['text'] for entry in transcript_list])
    except:
        return None

def analyze_video(api_key, transcript):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(transcript)
    return response.text

# --------------------------------------------------------------------------
# 4. 메인 화면
# --------------------------------------------------------------------------
st.markdown('<div class="main-header">🎥 유튜브 세일즈 마스터</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">영상 링크만 넣으세요. FC님을 위한 세일즈 자료가 쏟아집니다.</div>', unsafe_allow_html=True)

# API 키 처리 (비밀 관리자 또는 사용자 입력)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("관리자 키 입력 (설정되지 않음)", type="password")

url = st.text_input("분석할 유튜브 영상 URL", placeholder="https://www.youtube.com/watch?v=...")
if st.button("분석 시작 🚀"):
    if not api_key:
        st.error("⚠️ API 키가 설정되지 않았습니다.")
    elif not url:
        st.warning("⚠️ 유튜브 URL을 입력해주세요.")
    else:
        video_id = get_video_id(url)
        if not video_id:
            st.error("⚠️ 올바르지 않은 유튜브 URL입니다.")
        else:
            with st.spinner("영상을 분석 중입니다... 잠시만 기다려주세요!"):
                transcript = get_transcript(video_id)
                if transcript:
                    try:
                        result = analyze_video(api_key, transcript)
                        st.success("분석 완료!")
                        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 요약", "🎯 포인트", "💬 문자", "📞 상담", "🎨 PPT"])
                        with tab1: st.markdown(result) # 전체 내용을 탭1에 보여줍니다 (편의상)
                        st.info("💡 각 탭을 클릭하면 내용을 자세히 볼 수 있습니다. (현재 버전은 전체 내용이 통합되어 표시됩니다)")
                    except Exception as e:
                        st.error(f"오류 발생: {e}")
                else:
                    st.error("⚠️ 한글 자막이 없는 영상입니다.")
