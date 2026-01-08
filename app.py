import streamlit as st
import urllib.parse

# ==========================================
# 0. 系統設置
# ==========================================

st.set_page_config(
    page_title="三一協會健康諮詢APP",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 初始化 Session State
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'
if 'selected_symptom' not in st.session_state:
    st.session_state['selected_symptom'] = None
if 'user_district' not in st.session_state:
    st.session_state['user_district'] = "桃園區" # 預設值

# ==========================================
# 1. CSS 樣式設計 (針對手機觸控優化)
# ==========================================
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: "Microsoft JhengHei", sans-serif;
    }
    
    /* 按鈕優化 */
    .stButton>button {
        width: 100%;
        min-height: 65px;
        font-size: 22px !important; 
        font-weight: bold;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* 🚨 紅色求救按鈕 (首頁專用) */
    .stButton>button[kind="primary"] {
        height: 90px !important;      
        font-size: 32px !important;   
        background-color: #d32f2f !important;
        color: white !important;
        border: 2px solid white !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

    /* 醫院卡片 */
    .hospital-card {
        background-color: #f8f9fa;
        border-left: 6px solid #1a237e;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .hospital-name {
        font-size: 24px;
        font-weight: 900;
        color: #1a237e;
        margin-bottom: 5px;
    }
    
    /* 警示橫幅 */
    .alert-banner {
        padding: 15px;
        color: white;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .bg-red { background-color: #c62828; }
    .bg-yellow { background-color: #fbc02d; color: black !important; }
    .bg-green { background-color: #2e7d32; }
    
    /* SOP 文字 */
    .sop-text {
        font-size: 20px;
        margin: 5px 0;
        padding: 10px;
        background: #eef;
        border-radius: 5px;
        border-left: 4px solid #5c6bc0;
    }
    
    /* 連結按鈕 (核心修復部分) */
    a.action-btn {
        display: inline-block;
        padding: 12px 20px; /* 加大點擊範圍 */
        color: white !important;
        text-decoration: none;
        border-radius: 8px;
        margin-right: 8px;
        margin-top: 8px;
        font-size: 18px;
        font-weight: bold;
        text-align: center;
        background-color: #0288d1; /* 藍色導航 */
        min-width: 120px;
    }
    a.phone-btn {
        background-color: #00897b; /* 綠色撥打 */
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 資料庫 (桃園版)
# ==========================================

# 桃園行政區列表
DISTRICTS = [
    "桃園區", "中壢區", "平鎮區", "八德區", "楊梅區", 
    "蘆竹區", "龜山區", "龍潭區", "大溪區", "大園區", 
    "觀音區", "新屋區", "復興區"
]

# 桃園主要醫院資料庫
TAOYUAN_HOSPITALS = [
    {"name": "林口長庚紀念醫院", "dist": "龜山區", "level": 1, "tel": "03-328-1200", "addr": "桃園市龜山區復興街5號"},
    {"name": "衛福部桃園醫院", "dist": "桃園區", "level": 1, "tel": "03-369-9721", "addr": "桃園市桃園區中山路1492號"},
    {"name": "天晟醫院", "dist": "中壢區", "level": 2, "tel": "03-462-9292", "addr": "桃園市中壢區延平路155號"},
    {"name": "聯新國際醫院", "dist": "平鎮區", "level": 2, "tel": "03-494-1234", "addr": "桃園市平鎮區廣泰路77號"},
    {"name": "國軍桃園總醫院", "dist": "龍潭區", "level": 2, "tel": "03-479-9595", "addr": "桃園市龍潭區中興路168號"},
    {"name": "敏盛綜合醫院", "dist": "桃園區", "level": 2, "tel": "03-317-9599", "addr": "桃園市桃園區經國路168號"},
    {"name": "怡仁綜合醫院", "dist": "楊梅區", "level": 2, "tel": "03-485-5566", "addr": "桃園市楊梅區楊新北路321巷30號"},
    {"name": "聖保祿醫院", "dist": "桃園區", "level": 2, "tel": "03-361-3141", "addr": "桃園市桃園區建新街123號"},
    {"name": "臺北榮總桃園分院", "dist": "桃園區", "level": 2, "tel": "03-338-4889", "addr": "桃園市桃園區成功路三段100號"},
]

# 症狀資料庫
SYMPTOMS_DB = {
    # --- Tab 1: 頭部/心臟 ---
    "嘴歪眼斜/單側無力 (中風)": ("RED", ["⛔ 絕對不可餵食/餵藥", "🛌 讓患者側躺防嗆到", "⏱️ 記下發作時間"]),
    "劇烈頭痛 (像被雷打到)": ("RED", ["🛌 保持安靜躺下", "🚑 立即呼叫救護車"]),
    "意識不清/叫不醒": ("RED", ["🗣️ 大聲呼喚檢查反應", "🛌 側躺暢通呼吸道"]),
    "頭暈/天旋地轉": ("GREEN", ["🪑 坐下休息防跌倒", "💧 喝溫開水", "💊 若有高血壓請量血壓"]),
    "突然看不見/視力模糊": ("RED", ["⛔ 不要揉眼睛", "🚑 這是中風警訊，快去大醫院"]),
    "胸痛 (像石頭壓/冒冷汗)": ("RED", ["⛔ 停止所有活動", "🪑 採半坐臥姿勢", "💊 若有舌下含片可使用"]),
    "心跳很快/心悸": ("YELLOW", ["🪑 坐下深呼吸", "⌚ 測量脈搏"]),
    "呼吸困難/喘不過氣": ("RED", ["🪑 端坐呼吸(坐著身體前傾)", "👕 解開衣領鈕扣"]),
    
    # --- Tab 2: 肚子/內科 ---
    "咳血": ("RED", ["🥣 保留檢體", "🚑 立即就醫"]),
    "肚子劇痛 (按壓會痛)": ("YELLOW", ["⛔ 暫時禁食", "🌡️ 量測體溫"]),
    "吐血/解黑便": ("RED", ["⛔ 禁止飲食", "🚑 收集嘔吐物/拍照"]), 
    "嚴重拉肚子/嘔吐": ("YELLOW", ["💧 補充水分/電解質", "💊 攜帶目前用藥"]),
    "無法排尿 (脹痛)": ("YELLOW", ["⛔ 勿強壓膀胱", "🏥 需導尿"]),
    "誤食農藥/毒物": ("RED", ["📸 拍下農藥罐子", "⛔ 不要催吐", "🚑 叫救護車"]),

    # --- Tab 3: 外傷/跌倒 ---
    "骨折 (肢體變形)": ("RED", ["⛔ 不要移動患肢", "🪵 就地固定(用紙板/木棍)"]),
    "嚴重割傷 (血流不止)": ("YELLOW", ["🩹 直接加壓止血", "✋ 抬高患肢"]),
    "一般跌倒 (皮肉傷)": ("GREEN", ["🧼 清水沖洗傷口", "🩹 消毒包紮"]),
    "跌倒 (撞到頭/想吐)": ("RED", ["⛔ 不要睡著，觀察意識", "🚑 腦震盪警訊"]),
    "被蛇/虎頭蜂咬傷": ("YELLOW", ["📸 記住蛇/蜂的特徵", "⛔ 勿切開傷口", "⌚ 取下戒指"]),
    "被狗/動物咬傷": ("YELLOW", ["🧼 大量清水沖洗", "🏥 需打狂犬病疫苗"]),

    # --- Tab 4: 其他 ---
    "發高燒 (>38.5度)": ("YELLOW", ["💧 多喝水", "👕 穿透氣衣物散熱"]),
    "血糖過低 (冒冷汗/手抖)": ("YELLOW", ["🍬 吃糖果/喝果汁", "🛌 休息觀察"]),
    "皮膚紅腫/長疹子": ("GREEN", ["📷 拍照記錄", "⛔ 勿抓破"]),
    "慢性病拿藥": ("GREEN", ["💊 攜帶健保卡", "📅 確認醫生班表"]),
    "身體痠痛/復健": ("GREEN", ["🌡️ 熱敷", "💊 貼布"]),
    "只是覺得怪怪的 (虛弱)": ("GREEN", ["🛌 多休息", "📞 打電話給子女聊天"])
}

# ==========================================
# 3. 邏輯處理函數 (修正重點)
# ==========================================

def get_google_maps_link(query):
    """
    產生 Google Maps 導航連結 (FIXED: 使用官方 Universal Link)
    """
    # 將地址編碼 (例如 "桃園市" 變成 "%E6%A1%83%E5%9C%92%E5%B8%82")
    query_enc = urllib.parse.quote(query)
    # 這是 Google Maps 官方文件指定的跨平台導航網址格式
    return f"https://www.google.com/maps/dir/?api=1&destination={query_enc}"

def find_nearest_hospitals(user_dist, severity_level):
    if severity_level == "GREEN":
        return []

    target_levels = [1] if severity_level == "RED" else [1, 2]
    local_matches = [h for h in TAOYUAN_HOSPITALS if h['dist'] == user_dist and h['level'] in target_levels]
    
    if not local_matches:
        if severity_level == "RED":
            return [h for h in TAOYUAN_HOSPITALS if h['level'] == 1]
        else:
            return TAOYUAN_HOSPITALS
            
    return local_matches

# ==========================================
# 4. 頁面邏輯
# ==========================================

def page_home():
    st.title("🏥 三一協會健康諮詢")
    
    msg = "親愛的長輩朋友，身體不舒服不要忍耐。請先告訴我們您在哪裡，然後按下紅色按鈕。"
    st.markdown(f"""<div style="background-color:#fff3e0; padding:15px; border-radius:10px; border-left:5px solid #ff9800;"><b>💌 叮嚀：</b><br>{msg}</div>""", unsafe_allow_html=True)
    
    st.write("")
    
    st.markdown("### 📍 第一步：您現在在哪裡？")
    st.session_state['user_district'] = st.selectbox(
        "請選擇您的行政區：", 
        DISTRICTS, 
        index=DISTRICTS.index(st.session_state['user_district'])
    )
    
    st.write("---")
    st.markdown("### 👇 第二步：身體不舒服按這裡")
    
    if st.button("🆘 救命 / 不舒服", type="primary", use_container_width=True):
        st.session_state['page'] = 'symptom_select'
        st.rerun()

    st.write("---")
    with st.expander("ℹ️ 關於三一協會", expanded=False):
        st.write("三一協會致力於關懷社區長者健康，提供即時的數位諮詢工具。本工具僅供輔助參考，緊急狀況請直接撥打 119。")

def page_symptom_select():
    st.title("👀 哪裡不舒服？")
    col_back, col_home = st.columns([1, 3])
    with col_back:
        if st.button("🔙 上一頁"):
            st.session_state['page'] = 'home'
            st.rerun()
    
    st.info(f"📍 目前位置設定：**桃園市 {st.session_state['user_district']}**")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🧠 頭/心臟", "🤢 肚子/內科", "🦴 跌倒/外傷", "💊 發燒/其他"])
    
    def create_buttons(symptom_list, container):
        cols = container.columns(2)
        for i, sym in enumerate(symptom_list):
            if cols[i % 2].button(sym):
                go_to_result(sym)

    with tab1:
        st.subheader("頭痛、中風、心臟")
        symptoms = ["嘴歪眼斜/單側無力 (中風)", "劇烈頭痛 (像被雷打到)", "意識不清/叫不醒", 
                   "胸痛 (像石頭壓/冒冷汗)", "呼吸困難/喘不過氣", "心跳很快/心悸", 
                   "突然看不見/視力模糊", "頭暈/天旋地轉"]
        create_buttons(symptoms, st)

    with tab2:
        st.subheader("肚子痛、吐、大小便")
        symptoms = ["肚子劇痛 (按壓會痛)", "吐血/解黑便", "嚴重拉肚子/嘔吐", 
                   "無法排尿 (脹痛)", "誤食農藥/毒物", "咳血"]
        create_buttons(symptoms, st)

    with tab3:
        st.subheader("流血、骨折、被咬")
        symptoms = ["骨折 (肢體變形)", "嚴重割傷 (血流不止)", "跌倒 (撞到頭/想吐)", 
                   "被蛇/虎頭蜂咬傷", "被狗/動物咬傷", "一般跌倒 (皮肉傷)"]
        create_buttons(symptoms, st)
                
    with tab4:
        st.subheader("發燒、慢性病、怪怪的")
        symptoms = ["發高燒 (>38.5度)", "血糖過低 (冒冷汗/手抖)", "皮膚紅腫/長疹子", 
                   "慢性病拿藥", "身體痠痛/復健", "只是覺得怪怪的 (虛弱)"]
        create_buttons(symptoms, st)

def go_to_result(symptom):
    st.session_state['selected_symptom'] = symptom
    st.session_state['page'] = 'result'
    st.rerun()

def page_result():
    symptom = st.session_state['selected_symptom']
    district = st.session_state['user_district']
    
    level_color, sop_list = SYMPTOMS_DB.get(symptom, ("GREEN", []))
    
    if level_color == "RED":
        st.markdown('<div class="alert-banner bg-red">🚨 生命危急！去大醫院</div>', unsafe_allow_html=True)
        rec_title = "建議前往：醫學中心 / 大型急診"
    elif level_color == "YELLOW":
        st.markdown('<div class="alert-banner bg-yellow">⚠️ 需看急診！盡快就醫</div>', unsafe_allow_html=True)
        rec_title = "建議前往：綜合醫院 / 急診"
    else:
        st.markdown('<div class="alert-banner bg-green">🟢 一般門診 / 多休息</div>', unsafe_allow_html=True)
        rec_title = "建議前往：附近診所 / 居家休養"

    st.markdown(f"### 您的狀況：{symptom}")
    st.write("---")

    st.markdown(f"### 📍 {rec_title}")
    
    if level_color == "GREEN":
        # 綠燈：Google Map 搜尋
        search_query = f"桃園市{district} 診所"
        # 使用 Google Map 搜尋模式
        map_link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(search_query)}"
        
        st.markdown(f"""
        <div class="hospital-card" style="border-left-color: #2e7d32;">
            <div class="hospital-name">🏡 附近的診所</div>
            <div style="font-size: 20px; color: #555;">
                您的狀況屬於輕症，建議前往附近的診所就醫，或在家多休息。<br>
            </div>
            <br>
            <a href="{map_link}" target="_blank" class="action-btn">🗺️ 點此搜尋附近診所</a>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        hospitals = find_nearest_hospitals(district, level_color)
        
        if not hospitals:
            st.warning(f"⚠️ {district} 附近無大型急救醫院，建議前往鄰近的大醫院：")
            hospitals = [h for h in TAOYUAN_HOSPITALS if h['level'] == 1]

        for h in hospitals:
            dist_tag = f"【{h['dist']}】" if h['dist'] != district else "【本區】"
            
            # 1. 導航連結 (FIXED)
            map_link = get_google_maps_link(h['addr'])
            
            # 2. 撥打連結 (FIXED: 移除 target='_blank' 避免手機瀏覽器阻擋)
            clean_tel = h['tel'].replace("-", "").replace(" ", "")
            
            st.markdown(f"""
            <div class="hospital-card">
                <div class="hospital-name">{dist_tag} {h['name']}</div>
                <div style="font-size: 20px; margin-bottom:10px;">
                    📞 電話：<a href="tel:{clean_tel}" style="text-decoration:none; color:#1a237e;">{h['tel']}</a><br>
                    🏥 地址：{h['addr']}
                </div>
                <a href="{map_link}" target="_blank" class="action-btn">🗺️ 導航出發</a>
                <a href="tel:{clean_tel}" class="action-btn phone-btn">📞 直接撥打</a>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")
    
    st.markdown("### 📋 現場該做什麼？")
    for step in sop_list:
        st.markdown(f'<div class="sop-text">{step}</div>', unsafe_allow_html=True)
        
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重選"):
            st.session_state['page'] = 'symptom_select'
            st.rerun()
    with col2:
        if st.button("🏠 回首頁"):
            st.session_state['page'] = 'home'
            st.rerun()

# ==========================================
# 5. 主程式入口
# ==========================================

if st.session_state['page'] == 'home':
    page_home()
elif st.session_state['page'] == 'symptom_select':
    page_symptom_select()
elif st.session_state['page'] == 'result':
    page_result()
