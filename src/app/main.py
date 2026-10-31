"""Streamlit app: search cutoff scores and get university/major recommendations."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.model.recommend import Recommender

DATA_PATH = Path("data/processed/scores.csv")

st.set_page_config(
    page_title="Tra cứu điểm chuẩn & Gợi ý ngành/trường",
    page_icon="🎓",
    layout="wide",
)


@st.cache_resource
def load_recommender() -> Recommender:
    return Recommender(DATA_PATH)


@st.cache_data
def load_df() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, encoding="utf-8-sig")


recommender = load_recommender()
df_all = load_df()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎓 Tra cứu điểm chuẩn đại học Việt Nam")
st.caption("Dữ liệu 2020–2026 · Nguồn: trang chính thức các trường và Bộ GD&ĐT")

tab_recommend, tab_search, tab_trend = st.tabs(
    ["💡 Gợi ý trường/ngành", "🔍 Tra cứu điểm chuẩn", "📈 Xu hướng điểm chuẩn"]
)

# ── Tab 1: Recommendation ─────────────────────────────────────────────────────
with tab_recommend:
    st.subheader("Nhập điểm và tổ hợp môn để nhận gợi ý")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        student_score = st.number_input(
            "Điểm của bạn (tổng 3 môn, thang 30)",
            min_value=0.0,
            max_value=30.0,
            value=24.0,
            step=0.25,
        )
    with col2:
        combo = st.selectbox("Tổ hợp môn", options=recommender.combos)
    with col3:
        top_n = st.number_input("Số gợi ý mỗi nhóm", min_value=1, max_value=20, value=5)

    if st.button("Tìm gợi ý", type="primary"):
        result = recommender.recommend(student_score, combo, top_n=int(top_n))

        def render_group(recs, label, color):
            if not recs:
                st.info(f"Không có trường nào trong nhóm {label} với tổ hợp {combo}.")
                return
            rows = []
            for r in recs:
                rows.append(
                    {
                        "Trường": r.university_name,
                        "Ngành": r.major_name,
                        "Điểm chuẩn": r.cutoff_score,
                        "Năm": r.year,
                        "Chênh lệch": f"{r.gap:+.2f}",
                        "Xu hướng": r.trend,
                        "Lý do gợi ý": r.reason,
                    }
                )
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Lý do gợi ý": st.column_config.TextColumn(width="large"),
                },
            )

        st.markdown(f"### Kết quả cho điểm **{student_score}** · tổ hợp **{combo}**")

        with st.expander("🎯 Trường phù hợp (chênh ≤ 2đ)", expanded=True):
            render_group(result.target, "phù hợp", "blue")

        with st.expander("🛡️ Trường an toàn (điểm cao hơn > 2đ)"):
            render_group(result.safety, "an toàn", "green")

        with st.expander("🚀 Trường thách thức (điểm chuẩn cao hơn ≤ 1đ)"):
            render_group(result.reach, "thách thức", "orange")

# ── Tab 2: Search ─────────────────────────────────────────────────────────────
with tab_search:
    st.subheader("Tìm điểm chuẩn theo trường hoặc ngành")
    col_a, col_b = st.columns(2)
    with col_a:
        uni_filter = st.selectbox(
            "Chọn trường (bỏ trống = tất cả)",
            options=[""] + sorted(df_all["university_name"].dropna().unique().tolist()),
        )
    with col_b:
        year_filter = st.multiselect(
            "Năm",
            options=sorted(df_all["year"].unique().tolist(), reverse=True),
            default=[int(df_all["year"].max())],
        )

    keyword = st.text_input("Tên ngành chứa…")

    filtered = df_all.copy()
    if uni_filter:
        filtered = filtered[filtered["university_name"] == uni_filter]
    if year_filter:
        filtered = filtered[filtered["year"].isin(year_filter)]
    if keyword:
        filtered = filtered[filtered["major_name"].str.contains(keyword, case=False, na=False)]

    st.dataframe(
        filtered.sort_values(
            ["year", "university_name", "cutoff_score"], ascending=[False, True, False]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"{len(filtered)} bản ghi")

# ── Tab 3: Trend ──────────────────────────────────────────────────────────────
with tab_trend:
    st.subheader("Xu hướng điểm chuẩn qua các năm")

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
        )
        fig.update_layout(xaxis=dict(tickmode="linear", dtick=1))
        st.plotly_chart(fig, use_container_width=True)
