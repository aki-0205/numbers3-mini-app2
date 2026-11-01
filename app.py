import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta, timezone, date
from collections import Counter

# ページ設定
st.set_page_config(page_title="ナンバーズ3 ミニ 20口予測・的中率システム", layout="centered")

# 日本標準時（JST = UTC+9）の定義
JST = timezone(timedelta(hours=9))

# 初期データ（日付、当選下2桁）
INITIAL_DATA = [
    {"date": "2026-10-30", "num": "52"},
    {"date": "2026-10-29", "num": "17"},
    {"date": "2026-10-28", "num": "52"},
    {"date": "2026-10-26", "num": "16"},
    {"date": "2026-10-23", "num": "45"},
    {"date": "2026-10-22", "num": "25"},
    {"date": "2026-10-21", "num": "86"},
    {"date": "2026-10-20", "num": "08"},
    {"date": "2026-10-19", "num": "11"},
    {"date": "2026-10-16", "num": "45"},
]

# セッション状態の初期化
if "history" not in st.session_state:
    st.session_state.history = INITIAL_DATA.copy()
    st.session_state.history = sorted(st.session_state.history, key=lambda x: x['date'], reverse=True)

# -------------------------------------------------------------
# 1. 日付・時間判定のエッセンス（参考コードの堅牢なロジックを採用）
# -------------------------------------------------------------
def get_period_key() -> str:
    now_utc = datetime.utcnow()
    now = now_utc + timedelta(hours=9)
    
    current_time = now.time()
    weekday = now.weekday() # 0:月, 1:火, 2:水, 3:木, 4:金, 5:土, 6:日

    # 朝8時を基準とした日付の切り替わり
    if current_time >= time(8, 0):
        base_date = now.date()
        base_weekday = weekday
    else:
        base_date = now.date() - timedelta(days=1)
        base_weekday = (weekday - 1) % 7

    # 土日（5:土, 6:日）の場合は次の月曜日へ正確に日付を進める
    if base_weekday >= 5:
        days_to_monday = (7 - base_weekday) % 7
        if days_to_monday == 0:
            days_to_monday = 7
        target_date = base_date + timedelta(days=days_to_monday)
    else:
        target_date = base_date

    return target_date.strftime("%Y-%m-%d")

# -------------------------------------------------------------
# 2. オリジナルの20口選出ロジック
# -------------------------------------------------------------
def is_zorome(num_str):
    return len(num_str) == 2 and num_str[0] == num_str[1]

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
        seed_key = int(train_data[0]['num']) + (hash(train_data[0]['date']) % 10000)
        pred_20, _ = select_top_20_numbers(train_data, seed_val=seed_key)
        if actual_num in pred_20:
            hits += 1
        evaluated += 1
        
    if evaluated == 0:
        return 0.0
    return (hits / evaluated) * 100.0

def get_history_dataframe(history_data):
    if not history_data:
        return pd.DataFrame(columns=["抽選日", "当選下2桁", "当たり外れ", "累計当選確率"])
    
    sorted_hist = sorted(history_data, key=lambda x: x['date'])
    hits_so_far = 0
    evaluated_so_far = 0
    entry_evals = {}
    
    for i in range(len(sorted_hist)):
        current_entry = sorted_hist[i]
        train_data = sorted_hist[:i]
        
        if not train_data:
            judgement = "-"
            rate_str = "-"
        else:
            seed_key = int(train_data[0]['num']) + (hash(train_data[0]['date']) % 10000)
            pred_20, _ = select_top_20_numbers(train_data, seed_val=seed_key)
            actual_num = current_entry['num']
            
            evaluated_so_far += 1
            if actual_num in pred_20:
                hits_so_far += 1
                judgement = "当たり"
            else:
                judgement = "外れ"
                
            rate = (hits_so_far / evaluated_so_far) * 100.0
            rate_str = f"{rate:.1f}%"
            
        entry_evals[(current_entry['date'], current_entry['num'])] = (judgement, rate_str)
        
    display_data = []
    for item in history_data:
        key = (item['date'], item['num'])
        judgement, rate_str = entry_evals.get(key, ("-", "-"))
        display_data.append({
            "抽選日": item['date'],
            "当選下2桁": item['num'],
            "当たり外れ": judgement,
            "累計当選確率": rate_str
        })
        
    return pd.DataFrame(display_data)

# -------------------------------------------------------------
# 3. Streamlit 画面レイアウト（オリジナルデザイン）
# -------------------------------------------------------------
st.markdown(
    '<div style="background-color: #2b5c8f; padding: 16px; border-radius: 8px; text-align: center; color: white; margin-bottom: 15px;">'
    '<h2 style="margin: 0; font-size: 1.25rem;">🎯 ナンバーズ3 ミニ 20口予測・的中率システム</h2>'
    '</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["📊 20口予測 & 的中率", "📝 当選数字の入力・履歴 (最大50回)", "📈 出現傾向 棒グラフ"])

with tab1:
    period_key = get_period_key()
    target_date = datetime.strptime(period_key, "%Y-%m-%d").date()
    target_str = f"{target_date.month}月{target_date.day}日"
    now_jst = datetime.now(JST)
    
    # 24時間ウィンドウ（period_key）ごとに予測結果をセッションに固定
    if "period_key" not in st.session_state or st.session_state.period_key != period_key:
        st.session_state.period_key = period_key
        latest_entry = st.session_state.history[0] if st.session_state.history else {"num": "00", "date": "2026-01-01"}
        current_seed = int(latest_entry['num']) + (hash(latest_entry['date']) % 10000)
        selected_20, latest_used = select_top_20_numbers(st.session_state.history, seed_val=current_seed)
        st.session_state.selected_20 = selected_20
        st.session_state.latest_used = latest_used
    
    selected_20 = st.session_state.selected_20
    latest_used = st.session_state.latest_used
    accuracy_rate = calculate_backtest_accuracy(st.session_state.history, 50)
    
    st.info(f"🕒 時刻 (JST): {now_jst.strftime('%H:%M')} (朝8時境界24時間固定) | 🎯 予測対象: **{target_str}** | 📊 固定キー: `{period_key}`")
    
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
    st.subheader("当選数字の登録（日付自動連動） & 履歴管理")
    st.write("抽選日と当選下2桁を入力してください。追加すると自動的に日付の新しい順に並び替えられ、最大50回分まで保存されます。")
    
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            input_date = st.date_input("抽選日", value=date.today())
        with col2:
            input_num = st.text_input("当選下2桁 (00〜99)", max_chars=2, placeholder="例: 52")
            
        submitted = st.form_submit_button("データを追加する")
        
        if submitted:
            if len(input_num) == 2 and input_num.isdigit():
                new_entry = {
                    "date": input_date.strftime("%Y-%m-%d"),
                    "num": input_num
                }
                st.session_state.history.insert(0, new_entry)
                st.session_state.history = sorted(st.session_state.history, key=lambda x: x['date'], reverse=True)
                
                if len(st.session_state.history) > 50:
                    st.session_state.history = st.session_state.history[:50]
                
                if "period_key" in st.session_state:
                    del st.session_state.period_key
                    
                st.success(f"{input_date.strftime('%m月%d日')}（{input_num}）を保存しました！")
                st.rerun()
            else:
                st.error("下2桁の数字（00〜99）を正確に2桁で入力してください。")

    st.markdown("---")
    st.subheader("📋 保持している履歴一覧（直近50回・日付順）")
    
    df_display = get_history_dataframe(st.session_state.history)
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
