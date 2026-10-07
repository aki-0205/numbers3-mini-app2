import streamlit as st
import pandas as pd
import datetime
import random
import numpy as np
import os

# ==============================================================================
# 1. アプリ基本設定 & 1画面収まり用CSS
# ==============================================================================
st.set_page_config(
    page_title="ナンバーズ3 ミニ 厳選予測",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# スクロール不要で1画面に収めるためのスタイル定義
st.markdown("""
    <style>
        .block-container { padding-top: 0.8rem; padding-bottom: 0.5rem; padding-left: 0.8rem; padding-right: 0.8rem; }
        .stApp { background-color: #0f172a; color: #f8fafc; }
        h1, h2, h3, h4, h5 { margin-bottom: 0.3rem !important; padding-top: 0rem !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 4px; }
        .stTabs [data-baseweb="tab"] { height: 38px; font-size: 14px; padding-left: 12px; padding-right: 12px; }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "prediction_history.csv"

# ==============================================================================
# 2. データ入出力（KeyError・欠損自動対策）
# ==============================================================================
def load_data() -> pd.DataFrame:
    required_cols = ['target_date', 'actual_num', 'prev_num']
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE, dtype=str)
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""
            return df[required_cols]
        except Exception:
            pass
    return pd.DataFrame(columns=required_cols)

def save_data(df: pd.DataFrame) -> None:
    df.to_csv(CSV_FILE, index=False)

df_history = load_data()

# ==============================================================================
# 3. 日時自動切り替え & 前回・前々回数字の自動取得
# ==============================================================================
now = datetime.datetime.now()

# 19:00を境に翌日へ自動切り替え
if now.hour >= 19:
    target_date_dt = now.date() + datetime.timedelta(days=1)
else:
    target_date_dt = now.date()

target_date_str = target_date_dt.strftime('%Y-%m-%d')
display_date_str = target_date_dt.strftime('%Y年%m月%d日')

# 過去データから前回・前々回の数字を自動特定
latest_actual = "00"
prev_prev_actual = "なし"

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

        # Sum範囲
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

        # パターンルール
        if ten == one:
            score -= 15.0
        if abs(ten - one) == 1:
            score += 8.0
        if abs(ten - one) == 5:
            score += 6.0

        # 前回連動ルール（引っ張り・スライド）
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

# 予測の実行
top_20_nums = calculate_predictions(latest_actual, target_date_str)

# ==============================================================================
# 5. UI（1画面完結レイアウト）
# ==============================================================================
st.title("🎲 ナンバーズ3 ミニ 厳選予測")

tab1, tab2 = st.tabs(["🎯 当日予測", "📊 検証・過去履歴"])

# --- TAB 1: 予想画面 ---
with tab1:
    # 日付と前回・前々回数字を1行でコンパクト表示
    st.markdown(
        f"""
        <div style='background-color:#1e293b; padding:8px 12px; border-radius:6px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;'>
            <span style='font-size:15px; font-weight:bold; color:#38bdf8;'>📅 予測対象日: {display_date_str}</span>
            <span style='font-size:13px; color:#cbd5e1;'>
                前回: <b style='color:#facc15; font-size:15px;'>『{latest_actual}』</b> 
                <span style='color:#64748b; margin:0 4px;'>|</span> 
                前々回: <b style='color:#94a3b8; font-size:14px;'>『{prev_prev_actual}』</b>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1画面収まりグリッド（10列 × 2行）
    row1 = top_20_nums[:10]
    row2 = top_20_nums[10:]

    def render_1page_grid(num_list):
        cols = st.columns(10)
        for idx, num in enumerate(num_list):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="
                        text-align: center;
                        background-color: #334155;
                        color: #ffffff;
                        padding: 7px 0px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 18px;
                        border: 1px solid #475569;
                        margin-bottom: 5px;
                    ">
                        {num}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    render_1page_grid(row1)
    render_1page_grid(row2)

# --- TAB 2: 検証・履歴画面 ---
with tab2:
    st.markdown("##### 📊 抽選結果の登録と履歴確認")

    # 直近の状況サマリーカード
    st.markdown(
        f"""
        <div style='background-color:#1e293b; padding:10px; border-radius:6px; margin-bottom:12px; border-left:4px solid #38bdf8;'>
            <b>【直近の当選データ状態】</b><br>
            ・直近（前回）当選番号: <b style='color:#facc15;'>『{latest_actual}』</b><br>
            ・その前（前々回）当選番号: <b style='color:#94a3b8;'>『{prev_prev_actual}』</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_date, col_num, col_btn = st.columns([1, 1, 1])
    
    with col_date:
        val_date = st.date_input("対象日", value=datetime.date.today(), label_visibility="collapsed")
        val_date_str = val_date.strftime('%Y-%m-%d')

    with col_num:
        val_actual = st.text_input("当選番号(2桁)", max_chars=2, key="val_actual_input", placeholder="例: 45", label_visibility="collapsed")

    with col_btn:
        if st.button("登録する", type="primary", use_container_width=True):
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
                st.error("2桁数字を入力してください")

    st.markdown("---")
    st.markdown("###### 📝 全履歴一覧（上ほど最新）")
    if not df_history.empty:
        # 見やすい形式に整えて表示
        display_df = df_history.sort_values(by='target_date', ascending=False).copy()
        display_df.columns = ['対象日付', '当選番号(ミニ)', '基準前回番号']
        st.dataframe(display_df, use_container_width=True, height=180)
    else:
        st.info("登録データはまだありません。")
