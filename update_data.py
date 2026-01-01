import requests
import json
import os
import time
import sys
import traceback
import random
import math
import re
from datetime import datetime, timedelta

# ==========================================
# 1. 基本設定
# ==========================================
EBIRD_API_KEY = '1mpok1sjosl5'
WIKI_CACHE = {}
START_TIME = time.time()

# 磁吸設定
SNAP_RADIUS_KM = 2.0  # 距離門檻
GEO_SEARCH_DIST_KM = 3 # 補漏網之魚的搜尋半徑

TAIWAN_COUNTIES = [
    'TW-TPE', 'TW-NWT', 'TW-KLU', 'TW-TYU', 'TW-HSQ', 'TW-HSZ', 'TW-MIA', 
    'TW-TXG', 'TW-CWH', 'TW-NTO', 'TW-YUL', 'TW-CHY', 'TW-CYI', 'TW-TNN', 
    'TW-KHH', 'TW-PIF', 'TW-ILA', 'TW-HUA', 'TW-TTT', 'TW-PEN', 'TW-KIN', 'TW-LIE'
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(BASE_DIR, 'static')
FILE_PATH = os.path.join(TARGET_DIR, 'birds_data.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'X-eBirdApiToken': EBIRD_API_KEY
}

# ==========================================
# 2. 🛡️ 手動修復資料庫 (針對死圖或常見鳥)
# ==========================================
MANUAL_FIX_DB = {
    "Pycnonotus sinensis": { "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Light-vented_Bulbul_%28Pycnonotus_sinensis%29.jpg/600px-Light-vented_Bulbul_%28Pycnonotus_sinensis%29.jpg", "desc": "白頭翁...常見留鳥。" },
    "Passer montanus": { "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Passer_montanus_4_%28Marek_Szczepanek%29.jpg/600px-Passer_montanus_4_%28Marek_Szczepanek%29.jpg", "desc": "麻雀...親近人類。" },
    "Columba livia": { "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Rock_Pigeon_Columba_livia.jpg/600px-Rock_Pigeon_Columba_livia.jpg", "desc": "原鴿...適應力強。" },
    "Streptopelia tranquebarica": { "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Red_Turtle_Dove_Show_Love.jpg/600px-Red_Turtle_Dove_Show_Love.jpg", "desc": "紅鳩...體型嬌小。" },
    "Spilopelia chinensis": { "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Spotted_Dove_-_Mata_Ayer.jpg/600px-Spotted_Dove_-_Mata_Ayer.jpg", "desc": "珠頸斑鳩...頸部珍珠斑點。" },
    "Aythya fuligula": { "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Aythya_fuligula_3_%28Marek_Szczepanek%29.jpg/600px-Aythya_fuligula_3_%28Marek_Szczepanek%29.jpg", "desc": "鳳頭潛鴨...冬季常見候鳥。" }
}

# ==========================================
# 3. 🌟 完整全台熱點資料 (V13.3 座標校正版 + 關鍵字)
# ==========================================
# 注意：這裡加入了 'keywords' 欄位，用於新的智慧磁吸判斷
HOT_SPOTS_DATA = {
    "台北市": [
        {"name": "關渡自然公園", "lat": 25.1163, "lng": 121.4725, "keywords": ["關渡", "Guandu"], "desc": "台北市最重要的水鳥保育區...", "potential": [{"name": "花嘴鴨", "sci": "Anas zonorhyncha"}]},
        {"name": "大安森林公園", "lat": 25.0326, "lng": 121.5345, "keywords": ["大安森林", "Daan"], "desc": "都市之肺...", "potential": [{"name": "五色鳥", "sci": "Psilopogon nuchalis"}]},
        {"name": "植物園", "lat": 25.0335, "lng": 121.5095, "keywords": ["植物園", "Botanical"], "desc": "歷史悠久...", "potential": [{"name": "翠鳥", "sci": "Alcedo atthis"}]},
        {"name": "大湖公園", "lat": 25.0841, "lng": 121.6026, "keywords": ["大湖", "Dahu"], "desc": "內湖區著名的湖泊公園...", "potential": [{"name":"大白鷺", "sci":"Ardea alba"}]},
        {"name": "松山文創園區", "lat": 25.0438, "lng": 121.5606, "keywords": ["松山文創", "Songshan"], "desc": "信義區的生態跳島...", "potential": [{"name":"翠鳥", "sci":"Alcedo atthis"}]},
        {"name": "芝山岩", "lat": 25.1038, "lng": 121.5305, "keywords": ["芝山", "Zhishan"], "desc": "隆起的珊瑚礁地形...", "potential": [{"name": "領角鴞", "sci": "Otus lettia"}]}
    ],
    "新北市": [
        {"name": "金山清水濕地", "lat": 25.2285, "lng": 121.6285, "keywords": ["金山", "Jinshan", "清水"], "desc": "北海岸著名的候鳥驛站...", "potential": [{"name": "黑鳶", "sci": "Milvus migrans"}]},
        {"name": "萬里野柳地質公園", "lat": 25.2065, "lng": 121.6925, "keywords": ["野柳", "Yehliu"], "desc": "突出海岬地形...", "potential": [{"name": "藍磯鶇", "sci": "Monticola solitarius"}]},
        {"name": "田寮洋", "lat": 25.0185, "lng": 121.9385, "keywords": ["田寮洋", "Tianliao"], "desc": "位於貢寮的隱密濕地...", "potential": [{"name": "魚鷹", "sci": "Pandion haliaetus"}]},
        {"name": "烏來福山", "lat": 24.7855, "lng": 121.5055, "keywords": ["烏來", "福山", "Wulai"], "desc": "低海拔闊葉林代表...", "potential": [{"name": "鉛色水鶇", "sci": "Phoenicurus fuliginosus"}]}
    ],
    "桃園市": [
        {"name": "許厝港濕地", "lat": 25.0865, "lng": 121.1855, "keywords": ["許厝港", "Xucuo"], "desc": "國家級重要濕地...", "potential": [{"name": "唐白鷺", "sci": "Egretta eulophotes"}]},
        {"name": "大園水田", "lat": 25.0685, "lng": 121.2085, "keywords": ["大園", "Dayuan"], "desc": "廣大的水田區...", "potential": [{"name": "小青足鷸", "sci": "Tringa stagnatilis"}]}
    ],
    "新竹市": [
        {"name": "金城湖賞鳥區", "lat": 24.8105, "lng": 120.9035, "keywords": ["金城湖", "Jincheng"], "desc": "香山濕地北端的淡水湖泊...", "potential": [{"name": "高蹺鴴", "sci": "Himantopus himantopus"}]},
        {"name": "香山濕地", "lat": 24.7755, "lng": 120.9125, "keywords": ["香山", "Siangshan"], "desc": "廣達1700公頃的泥質灘地...", "potential": [{"name": "大杓鷸", "sci": "Numenius arquata"}]}
    ],
    "苗栗縣": [
        {"name": "通霄海水浴場", "lat": 24.4985, "lng": 120.6755, "keywords": ["通霄", "Tongxiao"], "desc": "包含周邊防風林與海岸線...", "potential": [{"name": "戴勝", "sci": "Upupa epops"}]}
    ],
    "台中市": [
        {"name": "高美濕地", "lat": 24.3125, "lng": 120.5495, "keywords": ["高美", "Gaomei"], "desc": "著名的雲林莞草區...", "potential": [{"name": "黑嘴鷗", "sci": "Saundersilarus saundersi"}]},
        {"name": "大雪山林道 23.5K", "lat": 24.2385, "lng": 120.9385, "keywords": ["大雪山", "Dasyueshan", "23K", "23.5K"], "desc": "國際級賞鳥熱點...", "potential": [{"name": "藍腹鷴", "sci": "Lophura swinhoii"}]},
        {"name": "大雪山林道 50K", "lat": 24.2755, "lng": 121.0085, "keywords": ["大雪山", "Dasyueshan", "50K", "天池"], "desc": "高海拔針葉林區...", "potential": [{"name": "帝雉", "sci": "Syrmaticus mikado"}]}
    ],
    "南投縣": [
        {"name": "合歡山", "lat": 24.1385, "lng": 121.2755, "keywords": ["合歡山", "Hehuan"], "desc": "台灣公路最高點...", "potential": [{"name": "岩鷚", "sci": "Prunella collaris"}]},
        {"name": "塔塔加", "lat": 23.4875, "lng": 120.8845, "keywords": ["塔塔加", "Tataka"], "desc": "玉山國家公園西北園區...", "potential": [{"name": "星鴉", "sci": "Nucifraga caryocatactes"}]}
    ],
    "彰化縣": [
        {"name": "福寶濕地", "lat": 24.0355, "lng": 120.3655, "keywords": ["福寶", "Fubao", "漢寶"], "desc": "彰化沿海重要的漢寶/福寶濕地群...", "potential": [{"name": "彩鷸", "sci": "Rostratula benghalensis"}]}
    ],
    "雲林縣": [
        {"name": "湖本村", "lat": 23.6885, "lng": 120.6185, "keywords": ["湖本", "Huben", "八色鳥"], "desc": "以八色鳥繁殖地聞名...", "potential": [{"name": "八色鳥", "sci": "Pitta nympha"}]},
        {"name": "成龍濕地", "lat": 23.5555, "lng": 120.1655, "keywords": ["成龍", "Chenglong"], "desc": "地層下陷形成的濕地...", "potential": [{"name": "赤頸鴨", "sci": "Mareca penelope"}]}
    ],
    "嘉義縣": [
        {"name": "鰲鼓濕地", "lat": 23.5045, "lng": 120.1385, "keywords": ["鰲鼓", "Aogu"], "desc": "台灣最大的人工濕地...", "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}]},
        {"name": "阿里山沼平公園", "lat": 23.5135, "lng": 120.8085, "keywords": ["阿里山", "Alishan", "沼平"], "desc": "觀賞中高海拔鳥類...", "potential": [{"name": "栗背林鴝", "sci": "Tarsiger johnstoniae"}]}
    ],
    "台南市": [
        {"name": "七股黑面琵鷺保護區", "lat": 23.0465, "lng": 120.0685, "keywords": ["七股", "Qigu", "黑面琵鷺"], "desc": "全球黑面琵鷺度冬數量最多的區域...", "potential": [{"name": "黑面琵鷺", "sci": "Platalea minor"}]},
        {"name": "官田水雉園區", "lat": 23.1785, "lng": 120.3155, "keywords": ["官田", "Guantian", "水雉"], "desc": "凌波仙子—水雉的主要復育地...", "potential": [{"name": "水雉", "sci": "Hydrophasianus chirurgus"}]}
    ],
    "高雄市": [
        {"name": "茄萣濕地", "lat": 22.8955, "lng": 120.1855, "keywords": ["茄萣", "Qieding"], "desc": "原為鹽田，現為水鳥保護區...", "potential": [{"name": "黑面琵鷺", "sci": "Platalea minor"}]},
        {"name": "中寮山", "lat": 22.8255, "lng": 120.4185, "keywords": ["中寮山", "Zhongliao"], "desc": "南部著名的猛禽觀賞點...", "potential": [{"name": "灰面鵟鷹", "sci": "Butastur indicus"}]}
    ],
    "屏東縣": [
        {"name": "龍鑾潭自然中心", "lat": 21.9855, "lng": 120.7455, "keywords": ["龍鑾潭", "Longluan"], "desc": "南台灣最大的淡水湖泊...", "potential": [{"name": "鳳頭潛鴨", "sci": "Aythya fuligula"}]},
        {"name": "社頂自然公園", "lat": 21.9565, "lng": 120.8255, "keywords": ["社頂", "Sheding", "墾丁", "Kenting"], "desc": "恆春半島特有的珊瑚礁林地形...", "potential": [{"name": "赤腹鷹", "sci": "Accipiter soloensis"}]}
    ],
    "宜蘭縣": [
        # ✅ 修正座標：使用您指定的無尾港核心區 (24.6153, 121.8557)
        {"name": "無尾港水鳥保護區", "lat": 24.6153, "lng": 121.8557, "keywords": ["無尾港", "Wuwei"], "desc": "位於蘇澳的國家級重要濕地，核心賞鳥平台...", "potential": [{"name": "小水鴨", "sci": "Anas crecca"}]},
        {"name": "五十二甲濕地", "lat": 24.6655, "lng": 121.8225, "keywords": ["五十二甲", "52jia"], "desc": "原始的蘆葦草澤濕地...", "potential": [{"name": "黑頸鸊鷉", "sci": "Podiceps nigricollis"}]},
        {"name": "壯圍沙丘", "lat": 24.7585, "lng": 121.8085, "keywords": ["壯圍", "Zhuangwei", "蘭陽溪"], "desc": "蘭陽溪口南岸的廣闊沙丘...", "potential": [{"name": "小燕鷗", "sci": "Sternula albifrons"}]},
        {"name": "太平山", "lat": 24.4955, "lng": 121.5355, "keywords": ["太平山", "Taipingshan"], "desc": "潮濕多霧的中高海拔森林...", "potential": [{"name": "金翼白眉", "sci": "Garrulax morrisonianus"}]}
    ],
    "花蓮縣": [
        {"name": "布洛灣", "lat": 24.1725, "lng": 121.5755, "keywords": ["布洛灣", "Bulowan", "太魯閣"], "desc": "太魯閣國家公園內的台地...", "potential": [{"name": "黃山雀", "sci": "Machlolophus holsti"}]}
    ],
    "台東縣": [
        {"name": "知本濕地", "lat": 22.6855, "lng": 121.0555, "keywords": ["知本", "Zhiben"], "desc": "台東市近郊的河口濕地...", "potential": [{"name": "環頸雉", "sci": "Phasianus colchicus"}]}
    ],
    "金門縣": [
        {"name": "慈湖", "lat": 24.4555, "lng": 118.3055, "keywords": ["慈湖", "Cihu"], "desc": "金門最大的鹹水湖...", "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}]},
        {"name": "青年農莊", "lat": 24.4655, "lng": 118.4355, "keywords": ["青年農莊", "Youth Farm"], "desc": "位於金門東半島...", "potential": [{"name": "栗喉蜂虎", "sci": "Merops philippinus"}]}
    ],
    "連江縣": [
        {"name": "馬祖東引北海坑道", "lat": 26.3755, "lng": 120.4855, "keywords": ["東引", "Dongyin", "北海坑道"], "desc": "地形險峻的岩岸...", "potential": [{"name": "黑嘴端鳳頭燕鷗", "sci": "Thalasseus bernsteini"}]},
        {"name": "南竿介壽菜園", "lat": 26.1539, "lng": 119.9497, "keywords": ["南竿", "Nangan", "介壽", "菜園"], "desc": "位於縣政府前方的蔬菜公園...", "potential": [{"name": "田鵐", "sci": "Emberiza rustica"}]}
    ]
}

# ==========================================
# 4. 工具函式
# ==========================================

def format_obs_date(date_str):
    try:
        if len(date_str) > 10:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            return dt.strftime("%m/%d %H:%M")
        return date_str
    except:
        return date_str

def calculate_distance(lat1, lng1, lat2, lng2):
    """計算兩點經緯度的距離 (單位: 公里)"""
    try:
        R = 6371  # 地球半徑
        dLat = math.radians(lat2 - lat1)
        dLng = math.radians(lng2 - lng1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLng/2) * math.sin(dLng/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except:
        return 9999

def get_wiki_data(sci_name, common_name):
    """ 
    V12.1: 優先檢查 Manual Fix DB，再查 Wiki API 
    """
    # 1. 優先查手動修復庫
    if common_name in MANUAL_FIX_DB:
        return MANUAL_FIX_DB[common_name], True

    # 2. 查快取
    if sci_name in WIKI_CACHE: return WIKI_CACHE[sci_name], True

    search_queries = [sci_name, common_name, f"{common_name} (鳥類)"]

    for query in search_queries:
        if not query: continue
        try:
            time.sleep(random.uniform(0.1, 0.3))
            params = {
                "action": "query", "format": "json", "prop": "pageimages|extracts",
                "titles": query, "pithumbsize": 400, 
                "exintro": True, "explaintext": True, 
                "variant": "zh-tw", "redirects": 1
            }
            resp = requests.get("https://zh.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=5).json()
            pages = resp.get("query", {}).get("pages", {})
            for k, v in pages.items():
                if k != "-1":
                    raw_desc = v.get("extract", "")
                    
                    # 清除 (學名...) 或 （...）
                    clean_desc = re.sub(r'[\(（].*?[\)）]', '', raw_desc)
                    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

                    # 限制 200 字 + 找句號
                    limit = 200
                    if len(clean_desc) > limit:
                        short_desc = clean_desc[:limit]
                        last_period = max(short_desc.rfind('。'), short_desc.rfind('！'))
                        
                        if last_period != -1:
                            final_desc = short_desc[:last_period+1]
                        else:
                            final_desc = short_desc + "..." 
                    else:
                        final_desc = clean_desc

                    if len(final_desc) < 10: continue 

                    data = {
                        "img": v.get("thumbnail", {}).get("source", ""),
                        "desc": final_desc
                    }
                    WIKI_CACHE[sci_name] = data
                    return data, False
        except Exception as e:
            pass
            
    empty = {"img": "", "desc": "暫無詳細介紹"}
    WIKI_CACHE[sci_name] = empty
    return empty, False

def get_ebird_data_by_geo(lat, lng):
    """ 針對熱點座標進行半徑搜尋 """
    try:
        url = f"https://api.ebird.org/v2/data/obs/geo/recent?lat={lat}&lng={lng}&dist={GEO_SEARCH_DIST_KM}&back=21&maxResults=2000&sppLocale=zh-TW"
        r = requests.get(url, headers={'X-eBirdApiToken': EBIRD_API_KEY}, timeout=20)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []

# 封裝 print 以避免 Windows 編碼錯誤
def safe_print(msg):
    try:
        print(msg)
    except:
        pass

# ==========================================
# 5. 主程式
# ==========================================
def main():
    if not os.path.exists(TARGET_DIR): os.makedirs(TARGET_DIR)
    
    # 載入舊快取
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                if 'hotspots' in old_data:
                    for city, spots in old_data['hotspots'].items():
                        for spot in spots:
                            for p in spot.get('potential', []):
                                if p.get('sci') and p.get('wikiImg'):
                                    WIKI_CACHE[p['sci']] = {'img': p.get('wikiImg', ''), 'desc': p.get('wikiDesc', '')}
                if 'recent' in old_data and isinstance(old_data['recent'], list):
                    for b in old_data['recent']:
                        if b.get('sciName') and b.get('wikiImg'):
                            WIKI_CACHE[b['sciName']] = {'img': b.get('wikiImg', ''), 'desc': b.get('wikiDesc', '')}
                safe_print(f"📦 已載入 {len(WIKI_CACHE)} 筆舊圖檔快取")
        except: pass

    safe_print(f"\n🚀 [1/3] 啟動全台鳥況更新 (V13.3 穩定版)...")
    
    all_unique_birds = {} 
    start_time = time.time()

    # --- 階段一：縣市大範圍掃描 ---
    safe_print("   👉 階段一：縣市廣域掃描 (County Scan)")
    for code in TAIWAN_COUNTIES:
        try:
            url = f"https://api.ebird.org/v2/data/obs/{code}/recent?back=21&maxResults=2000&detail=full&sppLocale=zh-TW"
            r = requests.get(url, headers={'X-eBirdApiToken': EBIRD_API_KEY}, timeout=20)
            if r.status_code == 200:
                obs_list = r.json()
                count = 0
                for obs in obs_list:
                    key = f"{obs.get('subId')}_{obs.get('speciesCode')}"
                    if key not in all_unique_birds:
                        all_unique_birds[key] = obs
                        all_unique_birds[key]['_source_county'] = code 
                        count += 1
                safe_print(f"      - {code}: 獲得 {count} 筆")
            time.sleep(0.5)
        except: pass

    # --- 階段二：熱點定點打擊 ---
    safe_print("\n   👉 階段二：熱點定點打擊 (Hotspot Geo-Targeting)")
    hotspot_list = []
    for city, spots in HOT_SPOTS_DATA.items():
        for spot in spots:
            hotspot_list.append(spot)
    
    total_hotspots = len(hotspot_list)
    for i, spot in enumerate(hotspot_list):
        # 簡單進度顯示
        if i % 10 == 0:
            safe_print(f"      - 掃描進度: {i}/{total_hotspots}")
        
        geo_birds = get_ebird_data_by_geo(spot['lat'], spot['lng'])
        
        for obs in geo_birds:
            key = f"{obs.get('subId')}_{obs.get('speciesCode')}"
            if key not in all_unique_birds:
                all_unique_birds[key] = obs
                all_unique_birds[key]['_source_county'] = 'GEO_ADDED' 
            
        time.sleep(0.2) 

    # --- 階段三：智慧磁吸與資料處理 ---
    safe_print(f"\n🚀 [2/3] 正在處理 {len(all_unique_birds)} 筆資料 (智慧磁吸 + Wiki)...")
    
    final_bird_list = []
    
    flat_hotspots = []
    for city, spots in HOT_SPOTS_DATA.items():
        for s in spots:
            flat_hotspots.append(s)

    processed_count = 0
    for key, obs in all_unique_birds.items():
        processed_count += 1
        if processed_count % 200 == 0:
            safe_print(f"      進度: {processed_count}/{len(all_unique_birds)}")

        lat = obs.get('lat')
        lng = obs.get('lng')
        locName = obs.get('locName', '') # 確保有字串
        
        # 預設：保留原資料
        final_lat = lat
        final_lng = lng
        final_locName = locName
        
        # 🌟 智慧磁吸邏輯 V2 (Smart Snap)
        # 條件 1: 距離熱點 < SNAP_RADIUS_KM (2.0)
        # 條件 2: 地點名稱 (locName) 包含 熱點關鍵字
        
        best_match_spot = None
        min_dist = SNAP_RADIUS_KM
        
        for spot in flat_hotspots:
            dist = calculate_distance(lat, lng, spot['lat'], spot['lng'])
            
            if dist <= SNAP_RADIUS_KM:
                # 檢查關鍵字匹配
                is_name_match = False
                
                # A. 檢查熱點全名
                if spot['name'] in locName:
                    is_name_match = True
                
                # B. 檢查關鍵字列表 (如果有設定)
                if not is_name_match and 'keywords' in spot:
                    for kw in spot['keywords']:
                        if kw in locName:
                            is_name_match = True
                            break
                
                # 只有當「距離夠近」且「名稱相關」才吸附
                if is_name_match:
                    if dist < min_dist:
                        min_dist = dist
                        best_match_spot = spot

        if best_match_spot:
            final_lat = best_match_spot['lat']
            final_lng = best_match_spot['lng']
            final_locName = best_match_spot['name'] # 統一使用熱點標準名稱

        # 抓 Wiki
        wiki, is_cache = get_wiki_data(obs.get('sciName'), obs.get('comName'))
        fmt_date = format_obs_date(obs.get('obsDt'))

        final_bird_list.append({
            'id': obs.get('subId'),
            'name': obs.get('comName'),
            'sciName': obs.get('sciName'),
            'locName': final_locName,
            'lat': final_lat,
            'lng': final_lng,
            'date': fmt_date,
            'speciesCode': obs.get('speciesCode'),
            'county': obs.get('_source_county', 'UNKNOWN'),
            'wikiImg': wiki['img'],
            'wikiDesc': wiki['desc']
        })

    safe_print(f"\n🚀 [3/3] 存檔中...")
    
    tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    final_json = {
        "update_at": tw_time,
        "recent": final_bird_list,
        "hotspots": HOT_SPOTS_DATA
    }
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
    
    total_time = time.time() - start_time
    safe_print(f"\n🎉 V13.3 更新完成！")
    safe_print(f"   - 總資料筆數: {len(final_bird_list)}")
    safe_print(f"   - 總耗時: {total_time:.1f} 秒")
    safe_print(f"   - 時間: {tw_time}")

if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()
