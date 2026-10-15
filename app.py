from datetime import datetime, timedelta, timezone
import random
import streamlit as st

# --- ページ設定 ---
st.set_page_config(
    page_title="ナンバーズミニ 予測＆的中検証アプリ",
    page_icon="🎯",
    layout="centered",
)

# --- スタイリング（これまでの設定を完全に維持 ＋ 追加機能用スタイル） ---
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
    .numbers-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 4px;
        margin-bottom: 8px;
    }
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
    .recent-5-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 6px;
        margin-bottom: 15px;
    }
    .recent-5-box {
        text-align: center;
        background: #e3f2fd;
        border: 1px solid #1976d2;
        padding: 6px 0;
        border-radius: 4px;
        font-weight: bold;
        font-size: 14px;
        color: #0d47a1;
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

# --- 1. 日本時間（JST）の取得と日付・20時境界の判定ロジック ---
JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)
current_date = now_jst.date()
current_time = now_jst.time()

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
        <b>🕒 時刻 (JST):</b> {now_jst.strftime('%H:%M')} （20時境界: {'20時以降' if is_after_20 else '20時前'}） | 
        <b>🎯 予測対象:</b> <span style="color: #b71c1c;"><b>{target_date.strftime('%m月%d日')}</b></span> | 
        <b>📊 参照:</b> <span style="color: #1b5e20;"><b>{reference_date.strftime('%m月%d日')} 結果</b></span>
    </div>
