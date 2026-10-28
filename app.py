import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta, timezone, date

# ページ設定
st.set_page_config(page_title="ナンバーズ3 ミニ 20口予測・的中率システム", layout="centered")

# 日本標準時（JST = UTC+9）の定義
JST = timezone(timedelta(hours=9))

# 初期データ（日付、抽選回号、当選下2桁）
INITIAL_DATA = [
    {"date": "2026-10-26", "draw": 7099, "num": "16"},
    {"date": "2026-10-23", "draw": 7098, "num": "45"},
    {"date": "2026-10-22", "draw": 7097, "num": "25"},
    {"date": "2026-10-21", "draw": 7096, "num": "86"},
    {"date": "2026-10-20", "draw": 7095, "num": "08"},
    {"date": "2026-10-19", "draw": 7094, "num": "11"},
    {"date": "2026-10-16", "draw": 7093, "num": "45"},
    {"date": "2026-10-15", "draw": 7092, "num": "15"},
    {"date": "2026-10-14", "draw": 7091, "num": "52"},
    {"date": "2026-10-13", "draw": 7090, "num": "10"},
]

# セッション状態の初期化
if "history" not in st.session_state:
    st.session_state.history = INITIAL_DATA.copy()

# -------------------------------------------------------------
# 1. 時間固定ロジック（抽選日当日の朝8時切替、土日は月曜朝8時まで固定）
# -------------------------------------------------------------
def get_current_window_info():
    now = datetime.now(JST)
    weekday = now.weekday() # 0:月, 1:火, 2:水, 3:木, 4:金, 5:土, 6:日
    
    target_date = now.date()
    if now.time() < time(8, 0):
        target_date -= timedelta(days=1)
        weekday = target_date.weekday()
    
    # 土日の場合の処理（月曜朝8時までは金曜ウィンドウ）
    if weekday == 5: # 土
        target_date -= timedelta(days=1)
    elif weekday == 6: # 日
        target_date -= timedelta(days=2)
        
    # 次の抽選日（予測対象日）の算出
    next_date = target_date + timedelta(days=1)
    if next_date.weekday() == 5: # 土曜なら月曜にする
        next_date += timedelta(days=2)
    elif next_date.weekday() == 6: # 日曜なら月曜にする
        next_date += timedelta(days=1)
        
    prediction_target_str = f"{next_date.month}月{next_date.day}日"
    ref_date_str = f"{target_date.month}月{target_date.day}日"
    
    return prediction_target_str, ref_date_str

# -------------------------------------------------------------
# 2. 20口選出ロジック
# -------------------------------------------------------------
def is_zorome(num_str):
    return num_str[0] == num_str[1]

def is_renban(num_str):
    d1 = int(num_str[0])
    d2 = int(num_str[1])
    if abs(d1 - d2) == 1:
        if {d1, d2} == {0, 9}:
            return False
        return True
    return False

def select_top_20_numbers(history_data, seed_val=None):
    if seed_val is not None:
        np.random.seed(seed_val)
        
    all_candidates = [f"{i:02d}" for i in range(100)]
    df_hist = pd.DataFrame(history_data)
    freq_map = df_hist['num'].value_counts().to_dict()
    latest_num = history_data[0]['num'] if history_data else "00"
    
    scores = {}
    for num in all_candidates:
        freq = freq_map.get(num, 0)
        base_score = 10.0 - (freq * 1.5) + np.random.uniform(0, 2.0)
        if int(num) % 2 != 0:
            base_score += 0.2
        scores[num] = base_score

    excluded = {latest_num}
    if is_zorome(latest_num):
        for num in all_candidates:
            if is_zorome(num):
                excluded.add(num)
    if is_renban(latest_num):
        for num in all_candidates:
            if is_renban(num):
                excluded.add(num)

    valid_candidates = [num for num in all_candidates if num not in excluded]
    valid_candidates.sort(key=lambda x: scores[x], reverse=True)
    selected = valid_candidates[:20]
    selected.sort()
    return selected, latest_num

def calculate_backtest_accuracy(history_data, max_eval=50):
    """過去の履歴を順に検証し、直近50回分の的中率（当選確率）を算出する"""
    n = len(history_data)
    if n <= 1:
        return 0.0
    
    limit = min(n - 1, max_eval)
    hits = 0
    evaluated = 0
    
    for i in range(limit):
        actual_num = history_data[i]['num']
        train_data = history_data[i+1:]
        if not train_data:
            continue
        seed_key = int(train_data[0]['num']) + train_data[0]['draw']
        pred_20, _ = select_top_20_numbers(train_data, seed_val=seed_key)
        if actual_num in pred_20:
            hits += 1
        evaluated += 1
        
    if evaluated == 0:
        return 0.0
    return (hits / evaluated) * 100.0

