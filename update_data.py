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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TaiwanBirdMap/16.0',
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
    },
    "Spilornis cheela": {
        "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Crested_Serpent_Eagle_in_Taiwan.jpg/600px-Crested_Serpent_Eagle_in_Taiwan.jpg",
        "desc": "大冠鷲（留鳥）。【生態習性】中低海拔山區最常見的猛禽。常乘熱氣流盤旋，發出「忽、忽、忽悠—」的叫聲。主食蛇類，又名蛇鵰。"
    }
}

# ==========================================
# 3. 🌟 完整全台熱點資料 (V16.0 修正：描述與常見鳥種)
# ==========================================
HOT_SPOTS_DATA = {
    "基隆市": [
        {"name": "基隆港 (海洋廣場)", "lat": 25.1315, "lng": 121.7405, "keywords": ["基隆港", "Keelung Port", "海洋廣場"], "desc": "全台最佳黑鳶觀賞點，冬季可近距離觀察猛禽港內覓食。", "potential": [{"name": "黑鳶", "sci": "Milvus migrans"}, {"name": "遊隼", "sci": "Falco peregrinus"}]},
        {"name": "和平島公園", "lat": 25.1605, "lng": 121.7635, "keywords": ["和平島", "Heping Island"], "desc": "擁有豐富海蝕地形，春秋過境期是海岸鳥類的重要休息站。", "potential": [{"name": "岩鷺", "sci": "Egretta sacra"}, {"name": "藍磯鶇", "sci": "Monticola solitarius"}]},
        {"name": "潮境公園", "lat": 25.1425, "lng": 121.8025, "keywords": ["潮境", "Chaojing"], "desc": "開闊的海岸草地與懸崖，適合觀察過境燕鷗與海鳥。", "potential": [{"name": "藍磯鶇", "sci": "Monticola solitarius"}, {"name": "戴勝", "sci": "Upupa epops"}]},
        {"name": "八斗子漁港", "lat": 25.1405, "lng": 121.7925, "keywords": ["八斗子", "Badouzi"], "desc": "冬季東北季風增強時，是鷿鷉與潛鴨避風的優良港灣。", "potential": [{"name": "黑頸鸊鷉", "sci": "Podiceps nigricollis"}, {"name": "蒼鷺", "sci": "Ardea cinerea"}]},
        {"name": "情人湖公園", "lat": 25.1505, "lng": 121.7105, "keywords": ["情人湖", "Lovers Lake"], "desc": "環境清幽的山區湖泊，周邊林相豐富，常見台灣藍鵲。", "potential": [{"name": "台灣藍鵲", "sci": "Urocissa caerulea"}, {"name": "五色鳥", "sci": "Psilopogon nuchalis"}]},
        {"name": "大武崙砲台", "lat": 25.1585, "lng": 121.7155, "keywords": ["大武崙", "Dawulun"], "desc": "居高臨下的砲台古蹟，視野開闊，是秋季觀察猛禽過境的制高點。", "potential": [{"name": "赤腹鷹", "sci": "Accipiter soloensis"}, {"name": "大冠鷲", "sci": "Spilornis cheela"}]}
    ],
    "台北市": [
        {"name": "關渡自然公園", "lat": 25.1163, "lng": 121.4725, "keywords": ["關渡", "Guandu"], "desc": "台北市最重要的濕地保育區，擁有廣大草澤，水鳥種類極多。", "potential": [{"name": "花嘴鴨", "sci": "Anas zonorhyncha"}, {"name": "高蹺鴴", "sci": "Himantopus himantopus"}]},
        {"name": "大安森林公園", "lat": 25.0326, "lng": 121.5345, "keywords": ["大安森林", "Daan"], "desc": "都市之肺，生態池鷺科群聚，樹林間五色鳥與鳳頭蒼鷹穩定繁殖。", "potential": [{"name": "五色鳥", "sci": "Psilopogon nuchalis"}, {"name": "鳳頭蒼鷹", "sci": "Accipiter trivirgatus"}]},
        {"name": "植物園", "lat": 25.0335, "lng": 121.5095, "keywords": ["植物園", "Botanical"], "desc": "歷史悠久的公園，荷花池是拍攝翠鳥與紅冠水雞的熱點。", "potential": [{"name": "翠鳥", "sci": "Alcedo atthis"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]},
        {"name": "大湖公園", "lat": 25.0841, "lng": 121.6026, "keywords": ["大湖", "Dahu"], "desc": "內湖區的湖泊公園，常見小白鷺、夜鷺在錦帶橋畔佇立。", "potential": [{"name": "大白鷺", "sci": "Ardea alba"}, {"name": "夜鷺", "sci": "Nycticorax nycticorax"}]},
        {"name": "華江雁鴨自然公園", "lat": 25.0285, "lng": 121.4915, "keywords": ["華江", "Huajiang"], "desc": "新店溪與大漢溪匯流處，廣大沙洲是冬季小水鴨的重要棲地。", "potential": [{"name": "小水鴨", "sci": "Anas crecca"}, {"name": "蒼鷺", "sci": "Ardea cinerea"}]},
        {"name": "陽明山二子坪", "lat": 25.1855, "lng": 121.5245, "keywords": ["陽明山", "Yangmingshan", "二子坪"], "desc": "平緩的林間步道，是觀察台灣藍鵲、竹雞與中海拔山鳥的好地方。", "potential": [{"name": "台灣藍鵲", "sci": "Urocissa caerulea"}, {"name": "台灣竹雞", "sci": "Bambusicola sonorivox"}]},
        {"name": "台大校園", "lat": 25.0175, "lng": 121.5395, "keywords": ["台大", "NTU", "台灣大學"], "desc": "校園生態豐富，醉月湖與農場可見黑冠麻鷺與領角鴞。", "potential": [{"name": "黑冠麻鷺", "sci": "Gorsachius melanolophus"}, {"name": "領角鴞", "sci": "Otus lettia"}]},
        {"name": "芝山岩", "lat": 25.1038, "lng": 121.5305, "keywords": ["芝山", "Zhishan"], "desc": "隆起的珊瑚礁地形，古木參天，是都市中猛禽與貓頭鷹的棲地。", "potential": [{"name": "領角鴞", "sci": "Otus lettia"}, {"name": "鳳頭蒼鷹", "sci": "Accipiter trivirgatus"}]},
        {"name": "南港公園", "lat": 25.0405, "lng": 121.5855, "keywords": ["南港公園", "Nangang Park"], "desc": "擁有寬闊的埤塘與樹林，翠鳥、蒼鷺常駐，是東區賞鳥好去處。", "potential": [{"name": "翠鳥", "sci": "Alcedo atthis"}, {"name": "蒼鷺", "sci": "Ardea cinerea"}]}
    ],
    "新北市": [
        {"name": "金山清水濕地", "lat": 25.2285, "lng": 121.6285, "keywords": ["金山", "Jinshan", "清水"], "desc": "北海岸著名的候鳥驛站，水田環境常吸引迷鳥停留。", "potential": [{"name": "黑鳶", "sci": "Milvus migrans"}, {"name": "高蹺鴴", "sci": "Himantopus himantopus"}]},
        {"name": "萬里野柳地質公園", "lat": 25.2065, "lng": 121.6925, "keywords": ["野柳", "Yehliu"], "desc": "突出的海岬地形，是候鳥渡海來台的第一站，過境期鳥況極佳。", "potential": [{"name": "藍磯鶇", "sci": "Monticola solitarius"}, {"name": "白腹鶇", "sci": "Turdus pallidus"}]},
        {"name": "田寮洋", "lat": 25.0185, "lng": 121.9385, "keywords": ["田寮洋", "Tianliao"], "desc": "貢寮的隱密濕地，草澤豐富，是觀察猛禽與雁鴨的好點。", "potential": [{"name": "魚鷹", "sci": "Pandion haliaetus"}, {"name": "大冠鷲", "sci": "Spilornis cheela"}]},
        {"name": "烏來福山", "lat": 24.7855, "lng": 121.5055, "keywords": ["烏來", "福山", "Wulai"], "desc": "低海拔闊葉林與溪流，可見鉛色水鶇、紫嘯鶇等溪流鳥類。", "potential": [{"name": "鉛色水鶇", "sci": "Phoenicurus fuliginosus"}, {"name": "紫嘯鶇", "sci": "Myophonus insularis"}]},
        {"name": "五股濕地", "lat": 25.0955, "lng": 121.4555, "keywords": ["五股", "Wugu"], "desc": "廣大的蘆葦叢，夏季黃昏有壯觀的燕群聚集。", "potential": [{"name": "家燕", "sci": "Hirundo rustica"}, {"name": "埃及聖鹮", "sci": "Threskiornis aethiopicus"}]},
        {"name": "新店廣興", "lat": 24.9355, "lng": 121.5555, "keywords": ["廣興", "Guangxing"], "desc": "新店溪上游屈尺壩，水面平靜，是拍攝魚鷹捕魚的勝地。", "potential": [{"name": "魚鷹", "sci": "Pandion haliaetus"}, {"name": "黑鳶", "sci": "Milvus migrans"}]},
        {"name": "淡水金色水岸", "lat": 25.1685, "lng": 121.4425, "keywords": ["淡水", "Tamsui", "金色水岸"], "desc": "淡水河出海口右岸，退潮時露出泥灘地，可觀察濱鷸與鷺科。", "potential": [{"name": "磯鷸", "sci": "Actitis hypoleucos"}, {"name": "小白鷺", "sci": "Egretta garzetta"}]},
        {"name": "挖子尾自然保留區", "lat": 25.1585, "lng": 121.4155, "keywords": ["挖子尾", "Waziwei"], "desc": "位於八里左岸，擁有豐富的紅樹林與潮間帶，是唐白鷺的棲地。", "potential": [{"name": "唐白鷺", "sci": "Egretta eulophotes"}, {"name": "東方環頸鴴", "sci": "Charadrius alexandrinus"}]},
        {"name": "鹿角溪人工濕地", "lat": 24.9655, "lng": 121.4155, "keywords": ["鹿角溪", "Lujiao"], "desc": "大漢溪旁的人工濕地，紅冠水雞與小鷿鷉數量穩定。", "potential": [{"name": "紅冠水雞", "sci": "Gallinula chloropus"}, {"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}]}
    ],
    "桃園市": [
        {"name": "許厝港濕地", "lat": 25.0865, "lng": 121.1855, "keywords": ["許厝港", "Xucuo"], "desc": "國家級重要濕地，擁有廣闊潮間帶，過境期鷸鴴科數量龐大。", "potential": [{"name": "唐白鷺", "sci": "Egretta eulophotes"}, {"name": "東方環頸鴴", "sci": "Charadrius alexandrinus"}]},
        {"name": "大園水田", "lat": 25.0685, "lng": 121.2085, "keywords": ["大園", "Dayuan"], "desc": "冬季休耕水田，吸引小天鵝及各種特殊鷸鴴科出沒。", "potential": [{"name": "小青足鷸", "sci": "Tringa stagnatilis"}, {"name": "鷹斑鷸", "sci": "Tringa glareola"}]},
        {"name": "八德埤塘自然生態公園", "lat": 24.9455, "lng": 121.3055, "keywords": ["八德", "Bade", "埤塘"], "desc": "桃園特有的埤塘地景，常見紅冠水雞、鴛鴦與水禽。", "potential": [{"name": "鴛鴦", "sci": "Aix galericulata"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]},
        {"name": "石門水庫", "lat": 24.8155, "lng": 121.2455, "keywords": ["石門水庫", "Shimen"], "desc": "周邊變葉木林相優美，適合觀察台灣藍鵲、樹鵲等山鳥。", "potential": [{"name": "樹鵲", "sci": "Dendrocitta formosae"}, {"name": "五色鳥", "sci": "Psilopogon nuchalis"}]},
        {"name": "龍潭大池", "lat": 24.8655, "lng": 121.2155, "keywords": ["龍潭", "Longtan"], "desc": "大型人工湖泊，湖中人工島吸引鷺科夜棲，冬季可見鳳頭潛鴨。", "potential": [{"name": "夜鷺", "sci": "Nycticorax nycticorax"}, {"name": "鳳頭潛鴨", "sci": "Aythya fuligula"}]},
        {"name": "大溪河濱公園", "lat": 24.8955, "lng": 121.2855, "keywords": ["大溪", "Daxi"], "desc": "大漢溪畔的綠地，擁有落羽松林，常見夜鷺與翠鳥。", "potential": [{"name": "翠鳥", "sci": "Alcedo atthis"}, {"name": "夜鷺", "sci": "Nycticorax nycticorax"}]}
    ],
    "新竹市": [
        {"name": "金城湖賞鳥區", "lat": 24.8105, "lng": 120.9035, "keywords": ["金城湖", "Jincheng"], "desc": "香山濕地北端的淡水湖泊，提供穩定水源，高蹺鴴與琵嘴鴨群聚。", "potential": [{"name": "高蹺鴴", "sci": "Himantopus himantopus"}, {"name": "琵嘴鴨", "sci": "Spatula clypeata"}]},
        {"name": "香山濕地", "lat": 24.7755, "lng": 120.9125, "keywords": ["香山", "Siangshan"], "desc": "廣大的泥質灘地，孕育大量底棲生物，吸引大杓鷸等候鳥。", "potential": [{"name": "大杓鷸", "sci": "Numenius arquata"}, {"name": "黑腹濱鷸", "sci": "Calidris alpina"}]},
        {"name": "新竹南寮漁港", "lat": 24.8485, "lng": 120.9255, "keywords": ["南寮", "Nanliao", "漁港"], "desc": "除了漁港風光，堤防外側是觀察鷗科與過境海鳥的好地方。", "potential": [{"name": "黑尾鷗", "sci": "Larus crassirostris"}, {"name": "紅嘴鷗", "sci": "Chroicocephalus ridibundus"}]},
        {"name": "十八尖山", "lat": 24.7955, "lng": 120.9855, "keywords": ["十八尖山", "18 Peaks"], "desc": "新竹市的綠肺，低海拔次生林保留完整，林鳥豐富。", "potential": [{"name": "綠繡眼", "sci": "Zosterops simplex"}, {"name": "黑枕藍鶲", "sci": "Hypothymis azurea"}]},
        {"name": "鳳山溪口", "lat": 24.8655, "lng": 120.9155, "keywords": ["鳳山溪", "Fengshan"], "desc": "河口沖積扇，退潮時有大片泥灘，是觀察大型水鳥的熱點。", "potential": [{"name": "蒼鷺", "sci": "Ardea cinerea"}, {"name": "大白鷺", "sci": "Ardea alba"}]}
    ],
    "新竹縣": [
        {"name": "新豐紅樹林", "lat": 24.9125, "lng": 120.9705, "keywords": ["新豐", "Xinfeng", "紅樹林"], "desc": "北台灣重要的水筆仔與海茄苳混生林，可觀察秧雞科與水鳥。", "potential": [{"name": "紅冠水雞", "sci": "Gallinula chloropus"}, {"name": "夜鷺", "sci": "Nycticorax nycticorax"}]},
        {"name": "頭前溪豆腐岩", "lat": 24.8155, "lng": 121.0155, "keywords": ["頭前溪", "Touqian", "豆腐岩"], "desc": "寬闊的河床與草叢，吸引鶺鴒科與鷸鴴科停留。", "potential": [{"name": "白鶺鴒", "sci": "Motacilla alba"}, {"name": "磯鷸", "sci": "Actitis hypoleucos"}]},
        {"name": "司馬庫斯", "lat": 24.5785, "lng": 121.3355, "keywords": ["司馬庫斯", "Smangus"], "desc": "上帝的部落，巨木群周邊是深山特有種鳥類的世外桃源。", "potential": [{"name": "黃山雀", "sci": "Machlolophus holsti"}, {"name": "白尾鴝", "sci": "Myiomela leucura"}]},
        {"name": "峨眉湖", "lat": 24.6755, "lng": 120.9855, "keywords": ["峨眉湖", "Emei"], "desc": "風景秀麗的湖泊，常見鸕鶿、魚鷹以及鷺科鳥類。", "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}, {"name": "魚鷹", "sci": "Pandion haliaetus"}]},
        {"name": "觀霧國家森林", "lat": 24.5055, "lng": 121.1155, "keywords": ["觀霧", "Guanwu"], "desc": "終年雲霧繚繞，是尋找帝雉、黃山雀等中高海拔鳥類的熱點。", "potential": [{"name": "帝雉", "sci": "Syrmaticus mikado"}, {"name": "藪鳥", "sci": "Liocichla steereii"}]}
    ],
    "苗栗縣": [
        {"name": "通霄海水浴場", "lat": 24.4985, "lng": 120.6755, "keywords": ["通霄", "Tongxiao"], "desc": "包含周邊防風林與海岸線，是過境鳥類暫歇的熱點。", "potential": [{"name": "戴勝", "sci": "Upupa epops"}, {"name": "紅尾伯勞", "sci": "Lanius cristatus"}]},
        {"name": "雪見遊憩區", "lat": 24.4255, "lng": 121.0155, "keywords": ["雪見", "Xuejian"], "desc": "位於雪霸國家公園，林道平緩，冬季可見大型畫眉科與山雀。", "potential": [{"name": "藪鳥", "sci": "Liocichla steereii"}, {"name": "紅頭山雀", "sci": "Aegithalos concinnus"}]},
        {"name": "後龍溪口", "lat": 24.6155, "lng": 120.7555, "keywords": ["後龍", "Houlong"], "desc": "典型的河口濕地，沙洲與農田交錯，冬季有大量鸕鶿停棲。", "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}, {"name": "小水鴨", "sci": "Anas crecca"}]},
        {"name": "鯉魚潭水庫", "lat": 24.3355, "lng": 120.7755, "keywords": ["鯉魚潭", "Liyutan"], "desc": "群山環繞的水庫，常可見大冠鷲盤旋，湖面有小鷿鷉。", "potential": [{"name": "大冠鷲", "sci": "Spilornis cheela"}, {"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}]},
        {"name": "龍鳳漁港", "lat": 24.6985, "lng": 120.8585, "keywords": ["龍鳳", "Longfeng"], "desc": "海岸防風林與沙灘交界，春秋過境期常有驚喜。", "potential": [{"name": "藍磯鶇", "sci": "Monticola solitarius"}, {"name": "黃尾鴝", "sci": "Phoenicurus auroreus"}]},
        {"name": "挑炭古道", "lat": 24.3985, "lng": 120.7855, "keywords": ["挑炭", "Taotan"], "desc": "位於三義，環境清幽的低海拔山徑，五月桐花季鳥況佳。", "potential": [{"name": "頭烏線", "sci": "Alcippe brunnea"}, {"name": "小彎嘴", "sci": "Pomatorhinus musicus"}]}
    ],
    "台中市": [
        {"name": "高美濕地", "lat": 24.3125, "lng": 120.5495, "keywords": ["高美", "Gaomei"], "desc": "著名的雲林莞草區，夕陽下是黑嘴鷗與濱鷸的樂園。", "potential": [{"name": "黑嘴鷗", "sci": "Saundersilarus saundersi"}, {"name": "大白鷺", "sci": "Ardea alba"}]},
        {"name": "大雪山林道 23.5K", "lat": 24.2385, "lng": 120.9385, "keywords": ["大雪山", "Dasyueshan", "23K", "23.5K"], "desc": "國際級賞鳥熱點，中海拔山鳥精華區，藍腹鷴常在路邊現身。", "potential": [{"name": "藍腹鷴", "sci": "Lophura swinhoii"}, {"name": "白耳畫眉", "sci": "Heterophasia auricularis"}]},
        {"name": "大雪山林道 50K", "lat": 24.2755, "lng": 121.0085, "keywords": ["大雪山", "Dasyueshan", "50K", "天池"], "desc": "高海拔針葉林與天池，是帝雉、火冠戴菊的大本營。", "potential": [{"name": "帝雉", "sci": "Syrmaticus mikado"}, {"name": "火冠戴菊", "sci": "Regulus goodfellowi"}]},
        {"name": "台中都會公園", "lat": 24.2055, "lng": 120.5955, "keywords": ["都會公園", "Metropolitan Park"], "desc": "大肚台地上的廣闊綠地，擁有草原與次生林，適合觀察伯勞。", "potential": [{"name": "紅尾伯勞", "sci": "Lanius cristatus"}, {"name": "小雲雀", "sci": "Alauda gulgula"}]},
        {"name": "旱溪", "lat": 24.1255, "lng": 120.7055, "keywords": ["旱溪", "Hanxi"], "desc": "貫穿市區的河川，經過整治後生態豐富，常見燕鴴。", "potential": [{"name": "燕鴴", "sci": "Glareola maldivarum"}, {"name": "環頸鴴", "sci": "Charadrius alexandrinus"}]},
        {"name": "武陵農場", "lat": 24.3655, "lng": 121.3155, "keywords": ["武陵", "Wuling"], "desc": "群山環繞的谷地，溪流邊可見河烏、鉛色水鶇。", "potential": [{"name": "紅頭山雀", "sci": "Aegithalos concinnus"}, {"name": "鉛色水鶇", "sci": "Phoenicurus fuliginosus"}]},
        {"name": "大肚溪口野生動物保護區", "lat": 24.1985, "lng": 120.4855, "keywords": ["大肚溪", "Dadu River"], "desc": "位於台中與彰化交界，廣闊的河口沙洲，是國際級的鷸鴴科棲地。", "potential": [{"name": "大杓鷸", "sci": "Numenius arquata"}, {"name": "黑腹濱鷸", "sci": "Calidris alpina"}]}
    ],
    "彰化縣": [
        {"name": "福寶濕地", "lat": 24.0355, "lng": 120.3655, "keywords": ["福寶", "Fubao", "漢寶"], "desc": "彰化沿海重要的濕地群，人工棲地吸引大量水鳥與彩鷸。", "potential": [{"name": "彩鷸", "sci": "Rostratula benghalensis"}, {"name": "高蹺鴴", "sci": "Himantopus himantopus"}]},
        {"name": "八卦山", "lat": 24.0755, "lng": 120.5555, "keywords": ["八卦山", "Bagua"], "desc": "每年三月春分前後，是灰面鵟鷹北返過境的「鷹柱」熱點。", "potential": [{"name": "灰面鵟鷹", "sci": "Butastur indicus"}, {"name": "大冠鷲", "sci": "Spilornis cheela"}]},
        {"name": "芳苑濕地", "lat": 23.9255, "lng": 120.3155, "keywords": ["芳苑", "Fangyuan"], "desc": "廣闊的潮間帶泥灘地，退潮時吸引大量杓鷸與濱鷸覓食。", "potential": [{"name": "大杓鷸", "sci": "Numenius arquata"}, {"name": "東方環頸鴴", "sci": "Charadrius alexandrinus"}]},
        {"name": "溪州公園", "lat": 23.8555, "lng": 120.4855, "keywords": ["溪州", "Xizhou"], "desc": "位於濁水溪畔的大型公園，樹林茂密，常見平原性鳥類。", "potential": [{"name": "黑領椋鳥", "sci": "Gracupica nigricollis"}, {"name": "戴勝", "sci": "Upupa epops"}]},
        {"name": "伸港濕地", "lat": 24.1855, "lng": 120.4855, "keywords": ["伸港", "Shengang"], "desc": "大肚溪出海口南岸，廣大的泥灘地與招潮蟹，水鳥豐富。", "potential": [{"name": "黑腹濱鷸", "sci": "Calidris alpina"}, {"name": "東方環頸鴴", "sci": "Charadrius alexandrinus"}]}
    ],
    "南投縣": [
        {"name": "合歡山", "lat": 24.1385, "lng": 121.2755, "keywords": ["合歡山", "Hehuan"], "desc": "台灣公路最高點，易觀察岩鷚、酒紅朱雀等高山鳥類。", "potential": [{"name": "岩鷚", "sci": "Prunella collaris"}, {"name": "酒紅朱雀", "sci": "Carpodacus vinaceus"}]},
        {"name": "塔塔加", "lat": 23.4875, "lng": 120.8845, "keywords": ["塔塔加", "Tataka"], "desc": "玉山國家公園西北園區，常見星鴉、灰林鴞等中高海拔鳥種。", "potential": [{"name": "星鴉", "sci": "Nucifraga caryocatactes"}, {"name": "金翼白眉", "sci": "Garrulax morrisonianus"}]},
        {"name": "溪頭自然教育園區", "lat": 23.6755, "lng": 120.7955, "keywords": ["溪頭", "Xitou"], "desc": "著名的雲霧森林，人工柳杉林與天然林交錯，藪鳥眾多。", "potential": [{"name": "藪鳥", "sci": "Liocichla steereii"}, {"name": "白耳畫眉", "sci": "Heterophasia auricularis"}]},
        {"name": "日月潭", "lat": 23.8555, "lng": 120.9155, "keywords": ["日月潭", "Sun Moon Lake"], "desc": "湖光山色中，可於環湖步道觀察五色鳥、繡眼畫眉。", "potential": [{"name": "繡眼畫眉", "sci": "Alcippe morrisonia"}, {"name": "五色鳥", "sci": "Psilopogon nuchalis"}]},
        {"name": "奧萬大", "lat": 23.9555, "lng": 121.1755, "keywords": ["奧萬大", "Aowanda"], "desc": "以楓紅聞名，同時擁有完整的森林生態，常見台灣藍鵲。", "potential": [{"name": "台灣藍鵲", "sci": "Urocissa caerulea"}, {"name": "冠羽畫眉", "sci": "Yuhina brunneiceps"}]},
        {"name": "鳳凰谷鳥園周邊", "lat": 23.7255, "lng": 120.7855, "keywords": ["鳳凰谷", "Fenghuang"], "desc": "除了園區內的鳥類，周邊天然林也是賞鳥熱點，常見竹雞。", "potential": [{"name": "台灣竹雞", "sci": "Bambusicola sonorivox"}, {"name": "大冠鷲", "sci": "Spilornis cheela"}]}
    ],
    "雲林縣": [
        {"name": "湖本村", "lat": 23.6885, "lng": 120.6185, "keywords": ["湖本", "Huben", "八色鳥"], "desc": "以八色鳥繁殖地聞名，夏季時吸引大量鳥友前往朝聖。", "potential": [{"name": "八色鳥", "sci": "Pitta nympha"}, {"name": "黑枕藍鶲", "sci": "Hypothymis azurea"}]},
        {"name": "成龍濕地", "lat": 23.5555, "lng": 120.1655, "keywords": ["成龍", "Chenglong"], "desc": "地層下陷形成的濕地，常可見黑面琵鷺與大量雁鴨科。", "potential": [{"name": "赤頸鴨", "sci": "Mareca penelope"}, {"name": "黑面琵鷺", "sci": "Platalea minor"}]},
        {"name": "椬梧滯洪池", "lat": 23.5355, "lng": 120.1755, "keywords": ["椬梧", "Yiwu"], "desc": "有「雲林版日月潭」之稱，冬季吸引大量潛鴨、鸕鶿棲息。", "potential": [{"name": "鳳頭潛鴨", "sci": "Aythya fuligula"}, {"name": "鸕鶿", "sci": "Phalacrocorax carbo"}]},
        {"name": "林內龍過脈步道", "lat": 23.7555, "lng": 120.6155, "keywords": ["林內", "Linnei", "龍過脈"], "desc": "低海拔山林步道，生態豐富，可見八色鳥與猛禽。", "potential": [{"name": "黑枕藍鶲", "sci": "Hypothymis azurea"}, {"name": "大冠鷲", "sci": "Spilornis cheela"}]},
        {"name": "濁水溪口", "lat": 23.8355, "lng": 120.2355, "keywords": ["濁水溪", "Zhuoshui"], "desc": "台灣最長河流的出海口，廣漠的沙洲是東方環頸鴴的繁殖地。", "potential": [{"name": "東方環頸鴴", "sci": "Charadrius veredus"}, {"name": "小燕鷗", "sci": "Sternula albifrons"}]}
    ],
    "嘉義市": [
        {"name": "嘉義植物園", "lat": 23.4815, "lng": 120.4685, "keywords": ["植物園", "Botanical Garden"], "desc": "百年樹木林立，是都市中觀察五色鳥、小啄木及黑冠麻鷺的熱點。", "potential": [{"name": "五色鳥", "sci": "Psilopogon nuchalis"}, {"name": "小啄木", "sci": "Yungipicus canicapillus"}]},
        {"name": "蘭潭水庫", "lat": 23.4685, "lng": 120.4855, "keywords": ["蘭潭", "Lantan"], "desc": "湖光山色，周邊步道生態良好，冬季湖面可見小鷿鷉與鷺科。", "potential": [{"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}, {"name": "大冠鷲", "sci": "Spilornis cheela"}]},
        {"name": "八掌溪軍輝橋", "lat": 23.4585, "lng": 120.4625, "keywords": ["八掌溪", "Bazhang"], "desc": "秋季甜根子草盛開，河床上常見斑文鳥與褐頭鷦鶯。", "potential": [{"name": "斑文鳥", "sci": "Lonchura punctulata"}, {"name": "褐頭鷦鶯", "sci": "Priniainornata"}]}
    ],
    "嘉義縣": [
        {"name": "鰲鼓濕地", "lat": 23.5045, "lng": 120.1385, "keywords": ["鰲鼓", "Aogu"], "desc": "台灣最大的人工濕地之一，冬季候鳥數量極多，猛禽與水鳥精彩。", "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}, {"name": "琵嘴鴨", "sci": "Spatula clypeata"}]},
        {"name": "阿里山沼平公園", "lat": 23.5135, "lng": 120.8085, "keywords": ["阿里山", "Alishan", "沼平"], "desc": "觀賞栗背林鴝、冠羽畫眉的經典路線，櫻花季時更是鳥語花香。", "potential": [{"name": "栗背林鴝", "sci": "Tarsiger johnstoniae"}, {"name": "冠羽畫眉", "sci": "Yuhina brunneiceps"}]},
        {"name": "布袋濕地", "lat": 23.3755, "lng": 120.1555, "keywords": ["布袋", "Budai"], "desc": "廢棄鹽田與魚塭區，是黑面琵鷺在嘉義的重要棲地。", "potential": [{"name": "黑面琵鷺", "sci": "Platalea minor"}, {"name": "反嘴鴴", "sci": "Recurvirostra avosetta"}]},
        {"name": "仁義潭水庫", "lat": 23.4655, "lng": 120.5255, "keywords": ["仁義潭", "Renyiitan"], "desc": "供應嘉義用水的水庫，湖面開闊，冬季常有鸕鶿群聚。", "potential": [{"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}, {"name": "鸕鶿", "sci": "Phalacrocorax carbo"}]},
        {"name": "朴子溪口", "lat": 23.4555, "lng": 120.1455, "keywords": ["朴子溪", "Puzi"], "desc": "擁有美麗的紅樹林綠色隧道，泥灘地吸引白鷺鷥與夜鷺營巢。", "potential": [{"name": "小白鷺", "sci": "Egretta garzetta"}, {"name": "夜鷺", "sci": "Nycticorax nycticorax"}]},
        {"name": "觸口自然教育中心", "lat": 23.4425, "lng": 120.6055, "keywords": ["觸口", "Chukou"], "desc": "阿里山公路起點，低海拔森林環境優良，是觀察朱鸝的熱點。", "potential": [{"name": "朱鸝", "sci": "Oriolus traillii"}, {"name": "黑枕藍鶲", "sci": "Hypothymis azurea"}]}
    ],
    "台南市": [
        {"name": "七股黑面琵鷺保護區", "lat": 23.0465, "lng": 120.0685, "keywords": ["七股", "Qigu", "黑面琵鷺"], "desc": "全球黑面琵鷺度冬數量最多的區域之一，設有數個賞鳥亭。", "potential": [{"name": "黑面琵鷺", "sci": "Platalea minor"}, {"name": "大白鷺", "sci": "Ardea alba"}]},
        {"name": "官田水雉園區", "lat": 23.1785, "lng": 120.3155, "keywords": ["官田", "Guantian", "水雉"], "desc": "水雉的主要復育地，菱角田環境優美，夏季可見繁殖育雛。", "potential": [{"name": "水雉", "sci": "Hydrophasianus chirurgus"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]},
        {"name": "四草野生動物保護區", "lat": 23.0155, "lng": 120.1355, "keywords": ["四草", "Sicao"], "desc": "包含鹽田與紅樹林，高蹺鴴、反嘴鴴常在此築巢繁殖。", "potential": [{"name": "反嘴鴴", "sci": "Recurvirostra avosetta"}, {"name": "高蹺鴴", "sci": "Himantopus himantopus"}]},
        {"name": "將軍濕地", "lat": 23.2055, "lng": 120.0955, "keywords": ["將軍", "Jiangjun"], "desc": "廣大的鹽灘地，是觀察國際瀕危鳥種如諾氏鷸、大濱鷸的據點。", "potential": [{"name": "紅胸濱鷸", "sci": "Calidris ruficollis"}, {"name": "黑腹濱鷸", "sci": "Calidris alpina"}]},
        {"name": "巴克禮紀念公園", "lat": 22.9755, "lng": 120.2255, "keywords": ["巴克禮", "Barclay"], "desc": "台南市區的生態寶石，擁有自然式河道，可近距離觀察翠鳥。", "potential": [{"name": "五色鳥", "sci": "Psilopogon nuchalis"}, {"name": "翠鳥", "sci": "Alcedo atthis"}]},
        {"name": "北門潟湖", "lat": 23.2655, "lng": 120.1155, "keywords": ["北門", "Beimen"], "desc": "以夕陽與候鳥聞名，黑腹燕鷗在黃昏時萬鳥歸巢是必看奇觀。", "potential": [{"name": "黑腹燕鷗", "sci": "Chlidonias hybrida"}, {"name": "大白鷺", "sci": "Ardea alba"}]},
        {"name": "學甲濕地生態園區", "lat": 23.2505, "lng": 120.1755, "keywords": ["學甲", "Xuejia"], "desc": "位於急水溪灘地，是黑面琵鷺的重要棲地之一，常見灰斑鴴。", "potential": [{"name": "灰斑鴴", "sci": "Pluvialis squatarola"}, {"name": "黑面琵鷺", "sci": "Platalea minor"}]}
    ],
    "高雄市": [
        {"name": "茄萣濕地", "lat": 22.8955, "lng": 120.1855, "keywords": ["茄萣", "Qieding"], "desc": "原為鹽田，近年來黑面琵鷺度冬數量穩定增加。", "potential": [{"name": "黑面琵鷺", "sci": "Platalea minor"}, {"name": "赤頸鴨", "sci": "Mareca penelope"}]},
        {"name": "中寮山", "lat": 22.8255, "lng": 120.4185, "keywords": ["中寮山", "Zhongliao"], "desc": "南部著名的猛禽觀賞點，春季是赤腹鷹與灰面鵟鷹北返必經之路。", "potential": [{"name": "灰面鵟鷹", "sci": "Butastur indicus"}, {"name": "赤腹鷹", "sci": "Accipiter soloensis"}]},
        {"name": "衛武營都會公園", "lat": 22.6255, "lng": 120.3455, "keywords": ["衛武營", "Weiwuying"], "desc": "保留許多老樹的都會公園，是觀察黃鸝、鳳頭蒼鷹的熱點。", "potential": [{"name": "黃鸝", "sci": "Oriolus chinensis"}, {"name": "鳳頭蒼鷹", "sci": "Accipiter trivirgatus"}]},
        {"name": "高屏溪舊鐵橋濕地", "lat": 22.6555, "lng": 120.4355, "keywords": ["高屏溪", "舊鐵橋"], "desc": "高屏溪畔的人工濕地，蘆葦叢是褐頭鷦鶯、斑文鳥的家。", "potential": [{"name": "褐頭鷦鶯", "sci": "Priniainornata"}, {"name": "斑文鳥", "sci": "Lonchura punctulata"}]},
        {"name": "鳥松濕地", "lat": 22.6655, "lng": 120.3855, "keywords": ["鳥松", "Niaosong"], "desc": "台灣第一座濕地公園，植被豐富，常見翠鳥、紅冠水雞。", "potential": [{"name": "翠鳥", "sci": "Alcedo atthis"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]},
        {"name": "美濃湖", "lat": 22.9055, "lng": 120.5555, "keywords": ["美濃", "Meinong"], "desc": "群山倒映的湖泊，除了水鳥，周邊農田可尋找黃胸藪眉。", "potential": [{"name": "水雉", "sci": "Hydrophasianus chirurgus"}, {"name": "黃胸藪鶥", "sci": "Liocichla steereii"}]},
        {"name": "援中港濕地", "lat": 22.7255, "lng": 120.2555, "keywords": ["援中港", "Yuanzhonggang"], "desc": "位於楠梓區，擁有紅樹林與草澤，是水雉在高雄的穩定繁殖地。", "potential": [{"name": "水雉", "sci": "Hydrophasianus chirurgus"}, {"name": "高蹺鴴", "sci": "Himantopus himantopus"}]},
        {"name": "壽山國家自然公園", "lat": 22.6555, "lng": 120.2655, "keywords": ["壽山", "Shoushan", "柴山"], "desc": "珊瑚礁石灰岩地形，密林中是台灣畫眉與獼猴的家。", "potential": [{"name": "台灣畫眉", "sci": "Garrulax taewanus"}, {"name": "五色鳥", "sci": "Psilopogon nuchalis"}]}
    ],
    "屏東縣": [
        {"name": "龍鑾潭自然中心", "lat": 21.9855, "lng": 120.7455, "keywords": ["龍鑾潭", "Longluan"], "desc": "南台灣最大的淡水湖泊，冬季雁鴨科眾多，鳳頭潛鴨是招牌。", "potential": [{"name": "鳳頭潛鴨", "sci": "Aythya fuligula"}, {"name": "澤鳧", "sci": "Aythya fuligula"}]},
        {"name": "社頂自然公園", "lat": 21.9565, "lng": 120.8255, "keywords": ["社頂", "Sheding", "墾丁", "Kenting"], "desc": "恆春半島特有地形，秋季九月是觀賞赤腹鷹過境的聖地。", "potential": [{"name": "赤腹鷹", "sci": "Accipiter soloensis"}, {"name": "灰面鵟鷹", "sci": "Butastur indicus"}]},
        {"name": "大鵬灣國家風景區", "lat": 22.4455, "lng": 120.4755, "keywords": ["大鵬灣", "Dapeng"], "desc": "廣大的潟湖地形，周邊紅樹林適合觀察鷺科與燕鷗。", "potential": [{"name": "大白鷺", "sci": "Ardea alba"}, {"name": "黃小鷺", "sci": "Ixobrychus sinensis"}]},
        {"name": "穎達生態農場", "lat": 22.6155, "lng": 120.6155, "keywords": ["穎達", "Yingda"], "desc": "擁有次生林與草地，是觀察朱鸝、黑枕藍鶲等低海拔山鳥的絕佳私人景點。", "potential": [{"name": "朱鸝", "sci": "Oriolus traillii"}, {"name": "黑枕藍鶲", "sci": "Hypothymis azurea"}]},
        {"name": "墾丁國家森林遊樂區", "lat": 21.9655, "lng": 120.8155, "keywords": ["墾丁森林", "Kenting Forest"], "desc": "熱帶植物園，林相茂密，可見台灣畫眉、五色鳥。", "potential": [{"name": "台灣畫眉", "sci": "Garrulax taewanus"}, {"name": "五色鳥", "sci": "Psilopogon nuchalis"}]},
        {"name": "雙流國家森林遊樂區", "lat": 22.2155, "lng": 120.8155, "keywords": ["雙流", "Shuangliu"], "desc": "擁有潔淨的溪流與瀑布，是觀察鉛色水鶇、紫嘯鶇的好去處。", "potential": [{"name": "鉛色水鶇", "sci": "Phoenicurus fuliginosus"}, {"name": "紫嘯鶇", "sci": "Myophonus insularis"}]},
        {"name": "大漢山林道", "lat": 22.4055, "lng": 120.7555, "keywords": ["大漢山", "Dahanshan"], "desc": "南部最重要的中高海拔賞鳥路線，可尋找深山竹雞、藍腹鷴。", "potential": [{"name": "深山竹雞", "sci": "Arborophila crudigularis"}, {"name": "藍腹鷴", "sci": "Lophura swinhoii"}]}
    ],
    "宜蘭縣": [
        {"name": "蘭陽溪口", "lat": 24.7155, "lng": 121.8355, "keywords": ["蘭陽溪", "Lanyang River", "東港"], "desc": "宜蘭最重要的河口濕地，沙洲遼闊，是鷗科與過境水鳥的一級戰區。", "potential": [{"name": "黑嘴鷗", "sci": "Saundersilarus saundersi"}, {"name": "小燕鷗", "sci": "Sternula albifrons"}]},
        {"name": "無尾港水鳥保護區", "lat": 24.6153, "lng": 121.8557, "keywords": ["無尾港", "Wuwei"], "desc": "國家級重要濕地，核心區視野佳，冬季雁鴨科種類豐富。", "potential": [{"name": "小水鴨", "sci": "Anas crecca"}, {"name": "尖尾鴨", "sci": "Anas acuta"}]},
        {"name": "五十二甲濕地", "lat": 24.6655, "lng": 121.8225, "keywords": ["五十二甲", "52jia"], "desc": "原始的蘆葦草澤濕地，是全台少數能穩定觀察黑頸鸊鷉的地點。", "potential": [{"name": "黑頸鸊鷉", "sci": "Podiceps nigricollis"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]},
        {"name": "壯圍沙丘", "lat": 24.7585, "lng": 121.8085, "keywords": ["壯圍", "Zhuangwei"], "desc": "蘭陽溪口南岸的廣闊沙丘，是觀察燕鷗科與海鳥的潛力點。", "potential": [{"name": "小燕鷗", "sci": "Sternula albifrons"}, {"name": "鳳頭燕鷗", "sci": "Thalasseus bergii"}]},
        {"name": "太平山", "lat": 24.4955, "lng": 121.5355, "keywords": ["太平山", "Taipingshan"], "desc": "潮濕多霧的中高海拔森林，是金翼白眉、灰林鳩等山鳥的樂園。", "potential": [{"name": "金翼白眉", "sci": "Garrulax morrisonianus"}, {"name": "灰林鳩", "sci": "Columba pulchricollis"}]},
        {"name": "頭城烏石港", "lat": 24.8755, "lng": 121.8355, "keywords": ["烏石港", "Wushi", "頭城"], "desc": "賞鯨船起點，港區內外常有各種燕鷗與海鳥停棲。", "potential": [{"name": "鳳頭燕鷗", "sci": "Thalasseus bergii"}, {"name": "岩鷺", "sci": "Egretta sacra"}]},
        {"name": "福山植物園", "lat": 24.7555, "lng": 121.5955, "keywords": ["福山植物園", "Fushan"], "desc": "限制入園人數，環境原始清幽，水生植物池有小鷿鷉、鴛鴦。", "potential": [{"name": "鴛鴦", "sci": "Aix galericulata"}, {"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}]},
        {"name": "羅東林業文化園區", "lat": 24.6855, "lng": 121.7755, "keywords": ["羅東林場", "Luodong Forestry"], "desc": "舊貯木池轉型的生態池，周邊大樹林立，常見翠鳥捕魚。", "potential": [{"name": "翠鳥", "sci": "Alcedo atthis"}, {"name": "蒼鷺", "sci": "Ardea cinerea"}]},
        {"name": "冬山河生態綠舟", "lat": 24.6355, "lng": 121.7855, "keywords": ["冬山河", "Dongshan"], "desc": "位於冬山河流域，擁有廣大的草地與河岸，常見夜鷺與秧雞。", "potential": [{"name": "白腹秧雞", "sci": "Amaurornis phoenicurus"}, {"name": "夜鷺", "sci": "Nycticorax nycticorax"}]},
        {"name": "下埔濕地", "lat": 24.8355, "lng": 121.7955, "keywords": ["下埔", "Xiapu"], "desc": "位於頭城，原本是養殖漁塭，現為水鳥與田鳥的重要熱點。", "potential": [{"name": "紫鷺", "sci": "Ardea purpurea"}, {"name": "花嘴鴨", "sci": "Anas zonorhyncha"}]}
    ],
    "花蓮縣": [
        {"name": "布洛灣", "lat": 24.1725, "lng": 121.5755, "keywords": ["布洛灣", "Bulowan", "太魯閣"], "desc": "太魯閣國家公園內的台地，春季吸引黃山雀、赤腹山雀降遷覓食。", "potential": [{"name": "黃山雀", "sci": "Machlolophus holsti"}, {"name": "赤腹山雀", "sci": "Sittiparus castaneoventris"}]},
        {"name": "花蓮溪口", "lat": 23.9455, "lng": 121.6055, "keywords": ["花蓮溪", "Hualien River"], "desc": "國家級重要濕地，廣闊河口沙洲，冬季可見大量鷸鴴科與鴨科。", "potential": [{"name": "花嘴鴨", "sci": "Anas zonorhyncha"}, {"name": "小環頸鴴", "sci": "Charadrius dubius"}]},
        {"name": "鯉魚潭", "lat": 23.9355, "lng": 121.5055, "keywords": ["鯉魚潭", "Liyu Lake"], "desc": "花蓮最大的內陸湖泊，群山環繞。環潭步道生態豐富，是觀察低海拔山鳥與猛禽的絕佳地點。", "potential": [{"name": "大冠鷲", "sci": "Spilornis cheela"}, {"name": "五色鳥", "sci": "Psilopogon nuchalis"}]},
        {"name": "大農大富平地森林", "lat": 23.6155, "lng": 121.4155, "keywords": ["大農大富", "Danongdafu"], "desc": "花東縱谷中的廣大造林地，全台最容易觀察環頸雉的地方之一。", "potential": [{"name": "環頸雉", "sci": "Phasianus colchicus"}, {"name": "朱鸝", "sci": "Oriolus traillii"}]},
        {"name": "南安遊客中心", "lat": 23.3255, "lng": 121.2855, "keywords": ["南安", "Nanan", "瓦拉米"], "desc": "玉山國家公園東部入口，低海拔闊葉林鳥況佳，常見冠羽畫眉。", "potential": [{"name": "冠羽畫眉", "sci": "Yuhina brunneiceps"}, {"name": "朱鸝", "sci": "Oriolus traillii"}]},
        {"name": "東華大學", "lat": 23.8955, "lng": 121.5455, "keywords": ["東華大學", "Donghua"], "desc": "校園廣闊且生態豐富，草地上常可見到保育類的環頸雉漫步。", "potential": [{"name": "環頸雉", "sci": "Phasianus colchicus"}, {"name": "紅尾伯勞", "sci": "Lanius cristatus"}]},
        {"name": "美崙山", "lat": 23.9955, "lng": 121.6155, "keywords": ["美崙山", "Meilun"], "desc": "花蓮市區的綠肺，低海拔森林，市民晨間運動可見五色鳥與朱鸝。", "potential": [{"name": "朱鸝", "sci": "Oriolus traillii"}, {"name": "黑枕藍鶲", "sci": "Hypothymis azurea"}]},
        {"name": "富源國家森林遊樂區", "lat": 23.5855, "lng": 121.3555, "keywords": ["富源", "Fuyuan", "蝴蝶谷"], "desc": "擁有樟樹林與溪流環境，是觀察黃山雀、五色鳥的好地方。", "potential": [{"name": "黃山雀", "sci": "Machlolophus holsti"}, {"name": "鉛色水鶇", "sci": "Phoenicurus fuliginosus"}]}
    ],
    "台東縣": [
        {"name": "知本濕地", "lat": 22.6855, "lng": 121.0555, "keywords": ["知本", "Zhiben"], "desc": "台東市近郊的河口濕地，擁有沙洲與草澤，曾記錄到東方白鸛。", "potential": [{"name": "環頸雉", "sci": "Phasianus colchicus"}, {"name": "黃鸝", "sci": "Oriolus chinensis"}]},
        {"name": "台東森林公園", "lat": 22.7655, "lng": 121.1655, "keywords": ["台東森林", "Forest Park"], "desc": "包含琵琶湖、鷺鷥湖，水域環境穩定，是觀察紅冠水雞與鷺科的好地方。", "potential": [{"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]},
        {"name": "大坡池", "lat": 23.1155, "lng": 121.2255, "keywords": ["大坡池", "Dapo"], "desc": "池上鄉的天然湖泊，周邊稻田環繞，夏季荷花盛開可見水雉。", "potential": [{"name": "花嘴鴨", "sci": "Anas zonorhyncha"}, {"name": "水雉", "sci": "Hydrophasianus chirurgus"}]},
        {"name": "蘭嶼", "lat": 22.0555, "lng": 121.5555, "keywords": ["蘭嶼", "Lanyu", "Orchid Island"], "desc": "擁有獨特的島嶼生態，特有亞種眾多，蘭嶼角鴞是必訪明星。", "potential": [{"name": "蘭嶼角鴞", "sci": "Otus elegans"}, {"name": "紅頭綠鳩", "sci": "Treron formosae"}]},
        {"name": "知本森林遊樂區", "lat": 22.6955, "lng": 121.0155, "keywords": ["知本森林", "Zhiben Forest"], "desc": "擁有巨大的白榕與豐富的熱帶季風林，是觀察朱鸝的極佳地點。", "potential": [{"name": "朱鸝", "sci": "Oriolus traillii"}, {"name": "黃山雀", "sci": "Machlolophus holsti"}]},
        {"name": "利嘉林道", "lat": 22.8055, "lng": 121.0355, "keywords": ["利嘉", "Lijia"], "desc": "生態豐富的林道，夜間生態觀察（夜觀）的熱門路線。", "potential": [{"name": "領角鴞", "sci": "Otus lettia"}, {"name": "黃嘴角鴞", "sci": "Otus spilocephalus"}]},
        {"name": "三仙台", "lat": 23.1255, "lng": 121.4155, "keywords": ["三仙台", "Sanxiantai"], "desc": "突出於海中的岬角，是海鳥重要的棲息地，常見岩鷺。", "potential": [{"name": "岩鷺", "sci": "Egretta sacra"}, {"name": "藍磯鶇", "sci": "Monticola solitarius"}]},
        {"name": "卑南溪口", "lat": 22.7755, "lng": 121.1755, "keywords": ["卑南溪", "Beinan River"], "desc": "廣闊的河口沙洲，是水鳥在東部重要的驛站，小燕鷗常在此繁殖。", "potential": [{"name": "小燕鷗", "sci": "Sternula albifrons"}, {"name": "燕鴴", "sci": "Glareola maldivarum"}]}
    ],
    "澎湖縣": [
        {"name": "青螺濕地", "lat": 23.5855, "lng": 119.6555, "keywords": ["青螺", "Qingluo"], "desc": "澎湖最大的紅樹林濕地，夏季是小燕鷗繁殖季。", "potential": [{"name": "小燕鷗", "sci": "Sternula albifrons"}, {"name": "岩鷺", "sci": "Egretta sacra"}]},
        {"name": "興仁水庫", "lat": 23.5455, "lng": 119.5955, "keywords": ["興仁水庫", "Xingren"], "desc": "淡水資源在離島極為珍貴，水庫區是觀察雁鴨科的好地方。", "potential": [{"name": "花嘴鴨", "sci": "Anas zonorhyncha"}, {"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}]},
        {"name": "林投公園", "lat": 23.5655, "lng": 119.6355, "keywords": ["林投", "Lintou"], "desc": "擁有長達3公里的沙灘與茂密樹林，春秋過境期常充滿驚喜。", "potential": [{"name": "黃眉柳鶯", "sci": "Phylloscopus inornatus"}, {"name": "極北柳鶯", "sci": "Phylloscopus borealis"}]},
        {"name": "天台山 (望安)", "lat": 23.3755, "lng": 119.5055, "keywords": ["天台山", "Tiantai", "望安"], "desc": "望安島最高點，草原開闊，是觀察過境猛禽與伯勞的好地方。", "potential": [{"name": "紅尾伯勞", "sci": "Lanius cristatus"}, {"name": "藍磯鶇", "sci": "Monticola solitarius"}]},
        {"name": "菜園濕地", "lat": 23.5555, "lng": 119.5855, "keywords": ["菜園", "Caiyuan"], "desc": "澎湖國家風景區管理處旁，包含濕地與造林區，觀察林鳥熱點。", "potential": [{"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}, {"name": "斑文鳥", "sci": "Lonchura punctulata"}]}
    ],
    "金門縣": [
        {"name": "慈湖", "lat": 24.4555, "lng": 118.3055, "keywords": ["慈湖", "Cihu"], "desc": "金門最大的鹹水湖，冬季鸕鶿歸巢場面壯觀。", "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}, {"name": "斑翡翠", "sci": "Ceryle rudis"}]},
        {"name": "青年農莊", "lat": 24.4655, "lng": 118.4355, "keywords": ["青年農莊", "Youth Farm"], "desc": "夏季色彩繽紛的栗喉蜂虎會在土坡挖洞繁殖，吸引眾多攝影師。", "potential": [{"name": "栗喉蜂虎", "sci": "Merops philippinus"}, {"name": "戴勝", "sci": "Upupa epops"}]},
        {"name": "浯江溪口", "lat": 24.4255, "lng": 118.3155, "keywords": ["浯江溪", "Wujiang"], "desc": "鄰近建功嶼，擁有廣闊的紅樹林，是觀察鸕鶿、鷸鴴科與鱟的地點。", "potential": [{"name": "中杓鷸", "sci": "Numenius phaeopus"}, {"name": "翻石鷸", "sci": "Arenaria interpres"}]},
        {"name": "太湖遊憩區", "lat": 24.4355, "lng": 118.4255, "keywords": ["太湖", "Taihu"], "desc": "金門最大的人工淡水湖，水源穩定，水獺偶爾現蹤。", "potential": [{"name": "斑翡翠", "sci": "Ceryle rudis"}, {"name": "白胸苦惡鳥", "sci": "Amaurornis phoenicurus"}]},
        {"name": "金門植物園", "lat": 24.4555, "lng": 118.3855, "keywords": ["金門植物園", "Botanical Garden"], "desc": "利用廢棄營區改建，植被茂密，是觀察戴勝、八哥及過境鳥的場所。", "potential": [{"name": "戴勝", "sci": "Upupa epops"}, {"name": "黑領椋鳥", "sci": "Gracupica nigricollis"}]}
    ],
    "連江縣": [
        {"name": "馬祖東引北海坑道", "lat": 26.3755, "lng": 120.4855, "keywords": ["東引", "Dongyin", "北海坑道"], "desc": "地形險峻岩岸，是神話之鳥黑嘴端鳳頭燕鷗的繁殖地。", "potential": [{"name": "黑嘴端鳳頭燕鷗", "sci": "Thalasseus bernsteini"}, {"name": "黑尾鷗", "sci": "Larus crassirostris"}]},
        {"name": "南竿介壽菜園", "lat": 26.1539, "lng": 119.9497, "keywords": ["南竿", "Nangan", "介壽", "菜園"], "desc": "位於縣政府前方的蔬菜公園，春秋過境期常吸引過境陸鳥停留。", "potential": [{"name": "田鵐", "sci": "Emberiza rustica"}, {"name": "樹鷚", "sci": "Anthus hodgsoni"}]},
        {"name": "勝利水庫", "lat": 26.1555, "lng": 119.9355, "keywords": ["勝利水庫", "Shengli"], "desc": "南竿的重要水源地，周邊林相完整，環境清幽。", "potential": [{"name": "小鷿鷉", "sci": "Tachybaptus ruficollis"}, {"name": "蒼鷺", "sci": "Ardea cinerea"}]},
        {"name": "北竿芹壁", "lat": 26.2255, "lng": 119.9855, "keywords": ["芹壁", "Chinbe"], "desc": "保存完整的閩東聚落，屋簷下常見家燕築巢，海面可見燕鷗。", "potential": [{"name": "家燕", "sci": "Hirundo rustica"}, {"name": "大鳳頭燕鷗", "sci": "Thalasseus bergii"}]},
        {"name": "西莒坤坵沙灘", "lat": 25.9755, "lng": 119.9355, "keywords": ["西莒", "Xiju", "坤坵"], "desc": "擁有世界級的方塊海奇景，對面的蛇島是燕鷗保護區。", "potential": [{"name": "大鳳頭燕鷗", "sci": "Thalasseus bergii"}, {"name": "蒼燕鷗", "sci": "Sterna sumatrana"}]}
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
    V16.0: 使用 Wikipedia API 抓取繁體中文資料，強制 3 個完整句子。
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
# 5. 主程式流程 (V16.0)
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

    safe_print(f"\n🚀 [1/3] 啟動 eBird 增量更新 (V16.0)...")
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