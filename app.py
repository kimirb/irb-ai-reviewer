import streamlit as st
import os
import base64
import datetime
import html  
import re

# 한 번에 검토 가능한 전체 페이지 수 상한 (AI 호출 과부하 방지)
MAX_TOTAL_PAGES = 150

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="김안과병원IRB AI 사전검토", page_icon="⚖️", layout="wide")

# 세션 상태(금고) 초기화 로직 — 페이지 진입 시 가장 먼저 한 번만 실행
if "ai_result" not in st.session_state:
    st.session_state.ai_result = None
if "uploaded_files_signature" not in st.session_state:
    st.session_state.uploaded_files_signature = ()
if "uploader_key" not in st.session_state:      # ← 추가
    st.session_state.uploader_key = 0           # ← 추가

# 2. 메인 타이틀 및 상단 디자인
st.title("⚖️김안과병원 IRB AI 사전 행정검토")

st.markdown("""
    <div style="font-size: 17px; line-height: 1.6; color: #31333F; margin-top: 22px; margin-bottom: 10px;">
        본 시스템은 <b>김안과병원 연구자</b> 분들의 원활한 IRB 심의서류 작성을 위해, IRB 의뢰 전 
        <b>연구자주도 후향적 연구 서류</b>에 대한 <b>AI 기반 사전 행정검토</b>를 지원합니다.<br>
        단, AI 검토 결과는 참고용으로만 활용하시기 바라며, IRB 행정간사의 공식 의견을 대변하지 않습니다.
    </div>
""", unsafe_allow_html=True)


# 버튼을 만들기 위한 CSS 및 함수 정의 (버튼을 그리기 전에 먼저 선언되어야 합니다)
SIDEBAR_BUTTON_CSS = """
<style>
.sidebar-btn, .sidebar-btn:link, .sidebar-btn:visited,
.sidebar-btn:hover, .sidebar-btn:active {
    color:#ffffff !important;
}
</style>
"""

def build_pdf_open_button_html(label, pdf_path, color="#0f766e"):
    if not os.path.exists(pdf_path):
        return f"""<div style="font-size: 12px; color: #b91c1c; margin: 2px 0 8px 0;">
            ⚠️ {html.escape(label)} 파일이 서버에 없습니다. (경로: {html.escape(pdf_path)})
        </div>"""
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    
    # 💡 1. 파일 경로에서 이름만 쏙 뽑아옵니다 (Retro_guide.pdf)
    file_name = os.path.basename(pdf_path)
    
    # 💡 2. target="_blank"를 지우고, download="{file_name}"을 넣어줍니다!
    return f"""<a href="data:application/pdf;base64,{b64_pdf}" download="{file_name}" class="sidebar-btn"
           style="display:flex; align-items:center; justify-content:center; width:100%;
                  box-sizing:border-box; padding:9px 14px; background-color:{color};
                  color:#ffffff !important; border-radius:8px; font-size:14px; font-weight:600;
                  text-decoration:none;">
            📄&nbsp; {html.escape(label)}
        </a>"""

def build_link_button_html(label, url, color="#1e3a5f", icon="🔗"):
    return f"""<a href="{url}" target="_blank" class="sidebar-btn"
           style="display:flex; align-items:center; justify-content:center; width:100%;
                  box-sizing:border-box; padding:9px 14px; background-color:{color};
                  color:#ffffff !important; border-radius:8px; font-size:14px; font-weight:600;
                  text-decoration:none;">
            {icon}&nbsp; {html.escape(label)}
        </a>"""

e_irb_btn = build_link_button_html(
    "김안과병원 e-IRB 바로가기",
    "https://r-bay.co.kr/agency/main/enh5TE5EYlBUZ1hnZElnaXNidjczdz09",
    color="#1e3a5f",
    icon="🔗",
)
guide_btn = build_pdf_open_button_html(
    "e-IRB 신청서 작성 가이드 열기",
    "forms/Retro_guide.pdf",
    color="#0f766e",
)

st.markdown(SIDEBAR_BUTTON_CSS, unsafe_allow_html=True)
st.markdown(
    f"""<div style="display:flex; flex-direction:row; justify-content:flex-start; gap:16px; margin-bottom:0px;">
        <div style="width: 280px;">{e_irb_btn}</div>
        <div style="width: 280px;">{guide_btn}</div>
    </div>""",
    unsafe_allow_html=True,
)
# ────────────────────────────────────────────────────────

st.markdown('<hr style="border: 0; border-top: 1px solid #e2e8f0; margin-top: 25px; margin-bottom: 15px;">', unsafe_allow_html=True)

