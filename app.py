import streamlit as st
import pandas as pd
import datetime
import random
import numpy as np
import os

# --- 画面基本設定 ---
st.set_page_config(
    page_title="ナンバーズ3 ミニ 予測アプリ",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CSV_FILE = "prediction_history.csv"

# --- データ読み込み・保存関数 ---
def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE, dtype={'target_date': str, 'actual_num': str, 'prev_num': str})
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=['target_date', 'actual_num', 'prev_num'])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

df_history = load_data()

# --- 日付・前回数字の判定ロジック ---
now = datetime.datetime.now()

# 19:00以降は翌日を対象日とする
if now.hour >= 19:
    target_date_dt = now.date() + datetime.timedelta(days=1)
else:
    target_date_dt = now.date()

target_date_str = target_date_dt.strftime('%Y-%m-%d')
display_date_str = target_date_dt.strftime('%Y年%m月%d日')

# CSV履歴から一番新しい当選番号を自動取得
latest_actual = "00"
if not df_history.empty:
    valid_records = df_history[df_history['actual_num'].notna() & (df_history['actual_num'] != "")]
    if not valid_records.empty:
        latest_actual = str(valid_records.iloc[-1]['actual_num']).zfill(2)

# --- 予測アルゴリズム ---
def calculate_predictions(prev_actual_num: str, seed_date_str: str) -> list:
    try:
        seed_val = int(seed_date_str.replace('-', ''))
    except ValueError:
        seed_val = 20261008

    random.seed(seed_val)
    np.random.seed(seed_val)

    all_nums = [f"{i:02d}" for i in range(100)]
    scores = {}

    prev_ten = int(prev_actual_num[0]) if len(prev_actual_num) == 2 and prev_actual_num.isdigit() else None
    prev_one = int(prev_actual_num[1]) if len(prev_actual_num) == 2 and prev_actual_num.isdigit() else None

    for num_str in all_nums:
        ten = int(num_str[0])
        one = int(num_str[1])
        num_sum = ten + one

        score = 100.0

        # Sum範囲フィルター
        if num_sum in [0, 1, 17, 18]:
            score -= 25.0
        elif 5 <= num_sum <= 13:
            score += 15.0

        # 偶奇バランス
        if (ten % 2 == 0) != (one % 2 == 0):
            score += 12.0
        else:
            score += 4.0

        # 大小バランス
        if (ten >= 5) != (one >= 5):
            score += 10.0
        else:
            score += 3.0

        # Zodiac / 差分ルール
        if ten == one:
            score -= 15.0
        if abs(ten - one) == 1:
            score += 8.0
        if abs(ten - one) == 5:
            score += 6.0

        # 前回当選番号からの連動（引っ張り / 近接）
        if prev_ten is not None and prev_one is not None:
            if (ten == prev_ten and one != prev_one) or (ten != prev_ten and one == prev_one):
                score += 18.0
            elif ten == prev_ten and one == prev_one:
                score -= 30.0

            if abs(ten - prev_ten) == 1 or abs(one - prev_one) == 1:
                score += 10.0

        # 日次シード揺らぎ
        det_factor = (hash(f"{seed_val}_{num_str}") % 1000) / 40.0
        score += det_factor

        scores[num_str] = score

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items[:20]]


# --- メイン UI 構成 ---
st.title("🎲 ナンバーズ3 ミニ 厳選予測")

tab1, tab2 = st.tabs(["🎯 当日予測", "📊 検証・結果登録"])

# === TAB 1: 予測画面 ===
with tab1:
    st.header(f"🎯 予測対象日: {display_date_str}")
    
    col_input, col_info = st.columns([1, 2])
    with col_input:
        prev_num_input = st.text_input(
            "前回の当選番号 (ミニ2桁)",
            value=latest_actual,
            max_chars=2,
            help="自動取得された最新の当選番号です。必要に応じて手動変更も可能です。"
        )

    # 2桁フォーマット補正
    prev_num_clean = prev_num_input.zfill(2) if prev_num_input.isdigit() else "00"

    # 20口計算
    top_20_nums = calculate_predictions(prev_num_clean, target_date_str)

    st.subheader(f"🔥 厳選 20 口（基準前回数字: {prev_num_clean}）")
    
    # 10×2 コンパクトグリッド表示
    row1 = top_20_nums[:10]
    row2 = top_20_nums[10:]

    def render_grid(num_list):
        cols = st.columns(10)
        for idx, num in enumerate(num_list):
            with cols[idx]:
                st.markdown(
                    f"<div style='text-align:center; background-color:#1e293b; color:#ffffff; "
                    f"padding:12px 4px; border-radius:8px; font-weight:bold; font-size:20px; "
                    f"border:1px solid #334155;'>{num}</div>",
                    unsafe_allow_html=True
                )

    render_grid(row1)
    st.write("")
    render_grid(row2)


# === TAB 2: 検証・登録画面 ===
with tab2:
    st.header("📊 当選結果の入力・検証")

    val_date = st.date_input("検証対象日", value=datetime.date.today())
    val_date_str = val_date.strftime('%Y-%m-%d')

    val_actual = st.text_input("実際の当選番号 (ミニ2桁)", max_chars=2, key="val_actual_input")

    if st.button("結果を記録して適用"):
        if len(val_actual) == 2 and val_actual.isdigit():
            # 重複日付があれば更新、なければ追加
            new_row = {'target_date': val_date_str, 'actual_num': val_actual, 'prev_num': latest_actual}
            
            if not df_history.empty and val_date_str in df_history['target_date'].values:
                df_history.loc[df_history['target_date'] == val_date_str, 'actual_num'] = val_actual
            else:
                df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(df_history)
            st.success(f"{val_date_str} の当選番号 『{val_actual}』 を記録しました！予想画面を更新します。")
            st.rerun()
        else:
            st.error("2桁の数字を入力してください。")

    st.subheader("📝 過去の記録")
    if not df_history.empty:
        st.dataframe(df_history.sort_values(by='target_date', ascending=False), use_container_width=True)
    else:
        st.info("記録されているデータはありません。")
