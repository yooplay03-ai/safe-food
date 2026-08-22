import streamlit as st
import requests
import html
import urllib.parse
from datetime import datetime, timedelta


def render_html(s):
    """멀티라인 HTML/CSS 문자열을 안전하게 렌더링.
    Streamlit의 마크다운 렌더러는 4칸 이상 들여쓰기된 줄을 '코드블록'으로 오인해
    HTML 태그를 그대로 텍스트로 출력하는 문제가 있음 (Python 코드 들여쓰기가
    f-string에 그대로 들어가기 때문). 모든 줄의 들여쓰기를 제거해 이 문제를 막음."""
    cleaned = "".join(line.strip() for line in s.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def get_secret(key, default=""):
    """.streamlit/secrets.toml에 키가 있으면 그 값을, 없으면 default를 반환.
    사이드바 입력창의 기본값으로 써서, secrets.toml에 미리 채워두면
    매번 API 키를 다시 입력할 필요 없게 함 (그래도 화면에서 수정은 가능)."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


st.set_page_config(page_title="Safe-Food | 만성질환자 맞춤형 외식 안전 가이드", layout="wide", page_icon="🧳")

render_html("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --sf-pink: #EC4899;
  --sf-pink-deep: #DB2777;
  --sf-sky: #8B5CF6;
  --sf-sky-deep: #7C3AED;
  --sf-paper: #FFF8FC;
  --sf-card: #FFFFFF;
  --sf-ink: #1F1B2E;
  --sf-muted: #726C82;
  --sf-safe: #059669;
  --sf-caution: #B45309;
  --sf-warning: #DC2626;
  --sf-none: #6B7280;
  --sf-border: #F2DCE9;
}

/* 드롭다운/멀티셀렉트 팝업은 body 최상단에 별도로 렌더링되기 때문에,
   페이지 전체를 다크로 바꾸면 그 팝업 내부 글자가 안 보이는 문제가 생김.
   그래서 기본 배경은 밝게 유지하고, 컬러는 채도 있는 핑크/바이올렛으로 포인트만 줌. */
html, body, .stApp { background: var(--sf-paper) !important; color: var(--sf-ink); }
.stApp, .stApp p, .stApp span, .stApp label, .stApp li { font-family: 'Pretendard', -apple-system, sans-serif; }
[data-testid="stIconMaterial"], span[class*="material-symbols"], i[class*="material-symbols"] {
  font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}
[data-testid="stHeaderActionElements"] { display: none !important; }
[data-testid="stCaptionContainer"] { margin-bottom: 0.15rem !important; color: var(--sf-muted) !important; }

/* 배경에 은은하게 깔리는 핑크/바이올렛 글로우 (밝은 배경이라 아주 옅게) */
[data-testid="stAppViewContainer"]::before {
  content: ""; position: fixed; top: -10%; left: -10%; width: 55%; height: 55%;
  background: radial-gradient(circle, rgba(236,72,153,0.10) 0%, transparent 70%);
  pointer-events: none; z-index: 0;
}
[data-testid="stAppViewContainer"]::after {
  content: ""; position: fixed; bottom: -15%; right: -10%; width: 50%; height: 50%;
  background: radial-gradient(circle, rgba(124,58,237,0.09) 0%, transparent 70%);
  pointer-events: none; z-index: 0;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #FFF9FC 0%, #FBF5FF 100%);
  border-right: 1px solid var(--sf-border);
}
[data-testid="stSidebar"] * { color: var(--sf-ink) !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-weight: 800 !important; letter-spacing: -0.01em;
}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background: #FFFFFF !important;
  border-radius: 10px !important;
  border: 1.5px solid var(--sf-border) !important;
  color: var(--sf-ink) !important;
}
[data-testid="stSidebar"] input::placeholder { color: #B8A9C4 !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stExpander"] {
  background: #FFFFFF;
  border-radius: 12px !important;
  border: 1px solid var(--sf-border) !important;
}

h1, h2, h3 { font-family: 'Pretendard', sans-serif !important; color: var(--sf-ink); letter-spacing: -0.02em; font-weight: 800 !important; }
h2 { border-bottom: none; padding-bottom: 0.6rem; position: relative; }
h2::after {
  content: ""; display: block; margin-top: 0.6rem;
  height: 3px; width: 56px; border-radius: 999px;
  background: linear-gradient(90deg, var(--sf-pink) 0%, var(--sf-sky) 100%);
}

hr { border: none !important; height: 1px !important; margin: 2rem 0 !important;
  background: linear-gradient(90deg, transparent 0%, var(--sf-border) 20%, var(--sf-border) 80%, transparent 100%) !important; }

.stButton > button {
  background: linear-gradient(135deg, var(--sf-pink) 0%, var(--sf-sky) 100%) !important;
  color: white !important;
  border-radius: 999px !important;
  border: none !important;
  padding: 0.5rem 1.6rem !important;
  font-weight: 700 !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 4px 16px rgba(236,72,153,0.3);
}
.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 26px rgba(124,58,237,0.4);
}

[data-testid="stMetric"] {
  background: var(--sf-card);
  border: 1px solid var(--sf-border);
  border-radius: 14px;
  padding: 0.9rem 1rem;
  box-shadow: 0 4px 16px rgba(236,72,153,0.08);
}

[data-testid="stExpander"] { background: var(--sf-card); border-radius: 14px !important; border: 1px solid var(--sf-border) !important; overflow: hidden; }
[data-baseweb="notification"] { border-radius: 12px !important; }

@keyframes sfFadeInUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes sfDotPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(236,72,153,0.5); }
  50% { box-shadow: 0 0 0 5px rgba(236,72,153,0); }
}
@keyframes sfAvatarGlow {
  0%, 100% { box-shadow: 0 0 0 3px rgba(236,72,153,0.2), 0 4px 14px rgba(0,0,0,0.15); }
  50% { box-shadow: 0 0 0 7px rgba(236,72,153,0.05), 0 4px 14px rgba(0,0,0,0.15); }
}
@keyframes sfGlowFloat {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-3%, 3%); }
}

/* 사이드바 프로필 카드 - 채도 있는 다크 카드를 포인트로 (자체 완결형이라 팝업 이슈 없음) */
.sf-profile-card {
  background: linear-gradient(150deg, #241729 0%, #2E1A45 100%);
  border: 1px solid rgba(236,72,153,0.25);
  border-radius: 18px;
  padding: 1.1rem 1.2rem;
  margin: 0.8rem 0 1.2rem 0;
  box-shadow: 0 10px 28px rgba(236,72,153,0.22);
  animation: sfFadeInUp 0.55s ease both;
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}
.sf-profile-card:hover { box-shadow: 0 14px 36px rgba(124,58,237,0.3); transform: translateY(-2px); }
.sf-profile-card * { color: #F5EFFA !important; }
.sf-profile-label {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.66rem;
  letter-spacing: 0.16em; text-transform: uppercase;
  color: #F0A8CE !important; margin: 0 0 0.7rem 0;
}
.sf-profile-label .sf-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #EC4899; animation: sfDotPulse 1.8s ease-in-out infinite;
}
.sf-profile-row { display: flex; align-items: center; gap: 0.85rem; }
.sf-profile-avatar {
  flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; overflow: hidden;
  background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%);
  border: 2px solid rgba(236,72,153,0.5);
  animation: sfAvatarGlow 2.6s ease-in-out infinite;
}
.sf-profile-name {
  font-weight: 800; font-size: 1.1rem; margin: 0;
  background: linear-gradient(90deg, #F9A8D4 0%, #C4B5FD 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent !important;
}
.sf-profile-meta { font-family: 'IBM Plex Mono', monospace; font-size: 0.76rem; color: #C9BEDD !important; margin: 0.15rem 0 0 0; }

.sf-badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.32rem 0.85rem; border-radius: 999px;
  font-weight: 700; font-size: 0.9rem;
  font-family: 'IBM Plex Mono', monospace;
  border: 1px solid transparent;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.sf-badge:hover { transform: translateY(-1px) scale(1.03); }
.sf-badge-safe { background: rgba(5,150,105,0.1); color: var(--sf-safe); border-color: rgba(5,150,105,0.3); }
.sf-badge-caution { background: rgba(180,83,9,0.1); color: var(--sf-caution); border-color: rgba(180,83,9,0.3); }
.sf-badge-warning { background: rgba(220,38,38,0.1); color: var(--sf-warning); border-color: rgba(220,38,38,0.3); }
.sf-badge-none { background: rgba(107,114,128,0.1); color: var(--sf-none); border-color: rgba(107,114,128,0.25); }

.sf-food-card {
  background: var(--sf-card); border: 1px solid var(--sf-border); border-radius: 16px;
  padding: 1.25rem 1.5rem; margin-bottom: 1.25rem;
  box-shadow: 0 4px 20px rgba(236,72,153,0.08);
  transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.25s ease;
}
.sf-food-card:hover { box-shadow: 0 14px 34px rgba(124,58,237,0.16); transform: translateY(-3px); border-color: rgba(236,72,153,0.3); }
.sf-food-card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
.sf-food-name { font-size: 1.2rem; font-weight: 700; color: var(--sf-ink); margin: 0 0 0.15rem 0; }
.sf-food-sub { color: var(--sf-muted); font-size: 0.83rem; margin-bottom: 0.5rem; }
.sf-food-stats { font-family: 'IBM Plex Mono', monospace; font-size: 0.92rem; color: var(--sf-ink); margin: 0.4rem 0; }
.sf-caption { color: var(--sf-muted); font-size: 0.78rem; margin: 0.15rem 0; }
.sf-note { border-left: 3px solid var(--sf-caution); background: rgba(180,83,9,0.06); padding: 0.5rem 0.8rem; border-radius: 8px; font-size: 0.85rem; margin-top: 0.5rem; color: var(--sf-ink); }
.sf-note-danger { border-left: 3px solid var(--sf-warning); background: rgba(220,38,38,0.06); }

/* 히어로 - 밝은 배경 + 은은한 글로우 + 그라데이션 텍스트 */
.sf-hero {
  background: linear-gradient(160deg, #FFFFFF 0%, #FDF2F8 100%);
  border: 1px solid var(--sf-border);
  border-radius: 24px; padding: 2.4rem 2.6rem; color: var(--sf-ink);
  margin-bottom: 1.4rem; position: relative; overflow: hidden;
  box-shadow: 0 16px 44px rgba(236,72,153,0.14);
  animation: sfFadeInUp 0.6s ease both;
}
.sf-hero::before {
  content: ""; position: absolute; top: -30%; right: -15%; width: 55%; height: 130%;
  background: radial-gradient(circle, rgba(236,72,153,0.16) 0%, transparent 65%);
  animation: sfGlowFloat 8s ease-in-out infinite;
  pointer-events: none;
}
.sf-hero::after {
  content: ""; position: absolute; bottom: -40%; left: -10%; width: 45%; height: 110%;
  background: radial-gradient(circle, rgba(139,92,246,0.14) 0%, transparent 65%);
  animation: sfGlowFloat 9s ease-in-out infinite reverse;
  pointer-events: none;
}
.sf-hero-eyebrow {
  position: relative; z-index: 1;
  display: inline-flex; align-items: center; gap: 0.45rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--sf-pink-deep);
  background: rgba(236,72,153,0.08); border: 1px solid rgba(236,72,153,0.28);
  border-radius: 999px; padding: 0.35rem 0.9rem; margin-bottom: 1.1rem;
}
.sf-hero-eyebrow .sf-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--sf-pink); animation: sfDotPulse 1.8s ease-in-out infinite; }
.sf-wordmark {
  position: relative; z-index: 1;
  font-weight: 900; font-size: 2.7rem; letter-spacing: -0.03em; margin: 0;
  display: flex; align-items: center; gap: 0.5rem;
  background: linear-gradient(90deg, #1F1B2E 0%, var(--sf-pink) 55%, var(--sf-sky) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.sf-tagline { position: relative; z-index: 1; font-size: 1.02rem; color: var(--sf-muted); margin: 0.5rem 0 1.3rem 0; max-width: 34rem; }
.sf-legend { position: relative; z-index: 1; display: flex; gap: 0.6rem; flex-wrap: wrap; }

.sf-eyebrow { color: var(--sf-pink-deep) !important; }

@media (max-width: 640px) {
  .sf-hero { padding: 1.8rem 1.5rem; border-radius: 18px; }
  .sf-wordmark { font-size: 1.8rem; }
  .sf-tagline { font-size: 0.88rem; }
  .sf-legend { gap: 0.4rem; }
  .sf-legend .sf-badge { font-size: 0.78rem; padding: 0.26rem 0.65rem; }
  .sf-food-card { padding: 1rem 1.1rem; border-radius: 12px; margin-bottom: 1rem; }
  .sf-food-card-top { flex-direction: column; gap: 0.6rem; }
  .sf-food-card-top > div:last-child { text-align: left !important; width: 100%; }
  .sf-food-card-top > div:last-child p { max-width: 100% !important; }
  .sf-food-name { font-size: 1.1rem; }
  .sf-food-stats { font-size: 0.85rem; }
}
</style>
""")