# 3. 사이드바 (제출 서류 안내, 지적 사항, 문의처 포함)
with st.sidebar:
    st.markdown("""
    <style>    
    section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
        padding-top: 0rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stSidebarHeader"] {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }   
    section[data-testid="stSidebar"] div[data-testid="stSidebarHeader"] button {
    min-width: 1.25rem !important;
    min-height: 0rem !important;
    padding: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <h2 style="margin-top: -50px; margin-bottom: 10px; font-size: 20px; font-weight: 700;">📁 후향적 연구 제출 서류</h2>
    <small style="color: #666; display: block; margin-bottom: 12px;">사전 검토를 위해 아래 서류들을 모두 업로드창에 드래그하여 넣어주세요.</small>
    
    <div style="line-height: 1.9; font-size: 15px; color: #31333F;">
        <b>1. [서식 2] 후향적 연구계획서</b> 
           <span style="background-color: #ffe4e6; color: #e11d48; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 4px;">필수</span><br>
        <b>2. [서식 7] 연구자 서약서</b> 
           <span style="background-color: #ffe4e6; color: #e11d48; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 4px;">필수</span><br>
        <b>3. 증례기록서(CRF)</b> 
           <span style="background-color: #ffe4e6; color: #e11d48; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 4px;">필수</span><br>
        <b>4. 연구책임자 이력서</b> 
           <span style="background-color: #ffe4e6; color: #e11d48; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 4px;">필수</span><br>
        <b>5. [서식 11] 심의면제 자가점검표</b> 
           <span style="background-color: #f1f5f9; color: #64748b; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 4px;">해당 시</span><br>
        <b>6. [서식 12] 연구비 산정서</b> 
           <span style="background-color: #f1f5f9; color: #64748b; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-left: 4px;">해당 시</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # 구분선(---) 바로 아래의 여백도 당겨줍니다(-25px)
    st.markdown("""
    <h2 style="margin-top: -25px; margin-bottom: 0px; font-size: 20px; font-weight: 700;">📌 주요 지적사항</h2>
    
    <ul style="font-size: 15px; line-height: 1.5; padding-left: 8px; color: #31333F; margin-top: 2px;">
        <li style="margin-bottom: 8px;"><b>연구계획서와 증례기록서</b><br>버전 및 유효일자 필수 (ex. V1.0, 2026.07.01)</li>
        <li style="margin-bottom: 8px;"><b>연구자 소속</b><br>각막센터, 망막병원, 녹내장센터, 사시소아안과센터, 성형안과센터, 수련부, 임상연구센터(안과❌)</li>
        <li style="margin-bottom: 8px;"><b>연구자 직함</b><br>전문의, 전공의, 센터장 등(교수❌)</li>
        <li style="margin-bottom: 8px;"><b>연구제목 일치</b><br>모든 서류의 연구제목 반드시 일치</li>
        <li style="margin-bottom: 8px;"><b>연구진 일치</b><br>R-Bay 신청서와 연구계획서 내 연구자 명단 일치</li>
        <li style="margin-bottom: 8px;"><b>수집항목 일치</b><br>연구계획서와 증례기록서 수집항목 100% 동일하게 작성</li>
        <li style="margin-bottom: 8px;"><b>수집불가 항목🚨</b><br>이름, 주민등록번호, 생년월일, 병원등록번호, 주소 등 개인정보 수집 불가</li>
    </ul>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin-top: 8px; margin-bottom: 15px;">
        """, unsafe_allow_html=True)
        
    st.markdown("""
        <div style="line-height: 1; font-size: 15px; color: #31333F;">
            ▪️문의 : IRB사무국(02-2639-7812 / 내선 812)
        </div>
    """, unsafe_allow_html=True)

# 4. 파일 업로드 섹션
st.subheader("📂 Submit IRB Documents")

# 업로더 + 삭제 버튼을 하나의 컨테이너로 묶어서, 버튼을 박스 우측 하단에 겹쳐 배치
upload_area = st.container(key="upload_area")
with upload_area:
    uploaded_files = st.file_uploader(
        "연구계획서, 증례기록서, 연구자 서약서 등 PDF 파일을 모두 선택하여 업로드해 주세요.",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    if st.button("전체 삭제", key="clear_btn", type="tertiary"):
        st.session_state.uploader_key += 1
        st.session_state.ai_result = None
        st.session_state.uploaded_files_signature = ()
        st.rerun()

st.markdown("""
<style>
.st-key-upload_area { position: relative; }
.st-key-clear_btn {
    position: absolute;
    bottom: 13px;
    right: 13px;
    margin: 0 !important;
    z-index: 10;
}
.st-key-clear_btn div.stButton > button {
    border: none !important;
}
.st-key-clear_btn div.stButton > button:hover {
    background-color: transparent !important;
    border: none !important;
}
.st-key-clear_btn div.stButton > button,
.st-key-clear_btn div.stButton > button p {
    font-weight: 400 !important;
    font-size: 12px !important;
    color: #94a3b8 !important;
}
.st-key-clear_btn div.stButton > button:hover,
.st-key-clear_btn div.stButton > button:hover p {
    color: #ef4444 !important;
}
</style>
""", unsafe_allow_html=True)

# 업로드된 파일 구성(파일명+크기)이 이전과 달라지면 이전 검토 결과를 자동으로 무효화
current_files_signature = tuple(sorted((f.name, f.size) for f in uploaded_files)) if uploaded_files else ()
if st.session_state.get("uploaded_files_signature") != current_files_signature:
    st.session_state.ai_result = None
    st.session_state.uploaded_files_signature = current_files_signature

def split_recommendation_section(md_text):
    """AI 응답에서 본문과 '[행정 권고사항]' 블록을 분리합니다."""
    marker = "[행정 권고사항]"
    if marker not in md_text:
        return md_text, None

    before, _, after = md_text.partition(marker)
    
    # 💡 수정된 부분 1: 마커 앞에 남아있는 <br> 잔여물 제거 (대소문자/공백/줄바꿈 모두 고려)
    before = re.sub(r'(?i)<br\s*/?>\s*$', '', before.strip())

    # <br>(대소문자/공백 변형 포함) 기준으로 분리
    raw_items = re.split(r'<br\s*/?>', after, flags=re.IGNORECASE)
    items = []
    for raw in raw_items:
        cleaned = re.sub(r'^\s*\d+[.)]\s*', '', raw.strip())  # 앞의 "1. " 같은 번호 제거
        if cleaned:
            items.append(cleaned)

    return before.strip(), (items if items else None)

# 현재 연도와 작년 연도를 자동으로 계산
current_year = datetime.date.today().year
prev_year = current_year - 1

# 5. AI 검토 시스템 작동 엔진 (★앞에 소문자 f를 꼭 붙여주세요!)
SYSTEM_PROMPT = f"""
너는 김안과병원(Kim's Eye Hospital) IRB의 전문적이고 정중한 AI 행정검토 어시스턴트야. 연구자가 심의를 접수하기 전, 서류의 행정적 누락이나 오류를 미리 확인하여 도움을 주는 것이 너의 목적이야.

* 답변 톤 앤 매너: 감정적이거나 과장된 표현은 배제하고, 객관적이고 정중한 사무용 어투(~합니다, ~가 필요합니다)를 사용해.
* 예외 처리 판단: 문서를 읽고 해당 연구가 '단일기관 연구'인지 '다기관 연구'인지, 그리고 연구 디자인이 일반적인 '임상 연구'인지 '증례 보고(Case Report / Case Series)'인지 먼저 파악하여 아래의 예외 조항을 유연하게 적용해.

* [★중요 - 출력 형식 필수 지침★]
  - 검토 결과 중 '적절' 판정을 받은 항목은 연구자가 보완할 필요가 없으므로 표에서 완전히 제외해줘.
  - 오직 검토 결과가 '보완'이거나 추가 확인/수정이 필요한 항목들만 표의 행(Row)으로 구성해서 출력해줘. (라벨 이름은 무조건 '보완' 두 글자로 통일해줘)
  - 만약 모든 검토 항목이 완벽하여 '보완' 항목이 단 하나도 없다면, 표를 그리지 말고 아래 문구만 대형 이모지와 함께 깔끔하게 출력해줘:
    "🎉 축하합니다! 모든 행정 검토 항목이 '적절'합니다. 누락이나 오류가 발견되지 않았으므로 이대로 안심하고 심의를 신청하셔도 좋습니다."
  - 표를 출력할 때는 무조건 깔끔한 가로형 마크다운 표(Markdown Table) 형태로 출력해줘.
  - 절대 모든 내용을 한 줄로 길게 이어 붙이거나 '||' 같은 문자로 때우지 마. 
  - 한 행(Row) 작성이 끝나면 반드시 줄바꿈(엔터)을 실행하여 실제 표 격자 구조가 깨지지 않게 해줘.
  - 표의 헤더 구조는 아래 형식을 똑같이 따라해줘:
    | 구분 | 검토 항목 | 검토<br>결과 | 상세 내용 및 보완 사항 |
    | :--- | :--- | :--- | :--- |
  - [★중요★] 표의 '구분' 열에는 '1', '4' 같은 단순 숫자를 적지 말고, 점검 분야의 이름(예: '서류 교차 검증', '개인정보 보호', '증례기록서 점검' 등)을 텍스트로 명확히 적어줘.
  - [행정 권고사항]이 1개 이상 발생할 경우, 반드시 마크다운 표 바깥 하단에 '[행정 권고사항]<br>1. 첫 번째 내용<br>2. 두 번째 내용' 형식으로 번호를 매기고 줄바꿈(<br>)을 적용하여 깔끔하게 출력해줘.
  
[★필수 제출 서류 누락 점검 지침★]
- 필수 제출 서류 4종: '연구계획서', '연구자 서약서', '증례기록서(CRF)', '연구책임자 이력서'
- 제공된 모든 문서의 파일명 및 내용을 바탕으로 위 4종의 서류가 모두 제출되었는지 가장 먼저 스캔해.
- 하나라도 누락된 서류가 있다면, 표의 '구분' 열을 '필수 서류 점검'으로 지정하고 [보완] 판정과 함께 "필수 제출 서류인 OOO이(가) 누락되었습니다. 해당 서류를 함께 제출해 주시기 바랍니다."라고 안내해줘.

[★서류 서식 버전 검증 지침★]
- 제출된 문서 중 기관 공식 양식('연구자 서약서', '연구대상자 동의면제 점검표', '심의면제 자가점검표', '연구비 산정서'등)의 우측 하단 바닥글을 확인해. 최신 공식 규격은 **V15.0(또는 Ver 15.0)**이야.
- 만약 문서의 우측 하단 바닥글이나 텍스트 내에서 버전 표시를 정밀 스캔하여, 만약 **V14.0** 등 구버전 양식을 사용한 것이 확인되면 **[보완]** 판정해.
- 구버전 서식 적발 시 상세 내용에 다음 안내를 필수 포함해줘: "김안과병원 IRB 최신 공식 양식인 V15.0 서식을 사용하여 재작성 및 제출해 주시기 바랍니다."
- ★단, 문서의 양식 자체는 최신 양식이 맞으나, 연구자가 임의로 바닥글 버전만 본인의 연구계획서 버전에 맞춰 'Ver 1.0' 등으로 임의 수정한 것으로 보인다면 **[보완] 판정을 내리지 마**. 대신 표 하단 **[행정 권고사항]** 목록에 "제출하신 연구자 서약서 등의 바닥글에 기재된 버전(Ver 1.0)은 연구자가 임의로 변경한 것으로 보입니다. 기관 공식 서식의 버전(V15.0)은 연구자가 임의로 변경하지 않고 유지해 주시기 바랍니다."라는 내용을 추가해.
- 단, **'연구계획서'**, **'동의서'**와 **'이력서'**는 기관 전용 서식을 강제하지 않으므로 버전 불일치로 인한 보완 요구를 적용하지 마.

[★연구계획서 파일명 및 내부 버전 일치 검증 지침★]
- 제공된 연구계획서의 [문서 파일명]에 포함된 버전 정보(예: _V15.0)와 문서 내부 바닥글(또는 본문)에 연구자가 기재한 버전 정보(예: V1.0_2025-10-13)를 교차 대조해줘.
- 만약 파일명에 적힌 버전과 내부 바닥글 버전의 숫자가 서로 다를 경우(예: 파일명은 V15.0인데 내부 바닥글은 V1.0인 경우), 무조건 **[보완]**으로 판정하고 상세 내용에 아래 문구를 정중하게 출력해줘:
  "연구계획서 내부 바닥글에 기재된 버전과 제출하신 파일명의 버전이 서로 일치하지 않습니다. 내부 문서 버전과 일치하도록 파일명을 수정하거나, 최신 버전에 맞게 내부 서식을 업데이트하여 일치시켜 주시기 바랍니다."

[★증례기록서(CRF) 필수 항목 및 양식 인식 지침★]
- 파일명 인식 예외: 제출된 파일의 이름이 'sheet', '통계', '데이터' 등 모호하게 되어 있더라도, 내부에 환자 데이터를 수집하는 표나 항목(변수)들이 나열된 문서라면 이를 무조건 '증례기록서(CRF)'로 간주해.
- 필수 기재 항목 점검: 증례기록서(CRF) 문서 내부(주로 상단이나 하단 바닥글)에 다음 4가지 항목이 모두 기재되어 있는지 확인해:
  1) 연구과제명 (연구제목)
  2) 연구책임자 성명
  3) 문서 버전 (예: Ver 1.0, V1.0 등)
  4) 작성일자 또는 유효일자 (예: 2026.07.01 등)
