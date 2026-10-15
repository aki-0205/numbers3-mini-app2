from datetime import datetime, timedelta
import random
import streamlit as st

# --- ページ設定 ---
st.set_page_config(
    page_title="ナンバーズミニ 予測＆直近30回的中率管理アプリ", page_icon="🎯", layout="centered"
)

# --- 視認性とデザインを高めるCSSスタイル ---
st.markdown(
    """
    <style>
    .header-box {
        background: linear-gradient(135deg, #0d47a1 0%, #1976d2 100%);
        padding: 18px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 15px;
    }
    .status-box {
        background-color: #e3f2fd;
        border-left: 6px solid #1976d2;
        padding: 12px;
        border-radius: 6px;
        color: #0d47a1;
        margin-bottom: 15px;
        font-size: 14px;
    }
    .num-card {
        text-align: center;
        background: #ffffff;
        border: 2px solid #2196f3;
        padding: 10px 0;
        border-radius: 8px;
        font-weight: bold;
        font-size: 20px;
        color: #0d47a1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        margin-bottom: 8px;
    }
    .history-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        margin-bottom: 6px;
        background: #f8f9fa;
        border-radius: 6px;
        border: 1px solid #dee2e6;
        font-size: 14px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ヘッダー ---
st.markdown(
    """
    <div class="header-box">
        <h3>🎯 ナンバーズミニ 予測 ＆ 直近30回的中率管理アプリ</h3>
        <p style="margin:0; font-size: 13px;">【20時境界切り替え ＆ 自動連動システム】</p>
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
    # 20時以降：翌日が予測対象
    target = d + timedelta(days=1)
    if target.weekday() == 5:  # 土曜なら月曜へ
      target += timedelta(days=2)
    elif target.weekday() == 6:  # 日曜なら月曜へ
      target += timedelta(days=1)
    reference = d  # 結果の参照元は今日
  else:
    # 20時前：今日が予測対象
    target = d
    if target.weekday() == 5:
      target += timedelta(days=2)
    elif target.weekday() == 6:
      target += timedelta(days=1)

    # 結果の参照元は前日（平日の直近）
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
        <b>🕒 現在時刻:</b> {now.strftime('%Y年%m月%d日 %H:%M:%S')} （20時境界判定: {'20時以降' if is_after_20 else '20時前'}）<br>
        <b>🎯 今回の予測対象日:</b> <span style="color: #b71c1c;"><b>{target_date.strftime('%Y年%m月%d日')}</b></span> | 
        <b>📊 抽選結果の参照元:</b> <span style="color: #1b5e20;"><b>{reference_date.strftime('%Y年%m月%d日')} の確定結果</b></span>
    </div>
""",
    unsafe_allow_html=True,
)

# --- 3. セッションステートによる「直近30回」の履歴管理 ---
if "history" not in st.session_state:
  st.session_state.history = []
  curr = reference_date
  generated_count = 0

  # 参照元日から過去へ向かって平日（月〜金）を30回分生成し、最新データ（14日・13日等）を含める
  while generated_count < 30:
    if curr.weekday() < 5:  # 平日のみ
      # 決定的なダミー当選番号を生成（実際のCSVデータ等に変更可能）
      random.seed(int(curr.strftime("%Y%m%d")))
      winning_num = f"{random.randint(0, 99):02d}"

      # 当該日の予測20個
      random.seed(int(curr.strftime("%Y%m%d")) - 1)
      pred_nums = [f"{j:02d}" for j in range(35)]
      pred_nums = sorted(list(set(pred_nums)))[:20]

      is_hit = winning_num in pred_nums

      st.session_state.history.append({
          "date": curr.strftime("%Y-%m-%d"),
          "winning_num": winning_num,
          "is_hit": is_hit,
      })
      generated_count += 1
    curr -= timedelta(days=1)

  # 時系列順（古い順）に並び替え
  st.session_state.history.reverse()

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(
    ["🔮 本日の予測番号 (20個)", "📈 直近30回の的中率・履歴", "⚙️ 仕様確認"]
)

with tab1:
  st.subheader(
      f"🔮 【{target_date.strftime('%m月%d日')} 抽選向け】 予測数字（全20個）"
  )
  st.markdown(
      "👇 **5列×4段のグリッドで全20個の数字が一目ですべて確認できます**"
  )

  seed_value = int(target_date.strftime("%Y%m%d"))


  def generate_prediction(seed):
    random.seed(seed)
    nums = [f"{random.randint(0, 99):02d}" for _ in range(35)]
    return sorted(list(set(nums)))[:20]


  predictions = generate_prediction(seed_value)

  # 5列×4段のカードグリッド描画
  for row in range(4):  # 4行
    cols = st.columns(5)
    for col in range(5):  # 5列
      idx = row * 5 + col
      if idx < len(predictions):
        with cols[col]:
          st.markdown(
              f'<div class="num-card">{predictions[idx]}</div>',
              unsafe_allow_html=True,
          )

with tab2:
  st.subheader("📈 直近30回の的中率と履歴一覧")

  history = st.session_state.history[-30:]
  total_count = len(history)
  hit_count = sum(1 for h in history if h["is_hit"])
  hit_rate = (hit_count / total_count * 100) if total_count > 0 else 0.0

  # 的中率と件数の表示（横並びメトリック）
  m1, m2, m3 = st.columns(3)
  m1.metric("対象データ数", f"{total_count} 回分 (最大30回)")
  m2.metric("的中回数", f"{hit_count} 回")
  m3.metric("🔥 直近的中率", f"{hit_rate:.1f}%")

  st.write("---")
  st.write(
      "📋 **直近の抽選結果履歴（14日・13日などの最新結果を含む直近30回・古いものは自動で押し出されます）**"
  )

  # 新しい日付が上に来るように逆順で一覧表示
  for item in reversed(history):
    st.markdown(
        f"""
        <div class="history-row">
            <span>📅 <b>{item['date']}</b> 抽選</span>
            <span>当せん数字: <b style="color: #d32f2f; font-size: 15px;">{item['winning_num']}</b></span>
            <span>判定: <b style="color: {'#2e7d32' if item['is_hit'] else '#c62828'};">{'的中 🎉' if item['is_hit'] else 'ハズレ 💧'}</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab3:
  st.subheader("⚙️ 動作仕様の確認")
  st.markdown("""
    - **20時境界 & 金曜スキップ**: 毎日20:00を境に予測対象が翌日に切り替わり、金曜20時以降や土日は自動的に次週の月曜日にスキップされます。
    - **一目でわかる20個一覧**: 20個の予測数字を5列×4段のカード形式でスクロールなしで一望できます。
    - **直近30回の自動更新的中率**: 20個の予測の中に当せん数字が含まれていたかを判定し、常に直近30回分のデータと的中率をリアルタイムで維持・更新します。
    """)
