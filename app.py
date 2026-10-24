import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import pytz

# ページ設定
st.set_page_config(page_title="ナンバーズ3 ミニ 20口予測システム", layout="centered")

# JSTタイムゾーン
JST = pytz.timezone("Asia/Tokyo")

# 初期データ（第7050回〜第7099回の直近50回分の下2桁データ）
INITIAL_DATA = [
    {"draw": 7099, "num": "16"}, {"draw": 7098, "num": "45"}, {"draw": 7097, "num": "25"},
    {"draw": 7096, "num": "86"}, {"draw": 7095, "num": "08"}, {"draw": 7094, "num": "11"},
    {"draw": 7093, "num": "45"}, {"draw": 7092, "num": "15"}, {"draw": 7091, "num": "52"},
    {"draw": 7090, "num": "10"}, {"draw": 7089, "num": "31"}, {"draw": 7088, "num": "75"},
    {"draw": 7087, "num": "45"}, {"draw": 7086, "num": "05"}, {"draw": 7085, "num": "69"},
    {"draw": 7084, "num": "69"}, {"draw": 7083, "num": "06"}, {"draw": 7082, "num": "18"},
    {"draw": 7081, "num": "20"}, {"draw": 7080, "num": "79"}, {"draw": 7079, "num": "46"},
    {"draw": 7078, "num": "35"}, {"draw": 7077, "num": "68"}, {"draw": 7076, "num": "16"},
    {"draw": 7075, "num": "68"}, {"draw": 7074, "num": "46"}, {"draw": 7073, "num": "46"},
    {"draw": 7072, "num": "24"}, {"draw": 7071, "num": "56"}, {"draw": 7070, "num": "15"},
    {"draw": 7069, "num": "09"}, {"draw": 7068, "num": "69"}, {"draw": 7067, "num": "57"},
    {"draw": 7066, "num": "29"}, {"draw": 7065, "num": "24"}, {"draw": 7064, "num": "24"},
    {"draw": 7063, "num": "64"}, {"draw": 7062, "num": "29"}, {"draw": 7061, "num": "09"},
    {"draw": 7060, "num": "09"}, {"draw": 7059, "num": "09"}, {"draw": 7058, "num": "48"},
    {"draw": 7057, "num": "06"}, {"draw": 7056, "num": "16"}, {"draw": 7055, "num": "69"},
    {"draw": 7054, "num": "26"}, {"draw": 7053, "num": "89"}, {"draw": 7052, "num": "89"},
    {"draw": 7051, "num": "07"}, {"draw": 7050, "num": "98"}
]

# セッション状態の初期化（履歴は最大50回分を保持）
if "history" not in st.session_state:
    st.session_state.history = INITIAL_DATA.copy()

# -------------------------------------------------------------
# 1. 時間固定ロジック（平日20時切替、土日は月曜20時まで固定）
# -------------------------------------------------------------
def get_current_window_key():
    now = datetime.now(JST)
    # 基準として「当日の20:00」を区切りにする
    # 土日（土曜、日曜）の場合は、次の月曜の20:00まで同一のキーにする
    weekday = now.weekday() # 0:月, 1:火, 2:水, 3:木, 4:金, 5:土, 6:日
    
    target_date = now.date()
    if now.time() < time(20, 0):
        target_date -= timedelta(days=1)
        weekday = target_date.weekday()
    
    # 土日（5:土, 6:日）の場合、月曜の20:00までは金曜日ウィンドウ扱いとするなど固定
    if weekday == 5: # 土
        target_date -= timedelta(days=1)
    elif weekday == 6: # 日
        target_date -= timedelta(days=2)
        
    return target_date.strftime("%Y-%m-%d")

# -------------------------------------------------------------
# 2. 20口選出ロジック（スコアリング・除外・繰り上げ補充）
# -------------------------------------------------------------
def is_zorome(num_str):
    return num_str[0] == num_str[1]

def is_renban(num_str):
    d1 = int(num_str[0])
    d2 = int(num_str[1])
    # 端のつながり（09, 90など）は除外、純粋な差が1のもの
    if abs(d1 - d2) == 1:
        # ただし '0' と '9' のペアは除外（ユーザー指定：端のつながりは連番としない）
        if {d1, d2} == {0, 9}:
            return False
        return True
    return False

def select_top_20_numbers(history_data):
    # 00〜99の候補リスト
    all_candidates = [f"{i:02d}" for i in range(100)]
    
    # 直近データから傾向を分析
    df_hist = pd.DataFrame(history_data)
    df_hist['num_int'] = df_hist['num'].astype(int)
    
    # 出現頻度の計算
    freq_map = df_hist['num'].value_counts().to_dict()
    
    # 前日の当選数字（履歴の先頭が最新）
    latest_num = history_data[0]['num']
    
    # スコアリング（確率・傾向・平均化に基づく評価）
    # 出現回数が少ないもの、およびグループバランスを考慮したスコア算出
    scores = {}
    for num in all_candidates:
        # 基本スコア（出現頻度の逆数や適正頻度からの近さを評価、基本はランダム性を適度に入れつつ確率を反映）
        freq = freq_map.get(num, 0)
        # 0回〜数回のものに適度な重み、極端に出過ぎていないものを優遇
        base_score = 10.0 - (freq * 1.5) + np.random.uniform(0, 2.0)
        
        # 奇数・偶数のバランス補正
        val = int(num)
        if val % 2 != 0:
            base_score += 0.2  # 奇数・偶数の偏り調整
            
        scores[num] = base_score

    # 除外ルールの適用
    excluded = set()
    # 1. 前日の当選数字を除外
    excluded.add(latest_num)
    
    # 2. 前日がゾロ目なら全ゾロ目を除外
    if is_zorome(latest_num):
        for num in all_candidates:
            if is_zorome(num):
                excluded.add(num)
                
    # 3. 前日が連番なら全連番を除外
    if is_renban(latest_num):
        for num in all_candidates:
            if is_renban(num):
                excluded.add(num)

    # 有効な候補をスコアが高い順にソート
    valid_candidates = [num for num in all_candidates if num not in excluded]
    valid_candidates.sort(key=lambda x: scores[x], reverse=True)
    
    # 20個を選出（不足する場合はスコア順に次点から補充、確実に20個確保）
    selected = valid_candidates[:20]
    
    # ユーザーが見やすいよう昇順に並び替え
    selected.sort()
    return selected, latest_num