- 만약 위 4가지 중 하나라도 아예 기재되어 있지 않다면(누락되었다면) 무조건 [보완] 판정을 내려. 표의 '구분' 열을 '증례기록서 점검'으로 지정하고 상세 내용에 "증례기록서(CRF) 내에 필수 기재 항목인 [누락된 항목 이름, ex: 연구과제명 및 작성일자]이(가) 확인되지 않습니다. 증례기록서 상/하단 등에 해당 내용을 명확히 기재하여 주시기 바랍니다."라고 지적해.

[★증례기록서(CRF) 파일명 및 내부 버전 일치 검증 지침★]
- 제공된 증례기록서(CRF)의 [문서 파일명]에 포함된 버전 정보(예: _V1.0)와 문서 내부 바닥글(또는 본문)에 연구자가 기재한 버전 정보(예: V1.0_2026-07-01)를 교차 대조해줘.
- 만약 파일명에 적힌 버전과 내부 바닥글 버전의 숫자가 서로 다를 경우(예: 파일명은 V2.0인데 내부 바닥글은 V1.0인 경우), 무조건 **[보완]**으로 판정하고 표의 '구분' 열을 '증례기록서 점검'으로 지정한 뒤 상세 내용에 아래 문구를 정중하게 출력해줘:
  "증례기록서(CRF) 내부 바닥글에 기재된 버전과 제출하신 파일명의 버전이 서로 일치하지 않습니다. 내부 문서 버전과 일치하도록 파일명을 수정하거나, 최신 버전에 맞게 내부 서식을 업데이트하여 일치시켜 주시기 바랍니다."

[김안과병원 사전검토 체크리스트]
0. 연구계획서 필수 기재 항목 점검
- 제출된 연구계획서 본문에 다음 12가지 필수 항목이 모두 기재되어 있는지 전체 문맥과 목차를 스캔해: 
  1) 연구제목, 2) 연구자(책임/공동/담당자의 성명, 소속, 직위), 3) 연구의 배경, 4) 연구의 목적, 5) 연구 대상자 선정기준, 6) 연구 대상자 제외기준, 7) 연구대상자의 수 및 근거, 8) 연구의 기간, 9) 연구의 방법, 10) 평가항목, 11) 효과 평가기준·평가방법 및 해석방법, 12) 대상자의 개인정보 보호대책(익명화 방법 등).
- ★[연구자 정보 파악 주의]: 2)번 항목을 스캔할 때, '김민지 각막센터 전문의'처럼 [성명] [소속] [직함]이 한 줄에 띄어쓰기로만 연속 표기된 경우가 매우 많아. '직함:'이라는 라벨 글자가 명시되어 있지 않더라도, 이름 옆에 '전문의', '전공의' 등의 직위 명칭이 텍스트 내에 존재한다면 정상 인식하고 누락으로 오진하지 마.
- ★[다기관 연구 예외 적용]: 만약 서류 문맥상 해당 연구가 여러 병원이 참여하는 '다기관 연구'로 파악된다면, 공통 계획서 양식 특성상 본문에 특정 병원의 '연구자 성명 및 소속(2번 항목)'이 아예 기재되어 있지 않을 수 있어. 다기관 연구인데 계획서에 연구자 이름이 비어있다고 해서 누락으로 지적(보완)하지 말고 유연하게 [적절]로 넘어가줘.
- 만약 위 항목 중 1개라도 내용이 누락되었다면(다기관 예외 제외) 표의 '구분' 열을 '계획서 필수 항목'으로 지정하고 [보완] 판정을 내려. 상세 내용에는 "연구계획서 내 필수 기재 항목인 [누락된 항목 이름]이(가) 확인되지 않습니다. 해당 내용을 기재하여 주시기 바랍니다."라고 명확히 안내해.
- 13) 대상자 동의(서) 면제 사유 및 동의서 제출 검증: 후향적 연구 중 연구자가 동의면제를 원하지 않고 직접 동의서를 구득하여 제출하는 경우가 있어. 따라서 다음 세 가지 조건 중 **어느 하나(1개)라도 만족하면 무조건 [적절]**로 판정하고 절대 보완을 요구하지 마:
  A) 연구계획서 본문 내에 '대상자 동의 면제 사유'가 명확히 기재되어 있음.
  B) 제출된 전체 파일 중 '[서식 4] 연구대상자 동의면제 점검표' 서식이 존재함.
  C) 제출된 전체 파일 중 '동의서' 또는 '연구대상자 동의서' 양식이 별도로 존재함.
  ★[중요] 만약 계획서에 동의 면제 사유도 없고, [서식 4] 점검표도 제출되지 않았으며, 동시에 별도의 '동의서' 파일도 업로드되지 않은 '셋 다 누락된 상태'일 때만 [보완] 판정을 내려. 상세 내용에는 "연구계획서 내 '대상자 동의 면제 사유'가 누락되었거나 [서식 4] 동의면제 점검표가 제출되지 않았습니다. 동의면제를 신청하시려면 계획서 내용을 보완하거나 서식 4를 제출해 주시고, 만약 동의면제를 신청하지 않고 직접 동의를 받는 연구라면 별도의 '연구대상자 동의서' 양식을 함께 업로드하여 제출해 주시기 바랍니다."라고 안내해줘.

  1. 통합 서류 교차 검증 (연구제목 및 명단)
- 연구제목 교차 검증: 모든 제출 서류의 연구과제명이 서로 동일한지 대조해. ★[환각 및 줄바꿈 오진 절대 주의]: PDF 문서 표 안에서 제목이 길어 줄바꿈(엔터)이 발생해 글자가 쪼개져 인식되더라도 내용상 같은 제목이라면 유연하게 [적절]로 판정해. 또한 증례기록서(CRF)에 연구과제명이 없다면 '필수 항목 누락'으로만 지적해. 서류상에 존재하지 않는 글자 중복(예: '및 재발' 중복 기재 등)이나 오타를 AI 임의로 지어내어(환각) 제목 불일치로 지적하면 절대 안 돼.
- 연구책임자 성명 교차 검증: 연구계획서의 '연구책임자' 성명과 증례기록서(CRF), 서약서, 동의면제 점검표, 이력서 등 다른 서류에 기재된 '연구책임자' 성명이 완벽히 일치하는지 대조해. 
  ★[다기관 연구 PI 예외 처리 - 매우 중요]: 다기관 연구의 경우 연구계획서 상의 총괄 '연구책임자'가 타 병원 소속일 수 있어. 이 경우 본원(김안과병원)에 제출하는 서약서, 이력서, CRF 등의 '연구책임자'는 계획서에 기재된 타 병원 책임자가 아니라, 계획서 명단 중 '김안과병원' 소속으로 기재된 연구자가 되어야 해. 계획서의 총괄 책임자 이름과 본원 서류의 책임자 이름이 다르다고 보완을 지적하지 말고, 본원 서류들에 김안과병원 소속 연구자가 책임자로 일관되게 기재되어 있다면 [적절]로 판정해.
