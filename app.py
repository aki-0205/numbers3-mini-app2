import streamlit as st
import pandas as pd
import altair as alt
from collections import Counter, deque
from datetime import datetime, time, timedelta, date
import json
import os

st.set_page_config(page_title="ナンバーズミニ20口予測", page_icon="🎯", layout="centered")

INITIAL_50 = [
    "16", "45", "25", "86", "08", "11", "45", "15", "52", "10",
    "31", "75", "45", "05", "69", "69", "06", "18", "20", "02",
    "26", "39", "87", "56", "82", "66", "88", "29", "53", "88",
    "08", "60", "50", "94", "82", "51", "66", "12", "82", "77",
    "91", "60", "08", "86", "37", "86", "19", "72", "09", "78"
]

DATA_FILE = "mini_history.json"
CACHE_FILE = "prediction_cache.json"
HIT_LOG_FILE = "hit_log.json"

def is_zorome(num: str) -> bool:
    return len(num) == 2 and num[0] == num[1]

def get_period_key() -> str:
    now_utc = datetime.utcnow()
    now = now_utc + timedelta(hours=9)
    
    current_time = now.time()
    weekday = now.weekday()

    if current_time >= time(8, 0):
        base_date = now.date()
        base_weekday = weekday
    else:
        base_date = now.date() - timedelta(days=1)
        base_weekday = (weekday - 1) % 7

    if base_weekday >= 5:
        days_to_monday = (7 - base_weekday) % 7
        if days_to_monday == 0:
            days_to_monday = 7
        target_date = base_date + timedelta(days=days_to_monday)
    else:
        target_date = base_date

    return target_date.strftime("%Y-%m-%d")

def load_history() -> deque:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return deque(json.load(f), maxlen=50)
        except:
            pass
    return deque(INITIAL_50, maxlen=50)

def save_history(history: deque):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(list(history), f, ensure_ascii=False)
    except:
        pass

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache: dict):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except:
        pass

