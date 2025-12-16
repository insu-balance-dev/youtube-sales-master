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
# 2. 시스템 프롬프트
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
당신은 최고의 보험 세일즈 마케팅 전문가이자 콘텐츠 기획자입니다.
사용자가 입력한 영상 내용(자막)을 분석하여 영업 사원(FC, RC)의 실적 향상을 위한 5가지 핵심 세일즈 자료를 생성하십시오.

[필수 수행 절차]
1. 내용에서 상품의 특징, 고객의 문제점(Pain Point), 해결책(Solution), 혜택(Benefit)을 추출하십시오.
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
# 3. 로직 함수 (오류 수정됨)
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
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # 한국어 우선 검색 (수동 및 자동)
        try:
            transcript = transcript_list.find_transcript(['ko', 'ko-KR'])
        except:
            # 한국어가 없으면 생성된 자막이라도 시도
            transcript = transcript_list.find_generated_transcript(['ko', 'ko-KR'])
            
        return " ".join([entry['text'] for entry in transcript.fetch()])
    except Exception as e:
        return None

def analyze_content(api_key, text):
    genai.configure(api_key=api_key)
    # [수정 완료] 오류가 났던 flash 대신 가장 안정적인 'gemini-1.5-pro' 사용
    model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=SYSTEM_PROMPT)
    response = model.generate_content(text)
    return response.text

# --------------------------------------------------------------------------
# 4. 메인 화면 구성
# --------------------------------------------------------------------------
st.markdown('<div class="main-header">🎥 유튜브 세일즈 마스터</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">영상 링크를 넣거나, 대본을 직접 입력하세요.</div>', unsafe_allow_html=True)

# API 키 설정
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("관리자 키 입력 (설정되지 않음)", type="password")

# 탭 구성: URL 입력 vs 텍스트 직접 입력
tab_url, tab_text = st.tabs(["🔗 유튜브 링크로 분석", "✍️ 텍스트 직접 입력"])

# [TAB 1] 유튜브 링크 분석
with tab_url:
    url = st.text_input("분석할 유튜브 영상 URL", placeholder="https://www.youtube.com/watch?v=...")
    if st.button("링크로 분석 시작 🚀"):
        if not api_key:
            st.error("⚠️ API 키가 설정되지 않았습니다.")
        elif not url:
            st.warning("⚠️ 유튜브 URL을 입력해주세요.")
        else:
            video_id = get_video_id(url)
            if not video_id:
                st.error("⚠️ 올바르지 않은 유튜브 URL입니다.")
            else:
                with st.spinner("자막을 추출하고 분석 중입니다..."):
                    transcript = get_transcript(video_id)
                    if transcript:
                        try:
                            result = analyze_content(api_key, transcript)
                            st.success("분석 완료!")
                            st.markdown(result)
                        except Exception as e:
                            st.error(f"분석 중 오류 발생: {e}")
                    else:
                        st.error("⚠️ 이 영상은 자막을 가져올 수 없습니다. 아래 해결책을 사용하세요!")
                        st.info("💡 **해결책:** 영상의 '스크립트'를 복사해서 **'✍️ 텍스트 직접 입력'** 탭에 붙여넣어 보세요!")

# [TAB 2] 텍스트 직접 입력 (백업 플랜)
with tab_text:
    st.caption("유튜브 자막 다운로드가 안 되는 영상은 여기에 내용을 직접 붙여넣으세요.")
    manual_text = st.text_area("영상 스크립트 또는 내용 붙여넣기", height=300)
    if st.button("텍스트로 분석 시작 ✨"):
        if not api_key:
            st.error("⚠️ API 키가 설정되지 않았습니다.")
        elif not manual_text:
            st.warning("⚠️ 분석할 내용을 입력해주세요.")
        else:
            with st.spinner("입력한 내용을 분석 중입니다..."):
                try:
                    result = analyze_content(api_key, manual_text)
                    st.success("분석 완료!")
                    st.divider()
                    st.markdown(result)
                except Exception as e:
                    st.error(f"오류 발생: {e}")
