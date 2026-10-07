import streamlit as st
import pandas as pd
import datetime
import random
import numpy as np
import os

# ==============================================================================
# 1. アプリケーション基本設定（画面ワイド・タイトル設定）
# ==============================================================================
st.set_page_config(
    page_title="ナンバーズ3 ミニ 予測・検証アプリケーション",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 保存用CSVファイルのパス定義
CSV_FILE = "prediction_history.csv"


# ==============================================================================
# 2. データ入出力関数（CSV永続化ロジック）
# ==============================================================================
def load_data() -> pd.DataFrame:
    """保存済みの予測履歴・結果検証データを読み込む"""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(
                CSV_FILE,
                dtype={'target_date': str, 'actual_num': str, 'prev_num': str}
            )
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=['target_date', 'actual_num', 'prev_num'])


def save_data(df: pd.DataFrame) -> None:
    """検証データをCSVファイルへ書き込む"""
    df.to_csv(CSV_FILE, index=False)


# データの初期ロード
df_history = load_data()


# ==============================================================================
# 3. 日時判定および基準ナンバー自動設定ロジック
# ==============================================================================
now = datetime.datetime.now()

# 19:00以降の判定: 当日の抽籤終了後は翌日（10/8等）へ自動切り替え
if now.hour >= 19:
    target_date_dt = now.date() + datetime.timedelta(days=1)
else:
    target_date_dt = now.date()

target_date_str = target_date_dt.strftime('%Y-%m-%d')
display_date_str = target_date_dt.strftime('%Y年%m月%d日')

# CSV履歴から最後に登録された有効な当選番号を自動抽出
latest_actual = "00"
if not df_history.empty:
    valid_records = df_history[
        df_history['actual_num'].notna() & (df_history['actual_num'] != "")
    ]
    if not valid_records.empty:
        latest_actual = str(valid_records.iloc[-1]['actual_num']).zfill(2)


# ==============================================================================
# 4. ナンバーズ3 ミニ 統計的予想・スコアリングエンジン（全ロジック完全記述）
# ==============================================================================
def calculate_predictions(prev_actual_num: str, seed_date_str: str) -> list:
    """
    全100通りの数字（00〜99）に対して各種統計フィルターを適用し、
    決定論的シード（日付ベース）のもとで上位20口を選出する。
    """
    # シード値の生成（YYYYMMDD形式の数値）
    try:
        seed_val = int(seed_date_str.replace('-', ''))
    except ValueError:
        seed_val = 20261008

    random.seed(seed_val)
    np.random.seed(seed_val)

    all_nums = [f"{i:02d}" for i in range(100)]
    scores = {}

    # 前回当選番号の分解（十の位・一の位）
    prev_ten = None
    prev_one = None
    if len(prev_actual_num) == 2 and prev_actual_num.isdigit():
        prev_ten = int(prev_actual_num[0])
        prev_one = int(prev_actual_num[1])

    for num_str in all_nums:
        ten = int(num_str[0])
        one = int(num_str[1])
        num_sum = ten + one

        score = 100.0  # 基本スコア

        # ----------------------------------------------------------------------
        # A. Sum（合計値）フィルタリング
        # ----------------------------------------------------------------------
        if num_sum in [0, 1, 17, 18]:
            score -= 25.0  # 極端な端数（0, 1, 17, 18）は大幅減点
        elif 5 <= num_sum <= 13:
            score += 15.0  # 出現頻度の高い中央帯（5〜13）は加点

        # ----------------------------------------------------------------------
        # B. Parity（偶奇バランス）フィルタリング
        # ----------------------------------------------------------------------
        ten_is_even = (ten % 2 == 0)
        one_is_even = (one % 2 == 0)
        if ten_is_even != one_is_even:
            score += 12.0  # 偶奇ペア（偶・奇 または 奇・偶）は優遇
        else:
            score += 4.0   # 同種ペア（偶・偶 または 奇・奇）は控えめな加点

        # ----------------------------------------------------------------------
        # C. Big-Small（大小バランス）フィルタリング（5以上を「大」とする）
        # ----------------------------------------------------------------------
        ten_is_big = (ten >= 5)
        one_is_big = (one >= 5)
        if ten_is_big != one_is_big:
            score += 10.0  # 大小ペア（大・小 または 小・大）は優遇
        else:
            score += 3.0   # 同大小ペアは控えめな加点

        # ----------------------------------------------------------------------
        # D. Zodiac / 差分 / 特殊数字パターンルール
        # ----------------------------------------------------------------------
        if ten == one:
            score -= 15.0  # ゾロ目（00, 11...）は出現率が低いため減点
        if abs(ten - one) == 1:
            score += 8.0   # 連番（12, 23, 89など）は加点
        if abs(ten - one) == 5:
            score += 6.0   # 裏数字関係（05, 16, 27など）は加点

        # ----------------------------------------------------------------------
        # E. 前回当選番号からの連動ルール（引っ張り・近接・重複減点）
        # ----------------------------------------------------------------------
        if prev_ten is not None and prev_one is not None:
            # 1. 引っ張りルール（片方の桁のみ一致）
            if (ten == prev_ten and one != prev_one) or (ten != prev_ten and one == prev_one):
                score += 18.0
            # 2. 完全同一（連続ゾロ引き）の大幅減点
            elif ten == prev_ten and one == prev_one:
                score -= 30.0

            # 3. 近接数字・スライド（どちらかの桁が±1）
            if abs(ten - prev_ten) == 1 or abs(one - prev_one) == 1:
                score += 10.0

        # ----------------------------------------------------------------------
        # F. 日次シードによる微細決定論的揺らぎ（同点時のソート順固定）
        # ----------------------------------------------------------------------
        det_factor = (hash(f"{seed_val}_{num_str}") % 1000) / 40.0
        score += det_factor

        scores[num_str] = score

    # スコアが高い順にソートし、上位20口を厳選
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_20 = [item[0] for item in sorted_items[:20]]
    return top_20