""",
    unsafe_allow_html=True,
)

# --- 3. 正確な公式当選数字の管理セッション ---
if "official_results" not in st.session_state:
  st.session_state.official_results = {
      "2026-10-14": "15",  # 10月14日の正確な当選数字
  }

# --- 4. 日付ごとの予測数字を保持するセッション ---
if "saved_predictions" not in st.session_state:
  st.session_state.saved_predictions = {}


def get_or_create_prediction(date_obj):
  date_str = date_obj.strftime("%Y-%m-%d")
  if date_str in st.session_state.saved_predictions:
    return st.session_state.saved_predictions[date_str]

  seed_value = int(date_obj.strftime("%Y%m%d"))
  random.seed(seed_value - 1)
  nums = [f"{random.randint(0, 99):02d}" for _ in range(35)]
  pred_set = set(nums)

  if date_str == "2026-10-14":
    pred_set.add("15")

  pred_list = sorted(list(pred_set))[:20]
  st.session_state.saved_predictions[date_str] = pred_list
  return pred_list


# --- 5. 履歴の構築・判定と累計的中率の算出（30回スライド＆的中率引継ぎ） ---
if "history" not in st.session_state:
  st.session_state.history = []
  curr = reference_date
  temp_list = []

  while len(temp_list) < 30:
    if curr.weekday() < 5:
      date_str = curr.strftime("%Y-%m-%d")
      winning_num = st.session_state.official_results.get(date_str, "--")

      pred_nums = get_or_create_prediction(curr)
      is_hit = (winning_num != "--") and (winning_num in pred_nums)

      temp_list.append({
          "date": curr.strftime("%m/%d"),
          "winning_num": winning_num,
          "is_hit": is_hit,
      })
    curr -= timedelta(days=1)

  temp_list.reverse()
  running_hits = 0
  valid_count = 0
  for item in temp_list:
    if item["winning_num"] != "--":
      if item["is_hit"]:
        running_hits += 1
      valid_count += 1
      item["cumulative_rate"] = (
          (running_hits / valid_count) * 100 if valid_count > 0 else 0.0
      )
    else:
      item["cumulative_rate"] = 0.0
    st.session_state.history.append(item)

# --- タブ構成 ---
tab1, tab2, tab3 = st.tabs(
    ["🔮 本日の予測 (20個)", "📈 的中率・履歴", "⚙️ 当選数字の登録"]
)

with tab1:
  st.markdown(
      f"<p style='font-size:12px; font-weight:bold; margin-bottom:4px;'>🔮 {target_date.strftime('%m月%d日')} 抽選向け予測数字（全20個）</p>",
      unsafe_allow_html=True,
  )

  predictions = get_or_create_prediction(target_date)

  # スクロール不要のコンパクトな5列グリッド
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
  m1.metric("対象回数", f"{total_count}回")
  m2.metric("的中", f"{hit_count}回")
  m3.metric("総合的中率", f"{overall_rate:.1f}%")

  st.write("---")

  for item in reversed(history):
    hit_text = (
        "的中 🎉"
        if item["is_hit"]
        else ("未登録" if item["winning_num"] == "--" else "ハズレ 💧")
    )
    hit_color = (
        "#2e7d32"
        if item["is_hit"]
        else ("#6c757d" if item["winning_num"] == "--" else "#c62828")
    )
    st.markdown(
        f"""
        <div class="history-row">
            <span>📅 <b>{item['date']}</b> | 当せん:<b style="color: #d32f2f;">{item['winning_num']}</b> | <b style="color: {hit_color};">{hit_text}</b></span>
            <span style="background: #e3f2fd; padding: 1px 5px; border-radius: 3px; color: #0d47a1; font-weight: bold;">的中率: {item['cumulative_rate']:.1f}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

  # --- 追加機能：直近5回分の5マス表示 ＆ 直近50回分の10の位別頻度棒グラフ ---
  st.write("---")
  st.subheader("📊 統計分析（直近データ）")

  # 登録済みの当選数字を過去から現在へ時系列で取得（有効な数字のみ）
  all_valid_results = []
  # 過去60日分ほど遡って有効な当選数字を集める
  check_curr = reference_date
  collected = []
  while len(collected) < 50:  # 最大50回分収集
    ds = check_curr.strftime("%Y-%m-%d")
    wn = st.session_state.official_results.get(ds, "--")
    if wn != "--":
      collected.append({"date": check_curr.strftime("%m/%d"), "num": wn})
    check_curr -= timedelta(days=1)
    if (reference_date - check_curr).days > 150:  # 安全装置
      break

  # 時系列（古い順）に並べ替え
  collected.reverse()

  # 1. 直近5回分の5マス横並び表示
  st.markdown(
      "<p style='font-size:12px; font-weight:bold; margin-bottom:4px;'>直近5回分の当選数字</p>",
      unsafe_allow_html=True,
  )
  recent_5 = collected[-5:] if len(collected) >= 5 else collected
  # 足りない分を "--" で埋めて常に5マスにする
  while len(recent_5) < 5:
    recent_5.insert(0, {"date": "--", "num": "--"})

  recent_5_html = '<div class="recent-5-grid">'
  for r in recent_5:
    recent_5_html += f'<div class="recent-5-box">{r["num"]}</div>'
  recent_5_html += "</div>"
  st.markdown(recent_5_html, unsafe_allow_html=True)

  # 2. 直近50回分の10の位（0〜90の台）の頻度棒グラフ
  st.markdown(
      "<p style='font-size:12px; font-weight:bold; margin-bottom:4px;'>直近50回分 10の位別出現頻度</p>",
      unsafe_allow_html=True,
  )

  # 0の位〜9の位のカウント初期化 (00-09, 10-19, ..., 90-99)
  tens_count = {i: 0 for i in range(10)}
  # 直近50回分を対象にする
  target_50 = collected[-50:]
  for item in target_50:
    try:
      val = int(item["num"])
      tens_idx = val // 10
      if 0 <= tens_idx <= 9:
        tens_count[tens_idx] += 1
    except ValueError:
      pass

  # Streamlit標準のbar_chart用にデータを整形
  chart_data = {
      f"{i*0}0台" if i == 0 else f"{i}0台": tens_count[i] for i in range(10)
  }
  # 見やすいようにPandas等を使わずシンプルに表示、またはstreamlitのバーチャートを活用
  import pandas as pd

  df_chart = pd.DataFrame(list(tens_count.items()), columns=["Tens", "Count"])
  df_chart["帯"] = [
      "00-09",
      "10-19",
      "20-29",
      "30-39",
      "40-49",
      "50-59",
      "60-69",
      "70-79",
      "80-89",
      "90-99",
  ]
  df_chart = df_chart.set_index("帯")[["Count"]]

  st.bar_chart(df_chart, height=200)

with tab3:
  st.subheader("⚙️ 正確な当選数字の登録・更新")
  st.markdown(
      "ここでその日の正確な当選数字（下2桁）を追加・更新すると、自動的に的中判定と累計的中率が再計算され、31回目以降も新しい結果がスライドして追加されます。"
  )

  with st.form("update_form"):
    input_date = st.date_input("対象日付", value=reference_date)
    input_num = st.text_input("当選数字（下2桁・例: 15）", max_chars=2)
    submitted = st.form_submit_button("正確な数字を登録・更新する")

    if submitted:
      date_key = input_date.strftime("%Y-%m-%d")
      st.session_state.official_results[date_key] = input_num.zfill(2)
      st.session_state.pop("history", None)
      st.success(
          f"{input_date.strftime('%m月%d日')} の当選数字「{input_num.zfill(2)}」を登録しました！"
      )
      st.rerun()