render_html("""
<div class="sf-hero">
  <p class="sf-hero-eyebrow"><span class="sf-dot"></span>TRAVEL & HEALTH COMPANION</p>
  <p class="sf-wordmark">🧳 Safe-Food</p>
  <p class="sf-tagline">여행지에서도, 안심하고 드세요 — 만성질환자를 위한 외식 안전 가이드</p>
  <div class="sf-legend">
    <span class="sf-badge sf-badge-safe">🟢 안전</span>
    <span class="sf-badge sf-badge-caution">🟡 주의</span>
    <span class="sf-badge sf-badge-warning">🔴 경고</span>
  </div>
</div>
""")


def badge_html(grade):
    """등급(안전/주의/경고/None)을 '도장' 스타일 배지 HTML로 변환"""
    cls_map = {"안전": "sf-badge-safe", "주의": "sf-badge-caution", "경고": "sf-badge-warning"}
    icon_map = {"안전": "🟢", "주의": "🟡", "경고": "🔴"}
    cls = cls_map.get(grade, "sf-badge-none")
    icon = icon_map.get(grade, "⚪")
    label = html.escape(grade or "정보없음")
    return f'<span class="sf-badge {cls}">{icon} {label}</span>'


def section_eyebrow(number, label):
    """보딩패스 톤의 섹션 레이블 (예: GATE 01 · 건강 프로필) — 히어로와 톤을 통일"""
    render_html(f"""
    <p style="font-family:'IBM Plex Mono',monospace; font-size:0.75rem; letter-spacing:0.14em;
    color: var(--sf-pink-deep); margin: 1.2rem 0 -0.6rem 0;">GATE {number} · {html.escape(label)}</p>
    """)

# ============================================================
# 2. 질환별 숫자 기준 설계
#    ※ 이전 버전은 예시 수치를 그대로 썼지만, 이번엔 실제 임상 가이드라인의
#      "하루" 권장/제한량을 가져와서 1식(끼) 기준으로 환산함.
#      (1일 3식 가정: 주의=하루기준÷3, 경고=하루기준÷2)
#    출처:
#      - 나트륨(고혈압): 대한고혈압학회 2024 가이드라인, 하루 2,000mg 이하
#      - 당류(당뇨병): 대한당뇨병학회, 총열량의 10% 이내 (2,000kcal 기준 50g)
#      - 나트륨(신장질환): 대한신장학회 권고, 병기별 2,300/1,500/1,000mg
#      - 단백질(신장질환): 국제신장학회(KDIGO), 체중 1kg당 0.8g
# ============================================================
DISEASE_NUMERIC_NAMES = ["고혈압", "당뇨병", "신장질환"]

DAILY_TARGETS = {
    "고혈압_나트륨": {"daily": 2000, "unit": "mg", "출처": "대한고혈압학회(2024)"},
    "당뇨병_당류": {"daily": 50, "unit": "g", "출처": "대한당뇨병학회(총열량 10% 이내, 2,000kcal 기준)"},
}

CKD_SODIUM_BY_STAGE = {
    "1~2기(경증)": 2300,
    "3~4기(중등도)": 1500,
    "5기·투석(중증)": 1000,
}
CKD_PROTEIN_G_PER_KG = 0.8  # 국제신장학회(KDIGO) 권고

# 숫자 기준이 애매한 질환 → 음식명 키워드 기반 주의 플래그
KEYWORD_WARNINGS = {
    "염증성장질환(크론병·궤양성대장염)": {
        "keywords": ["튀김", "볶음", "매운", "곱창", "생채", "샐러드", "회", "탄산"],
        "msg": "자극적이거나 잔여물이 많은 음식일 수 있어요. 활성기(증상기)에는 특히 주의하세요."
    },
    "과민성대장증후군(IBS)": {
        "keywords": ["양파", "마늘", "밀", "라면", "빵", "우유", "크림", "콩"],
        "msg": "고포드맵(FODMAP) 식품이 포함될 수 있어요."
    },
    "역류성식도염/위염": {
        "keywords": ["튀김", "매운", "탄산", "커피", "초콜릿", "기름"],
        "msg": "위산 역류를 유발할 수 있는 자극적인 음식이에요."
    },
    "통풍": {
        "keywords": ["곱창", "간", "내장", "육회", "등뼈", "국물", "육수"],
        "msg": "퓨린 함량이 높을 수 있는 식품이에요. 육류 국물류는 특히 주의하세요."
    },
}

ALLERGY_KEYWORDS = {
    "갑각류": ["새우", "게", "랍스터", "가재"],
    "견과류": ["땅콩", "호두", "아몬드", "잣"],
    "우유":   ["우유", "치즈", "크림", "버터"],
    "밀(글루텐)": ["밀", "빵", "면", "라면", "튀김"],
    "계란":   ["계란", "달걀"],
}

# ============================================================
# 2-1. 질환별 "직원에게 물어볼 체크리스트"
#    ※ 식약처 DB에 메뉴가 없어도(동네 식당 등) 항상 도움이 되는 정보.
#      정확한 수치 대신, 외식 현장에서 바로 쓸 수 있는 실질적 질문 제공.
# ============================================================
CHECKLIST_QUESTIONS = {
    "고혈압": [
        "국물이나 소금 양을 줄여줄 수 있는지 물어보세요.",
        "젓갈·장아찌 등 밑반찬은 나트륨이 높으니 적게 요청하세요.",
    ],
    "당뇨병": [
        "밥 양을 조절하거나 잡곡밥으로 바꿀 수 있는지 물어보세요.",
        "양념장·소스는 따로 담아달라고 요청해보세요 (당류 조절 가능).",
    ],
    "신장질환": [
        "국물·찌개류는 적게 달라고 요청하세요.",
        "젓갈·장류 등 고나트륨 반찬을 빼달라고 요청해보세요.",
    ],
    "염증성장질환(크론병·궤양성대장염)": [
        "튀김 대신 삶거나 구운 조리로 바꿀 수 있는지 물어보세요.",
        "맵기 조절이 가능한지, 자극적이지 않은 메뉴가 있는지 확인하세요.",
    ],
    "과민성대장증후군(IBS)": [
        "양파·마늘을 빼줄 수 있는지 물어보세요.",
        "크림·유제품이 들어가는지 확인하세요.",
    ],
    "역류성식도염/위염": [
        "튀김보다 담백한 조리법으로 바꿔달라고 요청해보세요.",
        "카페인·탄산음료는 피하는 게 좋아요.",
    ],
    "통풍": [
        "사골·곰탕 등 진한 육수인지 확인하고, 국물은 적게 드세요.",
    ],
}

def get_checklist(diseases, ibd_active, category_text=None):
    """선택된 질환 + (있으면) 식당 업종 기준으로 '직원에게 물어볼 체크리스트' 생성.
    업종 힌트는 get_category_hint()(카카오 category_name 키워드 매칭)를 재사용해서
    같은 키워드 판단 로직을 두 곳에서 따로 관리하지 않도록 함.
    데이터 매칭 여부와 무관하게 항상 제공됨."""
    checklist = []
    for d in diseases:
        if d in CHECKLIST_QUESTIONS:
            for q in CHECKLIST_QUESTIONS[d]:
                tag = f"[{d}]"
                if d == "염증성장질환(크론병·궤양성대장염)" and ibd_active:
                    tag += " ⚠️활성기"
                checklist.append(f"{tag} {q}")
    if category_text:
        hint = get_category_hint(category_text)
        if hint:
            checklist.append(f"[업종 참고] {hint}")
    return checklist

