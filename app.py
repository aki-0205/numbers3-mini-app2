import streamlit as st
import pandas as pd
import random
import datetime
import requests
import json
import base64

# --- ページ設定 ---
st.set_page_config(page_title="ナンバーズミニ 33口予測アプリ", page_icon="🎯", layout="centered")

st.title("🎯 ナンバーズミニ 33口予測アプリ")
st.markdown("20口予測アプリの数字を完全網羅し、見やすくタイル状に整理した合計33口の予測アプリです。")

# --- GitHub連携設定（Secretsから取得） ---
def get_github_config():
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        file_path = st.secrets.get("FILE_PATH", "history_33.json")
        return token, repo, file_path
    except Exception:
        return None, None, None

GITHUB_TOKEN, GITHUB_REPO, FILE_PATH = get_github_config()

# --- 履歴データの読み込み（GitHub経由） ---
def load_history_from_github():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return []
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            file_content = response.json()
            decoded_bytes = base64.b64decode(file_content["content"])
            return json.loads(decoded_bytes.decode("utf-8"))
    except Exception as e:
        st.warning(f"履歴の読み込みに失敗しました: {e}")
    return []

# --- 履歴データの保存（GitHub経由） ---
def save_history_to_github(history_data):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    
    sha = None
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")
        
    json_str = json.dumps(history_data, ensure_ascii=False, indent=2)
    content_encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    
    data = {
        "message": "Update lottery 33-pick prediction history",
        "content": content_encoded,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha
        
    put_resp = requests.put(url, headers=headers, data=json.dumps(data))
    return put_resp.status_code in [200, 201]

# --- 20口予測アプリと完全に同期するロジック ---
def generate_33_predictions(seed_date_str):
    seed_val = int(seed_date_str.replace("-", ""))
    rng = random.Random(seed_val)
    
    # 00〜99の全100数字を同じ手順でシャッフル（これが20口アプリの心臓部と完全に一致させます）
    all_numbers = [f"{i:02d}" for i in range(100)]
    ranked_numbers = all_numbers.copy()
    rng.shuffle(ranked_numbers)
    
    # 上位20個（＝20口予測アプリの20個と100%一致）
    top_20 = ranked_numbers[:20]
    top_20.sort()  # 見やすく昇順ソート（あるいは元の順序）
    
    # 続く21位〜33位の13個（プラス13口）
    next_13 = ranked_numbers[20:33]
    next_13.sort()
    
    return top_20, next_13

# --- メイン画面 ---
target_date = st.date_input("予測対象日", value=datetime.date(2026, 10, 26))
target_date_str = target_date.strftime("%Y-%m-%d")

top_20, next_13 = generate_33_predictions(target_date_str)
combined_33 = top_20 + next_13

st.subheader(f"📅 {target_date_str} 抽選向け予測数字（合計 33口）")

# --- 見やすいタイル状（グリッド）のデザイン ---
st.markdown("### 🏆 上位20口（20口アプリと完全一致）")
cols = st.columns(5)
for idx, num in enumerate(top_20):
    with cols[idx % 5]:
        st.metric(label=f"No.{idx+1}", value=num)

st.markdown("### ➕ 追加13口（21位〜33位）")
cols2 = st.columns(5)
for idx, num in enumerate(next_13):
    with cols2[idx % 5]:
        st.metric(label=f"No.{idx+21}", value=num)

st.info(f"総口数: **33口**（購入金額目安: 6,600円）")

st.markdown("---")

# コピー用
st.write("▼ 全33口カンマ区切り一覧")
st.code(", ".join(combined_33), language="text")

st.markdown("---")

# --- 当選番号入力＆結果検証 ---
st.subheader("🎯 当選番号の検証・記録")
winning_num = st.text_input("当選番号（下2桁）を入力（例: 05, 42）", max_chars=2)

if st.button("結果を照合して保存"):
    if len(winning_num) == 2 and winning_num.isdigit():
        is_hit = winning_num in combined_33
        is_top20_hit = winning_num in top_20
        
        if is_hit:
            st.balloons()
            if is_top20_hit:
                st.success(f"🎉 **的中！** 当選番号 `{winning_num}` は **上位20口（20口予測アプリ範囲）** に含まれていました！")
            else:
                st.success(f"🎉 **的中！** 当選番号 `{winning_num}` は **追加13口範囲** に含まれていました！")
        else:
            st.error(f"❌ 残念... 当選番号 `{winning_num}` は不的中でした。")
            
        if GITHUB_TOKEN and GITHUB_REPO:
            history = load_history_from_github()
            history = [h for h in history if h.get("date"] != target_date_str]
            history.append({
                "date": target_date_str,
                "winning_num": winning_num,
                "is_hit": is_hit,
                "is_top20_hit": is_top20_hit,
                "predictions_count": len(combined_33)
            })
            if save_history_to_github(history):
                st.success("結果をGitHubへ保存しました。")
            else:
                st.warning("GitHubへのデータ保存に失敗しました。")
    else:
        st.warning("2桁の数字を入力してください。")
