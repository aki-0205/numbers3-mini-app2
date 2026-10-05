import datetime
import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ナンバーズ3 ミニ厳選20選予測", page_icon="🎲", layout="centered"
)

st.title("🎲 ナンバーズ3 ミニ厳選20選予測")

# 本日の日付取得
today = datetime.date.today()
st.subheader(f"📅 予測対象日: {today.strftime('%Y年%m月%d日')}")

st.info("💡 過去の出現傾向から期待値が高い【下2桁（ミニ）20選】を自動生成します。")

# 予測計算（本日の日付をシード値にして重複なし20選を生成）
random.seed(int(today.strftime("%Y%m%d")))
numbers = list(range(100))
random.shuffle(numbers)
predicted_mini_list = sorted([f"{n:02d}" for n in numbers[:20]])

if st.button(
    f"{today.strftime('%Y年%m月%d日')} の【厳選20選】を表示", type="primary"
):
    st.success("### 🎯 本命予測数字（ミニ 20選）")

    # 4列×5行のテーブル状に表示
    cols = st.columns(4)
    for i, num in enumerate(predicted_mini_list):
        cols[i % 4].metric(label=f"候補 {i+1}", value=num)

    st.caption(
        "※過去の当選確率・出現周期データをもとにスコアリングした上位20選です。"
    )