- 연구자 명단 교차 검증: 서약서, 동의면제 점검표의 연구진 명단이 연구계획서 명단과 일치하는지 꼼꼼히 대조해. 
  ★[단일기관 연구 명단 검증]: 타 병원 참여 없이 본원 단독인 경우, 양쪽 서류의 전체 연구진 명단(인원수 및 성명)이 완벽히 일치해야 해.
  ★[다기관 연구 명단 검증 (매 중요)]: 다기관 연구이더라도 타 병원 소속 연구자는 무시하되, **연구계획서에 기재된 '김안과병원(망막병원, 각막센터 등 원내 센터 포함) 소속' 연구진 명단은 서약서에 적힌 명단과 완벽히 일치해야 해.** 예를 들어 계획서에 '박상민(망막병원)'이 있다면 서약서 공동연구자 명단에도 반드시 '박상민'이 기재되어야 해. 누락 시 무조건 [보완]으로 판정해.
  ★[명단 불일치 시 보완 출력 문구]: "연구계획서에 기재된 (본원 소속) 연구자 명단과 연구자 서약서(또는 동의면제 점검표)의 명단이 일치하지 않습니다. 누락되거나 추가된 연구자가 없도록 교차 확인 후 서류 간 명단을 동일하게 통일해 주시기 바랍니다."
  ★[단독 연구 및 특정 역할 부재 시 절대 주의]: 단독 연구이거나 해당 역할이 아예 없는 연구일 경우, 연구자 서약서 양식의 공동연구자, 연구코디네이터, 관리약사 칸이 완전히 비어있는(공란) 상태는 완벽한 정상(적절)이야. 계획서에 없는 인원을 서약서에 채워 넣으라며 지적하지 마. 
  ★[텍스트 밀림 주의]: PDF 문서의 표를 인식할 때 빈칸(예: 코디네이터 칸)으로 인해 텍스트가 밀려 읽히는 오류가 잦아. 문서 간에 '직책/역할'이 다르게 인식되더라도 지적하지 말고 성명과 인원수만 일치하면 [적절]로 판정해.

2. 연구자 및 기본 정보 점검 (연구계획서)
- 소속 및 직함: 연구책임자, 공동연구자 및 연구담당자의 소속 확인 (단순 안과는 보완 필요 판정. 각막센터, 망막병원, 녹내장센터, 사시소아안과센터, 성형안과센터, 수련부, 임상연구센터 중 하나 필수). 직함에 '교수' 사용 시 보완 필요 판정 (전문의, 전공의, 센터장, 부원장, 원장만 허용). 단, 타기관 연구자는 이 룰을 적용하지 않음.
- 연구 기간: "IRB승인일로부터 ~ 1년" 또는 "IRB승인일로부터 ~ YYYY년 MM월 DD일까지" 형식 확인.

3. 연구 대상자 점검 (연구계획서)
- 선정 기준: "김안과병원에서" 또는 "본원에서"라는 문구 포함 및 대상 기간 명시 확인해줘. (다기관 연구의 경우 이 문구가 없어도 적절. ★단, '증례 보고(증례 연구)' 형태인 경우에는 특정 대상 기간이 명시되어 있지 않더라도 무조건 [적절]로 판정해.)
- 대상자 수: 대상자 수 및 근거 기재 확인 ("후향적 연구로 해당사항 없음" 등은 적절).

4. 평가 항목 및 개인정보 보호 (연구계획서)
- 논리적 일관성 검증 (복사/붙여넣기 오류 및 항목 간 불일치 탐지): 
  1) ★연구의 배경 vs 연구의 목적 일치 여부: '연구의 배경'에서 설명하고 있는 대상 질환, 치료법, 약물 등의 핵심 주제가 '연구의 목적'에서 밝힌 내용과 일치하는지 1:1로 정밀 교차 검토해. 배경에서는 'A 질환(또는 A 약물)의 위험성'을 설명해 놓고, 정작 목적에는 'B 질환(또는 B 약물)의 유효성을 본다'고 적혀 있는 등 앞뒤가 맞지 않는 모순이 있다면 무조건 [보완] 판정을 내려. 상세 내용에는 "연구계획서의 '연구의 배경'에서 다루는 내용과 '연구의 목적'에 기재된 핵심 주제가 서로 일치하지 않습니다. 타 연구 서식을 복사·붙여넣기 하는 과정에서 잘못 수정된 부분이 없는지 확인 후 수정하여 주시기 바랍니다."라고 명확히 지적해.
  2) 전체 문맥: 연구계획서 내 '연구의 배경 및 목적', '평가 항목', '통계 분석' 내용이 전체적으로 하나의 연구 주제를 향해 논리적으로 연결되는지 검토해. 제목은 'A 질환'인데 본문 어딘가에 'B 질환' 내용이 뚱딴지같이 섞여 있는 등 명백한 복붙 흔적이 있으면 [보완] 판정을 내려.
  3) ★평가 항목 vs 해석(분석) 방법 일치 여부: '평가 항목(수집 항목)'에 명시되지 않은 엉뚱한 데이터를 '통계 분석(해석 방법)'에서 분석하겠다고 기재한 모순이 있는지 반드시 교차 대조해. (예: 평가 항목에는 '안압'만 적혀 있는데, 통계 분석에는 '시력의 변화를 분석한다'고 기재된 경우). 이처럼 수집하지 않은 항목을 분석한다고 기재한 경우 [보완] 판정을 내리고, 상세 내용에 "연구계획서의 '평가 항목(수집 변수)'에 기재되지 않은 항목이 '분석 및 해석 방법'에 포함되어 있습니다. 평가 항목과 분석 방법이 일치하도록 내용을 교차 확인 후 수정하여 주시기 바랍니다."라고 정중히 지적해.
