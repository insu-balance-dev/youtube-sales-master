import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# 1. 페이지 설정
st.set_page_config(page_title="유튜브 세일즈 마스터", page_icon="💼", layout="wide")

st.markdown("""
    <style>
    .main-header { font-size: 2.5rem; color: #0365DB; font-weight: 700; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #0365DB; color: white; font-weight: bold; border-radius: 10px; width: 100%; height: 50px; }
    </style>
""", unsafe_allow_html=True)

# 2. 시스템 프롬프트
SYSTEM_PROMPT = """
당신은 최고의 보험 세일즈 마케팅 전문가입니다. 입력된 내용을 분석하여 영업 사원(FC)을 위한 5가지 자료를 생성하세요.
[출력 형식]
1. 📝 핵심 요약 (3~5줄)
2. 🎯 강력한 셀링 포인트 (소구점 3가지)
3. 💬 카톡/문자 스크립트 (버전 A/B)
4. 📞 유선 상담 스크립트 (도입-전개-제안-거절처리-클로징)
5. 🎨 PPT 기획안 (슬라이드 1, 2)
[톤앤매너] 전문적, 신뢰감, 한국어.
"""

# 3. 함수 정의
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
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try: transcript = transcript_list.find_transcript(['ko', 'ko-KR'])
        except: transcript = transcript_list.find_generated_transcript(['ko', 'ko-KR'])
        return " ".join([entry['text'] for entry in transcript.fetch()])
    except: return None

def analyze_content(api_key, text):
    genai.configure(api_key=api_key)
    # 모델명을 가장 안정적인 pro로 변경
    model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(text)
    return response.text

# 4. 메인 화면
st.markdown('<div class="main-header">🎥 유튜브 세일즈 마스터</div>', unsafe_allow_html=True)

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("API Key 입력", type="password")

tab1, tab2 = st.tabs(["🔗 링크로 분석", "✍️ 직접 입력(추천)"])

with tab1:
    url = st.text_input("유튜브 URL")
    if st.button("링크 분석 시작"):
        if not api_key: st.error("API 키가 없습니다.")
        elif not url: st.warning("URL을 넣으세요.")
        else:
            vid = get_video_id(url)
            if vid:
                with st.spinner("자막 추출 중... (실패 시 옆 탭을 이용하세요)"):
                    txt = get_transcript(vid)
                    if txt:
                        st.markdown(analyze_content(api_key, txt))
                    else:
                        st.error("❌ 유튜브 보안으로 자막이 차단되었습니다.")
                        st.info("👉 **해결책:** '✍️ 직접 입력' 탭에 내용을 붙여넣으세요! (100% 됨)")

with tab2:
    st.caption("유튜브 영상의 '스크립트'를 복사해서 여기에 붙여넣으세요.")
    txt_input = st.text_area("내용 붙여넣기", height=300)
    if st.button("텍스트 분석 시작"):
        if not api_key: st.error("API 키가 없습니다.")
        elif not txt_input: st.warning("내용을 입력하세요.")
        else:
            with st.spinner("분석 중..."):
                st.markdown(analyze_content(api_key, txt_input))
