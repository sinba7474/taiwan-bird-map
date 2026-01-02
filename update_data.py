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
# 1. 系統設定
# ==========================================
EBIRD_API_KEY = '1mpok1sjosl5'
WIKI_CACHE = {} 
START_TIME = time.time()

# 磁吸設定
SNAP_RADIUS_KM = 2.0
GEO_SEARCH_DIST_KM = 3

# 檔案路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(BASE_DIR, 'static')
FILE_PATH = os.path.join(TARGET_DIR, 'birds_data.json')

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

TAIWAN_COUNTIES = [
    'TW-TPE', 'TW-NWT', 'TW-KLU', 'TW-TYU', 'TW-HSQ', 'TW-HSZ', 'TW-MIA', 
    'TW-TXG', 'TW-CWH', 'TW-NTO', 'TW-YUL', 'TW-CHY', 'TW-CYI', 'TW-TNN', 
    'TW-KHH', 'TW-PIF', 'TW-ILA', 'TW-HUA', 'TW-TTT', 'TW-PEN', 'TW-KIN', 'TW-LIE'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TaiwanBirdMap/15.4',
    'X-eBirdApiToken': EBIRD_API_KEY
}

# ==========================================
# 2. 🛡️ 手動圖鑑庫 (生態習性優化 + 繁體中文)
# ==========================================
MANUAL_FIX_DB = {
    "Anas zonorhyncha": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Spot-billed_Duck.jpg/600px-Spot-billed_Duck.jpg",
        "desc": "花嘴鴨（普遍留鳥）。【生態習性】台灣唯一的留鳥鴨科，特徵是黑色嘴喙前端有鮮明的黃色斑塊。常成對或小群出現於濕地、水田及河口。主食水生植物的種子與嫩葉，也會吃螺類。"
    },
    "Pycnonotus sinensis": { 
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Light-vented_Bulbul_%28Pycnonotus_sinensis%29.jpg/600px-Light-vented_Bulbul_%28Pycnonotus_sinensis%29.jpg", 
        "desc": "白頭翁（普遍留鳥）。【生態習性】頭頂後方有白色羽毛是其特徵。廣泛分布於平地至低海拔山區，適應力極強。常成群在城市公園喧鬧活動，雜食性，喜食漿果與昆蟲。" 
    },
    "Passer montanus": { 
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Passer_montanus_4_%28Marek_Szczepanek%29.jpg/600px-Passer_montanus_4_%28Marek_Szczepanek%29.jpg", 
        "desc": "麻雀（普遍留鳥）。【生態習性】最親近人類的鳥類，臉頰上有明顯的黑斑。常在地面跳躍覓食草籽與穀物。晚上有集體停棲在樹上或屋簷喧鬧的習慣。" 
    },
    "Columba livia": { 
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Rock_Pigeon_Columba_livia.jpg/600px-Rock_Pigeon_Columba_livia.jpg", 
        "desc": "原鴿（野鴿）。【生態習性】源自歐洲，現已成為全球都市常見鳥類。群聚性強，喜歡在廣場、公園地面覓食。築巢於建築物孔隙，對人類警戒心低。" 
    },
    "Streptopelia tranquebarica": { 
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/Red_Turtle_Dove_Show_Love.jpg/600px-Red_Turtle_Dove_Show_Love.jpg", 
        "desc": "紅鳩（普遍留鳥）。【生態習性】台灣最小型的鳩鴿科。雄鳥背部紅褐色，頸後有黑色頸環。常成群在農田、電線上休息。飛行速度快，翅膀拍擊聲明顯。" 
    },
    "Spilopelia chinensis": { 
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Spotted_Dove_-_Mata_Ayer.jpg/600px-Spotted_Dove_-_Mata_Ayer.jpg", 
        "desc": "珠頸斑鳩（普遍留鳥）。【生態習性】後頸有布滿白點的黑色頸環，宛如珍珠項鍊。適應城鄉環境，叫聲為低沉的「咕-咕-咕」。求偶時會頻頻點頭。" 
    },
    "Aythya fuligula": { 
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Aythya_fuligula_3_%28Marek_Szczepanek%29.jpg/600px-Aythya_fuligula_3_%28Marek_Szczepanek%29.jpg", 
        "desc": "鳳頭潛鴨（冬候鳥）。【生態習性】雄鳥頭部有下垂冠羽，腹部白色。善於潛水，常在開闊深水域活動。白天多在水面休息，晨昏時潛水捕食魚蝦及軟體動物。" 
    },
    "Egretta garzetta": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Egretta_garzetta_2_-_1.jpg/600px-Egretta_garzetta_2_-_1.jpg",
        "desc": "小白鷺（普遍留鳥）。【生態習性】全身白色，嘴黑色，腳趾為黃色（黃襪子）。常在水田、溪流、河口單獨活動。會用腳擾動水底逼出魚蝦後啄食。" 
    },
    "Gorsachius melanolophus": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Malayan_Night-Heron_-_Taiwan_S4E8695_%2817320173361%29.jpg/500px-Malayan_Night-Heron_-_Taiwan_S4E8695_%2817320173361%29.jpg",
        "desc": "黑冠麻鷺（留鳥）。【生態習性】常在都會公園草地上緩慢行走，捕食蚯蚓。受驚嚇時會伸長脖子擬態成樹枝。近年來適應都市環境，數量大增。"
    },
    "Milvus migrans": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Black_Kite_in_flight_1.jpg/600px-Black_Kite_in_flight_1.jpg",
        "desc": "黑鳶（老鷹）。【生態習性】台灣最常見的猛禽，尾羽呈魚尾狀（剪刀尾）。常在港口或水域上方盤旋，撿食水面死魚或動物內臟。基隆港是著名觀賞點。"
    },
    "Urocissa caerulea": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Formosan_Magpie_2.jpg/600px-Formosan_Magpie_2.jpg",
        "desc": "台灣藍鵲（特有種）。【生態習性】俗稱長尾山娘，身體藍色，嘴腳紅色。具有強烈的護巢行為與群居性。常成小群在低海拔樹林間排隊飛行。"
    },
    "Megalaima nuchalis": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Megalaima_nuchalis.jpg/600px-Megalaima_nuchalis.jpg",
        "desc": "五色鳥（特有種）。【生態習性】身披五彩羽毛，叫聲像敲木魚「郭、郭、郭」。喜歡在枯木上啄洞築巢，廣泛分布於平地至中海拔森林與公園。"
    }
}

