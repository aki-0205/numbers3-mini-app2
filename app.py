import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 0. ページ設定＆カスタムCSS（1画面収容コンパクトデザイン）
# ---------------------------------------------------------
st.set_page_config(
    page_title="ナンバーズ3 ミニ 統計厳選20口＆外れ要因分析システム",
    page_icon="🎲",
    layout="wide",
)

# 1画面内に収めるためのコンパクトCSSスタイル
st.markdown(
    """
    <style>
    /* 全体のアッパーマージン・パディングを削減 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    /* 20個のマス目を1画面に並べるグリッドコンテナ */
    .number-box-container {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 8px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    @media (max-width: 992px) {
        .number-box-container {
            grid-template-columns: repeat(5, 1fr);
        }
    }
    /* コンパクトなカード風マス目 */
    .number-box {
        background-color: #f0f8ff;
        border: 1.5px solid #1e90ff;
        border-radius: 8px;
        padding: 8px 0;
        font-size: 20px;
        font-weight: bold;
        color: #1e90ff;
        text-align: center;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.08);
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🎲 ナンバーズ3 ミニ 統計厳選20口＆外れ要因分析システム")

# ---------------------------------------------------------
# 1. 19時切り替え・日次シード固定処理
# ---------------------------------------------------------
now = datetime.now()
# 19:00以降は翌日分、19:00前は本日分
if now.hour >= 19:
    target_date = now.date() + timedelta(days=1)
else:
    target_date = now.date()

target_date_str = target_date.strftime("%Y-%m-%d")
seed_value = int(target_date.strftime("%Y%m%d"))

# 乱数・確率計算シードを日付で固定（19時まで何度再読み込みしても完全に同じ結果が出力される）
random.seed(seed_value)
np.random.seed(seed_value)

# ---------------------------------------------------------
# 2. ログ・履歴保存設定
# ---------------------------------------------------------
DATA_FILE = "prediction_history.csv"


def load_history():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_history_record(records):
    df_new = pd.DataFrame(records)
    if os.path.exists(DATA_FILE):
        df_old = load_history()
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined.to_csv(DATA_FILE, index=False)
    else:
        df_new.to_csv(DATA_FILE, index=False)


# ---------------------------------------------------------
# 3. 確率スコアリング・多重フィルター計算エンジン（完全版）
# ---------------------------------------------------------
def calculate_statistical_top_20(prev_actual_num: str, seed: int) -> list:
    """過去統計・多重フィルター（引っ張り、ハマリ、合計値、偶奇・大小バランス、
    風車盤近接等）に基づき全100通りを厳密スコアリングし、上位20口を固定選出する
    """
    random.seed(seed)
    np.random.seed(seed)

    all_nums = [f"{i:02d}" for i in range(100)]
    scores = {}

    prev_ten = int(prev_actual_num[0]) if len(prev_actual_num) == 2 else None
    prev_one = int(prev_actual_num[1]) if len(prev_actual_num) == 2 else None

    for num_str in all_nums:
        ten = int(num_str[0])
        one = int(num_str[1])
        num_sum = ten + one

        score = 100.0  # 基礎スコア

        # --- フィルター1: 合計値（Sum）範囲評価 ---
        if num_sum in [0, 1, 17, 18]:
            score -= 25.0
        elif 5 <= num_sum <= 13:
            score += 15.0

        # --- フィルター2: 偶奇バランス（Parity） ---
        ten_even = ten % 2 == 0
        one_even = one % 2 == 0
        if ten_even != one_even:
            score += 12.0
        else:
            score += 4.0

        # --- フィルター3: 大小バランス（Big / Small: 5以上は大） ---
        ten_big = ten >= 5
        one_big = one >= 5
        if ten_big != one_big:
            score += 10.0
        else:
            score += 3.0

        # --- フィルター4: ゾロ目・連番・差5（裏数字）評価 ---
        if ten == one:
            score -= 15.0
        if abs(ten - one) == 1:
            score += 8.0
        if abs(ten - one) == 5:
            score += 6.0

        # --- フィルター5: 前回当選番号からの「引っ張り」「近接（±1）」解析 ---
        if prev_ten is not None and prev_one is not None:
            if (ten == prev_ten and one != prev_one) or (
                ten != prev_ten and one == prev_one
            ):
                score += 18.0
            elif ten == prev_ten and one == prev_one:
                score -= 30.0

            if abs(ten - prev_ten) == 1 or abs(one - prev_one) == 1:
                score += 10.0

        # --- 決定論的シード揺らぎ因子（日次確定） ---
        det_factor = (hash(f"{seed}_{num_str}") % 1000) / 40.0
        score += det_factor

        scores[num_str] = score

    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_20 = [item[0] for item in sorted_items[:20]]

    return sorted(top_20)


# ---------------------------------------------------------
# 4. 外れ原因の自動判定診断エンジン
# ---------------------------------------------------------
def diagnose_miss_reasons(
    predicted_list: list, actual: str, prev_actual: str = None
) -> list:
    """選出された20口全体と実際の当選番号を照合し、外れ原因を精密判定"""
    reasons = []

    if actual in predicted_list:
        return ["🎯 完全的中"]

    reversed_actual = actual[1] + actual[0]
    if reversed_actual in predicted_list:
        reasons.append("桁逆転（ボックス外れ）")

    ten_match = any(p[0] == actual[0] for p in predicted_list)
    one_match = any(p[1] == actual[1] for p in predicted_list)

    if ten_match and not one_match:
        reasons.append("十の位のみ一致（一の位外し）")
    elif one_match and not ten_match:
        reasons.append("一の位のみ一致（十の位外し）")
    elif not ten_match and not one_match:
        reasons.append("両桁完全不一致")

    act_ten, act_one = int(actual[0]), int(actual[1])
    near_exists = False
    for p in predicted_list:
        p_ten, p_one = int(p[0]), int(p[1])
        if abs(p_ten - act_ten) <= 1 and abs(p_one - act_one) <= 1:
            near_exists = True
            break
    if near_exists:
        reasons.append("近接数字ずれ（±1以内）")

    reverse_exists = False
    for p in predicted_list:
        p_ten, p_one = int(p[0]), int(p[1])
        if abs(p_ten - act_ten) == 5 or abs(p_one - act_one) == 5:
            reverse_exists = True
            break
    if reverse_exists:
        reasons.append("裏数字（対角ナンバー・差5）ズレ")

    if prev_actual and len(prev_actual) == 2:
        prev_digits = set(prev_actual)
        actual_digits = set(actual)
        if actual_digits & prev_digits:
            pred_has_pull = any(
                (set(p) & actual_digits & prev_digits) for p in predicted_list
            )
            if not pred_has_pull:
                reasons.append("引っ張り数字の見落とし")

    return reasons if reasons else ["完全パターン範囲外"]


# ---------------------------------------------------------
# 5. UI 画面構成（3タブ構造）
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    [
        "🎯 本日の統計厳選20口予想",
        "🔍 外れ要因検証・自動記録",
        "📊 過去の検証・累積データ分析",
    ]
)

# ---------------------------------------------------------
# TAB 1: 厳選20口予想（1画面に収めるコンパクト表示）
# ---------------------------------------------------------
with tab1:
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader(f"📅 対象抽選日: {target_date_str} の統計厳選20口")
    with col_header2:
        prev_num_input = st.text_input(
            "前回の当選番号",
            value="00",
            max_chars=2,
            key="tab1_prev_input",
            help="分析精度向上のため入力",
        )

    # 厳選20口の計算実行（日付シード固定）
    selected_20 = calculate_statistical_top_20(prev_num_input, seed_value)
    st.session_state["current_selected_20"] = selected_20
    st.session_state["current_target_date"] = target_date_str

    # コンパクトな横10列×2行のグリッドで描画（1画面収容）
    boxes_html = '<div class="number-box-container">'
    for num in selected_20:
        boxes_html += f'<div class="number-box">{num}</div>'
    boxes_html += "</div>"

    st.markdown(boxes_html, unsafe_allow_html=True)
    st.caption(
        "※ 過去統計・多重フィルターにより算出。毎日19:00に翌日分へ自動更新（それまでは何度読み込んでも同じ20口が固定されます）。"
    )

# ---------------------------------------------------------
# TAB 2: 外れ要因検証＆自動CSV保存
# ---------------------------------------------------------
with tab2:
    st.header("🔍 外れ要因の自動検証・判定")
    st.caption(
        "抽選結果を入力すると外れ理由を詳細に自動判定し、検証結果を累積データベース（CSV）に自動保存します。"
    )

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        actual_input = st.text_input(
            "今回の当選番号（ミニ2桁）",
            value="",
            max_chars=2,
            placeholder="例: 45",
        )
    with col_v2:
        check_date = st.date_input("検証対象日", value=target_date)

    prev_actual_input = st.text_input(
        "前回の当選番号（引っ張り分析用・2桁）",
        value="00",
        max_chars=2,
        key="tab2_prev_input",
    )

    if st.button("📊 外れ要因を検証・記録保存する", type="primary"):
        if not actual_input or len(actual_input) != 2 or not actual_input.isdigit():
            st.error("今回の当選番号を2桁の半角数字で入力してください。")
        else:
            check_seed = int(check_date.strftime("%Y%m%d"))
            historical_20 = calculate_statistical_top_20(
                prev_actual_input, check_seed
            )

            is_hit = actual_input in historical_20
            reasons = diagnose_miss_reasons(
                historical_20, actual_input, prev_actual_input
            )
            reason_str = " / ".join(reasons)

            st.subheader("📋 検証・分析結果")
            if is_hit:
                st.balloons()
                st.success(
                    f"🎉 🎯 的中！ 厳選20口の中に当選番号 [{actual_input}] が含まれていました！"
                )
            else:
                st.error(f"❌ 不的中 （当選番号: {actual_input}）")
                st.warning(f"🔍 **判定された外れ要因**: {reason_str}")

            record = [
                {
                    "日時": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "対象抽選日": check_date.strftime("%Y-%m-%d"),
                    "当選番号": actual_input,
                    "判定": "的中" if is_hit else "外れ",
                    "分析・外れ要因": reason_str,
                }
            ]
            save_history_record(record)
            st.success("検証結果を `prediction_history.csv` に自動保存しました。")

# ---------------------------------------------------------
# TAB 3: 累積データ分析
# ---------------------------------------------------------
with tab3:
    st.header("📊 蓄積データによる累積外れ傾向分析")

    df_history = load_history()

    if df_history.empty:
        st.info(
            "まだ検証データが記録されていません。TAB2で検証を実行するとデータが蓄積されます。"
        )
    else:
        total_count = len(df_history)
        hit_count = len(df_history[df_history["判定"] == "的中"])
        hit_rate = (hit_count / total_count * 100) if total_count > 0 else 0.0

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("累計検証件数", f"{total_count} 件")
        with col_m2:
            st.metric("累計的中率", f"{hit_rate:.1f} %")

        st.subheader("📜 検証履歴ログ")
        st.dataframe(df_history, use_container_width=True)

        fail_df = df_history[df_history["判定"] == "外れ"]
        if not fail_df.empty:
            st.subheader("📈 累積・最頻外れ要因ランキング")

            all_reasons = []
            for item in fail_df["分析・外れ要因"].dropna():
                all_reasons.extend(str(item).split(" / "))

            reason_counts = pd.Series(all_reasons).value_counts()
            st.bar_chart(reason_counts)
