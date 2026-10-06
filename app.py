import datetime
import hashlib
import random
import streamlit as st

# ---------------------------------------------------------
# 1. ページ基本設定
# ---------------------------------------------------------
st.set_page_config(
    page_title="N3ミニ 厳選20選",
    page_icon="🎲",
    layout="centered"
)

# ---------------------------------------------------------
# 2. 日替わりシード値算出（毎日00:00更新）
# ---------------------------------------------------------
def get_daily_seed():
    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    now_jst = datetime.datetime.now(tz_jst)
    today_str = now_jst.strftime("%Y%m%d")
    
    seed_val = int(hashlib.sha256(today_str.encode('utf-8')).hexdigest(), 16) % (2**32)
    return now_jst, seed_val

# ---------------------------------------------------------
# 3. ナンバーズ3 ミニ 厳選20選抽出エンジン
# ---------------------------------------------------------
def generate_numbers3_mini_20(seed):
    random.seed(seed)
    
    hot_pairs = ["12", "35", "58", "79", "04", "26", "48", "60", "81", "93"]
    cold_pairs = ["07", "19", "31", "52", "84"]
    last_pair = "58"
    
    all_pairs = [f"{i:02d}" for i in range(100)]
    weights = []
    
    for p in all_pairs:
        w = 10
        if p in hot_pairs: w += 8
        if p in cold_pairs: w += 4
        if p == last_pair: w += 3
        
        d1, d2 = int(p[0]), int(p[1])
        if d1 == d2: w += 2
        
        weights.append(w)
    
    selected = []
    while len(selected) < 20:
        choice = random.choices(all_pairs, weights=weights, k=1)[0]
        if choice not in selected:
            selected.append(choice)
            
    return sorted(selected)

# ---------------------------------------------------------
# 4. アプリUI描画（スマホ最適化テーブル一覧表示）
# ---------------------------------------------------------
now_jst, seed = get_daily_seed()
predictions = generate_numbers3_mini_20(seed)

st.title("🎲 N3ミニ 厳選20選")

weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
date_display = f"{now_jst.strftime('%Y年%m月%d日')}（{weekdays_jp[now_jst.weekday()]}）"
st.caption(f"📅 予測対象日：{date_display}")

st.markdown("---")

st.subheader("🎯 本日の厳選20選")

# 横4列×縦5行のMarkdownテーブルを作成（スマホでも折り返されない）
table_md = """
| 番号 | 予測 | 番号 | 予測 | 番号 | 予測 | 番号 | 予測 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

for row in range(5):
    p1 = predictions[row]
    p2 = predictions[row + 5]
    p3 = predictions[row + 10]
    p4 = predictions[row + 15]
    table_md += f"| #{row+1:02d} | **{p1}** | #{row+6:02d} | **{p2}** | #{row+11:02d} | **{p3}** | #{row+16:02d} | **{p4}** |\n"

st.markdown(table_md)

st.markdown("---")
st.write("▼ 一括コピー用・テキスト表示")
# 1行で全20個を表示（タップで全選択コピーしやすい形）
st.code(" , ".join(predictions))

st.caption("※ 毎日 午前0:00 に自動更新されます。")