# ============================================================
# 3. 사이드바 - 사용자 건강 프로필
# ============================================================
with st.sidebar:
    name_col, age_col = st.columns([1.3, 1])
    with name_col:
        user_name = st.text_input("이름 (선택)", placeholder="")
    with age_col:
        user_age = st.number_input("나이", min_value=1, max_value=120, value=25, step=1)

    # 기존 로직(저작·삼킴 안내 등)과의 호환을 위해 실제 나이를 연령대 버킷으로 변환
    if user_age < 20:
        age_group = "20대 이하"
    elif user_age < 40:
        age_group = "20~40대"
    elif user_age < 65:
        age_group = "40~65세"
    else:
        age_group = "65세 이상"

    name_html = (
        f'<p class="sf-profile-name">{html.escape(user_name.strip())}</p>'
        if user_name.strip() else ""
    )
    render_html(f"""
    <div class="sf-profile-card">
      <p class="sf-profile-label"><span class="sf-dot"></span>PROFILE</p>
      <div class="sf-profile-row">
        <div class="sf-profile-avatar">🧍</div>
        <div>
          {name_html}
          <p class="sf-profile-meta">{user_age}세 · {html.escape(age_group)}</p>
        </div>
      </div>
    </div>
    """)

    if age_group == "65세 이상":
        st.caption("🦷 저작·삼킴이 편한 메뉴를 우선 안내해 드려요.")

st.sidebar.markdown("**관리 중인 만성질환** (중복 선택 가능)")
disease_options = DISEASE_NUMERIC_NAMES + list(KEYWORD_WARNINGS.keys())
selected_diseases = st.sidebar.multiselect(
    "질환 선택",
    disease_options,
    default=["고혈압"]
)

# 염증성장질환 선택 시 세부 상태 체크
ibd_active = False
if "염증성장질환(크론병·궤양성대장염)" in selected_diseases:
    ibd_state = st.sidebar.radio(
        "현재 장 상태",
        ["관해기(안정)", "활성기(증상 있음)"],
        key="ibd_state"
    )
    ibd_active = (ibd_state == "활성기(증상 있음)")

# 신장질환 선택 시 병기(단계) 체크 — 병기에 따라 나트륨 제한이 크게 달라짐
ckd_stage = None
if "신장질환" in selected_diseases:
    ckd_stage = st.sidebar.radio(
        "만성콩팥병 병기(신장 기능 단계)",
        list(CKD_SODIUM_BY_STAGE.keys()),
        index=1,
        key="ckd_stage",
        help="정확한 병기는 사구체여과율(eGFR) 검사 결과를 참고하세요. 모르면 '3~4기(중등도)'를 기본값으로 둡니다."
    )

st.sidebar.markdown("**식품 알레르기** (중복 선택 가능)")
selected_allergies = st.sidebar.multiselect(
    "알레르기 선택",
    list(ALLERGY_KEYWORDS.keys())
)

st.sidebar.markdown("---")
st.sidebar.caption("💡 여러 질환을 선택하면, 가장 엄격한 기준으로 판정합니다.")

# ============================================================
# 3-1. 건강검진 수치 자가입력 (선택)
#    ※ 실제 개인 건강검진 결과 자동 연동(마이헬스웨이/CODEF 등)은
#      마이데이터 사업자 등록·심사가 필요해 이번 버전 범위 밖.
#      대신 사용자가 최근 검진 수치를 직접 입력하면
#      임상 가이드라인 기준(대한고혈압학회·당뇨병학회 등)으로 비교해줌.
# ============================================================
CLINICAL_REFERENCE = {
    "수축기혈압": {"unit": "mmHg", "정상": 120, "주의": 140, "출처": "대한고혈압학회"},
    "이완기혈압": {"unit": "mmHg", "정상": 80, "주의": 90, "출처": "대한고혈압학회"},
    "공복혈당":   {"unit": "mg/dL", "정상": 100, "주의": 126, "출처": "대한당뇨병학회"},
    "총콜레스테롤": {"unit": "mg/dL", "정상": 200, "주의": 240, "출처": "한국지질동맥경화학회"},
}

with st.sidebar.expander("🩺 건강검진 수치 입력 (선택)"):
    st.caption("최근 건강검진 결과가 있다면 입력해보세요. 자동 연동이 아닌 자가 입력 방식입니다.")
    checkup_input = {}
    checkup_input["수축기혈압"] = st.number_input("수축기 혈압 (mmHg)", min_value=0, max_value=250, value=0, step=1)
    checkup_input["이완기혈압"] = st.number_input("이완기 혈압 (mmHg)", min_value=0, max_value=200, value=0, step=1)
    checkup_input["공복혈당"] = st.number_input("공복혈당 (mg/dL)", min_value=0, max_value=500, value=0, step=1)
    checkup_input["총콜레스테롤"] = st.number_input("총콜레스테롤 (mg/dL)", min_value=0, max_value=500, value=0, step=1)
    height_cm = st.number_input("키 (cm)", min_value=0, max_value=250, value=0, step=1)
    weight_kg = st.number_input("몸무게 (kg)", min_value=0, max_value=250, value=0, step=1)


def judge_checkup_value(name, value):
    ref = CLINICAL_REFERENCE[name]
    if value <= 0:
        return None
    if value < ref["정상"]:
        return "정상", ref
    elif value < ref["주의"]:
        return "주의", ref
    else:
        return "위험", ref


checkup_results = {
    name: judge_checkup_value(name, val)
    for name, val in checkup_input.items()
    if val > 0
}

bmi = None
if height_cm > 0 and weight_kg > 0:
    bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)

if checkup_results or bmi:
    section_eyebrow("01", "HEALTH CHECK")
    st.header("🩺 건강검진 결과 비교")
    st.caption("※ 자동 연동이 아닌 자가 입력값이며, 임상 가이드라인 기준으로 비교한 참고 정보입니다. 정확한 진단은 의료진과 상담하세요.")

    cols = st.columns(max(len(checkup_results) + (1 if bmi else 0), 1))
    idx = 0
    grade_color = {"정상": "🟢", "주의": "🟡", "위험": "🔴"}

    for name, (grade, ref) in checkup_results.items():
        with cols[idx]:
            st.metric(name, f"{checkup_input[name]} {ref['unit']}")
            st.caption(f"{grade_color[grade]} {grade} (출처: {ref['출처']})")
        idx += 1

    if bmi:
        with cols[idx]:
            bmi_grade = "정상" if 18.5 <= bmi < 23 else ("주의" if bmi < 25 else "위험")
            st.metric("체질량지수(BMI)", bmi)
            st.caption(f"{grade_color[bmi_grade]} {bmi_grade} (아시아인 기준)")

    risky = [name for name, (grade, _) in checkup_results.items() if grade in ("주의", "위험")]
    if "수축기혈압" in risky or "이완기혈압" in risky:
        if "고혈압" not in selected_diseases:
            st.info("💡 혈압 수치가 기준보다 높아요. 사이드바에서 '고혈압'을 질환으로 선택하면 메뉴 분석 시 나트륨 기준이 더 엄격하게 적용돼요.")
    if "공복혈당" in risky:
        if "당뇨병" not in selected_diseases:
            st.info("💡 공복혈당 수치가 기준보다 높아요. 사이드바에서 '당뇨병'을 질환으로 선택하면 당류 기준이 더 엄격하게 적용돼요.")

    st.markdown("---")

# ============================================================
# 4. 선택된 질환 → 최종 기준치 계산
#    하루 권장/제한량을 1식(끼) 기준으로 환산: 주의=하루기준÷3, 경고=하루기준÷2
#    여러 질환이 겹치면 가장 엄격한(작은) 값을 채택
# ============================================================
def compute_limits(diseases, ckd_stage, weight_kg):
    limits = {}
    notes = []  # UI에 보여줄 계산 근거 문구

    def add_limit(nutrient, daily_target, source):
        caution = round(daily_target / 3)
        warning = round(daily_target / 2)
        if nutrient in limits:
            prev_c, prev_w = limits[nutrient]
            limits[nutrient] = (min(prev_c, caution), min(prev_w, warning))
        else:
            limits[nutrient] = (caution, warning)
        notes.append(f"{nutrient} — 하루 {daily_target}{'g' if nutrient in ('당류','단백질') else 'mg'} 기준 ({source}) → 1식 주의 {caution} / 경고 {warning}")

    if "고혈압" in diseases:
        t = DAILY_TARGETS["고혈압_나트륨"]
        add_limit("나트륨", t["daily"], t["출처"])

    if "당뇨병" in diseases:
        t = DAILY_TARGETS["당뇨병_당류"]
        add_limit("당류", t["daily"], t["출처"])

    if "신장질환" in diseases:
        stage = ckd_stage or "3~4기(중등도)"
        sodium_daily = CKD_SODIUM_BY_STAGE[stage]
        add_limit("나트륨", sodium_daily, f"대한신장학회 권고 · {stage}")

        if weight_kg and weight_kg > 0:
            protein_daily = weight_kg * CKD_PROTEIN_G_PER_KG
            protein_source = f"국제신장학회(KDIGO) · 체중 {weight_kg}kg 기준"
        else:
            protein_daily = 60 * CKD_PROTEIN_G_PER_KG
            protein_source = "국제신장학회(KDIGO) · 체중 미입력으로 60kg 가정"
        add_limit("단백질", protein_daily, protein_source)

    return limits, notes

active_limits, limit_notes = compute_limits(selected_diseases, ckd_stage, weight_kg)

if active_limits:
    with st.sidebar.expander("🔧 적용 중인 영양 기준 (근거 기반 자동 계산)"):
        for note in limit_notes:
            st.caption(f"• {note}")
else:
    st.sidebar.info("숫자 기준이 적용되는 질환(고혈압/당뇨병/신장질환)을 선택하면 자동 판정됩니다.")

# 필드 매핑 (식약처 API 필드명 ↔ 한글 영양소명)
FIELD_MAP = {
    "나트륨": "nat",
    "당류": "sugar",
    "단백질": "prot",
}


def get_serving_scale(item):
    """식약처 API는 영양성분을 100g/100ml 기준으로 제공하지만,
    실제 1인분 중량은 foodSize 필드에 별도로 있음.
    ex) nutConSrtrQua='100ml', foodSize='372.8' → 이 메뉴 1인분은 372.8ml
        → 모든 영양성분 값에 372.8/100 = 3.728배를 곱해야 실제 섭취량이 됨.
    foodSize 정보가 없으면 스케일 1.0(=100g/ml 기준값 그대로)로 폴백."""
    import re
    base_qty_str = item.get("nutConSrtrQua", "100")
    food_size_str = item.get("foodSize", "")

    try:
        base_qty = float(re.sub(r"[^0-9.]", "", base_qty_str) or 100)
    except ValueError:
        base_qty = 100

    try:
        food_size = float(food_size_str)
    except (ValueError, TypeError):
        food_size = None

    if food_size and food_size > 0 and base_qty > 0:
        return food_size / base_qty, food_size
    return 1.0, None