def load_hit_log() -> list:
    if os.path.exists(HIT_LOG_FILE):
        try:
            with open(HIT_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data[-50:] if isinstance(data, list) else []
        except:
            pass
    return []

def save_hit_log(log: list):
    try:
        with open(HIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log[-50:], f, ensure_ascii=False)
    except:
        pass

def calculate_scores(history: list) -> dict:
    counter = Counter(history)
    total = len(history)
    scores = {}
    for i in range(100):
        num = f"{i:02d}"
        count = counter.get(num, 0)
        score = count * 10.0
        if num in history[-10:]:
            score += 3.0
        if num in history[-5:]:
            score += 2.0
        odd_count = sum(1 for h in history if int(h) % 2 == 1)
        even_count = total - odd_count
        if odd_count > even_count + 5 and int(num) % 2 == 0:
            score += 1.5
        elif even_count > odd_count + 5 and int(num) % 2 == 1:
            score += 1.5
        scores[num] = score
    return scores

def generate_prediction(history: list) -> list:
    scores = calculate_scores(history)
    latest = history[-1] if history else None
    excluded = set()
    if latest and is_zorome(latest):
        for i in range(10):
            excluded.add(f"{i}{i}")
    ranked = sorted(scores.keys(), key=lambda x: (-scores[x], x))
    return [num for num in ranked if num not in excluded][:20]

# ==================== メイン ====================
st.markdown("""
<div style="background:linear-gradient(135deg,#1a365d,#2b6cb0);padding:14px;border-radius:10px;text-align:center;color:white;margin-bottom:12px;">
    <h2 style="margin:0;font-size:1.25rem;">🎯 ナンバーズ3 ミニ 20口予測</h2>
    <p style="margin:4px 0 0;font-size:0.8rem;opacity:0.9;">直近50回分析（初回7050〜7099）</p>
</div>
""", unsafe_allow_html=True)

history = load_history()
period_key = get_period_key()
cache = load_cache()
hit_log = load_hit_log()

if period_key in cache and len(cache[period_key]) == 20:
    selected_20 = cache[period_key]
else:
    selected_20 = generate_prediction(list(history))
    cache[period_key] = selected_20
    save_cache(cache)

target_date = datetime.strptime(period_key, "%Y-%m-%d").date()
st.subheader(f"抽選日：{target_date.strftime('%Y年%m月%d日')} の20口")
st.caption(f"固定期間キー: **{period_key}** ／ 使用データ: 直近{len(history)}回")

# 予測数字一覧
st.markdown("### 予測数字一覧")
lines = []
for i in range(0, 20, 5):
    group = selected_20[i:i+5]
    line = "　".join([f"**{num}**" for num in group])
    lines.append(f"口{i+1:2d}〜{i+5:2d}： {line}")
st.markdown("\n\n".join(lines))

st.markdown("---")
compact = "  ".join(selected_20)
st.markdown(
    f"<div style='font-size:1.3rem;font-weight:700;letter-spacing:1px;text-align:center;padding:10px;background:#f0f4f8;border-radius:8px;'>{compact}</div>",
    unsafe_allow_html=True
)

# ========== 当選登録 ==========
st.markdown("---")
st.subheader("当選数字の登録")

draw_date = st.date_input("抽選日", value=date.today(), max_value=date.today(), format="YYYY/MM/DD")

col1, col2 = st.columns([3, 1])
with col1:
    win_input = st.text_input("当選ミニ数字（2桁）", max_chars=2, label_visibility="collapsed", placeholder="例: 16")
with col2:
    register_btn = st.button("登録", use_container_width=True)

if register_btn:
    if win_input and win_input.isdigit() and len(win_input) == 2:
        win_num = win_input.zfill(2)
        
        history.append(win_num)
        save_history(history)

        is_hit = win_num in selected_20

        hit_log.append({
            "date": draw_date.strftime("%Y年%m月%d日"),
            "number": win_num,
            "hit": is_hit
        })
        if len(hit_log) > 50:
            hit_log = hit_log[-50:]
        save_hit_log(hit_log)

        if is_hit:
            st.success(f"✅ {draw_date.strftime('%Y年%m月%d日')} の当選数字【{win_num}】を登録しました（的中）")
        else:
            st.success(f"✅ {draw_date.strftime('%Y年%m月%d日')} の当選数字【{win_num}】を登録しました（外れ）")
        
        st.balloons()
        st.rerun()
    else:
        st.error("2桁の数字を入力してください")

# ========== 直近50回の当選状況（一覧表示） ==========
st.markdown("---")
st.subheader("直近50回の当選状況")

if hit_log:
    total_hits = sum(1 for x in hit_log if x.get("hit"))
    total_count = len(hit_log)
    rate = (total_hits / total_count * 100) if total_count > 0 else 0

    st.markdown(f"**累計当選確率：{rate:.1f}%（{total_hits}/{total_count}）**")
    st.markdown("---")

    # 新しいものから一覧表示
    for item in reversed(hit_log):
        result = "的中 ✅" if item.get("hit") else "外れ ❌"
        st.markdown(f"**{item['date']}**　当選数字 **{item['number']}**　→　{result}")
else:
    st.info("まだ当選数字が登録されています。登録するとここに一覧表示されます。")

# 出現分布
st.markdown("---")
st.subheader("出現分布（10単位・直近50回）")

if history:
    counter = Counter(history)
    bins = [f"{i:02d}-{i+9:02d}" for i in range(0, 100, 10)]
    values = [sum(counter.get(f"{j:02d}", 0) for j in range(i, i+10)) for i in range(0, 100, 10)]
    chart_df = pd.DataFrame({"レンジ": bins, "回数": values})

    chart = alt.Chart(chart_df).mark_bar(color="#2b6cb0").encode(
        x=alt.X("レンジ:N", title="レンジ", sort=None),
        y=alt.Y("回数:Q", title="出現回数", scale=alt.Scale(domain=[0, 15])),
        tooltip=["レンジ", "回数"]
    ).properties(height=280).configure_axis(grid=True)

    st.altair_chart(chart, use_container_width=True)
    st.caption("Y軸：0 / 5 / 10 / 15 で固定")

st.caption("※この予測は参考情報です。当選を保証するものではありません。")