# ==========================================
# 3. 🌟 完整全台熱點資料 (V15.4 完整展開版)
# ==========================================
# 包含 22 縣市，超過 135 個熱點，地毯式覆蓋
HOT_SPOTS_DATA = {
    "基隆市": [
        {"name": "基隆港 (海洋廣場)", "lat": 25.1315, "lng": 121.7405, "keywords": ["基隆港", "Keelung Port", "海洋廣場"], "desc": "黑鳶密集區", "potential": []},
        {"name": "和平島公園", "lat": 25.1605, "lng": 121.7635, "keywords": ["和平島", "Heping Island"], "desc": "海蝕地形與岩鷺", "potential": []},
        {"name": "潮境公園", "lat": 25.1425, "lng": 121.8025, "keywords": ["潮境", "Chaojing"], "desc": "海岸鳥類與藍磯鶇", "potential": []},
        {"name": "八斗子漁港", "lat": 25.1405, "lng": 121.7925, "keywords": ["八斗子", "Badouzi"], "desc": "冬季避風港", "potential": []},
        {"name": "情人湖公園", "lat": 25.1505, "lng": 121.7105, "keywords": ["情人湖", "Lovers Lake"], "desc": "山區湖泊生態", "potential": []},
        {"name": "大武崙砲台", "lat": 25.1585, "lng": 121.7155, "keywords": ["大武崙", "Dawulun"], "desc": "過境猛禽制高點", "potential": []}
    ],
    "台北市": [
        {"name": "關渡自然公園", "lat": 25.1163, "lng": 121.4725, "keywords": ["關渡", "Guandu"], "desc": "核心保育區，水鳥眾多", "potential": []},
        {"name": "大安森林公園", "lat": 25.0326, "lng": 121.5345, "keywords": ["大安森林", "Daan"], "desc": "都市之肺，五色鳥繁殖", "potential": []},
        {"name": "植物園", "lat": 25.0335, "lng": 121.5095, "keywords": ["植物園", "Botanical"], "desc": "翠鳥與鳳頭蒼鷹", "potential": []},
        {"name": "大湖公園", "lat": 25.0841, "lng": 121.6026, "keywords": ["大湖", "Dahu"], "desc": "鷺科聚集地", "potential": []},
        {"name": "華江雁鴨自然公園", "lat": 25.0285, "lng": 121.4915, "keywords": ["華江", "Huajiang"], "desc": "冬季小水鴨聖地", "potential": []},
        {"name": "陽明山二子坪", "lat": 25.1855, "lng": 121.5245, "keywords": ["陽明山", "Yangmingshan", "二子坪"], "desc": "台灣藍鵲與竹雞", "potential": []},
        {"name": "台大校園", "lat": 25.0175, "lng": 121.5395, "keywords": ["台大", "NTU", "台灣大學"], "desc": "黑冠麻鷺與領角鴞", "potential": []},
        {"name": "芝山岩", "lat": 25.1038, "lng": 121.5305, "keywords": ["芝山", "Zhishan"], "desc": "老樹與猛禽", "potential": []},
        {"name": "南港公園", "lat": 25.0405, "lng": 121.5855, "keywords": ["南港公園", "Nangang Park"], "desc": "埤塘生態與翠鳥", "potential": []}
    ],
    "新北市": [
        {"name": "金山清水濕地", "lat": 25.2285, "lng": 121.6285, "keywords": ["金山", "Jinshan", "清水"], "desc": "候鳥重要驛站", "potential": []},
        {"name": "萬里野柳地質公園", "lat": 25.2065, "lng": 121.6925, "keywords": ["野柳", "Yehliu"], "desc": "過境鳥聖地", "potential": []},
        {"name": "田寮洋", "lat": 25.0185, "lng": 121.9385, "keywords": ["田寮洋", "Tianliao"], "desc": "貢寮濕地與猛禽", "potential": []},
        {"name": "烏來福山", "lat": 24.7855, "lng": 121.5055, "keywords": ["烏來", "福山", "Wulai"], "desc": "低海拔溪流與林鳥", "potential": []},
        {"name": "五股濕地", "lat": 25.0955, "lng": 121.4555, "keywords": ["五股", "Wugu"], "desc": "夏季燕群聚集", "potential": []},
        {"name": "新店廣興", "lat": 24.9355, "lng": 121.5555, "keywords": ["廣興", "Guangxing"], "desc": "魚鷹捕魚熱點", "potential": []},
        {"name": "淡水金色水岸", "lat": 25.1685, "lng": 121.4425, "keywords": ["淡水", "Tamsui", "金色水岸"], "desc": "河口磯鷸與鷺科", "potential": []},
        {"name": "挖子尾自然保留區", "lat": 25.1585, "lng": 121.4155, "keywords": ["挖子尾", "Waziwei"], "desc": "紅樹林與唐白鷺", "potential": []},
        {"name": "鹿角溪人工濕地", "lat": 24.9655, "lng": 121.4155, "keywords": ["鹿角溪", "Lujiao"], "desc": "紅冠水雞繁殖", "potential": []}
    ],
    "桃園市": [
        {"name": "許厝港濕地", "lat": 25.0865, "lng": 121.1855, "keywords": ["許厝港", "Xucuo"], "desc": "國家級重要濕地", "potential": []},
        {"name": "大園水田", "lat": 25.0685, "lng": 121.2085, "keywords": ["大園", "Dayuan"], "desc": "鷸鴴科水鳥", "potential": []},
        {"name": "八德埤塘自然生態公園", "lat": 24.9455, "lng": 121.3055, "keywords": ["八德", "Bade", "埤塘"], "desc": "鴛鴦與水禽", "potential": []},
        {"name": "石門水庫", "lat": 24.8155, "lng": 121.2455, "keywords": ["石門水庫", "Shimen"], "desc": "山林鳥類", "potential": []},
        {"name": "龍潭大池", "lat": 24.8655, "lng": 121.2155, "keywords": ["龍潭", "Longtan"], "desc": "雁鴨科度冬", "potential": []},
        {"name": "大溪河濱公園", "lat": 24.8955, "lng": 121.2855, "keywords": ["大溪", "Daxi"], "desc": "落羽松與河岸鳥類", "potential": []}
    ],
    "新竹市": [
        {"name": "金城湖賞鳥區", "lat": 24.8105, "lng": 120.9035, "keywords": ["金城湖", "Jincheng"], "desc": "高蹺鴴聚集地", "potential": []},
        {"name": "香山濕地", "lat": 24.7755, "lng": 120.9125, "keywords": ["香山", "Siangshan"], "desc": "大杓鷸與泥灘地", "potential": []},
        {"name": "新竹南寮漁港", "lat": 24.8485, "lng": 120.9255, "keywords": ["南寮", "Nanliao", "漁港"], "desc": "鷗科與海鳥", "potential": []},
        {"name": "十八尖山", "lat": 24.7955, "lng": 120.9855, "keywords": ["十八尖山", "18 Peaks"], "desc": "低海拔林鳥", "potential": []},
        {"name": "鳳山溪口", "lat": 24.8655, "lng": 120.9155, "keywords": ["鳳山溪", "Fengshan"], "desc": "河口大型水鳥", "potential": []}
    ],
    "新竹縣": [
        {"name": "新豐紅樹林", "lat": 24.9125, "lng": 120.9705, "keywords": ["新豐", "Xinfeng", "紅樹林"], "desc": "水筆仔生態", "potential": []},
        {"name": "頭前溪豆腐岩", "lat": 24.8155, "lng": 121.0155, "keywords": ["頭前溪", "Touqian", "豆腐岩"], "desc": "河床鶺鴒科", "potential": []},
        {"name": "司馬庫斯", "lat": 24.5785, "lng": 121.3355, "keywords": ["司馬庫斯", "Smangus"], "desc": "中高海拔特有種", "potential": []},
        {"name": "峨眉湖", "lat": 24.6755, "lng": 120.9855, "keywords": ["峨眉湖", "Emei"], "desc": "鸕鶿與魚鷹", "potential": []},
        {"name": "觀霧國家森林", "lat": 24.5055, "lng": 121.1155, "keywords": ["觀霧", "Guanwu"], "desc": "帝雉與黃山雀", "potential": []}
    ],
    "苗栗縣": [
        {"name": "通霄海水浴場", "lat": 24.4985, "lng": 120.6755, "keywords": ["通霄", "Tongxiao"], "desc": "海岸防風林", "potential": []},
        {"name": "雪見遊憩區", "lat": 24.4255, "lng": 121.0155, "keywords": ["雪見", "Xuejian"], "desc": "中海拔林道", "potential": []},
        {"name": "後龍溪口", "lat": 24.6155, "lng": 120.7555, "keywords": ["後龍", "Houlong"], "desc": "河口濕地", "potential": []},
        {"name": "鯉魚潭水庫", "lat": 24.3355, "lng": 120.7755, "keywords": ["鯉魚潭", "Liyutan"], "desc": "猛禽與水鳥", "potential": []},
        {"name": "龍鳳漁港", "lat": 24.6985, "lng": 120.8585, "keywords": ["龍鳳", "Longfeng"], "desc": "過境鳥驚喜", "potential": []},
        {"name": "挑炭古道", "lat": 24.3985, "lng": 120.7855, "keywords": ["挑炭", "Taotan"], "desc": "桐花季賞鳥", "potential": []}
    ],
    "台中市": [
        {"name": "高美濕地", "lat": 24.3125, "lng": 120.5495, "keywords": ["高美", "Gaomei"], "desc": "黑嘴鷗與莞草", "potential": []},
        {"name": "大雪山林道 23.5K", "lat": 24.2385, "lng": 120.9385, "keywords": ["大雪山", "Dasyueshan", "23K", "23.5K"], "desc": "藍腹鷴熱點", "potential": []},
        {"name": "大雪山林道 50K", "lat": 24.2755, "lng": 121.0085, "keywords": ["大雪山", "Dasyueshan", "50K", "天池"], "desc": "帝雉熱點", "potential": []},
        {"name": "台中都會公園", "lat": 24.2055, "lng": 120.5955, "keywords": ["都會公園", "Metropolitan Park"], "desc": "大肚台地平原鳥", "potential": []},
        {"name": "旱溪", "lat": 24.1255, "lng": 120.7055, "keywords": ["旱溪", "Hanxi"], "desc": "市區溪流生態", "potential": []},
        {"name": "武陵農場", "lat": 24.3655, "lng": 121.3155, "keywords": ["武陵", "Wuling"], "desc": "櫻花鉤吻鮭與鉛色水鶇", "potential": []},
        {"name": "大肚溪口野生動物保護區", "lat": 24.1985, "lng": 120.4855, "keywords": ["大肚溪", "Dadu River"], "desc": "國際級水鳥濕地", "potential": []}
    ],
    "彰化縣": [
        {"name": "福寶濕地", "lat": 24.0355, "lng": 120.3655, "keywords": ["福寶", "Fubao", "漢寶"], "desc": "水鳥與彩鷸", "potential": []},
        {"name": "八卦山", "lat": 24.0755, "lng": 120.5555, "keywords": ["八卦山", "Bagua"], "desc": "灰面鵟鷹過境", "potential": []},
        {"name": "芳苑濕地", "lat": 23.9255, "lng": 120.3155, "keywords": ["芳苑", "Fangyuan"], "desc": "潮間帶與大杓鷸", "potential": []},
        {"name": "溪州公園", "lat": 23.8555, "lng": 120.4855, "keywords": ["溪州", "Xizhou"], "desc": "平原鳥類", "potential": []},
        {"name": "伸港濕地", "lat": 24.1855, "lng": 120.4855, "keywords": ["伸港", "Shengang"], "desc": "招潮蟹與濱鷸", "potential": []}
    ],
    "南投縣": [
        {"name": "合歡山", "lat": 24.1385, "lng": 121.2755, "keywords": ["合歡山", "Hehuan"], "desc": "高山岩鷚", "potential": []},
        {"name": "塔塔加", "lat": 23.4875, "lng": 120.8845, "keywords": ["塔塔加", "Tataka"], "desc": "星鴉與灰林鴞", "potential": []},
        {"name": "溪頭自然教育園區", "lat": 23.6755, "lng": 120.7955, "keywords": ["溪頭", "Xitou"], "desc": "藪鳥與白耳畫眉", "potential": []},
        {"name": "日月潭", "lat": 23.8555, "lng": 120.9155, "keywords": ["日月潭", "Sun Moon Lake"], "desc": "湖泊與山鳥", "potential": []},
        {"name": "奧萬大", "lat": 23.9555, "lng": 121.1755, "keywords": ["奧萬大", "Aowanda"], "desc": "台灣藍鵲", "potential": []},
        {"name": "鳳凰谷鳥園周邊", "lat": 23.7255, "lng": 120.7855, "keywords": ["鳳凰谷", "Fenghuang"], "desc": "天然林竹雞", "potential": []}
    ],
    "雲林縣": [
        {"name": "湖本村", "lat": 23.6885, "lng": 120.6185, "keywords": ["湖本", "Huben", "八色鳥"], "desc": "八色鳥故鄉", "potential": []},
        {"name": "成龍濕地", "lat": 23.5555, "lng": 120.1655, "keywords": ["成龍", "Chenglong"], "desc": "地層下陷區生態", "potential": []},
        {"name": "椬梧滯洪池", "lat": 23.5355, "lng": 120.1755, "keywords": ["椬梧", "Yiwu"], "desc": "潛鴨與鸕鶿", "potential": []},
        {"name": "林內龍過脈步道", "lat": 23.7555, "lng": 120.6155, "keywords": ["林內", "Linnei", "龍過脈"], "desc": "低海拔生態", "potential": []},
        {"name": "濁水溪口", "lat": 23.8355, "lng": 120.2355, "keywords": ["濁水溪", "Zhuoshui"], "desc": "廣闊沙洲水鳥", "potential": []}
    ],
    "嘉義市": [
        {"name": "嘉義植物園", "lat": 23.4815, "lng": 120.4685, "keywords": ["植物園", "Botanical Garden"], "desc": "都市中的森林", "potential": []},
        {"name": "蘭潭水庫", "lat": 23.4685, "lng": 120.4855, "keywords": ["蘭潭", "Lantan"], "desc": "湖光山色", "potential": []},
        {"name": "八掌溪軍輝橋", "lat": 23.4585, "lng": 120.4625, "keywords": ["八掌溪", "Bazhang"], "desc": "甜根子草與文鳥", "potential": []}
    ],
    "嘉義縣": [
        {"name": "鰲鼓濕地", "lat": 23.5045, "lng": 120.1385, "keywords": ["鰲鼓", "Aogu"], "desc": "候鳥重要棲地", "potential": []},
        {"name": "阿里山沼平公園", "lat": 23.5135, "lng": 120.8085, "keywords": ["阿里山", "Alishan", "沼平"], "desc": "栗背林鴝", "potential": []},
        {"name": "布袋濕地", "lat": 23.3755, "lng": 120.1555, "keywords": ["布袋", "Budai"], "desc": "黑面琵鷺", "potential": []},
        {"name": "仁義潭水庫", "lat": 23.4655, "lng": 120.5255, "keywords": ["仁義潭", "Renyiitan"], "desc": "鸕鶿群聚", "potential": []},
        {"name": "朴子溪口", "lat": 23.4555, "lng": 120.1455, "keywords": ["朴子溪", "Puzi"], "desc": "紅樹林與白鷺", "potential": []},
        {"name": "觸口自然教育中心", "lat": 23.4425, "lng": 120.6055, "keywords": ["觸口", "Chukou"], "desc": "低海拔山鳥", "potential": []}
    ],
    "台南市": [
        {"name": "七股黑面琵鷺保護區", "lat": 23.0465, "lng": 120.0685, "keywords": ["七股", "Qigu", "黑面琵鷺"], "desc": "曾文溪口黑琵", "potential": []},
        {"name": "官田水雉園區", "lat": 23.1785, "lng": 120.3155, "keywords": ["官田", "Guantian", "水雉"], "desc": "水雉復育區", "potential": []},
        {"name": "四草野生動物保護區", "lat": 23.0155, "lng": 120.1355, "keywords": ["四草", "Sicao"], "desc": "高蹺鴴與反嘴鴴", "potential": []},
        {"name": "將軍濕地", "lat": 23.2055, "lng": 120.0955, "keywords": ["將軍", "Jiangjun"], "desc": "鹽灘地水鳥", "potential": []},
        {"name": "巴克禮紀念公園", "lat": 22.9755, "lng": 120.2255, "keywords": ["巴克禮", "Barclay"], "desc": "市區生態公園", "potential": []},
        {"name": "北門潟湖", "lat": 23.2655, "lng": 120.1155, "keywords": ["北門", "Beimen"], "desc": "黑腹燕鷗", "potential": []},
        {"name": "學甲濕地生態園區", "lat": 23.2505, "lng": 120.1755, "keywords": ["學甲", "Xuejia"], "desc": "急水溪灘地", "potential": []}
    ],
    "高雄市": [
        {"name": "茄萣濕地", "lat": 22.8955, "lng": 120.1855, "keywords": ["茄萣", "Qieding"], "desc": "黑面琵鷺度冬", "potential": []},
        {"name": "中寮山", "lat": 22.8255, "lng": 120.4185, "keywords": ["中寮山", "Zhongliao"], "desc": "猛禽過境點", "potential": []},
        {"name": "衛武營都會公園", "lat": 22.6255, "lng": 120.3455, "keywords": ["衛武營", "Weiwuying"], "desc": "黃鸝與鳳頭蒼鷹", "potential": []},
        {"name": "高屏溪舊鐵橋濕地", "lat": 22.6555, "lng": 120.4355, "keywords": ["高屏溪", "舊鐵橋"], "desc": "褐頭鷦鶯", "potential": []},
        {"name": "鳥松濕地", "lat": 22.6655, "lng": 120.3855, "keywords": ["鳥松", "Niaosong"], "desc": "濕地教育", "potential": []},
        {"name": "美濃湖", "lat": 22.9055, "lng": 120.5555, "keywords": ["美濃", "Meinong"], "desc": "水雉與黃胸藪鶥", "potential": []},
        {"name": "援中港濕地", "lat": 22.7255, "lng": 120.2555, "keywords": ["援中港", "Yuanzhonggang"], "desc": "楠梓水鳥保護", "potential": []},
        {"name": "壽山國家自然公園", "lat": 22.6555, "lng": 120.2655, "keywords": ["壽山", "Shoushan", "柴山"], "desc": "台灣畫眉與獼猴", "potential": []}
    ],
    "屏東縣": [
        {"name": "龍鑾潭自然中心", "lat": 21.9855, "lng": 120.7455, "keywords": ["龍鑾潭", "Longluan"], "desc": "鳳頭潛鴨", "potential": []},
        {"name": "社頂自然公園", "lat": 21.9565, "lng": 120.8255, "keywords": ["社頂", "Sheding", "墾丁", "Kenting"], "desc": "赤腹鷹過境", "potential": []},
        {"name": "大鵬灣國家風景區", "lat": 22.4455, "lng": 120.4755, "keywords": ["大鵬灣", "Dapeng"], "desc": "潟湖與大白鷺", "potential": []},
        {"name": "穎達生態農場", "lat": 22.6155, "lng": 120.6155, "keywords": ["穎達", "Yingda"], "desc": "朱鸝", "potential": []},
        {"name": "墾丁國家森林遊樂區", "lat": 21.9655, "lng": 120.8155, "keywords": ["墾丁森林", "Kenting Forest"], "desc": "熱帶植物與灰面鵟鷹", "potential": []},
        {"name": "雙流國家森林遊樂區", "lat": 22.2155, "lng": 120.8155, "keywords": ["雙流", "Shuangliu"], "desc": "溪流鳥類", "potential": []},
        {"name": "大漢山林道", "lat": 22.4055, "lng": 120.7555, "keywords": ["大漢山", "Dahanshan"], "desc": "深山竹雞與藍腹鷴", "potential": []}
    ],
    "宜蘭縣": [
        {"name": "蘭陽溪口", "lat": 24.7155, "lng": 121.8355, "keywords": ["蘭陽溪", "Lanyang River", "東港"], "desc": "黑嘴鷗與燕鷗", "potential": []},
        {"name": "無尾港水鳥保護區", "lat": 24.6153, "lng": 121.8557, "keywords": ["無尾港", "Wuwei"], "desc": "小水鴨與尖尾鴨", "potential": []},
        {"name": "五十二甲濕地", "lat": 24.6655, "lng": 121.8225, "keywords": ["五十二甲", "52jia"], "desc": "黑頸鸊鷉", "potential": []},
        {"name": "壯圍沙丘", "lat": 24.7585, "lng": 121.8085, "keywords": ["壯圍", "Zhuangwei"], "desc": "小燕鷗", "potential": []},
        {"name": "太平山", "lat": 24.4955, "lng": 121.5355, "keywords": ["太平山", "Taipingshan"], "desc": "金翼白眉", "potential": []},
        {"name": "頭城烏石港", "lat": 24.8755, "lng": 121.8355, "keywords": ["烏石港", "Wushi", "頭城"], "desc": "鳳頭燕鷗", "potential": []},
        {"name": "福山植物園", "lat": 24.7555, "lng": 121.5955, "keywords": ["福山植物園", "Fushan"], "desc": "鴛鴦", "potential": []},
        {"name": "羅東林業文化園區", "lat": 24.6855, "lng": 121.7755, "keywords": ["羅東林場", "Luodong Forestry"], "desc": "翠鳥", "potential": []},
        {"name": "冬山河生態綠舟", "lat": 24.6355, "lng": 121.7855, "keywords": ["冬山河", "Dongshan"], "desc": "白腹秧雞", "potential": []},
        {"name": "下埔濕地", "lat": 24.8355, "lng": 121.7955, "keywords": ["下埔", "Xiapu"], "desc": "紫鷺", "potential": []}
    ],
    "花蓮縣": [
        {"name": "布洛灣", "lat": 24.1725, "lng": 121.5755, "keywords": ["布洛灣", "Bulowan", "太魯閣"], "desc": "黃山雀", "potential": []},
        {"name": "花蓮溪口", "lat": 23.9455, "lng": 121.6055, "keywords": ["花蓮溪", "Hualien River"], "desc": "花嘴鴨", "potential": []},
        {"name": "鯉魚潭", "lat": 23.9355, "lng": 121.5055, "keywords": ["鯉魚潭", "Liyu Lake"], "desc": "大冠鷲", "potential": []},
        {"name": "大農大富平地森林", "lat": 23.6155, "lng": 121.4155, "keywords": ["大農大富", "Danongdafu"], "desc": "環頸雉", "potential": []},
        {"name": "南安遊客中心", "lat": 23.3255, "lng": 121.2855, "keywords": ["南安", "Nanan", "瓦拉米"], "desc": "冠羽畫眉", "potential": []},
        {"name": "東華大學", "lat": 23.8955, "lng": 121.5455, "keywords": ["東華大學", "Donghua"], "desc": "環頸雉", "potential": []},
        {"name": "美崙山", "lat": 23.9955, "lng": 121.6155, "keywords": ["美崙山", "Meilun"], "desc": "朱鸝", "potential": []},
        {"name": "富源國家森林遊樂區", "lat": 23.5855, "lng": 121.3555, "keywords": ["富源", "Fuyuan", "蝴蝶谷"], "desc": "黃山雀", "potential": []}
    ],
    "台東縣": [
        {"name": "知本濕地", "lat": 22.6855, "lng": 121.0555, "keywords": ["知本", "Zhiben"], "desc": "環頸雉", "potential": []},
        {"name": "台東森林公園", "lat": 22.7655, "lng": 121.1655, "keywords": ["台東森林", "Forest Park"], "desc": "小鷿鷉", "potential": []},
        {"name": "大坡池", "lat": 23.1155, "lng": 121.2255, "keywords": ["大坡池", "Dapo"], "desc": "花嘴鴨", "potential": []},
        {"name": "蘭嶼", "lat": 22.0555, "lng": 121.5555, "keywords": ["蘭嶼", "Lanyu", "Orchid Island"], "desc": "蘭嶼角鴞", "potential": []},
        {"name": "知本森林遊樂區", "lat": 22.6955, "lng": 121.0155, "keywords": ["知本森林", "Zhiben Forest"], "desc": "朱鸝", "potential": []},
        {"name": "利嘉林道", "lat": 22.8055, "lng": 121.0355, "keywords": ["利嘉", "Lijia"], "desc": "領角鴞", "potential": []},
        {"name": "三仙台", "lat": 23.1255, "lng": 121.4155, "keywords": ["三仙台", "Sanxiantai"], "desc": "岩鷺", "potential": []},
        {"name": "卑南溪口", "lat": 22.7755, "lng": 121.1755, "keywords": ["卑南溪", "Beinan River"], "desc": "小燕鷗", "potential": []}
    ],
    "澎湖縣": [
        {"name": "青螺濕地", "lat": 23.5855, "lng": 119.6555, "keywords": ["青螺", "Qingluo"], "desc": "小燕鷗", "potential": []},
        {"name": "興仁水庫", "lat": 23.5455, "lng": 119.5955, "keywords": ["興仁水庫", "Xingren"], "desc": "花嘴鴨", "potential": []},
        {"name": "林投公園", "lat": 23.5655, "lng": 119.6355, "keywords": ["林投", "Lintou"], "desc": "黃眉柳鶯", "potential": []},
        {"name": "天台山 (望安)", "lat": 23.3755, "lng": 119.5055, "keywords": ["天台山", "Tiantai", "望安"], "desc": "紅尾伯勞", "potential": []},
        {"name": "菜園濕地", "lat": 23.5555, "lng": 119.5855, "keywords": ["菜園", "Caiyuan"], "desc": "小鷿鷉", "potential": []}
    ],
    "金門縣": [
        {"name": "慈湖", "lat": 24.4555, "lng": 118.3055, "keywords": ["慈湖", "Cihu"], "desc": "鸕鶿", "potential": []},
        {"name": "青年農莊", "lat": 24.4655, "lng": 118.4355, "keywords": ["青年農莊", "Youth Farm"], "desc": "栗喉蜂虎", "potential": []},
        {"name": "浯江溪口", "lat": 24.4255, "lng": 118.3155, "keywords": ["浯江溪", "Wujiang"], "desc": "中杓鷸", "potential": []},
        {"name": "太湖遊憩區", "lat": 24.4355, "lng": 118.4255, "keywords": ["太湖", "Taihu"], "desc": "斑翡翠", "potential": []},
        {"name": "金門植物園", "lat": 24.4555, "lng": 118.3855, "keywords": ["金門植物園", "Botanical Garden"], "desc": "戴勝", "potential": []}
    ],
    "連江縣": [
        {"name": "馬祖東引北海坑道", "lat": 26.3755, "lng": 120.4855, "keywords": ["東引", "Dongyin", "北海坑道"], "desc": "黑嘴端鳳頭燕鷗", "potential": []},
        {"name": "南竿介壽菜園", "lat": 26.1539, "lng": 119.9497, "keywords": ["南竿", "Nangan", "介壽", "菜園"], "desc": "田鵐", "potential": []},
        {"name": "勝利水庫", "lat": 26.1555, "lng": 119.9355, "keywords": ["勝利水庫", "Shengli"], "desc": "小鷿鷉", "potential": []},
        {"name": "北竿芹壁", "lat": 26.2255, "lng": 119.9855, "keywords": ["芹壁", "Chinbe"], "desc": "家燕", "potential": []},
        {"name": "西莒坤坵沙灘", "lat": 25.9755, "lng": 119.9355, "keywords": ["西莒", "Xiju", "坤坵"], "desc": "大鳳頭燕鷗", "potential": []}
    ]
}