# ==============================================================================
# 5. UI（ユーザーインターフェース）レイアウト定義
# ==============================================================================
st.title("🎲 ナンバーズ3 ミニ 高精度厳選予測システム")
st.caption("統計解析・前回連動フィルタリングによる自動選出エンジン")

# タブ構成（TAB1: 当日予測 / TAB2: 検証・結果登録）
tab1, tab2 = st.tabs(["🎯 当日予測画面", "📊 結果検証・データ登録"])


# ------------------------------------------------------------------------------
# TAB 1: 予測画面（メイン画面）
# ------------------------------------------------------------------------------
with tab1:
    st.markdown(f"### 🎯 予測対象日: **{display_date_str}**")
    
    # 前回の当選番号の確認・入力エリア
    col_input, col_info = st.columns([1, 2])
    with col_input:
        prev_num_input = st.text_input(
            "前回の当選番号 (ミニ2桁)",
            value=latest_actual,
            max_chars=2,
            help="過去データから自動取得された直近の当選番号です。手動で切り替えてシミュレーションすることもできます。"
        )

    # 入力値のフォーマット整形（数値2桁化）
    if prev_num_input.isdigit() and len(prev_num_input) > 0:
        prev_num_clean = prev_num_input.zfill(2)
    else:
        prev_num_clean = "00"

    # 厳選20口の計算実行
    top_20_nums = calculate_predictions(prev_num_clean, target_date_str)

    st.markdown("---")
    st.subheader(f"🔥 本日の厳選 20 口（基準前回数字: 『{prev_num_clean}』）")
    st.write("※以下の20口は統計スコア上位の推奨組み合わせです。")

    # 10×2 コンパクトグリッド描画処理
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
    st.info("💡 19:00を過ぎると自動的に「翌日分の予測」に切り替わります。TAB2で本日の当選番号を登録してください。")


# ------------------------------------------------------------------------------
# TAB 2: 検証・登録画面
# ------------------------------------------------------------------------------
with tab2:
    st.header("📊 当選結果の入力と自動更新")
    st.write("本日の実際の当選番号（下2桁）を入力して登録してください。")

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

    # 結果確定ボタン処理
    if st.button("当選番号を記録して予測を更新する", type="primary"):
        if len(val_actual) == 2 and val_actual.isdigit():
            val_actual_clean = val_actual.zfill(2)
            
            # 既存データがあれば更新、なければ新規行追加
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
        # 日付降順で表示
        display_df = df_history.sort_values(by='target_date', ascending=False)
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("過去の記録データはまだありません。上記のフォームから登録を行ってください。")
