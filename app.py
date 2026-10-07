import streamlit as st
import pandas as pd
import datetime
import random
import numpy as np
import os

# ==============================================================================
# 1. アプリケーション基本設定
# ==============================================================================
st.set_page_config(
    page_title="ナンバーズ3 ミニ 予測・検証アプリケーション",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CSV_FILE = "prediction_history.csv"

# ==============================================================================
# 2. データ入出力関数（KeyError安全対策込み）
# ==============================================================================
def load_data() -> pd.DataFrame:
    """保存済みの予測履歴・結果検証データを読み込む（列不足エラーを自動補正）"""
    required_cols = ['target_date', 'actual_num', 'prev_num']
    
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE, dtype=str)
            # 必要な列が欠けている場合は自動補完
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ""
            return df[required_cols]
        except Exception:
            pass
            
    # ファイルがない、または壊れている場合は新規作成
    return pd.DataFrame(columns=required_cols)

def save_data(df: pd.DataFrame) -> None:
    """検証データをCSVファイルへ書き込む"""
    df.to_csv(CSV_FILE, index=False)

# データの初期ロード
df_history = load_data()

# ==============================================================================
# 3. 日時判定および基準ナンバー自動設定ロジック
# ==============================================================================
now = datetime.datetime.now()

# 19:00以降の判定: 当日の抽籤終了後は翌日へ自動切り替え
if now.hour >= 19:
    target_date_dt = now.date() + datetime.timedelta(days=1)
else:
    target_date_dt = now.date()

target_date_str = target_date_dt.strftime('%Y-%m-%d')
display_date_str = target_date_dt.strftime('%Y年%m月%d日')

# CSV履歴から最後に登録された有効な当選番号を自動抽出（KeyError防止策適用）
latest_actual = "00"
if not df_history.empty and 'actual_num' in df_history.columns:
    valid_records = df_history[
        df_history['actual_num'].notna() & (df_history['actual_num'] != "")
    ]
    if not valid_records.empty:
        latest_actual = str(valid_records.iloc[-1]['actual_num']).zfill(2)

# ==============================================================================
# 4. ナンバーズ3 ミニ 統計的予想・スコアリングエンジン
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

    prev_ten = None
    prev_one = None
    if len(prev_actual_num) == 2 and prev_actual_num.isdigit():
        prev_ten = int(prev_actual_num[0])
        prev_one = int(prev_actual_num[1])

    for num_str in all_nums:
        ten = int(num_str[0])
        one = int(num_str[1])
        num_sum = ten + one

        score = 100.0

        # Sum（合計値）
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

        # 特殊パターン
        if ten == one:
            score -= 15.0
        if abs(ten - one) == 1:
            score += 8.0
        if abs(ten - one) == 5:
            score += 6.0

        # 前回連動（引っ張り・スライド）
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

# ==============================================================================
# 5. UI Layout
# ==============================================================================
st.title("🎲 ナンバーズ3 ミニ 高精度厳選予測システム")
st.caption("統計解析・前回連動フィルタリングによる自動選出エンジン")

tab1, tab2 = st.tabs(["🎯 当日予測画面", "📊 結果検証・データ登録"])

# --- TAB 1 ---
with tab1:
    st.markdown(f"### 🎯 予測対象日: **{display_date_str}**")
    
    col_input, col_info = st.columns([1, 2])
    with col_input:
        prev_num_input = st.text_input(
            "前回の当選番号 (ミニ2桁)",
            value=latest_actual,
            max_chars=2,
            help="過去データから自動取得された直近の当選番号です。"
        )

    if prev_num_input.isdigit() and len(prev_num_input) > 0:
        prev_num_clean = prev_num_input.zfill(2)
    else:
        prev_num_clean = "00"

    top_20_nums = calculate_predictions(prev_num_clean, target_date_str)

    st.markdown("---")
    st.subheader(f"🔥 本日の厳選 20 口（基準前回数字: 『{prev_num_clean}』）")

    row1 = top_20_nums[:10]
    row2 = top_20_nums[10:]

    def render_compact_grid(num_list):
        cols = st.columns(10)
        for idx, num in enumerate(num_list):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="
                        text-align: center;
                        background-color: #1e293b;
                        color: #ffffff;
                        padding: 14px 2px;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 22px;
                        border: 1px solid #334155;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        margin-bottom: 5px;
                    ">
                        {num}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    render_compact_grid(row1)
    render_compact_grid(row2)

    st.markdown("---")
    st.info("💡 19:00を過ぎると自動的に「翌日分の予測」に切り替わります。")

# --- TAB 2 ---
with tab2:
    st.header("📊 当選結果の入力と自動更新")
    
    col_date, col_num = st.columns([1, 1])
    with col_date:
        val_date = st.date_input("検証対象日", value=datetime.date.today())
        val_date_str = val_date.strftime('%Y-%m-%d')

    with col_num:
        val_actual = st.text_input(
            "実際の当選番号 (ミニ2桁)",
            max_chars=2,
            key="val_actual_input",
            placeholder="例: 45"
        )

    if st.button("当選番号を記録して予測を更新する", type="primary"):
        if len(val_actual) == 2 and val_actual.isdigit():
            val_actual_clean = val_actual.zfill(2)
            
            if not df_history.empty and val_date_str in df_history['target_date'].values:
                df_history.loc[df_history['target_date'] == val_date_str, 'actual_num'] = val_actual_clean
            else:
                new_row = {
                    'target_date': val_date_str,
                    'actual_num': val_actual_clean,
                    'prev_num': latest_actual
                }
                df_history = pd.concat([df_history, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(df_history)
            st.success(f"【記録完了】 {val_date_str} の当選番号 『{val_actual_clean}』 を登録しました！")
            st.rerun()
        else:
            st.error("⚠️ 2桁の半角数字（例: 45）を正しく入力してください。")

    st.markdown("---")
    st.subheader("📝 過去の登録データ・検証履歴")
    if not df_history.empty:
        display_df = df_history.sort_values(by='target_date', ascending=False)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("過去の記録データはまだありません。")
