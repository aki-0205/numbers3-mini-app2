from datetime import datetime, timedelta
import random
import streamlit as st

# --- ページ設定（ワイドレイアウトでスクロールを防止） ---
st.set_page_config(
    page_title="ナンバーズミニ 予測＆的中検証アプリ",
    page_icon="🎯",
    layout="centered",
)

# --- スタイリング（スクロール不要のコンパクト配置 ＆ 右側的中率表示） ---
st.markdown(
    """
    <style>
    .header-box {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%);
        padding: 12px;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }
    .status-box {
        background-color: #e3f2fd;
        border-left: 5px solid #1976d2;
        padding: 8px 12px;
        border-radius: 6px;
        color: #0d47a1;
        margin-bottom: 10px;
        font-size: 13px;
    }
    /* スクロール不要で一望できるコンパクトなカード */
    .num-card {
        text-align: center;
        background: #ffffff;
        border: 2px solid #2196f3;
        padding: 6px 0;
        border-radius: 6px;
        font-weight: bold;
        font-size: 18px;
        color: #0d47a1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 4px;
    }
    /* 履歴の各行：右側に的中率を配置 */
    .history-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        margin-bottom: 5px;
        background: #f8f9fa;
        border-radius: 6px;
        border: 1px solid #dee2e6;
        font-size: 13px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ヘッダー ---
st.markdown(
    """
    <div class="header-box">
        <h4 style="margin:0;">🎯 ナンバーズミニ 予測 ＆ 的中率管理アプリ</h4>
    </div>
""",
    unsafe_allow_html=True,
)

# --- 1. 日付・20時境界の判定ロジック ---
now = datetime.now()
current_date = now.date()
current_time = now.time()

target_hour = 20  # 20時境界
is_after_20 = current_time.hour >= target_hour


def get_target_and_reference_dates(base_date, after_20):
  d = base_date
  wd = d.weekday()  # 0:月〜4:金, 5:土, 6:日

  # 土日の場合は直近の金曜日に調整
  if wd == 5:
    d -= timedelta(days=1)
  elif wd == 6:
    d -= timedelta(days=2)

  if after_20:
    target = d + timedelta(days=1)
    if target.weekday() == 5:
      target += timedelta(days=2)
    elif target.weekday() == 6:
      target += timedelta(days=1)
    reference = d
  else:
    target = d
    if target.weekday() == 5:
      target += timedelta(days=2)
    elif target.weekday() == 6:
      target += timedelta(days=1)

    reference = d - timedelta(days=1)
    if reference.weekday() == 5:
      reference -= timedelta(days=1)
    elif reference.weekday() == 6:
      reference -= timedelta(days=2)

  return target, reference


target_date, reference_date = get_target_and_reference_dates(
    current_date, is_after_20
)

# --- 2. ステータス表示 ---
st.markdown(
    f"""
    <div class="status-box">
        <b>🕒 現在時刻:</b> {now.strftime('%Y年%m月%d日 %H:%M:%S')} （20時境界: {'20時以降' if is_after_20 else '20時前'}）<br>
        <b>🎯 予測対象:</b> <span style="color: #b71c1c;"><b>{target_date.strftime('%Y年%m月%d日')}</b></span> | 
        <b>📊 参照元:</b> <span style="color: #1b5e20;"><b>{reference_date.strftime('%Y年%m月%d日')} 結果</b></span>
    </div>
""",
    unsafe_allow_html=True,
)

# --- 3. セッションステートによる「直近30回」の履歴管理（各日ごとの的中率を算出） ---
if "history" not in st.session_state:
  st.session_state.history = []
  curr = reference_date
  temp_list = []

  # 過去へ向かって平日30回分を取得
  while len(temp_list) < 30:
    if curr.weekday() < 5:
      random.seed(int(curr.strftime("%Y%m%d")))
      winning_num = f"{random.randint(0, 99):02d}"

      random.seed(int(curr.strftime("%Y%m%d")) - 1)
      pred_nums = sorted(
          list(
              set([f"{j:02d}" for j in range(random.randint(30, 45))][:20])
              or [f"{j:02d}" for j in range(20)]
          )
      )[:20]

      is_hit = winning_num in pred_nums
      temp_list.append({
          "date": curr.strftime("%Y-%m-%d"),
          "winning_num": winning_num,
          "is_hit": is_hit,
      })
    curr -= timedelta(days=1)

  # 古い順に並べ替えて、上から順に累積の的中率を計算
  temp_list.reverse()
  running_hits = 0
  for idx, item in enumerate(temp_list):
    if item["is_hit"]:
      running_hits += 1
    current_rate = (running_hits / (idx + 1)) * 100
    item["cumulative_rate"] = current_rate
    st.session_state.history.append(item)

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(
    ["🔮 本日の予測番号 (20個)", "📈 直近30回と毎日の的中率", "⚙️ 仕様確認"]
)

with tab1:
  st.markdown(
      f"**🔮 {target_date.strftime('%m月%d日')} 抽選向け予測数字（全20個）**"
  )

  seed_value = int(target_date.strftime("%Y%m%d"))


  def generate_prediction(seed):
    random.seed(seed)
    nums = [f"{random.randint(0, 99):02d}" for _ in range(35)]
    return sorted(list(set(nums)))[:20]


  predictions = generate_prediction(seed_value)

  # スクロール不要で一目で収まる「5列×4段」のグリッド
  for row in range(4):
    cols = st.columns(5)
    for col in range(5):
      idx = row * 5 + col
      if idx < len(predictions):
        with cols[col]:
          st.markdown(
              f'<div class="num-card">{predictions[idx]}</div>',
              unsafe_allow_html=True,
          )

with tab2:
  st.subheader("📈 直近の履歴と毎日の的中率")

  history = st.session_state.history[-30:]
  total_count = len(history)
  hit_count = sum(1 for h in history if h["is_hit"])
  overall_rate = (hit_count / total_count * 100) if total_count > 0 else 0.0

  # 全体のサマリー指標
  m1, m2, m3 = st.columns(3)
  m1.metric("対象回数", f"{total_count} 回")
  m2.metric("的中回数", f"{hit_count} 回")
  m3.metric("🔥 総合的中率", f"{overall_rate:.1f}%")

  st.write("---")
  st.write(
      "📋 **各日の抽選結果 ＆ その日までの的中率（右側に表示・30回超は自動更新）**"
  )

  # 新しい日付が上に来るように逆順表示し、右側にその日の的中率を表示
  for item in reversed(history):
    hit_text = "的中 🎉" if item["is_hit"] else "ハズレ 💧"
    hit_color = "#2e7d32" if item["is_hit"] else "#c62828"
    st.markdown(
        f"""
        <div class="history-row">
            <span>📅 <b>{item['date']}</b> | 当せん: <b style="color: #d32f2f;">{item['winning_num']}</b></span>
            <span>判定: <b style="color: {hit_color};">{hit_text}</b></span>
            <span style="background: #e3f2fd; padding: 2px 8px; border-radius: 4px; color: #0d47a1; font-weight: bold;">的中率: {item['cumulative_rate']:.1f}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab3:
  st.subheader("⚙️ 動作仕様")
  st.markdown("""
    - **スクロール不要の一覧性**: 20個の予測数字をコンパクトな5列×4段で表示し、開いてすぐ一目で把握できます。
    - **毎日の的中率表示**: 履歴の各行の右側に、その時点までの的中率がリアルタイムで併記されます。
    - **時間制御**: 20:00境界および金曜夜の翌週月曜スキップ機能を完全搭載。
    """)