def get_scaled_nutrients(item):
    """1인분 기준으로 환산된 영양성분 dict 반환"""
    scale, food_size = get_serving_scale(item)
    fields = ["enerc", "prot", "fatce", "chocdf", "sugar", "nat", "chole"]
    scaled = {}
    for f in fields:
        try:
            raw = float(item.get(f, 0) or 0)
        except ValueError:
            raw = 0.0
        scaled[f] = round(raw * scale, 2)
    return scaled, scale, food_size


# ============================================================
# 4-1. 식약처 메뉴 영양성분 조회 & 안전성 판정
#    (날씨/TourAPI 섹션에서도 재사용하기 위해 여기서 미리 정의)
# ============================================================
@st.cache_data
def fetch_food_data(keyword):
    url = "https://api.data.go.kr/openapi/tn_pubr_public_nutri_food_info_api"
    try:
        service_key = st.secrets["MFDS_API_KEY"]
    except (KeyError, FileNotFoundError):
        # secrets.toml에 키가 없는 경우. st.cache_data 함수 안에서는 st.error를
        # 직접 호출하지 않는 게 안전해서(캐시 히트 시 표시 안 될 수 있음), 조용히 None 반환.
        return None

    params = {
        'serviceKey': service_key,
        'pageNo': '1',
        'numOfRows': '30',
        'type': 'json',
        'foodNm': keyword
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None


def judge_numeric(scaled_nutrients, limits):
    """선택된 숫자 기준(나트륨/당류/단백질 등)에 대해 각각 판정, 가장 나쁜 등급을 종합 등급으로 반환
    scaled_nutrients: get_scaled_nutrients()가 반환한 1인분 기준 환산값 dict"""
    results = {}
    worst_rank = 0  # 0=안전, 1=주의, 2=경고
    rank_map = {"안전": 0, "주의": 1, "경고": 2}

    for nutrient, (caution, warning) in limits.items():
        field = FIELD_MAP.get(nutrient)
        val = scaled_nutrients.get(field, 0.0)

        if val <= caution:
            grade = "안전"
        elif val <= warning:
            grade = "주의"
        else:
            grade = "경고"

        results[nutrient] = (val, grade)
        worst_rank = max(worst_rank, rank_map[grade])

    overall = ["안전", "주의", "경고"][worst_rank]
    return results, overall


def judge_keywords(food_name, diseases, ibd_active):
    """질환별 키워드 매칭 → 주의 문구 리스트 반환"""
    notes = []
    for d in diseases:
        if d in KEYWORD_WARNINGS:
            info = KEYWORD_WARNINGS[d]
            if any(kw in food_name for kw in info["keywords"]):
                prefix = f"[{d}]"
                if d == "염증성장질환(크론병·궤양성대장염)" and ibd_active:
                    notes.append(f"{prefix} ⚠️ 활성기 - {info['msg']}")
                else:
                    notes.append(f"{prefix} {info['msg']}")
    return notes


def judge_allergy(food_name, allergies):
    hits = []
    for a in allergies:
        if any(kw in food_name for kw in ALLERGY_KEYWORDS[a]):
            hits.append(a)
    return hits


def render_food_cards(items):
    """식약처 API 결과 items를 Safe-Food 카드 디자인으로 렌더링 (메인 검색 / 식당 대표메뉴 분석 공용)"""
    comment_map = {
        "안전": "권장 기준치보다 낮아 안심하고 드실 수 있습니다.",
        "주의": "국물은 적게 드시고, 짠 반찬(젓갈·장아찌)은 피해보세요.",
        "경고": "가능하면 다른 메뉴를 고려하거나, 국물·소스를 최소화해서 드세요.",
    }

    rank_map = {"안전": 0, "주의": 1, "경고": 2}

    # 여러 결과 중 '그나마 나은 선택' 찾기 (등급 우선, 동률이면 나트륨+당류 합이 낮은 쪽)
    precomputed = []
    for item in items:
        scaled, _, _ = get_scaled_nutrients(item)
        if active_limits:
            _, grade = judge_numeric(scaled, active_limits)
        else:
            grade = "안전"
        score = scaled.get("nat", 0) + scaled.get("sugar", 0) * 10  # 당류는 g당 임팩트가 크니 가중치
        precomputed.append((rank_map[grade], score))

    best_idx = None
    if len(items) > 1:
        best_idx = min(range(len(items)), key=lambda i: precomputed[i])

    for idx, item in enumerate(items):
        food_name = item.get("foodNm", "이름 없음")
        rest_name = item.get("restNm", "일반 표준 메뉴")

        scaled, scale, food_size = get_scaled_nutrients(item)
        kcal, prot, nat, sugar = scaled["enerc"], scaled["prot"], scaled["nat"], scaled["sugar"]

        if active_limits:
            nutrient_results, overall_grade = judge_numeric(scaled, active_limits)
        else:
            nutrient_results, overall_grade = {}, "안전"

        keyword_notes = judge_keywords(food_name, selected_diseases, ibd_active)
        allergy_hits = judge_allergy(food_name, selected_allergies)

        size_caption = (
            f"📏 1인분 기준: 약 {food_size}g/ml (식약처 100g/ml 기준값을 환산)"
            if food_size else
            "⚠️ 1인분 중량 정보 없음 — 100g/ml 기준값을 그대로 표시합니다."
        )

        best_pick_html = (
            '<p class="sf-caption" style="color: var(--sf-safe); font-weight:700;">⭐ 검색된 결과 중 그나마 가장 무난한 선택이에요</p>'
            if idx == best_idx else ""
        )

        detail_html = ""
        if nutrient_results:
            detail_str = " · ".join(
                f"{n} {v}{'mg' if n=='나트륨' else 'g'} ({g})"
                for n, (v, g) in nutrient_results.items()
            )
            detail_html = f'<p class="sf-caption">세부 판정 → {html.escape(detail_str)}</p>'

        notes_html = "".join(
            f'<div class="sf-note">⚠️ {html.escape(note)}</div>' for note in keyword_notes
        )
        allergy_html = (
            f'<div class="sf-note sf-note-danger">⚠️ 알레르기 주의: {html.escape(", ".join(allergy_hits))} 성분이 포함될 수 있어요.</div>'
            if allergy_hits else ""
        )

        render_html(f"""
        <div class="sf-food-card">
          <div class="sf-food-card-top">
            <div style="flex:1; min-width:240px;">
              <p class="sf-food-name">🍽️ {html.escape(food_name)}</p>
              <p class="sf-food-sub">출처/분류: {html.escape(rest_name)}</p>
              {best_pick_html}
              <p class="sf-food-stats">⚡ {kcal}kcal · 🥩 {prot}g · 🧂 {nat}mg · 🍬 {sugar}g</p>
              <p class="sf-caption">{size_caption}</p>
              <p class="sf-caption">ℹ️ 표준 레시피 기준 추정치이며, 실제 조리법·재료에 따라 다를 수 있어요.</p>
              {detail_html}
              {notes_html}
              {allergy_html}
            </div>
            <div style="text-align:right;">
              {badge_html(overall_grade)}
              <p class="sf-caption" style="margin-top:0.5rem; max-width:160px;">{html.escape(comment_map[overall_grade])}</p>
            </div>
          </div>
        </div>
        """)


@st.cache_data(ttl=3600)
def fetch_ai_nutrition_estimate(food_name, api_key):
    """식약처 DB에 없는 메뉴의 영양성분을 LLM에게 추정하게 함.
    ⚠️ 이건 실측치가 아니라 AI의 추정값이며, 참고용으로만 써야 함.
    similar_dish: 식약처 표준 DB에 있을 법한 유사 음식명 (있으면 실측 재검색에 사용).
    반환값이 None이면 호출 실패(키 오류 등)."""
    import json as _json
    import re as _re

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    prompt = (
        f"한식 메뉴 '{food_name}' 1인분의 영양성분을 일반적인 조리법 기준으로 대략 추정해줘. "
        f"다른 설명 없이 아래 JSON 형식으로만 답변해:\n"
        f'{{"kcal": 숫자, "sodium_mg": 숫자, "sugar_g": 숫자, "protein_g": 숫자, '
        f'"note": "추정 근거를 30자 이내 한 문장으로", '
        f'"similar_dish": "식약처 표준 영양성분 DB에 있을 법한 가장 비슷한 일반 음식명 (예: 즉석떡볶이->떡볶이, 없으면 빈 문자열)"}}'
    )
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        res = requests.post(url, headers=headers, json=body, timeout=20)
        if res.status_code != 200:
            return None
        data = res.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        match = _re.search(r"\{.*\}", text, _re.DOTALL)
        if not match:
            return None
        parsed = _json.loads(match.group(0))
        return {
            "kcal": float(parsed.get("kcal", 0)),
            "nat": float(parsed.get("sodium_mg", 0)),
            "sugar": float(parsed.get("sugar_g", 0)),
            "prot": float(parsed.get("protein_g", 0)),
            "note": str(parsed.get("note", "")).strip(),
            "similar_dish": str(parsed.get("similar_dish", "")).strip(),
        }
    except Exception:
        return None


def render_ai_estimate_card(food_name, est):
    """AI 추정치 전용 카드 — 실측 카드와 확실히 구분되는 스타일(점선 테두리 + 경고 라벨)"""
    scaled = {"nat": est["nat"], "sugar": est["sugar"], "prot": est["prot"]}
    if active_limits:
        nutrient_results, overall_grade = judge_numeric(scaled, active_limits)
    else:
        nutrient_results, overall_grade = {}, "안전"

    keyword_notes = judge_keywords(food_name, selected_diseases, ibd_active)
    allergy_hits = judge_allergy(food_name, selected_allergies)

    detail_html = ""
    if nutrient_results:
        detail_str = " · ".join(
            f"{n} {v}{'mg' if n=='나트륨' else 'g'} ({g})" for n, (v, g) in nutrient_results.items()
        )
        detail_html = f'<p class="sf-caption">세부 판정 → {html.escape(detail_str)}</p>'
    notes_html = "".join(f'<div class="sf-note">⚠️ {html.escape(n)}</div>' for n in keyword_notes)
    allergy_html = (
        f'<div class="sf-note sf-note-danger">⚠️ 알레르기 주의: {html.escape(", ".join(allergy_hits))}</div>'
        if allergy_hits else ""
    )

    note_html = f'<p class="sf-caption">💭 추정 근거: {html.escape(est["note"])}</p>' if est.get("note") else ""

    render_html(f"""
    <div class="sf-food-card" style="border: 2px dashed var(--sf-pink-deep);">
      <div class="sf-food-card-top">
        <div style="flex:1; min-width:240px;">
          <p class="sf-food-name">🤖 {html.escape(food_name)}</p>
          <p class="sf-food-sub" style="color: var(--sf-pink-deep); font-weight:600;">⚠️ AI 추정치 — 실측값이 아닙니다. 참고용으로만 사용하세요.</p>
          <p class="sf-food-stats">⚡ {est['kcal']}kcal(추정) · 🥩 {est['prot']}g(추정) · 🧂 {est['nat']}mg(추정) · 🍬 {est['sugar']}g(추정)</p>
          {note_html}
          {detail_html}
          {notes_html}
          {allergy_html}
        </div>
        <div style="text-align:right;">{badge_html(overall_grade)}</div>
      </div>
    </div>
    """)


# 질환별 "이런 메뉴 유형이 비교적 무난해요" 추천 — 방어(주의사항)만 있던 것을 보완.
# 근거: 질병관리청 국가건강정보포털, 대한당뇨병학회, 대한신장학회(KSN),
#      세브란스병원·삼성서울병원·서울아산병원 건강정보, 순천향대병원 임상영양팀 자료 등을 참고.
# ※ 일반적인 식품군 수준의 참고 정보이며, 개인별 정확한 식단은 의료진·영양사와 상담이 필요함.
RECOMMENDED_FOODS = {
    "고혈압": [
        "칼륨이 풍부한 채소·과일 반찬 (질병관리청·DASH 식단 기준)",
        "저지방 유제품, 통곡물류",
        "찜·구이처럼 양념(나트륨)이 적은 조리법",
    ],
    "당뇨병": [
        "잡곡밥·현미밥 (식이섬유가 혈당 상승을 완만하게 함, 대한당뇨병학회)",
        "채소 반찬이 많은 백반류, 규칙적인 양의 식사",
        "튀김보다 구이·찜 요리",
    ],
    "신장질환": [
        "저염 조리 메뉴 (하루 나트륨 2,000mg 이내, 대한신장학회)",
        "단백질은 병기별로 적정량이 다름 — 고기·생선은 손바닥 절반 크기 이하로 (담당 의료진·임상영양사와 상의 권장)",
        "칼륨 제한이 필요한 병기라면 잡곡밥 대신 흰쌀밥이 무난할 수 있음",
    ],
    "염증성장질환(크론병·궤양성대장염)": {
        "관해기": ["일반식 대부분 가능. 본인에게 안 맞는 음식을 서서히 확인해가며 늘려보세요 (세브란스병원)"],
        "활성기": ["흰쌀밥·죽, 푹 익힌 채소, 삶은 살코기·생선 등 자극이 적고 소화가 쉬운 음식 위주 (경희의료원)"],
    },
    "과민성대장증후군(IBS)": [
        "흰쌀밥 + 구운 생선이나 수육 + 계란찜 + 마늘·양파 적은 나물 조합 (외식 시 저포드맵 예시)",
        "통곡물·양파·마늘·유제품은 포드맵 함량이 높은 편이라 과다 섭취 주의",
    ],
    "역류성식도염/위염": [
        "죽처럼 소화가 쉬운 부드러운 음식, 소량씩 자주 먹기",
        "고지방·튀김보다 담백한 조리법",
    ],
    "통풍": [
        "채소·나물 반찬, 다시마 육수 기반 국물",
        "육류·생선은 1회 1토막(약 50g) 정도로 제한",
    ],
}


# 업종(카카오 category_name)별 "이 업종에서는 이런 걸 골라보세요" 긍정 프레이밍 팁.
# 체크리스트의 주의 문구(get_category_hint)와는 톤이 달라야 하므로 별도로 관리.
CATEGORY_POSITIVE_TIPS = {
    "한식": "나물 반찬이 많은 정식·백반 메뉴가 비교적 무난해요.",
    "고기": "살코기 위주 부위나 채소 쌈이 곁들여진 메뉴를 찾아보세요.",
    "구이": "기름기 적은 부위의 구이나 생선구이가 비교적 무난해요.",
    "카페": "무설탕·저당 옵션이 있는 아메리카노나 티 종류가 무난해요.",
    "디저트": "생과일이 들어간 메뉴가 크림·시럽 많은 것보다 나아요.",
    "제과": "생과일이 들어간 메뉴가 크림·시럽 많은 것보다 나아요.",
    "일식": "회·초밥처럼 간장을 적게 찍어 먹는 메뉴가 비교적 무난해요.",
    "중식": "탕수육처럼 소스를 따로 찍어 먹는 메뉴가 볶음 요리보다 나아요.",
    "분식": "튀김·국물 많은 메뉴보다 김밥류가 비교적 무난해요.",
    "치킨": "양념치킨보다 담백한 순살구이가 비교적 무난해요.",
}


def get_recommendations(diseases, ibd_active, category_text=None):
    """선택된 질환 + (있으면) 식당 업종 기준으로 '비교적 무난한 메뉴 유형' 추천 리스트 생성"""
    recs = []
    for d in diseases:
        entry = RECOMMENDED_FOODS.get(d)
        if entry is None:
            continue
        if isinstance(entry, dict):  # 염증성장질환처럼 관해기/활성기 구분이 있는 경우
            state = "활성기" if (d == "염증성장질환(크론병·궤양성대장염)" and ibd_active) else "관해기"
            items = entry.get(state, [])
            tag = f"[{d}·{state}]"
        else:
            items = entry
            tag = f"[{d}]"
        for item in items:
            recs.append(f"{tag} {item}")

    if category_text:
        for keyword, tip in CATEGORY_POSITIVE_TIPS.items():
            if keyword in category_text:
                recs.append(f"[업종 참고] {tip}")
                break  # 업종 팁은 가장 먼저 매칭되는 것 하나만 (여러 개 겹치면 오히려 산만함)

    return recs


def render_checklist():
    """선택된 질환 기준 '직원에게 물어볼 체크리스트' + '무난한 메뉴 추천'을 펼침 메뉴로 표시.
    (식약처 DB 매칭 여부와 무관하게 항상 도움되는 정보라 별도로 분리)"""
    checklist = get_checklist(selected_diseases, ibd_active)
    recommendations = get_recommendations(selected_diseases, ibd_active)

    if recommendations:
        with st.expander("🥗 이런 메뉴는 비교적 무난해요"):
            for r in recommendations:
                st.write(f"• {r}")
            st.caption("※ 일반적인 식품군 참고 정보이며, 정확한 개인별 식단은 의료진·영양사와 상담하세요.")

    if checklist:
        with st.expander("🗣️ 이 식당에서 확인해보세요 (직원에게 물어볼 것)"):
            for q in checklist:
                st.write(f"• {q}")


def analyze_menu(keyword):
    """메뉴명으로 식약처 DB 검색(폴백 매칭 포함) → 카드 렌더링까지 한번에 처리.
    매칭 실패 시, Anthropic API 키가 있으면 AI 추정치를 선택적으로 제공."""
    items, matched_name = search_food_with_fallback(keyword)

    if items:
        if matched_name != keyword:
            st.caption(f"↳ '{keyword}' 그대로는 매칭되지 않아 '{matched_name}'으로 재검색했어요.")
        st.success(f"검색어 '{keyword}'에 대한 분석 결과입니다. (총 {len(items)}건 매칭)")
        render_food_cards(items)
    else:
        st.info(
            f"'{keyword}'은(는) 식약처 표준 영양성분 DB에 등록되지 않은 메뉴예요. "
            f"조리법 이름 대신 재료명(예: '돼지고기', '닭')으로도 검색해보시고, 그래도 없으면 아래 체크리스트를 참고해보세요."
        )
        if anthropic_api_key:
            if st.button(f"🤖 '{keyword}' AI로 대략 추정해보기 (실측 아님, 유료 호출)", key=f"ai_est_{keyword}"):
                with st.spinner("AI가 추정하는 중..."):
                    est = fetch_ai_nutrition_estimate(keyword, anthropic_api_key)
                if est:
                    render_ai_estimate_card(keyword, est)
                    similar = est.get("similar_dish")
                    if similar and similar != keyword:
                        similar_items, similar_matched = search_food_with_fallback(similar)
                        if similar_items:
                            st.caption(f"🔎 AI가 제안한 유사 메뉴 '{similar}'로 식약처 DB를 다시 찾아보니, 실측 데이터가 있었어요:")
                            render_food_cards(similar_items)
                else:
                    st.error("AI 추정 호출에 실패했어요. API 키를 확인해주세요.")
        else:
            st.caption("AI 추정 기능은 현재 이용할 수 없어요. 대신 아래 체크리스트를 참고해보세요.")
    render_checklist()

# ============================================================
# 5. 지역 선택 & 기상청 날씨 연동
#    ※ 기상청 API는 위경도가 아니라 격자좌표(nx, ny)를 씀.
#      도시마다 nx,ny를 일일이 찾아 넣는 대신, 위경도 → 격자좌표
#      변환 공식(기상청 공식 LCC 투영법)을 써서 위경도만 알면
#      어떤 지역이든 쉽게 추가할 수 있게 함.
# ============================================================
import math

def latlon_to_grid(lat, lon):
    """위도/경도를 기상청 단기예보 격자좌표(nx, ny)로 변환 (기상청 공식 LCC 투영 공식)"""
    RE = 6371.00877   # 지구 반경(km)
    GRID = 5.0        # 격자 간격(km)
    SLAT1, SLAT2 = 30.0, 60.0   # 투영 위도1,2
    OLON, OLAT = 126.0, 38.0    # 기준점 경도/위도
    XO, YO = 43, 136             # 기준점 X,Y 격자좌표

    DEGRAD = math.pi / 180.0
    re = RE / GRID
    slat1, slat2 = SLAT1 * DEGRAD, SLAT2 * DEGRAD
    olon, olat = OLON * DEGRAD, OLAT * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > math.pi:
        theta -= 2 * math.pi
    if theta < -math.pi:
        theta += 2 * math.pi
    theta *= sn

    x = ra * math.sin(theta) + XO + 0.5
    y = ro - ra * math.cos(theta) + YO + 0.5
    return int(x), int(y)


# 지역명: (위도, 경도) — 위경도만 알면 되므로 도시 추가가 훨씬 쉬움
REGION_COORDS = {
    "서울":   (37.5665, 126.9780),
    "인천":   (37.4563, 126.7052),
    "강릉":   (37.7519, 128.8761),
    "속초":   (38.2070, 128.5918),
    "전주":   (35.8242, 127.1480),
    "여수":   (34.7604, 127.6622),
    "부산":   (35.1796, 129.0756),
    "경주":   (35.8562, 129.2247),
    "제주":   (33.4996, 126.5312),
    "대전":   (36.3504, 127.3845),
    # 경기도 주요 도시 추가
    "수원":   (37.2636, 127.0286),
    "성남":   (37.4201, 127.1268),
    "용인":   (37.2411, 127.1776),
    "고양":   (37.6584, 126.8320),
    "안양":   (37.3943, 126.9568),
    "부천":   (37.5035, 126.7660),
    "안산":   (37.3219, 126.8309),
    "파주":   (37.7599, 126.7800),
    "가평":   (37.8315, 127.5095),
    "평택":   (36.9921, 127.1129),
    "화성":   (37.1996, 126.8319),
}

REGION_GRID = {name: latlon_to_grid(lat, lon) for name, (lat, lon) in REGION_COORDS.items()}

# API 키는 사용자에게 입력받지 않고 secrets.toml에서 조용히 읽어옵니다.
# (실제 서비스라면 사용자가 API 키를 직접 입력하는 화면은 없어야 하므로,
#  개발/테스트 편의용이었던 사이드바 입력창을 제거하고 서버 설정값처럼 동작하게 함)
kma_service_key = get_secret("KMA_API_KEY")


def get_base_datetime():
    """기상청 단기예보는 02,05,08,11,14,17,20,23시에 발표됨.
    가장 최근 발표시각을 base_date/base_time으로 계산."""
    now = datetime.now()
    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    available = [h for h in base_hours if h <= now.hour]
    if available:
        base_hour = max(available)
        base_date = now.strftime("%Y%m%d")
    else:
        # 새벽 2시 이전이면 전날 23시 발표자료 사용
        base_hour = 23
        base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
    return base_date, f"{base_hour:02d}00"


@st.cache_data(ttl=1800)
def fetch_weather(nx, ny, service_key):
    base_date, base_time = get_base_datetime()
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": service_key,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None


def parse_weather(data):
    """가장 가까운 예보 시각의 강수형태(PTY), 기온(TMP), 강수확률(POP)만 추출"""
    try:
        items = data["response"]["body"]["items"]["item"]
    except (KeyError, TypeError):
        return None

    # (fcstDate, fcstTime) 별로 그룹핑 후 가장 이른 시각 선택
    from collections import defaultdict
    grouped = defaultdict(dict)
    for it in items:
        key = (it["fcstDate"], it["fcstTime"])
        grouped[key][it["category"]] = it["fcstValue"]

    if not grouped:
        return None

    earliest_key = sorted(grouped.keys())[0]
    values = grouped[earliest_key]

    pty_map = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}
    pty = pty_map.get(values.get("PTY", "0"), "정보없음")

    return {
        "날짜": earliest_key[0],
        "시각": earliest_key[1],
        "기온": values.get("TMP", "-"),
        "강수형태": pty,
        "강수확률": values.get("POP", "-"),
    }