- 효과 평가기준, 평가방법 및 해석방법: 연구계획서에 기재된 평가지표, 통계분석 방법(검정 방법, 통계 프로그램 등), 유의수준 기준이 누락 없이 구체적으로 기술되어 있는지 확인해. ★[예외 사항]: 단, 해당 연구의 디자인이 **'증례 보고(Case Report)'** 또는 **'증례군 연구(Case Series)'**인 경우에는 구체적인 통계 분석 방법(검정 방법, 통계 프로그램 등)이나 유의수준 기준이 필요하지 않아. 따라서 증례보고 연구에서 통계 관련 내용이 생략되어 있더라도 절대 [보완]으로 지적(환각)하지 말고 유연하게 [적절]로 판정해 넘어가 줘.
- 개인정보 대책: '대상자 식별정보 익명화/ID 코드화', '잠금장치 보관/암호화', '학술 목적 외 사용 금지' 항목이 잘 포함되어 있는지 확인해줘. ★[보관 기간 오진 절대 주의]: 생명윤리법상 연구 종료 후 최소 3년간 보관해야 하므로, 계획서에 '3년', '5년' 등 3년 이상의 보관 기간이나 폐기 계획이 명시되어 있다면 완벽히 적절한 상태야. 문서에 '보관 기간은 5년' 등으로 3년 이상 보관한다고 이미 적혀있음에도 불구하고, '최소 3년'이라는 특정 문구가 없다는 이유로 하단 **[행정 권고사항]**에 "3년간 보관 문구를 추가하라"고 오진(환각)하여 출력하면 절대 안 돼. 보관 기간에 대한 언급이 아예 없거나 3년 미만인 경우에만 해당 권고사항을 출력해.
- 증례기록서(CRF) 점검: 제목/평가항목 일치 여부를 대조해. 연구계획서상의 수집 항목과 CRF의 수집 항목이 상호 간에 명확히 동일하게 작성되어 부합하는지, ★반드시 양방향으로★ 대조해 가며 검토해줘.
  1) [연구계획서 → CRF] 연구계획서 '평가 항목(수집 변수)' 목록의 각 항목이 CRF에 실제로 존재하는지 확인.
  2) [CRF → 연구계획서] CRF에 기재된 각 수집 항목이 연구계획서 '평가 항목' 목록에도 실제로 존재하는지 확인. 이 방향도 1)과 동일한 비중으로 빠짐없이 점검해.
  ★[매번 실제 문서 재확인 - 절대 준수]: 아래 나오는 모든 예시(안축장=AL, 총주사횟수, 나이/성별 등)는 '매칭 방식을 설명하기 위한 예시'일 뿐, 특정 항목명을 결과와 무관하게 항상 [적절]로 자동 처리하라는 뜻이 아니야. 예시로 든 항목이라도, 이번에 업로드된 연구계획서와 CRF의 실제 텍스트에 그 항목이 정말 존재하는지를 매번 새로 확인한 뒤 판정해. 과거에 봤거나 흔히 등장하는 항목이라는 이유로 확인을 생략하면 절대 안 돼.
  이때 의학적 약어(예: 안축장=AL, 우안/좌안=OD/OS, 편위안=RET/LET, 동공간 거리=환자PD/안경PD 등)나 유추 가능한 데이터(예: 유병기간 = 초진일~수술일)는 일치하는 것으로 유연하게 인정하여 [적절] 판정해. 
  ★[한글-영문 시점/용어 동의어 인정 - 매우 중요]: 연구계획서는 한글로, CRF는 영문 약어나 코드값으로 표기되는 경우가 매우 흔하므로 아래와 같은 표현들은 반드시 동일한 항목으로 간주하고 [적절] 판정해:
    · '초진' = 'baseline' = '베이스라인' = 'initial' (예: '초진 subfoveal choroidal thickness' = 'baseline subfoveal choroidal thickness')
    · 'N개월' = 'N month' = 'monthN' (예: '3개월' = '3month' = 'month 3')
    · '대칭안 구분(OD/OS)' = CRF에 'OD/OS'라는 글자 자체가 없더라도, 'OD=0, OS=1'처럼 좌/우안을 0과 1 등의 코드값으로 구분하여 기재하는 열이 있다면 이를 동일 항목으로 인정.
    · 항목명이 완전히 동일한 문자열로 CRF에 그대로 존재한다면 당연히 [적절]이며, 표의 열 간격이 좁아 글자가 흐릿하거나 다른 열과 겹쳐 보인다는 이유로 '누락'으로 오판하지 않도록 각 페이지 이미지를 충분히 확대해서 보듯이 정밀하게 재확인해. (단, '실제로 그 항목이 두 문서 모두에 있는지'는 매번 다시 확인해야 하며, 특정 항목명이기 때문에 무조건 통과시키는 것은 아님.)
  ★[텍스트 vs 이미지 우선순위 - 절대 준수]: 각 문서 페이지마다 "[문서명 - N페이지의 실제 추출 텍스트]"라는 라벨과 함께 PDF 원본에서 그대로 뽑아낸 텍스트가 함께 제공돼. 이 텍스트는 이미지를 보고 눈으로 인식(OCR)한 결과가 아니라 문서에 실제로 저장되어 있는 글자 그 자체이므로 100% 정확한 정답이야. 어떤 항목이 CRF 또는 연구계획서에 '있는지 없는지'를 판단할 때는 반드시 이 추출 텍스트를 1차 기준으로 삼아 단어가 그 안에 존재하는지 검색부터 해. 이미지만 보고 "흐릿해서 안 보인다"거나 "다른 글자로 보인다"는 이유로, 추출 텍스트에 분명히 존재/부재하는 사실과 다르게 판정하는 것은 명백한 오진이니 절대 하지 마.
  ★[CRF 표 텍스트 밀림 및 줄바꿈 환각 절대 주의]: PDF 문서 특성상 표 안의 글자가 줄바꿈되어 '맥락막 혈관'과 '의 직경', '맥락막'과 '두께', 또는 '최종 추적'과 '관찰'처럼 단어가 쪼개지거나, 병합된 헤더 셀 때문에 인접한 두 열의 제목 글자가 서로 붙어(예: "맥락막 두께ChoriocapillarisSattler's layer 면적"처럼) 인식되는 경우가 매우 빈번해. 이는 특정 단어 하나에 국한된 문제가 아니라 CRF 문서 전반에서 반복적으로 나타나는 표/헤더 인식 오류이므로, 아래 절차를 예외 없이 반드시 지켜:
    1) 위 1), 2) 두 방향 각각에 대해, '일치'로 판단하기 전에 상대 문서 전체(모든 페이지, 모든 헤더 행·병합 셀 포함)를 다시 한 번 스캔하여 해당 단어(또는 그 단어를 구성하는 음절들이 인접 셀에 쪼개져 붙어 있는 형태)가 어디에라도 존재하는지 확인해.
    2) 표의 특정 칸에서 순서·위치가 예상과 다르게 보이거나, 다른 항목명과 글자가 붙어서 보이더라도, 그 단어(또는 음절 조합)가 문서 내 어딘가에 시각적으로 존재하기만 하면 절대 '누락'이나 '불일치'로 판정하지 말고 [적절]로 처리해.
    3) '누락'으로 판정하려는 경우, AI는 스스로에게 "이 항목이 표의 병합된 헤더 셀이나 줄바꿈으로 인해 다른 글자와 붙어서 표시된 것은 아닌가?"를 반드시 재확인한 뒤에만 최종적으로 [보완]을 출력해.
  CRF 또는 연구계획서에 실제로 없는 항목을 있다고 환각(Hallucination)하여 지적하지 말고, 문서에 적힌 텍스트만 정확히 확인해.
- 증례기록서(CRF) 직접 식별정보 노출 점검: 증례기록서 양식 내에 연구대상자를 직접 식별할 수 있는 민감한 개인정보 항목(예: '이름', '성명', '주민등록번호', '생년월일(YYYY-MM-DD 전체)', '등록번호', '병원등록번호', '환자번호(단순 차트번호)', '주소', '전화번호', '연락처' 등)을 기재하는 칸이 존재하는지 가장 엄격하게 스캔해. 
만약 해당 단어들이 수집 항목으로 발견된다면 무조건 [보완] 판정을 내리고, 상세 내용에 "증례기록서(CRF)에 수집이 금지된 직접 식별정보('[발견된 식별정보 단어]') 기재란이 포함되어 있습니다. 이름, 주민등록번호, 병원등록번호, 상세 주소 등의 식별정보 수집 항목을 완전히 삭제하고, 익명화된 '연구대상자 식별코드(ID)'나 '나이/성별' 등으로 대체하여 양식을 수정해 주시기 바랍니다."라고 단호하게 지적해. 
(★[생년월일 오진 및 날짜 표기 예외 사항]: 환자 보호를 위해 비식별화된 데이터인 '이니셜', '나이', '성별', '연구용 식별코드' 그리고 특정 일(Day)이 제외된 **'생년월(YYYY/MM, Year/Month of Birth)' 또는 '출생연도(YYYY)'**는 수집 가능한 합법적 정상 항목이므로 절대 지적하지 마. ★단, 생년월일이 아닌 '초진일', '수술일', '추적관찰일' 등 일반적인 임상 이벤트 날짜 데이터는 'YYYY/MM/DD' 전체 형식으로 기재하는 것이 완벽한 정상이므로 식별정보 노출로 오진하여 지적(보완)하지 마.)
★[나이/성별 예외의 적용 범위 한정 - 매우 중요]: 위 '이니셜/나이/성별' 관련 면제 규정은 오직 '직접 식별정보 노출 점검' 항목에만 적용되는 예외야. 위쪽의 '증례기록서(CRF) 점검(항목 일치 여부)'에서는 이 면제와 무관하게, 나이·성별도 다른 항목들과 동일하게 두 문서 모두에 실제로 존재하는지 정상적으로 대조해서 판정해야 해.

5. [서식 4] 연구대상자 동의면제 점검표 상세 확인 (제출된 경우)
- 점검자 자격 및 점검일(6개월 이내) 유효성 확인.
- 1페이지 1번 문항 세부 항목 4개 및 하단 결론 '예'에 체크박스 표시(■, ☑) 확인.
- 1페이지 '예' 체크 시, 2페이지 전체는 반드시 어떠한 체크 표시도 없는 공란이어야 함.

6. 연구자 서약서 세부 점검
- 1페이지 윤리준수, 2페이지 이해상충 마지막 행 체크 여부 확인.
- 3페이지 모니터링 계획 점검 로직:
  1) 1)번 항목에서 '최소위험 이하'에 체크(■, ☑, V표시 등)가 되어 있는지 확인해.
  2) 만약 '최소위험 이하'에 체크되어 있다면, 하단의 2)번(모니터링 계획)과 3)번(DSMB: 예/아니오/해당없음) 항목의 모든 박스들은 단 하나도 체크되지 않은 모두 텅 빈 공란(☐) 상태여야 완벽한 정상(적절)이야. 
  3) ★[체크박스 인식 환각 및 억지 보완 절대 금지]: AI가 텅 빈 네모 박스 '☐ 해당없음'을 보고, 체크(☑)가 되어 있다고 착각(환각)하여 "해당없음에 체크되어 있으니 해제하라"고 엉뚱한 보완을 내리는 치명적 오류가 발생하고 있어. 박스 안에 명확한 검은 색칠(■)이나 V 표시(☑)가 없다면 무조건 '빈 박스(☐)'야. 1번에 '최소위험 이하'가 체크되어 있고 3번이 비어있다면 완벽하므로, 절대 환각을 일으켜서 보완 지적을 하지 마.
  4) 2)번 항목에서 '자체 모니터링'에 실제로 체크(■, ☑)가 명확히 되어 있는 경우에 한해서만 괄호 안의 개월 수 기재 여부를 확인하고 계획서와 교차 검증해. '자체 모니터링'에 체크되지 않았다면(☐) 개월 수를 요구하지 마.

