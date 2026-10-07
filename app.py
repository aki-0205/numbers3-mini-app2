import os
import random
from datetime import datetime
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 0. ファイル保存の設定（CSVデータベース）
# ---------------------------------------------------------
DATA_FILE = "prediction_history.csv"


def load_history():
    """過去の検証ログを読み込む"""
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def save_history_record(records):
    """検証結果をCSVに追記保存する"""
    df_new = pd.DataFrame(records)
    if os.path.exists(DATA_FILE):
        df_old = load_history()
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        df_combined.to_csv(DATA_FILE, index=False)
    else:
        df_new.to_csv(DATA_FILE, index=False)


# ---------------------------------------------------------
# 1. ページ基本設定
# ---------------------------------------------------------
st.set_page_config(
    page_title="ナンバーズ3 ミニ 予測 & 高精度外れ検証システム",
    page_icon="🎲",
    layout="wide",
)

st.title("🎲 ナンバーズ3 ミニ 予測 & 高精度外れ検証システム")


# ---------------------------------------------------------
# 2. 予測・検証コアロジック
# ---------------------------------------------------------
def generate_predictions(
    filter_parity: str, filter_bs: str, count: int = 5
) -> list:
    """予測数字の生成ロジック（フィルター適用）"""
    candidates = []
    attempts = 0
    max_attempts = 2000

    while len(candidates) < count and attempts < max_attempts:
        attempts += 1
        num = f"{random.randint(0, 99):02d}"
        ten, one = int(num[0]), int(num[1])

        # 偶奇フィルター
        if filter_parity == "偶・偶" and not (ten % 2 == 0 and one % 2 == 0):
            continue
        elif filter_parity == "奇・奇" and not (ten % 2 != 0 and one % 2 != 0):
            continue
        elif filter_parity == "偶・奇" and not (
            ten % 2 == 0 and one % 2 != 0
        ):
            continue
        elif filter_parity == "奇・偶" and not (
            ten % 2 != 0 and one % 2 == 0
        ):
            continue

        # 大小フィルター (5以上は大)
        if filter_bs == "大・大" and not (ten >= 5 and one >= 5):
            continue
        elif filter_bs == "小・小" and not (ten < 5 and one < 5):
            continue
        elif filter_bs == "大・小" and not (ten >= 5 and one < 5):
            continue
        elif filter_bs == "小・大" and not (ten < 5 and one >= 5):
            continue

        if num not in candidates:
            candidates.append(num)

    return candidates


def diagnose_miss_reason(
    predicted: str, actual: str, prev_actual: str = None
) -> list:
    """予想数字と当選数字を徹底比較し、外れ要因をマルチアングルで判定"""
    reasons = []

    if not (
        len(predicted) == 2
        and predicted.isdigit()
        and len(actual) == 2
        and actual.isdigit()
    ):
        return ["入力形式エラー"]

    p_ten, p_one = int(predicted[0]), int(predicted[1])
    a_ten, a_one = int(actual[0]), int(actual[1])

    # 1. 完全的中
    if predicted == actual:
        return ["🎯 的中"]

    # 2. ボックス（並び順逆転）
    if predicted[::-1] == actual:
        reasons.append("桁位置逆転（ボックス外れ）")

    # 3. 桁ごとの一致チェック
    ten_match = p_ten == a_ten
    one_match = p_one == a_one

    if ten_match and not one_match:
        reasons.append("一の位のみ不一致")
    elif not ten_match and one_match:
        reasons.append("十の位のみ不一致")
    elif not ten_match and not one_match and predicted[::-1] != actual:
        reasons.append("両桁不一致")

    # 4. 風車盤・差分距離の細分化判定
    diff_ten = abs(p_ten - a_ten)
    diff_one = abs(p_one - a_one)

    if diff_ten == 1 or diff_one == 1:
        reasons.append("近接数字ずれ（±1差）")
    if diff_ten == 2 or diff_one == 2:
        reasons.append("近接数字ずれ（±2差）")
    if diff_ten == 5 or diff_one == 5:
        reasons.append("裏数字（対角ナンバー・差5）")

    # 5. 偶奇（Parity）パターン不一致
    p_parity = (p_ten % 2, p_one % 2)
    a_parity = (a_ten % 2, a_one % 2)
    if p_parity != a_parity:
        reasons.append("偶奇パターン不一致")

    # 6. 大小（Big/Small）パターン不一致
    p_bs = (p_ten >= 5, p_one >= 5)
    a_bs = (a_ten >= 5, a_one >= 5)
    if p_bs != a_bs:
        reasons.append("大小パターン不一致")

    # 7. 引っ張り（リピート）要因の検証
    if prev_actual and len(prev_actual) == 2 and prev_actual.isdigit():
        prev_digits = set(prev_actual)
        actual_digits = set(actual)
        pred_digits = set(predicted)

        actual_repeats = actual_digits & prev_digits

        if actual_repeats:
            if not (pred_digits & actual_repeats):
                reasons.append("引っ張り数字の見落とし")
        else:
            if pred_digits & prev_digits:
                reasons.append("不要な引っ張り数字の選定")

    return reasons if reasons else ["要因特定不能（条件外れ）"]


# ---------------------------------------------------------
# 3. UI メイン画面（3タブ構造）
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    ["🎯 数字予測を生成", "🔍 外れ原因の自動検証", "📈 累積データの分析"]
)

