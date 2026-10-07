import streamlit as st
import pandas as pd
import datetime
import random
import numpy as np
import os

# ==============================================================================
# 1. アプリ基本設定 & CSS
# ==============================================================================
st.set_page_config(
    page_title="ナンバーズ3 ミニ 厳選予測",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .block-container { padding: 0.4rem 0.5rem !important; }
        .stApp { background-color: #0f172a; color: #f8fafc; }
        h1 { font-size: 18px !important; margin-bottom: 2px !important; margin-top: 0px !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 2px; }
        .stTabs [data-baseweb="tab"] { height: 34px; font-size: 13px; padding: 0 8px; }
        
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
# 2. データロード & 初期データ設定
# ==============================================================================
def load_data() -> pd.DataFrame:
    required_cols = ['target_date', 'actual_num', 'prev_num']
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

    # 正しい履歴データ (10/7の基準前回は05)
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
# 3. 日本時間（JST）判定 & 前回・前々回取得
# ==============================================================================
jst_tz = datetime.timezone(datetime.timedelta(hours=9))
now_jst = datetime.datetime.now(jst_tz)

if now_jst.hour >= 19:
    target_date_dt = now_jst.date() + datetime.timedelta(days=1)
else:
    target_date_dt = now_jst.date()

target_date_str = target_date_dt.strftime('%Y-%m-%d')
display_date_str = target_date_dt.strftime('%Y年%m月%d日')

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
# 5. UI
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

    items_html = "".join([f"<div class='grid-item'>{num}</div>" for num in top_20_nums])
    grid_html = f"<div class='grid-container'>{items_html}</div>"
    st.markdown(grid_html, unsafe_allow_html=True)

# --- TAB 2: 結果検証＆登録画面 ---
with tab2:
    st.markdown("##### 📊 当選番号の登録・自動的中検証")

    col_date, col_num = st.columns(2)
    with col_date:
        val_date = st.date_input("対象日", value=datetime.date.today())
        val_date_str = val_date.strftime('%Y-%m-%d')
    with col_num:
        val_actual = st.text_input("当選番号(2桁)", max_chars=2, key="val_actual_input", placeholder="例: 45")

    if st.button("登録して勝率を再計算", type="primary", use_container_width=True):
        if len(val_actual) == 2 and val_actual.isdigit():
            val_actual_clean = val_actual.zfill(2)
            
            # 正しい「基準前回」を既存履歴から検索取得
            calc_prev = "00"
            if not df_history.empty:
                prev_records = df_history[df_history['target_date'] < val_date_str].sort_values(by='target_date')
                if not prev_records.empty:
                    calc_prev = str(prev_records.iloc[-1]['actual_num']).zfill(2)

            if not df_history.empty and val_date_str in df_history['target_date'].values:
                df_history.loc[df_history['target_date'] == val_date_str, 'actual_num'] = val_actual_clean
            else:
                new_row = {'target_date': val_date_str, 'actual_num': val_actual_clean, 'prev_num': calc_prev}
                df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(df_history)
            st.success("登録完了！勝率データを正しく更新しました。")
            st.rerun()
        else:
            st.error("2桁の数字を入力してください")

    st.markdown("---")

    if not df_history.empty:
        verify_list = []
        total_trials = 0
        total_hits = 0

        # 正しい過去検証ロジック
        sorted_df = df_history.sort_values(by='target_date').reset_index(drop=True)
        for idx, row in sorted_df.iterrows():
            t_date = str(row['target_date'])
            act_num = str(row['actual_num']).zfill(2) if pd.notna(row['actual_num']) and str(row['actual_num']) != "" else None
            
            # 前日データの当選番号を「基準前回」として適用
            if idx == 0:
                p_num = str(row['prev_num']).zfill(2) if pd.notna(row['prev_num']) and str(row['prev_num']) != "" else "00"
            else:
                p_num = str(sorted_df.iloc[idx-1]['actual_num']).zfill(2)

            if act_num:
                total_trials += 1
                preds = calculate_predictions(p_num, t_date)
                
                if act_num in preds:
                    rank = preds.index(act_num) + 1
                    status = f"🎯 的中 ({rank}位)"
                    total_hits += 1
                else:
                    status = "❌ 不的中"

                verify_list.append({
                    '対象日': t_date,
                    '当選番号': act_num,
                    '検証結果': status,
                    '基準前回': p_num
                })

        hit_rate = (total_hits / total_trials * 100) if total_trials > 0 else 0
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("通算的中率", f"{hit_rate:.1f}%")
        with c2:
            st.metric("的中数", f"{total_hits} / {total_trials} 回")
        with c3:
            st.metric("不的中数", f"{total_trials - total_hits} 回")

        if verify_list:
            res_df = pd.DataFrame(verify_list).sort_values(by='対象日', ascending=False)
            st.dataframe(res_df, use_container_width=True, height=180)
