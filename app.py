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
# 2. 次回抽せん日時（毎日19:00切り替え・土日考慮）の算出
# ---------------------------------------------------------
def get_target_draw_info():
    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(tz_jst)
    
    today_19 = now.replace(hour=19, minute=0, second=0, microsecond=0)
    
    if now < today_19:
        target_date = now.date()
    else:
        target_date = now.date() + datetime.timedelta(days=1)
        
    if target_date.weekday() == 5:
        target_date += datetime.timedelta(days=2)
    elif target_date.weekday() == 6:
        target_date += datetime.timedelta(days=1)

    seed_string = target_date.strftime("%Y%m%d")
    seed_value = int(hashlib.sha256(seed_string.encode('utf-8')).hexdigest(), 16) % (2**32)
    
    return target_date, seed_value

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
# 4. アプリUI描画
# ---------------------------------------------------------
draw_date, seed = get_target_draw_info()
predictions = generate_numbers3_mini_20(seed)

st.title("🎲 N3ミニ 厳選20選")

weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
date_display = f"{draw_date.strftime('%Y年%m月%d日')}（{weekdays_jp[draw_date.weekday()]}）"

st.subheader(f"📅 次回抽せん日：{date_display}")
st.caption("※ 毎日 19:00 に次回抽せん分へ自動更新されます。")

st.markdown("---")

st.subheader("🎯 厳選20選")

# テーブルヘッダー
table_md = """
| 番号 | 予測 | 番号 | 予測 | 番号 | 予測 | 番号 | 予測 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

# 予測数字のみ赤字の太字（:red[**数字**]）で装飾
for row in range(5):
    p1 = f":red[**{predictions[row]}**]"
    p2 = f":red[**{predictions[row + 5]}**]"
    p3 = f":red[**{predictions[row + 10]}**]"
    p4 = f":red[**{predictions[row + 15]}**]"
    table_md += f"| #{row+1:02d} | {p1} | #{row+6:02d} | {p2} | #{row+11:02d} | {p3} | #{row+16:02d} | {p4} |\n"

st.markdown(table_md)

st.markdown("---")
st.write("▼ 一括コピー用")
st.code(" , ".join(predictions))
