import streamlit as st
import pandas as pd
import random
import datetime
import requests
import json
import base64

# --- ページ設定 ---
st.set_page_config(page_title="ナンバーズミニ 予測 ＆ 的中率管理", page_icon="🎯", layout="centered")

# --- GitHub連携設定 ---
def get_github_config():
    try:
        return st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"], st.secrets.get("FILE_PATH", "history_20.json")
    except Exception:
        return None, None, None

GITHUB_TOKEN, GITHUB_REPO, FILE_PATH = get_github_config()

def load_history_from_github():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return []
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return json.loads(base64.b64decode(response.json()["content"]).decode("utf-8"))
    except Exception:
        pass
    return []

def save_history_to_github(history_data):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    sha = None
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
    content_encoded = base64.b64encode(json.dumps(history_data, ensure_ascii=False, indent=2).encode("utf-8")).decode("utf-8")
    data = {"message": "Update history 20", "content": content_encoded, "branch": "main"}
    if sha:
        data["sha"] = sha
    return requests.put(url, headers=headers, data=json.dumps(data)).status_code in [200, 201]

# --- 20時境界による対象日・参照日決定 ---
now_jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
current_time_str = now_jst.strftime("%H:%M")

if now_jst.hour >= 20:
    target_date = now_jst.date() + datetime.timedelta(days=1)
    boundary_text = "20時以降"
else:
    target_date = now_jst.date()
    boundary_text = "20時前"

ref_date = target_date - datetime.timedelta(days=1)

target_date_str = target_date.strftime("%Y-%m-%d")

# --- 20口予測ロジック ---
def generate_20_predictions(seed_date_str):
    seed_val = int(seed_date_str.replace("-", ""))
    rng = random.Random(seed_val)
    all_numbers = [f"{i:02d}" for i in range(100)]
    ranked = all_numbers.copy()
    rng.shuffle(ranked)
    
    top_20 = ranked[:20]
    top_20.sort()
    return top_20

top_20 = generate_20_predictions(target_date_str)

# --- スタイリング（スクショの見た目を完全に再現） ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    /* 青いメインバナー */
    .main-banner {
        background-color: #1f618d;
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 8px;
    }
    /* 情報バー */
    .info-bar {
        background-color: #ebf5fb;
        border: 1px solid #aed6f1;
        border-radius: 6px;
        padding: 8px;
        font-size: 0.8rem;
        color: #2c3e50;
        margin-bottom: 12px;
        text-align: center;
    }
    /* タイル（青枠・白背景） */
    .pred-box {
        background-color: #ffffff;
        border: 2px solid #2980b9;
        border-radius: 6px;
        padding: 6px 0px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
        margin: 2px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        height: 34px;
        font-size: 0.8rem;
        padding-left: 10px;
        padding-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- ヘルパー表示 ---
st.markdown("<div class='main-banner'>🎯 ナンバーズミニ 予測 ＆ 的中率管理</div>", unsafe_allow_html=True)
st.markdown(f"<div class='info-bar'>🕒 時刻(JST): {current_time_str}（20時境界: {boundary_text}） | 🎯 予測対象: {target_date.strftime('%m月%d日')} | 📊 参照: {ref_date.strftime('%m月%d日')} 結果</div>", unsafe_allow_html=True)

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(["🔮 本日の予測 (20個)", "📈 的中率・履歴", "⚙️ 当選数"])

with tab1:
    st.markdown(f"### 🟣 {target_date.strftime('%m月%d日')} 抽選向け予測数字（全20個）")
    
    # 5列×4行＝20個のタイル表示
    for r in range(4):
        cols = st.columns(5)
        for c in range(5):
            idx = r * 5 + c
            if idx < len(top_20):
                with cols[c]:
                    st.markdown(f"<div class='pred-box'>{top_20[idx]}</div>", unsafe_allow_html=True)

with tab2:
    st.subheader("📈 的中率・履歴")
    history = load_history_from_github()
    if history:
        df = pd.DataFrame(history)
        hits = sum(1 for h in history if h.get("is_hit"))
        total = len(history)
        hit_rate = (hits / total) * 100 if total > 0 else 0.0
        
        st.metric(label="累計的中率", value=f"{hits}/{total} 回 ({hit_rate:.1f}%)")
        st.dataframe(df, use_container_width=True, height=150)
    else:
        st.info("保存された履歴データはありません。")

with tab3:
    st.subheader("🎯 当選番号の検証・記録")
    winning_num = st.text_input("当選番号（下2桁）を入力", max_chars=2)
    if st.button("結果を照合して保存"):
        if len(winning_num) == 2 and winning_num.isdigit():
            is_hit = winning_num in top_20
            if is_hit:
                st.balloons()
                st.success(f"🎉 的中！ (`{winning_num}`)")
            else:
                st.error(f"❌ 不的中 (`{winning_num}`)")
            
            history = load_history_from_github()
            history = [h for h in history if h.get("date") != target_date_str]
            history.append({
                "date": target_date_str,
                "winning_num": winning_num,
                "is_hit": is_hit,
                "predictions_count": len(top_20)
            })
            if save_history_to_github(history):
                st.success("GitHubへ保存完了")
            else:
                st.warning("GitHubへの保存に失敗しました")
        else:
            st.warning("2桁の数字を入力してください")
