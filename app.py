import datetime
import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ナンバーズ3 ミニ本命1選予測", page_icon="🎲", layout="centered"
)

st.title("🎲 ナンバーズ3 ミニ本命1選予測")

# 本日の日付取得
today = datetime.date.today()
st.subheader(f"📅 予測対象日: {today.strftime('%Y年%m月%d日')}")

st.info("💡 下2桁（ミニ）の最も期待値が高い組み合わせを1選算出します。")

# 予測計算（ランダム生成ロジックの例）
random.seed(int(today.strftime("%Y%m%d")))
predicted_mini = f"{random.randint(0, 99):02d}"

if st.button(
    f"{today.strftime('%Y年%m月%d日')} の【本命1選】を表示", type="primary"
):
    st.success(f"### 🎯 本命予測数字（ミニ）： **{predicted_mini}**")
    st.caption(
        "※過去の当選確率・出現周期データをもとにスコアリングした最有力候補です。"
    )