section_eyebrow("02", "DESTINATION")
st.header("📍 여행 지역")
col_region, col_weather = st.columns([1, 2])

with col_region:
    selected_region = st.selectbox("지역 선택", list(REGION_GRID.keys()))

is_rainy = False
with col_weather:
    if kma_service_key:
        nx, ny = REGION_GRID[selected_region]
        weather_data = fetch_weather(nx, ny, kma_service_key)
        if weather_data:
            parsed = parse_weather(weather_data)
            if parsed:
                is_rainy = parsed["강수형태"] != "없음" or (parsed["강수확률"] != "-" and int(parsed["강수확률"]) >= 60)
                weather_icon = "☔" if is_rainy else "☀️"
                st.markdown(
                    f"**{weather_icon} 오늘 {selected_region} 날씨** · "
                    f"🌡️ {parsed['기온']}℃ · 강수 {parsed['강수형태']} · 강수확률 {parsed['강수확률']}% "
                    f"<span style='font-size:0.8em;color:gray'>(발표: {parsed['시각'][:2]}시)</span>",
                    unsafe_allow_html=True,
                )
                if is_rainy:
                    st.caption("☔ 비 예보라 아래 실내 위주 식당을 먼저 보여드릴게요.")
            else:
                st.caption("날씨 데이터를 해석하지 못했습니다.")
        else:
            st.caption("기상청 API 호출 실패 — 인증키를 확인해주세요.")
    else:
        st.caption("날씨 정보를 준비 중이에요.")

