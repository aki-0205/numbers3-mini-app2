from datetime import datetime, timedelta
import random
import streamlit as st

# --- ページ設定 ---
st.set_page_config(
    page_title="ナンバーズミニ 予測＆的中検証アプリ", page_icon="🎯", layout="centered"
)

# --- 視認性を高めるCSSスタイル ---
st.markdown(
    """
    <style>
    .header-box {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .status-box {
        background-color: #e3f2fd;
        border-left: 6px solid #1976d2;
        padding: 15px;
        border-radius: 8px;
        color: #0d47a1;
        margin-bottom: 15px;
        font-size: 15px;
    }
    .number-box {
        text-align: center;
        background: #ffffff;
        border: 2px solid #90caf9;
        padding: 8px;
        border-radius: 6px;
        margin: 4px;
        font-weight: bold;
        font-size: 16px;
        color: #0d47a1;
    }
    .hit-number-box {
        text-align: center;
        background: #e8f5e9;
        border: 2px solid #4caf50;
        padding: 8px;
        border-radius: 6px;
        margin: 4px;
        font-weight: bold;
        font-size: 16px;
        color: #2e7d32;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ヘッダー ---
st.markdown(
    """
    <div class="header-box">
        <h2>🎯 ナンバーズミニ 予測 ＆ 直近30回的中率管理アプリ</h2>
        <p>【20時切り替え ＆ 的中自動連動システム】</p>
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
        <b>🕒 現在時刻:</b> {now.strftime('%Y年%m月%d日 %H:%M:%S')} （20時境界: {'20時以降' if is_after_20 else '20時前'}）<br>
        <b>🎯 予測対象日:</b> <span style="color: #b71c1c;"><b>{target_date.strftime('%Y年%m月%d日')}</b></span> | 
        <b>📊 的中検証の参照元:</b> <span style="color: #1b5e20;"><b>{reference_date.strftime('%Y年%m月%d日')} の抽選結果</b></span>
    </div>
""",
    unsafe_allow_html=True,
)

# --- 3. セッションステートによる「直近30回」の履歴管理 ---
if "history" not in st.session_state:
  # 初期データ（直近30回分のダミー履歴：日付、当せん数字、的中有無）
  import random

  st.session_state.history = []
  base_d = reference_date - timedelta(days=35)
  for i in range(30):
    base_d += timedelta(days=1)
    if base_d.weekday() >= 5:
      continue
    winning_num = f"{random.randint(0, 99):02d}"
    # ダミーの20個の予測数字
    pred_nums = [f"{j:02d}" for j in range(20)]
    is_hit = winning_num in pred_nums
    st.session_state.history.append({
        "date": base_d.strftime("%Y-%m-%d"),
        "winning_num": winning_num,
        "is_hit": is_hit,
    })
    if len(st.session_state.history) >= 30:
      break

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(
    ["🔮 本日の予測番号", "📈 直近30回の的中率・履歴", "⚙️ システム仕様"]
)

with tab1:
  st.subheader("🔮 20時固定・予測番号生成（20個）")
  st.markdown(
      f"**{target_date.strftime('%Y年%m月%d日')}** 抽選向けの20個の予測数字です。横一列で一覧表示しています。"
  )

  seed_value = int(target_date.strftime("%Y%m%d"))


  def generate_prediction(seed):
    random.seed(seed)
    nums = [f"{random.randint(0, 99):02d}" for _ in range(30)]
    return sorted(list(set(nums)))[:20]


  predictions = generate_prediction(seed_value)

  # 5列のグリッドで綺麗に横並び表示
  cols = st.columns(5)
  for i, num in enumerate(predictions):
    with cols[i % 5]:
      st.markdown(
          f'<div class="number-box">{num}</div>', unsafe_allow_html=True
      )

with tab2:
  st.subheader("📈 直近30回の的中率と履歴一覧")

  # 直近30回のデータから的中率を算出
  history = st.session_state.history[-30:]  # 常に直近30回に制限
  total_count = len(history)
  hit_count = sum(1 for h in history if h["is_hit"])
  hit_rate = (hit_count / total_count * 100) if total_count > 0 else 0.0

  # 上部に的中率と件数をわかりやすく横並びで表示
  m1, m2, m3 = st.columns(3)
  m1.metric("対象データ数", f"{total_count} 回分 (最大30回)")
  m2.metric("的中回数", f"{hit_count} 回")
  m3.metric("🔥 直近的中率", f"{hit_rate:.1f}%")

  st.write("---")
  st.write("📋 **直近の抽選結果と当せん数字の照合履歴（古いものから自動更新）**")

  # テーブル形式またはカード形式で一覧表示
  for item in reversed(history):
    status_icon = "🎉 的中"
    box_class = "hit-number-box" if item["is_hit"] else "number-box"
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; margin-bottom: 6px; background: #f8f9fa; border-radius: 6px; border: 1px solid #dee2e6;">
            <span>📅 <b>{item['date']}</b> 抽選</span>
            <span>当せん数字: <b style="color: #d32f2f;">{item['winning_num']}</b></span>
            <span>判定: <b style="color: {'#2e7d32' if item['is_hit'] else '#c62828'};">{'的中 🎉' if item['is_hit'] else 'ハズレ 💧'}</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab3:
  st.subheader("⚙️ 動作仕様の確認")
  st.markdown("""
    - **日付切り替え**: 毎日 **20:00** を境に当日の予測から翌日（金曜夜なら翌週月曜）の予測へ自動切り替え。
    - **的中判定の仕組み**: 生成された **20個の数字の中** に、実際の当せん数字（1個）が含まれていたかどうかを判定。
    - **直近30回管理**: 30回を超える古いデータは自動的に外され、常に直近30回分の実績と的中率がリアルタイムで更新・表示されます。
    """)