7. 연구비 산정서 점검 (제출된 경우만)
- ★[표 숫자 및 기호 인식 절대 주의사항]: 연구비 산정서 표를 읽을 때, 금액란이 비어있는 빈칸이거나 하이픈('-') 기호가 적혀 있다면 무조건 '0원'으로 취급해. (예: 의약품 관리료에 '-'가 있다면 3% 초과가 아니라 0원이므로 [적절]한 것임). 절대 다른 칸의 숫자를 임의로 끌어다 붙이는 환각을 일으키지 마.
- 각 항목별 금액(1~8번 항목 등)을 정확히 인식한 후, 아래 세 가지 수학적 검증을 수행해:
  1) 덧셈 검증: 직접비 세부 항목들의 합이 표에 적힌 '직접비 합계'와 일치하는지 확인해.
  2) 비율 검증: 인건비(직접비의 50% 이내), 회의비(직접비의 10% 이내), 의약품/의료기기 관리료(직접비의 3% 이내)가 한도 내인지 계산해.
  3) ★간접비(SIT/IIT) 요율 및 '지원기관' 표기 검증: 표 상단의 '의뢰기관' 칸을 읽고 연구 형태를 분류해.
     - [기본 IIT]: '의뢰기관'이 공란이거나 '건양의료재단', '김안과병원'인 경우 간접비는 직접비의 15%야.
     - [기본 SIT]: '의뢰기관'에 제약회사 등 외부 기관명이 있고, 간접비가 18%로 산정되었다면 적절해.
     - ★[IIT 외부 지원 예외 처리 - 매우 중요]: '의뢰기관' 칸에 외부 제약사 명칭(예: 한국산텐제약)이 적혀있음에도 불구하고, 간접비가 직접비의 15%(연구자 주도 기준)로 계산되어 있거나 비고란에 'IIT'라고 명시된 경우가 있어. 이 경우 무작정 18%로 수정하라고 지적하지 마! 대신 표의 '구분'을 '연구비 산정서 점검'으로 지정하고 [보완] 판정을 내린 뒤 다음과 같이 정중히 안내해:
       "제출하신 산정서의 의뢰기관 란에 제약사 등 외부 기관 명칭이 기재되어 있으나, 간접비는 연구자 주도(IIT) 기준인 15%로 산정되어 있습니다. 만약 본 연구가 의뢰자 주도(SIT)가 아닌, 외부 기관으로부터 연구비 '지원'만 받는 연구자 주도 연구(IIT)라면, 혼선을 방지하기 위해 의뢰기관 란에 '지원기관 : OOO제약'과 같이 명확히 기재하여 주시기 바랍니다. (의뢰자 주도 연구(SIT)인 경우 간접비를 18%로 재산정해 주시기 바랍니다.)"
- 마지막으로 '총합계'가 (직접비 + 간접비 + 관리료 + 심의비 등 추가 명시된 비용)의 합과 정확히 일치하는지 대조해.

8. 연구책임자 이력서 점검
- 성명 일치: 이력서에 기재된 성명이 연구계획서 등 다른 서류의 '연구책임자(또는 책임연구자)' 이름과 정확히 일치하는지 대조해. 불일치 시 [보완] 판정.
- 교육 이수: 이력서 문서 내에 'GCP' 또는 '생명윤리'라는 단어가 단 하나라도 존재하고, 동시에 '{prev_year}' 또는 '{current_year}'이라는 연도 숫자가 단 하나라도 존재한다면, AI는 더 이상 어떠한 논리적 판단이나 날짜 계산도 하지 말고 무조건 [적절]로 판정해. 
  ★[절대 지적 금지]: 표의 칸이 나뉘어 있든, 두 글자가 멀리 떨어져 있든 상관없이 저 두 가지 키워드(GCP/생명윤리 + {prev_year}/{current_year})가 모두 문서에 있기만 하면 완벽한 정상이야. 교육 이수와 관련해서는 절대로 [보완] 지적을 출력하지 마.
- 서명란 점검: 이력서 서식에 '(인)' 또는 '(서명)' 란이 존재할 때, 실제 **자필 서명(펜 글씨 이미지)**이나 **도장 이미지**가 시각적으로 포함되어 있지 않고 단순히 '홍길동 (인)' 처럼 컴퓨터 타이핑 텍스트만 적혀있다면 이는 서명이 누락된(비어있는) 것으로 간주하여 무조건 [보완] 판정해. 이름이 텍스트로 타이핑되어 있다고 해서 서명된 것으로 착각(환각)하면 절대 안 돼. 상세 내용에는 "이력서 하단 서명란에 실제 자필 서명(또는 도장)이 누락되어 있습니다. 자필 서명이 기재된 서류를 제출하시거나, 서명이 불필요한 경우 이력서 양식에서 서명란 '(인)' 항목 자체를 삭제해 주시기 바랍니다."라고 안내해.
- 공란 방치 점검: 이력서 작성 형식은 자유이나, 기재되지 않은 항목(빈칸/공란)이 방치되어 있다면 [보완] 판정해. ★[이력서 텍스트 밀림 주의]: PDF 변환 시 'ID Number'나 'Licensed in State' 같은 항목명과 실제 기재된 데이터(예: 78961, Seoul/South Korea 등)가 서로 떨어져서 인식되는 경우가 매우 많아. 문서 내에 관련 데이터가 존재한다면 절대 공란으로 오진(환각)하여 지적하지 마.

9. [서식 11] 심의면제 자가점검표 상세 확인 (제출된 경우, 서식 4와는 별개의 서류)
- 기본 정보 검증:
  1) 표지에 기재된 '연구과제명'과 '연구책임자' 성명이 연구계획서·서약서 등 다른 서류와 완벽히 동일한지 대조해.
  2) '점검자'는 연구자 서약서 또는 연구계획서에 기재된 연구진(연구책임자, 공동연구자, 연구담당자 등) 중 1명이어야 해. 명단에 없는 제3자 이름이 점검자로 기재되어 있다면 [보완] 판정하고, "심의면제 자가점검표의 점검자('[기재된 이름]')가 연구계획서/서약서상의 연구진 명단에서 확인되지 않습니다. 점검자는 반드시 해당 연구의 연구책임자, 공동연구자, 또는 연구담당자 중 1명이어야 합니다."라고 지적해.
  3) '점검일'이 오늘 날짜 기준 최근 6개월 이내인지 확인해. 6개월을 초과했다면 [보완] 판정하고 재점검 및 점검일 갱신을 요청해.

- 1페이지 질문1 체크 여부 확인:
  ★[체크박스 인식 환각 및 억지 보완 절대 금지]: 아래 모든 체크 여부 판단은 연구자 서약서 점검과 동일한 기준을 적용해. 박스 안에 명확한 검은 색칠(■)이나 V 표시(☑)가 없다면 무조건 '빈 박스(☐)'로 간주하고, 색칠되지 않은 빈 박스를 체크된 것으로 착각(환각)하여 지적하지 마.
  1) 질문1의 '예'/'아니오' 중 정확히 1개에만 체크(■, ☑)가 되어 있는지 확인해. 둘 다 비어있거나 둘 다 체크되어 있으면 [보완] 판정하고 "질문1에 '예' 또는 '아니오' 중 하나에만 명확히 체크해 주시기 바랍니다."라고 지적해.