st.markdown("---")

# ============================================================
# 6. TourAPI(한국관광공사) 지역 기반 음식점 추천
#    ※ 2024년 이후 신분류체계 적용으로 엔드포인트가 KorService2로 변경됨
#      (구 버전 KorService1 예제 코드는 더 이상 정상 작동하지 않음)
# API 키는 사용자에게 입력받지 않고 secrets.toml에서 조용히 읽어옵니다.
tour_service_key = get_secret("TOUR_API_KEY")
barrier_free_key = get_secret("BARRIER_FREE_API_KEY")
kakao_rest_key = get_secret("KAKAO_API_KEY")
anthropic_api_key = get_secret("ANTHROPIC_API_KEY")


CATEGORY_NUTRI_HINTS = {
    "찌개": "국물류는 나트륨이 높은 편이에요. 국물은 적게 드시는 걸 추천해요.",
    "전골": "국물류는 나트륨이 높은 편이에요. 국물은 적게 드시는 걸 추천해요.",
    "탕": "국물류는 나트륨이 높은 편이에요. 국물은 적게 드시는 걸 추천해요.",
    "국밥": "국물류는 나트륨이 높은 편이에요. 국물은 적게 드시는 걸 추천해요.",
    "찜": "양념이 진한 음식은 나트륨·당류가 높을 수 있어요.",
    "볶음": "양념이 진한 음식은 나트륨·당류가 높을 수 있어요.",
    "튀김": "튀김류는 칼로리·지방이 높은 편이에요.",
    "고기": "육류는 단백질은 높지만 나트륨 양념에 유의하세요.",
    "구이": "직화구이는 상대적으로 양념이 적어 무난한 편이에요.",
    "샐러드": "비교적 나트륨·칼로리 부담이 적은 편이에요.",
    "회": "생물 요리는 나트륨 부담이 비교적 적은 편이에요 (초장·양념장은 별도 유의).",
    "냉면": "냉면 육수는 나트륨이 상당할 수 있어요. 육수를 남기는 것도 방법이에요.",
    "국수": "면 요리 육수는 나트륨이 상당할 수 있어요.",
    "카레": "카레는 상대적으로 자극이 적고 무난한 편이에요.",
    "빵": "정제 탄수화물·당류 함량을 확인해보는 게 좋아요.",
    "카페": "당류가 높은 음료·디저트가 많을 수 있어요.",
}


def get_category_hint(category_text):
    """카카오 카테고리명 텍스트에서 키워드 매칭 → 일반 상식 수준의 영양 힌트 반환 (정확한 수치 아님)"""
    for keyword, hint in CATEGORY_NUTRI_HINTS.items():
        if keyword in category_text:
            return hint
    return None


# ============================================================
# TourAPI(한국관광공사) 지역코드 및 관광지 조회
#    ※ 공모전 "한국관광공사 OpenAPI 필수 활용" 요건 충족용 — 관광지 검색의 메인 데이터 소스.
#    2024년 이후 신분류체계 적용으로 엔드포인트가 KorService2로 변경됨.
# ============================================================
TOUR_AREA_CODE = {
    "서울": 1, "인천": 2, "대전": 3, "부산": 6, "제주": 39,
    "강릉": 32, "속초": 32, "전주": 37, "여수": 38, "경주": 35,
    "수원": 31, "성남": 31, "용인": 31, "고양": 31, "안양": 31,
    "부천": 31, "안산": 31, "파주": 31, "가평": 31, "평택": 31, "화성": 31,
}


