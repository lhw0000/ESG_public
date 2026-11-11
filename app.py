import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# verify=False 會產生 InsecureRequestWarning,這裡關閉警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="公開資訊資料檢視", page_icon="📊", layout="wide")
st.title("📊 公開資訊資料檢視")

DEFAULT_URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv"  # 換連結

# -------------------------------------------------------------------
# 側邊欄
# -------------------------------------------------------------------
with st.sidebar:
    st.header("設定")
    url = st.text_input("CSV 連結", value=DEFAULT_URL)
    verify_ssl = st.checkbox("驗證 SSL 憑證 (verify)", value=False)
    drop_na = st.checkbox("移除含空值的列 (dropna)", value=True)
    save_local = st.checkbox("同時儲存為 data01.csv", value=False)
    reload_btn = st.button("🔄 重新下載資料")


# -------------------------------------------------------------------
# 資料讀取 (快取 1 小時)
# -------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="資料下載中...")
def load_data(url: str, verify: bool, dropna: bool, save: bool) -> pd.DataFrame:
    response = requests.get(url, verify=verify, timeout=30)
    response.raise_for_status()

    if save:
        with open("data01.csv", "wb") as file:
            file.write(response.content)

    df = pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")  # 繁體中文
    if dropna:
        df = df.dropna()
    return df


if reload_btn:
    st.cache_data.clear()

try:
    df = load_data(url, verify_ssl, drop_na, save_local)
except Exception as e:
    st.error(f"資料讀取失敗:{e}")
    st.stop()

# -------------------------------------------------------------------
# 顯示資料
# -------------------------------------------------------------------
col1, col2 = st.columns(2)
col1.metric("資料筆數", f"{len(df):,}")
col2.metric("欄位數", f"{df.shape[1]:,}")

keyword = st.text_input("🔍 關鍵字搜尋 (搜尋所有欄位)")
if keyword:
    mask = df.astype(str).apply(
        lambda col: col.str.contains(keyword, case=False, na=False)
    ).any(axis=1)
    view_df = df[mask]
    st.caption(f"符合 {len(view_df):,} 筆")
else:
    view_df = df

st.dataframe(view_df, use_container_width=True, height=500)

st.download_button(
    label="⬇️ 下載 CSV",
    data=view_df.to_csv(index=False).encode("utf-8-sig"),
    file_name="data01.csv",
    mime="text/csv",
)