# -------------------------------------------------------------
# 3. Streamlit 画面レイアウト
# -------------------------------------------------------------
st.title("🎯 ナンバーズ3 ミニ 20口予測システム")

# タブの作成
tab1, tab2, tab3 = st.tabs(["📊 20口予測表示", "📝 当選数字の入力・履歴 (50回)", "📈 出現傾向 棒グラフ"])

# --- タブ1: 20口予測表示 ---
with tab1:
    st.subheader("本日の厳選 20口予測")
    st.info("※設定されたルール（前日連動除外・確率平均化・繰り上げ補充）に基づき選出しています。抽選日20時まで固定表示されます。")
    
    # 固定キーを用いたキャッシュ的表示
    window_key = get_current_window_key()
    
    # 安定した予測結果を得るため、window_keyとhistoryの最新状態をシードにする
    np.random.seed(hash(window_key + st.session_state.history[0]['num']) % (2**32))
    
    selected_20, latest_used = select_top_20_numbers(st.session_state.history)
    st.write(f"**直近の判定基準（前日当選数字）**: `{latest_used}` （有効期間キー: {window_key}）")
    
    st.markdown("---")
    
    # 横5列 × 縦4列のグリッドで表示
    cols_per_row = 5
    rows = 4
    
    for r in range(rows):
        cols = st.columns(cols_per_row)
        for c in range(cols_per_row):
            idx = r * cols_per_row + c
            if idx < len(selected_20):
                with cols[c]:
                    st.metric(label=f"予測口 {idx+1}", value=selected_20[idx])

# --- タブ2: 当選数字の入力・履歴 (50回) ---
with tab2:
    st.subheader("当選数字の登録 & 直近50回履歴管理")
    st.write("新しい抽選結果を入力してください。追加されると自動的に最も古いデータが削除され、常に直近50回分が維持されます。")
    
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            input_draw = st.number_input("抽選回号", min_value=1, value=st.session_state.history[0]['draw'] + 1, step=1)
        with col2:
            input_num = st.text_input("当選下2桁 (00〜99)", max_chars=2, placeholder="例: 16")
            
        submitted = st.form_submit_button("データを追加する")
        
        if submitted:
            if len(input_num) == 2 and input_num.isdigit():
                # 新しいデータを先頭に追加
                new_entry = {"draw": int(input_draw), "num": input_num}
                st.session_state.history.insert(0, new_entry)
                
                # 50回を超える場合は古いものを削除（最大50回を維持）
                if len(st.session_state.history) > 50:
                    st.session_state.history = st.session_state.history[:50]
                    
                st.success(f"第{input_draw}回（{input_num}）を追加しました！")
                st.rerun()
            else:
                st.error("下2桁の数字（00〜99）を正確に2桁で入力してください。")

    st.markdown("---")
    st.subheader("📋 保持している履歴一覧（直近50回）")
    
    # 履歴をデータフレームで表示
    df_display = pd.DataFrame(st.session_state.history)
    df_display.columns = ["抽選回号", "当選下2桁"]
    st.dataframe(df_display, use_container_width=True, height=300)

# --- タブ3: 出現傾向 棒グラフ ---
with tab3:
    st.subheader("10個単位グループ別 出現回数グラフ")
    st.write("直近50回分のデータに基づく、00〜99の10区分ごとの出現頻度です（Y軸目盛り: 0〜15）。")
    
    # 10個単位のグループ分け集計
    bins = [
        ("00-09", range(0, 10)),
        ("10-19", range(10, 20)),
        ("20-29", range(20, 30)),
        ("30-39", range(30, 40)),
        ("40-49", range(40, 50)),
        ("50-59", range(50, 60)),
        ("60-69", range(60, 70)),
        ("70-79", range(70, 80)),
        ("80-89", range(80, 90)),
        ("90-99", range(90, 100)),
    ]
    
    counts = {label: 0 for label, _ in bins}
    
    for item in st.session_state.history:
        val = int(item['num'])
        for label, r in bins:
            if val in r:
                counts[label] += 1
                
    df_chart = pd.DataFrame(list(counts.items()), columns=["グループ", "出現回数"])
    df_chart.set_index("グループ", inplace=True)
    
    # Streamlit標準の棒グラフ（Y軸の最大値を15に固定しやすくするためレイアウト調整）
    st.bar_chart(df_chart, y="出現回数")
    
    st.caption("※Y軸は自動スケーリングされますが、上限15を意識した直近50回分の統計分布です。")
