"""Streamlit app: search cutoff scores and get university/major recommendations."""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from src.model.recommend import Recommender  # noqa: E402

DATA_PATH = _ROOT / "data" / "processed" / "scores.csv"

st.set_page_config(
    page_title="Điểm chuẩn đại học Việt Nam",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #f5f6f8;
    font-family: "Segoe UI", Arial, sans-serif;
}

/* ── Remove default padding ── */
[data-testid="block-container"] { padding-top: 0 !important; }

/* ── Site header bar ── */
.site-header {
    background: #1a3260;
    color: #fff;
    padding: 18px 32px 14px;
    margin: -1rem -1rem 1.5rem;
    border-bottom: 4px solid #c0392b;
}
.site-header h1 {
    margin: 0; font-size: 1.45rem; font-weight: 700; letter-spacing: .01em;
}
.site-header p {
    margin: 4px 0 0; font-size: 0.82rem; opacity: .75; color: #fff;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-size: .93rem;
    font-weight: 600;
    border-radius: 0 !important;
    border-bottom: 3px solid transparent;
    padding: 8px 20px;
    color: #444;
    background: none;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    border-bottom: 3px solid #1a3260;
    color: #1a3260;
}

/* ── Inputs / Buttons ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div {
    border-radius: 2px !important;
    border-color: #ccc !important;
    font-size: .92rem;
}
button[kind="primary"] {
    background-color: #c0392b !important;
    color: #fff !important;
    border-radius: 2px !important;
    font-weight: 600;
    border: none !important;
}
button[kind="primary"]:hover { background-color: #a93226 !important; }

/* ── Result section labels ── */
.result-label {
    font-size: .8rem;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    padding: 4px 10px;
    display: inline-block;
    margin-bottom: 6px;
}
.label-target { background: #1a3260; color: #fff; }
.label-safety { background: #27ae60; color: #fff; }
.label-reach  { background: #c0392b; color: #fff; }

/* ── Section divider ── */
.section-sep {
    border: none;
    border-top: 1px solid #d0d5de;
    margin: 1.2rem 0;
}

/* ── Metric strip ── */
.metric-strip {
    display: flex; gap: 1.5rem; margin-bottom: 1rem;
}
.metric-box {
    background: #fff;
    border: 1px solid #dce0e8;
    border-left: 4px solid #1a3260;
    padding: 10px 18px;
    min-width: 140px;
}
.metric-box .val { font-size: 1.5rem; font-weight: 700; color: #1a3260; }
.metric-box .lbl { font-size: .75rem; color: #666; margin-top: 1px; }

/* ── Flatten expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #d0d5de !important;
    border-radius: 0 !important;
    background: #fff;
}
[data-testid="stExpander"] summary {
    font-weight: 600; font-size: .9rem;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #d0d5de; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_recommender() -> Recommender:
    return Recommender(DATA_PATH)


@st.cache_data
def load_df() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, encoding="utf-8-sig")


recommender = load_recommender()
df_all = load_df()

# ── Site header ───────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="site-header">
  <h1>Tra cứu điểm chuẩn đại học Việt Nam</h1>
  <p>Dữ liệu 2021 &nbsp;·&nbsp; Nguồn: tuyensinh.edu.vn &nbsp;·&nbsp; 487 bản ghi</p>
</div>
""",
    unsafe_allow_html=True,
)

tab_recommend, tab_search, tab_trend = st.tabs(
    ["Gợi ý trường / ngành", "Tra cứu điểm chuẩn", "Xu hướng điểm chuẩn"]
)

# ── Tab 1: Recommendation ─────────────────────────────────────────────────────
with tab_recommend:
    st.markdown("**Nhập điểm thi và tổ hợp để nhận danh sách trường/ngành phù hợp.**")
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        student_score = st.number_input(
            "Tổng điểm 3 môn (thang 30)",
            min_value=0.0,
            max_value=30.0,
            value=24.0,
            step=0.25,
        )
    with col2:
        combo = st.selectbox("Tổ hợp môn", options=recommender.combos)
    with col3:
        top_n = st.number_input("Số kết quả/nhóm", min_value=1, max_value=20, value=5)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("Tra cứu", type="primary", use_container_width=True)

    if run:
        result = recommender.recommend(student_score, combo, top_n=int(top_n))

        total = len(result.target) + len(result.safety) + len(result.reach)
        st.markdown(
            f"""
<div class="metric-strip">
  <div class="metric-box">
    <div class="val">{student_score:.2f}</div>
    <div class="lbl">Điểm của bạn</div>
  </div>
  <div class="metric-box">
    <div class="val">{combo}</div>
    <div class="lbl">Tổ hợp môn</div>
  </div>
  <div class="metric-box">
    <div class="val">{total}</div>
    <div class="lbl">Ngành/trường tìm thấy</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        def render_group(recs, label_html: str, empty_msg: str):
            st.markdown(label_html, unsafe_allow_html=True)
            if not recs:
                st.caption(empty_msg)
            else:
                rows = [
                    {
                        "Trường": r.university_name,
                        "Ngành": r.major_name,
                        "Điểm chuẩn": r.cutoff_score,
                        "Năm": r.year,
                        "Chênh lệch": f"{r.gap:+.2f}",
                        "Xu hướng": r.trend,
                        "Lý do gợi ý": r.reason,
                    }
                    for r in recs
                ]
                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                    column_config={"Lý do gợi ý": st.column_config.TextColumn(width="large")},
                )
            st.markdown('<hr class="section-sep">', unsafe_allow_html=True)

        render_group(
            result.target,
            '<span class="result-label label-target">Phù hợp &nbsp; (chênh lệch ≤ 2đ)</span>',
            f"Không có ngành phù hợp với tổ hợp {combo}.",
        )
        render_group(
            result.safety,
            '<span class="result-label label-safety">An toàn &nbsp; (điểm cao hơn > 2đ)</span>',
            f"Không có ngành an toàn với tổ hợp {combo}.",
        )
        render_group(
            result.reach,
            '<span class="result-label label-reach">Thách thức &nbsp; (điểm chuẩn cao hơn ≤ 1đ)</span>',
            f"Không có ngành thách thức với tổ hợp {combo}.",
        )

# ── Tab 2: Search ─────────────────────────────────────────────────────────────
with tab_search:
    col_a, col_b, col_c = st.columns([3, 2, 3])
    with col_a:
        uni_filter = st.selectbox(
            "Trường",
            options=["(tất cả)"] + sorted(df_all["university_name"].dropna().unique().tolist()),
        )
    with col_b:
        year_filter = st.multiselect(
            "Năm",
            options=sorted(df_all["year"].unique().tolist(), reverse=True),
            default=[int(df_all["year"].max())],
        )
    with col_c:
        keyword = st.text_input("Tên ngành chứa...")

    filtered = df_all.copy()
    if uni_filter != "(tất cả)":
        filtered = filtered[filtered["university_name"] == uni_filter]
    if year_filter:
        filtered = filtered[filtered["year"].isin(year_filter)]
    if keyword:
        filtered = filtered[filtered["major_name"].str.contains(keyword, case=False, na=False)]

    st.caption(f"{len(filtered):,} bản ghi")
    st.dataframe(
        filtered.sort_values(
            ["year", "university_name", "cutoff_score"], ascending=[False, True, False]
        ),
        use_container_width=True,
        hide_index=True,
    )

# ── Tab 3: Trend ──────────────────────────────────────────────────────────────
with tab_trend:
    col_x, col_y = st.columns(2)
    with col_x:
        trend_uni = st.selectbox(
            "Trường", options=sorted(df_all["university_name"].dropna().unique())
        )
    with col_y:
        uni_majors = df_all[df_all["university_name"] == trend_uni]["major_name"].dropna().unique()
        trend_major = st.selectbox("Ngành", options=sorted(uni_majors.tolist()))

    trend_df = df_all[
        (df_all["university_name"] == trend_uni) & (df_all["major_name"] == trend_major)
    ].copy()

    if trend_df.empty:
        st.info("Không có dữ liệu cho lựa chọn này.")
    else:
        fig = px.line(
            trend_df.sort_values("year"),
            x="year",
            y="cutoff_score",
            color="score_combo",
            markers=True,
            labels={"year": "Năm", "cutoff_score": "Điểm chuẩn", "score_combo": "Tổ hợp"},
            title=f"{trend_major} — {trend_uni}",
            color_discrete_sequence=["#1a3260", "#c0392b", "#27ae60", "#e67e22", "#8e44ad"],
        )
        fig.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            plot_bgcolor="#fff",
            paper_bgcolor="#fff",
            font=dict(family="Segoe UI, Arial", size=13),
            title_font=dict(size=15, color="#1a3260"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        fig.update_xaxes(showgrid=True, gridcolor="#ececec")
        fig.update_yaxes(showgrid=True, gridcolor="#ececec")
        st.plotly_chart(fig, use_container_width=True)
