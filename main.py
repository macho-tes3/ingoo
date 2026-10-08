# -*- coding: utf-8 -*-
"""
데이터의 '퍼짐' 눈으로 보기 (Streamlit 앱)
- 읍·면·동별 인구 데이터에서 가장 최신 연도만 골라 '총인구'를 계산합니다.
- 총인구의 describe() 표, 히스토그램, 상자그림을 순서대로 보여줍니다.
- 그래프는 plotly로 그려서 확대·축소하고 값을 확인할 수 있어요.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------
# 1. 페이지 기본 설정 (반드시 다른 streamlit 명령보다 먼저 나와야 해요)
# ------------------------------------------------------------
st.set_page_config(
    page_title="동네 인구 퍼짐 보기",
    page_icon="📊",
    layout="centered",
)

# ------------------------------------------------------------
# 2. 따뜻한 톤을 위한 간단한 꾸밈(CSS)
#    - 배경은 크림색, 글자는 짙은 갈색
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #FFF6DC; }
    .stApp h1, .stApp h2, .stApp h3,
    .stApp p, .stApp label, .stApp span, .stApp li { color: #4A3B20; }
    h1 { color: #8A5A00 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 3. 자주 쓰는 값
# ------------------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/main/"
    "data/population_yearly.csv.gz"
)
# 동네를 알아보는 데 쓰는 열
ID_COLUMNS = ["연도", "시도", "시군구", "동", "코드"]

# 그래프에 공통으로 쓸 따뜻한 색
BAR_COLOR = "#E08A00"
BG_PAPER = "#FFF6DC"   # 그래프 바깥 배경
BG_PLOT = "#FFFDF5"    # 그래프 안쪽 배경
TEXT_COLOR = "#4A3B20"


# ------------------------------------------------------------
# 4. 데이터를 불러오고 준비하는 함수
#    - @st.cache_data: 한 번 불러온 데이터는 1시간 동안 저장해 두고 다시 써요.
#      (버튼을 누를 때마다 인터넷에서 다시 받으면 느려지거든요)
# ------------------------------------------------------------
def is_needed_column(name):
    """필요한 열만 읽도록 골라 주는 함수 (메모리를 아끼려고요)."""
    return name in ID_COLUMNS or name.startswith(("남_", "여_"))


@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    """최신 연도 데이터만 남기고 '총인구' 열을 만들어 돌려줍니다."""
    # (1) CSV 읽기: .gz 압축 파일이어도 pandas가 알아서 풀어서 읽어요.
    #     한글 파일은 글자 인코딩이 다를 수 있어서, utf-8이 안 되면 cp949로 다시 읽어요.
    try:
        df = pd.read_csv(DATA_URL, usecols=is_needed_column, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(DATA_URL, usecols=is_needed_column, encoding="cp949")

    # (2) 가장 최신 연도만 남기기
    years = pd.to_numeric(df["연도"], errors="coerce")  # 숫자로 바꿔 비교해요
    if years.isna().all():
        latest = df["연도"].max()          # 숫자로 못 바꾸면 글자 기준으로 비교
        df = df[df["연도"] == latest].copy()
    else:
        latest = int(years.max())
        df = df[years == latest].copy()

    # (3) '남_'으로 시작하는 열과 '여_'로 시작하는 열을 모두 찾기
    #     ('계_' 열은 남+여와 같은 값이라서 더하면 두 배가 되니 뺐어요.)
    age_columns = [c for c in df.columns if c.startswith(("남_", "여_"))]
    if not age_columns:
        raise ValueError("'남_' 또는 '여_'로 시작하는 열을 찾지 못했어요.")

    # (4) 숫자가 글자로 들어 있을 때를 대비해 숫자로 바꿔요. (예: "1,234" -> 1234)
    for c in age_columns:
        if df[c].dtype == "object":
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            )

    # (5) 동네(행)마다 모든 나이별 열을 더해 '총인구' 만들기
    df["총인구"] = df[age_columns].sum(axis=1)

    return df, latest, len(age_columns)


# ------------------------------------------------------------
# 5. 제목과 간단한 설명
# ------------------------------------------------------------
st.title("📊 동네 인구, 얼마나 퍼져 있을까?")
st.write(
    "전국 읍·면·동의 **총인구**가 얼마나 들쭉날쭉한지 "
    "표와 그래프로 살펴봐요. 그래프는 마우스로 확대·축소하고, "
    "점이나 막대에 올리면 값을 볼 수 있어요."
)

# ------------------------------------------------------------
# 6. 데이터 불러오기 (실패하면 안내 문구를 보여 주고 멈춰요)
# ------------------------------------------------------------
try:
    with st.spinner("데이터를 불러오는 중이에요... (처음에는 조금 걸려요)"):
        df, latest_year, n_age_cols = load_data()
except KeyError as e:
    st.error(f"필요한 열을 찾지 못했어요: {e}. 데이터의 열 이름을 확인해 주세요.")
    st.stop()
except Exception as e:
    st.error(f"데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요. ({e})")
    st.stop()

st.caption(
    f"기준 연도: **{latest_year}년** · 동네 수: **{len(df):,}곳** · "
    f"더한 나이별 열: {n_age_cols}개 (남 + 여)"
)

# ------------------------------------------------------------
# 7. 첫 번째: 총인구의 describe() 결과 표
# ------------------------------------------------------------
st.header("1) 요약 통계표")

# describe()는 영어 이름(count, mean...)으로 나오니 한국어로 바꿔 줘요.
summary = df["총인구"].describe().to_frame(name="총인구")
summary = summary.rename(
    index={
        "count": "개수 (동네 수)",
        "mean": "평균",
        "std": "표준편차",
        "min": "최솟값",
        "25%": "25% 지점",
        "50%": "중앙값 (50%)",
        "75%": "75% 지점",
        "max": "최댓값",
    }
)
st.dataframe(summary.round(1), width="stretch")

# 평균과 중앙값을 비교해서 퍼짐 모양을 쉬운 말로 알려 줘요.
mean_value = df["총인구"].mean()
median_value = df["총인구"].median()
if mean_value > median_value:
    st.info(
        f"평균({mean_value:,.0f}명)이 중앙값({median_value:,.0f}명)보다 커요. "
        "아주 큰 동네 몇 곳이 평균을 끌어올린 모양이에요."
    )
else:
    st.info(
        f"평균({mean_value:,.0f}명)이 중앙값({median_value:,.0f}명)과 "
        "비슷하거나 더 작아요."
    )

# ------------------------------------------------------------
# 8. 두 번째: 총인구 히스토그램
#    - 히스토그램: 값을 구간으로 나눠 '각 구간에 동네가 몇 곳인지' 막대로 보여 줘요.
# ------------------------------------------------------------
st.header("2) 히스토그램")

fig_hist = px.histogram(
    df,
    x="총인구",
    nbins=50,                       # 막대(구간) 개수
    color_discrete_sequence=[BAR_COLOR],
    labels={"총인구": "총인구 (명)", "count": "동네 수"},
)
fig_hist.update_traces(
    marker_line_color="#FFF6DC",
    marker_line_width=1,
    hovertemplate="총인구: %{x}명<br>동네 수: %{y}곳<extra></extra>",
)
fig_hist.update_layout(
    title=f"{latest_year}년 동네별 총인구 분포",
    xaxis_title="총인구 (명)",
    yaxis_title="동네 수 (곳)",
    template="plotly_white",
    paper_bgcolor=BG_PAPER,
    plot_bgcolor=BG_PLOT,
    font=dict(color=TEXT_COLOR, size=14),
    bargap=0.05,
    margin=dict(l=10, r=10, t=60, b=10),
)
st.plotly_chart(fig_hist, width="stretch")

# ------------------------------------------------------------
# 9. 세 번째: 총인구 상자그림
#    - 상자그림: 상자는 가운데 50%의 동네, 상자 안의 선은 중앙값이에요.
#      상자 밖에 따로 찍힌 점은 유난히 크거나 작은 동네(이상치)예요.
# ------------------------------------------------------------
st.header("3) 상자그림")

fig_box = px.box(
    df,
    x="총인구",
    points="outliers",              # 튀는 값만 점으로 표시
    hover_data={"시도": True, "시군구": True, "동": True, "총인구": ":,"},
    color_discrete_sequence=[BAR_COLOR],
    labels={"총인구": "총인구 (명)"},
)
fig_box.update_layout(
    title=f"{latest_year}년 동네별 총인구 상자그림",
    xaxis_title="총인구 (명)",
    template="plotly_white",
    paper_bgcolor=BG_PAPER,
    plot_bgcolor=BG_PLOT,
    font=dict(color=TEXT_COLOR, size=14),
    margin=dict(l=10, r=10, t=60, b=10),
)
st.plotly_chart(fig_box, width="stretch")

st.caption(
    "※ 총인구 = 모든 나이의 남자 인구 + 여자 인구. "
    "상자 밖의 점에 마우스를 올리면 어느 동네인지 볼 수 있어요."
)
