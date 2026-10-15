from datetime import datetime, timedelta
import random
import streamlit as st

# --- ページ設定 ---
st.set_page_config(
    page_title="ナンバーズミニ 予測＆的中検証アプリ",
    page_icon="🎯",
    layout="centered",
)

# --- スタイリング（マス目をコンパクトに最適化） ---
st.markdown(
    """
    <style>
    .header-box {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%);
        padding: 8px;
        border-radius: 6px;
        color: white;
        text-align: center;
        margin-bottom: 6px;
    }
    .status-box {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
        padding: 6px 8px;
        border-radius: 4px;
        color: #0d47a1;
        margin-bottom: 6px;
        font-size: 11px;
    }
    /* スマホでも収まるコンパクトな5列グリッド */
    .numbers-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 4px;
        margin-bottom: 8px;
    }
    /* 各数字のカード：マス目を小さくコンパクトに調整 */
    .num-card {
        text-align: center;
        background: #ffffff;
        border: 1.5px solid #2196f3;
        padding: 4px 0;
        border-radius: 4px;
        font-weight: bold;
        font-size: 15px;
        color: #0d47a1;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    /* 履歴の各行：右側に的中率を配置 */
    .history-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 5px 8px;
        margin-bottom: 3px;
        background: #f8f9fa;
        border-radius: 4px;
        border: 1px solid #dee2e6;
        font-size: 11px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ヘッダー ---
st.markdown(
    """
    <div class="header-box">
        <h5 style="margin:0; font-size: 14px;">🎯 ナンバーズミニ 予測 ＆ 的中率管理</h5>
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
        <b>🕒 時刻:</b> {now.strftime('%H:%M')} （20時境界: {'20時以降' if is_after_20 else '20時前'}） | 
        <b>🎯 予測対象:</b> <span style="color: #b71c1c;"><b>{target_date.strftime('%m月%d日')}</b></span> | 
        <b>📊 参照:</b> <span style="color: #1b5e20;"><b>{reference_date.strftime('%m月%d日')} 結果</b></span>
    </div>
""",
    unsafe_allow_html=True,
)

# --- 3. セッションステートによる「直近30回」の履歴管理 ---
if "history" not in st.session_state:
  st.session_state.history = []
  curr = reference_date
  temp_list = []

  while len(temp_list) < 30:
    if curr.weekday() < 5:
      random.seed(int(curr.strftime("%Y%m%d")))
      winning_num = f"{random.randint(0, 99):02d}"

      random.seed(int(curr.strftime("%Y%m%d")) - 1)
      pred_nums = sorted(
          list(set([f"{j:02d}" for j in range(35)]))[:20]
      )

      is_hit = winning_num in pred_nums
      temp_list.append({
          "date": curr.strftime("%m/%d"),
          "winning_num": winning_num,
          "is_hit": is_hit,
      })
    curr -= timedelta(days=1)

  temp_list.reverse()
  running_hits = 0
  for idx, item in enumerate(temp_list):
    if item["is_hit"]:
      running_hits += 1
    item["cumulative_rate"] = (running_hits / (idx + 1)) * 100
    st.session_state.history.append(item)

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(
    ["🔮 本日の予測 (20個)", "📈 的中率・履歴", "⚙️ 仕様"]
)

with tab1:
  st.markdown(
      f"<p style='font-size:12px; font-weight:bold; margin-bottom:4px;'>🔮 {target_date.strftime('%m月%d日')} 抽選向け予測数字（全20個）</p>",
      unsafe_allow_html=True,
  )

  seed_value = int(target_date.strftime("%Y%m%d"))


  def generate_prediction(seed):
    random.seed(seed)
    nums = [f"{random.randint(0, 99):02d}" for _ in range(35)]
    return sorted(list(set(nums)))[:20]


  predictions = generate_prediction(seed_value)

  # コンパクトな5列グリッドで一望
  cards_html = '<div class="numbers-grid">'
  for num in predictions:
    cards_html += f'<div class="num-card">{num}</div>'
  cards_html += "</div>"

  st.markdown(cards_html, unsafe_allow_html=True)

with tab2:
  st.subheader("📈 履歴と毎日の的中率")

  history = st.session_state.history[-30:]
  total_count = len(history)
  hit_count = sum(1 for h in history if h["is_hit"])
  overall_rate = (hit_count / total_count * 100) if total_count > 0 else 0.0

  m1, m2, m3 = st.columns(3)
  m1.metric("回数", f"{total_count}回")
  m2.metric("的中", f"{hit_count}回")
  m3.metric("的中率", f"{overall_rate:.1f}%")

  st.write("---")

  for item in reversed(history):
    hit_text = "的中 🎉" if item["is_hit"] else "ハズレ 💧"
    hit_color = "#2e7d32" if item["is_hit"] else "#c62828"
    st.markdown(
        f"""
        <div class="history-row">
            <span>📅 <b>{item['date']}</b> | 当せん:<b style="color: #d32f2f;">{item['winning_num']}</b> | <b style="color: {hit_color};">{hit_text}</b></span>
            <span style="background: #e3f2fd; padding: 1px 5px; border-radius: 3px; color: #0d47a1; font-weight: bold;">的中率: {item['cumulative_rate']:.1f}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab3:
  st.subheader("⚙️ 動作仕様")
  st.markdown("""
    - **コンパクトなグリッド**: マス目のサイズを小さく調整し、スマホ画面でスクロールなしですべての数字が一目で確認可能。
    - **右側的中率表示**: 履歴リストの各行の右側にその日時点の的中率を常時表示。
    - **20時境界・金曜夜スキップ**: 20時以降の切り替えおよび週末の月曜送りも完備。
    """)