@st.cache_data(ttl=3600)
def fetch_tour_attractions(area_code, service_key, num_of_rows=15):
    """TourAPI로 지역의 관광지(contentTypeId=12) 조회 — 공모전 필수 요건 데이터 소스"""
    url = "http://apis.data.go.kr/B551011/KorService2/areaBasedList2"
    params = {
        "serviceKey": service_key,
        "numOfRows": num_of_rows,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "SafeFoodTour",
        "arrange": "Q",
        "contentTypeId": 12,  # 12 = 관광지
        "areaCode": area_code,
        "_type": "json",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None


def parse_tour_attraction_list(data):
    """TourAPI 응답을 {관광지 이름: (경도, 위도)} 형태로 정리. 결과 1건이면 dict로 오므로 리스트로 통일."""
    try:
        items = data["response"]["body"]["items"]["item"]
    except (KeyError, TypeError):
        return {}
    if isinstance(items, dict):
        items = [items]
    result = {}
    for it in items:
        name, mapx, mapy = it.get("title"), it.get("mapx"), it.get("mapy")
        if name and mapx and mapy:
            result[name] = (float(mapx), float(mapy))
    return result


@st.cache_data(ttl=3600)
def fetch_barrier_free_info(area_code, service_key, num_of_rows=15):
    """한국관광공사_무장애 여행 정보 API로 지역의 무장애(편의시설) 관광지 조회.
    화장실·경사로 등 편의정보를 관광지·음식점·숙박시설 단위로 제공."""
    url = "http://apis.data.go.kr/B551011/KorWithService1/areaBasedList1"
    params = {
        "serviceKey": service_key,
        "numOfRows": num_of_rows,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "SafeFoodTour",
        "arrange": "Q",
        "areaCode": area_code,
        "_type": "json",
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None


def parse_barrier_free_list(data):
    """무장애 여행정보 응답을 [{이름, 주소}] 리스트로 정리"""
    try:
        items = data["response"]["body"]["items"]["item"]
    except (KeyError, TypeError):
        return []
    if isinstance(items, dict):
        items = [items]
    return [
        {"title": it.get("title", "이름 없음"), "addr": it.get("addr1", "")}
        for it in items if it.get("title")
    ]


@st.cache_data(ttl=1800)
def fetch_kakao_places(x, y, kakao_key, category_code, radius=1000, size=15):
    """카카오 로컬 API로 좌표 반경 내 장소 조회.
    category_code: FD6=음식점, AT4=관광명소.
    TourAPI보다 등록 범위가 훨씬 넓음(카카오맵 기준). 단, 메뉴 정보는 제공하지 않음."""
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    params = {
        "category_group_code": category_code,
        "x": x,
        "y": y,
        "radius": radius,
        "sort": "distance",
        "size": size,
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None


@st.cache_data(ttl=1800)
def fetch_kakao_keyword(query, x, y, kakao_key, radius=1000, size=15):
    """카카오 로컬 API 키워드 검색. 화장실처럼 별도 카테고리 코드가 없는 장소를 찾을 때 사용.
    ⚠️ 공식 화장실 등록 데이터가 아니라 카카오맵에 태그된 결과라 커버리지가 완벽하지 않을 수 있음."""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {kakao_key}"}
    params = {
        "query": query,
        "x": x,
        "y": y,
        "radius": radius,
        "sort": "distance",
        "size": size,
    }
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            return res.json()
        return None
    except Exception:
        return None


MENU_MODIFIER_PREFIXES = [
    "즉석", "매운", "얼큰", "매콤", "정통", "전통", "수제", "오리지널",
    "스페셜", "프리미엄", "특", "왕", "우리", "순한", "옛날", "명품", "본",
]

# 식당 브랜드명/지역명 뒤에 붙는 '음식 종류' 접미사 (예: '진미평양냉면' → '냉면')
MENU_TYPE_SUFFIXES = [
    "냉면", "칼국수", "국수", "우동", "짜장면", "짬뽕",
    "찌개", "전골", "탕", "국", "죽",
    "볶음밥", "비빔밥", "덮밥", "돈까스", "카레",
    "구이", "볶음", "조림", "찜", "튀김", "전",
    "떡볶이", "순대", "김밥", "만두", "회",
]


def strip_menu_modifier(name):
    """식당 메뉴명 앞에 붙은 흔한 수식어를 떼어 식약처 표준명에 가깝게 만듦
    (예: '즉석떡볶이' → '떡볶이', '본삼겹살' → '삼겹살')"""
    for prefix in MENU_MODIFIER_PREFIXES:
        if name.startswith(prefix) and len(name) > len(prefix):
            return name[len(prefix):]
    return name


def extract_menu_type_suffix(name):
    """메뉴명 끝부분의 '음식 종류' 단어만 추출
    (예: '진미평양냉면' → '냉면', '강남돈까스' → '돈까스')
    브랜드명·지역명이 앞에 붙어있어도 뒤쪽 음식 종류로 재검색하기 위함."""
    for suffix in MENU_TYPE_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            return suffix
    return None


def search_food_with_fallback(menu_name):
    """정확한 메뉴명 → 수식어 뗀 이름 → 음식종류 접미사 순으로 재검색"""
    def try_search(name):
        data = fetch_food_data(name)
        try:
            return data["response"]["body"]["items"] if data else []
        except (KeyError, TypeError):
            return []

    # 1차: 원본 그대로
    items = try_search(menu_name)
    if items:
        return items, menu_name

    # 2차: 앞 수식어 제거 (즉석떡볶이 → 떡볶이)
    stripped = strip_menu_modifier(menu_name)
    if stripped != menu_name:
        items = try_search(stripped)
        if items:
            return items, stripped

    # 3차: 끝 음식종류 단어만 추출 (진미평양냉면 → 냉면)
    suffix = extract_menu_type_suffix(menu_name)
    if suffix and suffix != menu_name:
        items = try_search(suffix)
        if items:
            return items, suffix

    return [], menu_name


try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False


def _dot_icon(color, size=16, border="#FFFFFF"):
    """기본 Leaflet 물방울 핀 대신 쓰는 심플한 원형 도트 마커 (더 정돈되어 보임)"""
    html = (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:{color};border:2px solid {border};'
        f'box-shadow:0 2px 6px rgba(0,0,0,0.35);"></div>'
    )
    return folium.DivIcon(html=html, icon_size=(size, size), icon_anchor=(size // 2, size // 2))


def build_restaurant_map(markers, attraction=None, toilets=None):
    """식당 좌표(mapx/mapy)에 원형 도트 마커를 찍은 folium 지도 생성.
    attraction이 주어지면 관광지 위치도 별 모양 파란 핀으로,
    toilets가 주어지면 화장실 위치도 연보라 도트로 함께 표시."""
    valid = [m for m in markers if m["lat"] and m["lon"]]
    toilets = toilets or []
    if not valid and not attraction and not toilets:
        return None

    if attraction:
        center_lat, center_lon = attraction["lat"], attraction["lon"]
    elif valid:
        center_lat = sum(m["lat"] for m in valid) / len(valid)
        center_lon = sum(m["lon"] for m in valid) / len(valid)
    else:
        center_lat, center_lon = toilets[0]["lat"], toilets[0]["lon"]

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=15 if attraction else 13)

    if attraction:
        folium.Marker(
            location=[attraction["lat"], attraction["lon"]],
            popup=f"📍 {attraction['name']} (관광지)",
            tooltip=attraction["name"],
            icon=folium.Icon(color="blue", icon="star", prefix="fa"),
        ).add_to(fmap)

    # 카카오는 자동 등급 정보가 없어 항상 같은 값이라, 등급색 대신 브랜드색 도트로 통일
    for m in valid:
        folium.Marker(
            location=[m["lat"], m["lon"]],
            popup=f"🍽️ {m['title']}",
            tooltip=m["title"],
            icon=_dot_icon("#4FA8D8", size=16),  # var(--sf-sky-deep)
        ).add_to(fmap)

    for t in toilets:
        if t.get("lat") and t.get("lon"):
            folium.Marker(
                location=[t["lat"], t["lon"]],
                popup=f"🚻 {t['title']}",
                tooltip=f"🚻 {t['title']}",
                icon=_dot_icon("#B8AFC4", size=12),
            ).add_to(fmap)

    return fmap


section_eyebrow("03", "NEARBY RESTAURANTS")
st.header("🍴 관광지 근처 맛집")

if not tour_service_key and not kakao_rest_key:
    st.info("관광지·맛집 정보를 준비 중이에요.")
else:
    region_lat, region_lon = REGION_COORDS[selected_region]

    # 1) 관광지 조회: TourAPI(한국관광공사, 필수 활용 요건) 우선, 없으면 카카오로 보조
    attraction_map = {}
    attraction_source = None
    if tour_service_key and selected_region in TOUR_AREA_CODE:
        tour_attraction_data = fetch_tour_attractions(TOUR_AREA_CODE[selected_region], tour_service_key)
        attraction_map = parse_tour_attraction_list(tour_attraction_data) if tour_attraction_data else {}
        if attraction_map:
            attraction_source = "한국관광공사 TourAPI"

    if not attraction_map and kakao_rest_key:
        kakao_attraction_data = fetch_kakao_places(region_lon, region_lat, kakao_rest_key, category_code="AT4", radius=5000, size=15)
        if kakao_attraction_data:
            for d in kakao_attraction_data.get("documents", []):
                name = d.get("place_name")
                if name and d.get("x") and d.get("y"):
                    attraction_map[name] = (float(d["x"]), float(d["y"]))
        if attraction_map:
            attraction_source = "카카오맵 (TourAPI 등록 정보 없어 보조 사용)"

    # 관광지 선택 + 출처 안내를 카드 하나로 묶음 (예전엔 캡션이 줄줄이 흩어져있어 지저분했음)
    with st.container(border=True):
        selected_attraction_name = None
        if attraction_map:
            attraction_choice = st.selectbox(
                "🏞️ 관광지 선택 — 이 근처 맛집을 보여드려요",
                [f"{selected_region} 중심으로 보기"] + list(attraction_map.keys()),
            )
            if attraction_choice != f"{selected_region} 중심으로 보기":
                selected_attraction_name = attraction_choice
            st.caption(f"관광지 출처: {attraction_source} · 맛집 출처: 카카오맵(거리순) · 대표메뉴 정보는 없어 체크리스트로 보완해요")
        else:
            st.caption("이 지역에 등록된 관광명소를 찾지 못해서, 지역 중심으로 맛집을 보여드려요.")

    # 1-1) 무장애 여행 정보 (선택) — 화장실·경사로 등 편의시설, 만성질환자 이동 부담 고려
    if barrier_free_key and selected_region in TOUR_AREA_CODE:
        bf_data = fetch_barrier_free_info(TOUR_AREA_CODE[selected_region], barrier_free_key)
        bf_list = parse_barrier_free_list(bf_data) if bf_data else []
        if bf_list:
            with st.expander(f"♿ '{selected_region}' 무장애(편의시설) 등록 명소 {len(bf_list)}곳"):
                st.caption("한국관광공사 무장애 여행 정보 기준 — 화장실·경사로 등 편의시설이 등록된 곳이에요.")
                for bf in bf_list[:10]:
                    st.write(f"• {bf['title']} — {bf['addr']}")

    if not kakao_rest_key:
        st.caption("근처 맛집 정보를 준비 중이에요.")
    else:
        # 2) 중심 좌표 결정: 관광지 선택 시 좁게(800m), 아니면 지역 중심으로 넓게(3km)
        attraction_marker = None
        if selected_attraction_name:
            center_x, center_y = attraction_map[selected_attraction_name]
            radius = 800
            attraction_marker = {"name": selected_attraction_name, "lat": center_y, "lon": center_x}
            toilet_query = f"{selected_attraction_name} 화장실"
            radius_desc = f"'{selected_attraction_name}' 반경 {radius}m 이내"
        else:
            center_x, center_y = region_lon, region_lat
            radius = 3000
            toilet_query = f"{selected_region} 화장실"
            radius_desc = f"'{selected_region}' 중심 반경 {radius}m 이내 (관광지를 고르면 더 좁혀져요)"

        # 화장실: 카카오 키워드 검색으로 실좌표 조회 시도 (공식 화장실 API는 2025년부터 좌표 미제공이라 대체)
        toilet_data = fetch_kakao_keyword("공중화장실", center_x, center_y, kakao_rest_key, radius=radius, size=10)
        toilets = []
        if toilet_data:
            for d in toilet_data.get("documents", []):
                if d.get("place_name") and d.get("x") and d.get("y"):
                    toilets.append({
                        "title": d["place_name"],
                        "lat": float(d["y"]),
                        "lon": float(d["x"]),
                    })

        kakao_map_url = f"https://map.kakao.com/?q={urllib.parse.quote(toilet_query)}"
        toilet_line = (
            f"🚻 화장실 {len(toilets)}곳 지도 표시 (카카오맵 태그 기준, 일부 누락 가능 · [더보기]({kakao_map_url}))"
            if toilets else
            f"🚻 태그된 화장실 없음 → [카카오맵에서 검색하기]({kakao_map_url})"
        )

        # 3) 음식점(FD6) 조회
        kakao_data = fetch_kakao_places(center_x, center_y, kakao_rest_key, category_code="FD6", radius=radius)
        if kakao_data:
            documents = kakao_data.get("documents", [])
            if not documents:
                st.info("이 근처에 카카오맵 등록 식당이 없어요. 다른 관광지를 선택해보세요.")

            restaurants = []
            for d in documents:
                restaurants.append({
                    "title": d.get("place_name", "이름 없음"),
                    "addr": d.get("road_address_name") or d.get("address_name", "주소 정보 없음"),
                    "category": (d.get("category_name") or "").split(">")[-1].strip(),
                    "distance": d.get("distance"),
                    "phone": d.get("phone"),
                    "url": d.get("place_url"),
                    "lat": float(d["y"]) if d.get("y") else None,
                    "lon": float(d["x"]) if d.get("x") else None,
                })

            # 지도 + 반경/화장실 안내를 카드 하나로 묶음
            with st.container(border=True):
                st.caption(f"📍 {radius_desc}  \n{toilet_line}")
                if FOLIUM_AVAILABLE:
                    map_markers = [{"title": r["title"], "lat": r["lat"], "lon": r["lon"], "grade": None} for r in restaurants]
                    fmap = build_restaurant_map(map_markers, attraction=attraction_marker, toilets=toilets)
                    if fmap:
                        st_folium(fmap, use_container_width=True, height=400, returned_objects=[])
                    else:
                        st.caption("지도에 표시할 좌표 정보가 없어요.")
                else:
                    st.info("🗺️ 지도를 보려면 터미널에서 `pip install folium streamlit-folium` 설치 후 앱을 다시 실행해주세요.")

            for r in restaurants:
                dist_txt = f"{r['distance']}m" if r["distance"] else ""
                phone_txt = f' · 📞 {html.escape(r["phone"])}' if r["phone"] else ""
                url_html = f' · <a href="{html.escape(r["url"])}" target="_blank">카카오맵에서 보기 ↗</a>' if r["url"] else ""

                render_html(f"""
                <div class="sf-food-card">
                  <div class="sf-food-card-top">
                    <div style="flex:1; min-width:240px;">
                      <p class="sf-food-name">🍽️ {html.escape(r['title'])}</p>
                      <p class="sf-food-sub">📍 {html.escape(r['addr'])} · {dist_txt}{phone_txt}</p>
                      <p class="sf-caption">🏷️ {html.escape(r['category'])}{url_html}</p>
                      <p class="sf-caption">ℹ️ 카카오는 메뉴 정보를 제공하지 않아요. 대표메뉴를 알고 계시면 아래 '메뉴 직접 검색'에 입력해보세요.</p>
                    </div>
                    <div style="text-align:right; color: var(--sf-muted); font-family:'IBM Plex Mono',monospace; font-size:0.85rem;">{dist_txt}</div>
                  </div>
                </div>
                """)

                restaurant_checklist = get_checklist(selected_diseases, ibd_active, category_text=r["category"])
                restaurant_recs = get_recommendations(selected_diseases, ibd_active, category_text=r["category"])
                if restaurant_recs:
                    with st.expander("🥗 이런 메뉴는 비교적 무난해요"):
                        for rec in restaurant_recs:
                            st.write(f"• {rec}")
                        st.caption("※ 일반적인 식품군 참고 정보이며, 정확한 개인별 식단은 의료진·영양사와 상담하세요.")
                if restaurant_checklist:
                    with st.expander("🗣️ 이 식당에서 확인해보세요"):
                        for q in restaurant_checklist:
                            st.write(f"• {q}")
        else:
            st.error("카카오 로컬 API 호출에 실패했습니다. REST API 키와 앱 설정의 '카카오맵 사용 설정'을 확인해주세요.")

st.markdown("---")

# ============================================================
# 7. 오늘의 코스 만들기 (직선거리 기준 간단 동선 생성)
#    ※ 실제 도보/차량 경로(Directions API)가 아니라 좌표 간 직선거리로
#      방문 순서만 정렬하는 수준의 MVP. 정확한 이동시간은 보장하지 않음.
# ============================================================
section_eyebrow("04", "BUILD YOUR ROUTE")
st.header("🗺️ 오늘의 코스 만들기")
st.caption("관광지를 2~4곳 고르면, 가까운 순서로 엮어서 간단한 동선을 만들어드려요. (직선거리 기준이라 실제 도보·차량 경로와는 다를 수 있어요)")

if not tour_service_key and not kakao_rest_key:
    st.info("코스 만들기 기능을 준비 중이에요.")
elif not attraction_map:
    st.caption("이 지역 근처에 등록된 관광명소가 없어서 코스를 만들 수 없어요.")
else:
    course_picks = st.multiselect(
        "코스에 넣을 관광지를 2~4곳 골라보세요",
        list(attraction_map.keys()),
        max_selections=4,
    )

    if len(course_picks) < 2:
        st.caption("관광지를 2곳 이상 선택하면 코스가 만들어져요.")
    else:
        def _haversine_km(lat1, lon1, lat2, lon2):
            from math import radians, sin, cos, sqrt, atan2
            R = 6371.0
            dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
            a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            return R * 2 * atan2(sqrt(a), sqrt(1 - a))

        # 최근접 이웃 방식으로 방문 순서 정렬 (지역 중심에서 가장 가까운 곳부터 시작)
        remaining = course_picks.copy()
        start = min(remaining, key=lambda n: _haversine_km(region_lat, region_lon, attraction_map[n][1], attraction_map[n][0]))
        ordered = [start]
        remaining.remove(start)
        while remaining:
            last_lon, last_lat = attraction_map[ordered[-1]]
            nxt = min(remaining, key=lambda n: _haversine_km(last_lat, last_lon, attraction_map[n][1], attraction_map[n][0]))
            ordered.append(nxt)
            remaining.remove(nxt)

        if is_rainy:
            st.info("☔ 오늘은 비 예보가 있어요. 야외 관광지 위주 코스라면 실내 대안도 함께 고려해보세요.")

        # 러프한 시간 배정: 09:00 시작, 관광지당 1.5시간 + 이동 30분 가정
        from datetime import datetime as _dt, timedelta as _td
        current_time = _dt.strptime("09:00", "%H:%M")
        course_map_markers = []

        for i, name in enumerate(ordered, start=1):
            lon, lat = attraction_map[name]
            arrival = current_time.strftime("%H:%M")
            current_time += _td(hours=1, minutes=30)
            departure = current_time.strftime("%H:%M")

            # 이 관광지 근처 최상위(거리순 1위) 식당 하나 추천
            nearby = fetch_kakao_places(lon, lat, kakao_rest_key, category_code="FD6", radius=500, size=1)
            nearby_name = None
            if nearby and nearby.get("documents"):
                nearby_name = nearby["documents"][0].get("place_name")

            nearby_html = (
                f'<p class="sf-caption">🍽️ 근처 추천: {html.escape(nearby_name)} (도보권)</p>'
                if nearby_name else '<p class="sf-caption">🍽️ 근처에 등록된 식당을 찾지 못했어요.</p>'
            )

            render_html(f"""
            <div class="sf-food-card">
              <div class="sf-food-card-top">
                <div style="flex:1; min-width:240px;">
                  <p class="sf-food-name">{i}. {html.escape(name)}</p>
                  <p class="sf-food-sub">🕐 {arrival} 도착 → {departure} 출발 (예상, 관광지당 1.5시간 가정)</p>
                  {nearby_html}
                </div>
              </div>
            </div>
            """)
            course_map_markers.append({"name": name, "lat": lat, "lon": lon, "order": i})

            if i < len(ordered):
                current_time += _td(minutes=30)  # 다음 장소까지 이동시간 대략치

        # 코스 지도: 순서대로 번호 핀 + 이동 경로 선
        if FOLIUM_AVAILABLE and course_map_markers:
            course_map = folium.Map(
                location=[course_map_markers[0]["lat"], course_map_markers[0]["lon"]],
                zoom_start=13,
            )
            coords = []
            for m in course_map_markers:
                folium.Marker(
                    location=[m["lat"], m["lon"]],
                    popup=f"{m['order']}. {m['name']}",
                    tooltip=f"{m['order']}. {m['name']}",
                    icon=folium.Icon(color="pink" if m["order"] == 1 else "blue", icon="flag", prefix="fa"),
                ).add_to(course_map)
                coords.append([m["lat"], m["lon"]])
            folium.PolyLine(coords, color="#E06FA0", weight=3, dash_array="6,8").add_to(course_map)
            st_folium(course_map, use_container_width=True, height=400, returned_objects=[])
            st.caption("📏 점선은 실제 경로가 아니라 방문 순서를 직선으로 이은 것이에요.")
        elif not FOLIUM_AVAILABLE:
            st.info("🗺️ 지도를 보려면 터미널에서 `pip install folium streamlit-folium` 설치 후 앱을 다시 실행해주세요.")

st.markdown("---")

# ============================================================
# 8. 메인 화면 - 메뉴 검색
# ============================================================
section_eyebrow("05", "MENU CHECK-IN")
st.header("🔍 메뉴 직접 검색")
search_keyword = st.text_input("방문하고 싶은 식당의 메뉴명 입력 (예: 갈비탕, 비빔밥, 김치찌개)", value="갈비탕")

if st.button("메뉴 영양성분 및 안전성 분석") or search_keyword:
    with st.spinner("표준 영양성분 DB와 대조하여 분석 중입니다..."):
        analyze_menu(search_keyword)