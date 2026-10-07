import streamlit as st
import pandas as pd
import datetime
import random
import numpy as np
import os

# ==============================================================================
# 1. アプリ基本設定 & スマホ1画面収まり用CSS
# ==============================================================================
st.set_page_config(
    page_title="ナンバーズ3 ミニ 厳選予測",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 横5列×4行でスクロールなしで20口を表示するHTML/CSS設定
st.markdown("""
    <style>
        .block-container { padding: 0.4rem 0.5rem !important; }
        .stApp { background-color: #0f172a; color: #f8fafc; }
        h1 { font-size: 18px !important; margin-bottom: 2px !important; margin-top: 0px !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 2px; }
        .stTabs [data-baseweb="tab"] { height: 34px; font-size: 13px; padding: 0 8px; }
        
        /* 5列×4行グリッド (スマホ対応) */
        .grid-container {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 4px;
            margin-top: 4px;
        }
        .grid-item {
            background-color: #1e293b;
            color: #ffffff;
            text-align: center;
            padding: 7px 0;
            border-radius: 6px;
            font-weight: bold;
            font-size: 18px;
            border: 1px solid #334155;
            box-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "prediction_history.csv"

# ==============================================================================
# 2. データ入出力 ＆ CSV空の時の自動補正（45/05を強制自動初期化）
# ==============================================================================
def load_data() -> pd.DataFrame:
    required_cols = ['target_date', 'actual_num', 'prev_num']
    
    # ファイルが存在しデータがある場合
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE, dtype=str)
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""
            if not df.empty:
                return df[required_cols]
        except Exception:
            pass

    # CSVが無い、または空の場合は10/6(05)と10/7(45)を自動初期登録
    initial_data = pd.DataFrame([
        {'target_date': '2026-10-06', 'actual_num': '05', 'prev_num': '00'},
        {'target_date': '2026-10-07', 'actual_num': '45', 'prev_num': '05'}
    ])
    initial_data.to_csv(CSV_FILE, index=False)
    return initial_data

def save_data(df: pd.DataFrame) -> None:
    df.to_csv(CSV_FILE, index=False)

df_history = load_data()

# ==============================================================================
# 3. 日本時間（JST）19:00切り替え ＆ 前回/前々回自動抽出
# ==============================================================================
# サーバー時間によらず「日本時間(JST)」で19:00切り替え判定
jst_tz = datetime.timezone(datetime.timedelta(hours=9))
now_jst = datetime.datetime.now(jst_tz)

if now_jst.hour >= 19:
    target_date_dt = now_jst.date() + datetime.timedelta(days=1)
else:
    target_date_dt = now_jst.date()

target_date_str = target_date_dt.strftime('%Y-%m-%d')
display_date_str = target_date_dt.strftime('%Y年%m月%d日')

# CSV履歴から前回・前々回を自動特定
latest_actual = "45"
prev_prev_actual = "05"

if not df_history.empty and 'actual_num' in df_history.columns:
    valid_records = df_history[
        df_history['actual_num'].notna() & (df_history['actual_num'] != "")
    ]
    if len(valid_records) >= 1:
        latest_actual = str(valid_records.iloc[-1]['actual_num']).zfill(2)
    if len(valid_records) >= 2:
        prev_prev_actual = str(valid_records.iloc[-2]['actual_num']).zfill(2)

# ==============================================================================
# 4. 統計的予測アルゴリズム
# ==============================================================================
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

        if num_sum in [0, 1, 17, 18]:
            score -= 25.0
        elif 5 <= num_sum <= 13:
            score += 15.0

        if (ten % 2 == 0) != (one % 2 == 0):
            score += 12.0
        else:
            score += 4.0

        if (ten >= 5) != (one >= 5):
            score += 10.0
        else:
            score += 3.0

        if ten == one:
            score -= 15.0
        if abs(ten - one) == 1:
            score += 8.0
        if abs(ten - one) == 5:
            score += 6.0

        if prev_ten is not None and prev_one is not None:
            if (ten == prev_ten and one != prev_one) or (ten != prev_ten and one == prev_one):
                score += 18.0
            elif ten == prev_ten and one == prev_one:
                score -= 30.0

            if abs(ten - prev_ten) == 1 or abs(one - prev_one) == 1:
                score += 10.0

        det_factor = (hash(f"{seed_val}_{num_str}") % 1000) / 40.0
        score += det_factor

        scores[num_str] = score

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [item[0] for item in sorted_items[:20]]

top_20_nums = calculate_predictions(latest_actual, target_date_str)

# ==============================================================================
# 5. UI（1画面完結型）
# ==============================================================================
st.title("🎲 ナンバーズ3 ミニ 厳選20口")

tab1, tab2 = st.tabs(["🎯 当日予測", "📊 結果検証・データ登録"])

# --- TAB 1: 予測画面 ---
with tab1:
    st.markdown(
        f"""
        <div style='background-color:#1e293b; padding:6px 10px; border-radius:6px; margin-bottom:4px; font-size:13px;'>
            <span style='color:#38bdf8; font-weight:bold;'>📅 予測対象: {display_date_str}</span><br>
            <span style='color:#cbd5e1;'>前回: <b style='color:#facc15;'>『{latest_actual}』</b> | 前々回: <b style='color:#94a3b8;'>『{prev_prev_actual}』</b></span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 横5列×縦4行のグリッドで一発表示
    items_html = "".join([f"<div class='grid-item'>{num}</div>" for num in top_20_nums])
    grid_html = f"<div class='grid-container'>{items_html}</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

# --- TAB 2: 結果登録画面 ---
with tab2:
    st.markdown("##### 📊 当選結果の入力・検証")
    
    st.markdown(
        f"""
        <div style='background-color:#1e293b; padding:6px 10px; border-radius:6px; margin-bottom:8px; font-size:12px;'>
            前回: <b style='color:#facc15;'>『{latest_actual}』</b> | 前々回: <b style='color:#94a3b8;'>『{prev_prev_actual}』</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_date, col_num = st.columns(2)
    with col_date:
        val_date = st.date_input("対象日", value=datetime.date.today())
        val_date_str = val_date.strftime('%Y-%m-%d')
    with col_num:
        val_actual = st.text_input("当選番号(2桁)", max_chars=2, key="val_actual_input", placeholder="例: 45")

    if st.button("登録して予測を更新", type="primary", use_container_width=True):
        if len(val_actual) == 2 and val_actual.isdigit():
            val_actual_clean = val_actual.zfill(2)
            if not df_history.empty and val_date_str in df_history['target_date'].values:
                df_history.loc[df_history['target_date'] == val_date_str, 'actual_num'] = val_actual_clean
            else:
                new_row = {'target_date': val_date_str, 'actual_num': val_actual_clean, 'prev_num': latest_actual}
                df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(df_history)
            st.success("登録完了！予測に反映します。")
            st.rerun()
        else:
            st.error("2桁の数字を入力してください")

    st.markdown("---")
    if not df_history.empty:
        display_df = df_history.sort_values(by='target_date', ascending=False).copy()
        display_df.columns = ['対象日付', '当選番号', '基準前回番号']
        st.dataframe(display_df, use_container_width=True, height=150)
