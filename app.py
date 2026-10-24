import streamlit as st
import pandas as pd
import random
import datetime
import requests
import json
import base64

# --- ページ設定 ---
st.set_page_config(page_title="ナンバーズミニ 20口予測アプリ", page_icon="🎯", layout="centered")

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

# --- 20時境界による対象日決定 ---
now_jst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
target_date = now_jst.date()
if now_jst.hour >= 20:
    target_date += datetime.timedelta(days=1)

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

# --- スタイリング (コンパクトなタイル表示) ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    h1 { font-size: 1.3rem !important; margin-bottom: 0px !important; }
    h3 { font-size: 0.9rem !important; margin-top: 4px !important; margin-bottom: 2px !important; }
    p, .stMarkdown { font-size: 0.8rem !important; margin-bottom: 2px !important; }

    .pred-box-base {
        background-color: #e8f4fd;
        border: 1.5px solid #2b7de9;
        border-radius: 4px;
        padding: 4px 0px;
        text-align: center;
        font-size: 16px;
        font-weight: bold;
        color: #1a5276;
        margin: 2px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 32px;
        font-size: 0.8rem;
        padding-left: 8px;
        padding-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 ナンバーズミニ 20口予測")

tab1, tab2, tab3 = st.tabs(["🔮 予測 (20個)", "📈 履歴", "⚙️ 検証"])

with tab1:
    st.markdown(f"**対象:** {target_date.strftime('%m月%d日')} （20時切替）")
    st.markdown("### 🏆 上位20口一覧")
    
    for r in range(4):
        cols = st.columns(5)
        for c in range(5):
            idx = r * 5 + c
            if idx < len(top_20):
                with cols[c]:
                    st.markdown(f"<div class='pred-box-base'>{top_20[idx]}</div>", unsafe_allow_html=True)
            
    st.markdown(f"<p style='text-align:right; color:gray; font-size:0.75rem;'>総口数: 20口 (4,000円)</p>", unsafe_allow_html=True)
    st.write("▼ 全20口カンマ区切り一覧")
    st.code(", ".join(top_20), language="text")

with tab2:
    st.subheader("📈 的中率・履歴")
    history = load_history_from_github()
    if history:
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True, height=150)
        hits = sum(1 for h in history if h.get("is_hit"))
        st.metric(label="累計的中率", value=f"{hits}/{len(history)} 回 ({hits/len(history)*100:.1f}%)" if history else "0%")
    else:
        st.info("履歴なし")

with tab3:
    st.subheader("🎯 当選番号の検証・記録")
    winning_num = st.text_input("当選番号（下2桁）", max_chars=2)
    if st.button("照合して保存"):
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
                st.success("保存完了")
            else:
                st.warning("保存失敗")
        else:
            st.warning("2桁で入力")