# ---------------------------------------------------------
# TAB 1: 予測画面
# ---------------------------------------------------------
with tab1:
    st.header("🎯 次回予想数字の生成")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        prev_input = st.text_input(
            "前回の当選番号（ミニ2桁）",
            value="00",
            max_chars=2,
            key="tab1_prev",
        )
    with col_b:
        parity_opt = st.selectbox(
            "偶奇絞り込み",
            ["指定なし", "偶・偶", "奇・奇", "偶・奇", "奇・偶"],
        )
    with col_c:
        bs_opt = st.selectbox(
            "大小絞り込み (5以上は大)",
            ["指定なし", "大・大", "小・小", "大・小", "小・大"],
        )

    num_count = st.slider("生成する予想数", min_value=1, max_value=10, value=5)

    if st.button("🚀 予測を実行する", type="primary"):
        preds = generate_predictions(
            parity_opt, bs_opt, count=num_count
        )
        st.session_state["last_predictions"] = preds
        st.session_state["last_prev_input"] = prev_input

        if len(preds) < num_count:
            st.warning(
                f"絞り込み条件が厳しいため、{len(preds)}件のみ生成されました。"
            )
        else:
            st.success("予測数字を生成しました！")

    if "last_predictions" in st.session_state:
        st.subheader("💡 最新の予測結果")
        st.write(
            " / ".join(
                [f"**[{p}]**" for p in st.session_state["last_predictions"]]
            )
        )


# ---------------------------------------------------------
# TAB 2: 検証画面
# ---------------------------------------------------------
with tab2:
    st.header("🔍 外れ要因の検証・エラー分析")
    st.caption(
        "抽選結果を入力すると外れ理由を自動判定し、検証結果を累積データベース（CSV）に保存します。"
    )

    default_prev = st.session_state.get("last_prev_input", "")

    v_col1, v_col2 = st.columns(2)
    with v_col1:
        actual_num = st.text_input(
            "今回の当選番号（ミニ2桁）",
            value="",
            max_chars=2,
            placeholder="例: 45",
        )
    with v_col2:
        prev_actual_num = st.text_input(
            "前回の当選番号（引っ張り検証用）",
            value=default_prev,
            max_chars=2,
            placeholder="例: 38",
        )

    default_preds = ""
    if "last_predictions" in st.session_state:
        default_preds = ", ".join(st.session_state["last_predictions"])

    target_preds_input = st.text_area(
        "検証したい予想番号リスト（カンマ区切り）",
        value=default_preds,
        placeholder="例: 35, 42, 89, 15",
    )

    if st.button("📊 外れ要因を検証・保存する"):
        if not actual_num or len(actual_num) != 2 or not actual_num.isdigit():
            st.error("今回の当選番号を2桁の数字（半角）で入力してください。")
        else:
            raw_preds = target_preds_input.replace("\n", ",").split(",")
            preds_list = [p.strip() for p in raw_preds if p.strip()]

            if not preds_list:
                st.warning("検証対象の予想番号が入力されていません。")
            else:
                st.subheader("📋 今回の判定結果")
                results = []
                save_records = []
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                for pred in preds_list:
                    reasons = diagnose_miss_reason(
                        pred, actual_num, prev_actual_num
                    )
                    is_hit = "🎯 的中" in reasons
                    reason_str = " / ".join(reasons)

                    results.append(
                        {
                            "予想番号": pred,
                            "判定": "🎯 的中" if is_hit else "❌ 外れ",
                            "分析・外れ要因": reason_str,
                        }
                    )

                    # 保存用レコード構築
                    save_records.append(
                        {
                            "日時": now_str,
                            "予想番号": pred,
                            "当選番号": actual_num,
                            "判定": "的中" if is_hit else "外れ",
                            "要因リスト": reason_str,
                        }
                    )

                # CSV保存処理
                save_history_record(save_records)
                st.success("検証データを蓄積ログ（CSV）に自動保存しました。")

                df_res = pd.DataFrame(results)
                st.dataframe(df_res, use_container_width=True)

                # 今回の外れ要因の簡易グラフ
                all_fail_reasons = []
                for r in results:
                    if r["判定"] == "❌ 外れ":
                        all_fail_reasons.extend(
                            r["分析・外れ要因"].split(" / ")
                        )

                if all_fail_reasons:
                    st.subheader("📈 今回の傾向グラフ")
                    reason_counts = pd.Series(all_fail_reasons).value_counts()
                    st.bar_chart(reason_counts)


# ---------------------------------------------------------
# TAB 3: 累積データの分析画面（新機能）
# ---------------------------------------------------------
with tab3:
    st.header("📈 蓄積された外れ要因の累積データベース分析")

    df_history = load_history()

    if df_history.empty:
        st.info(
            "まだ蓄積されたデータがありません。TAB2で検証を実行するとデータが溜まっていきます。"
        )
    else:
        st.metric("総検証サンプル数", f"{len(df_history)} 件")

        st.subheader("📜 検証履歴ログ")
        st.dataframe(df_history, use_container_width=True)

        # 蓄積データ全体の集計
        fail_df = df_history[df_history["判定"] == "外れ"]

        if not fail_df.empty:
            st.subheader("📊 累積・最頻外れ要因ランキング")

            all_cumulative_reasons = []
            for item in fail_df["要因リスト"].dropna():
                all_cumulative_reasons.extend(str(item).split(" / "))

            cum_counts = pd.Series(all_cumulative_reasons).value_counts()
            st.bar_chart(cum_counts)

            top_reason = cum_counts.index[0] if len(cum_counts) > 0 else None
            if top_reason:
                st.warning(
                    f"⚠️ **過去の最多外れパターン**: **「{top_reason}」** が最も多く発生しています。"
                )
                st.info(
                    "💡 **改善アクション提案**: TAB1で数字を生成する際、このパターンを回避できるようにフィルター条件（偶奇・大小の設定）を調整してください。"
                )