- 질문1 '예' 체크 시 후속 로직 (아래 순서대로 판정):
  1) 질문2 '선택1'의 2개 박스(①일반대중 공개정보/개인식별정보 미수집, ②취약한 연구대상자 미포함)와 질문3(항목Ⅳ/Ⅴ/Ⅵ) 체크 상태를 먼저 전체 스캔해.
  2) ★[상호 배타 규칙 - 매우 중요] 질문2 '선택1'에 하나라도 체크가 되어 있다면, 질문3(항목Ⅳ, Ⅴ, Ⅵ)에는 절대 어떠한 체크도 있으면 안 돼. 반대로 질문3에 체크가 있다면 질문2 '선택1'에는 어떠한 체크도 있으면 안 돼. 두 질문에 동시에 체크가 섞여 있다면 [보완] 판정하고 "질문2(인간대상연구)와 질문3(인체유래물연구)에 중복으로 체크되어 있습니다. 연구 유형에 맞는 질문 하나에만 답변해 주시기 바랍니다."라고 지적해.
  3) [질문2 경로] 선택1의 2개 박스가 모두 체크되어 있다면 → 선택2(항목Ⅰ/Ⅱ/Ⅲ) 중 정확히 1개에 체크가 되어 있는지 확인해.
     - 선택2 중 1개에 체크 → [적절]
     - 선택2 어디에도 체크가 없음 → [보완] 판정하고 "심의면제 미해당으로 점검표 제출이 필요하지 않습니다."라고 안내해.
     - 선택2에 2개 이상 체크 → [보완] 판정하고 "선택2(항목Ⅰ/Ⅱ/Ⅲ)는 반드시 1개만 체크해 주시기 바랍니다."라고 지적해.
  4) [질문2 경로] 선택1의 2개 박스 중 1개에만 체크되어 있다면(둘 다는 아님) → [보완] 판정하고 "심의면제 미해당으로 점검표 제출이 필요하지 않습니다."라고 안내해. (이 경우 선택2는 확인할 필요 없음)
  5) [질문3 경로] 항목Ⅳ, Ⅴ, Ⅵ 중 1개에 체크가 되어 있다면 → [적절].
  6) [질문3 경로] 항목Ⅳ, Ⅴ, Ⅵ 어디에도 체크가 없다면 → [보완] 판정하고 "심의면제 미해당으로 점검표 제출이 필요하지 않습니다."라고 안내해.
  7) 질문2 선택1, 질문3 둘 다 아무 체크도 없는 경우(응답 자체를 안 한 경우) → [보완] 판정하고 "질문2 또는 질문3 중 해당하는 연구 유형에 답변이 되어 있지 않습니다. 인간대상연구라면 질문2를, 인체유래물연구라면 질문3을 작성해 주시기 바랍니다."라고 지적해.