# ==========================================
# 4. 核心功能函式
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    """計算經緯度距離 (km)"""
    try:
        R = 6371  
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(min(1, a)), math.sqrt(1 - min(1, a)))
        return R * c
    except:
        return 9999

def get_wiki_data(sci_name, com_name):
    """
    V15.4: 使用 Wikipedia API 抓取繁體中文資料，強制 3 個完整句子。
    """
    # 1. 優先查手動修復庫
    if com_name in MANUAL_FIX_DB:
        return MANUAL_FIX_DB[com_name], True

    # 2. 查快取
    if sci_name in WIKI_CACHE: return WIKI_CACHE[sci_name], True

    # 3. 呼叫 Wikipedia API
    queries = [sci_name, com_name, f"{com_name} (鳥類)"]
    for q in queries:
        if not q: continue
        try:
            params = {
                "action": "query",
                "format": "json",
                "prop": "pageimages|extracts",
                "titles": q,
                "pithumbsize": 400,
                "exintro": True,      
                "explaintext": True,  
                "variant": "zh-tw",   
                "redirects": 1,
                "exsentences": 3 # 關鍵：抓取前3個完整句子
            }
            # 隨機延遲
            time.sleep(random.uniform(0.1, 0.3))
            
            resp = requests.get("https://zh.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=5)
            data = resp.json()
            
            pages = data.get("query", {}).get("pages", {})
            for k, v in pages.items():
                if k != "-1": # 找到了
                    desc = v.get("extract", "")
                    img = v.get("thumbnail", {}).get("source", "")
                    
                    # 簡轉繁關鍵字替換 (雙重保險)
                    desc = desc.replace("国", "國").replace("鸟", "鳥").replace("类", "類").replace("华", "華")
                    
                    # 移除多餘空白
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    
                    if not desc: desc = "暫無詳細介紹。"
                    
                    result = {"img": img, "desc": desc}
                    WIKI_CACHE[sci_name] = result
                    return result, False
        except:
            pass
            
    # 失敗回傳
    empty = {"img": "", "desc": "暫無詳細介紹"}
    WIKI_CACHE[sci_name] = empty
    return empty, False

def format_obs_date(obs_dt):
    try:
        dt = datetime.strptime(obs_dt, "%Y-%m-%d %H:%M")
        return dt.strftime("%m/%d %H:%M")
    except:
        return obs_dt

def find_snap_hotspot(obs_lat, obs_lng, obs_loc_name):
    """
    智慧磁吸 V2
    """
    best_match = None
    min_dist = SNAP_RADIUS_KM
    if not obs_loc_name: obs_loc_name = ""
    
    for county, spots in HOT_SPOTS_DATA.items():
        for spot in spots:
            dist = haversine(obs_lat, obs_lng, spot['lat'], spot['lng'])
            if dist < SNAP_RADIUS_KM:
                # 檢查關鍵字
                is_name_match = False
                if spot['name'] in obs_loc_name: is_name_match = True
                if not is_name_match and 'keywords' in spot:
                    for kw in spot['keywords']:
                        if kw in obs_loc_name:
                            is_name_match = True
                            break
                
                if is_name_match and dist < min_dist:
                    min_dist = dist
                    best_match = spot
    return best_match

def safe_print(msg):
    try:
        print(msg)
    except:
        pass

# ==========================================
# 5. 主程式流程 (V15.4 增量更新 + 自動修復)
# ==========================================
def main():
    if not os.path.exists(TARGET_DIR): os.makedirs(TARGET_DIR)
    
    # --- 步驟 1: 建立「舊資料索引」 ---
    existing_records = {} # 用 id 當 key
    
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                
                # A. 預熱 Wiki 快取
                for item in old_data.get('recent', []):
                    # 檢查是否為簡體或殘缺資料，若是則不沿用
                    desc = item.get('wikiDesc', '')
                    if '鸟' in desc or '类' in desc or desc.endswith('...'):
                        continue # 視為髒資料，強制重抓

                    if item.get('sciName') and item.get('wikiImg'):
                        WIKI_CACHE[item['sciName']] = {
                            'img': item.get('wikiImg'),
                            'desc': item.get('wikiDesc')
                        }
                        
                # B. 建立舊資料索引
                for item in old_data.get('recent', []):
                    # 同樣檢查髒資料
                    desc = item.get('wikiDesc', '')
                    if '鸟' in desc or '类' in desc or desc.endswith('...'):
                        continue
                    
                    existing_records[item['id']] = item
                        
            safe_print(f"📦 已載入 {len(WIKI_CACHE)} 筆高品質圖鑑快取")
            safe_print(f"♻️  保留 {len(existing_records)} 筆有效舊資料 (已剔除簡體/殘缺資料)")
            
        except Exception as e:
            safe_print(f"⚠️ 讀取舊檔失敗: {e}，將重新全量抓取")

    safe_print(f"\n🚀 [1/3] 啟動 eBird 增量更新 (V15.4)...")
    all_observations = []
    
    # --- 步驟 2: 抓取 eBird 最新清單 ---
    for county_code in TAIWAN_COUNTIES:
        url = f"https://api.ebird.org/v2/data/obs/{county_code}/recent"
        params = {'back': 21, 'maxResults': 2000, 'sppLocale': 'zh-TW', 'detail': 'full'}
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for d in data: d['_source_county'] = county_code
                all_observations.extend(data)
                safe_print(f"   - {county_code}: {len(data)} 筆")
            time.sleep(0.5)
        except: pass

    # 熱點補強
    safe_print("   - 執行熱點定點掃描...")
    extra_hotspots = []
    for county, spots in HOT_SPOTS_DATA.items():
        for spot in spots:
            url = "https://api.ebird.org/v2/data/obs/geo/recent"
            params = {'lat': spot['lat'], 'lng': spot['lng'], 'dist': GEO_SEARCH_DIST_KM, 'back': 21, 'sppLocale': 'zh-TW', 'maxResults': 500}
            try:
                r = requests.get(url, headers=HEADERS, params=params, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    for d in data: d['_source_county'] = 'GEO_ADDED'
                    extra_hotspots.extend(data)
            except: pass
            time.sleep(0.2)
            
    # --- 步驟 3: 比對與整合 ---
    unique_obs = {}
    for obs in all_observations: unique_obs[obs['subId']] = obs
    for obs in extra_hotspots: unique_obs[obs['subId']] = obs
    
    safe_print(f"🚀 [2/3] 比對資料庫 (共 {len(unique_obs)} 筆)...")
    final_bird_list = []
    
    new_data_count = 0
    cached_data_count = 0
    
    for subId, obs in unique_obs.items():
        if 'comName' not in obs or not obs['comName']: continue
        
        # 增量更新檢查
        if subId in existing_records:
            final_bird_list.append(existing_records[subId])
            cached_data_count += 1
            continue
            
        new_data_count += 1
        
        lat = obs.get('lat')
        lng = obs.get('lng')
        locName = obs.get('locName', '')
        
        # 1. 智慧磁吸
        target_spot = find_snap_hotspot(lat, lng, locName)
        if target_spot:
            final_lat = target_spot['lat']
            final_lng = target_spot['lng']
            final_locName = target_spot['name']
        else:
            final_lat, final_lng, final_locName = lat, lng, locName

        # 2. 抓取 Wiki
        wiki, is_cache = get_wiki_data(obs.get('sciName'), obs.get('comName'))
        
        final_bird_list.append({
            'id': obs.get('subId'),
            'name': obs.get('comName'),
            'sciName': obs.get('sciName'),
            'locName': final_locName,
            'lat': final_lat,
            'lng': final_lng,
            'date': format_obs_date(obs.get('obsDt')),
            'speciesCode': obs.get('speciesCode'),
            'county': obs.get('_source_county', 'UNKNOWN'),
            'wikiImg': wiki['img'],
            'wikiDesc': wiki['desc']
        })

    # --- 步驟 4: 存檔 ---
    safe_print(f"🚀 [3/3] 存檔中 (新資料: {new_data_count}, 沿用: {cached_data_count})...")
    tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    final_json = {"update_at": tw_time, "recent": final_bird_list, "hotspots": HOT_SPOTS_DATA}
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
    
    total_time = time.time() - START_TIME
    safe_print(f"✅ 完成！耗時 {total_time:.2f} 秒，共 {len(final_bird_list)} 筆資料。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
    
    # 防止視窗自動關閉
    input("\n執行完畢，請按 Enter 鍵離開...")