# -------------------------------------------------------------
# 3. Streamlit 画面レイアウト
# -------------------------------------------------------------
st.markdown(
    '<div style="background-color: #2b5c8f; padding: 16px; border-radius: 8px; text-align: center; color: white; margin-bottom: 15px;">'
    '<h2 style="margin: 0; font-size: 1.25rem;">🎯 ナンバーズ3 ミニ 20口予測・的中率管理システム</h2>'
    '</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["📊 20口予測 & 的中率", "📝 当選数字の入力・履歴 (最大50回)", "📈 出現傾向 棒グラフ"])

with tab1:
    target_str, ref_str = get_current_window_info()
    now_jst = datetime.now(JST)
    
    latest_entry = st.session_state.history[0] if st.session_state.history else {"num": "00", "draw": 0}
    current_seed = int(latest_entry['num']) + latest_entry['draw']
    
    selected_20, latest_used = select_top_20_numbers(st.session_state.history, seed_val=current_seed)
    accuracy_rate = calculate_backtest_accuracy(st.session_state.history, 50)
    
    st.info(f"🕒 時刻 (JST): {now_jst.strftime('%H:%M')} (朝8時境界固定) | 🎯 予測対象: **{target_str}** | 📊 参照: **{ref_str}** 結果 (`{latest_used}`)")
    
    # 的中率のみのシンプル表示
    st.metric("直近的中率（当選確率）", f"{accuracy_rate:.1f} %")
    
    st.markdown("---")
    st.markdown(f"#### 📌 {target_str} 抽選向け予測数字（全20個）")
    
    grid_html = '<div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 20px;">'
    for idx, num in enumerate(selected_20):
        grid_html += (
            '<div style="background-color: #ffffff; border: 2px solid #2b5c8f; border-radius: 8px; padding: 10px 4px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">'
            f'<div style="font-size: 0.7em; color: #555; margin-bottom: 3px; font-weight: bold;">口 {idx+1}</div>'
            f'<div style="font-size: 1.4em; font-weight: bold; color: #111; letter-spacing: 1px;">{num}</div>'
            '</div>'
        )
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

with tab2:
    st.subheader("当選数字の登録（日付選択対応） & 履歴管理")
    st.write("抽選日、回号、当選下2桁を入力してください。最大50回分まで保持され、51回目からは古いデータが自動削除されます。")
    
    with st.form("input_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            input_date = st.date_input("抽選日", value=date.today())
        with col2:
            next_draw = (st.session_state.history[0]['draw'] + 1) if st.session_state.history else 7100
            input_draw = st.number_input("抽選回号", min_value=1, value=next_draw, step=1)
        with col3:
            input_num = st.text_input("当選下2桁 (00〜99)", max_chars=2, placeholder="例: 16")
            
        submitted = st.form_submit_button("データを追加する")
        
        if submitted:
            if len(input_num) == 2 and input_num.isdigit():
                new_entry = {
                    "date": input_date.strftime("%Y-%m-%d"),
                    "draw": int(input_draw),
                    "num": input_num
                }
                st.session_state.history.insert(0, new_entry)
                
                if len(st.session_state.history) > 50:
                    st.session_state.history = st.session_state.history[:50]
                    
                st.success(f"{input_date.strftime('%m月%d日')} 第{input_draw}回（{input_num}）を追加しました！")
                st.rerun()
            else:
                st.error("下2桁の数字（00〜99）を正確に2桁で入力してください。")

    st.markdown("---")
    st.subheader("📋 保持している履歴一覧（直近50回）")
    
    df_display = pd.DataFrame(st.session_state.history)
    df_display.columns = ["抽選日", "抽選回号", "当選下2桁"]
    st.dataframe(df_display, use_container_width=True, height=300)

with tab3:
    st.subheader("10個単位グループ別 出現回数グラフ")
    st.write("直近50回分のデータに基づく、00〜99の10区分ごとの出現頻度です。")
    
    bins = [
        ("00-09", range(0, 10)), ("10-19", range(10, 20)), ("20-29", range(20, 30)),
        ("30-39", range(30, 40)), ("40-49", range(40, 50)), ("50-59", range(50, 60)),
        ("60-69", range(60, 70)), ("70-79", range(70, 80)), ("80-89", range(80, 90)),
        ("90-99", range(90, 100)),
    ]
    counts = {label: 0 for label, _ in bins}
    for item in st.session_state.history:
        val = int(item['num'])
        for label, r in bins:
            if val in r:
                counts[label] += 1
    st.bar_chart(pd.DataFrame(list(counts.items()), columns=["グループ", "出現回数"]).set_index("グループ"))