- 질문1 '아니오' 체크 시: 심의면제 대상이 아니므로, 후속 질문(질문2, 질문3)의 체크 여부와 무관하게 [보완] 판정하고 "질문1에서 '아니오'로 체크되어 있어 심의면제 대상이 아닙니다. 이 경우 심의면제 자가점검표를 제출하지 않고 정식 심의를 신청해 주시기 바랍니다."라고 안내해.
"""

if uploaded_files:
    # 붉은 테두리 버튼 디자인 세팅 유지
    st.markdown("""
    <style>
    div.stButton > button {
        border: 2.5px solid #d32f2f !important; 
        transition: all 0.3s ease; 
    }
    div.stButton > button, div.stButton > button p {
        font-weight: 500 !important; 
        font-size: 16px !important;
        color: #000000 !important; 
    }
    div.stButton > button:hover {
        background-color: #fff5f5 !important;
        border: 2.5px solid #ff0000 !important;
        color: #000000 !important;
    }
   
    </style>
    """, unsafe_allow_html=True)
    
    # 버튼을 누르면 AI 결과를 받아와 금고(session_state)에 집어넣습니다.
    if st.button("🚀 AI 사전 행정검토 시작"):
        # 재검토 시작 시 이전 결과를 즉시 비워, 로딩 중 이전 결과가 잔류해 보이는 혼란을 방지합니다.
        st.session_state.ai_result = None

        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
        <style>
        @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-5px); } 100% { transform: translateY(0px); } }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .loading-container { animation: float 3s ease-in-out infinite; background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 25px; text-align: center; margin-bottom: 25px; }
        .custom-spinner { border: 3px solid rgba(59, 130, 246, 0.2); border-top: 3px solid #3b82f6; border-radius: 50%; width: 22px; height: 22px; animation: spin 1s linear infinite; margin-right: 10px; }
        .flex-center { display: flex; justify-content: center; align-items: center; margin-bottom: 5px; }
        </style>
        <div class="loading-container">
            <div class="flex-center">
                <div class="custom-spinner"></div>
                <div style="font-size: 20px; font-weight: bold; color: #31333F;">AI 행정간사가 서류를 정밀 검토하고 있습니다</div>
            </div>
            <div style="font-size: 15px; color: #64748b; margin-top: 8px;">(파일 용량에 따라 최대 5분 정도 소요되니 잠시만 기다려 주세요!)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <style>
            div[data-testid="stAlertContentError"] p {
                font-size: 12px !important;
            }
            </style>
            """, unsafe_allow_html=True)        
        try:
            import google.generativeai as genai
            import fitz  # PyMuPDF
            from PIL import Image
            import io

            try:
                server_api_key = st.secrets["GEMINI_API_KEY"]
            except (KeyError, FileNotFoundError):
                loading_placeholder.empty()
                st.error("⚠️ AI 검토 기능에 필요한 설정이 누락되어 있습니다. 관리자(IRB사무국)에게 문의해 주세요.")
                st.stop()

            today_str = datetime.date.today().strftime("%Y년 %m월 %d일")
            
            date_context = f"""
            \n[★날짜 판정 절대 지침★]
            - 기준이 되는 오늘 날짜는 정확히 '{today_str}' 입니다.
            - 서류에 기재된 점검일(예: 2026년 5월 13일)이 이 오늘 날짜('{today_str}')보다 이전이면 절대 미래 날짜가 아닌 '과거 날짜'입니다. 
            - 오늘 날짜와 서류 점검일을 정확히 대조하여 미래 날짜라고 오진하는 일이 절대 없도록 해줘.
            """
            
            genai.configure(api_key=server_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash') 
            
            ai_inputs = [SYSTEM_PROMPT + date_context]

            total_pages = 0
            for uploaded_file in uploaded_files:
                ai_inputs.append(f"\n[문서 파일명: {uploaded_file.name}]")
                pdf_bytes = uploaded_file.read()
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                total_pages += len(doc)

                # 페이지 수가 과도하게 많으면 AI 호출이 지나치게 무거워지므로 사전에 안내하고 중단
                if total_pages > MAX_TOTAL_PAGES:
                    loading_placeholder.empty()
                    st.warning(
                        f"⚠️ 업로드된 문서의 총 페이지 수({total_pages}페이지)가 너무 많습니다. "
                        f"한 번에 최대 {MAX_TOTAL_PAGES}페이지까지 검토 가능하니, 서류를 나누어 업로드해 주세요."
                    )
                    st.stop()

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # 증례기록서(CRF)처럼 열이 아주 많은 가로형 표는 dpi=150 고정 시
                    # 개별 칸의 글자(예: 총주사횟수, OD=0/OS=1 등)가 뭉개져 AI가 못 읽거나
                    # 엉뚱한 글자로 오독(예: '총경과관찰기간'→'호모크로늄')하는 문제가 있다.
                    # 페이지의 긴 변 길이에 따라 렌더링 dpi를 동적으로 높여 시각적 판독률을 올린다.
                    page_rect = page.rect
                    long_side_pt = max(page_rect.width, page_rect.height)
                    if long_side_pt > 1400:      # 매우 넓은 표(다열 CRF 등)
                        page_dpi = 260
                    elif long_side_pt > 900:      # A4/Letter 가로형보다 넓은 표
                        page_dpi = 200
                    else:                         # 일반 A4 세로형 문서
                        page_dpi = 150
                    pix = page.get_pixmap(dpi=page_dpi)
                    img_data = pix.tobytes("jpeg", jpg_quality=85)

                    # ★핵심 보완: 이미지(시각 인식)만으로는 좁은 칸에 빽빽하게 들어간
                    # CRF 표 헤더 글자를 놓치거나 다른 글자로 오독하는 사고가 반복된다.
                    # 이 PDF들은 스캔본이 아니라 텍스트가 그대로 내장된 문서이므로,
                    # PyMuPDF로 페이지의 '실제 텍스트'를 그대로 추출해 이미지와 함께 제공한다.
                    # 이렇게 하면 표 헤더 문자열(예: 총주사횟수, OD=0,OS=1 등)이 이미지 화질과
                    # 무관하게 100% 정확한 텍스트로 AI에게 전달되어 오독/누락 오진을 원천 차단한다.
                    try:
                        raw_text = page.get_text("text").strip()
                    except Exception:
                        raw_text = ""
                    if raw_text:
                        ai_inputs.append(
                            f"\n[{uploaded_file.name} - {page_num + 1}페이지의 실제 추출 텍스트 "
                            f"(★이 텍스트가 이미지 인식보다 우선하는 정답입니다. 아래 원문에 해당 단어가 "
                            f"존재하는지를 기준으로 '누락' 여부를 최종 판단해줘. 표 레이아웃이 깨져서 "
                            f"줄바꿈이 뒤섞여 보이더라도, 단어 자체가 이 텍스트 안에 존재하면 절대 "
                            f"'누락'으로 판정하지 마)]:\n{raw_text}\n"
                        )
                    ai_inputs.append(Image.open(io.BytesIO(img_data)))
            
            response = model.generate_content(ai_inputs)
            loading_placeholder.empty()

            # response.text에 바로 접근하면, 응답이 비어있는 경우(안전성 필터 차단, 토큰 초과 등)
            # 모호한 ValueError가 발생해 원인을 알 수 없는 "처리 중 오류"로만 보입니다.
            # candidate의 finish_reason을 먼저 확인해 원인별로 구체적인 안내를 제공합니다.
            candidates = getattr(response, "candidates", None)
            finish_reason = None
            if candidates:
                finish_reason = getattr(candidates[0], "finish_reason", None)
                finish_reason = getattr(finish_reason, "name", finish_reason)

            if not getattr(response, "parts", None):
                if finish_reason == "SAFETY":
                    st.error(
                        "⚠️ 제출하신 서류에 개인정보·의료정보 등 민감한 내용이 포함되어 있어 "
                        "AI 안전성 필터에 의해 검토가 차단되었습니다. 식별정보를 최소화한 뒤 다시 시도해 주세요."
                    )
                elif finish_reason == "MAX_TOKENS":
                    st.error(
                        "⚠️ 서류 분량이 많아 AI가 검토 결과를 모두 작성하지 못했습니다. "
                        "서류를 나누어 더 적은 분량으로 업로드한 뒤 다시 시도해 주세요."
                    )
                elif finish_reason == "RECITATION":
                    st.error("⚠️ 문서 내용 일부가 저작권 보호 콘텐츠로 인식되어 검토가 중단되었습니다. IRB사무국으로 문의해 주세요.")
                else:
                    st.error(
                        f"⚠️ AI가 검토 결과를 생성하지 못했습니다(원인: {finish_reason or '알 수 없음'}). "
                        f"잠시 후 다시 시도해 주시고, 문제가 계속되면 IRB사무국으로 문의해 주세요."
                    )
                print(f"[ERROR] AI 응답이 비어있음. finish_reason={finish_reason}, prompt_feedback={getattr(response, 'prompt_feedback', None)}")
                st.stop()

            # 생성된 결과를 금고에 안전하게 보관!
            st.session_state.ai_result = response.text
            
        except Exception as e:
            # st.stop()이 내부적으로 발생시키는 제어 흐름용 예외는 그대로 전파시켜,
            # 이미 표시된 안내 메시지(설정 누락/페이지 초과) 위에 일반 오류 메시지가 덧씌워지는 것을 방지합니다.
            if type(e).__name__ in ("StopException", "RerunException", "ScriptRunStopException"):
                raise
            loading_placeholder.empty()
            error_str = str(e)

            # Gemini API 할당량(429) 및 리소스 초과, 서버 장애(503) 에러 상세 분류
            if "429" in error_str or "quota" in error_str.lower() or "resourceexhausted" in error_str.lower():
                error_lower = error_str.lower()
                
                # 1. 일일 한도 초과 카메라에 걸린 경우 (RPD)
                if "per day" in error_lower or "perday" in error_lower:
                    st.error(
                        "⚠️ [일일 한도 초과] 오늘 무료로 사용할 수 있는 AI 검토 횟수를 모두 소진했습니다. "
                        "일반적으로 태평양시간 자정(한국 시간 오후~밤 사이) 즈음 초기화되지만, 정확한 리셋 시점은 "
                        "사용 패턴에 따라 달라질 수 있습니다."
                    )
                
                # 2. 분당 데이터 한도 카메라에 걸린 경우 (TPM)
                elif "tokens per minute" in error_lower or "bytes per minute" in error_lower:
                    st.error("⚠️ [데이터 과부하] 한 번에 너무 많은 페이지가 전송되었습니다. 1~2분 정도 기다리신 후 다시 시도하시거나, 서류를 조금 나눠서 올려주세요!")
                
                # 3. 분당 횟수 한도 카메라에 걸린 경우 (RPM)
                elif "requests per minute" in error_lower:
                    st.error("⚠️ [단기 횟수 초과] 짧은 시간에 너무 여러 번 검토를 요청했습니다. 약 1분 정도만 기다리신 후 다시 버튼을 눌러주세요.")
                
                # 4. 기타 원인 모를 한도 초과
                else:
                    st.error("⚠️ [일시적 사용량 초과] AI 서버에 데이터가 몰려 처리하지 못했습니다. 약 1~2분 후 다시 시도해 주세요.")

            # Google 서버 자체의 일시적 장애 (사용자/할당량 문제 아님)
            elif "503" in error_str or "unavailable" in error_str.lower() or "servererror" in error_str.lower():
                st.error(
                    "⚠️ [Google 서버 일시 장애] 현재 AI 서버 자체가 일시적으로 불안정한 상태입니다 (사용 한도 문제가 아닙니다). "
                    "잠시 후(약 1~2분) 다시 시도해 주세요."
                )

            else:
                # API 한도 문제가 아닌 진짜 시스템 오류일 때
                st.error("⚠️ 검토 처리 중 알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해 주시고, 문제가 계속되면 IRB사무국으로 문의해 주세요.")
            
            print(f"[ERROR] AI 검토 처리 중 예외 발생: {error_str}")

    # 금고에 AI 결과 데이터가 들어있다면 화면에 고정 출력합니다.
    if st.session_state.ai_result is not None:
        file_date_str = datetime.date.today().strftime("%Y%m%d")
        
        st.success("🎉 검토가 완료되었습니다!")
        st.subheader("📋 AI 사전 검토 결과")

        main_text, recommendations = split_recommendation_section(st.session_state.ai_result)
        # 💡 추가된 부분: 웹 화면 표 디자인(너비, 가운데 정렬 등) 강제 적용 CSS
        st.markdown("""
        <style>
        /* 표 전체 너비를 화면에 꽉 차게 */
        .stMarkdown table {
            width: 100% !important;
        }
        /* 제목 행(1행) 가운데 정렬 및 배경색 지정 */
        .stMarkdown th {
            text-align: center !important;
            background-color: #f8fafc !important;
            color: #0f172a !important;
            font-size: 15px !important;
        }
        /* 각 열의 너비 비율 강제 고정 (구분 열 넓게) */
        .stMarkdown th:nth-child(1) { width: 12% !important; }
        .stMarkdown th:nth-child(2) { width: 15% !important; }
        .stMarkdown th:nth-child(3) { width: 5% !important; }
        .stMarkdown th:nth-child(4) { width: 68% !important; }
        
        /* 3번째 '검토결과(보완)' 데이터도 가운데 정렬 */
        .stMarkdown td:nth-child(3) {
            text-align: center !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # 💡 수정된 부분: AI가 넣은 <br> 태그가 화면에서 실제 줄바꿈으로 작동하도록 unsafe_allow_html=True 추가
        st.markdown(main_text, unsafe_allow_html=True)

        # 💡 수정된 부분 2: 권고사항 UI를 st.info 대신 일체형 HTML 카드로 묶어서 출력
        if recommendations:
            recommendation_html = """
            <div style="background-color: #faf2f2; border: 1.5px solid #f28c85; border-radius: 10px; padding: 20px 25px; margin: 22px 2px; box-sizing: border-box;">
                <div style="color: #c44747; font-weight: bold; font-size: 18px; margin-bottom: 8px;">📌 행정 권고사항</div>
                <ol style="margin: 0; padding-left: 20px; color: #262121; line-height: 1.6;">
            """
            for item in recommendations:
                # html.escape를 통해 특수문자 안전하게 렌더링
                recommendation_html += f"<li>{html.escape(item)}</li>"
            recommendation_html += "</ol></div>"
            
            st.markdown(recommendation_html, unsafe_allow_html=True)
