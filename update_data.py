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
EBIRD_API_KEY = '1mpok1sjosl5'  # 請確認您的 Key 是否有效
WIKI_CACHE = {}
START_TIME = time.time()

# 磁吸設定
SNAP_RADIUS_KM = 2.0  # 吸附半徑
GEO_SEARCH_DIST_KM = 3 # 定點打擊的搜尋半徑

# 台灣縣市代碼
TAIWAN_COUNTIES = [
    'TW-TPE', 'TW-NWT', 'TW-KLU', 'TW-TYU', 'TW-HSQ', 'TW-HSZ', 'TW-MIA', 
    'TW-TXG', 'TW-CWH', 'TW-NTO', 'TW-YUL', 'TW-CHY', 'TW-CYI', 'TW-TNN', 
    'TW-KHH', 'TW-PIF', 'TW-ILA', 'TW-HUA', 'TW-TTT', 'TW-PEN', 'TW-KIN', 'TW-LIE'
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(BASE_DIR, 'static')
FILE_PATH = os.path.join(TARGET_DIR, 'birds_data.json')

# 確保輸出目錄存在
if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)

HEADERS = {
    'X-eBirdApiToken': EBIRD_API_KEY
}

# ==========================================
# 2. 手動圖鑑庫 (Manual Fix DB) - 針對Wiki抓不到圖的常見鳥類
# ==========================================
COMMON_BIRDS_FIX = {
    "白頭翁": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Light-vented_Bulbul_-_Pycnonotus_sinensis.jpg/640px-Light-vented_Bulbul_-_Pycnonotus_sinensis.jpg",
    "麻雀": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Passer_montanus_Kobe.jpg/640px-Passer_montanus_Kobe.jpg",
    "珠頸斑鳩": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Spilopelia_chinensis_1.jpg/640px-Spilopelia_chinensis_1.jpg",
    "紅鳩": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Streptopelia_tranquebarica_humilis.jpg/640px-Streptopelia_tranquebarica_humilis.jpg",
    "喜鵲": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Pica_pica_-_Compans_Caffarelli_-_2012-03-16.jpg/640px-Pica_pica_-_Compans_Caffarelli_-_2012-03-16.jpg",
    "家八哥": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Acridotheres_tristis_-_Thailand.jpg/640px-Acridotheres_tristis_-_Thailand.jpg",
    "黑冠麻鷺": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Malayan_Night-Heron_-_Taiwan_S4E8695_%2817320173361%29.jpg/500px-Malayan_Night-Heron_-_Taiwan_S4E8695_%2817320173361%29.jpg",
    "夜鷺": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Nycticorax_nycticorax_01.jpg/640px-Nycticorax_nycticorax_01.jpg",
    "小白鷺": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Egretta_garzetta_at_Matsu.jpg/640px-Egretta_garzetta_at_Matsu.jpg",
    "大白鷺": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Ardea_alba_-_San_Diego.jpg/640px-Ardea_alba_-_San_Diego.jpg",
    "蒼鷺": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Grey_Heron_-_Ardea_cinerea.jpg/640px-Grey_Heron_-_Ardea_cinerea.jpg",
    "紅冠水雞": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Gallinula_chloropus_meridionalis_2.jpg/640px-Gallinula_chloropus_meridionalis_2.jpg",
    "翠鳥": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Common_Kingfisher_Alcedo_atthis.jpg/640px-Common_Kingfisher_Alcedo_atthis.jpg",
    "五色鳥": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Megalaima_nuchalis.jpg/640px-Megalaima_nuchalis.jpg",
    "大卷尾": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Black_Drongo_Dicrurus_macrocercus_by_Nitin_Vyas.jpg/640px-Black_Drongo_Dicrurus_macrocercus_by_Nitin_Vyas.jpg"
}

# ==========================================
# 3. 固定的賞鳥熱點資料 (人工校正版 V13.3)
# ==========================================
# Keywords 用於判斷 eBird 地點名稱是否與熱點相關
HOT_SPOTS_DATA = {
    "台北市": [
        {
            "name": "關渡自然公園",
            "lat": 25.1163, "lng": 121.4725,
            "keywords": ["關渡", "Guandu"],
            "desc": "台北市最重要的水鳥保育區，擁有廣大的草澤與水塘。核心區不對外開放，但透過自然中心望遠鏡可觀察大量雁鴨與鷺科。",
            "potential": [{"name": "花嘴鴨", "sci": "Anas zonorhyncha"}, {"name": "高蹺鴴", "sci": "Himantopus himantopus"}]
        },
        {
            "name": "大安森林公園",
            "lat": 25.0326, "lng": 121.5345,
            "keywords": ["大安森林", "Daan"],
            "desc": "都市之肺，生態池中有穩定的鷺科與秧雞科棲息，樹林間則是五色鳥與各式過境陸鳥的熱點。",
            "potential": [{"name": "五色鳥", "sci": "Psilopogon nuchalis"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]
        },
        {
            "name": "植物園",
            "lat": 25.0335, "lng": 121.5095,
            "keywords": ["植物園", "Botanical"],
            "desc": "歷史悠久的都會公園，荷花池與林區鳥況極佳，是北部拍攝翠鳥、紅冠水雞與鳳頭蒼鷹的入門聖地。",
            "potential": [{"name": "翠鳥", "sci": "Alcedo atthis"}, {"name": "鳳頭蒼鷹", "sci": "Accipiter trivirgatus"}]
        },
        {
            "name": "芝山岩",
            "lat": 25.1038, "lng": 121.5305,
            "keywords": ["芝山", "Zhishan"],
            "desc": "隆起的珊瑚礁地形，擁有茂密林相。是觀察領角鴞、皮黃腹鶲等低海拔山鳥與猛禽的好去處。",
            "potential": [{"name": "領角鴞", "sci": "Otus lettia"}, {"name": "黑冠麻鷺", "sci": "Gorsachius melanolophus"}]
        }
    ],
    "新北市": [
        {
            "name": "金山清水濕地",
            "lat": 25.2285, "lng": 121.6285,
            "keywords": ["金山", "Jinshan", "清水"],
            "desc": "北海岸著名的候鳥驛站，曾有小白鶴長期停留。農田與水域環境適合鷸鴴科與大型水鳥停棲。",
            "potential": [{"name": "黑鳶", "sci": "Milvus migrans"}, {"name": "黃頭鷺", "sci": "Bubulcus ibis"}]
        },
        {
            "name": "萬里野柳地質公園",
            "lat": 25.2065, "lng": 121.6925,
            "keywords": ["野柳", "Yehliu"],
            "desc": "突出海岬地形，是候鳥渡海來台的第一站。每年春秋過境期，岬角步道常充滿稀有過境鳥驚喜。",
            "potential": [{"name": "藍磯鶇", "sci": "Monticola solitarius"}, {"name": "遊隼", "sci": "Falco peregrinus"}]
        },
        {
            "name": "田寮洋",
            "lat": 25.0185, "lng": 121.9385,
            "keywords": ["田寮洋", "Tianliao"],
            "desc": "位於貢寮的隱密濕地，擁有豐富的草澤環境。冬季常有猛禽巡弋，也是雁鴨科的重要度冬地。",
            "potential": [{"name": "魚鷹", "sci": "Pandion haliaetus"}, {"name": "大冠鷲", "sci": "Spilornis cheela"}]
        },
        {
            "name": "烏來福山",
            "lat": 24.7855, "lng": 121.5055,
            "keywords": ["烏來", "福山", "Wulai"],
            "desc": "低海拔闊葉林代表，沿著桶後溪與南勢溪。可見鉛色水鶇、紫嘯鶇等溪流鳥類及多種畫眉科。",
            "potential": [{"name": "鉛色水鶇", "sci": "Phoenicurus fuliginosus"}, {"name": "紫嘯鶇", "sci": "Myophonus insularis"}]
        }
    ],
    "桃園市": [
        {
            "name": "許厝港濕地",
            "lat": 25.0865, "lng": 121.1855,
            "keywords": ["許厝港", "Xucuo"],
            "desc": "國家級重要濕地，擁有廣闊潮間帶與防風林。每年過境期鷸鴴科數量龐大，是北台灣海岸賞鳥首選。",
            "potential": [{"name": "唐白鷺", "sci": "Egretta eulophotes"}, {"name": "東方環頸鴴", "sci": "Charadrius veredus"}]
        },
        {
            "name": "大園水田",
            "lat": 25.0685, "lng": 121.2085,
            "keywords": ["大園", "Dayuan"],
            "desc": "廣大的水田區，冬季休耕期注水後成為水鳥天堂，常有小天鵝、各種特殊鷸鴴科出沒。",
            "potential": [{"name": "小青足鷸", "sci": "Tringa stagnatilis"}, {"name": "鷹斑鷸", "sci": "Tringa glareola"}]
        }
    ],
    "新竹市": [
        {
            "name": "金城湖賞鳥區",
            "lat": 24.8105, "lng": 120.9035,
            "keywords": ["金城湖", "Jincheng"],
            "desc": "香山濕地北端的淡水湖泊，提供穩定水源。高蹺鴴、琵嘴鴨等水鳥群聚，且距離市區不遠，交通方便。",
            "potential": [{"name": "高蹺鴴", "sci": "Himantopus himantopus"}, {"name": "琵嘴鴨", "sci": "Spatula clypeata"}]
        },
        {
            "name": "香山濕地",
            "lat": 24.7755, "lng": 120.9125,
            "keywords": ["香山", "Siangshan"],
            "desc": "廣達1700公頃的泥質灘地，孕育大量底棲生物，吸引成千上萬的候鳥覓食，以鷸鴴科為大宗。",
            "potential": [{"name": "大杓鷸", "sci": "Numenius arquata"}, {"name": "黑腹濱鷸", "sci": "Calidris alpina"}]
        }
    ],
    "苗栗縣": [
        {
            "name": "通霄海水浴場",
            "lat": 24.4985, "lng": 120.6755,
            "keywords": ["通霄", "Tongxiao"],
            "desc": "包含周邊防風林與海岸線，是過境鳥類暫歇的熱點。稀有鳥種如戴勝、各種鵐科常在此被記錄。",
            "potential": [{"name": "戴勝", "sci": "Upupa epops"}, {"name": "小雲雀", "sci": "Alauda gulgula"}]
        }
    ],
    "台中市": [
        {
            "name": "高美濕地",
            "lat": 24.3125, "lng": 120.5495,
            "keywords": ["高美", "Gaomei"],
            "desc": "著名的雲林莞草區，夕陽美景下也是水鳥樂園。黑嘴鷗等稀有海鳥常在此度冬。",
            "potential": [{"name": "黑嘴鷗", "sci": "Saundersilarus saundersi"}, {"name": "蒼鷺", "sci": "Ardea cinerea"}]
        },
        {
            "name": "大雪山林道 23.5K",
            "lat": 24.2385, "lng": 120.9385,
            "keywords": ["大雪山", "Dasyueshan", "23K", "23.5K"],
            "desc": "國際級賞鳥熱點，中海拔山鳥精華區。藍腹鷴常在清晨路邊現身，吸引國內外賞鳥人潮。",
            "potential": [{"name": "藍腹鷴", "sci": "Lophura swinhoii"}, {"name": "深山竹雞", "sci": "Arborophila crudigularis"}]
        },
        {
            "name": "大雪山林道 50K",
            "lat": 24.2755, "lng": 121.0085,
            "keywords": ["大雪山", "Dasyueshan", "50K", "天池"],
            "desc": "高海拔針葉林區，是帝雉、火冠戴菊、栗背林鴝等高山特有種的大本營。天池周邊鳥況亦佳。",
            "potential": [{"name": "帝雉", "sci": "Syrmaticus mikado"}, {"name": "火冠戴菊", "sci": "Regulus goodfellowi"}]
        }
    ],
    "南投縣": [
        {
            "name": "合歡山",
            "lat": 24.1385, "lng": 121.2755,
            "keywords": ["合歡山", "Hehuan"],
            "desc": "台灣公路最高點，主要觀察岩鷚、酒紅朱雀、金翼白眉等高山鳥類。松雪樓附近極易觀察。",
            "potential": [{"name": "岩鷚", "sci": "Prunella collaris"}, {"name": "酒紅朱雀", "sci": "Carpodacus vinaceus"}]
        },
        {
            "name": "塔塔加",
            "lat": 23.4875, "lng": 120.8845,
            "keywords": ["塔塔加", "Tataka"],
            "desc": "玉山國家公園西北園區，林相豐富。灰林鴞、星鴉等中高海拔鳥種常見，也是秋季觀察赤腹鷹過境的熱點。",
            "potential": [{"name": "星鴉", "sci": "Nucifraga caryocatactes"}, {"name": "灰林鴞", "sci": "Strix aluco"}]
        }
    ],
    "彰化縣": [
        {
            "name": "福寶濕地",
            "lat": 24.0355, "lng": 120.3655,
            "keywords": ["福寶", "Fubao", "漢寶"],
            "desc": "彰化沿海重要的漢寶/福寶濕地群，人工營造的棲地吸引大量水鳥。彩鷸、高蹺鴴為此地常客。",
            "potential": [{"name": "彩鷸", "sci": "Rostratula benghalensis"}, {"name": "反嘴鴴", "sci": "Recurvirostra avosetta"}]
        }
    ],
    "雲林縣": [
        {
            "name": "湖本村",
            "lat": 23.6885, "lng": 120.6185,
            "keywords": ["湖本", "Huben", "八色鳥"],
            "desc": "以八色鳥繁殖地聞名，夏季時吸引大量鳥友前往朝聖這美麗的夏候鳥。",
            "potential": [{"name": "八色鳥", "sci": "Pitta nympha"}, {"name": "朱鸝", "sci": "Oriolus traillii"}]
        },
        {
            "name": "成龍濕地",
            "lat": 23.5555, "lng": 120.1655,
            "keywords": ["成龍", "Chenglong"],
            "desc": "地層下陷形成的濕地，現已演替為豐富生態系。常可見黑面琵鷺與大量雁鴨科。",
            "potential": [{"name": "赤頸鴨", "sci": "Mareca penelope"}, {"name": "尖尾鴨", "sci": "Anas acuta"}]
        }
    ],
    "嘉義縣": [
        {
            "name": "鰲鼓濕地",
            "lat": 23.5045, "lng": 120.1385,
            "keywords": ["鰲鼓", "Aogu"],
            "desc": "台灣最大的人工濕地之一，擁有多樣棲地型態。冬季候鳥數量極多，是中南部觀賞猛禽與水鳥的最佳地點。",
            "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}, {"name": "琵嘴鴨", "sci": "Spatula clypeata"}]
        },
        {
            "name": "阿里山沼平公園",
            "lat": 23.5135, "lng": 120.8085,
            "keywords": ["阿里山", "Alishan", "沼平"],
            "desc": "觀賞中高海拔鳥類如栗背林鴝、冠羽畫眉的經典路線。櫻花季時更是鳥語花香。",
            "potential": [{"name": "栗背林鴝", "sci": "Tarsiger johnstoniae"}, {"name": "紋翼畫眉", "sci": "Actinodura morrisoniana"}]
        }
    ],
    "台南市": [
        {
            "name": "七股黑面琵鷺保護區",
            "lat": 23.0465, "lng": 120.0685,
            "keywords": ["七股", "Qigu", "黑面琵鷺"],
            "desc": "全球黑面琵鷺度冬數量最多的區域之一。設有數個賞鳥亭，能清楚觀察這瀕危物種的群聚行為。",
            "potential": [{"name": "黑面琵鷺", "sci": "Platalea minor"}, {"name": "裡海燕鷗", "sci": "Hydroprogne caspia"}]
        },
        {
            "name": "官田水雉園區",
            "lat": 23.1785, "lng": 120.3155,
            "keywords": ["官田", "Guantian", "水雉"],
            "desc": "凌波仙子—水雉的主要復育地。菱角田環境優美，夏季可見水雉繁殖育雛的精彩畫面。",
            "potential": [{"name": "水雉", "sci": "Hydrophasianus chirurgus"}, {"name": "紅冠水雞", "sci": "Gallinula chloropus"}]
        }
    ],
    "高雄市": [
        {
            "name": "茄萣濕地",
            "lat": 22.8955, "lng": 120.1855,
            "keywords": ["茄萣", "Qieding"],
            "desc": "原為鹽田，現為水鳥保護區。近年來黑面琵鷺度冬數量穩定增加，也是觀察反嘴鴴的好地方。",
            "potential": [{"name": "黑面琵鷺", "sci": "Platalea minor"}, {"name": "反嘴鴴", "sci": "Recurvirostra avosetta"}]
        },
        {
            "name": "中寮山",
            "lat": 22.8255, "lng": 120.4185,
            "keywords": ["中寮山", "Zhongliao"],
            "desc": "南部著名的猛禽觀賞點，春季是赤腹鷹與灰面鵟鷹北返的必經之路。",
            "potential": [{"name": "灰面鵟鷹", "sci": "Butastur indicus"}, {"name": "鳳頭蜂鷹", "sci": "Pernis ptilorhynchus"}]
        }
    ],
    "屏東縣": [
        {
            "name": "龍鑾潭自然中心",
            "lat": 21.9855, "lng": 120.7455,
            "keywords": ["龍鑾潭", "Longluan"],
            "desc": "南台灣最大的淡水湖泊，設有高倍望遠鏡。冬季雁鴨科水鳥眾多，鳳頭潛鴨是這裡的招牌。",
            "potential": [{"name": "鳳頭潛鴨", "sci": "Aythya fuligula"}, {"name": "澤鵟", "sci": "Circus spilonotus"}]
        },
        {
            "name": "社頂自然公園",
            "lat": 21.9565, "lng": 120.8255,
            "keywords": ["社頂", "Sheding", "墾丁", "Kenting"],
            "desc": "恆春半島特有的珊瑚礁林地形。秋季九月是觀賞赤腹鷹過境的聖地，數量動輒數萬隻。",
            "potential": [{"name": "赤腹鷹", "sci": "Accipiter soloensis"}, {"name": "台灣畫眉", "sci": "Garrulax taewanus"}]
        }
    ],
    "宜蘭縣": [
        {
            "name": "無尾港水鳥保護區",
            "lat": 24.6153, "lng": 121.8557,
            "keywords": ["無尾港", "Wuwei"],
            "desc": "位於蘇澳的國家級重要濕地，核心賞鳥平台視野極佳。冬季雁鴨科種類豐富，尤其是尖尾鴨與小水鴨群聚。",
            "potential": [{"name": "小水鴨", "sci": "Anas crecca"}, {"name": "尖尾鴨", "sci": "Anas acuta"}]
        },
        {
            "name": "五十二甲濕地",
            "lat": 24.6655, "lng": 121.8225,
            "keywords": ["五十二甲", "52jia"],
            "desc": "原始的蘆葦草澤濕地，冬候鳥數量可觀。也是全台少數能穩定觀察瀕危「黑頸鸊鷉」的地點之一。",
            "potential": [{"name": "黑頸鸊鷉", "sci": "Podiceps nigricollis"}, {"name": "磯鷸", "sci": "Actitis hypoleucos"}]
        },
        {
            "name": "壯圍沙丘",
            "lat": 24.7585, "lng": 121.8085,
            "keywords": ["壯圍", "Zhuangwei", "蘭陽溪"],
            "desc": "蘭陽溪口南岸的廣闊沙丘與防風林。是觀察燕鷗科、以及冬季稀有海鳥如短尾信天翁的潛力點。",
            "potential": [{"name": "小燕鷗", "sci": "Sternula albifrons"}, {"name": "東方環頸鴴", "sci": "Charadrius veredus"}]
        },
        {
            "name": "太平山",
            "lat": 24.4955, "lng": 121.5355,
            "keywords": ["太平山", "Taipingshan"],
            "desc": "潮濕多霧的中高海拔森林。擁有完整的檜木林相，是金翼白眉、灰林鳩等山鳥的樂園。",
            "potential": [{"name": "金翼白眉", "sci": "Garrulax morrisonianus"}, {"name": "灰林鳩", "sci": "Columba pulchricollis"}]
        }
    ],
    "花蓮縣": [
        {
            "name": "布洛灣",
            "lat": 24.1725, "lng": 121.5755,
            "keywords": ["布洛灣", "Bulowan", "太魯閣"],
            "desc": "太魯閣國家公園內的台地，植被豐富。春季吸引黃山雀、赤腹山雀等降遷覓食，鳥況極佳。",
            "potential": [{"name": "黃山雀", "sci": "Machlolophus holsti"}, {"name": "五色鳥", "sci": "Psilopogon nuchalis"}]
        }
    ],
    "台東縣": [
        {
            "name": "知本濕地",
            "lat": 22.6855, "lng": 121.0555,
            "keywords": ["知本", "Zhiben"],
            "desc": "台東市近郊的河口濕地，擁有沙洲與草澤。曾記錄到東方白鸛等珍稀迷鳥。",
            "potential": [{"name": "環頸雉", "sci": "Phasianus colchicus"}, {"name": "小雲雀", "sci": "Alauda gulgula"}]
        }
    ],
    "金門縣": [
        {
            "name": "慈湖",
            "lat": 24.4555, "lng": 118.3055,
            "keywords": ["慈湖", "Cihu"],
            "desc": "金門最大的鹹水湖，冬季擁有龐大的鸕鶿度冬族群，黃昏時「黑軍壓境」歸巢場面極為壯觀。",
            "potential": [{"name": "鸕鶿", "sci": "Phalacrocorax carbo"}, {"name": "斑翡翠", "sci": "Ceryle rudis"}]
        },
        {
            "name": "青年農莊",
            "lat": 24.4655, "lng": 118.4355,
            "keywords": ["青年農莊", "Youth Farm"],
            "desc": "位於金門東半島，夏季色彩繽紛的栗喉蜂虎會在土坡挖洞繁殖，吸引眾多攝影師。",
            "potential": [{"name": "栗喉蜂虎", "sci": "Merops philippinus"}, {"name": "戴勝", "sci": "Upupa epops"}]
        }
    ],
    "連江縣": [
        {
            "name": "馬祖東引北海坑道",
            "lat": 26.3755, "lng": 120.4855,
            "keywords": ["東引", "Dongyin", "北海坑道"],
            "desc": "地形險峻的岩岸，是極危物種「神話之鳥」黑嘴端鳳頭燕鷗的夏季繁殖地。遊客可搭乘賞鳥船從海上近距離觀察燕鷗育雛。",
            "potential": [{"name": "黑嘴端鳳頭燕鷗", "sci": "Thalasseus bernsteini"}]
        },
        {
            "name": "南竿介壽菜園",
            "lat": 26.1539, "lng": 119.9497,
            "keywords": ["南竿", "Nangan", "介壽", "菜園"],
            "desc": "位於縣政府前方的蔬菜公園，是馬祖少見的開闊農地。春秋過境期常吸引田鵐、樹鷚等過境陸鳥停留補充體力。",
            "potential": [{"name": "田鵐", "sci": "Emberiza rustica"}, {"name": "樹鷚", "sci": "Anthus hodgsoni"}]
        }
    ]
}

# ==========================================
# 4. 輔助函式
# ==========================================
def haversine(lat1, lon1, lat2, lon2):
    """計算兩點經緯度的距離 (km)"""
    R = 6371  
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_wiki_data(sci_name, com_name):
    """
    抓取 Wiki 圖片與介紹
    V13 改進：
    1. 優先查手動圖鑑庫 (Manual Fix DB)
    2. 若無，則爬 Wiki
    """
    
    # 1. 檢查手動圖鑑庫
    if com_name in COMMON_BIRDS_FIX:
        return {
            'img': COMMON_BIRDS_FIX[com_name],
            'desc': f"{com_name} (常見鳥種)，詳細資料請參閱圖鑑。"
        }, True

    # 2. 檢查快取
    if sci_name in WIKI_CACHE:
        return WIKI_CACHE[sci_name], True
    
    # 3. 爬蟲邏輯 (保持原樣，針對繁體中文優化)
    # 嘗試順序：中文學名 -> 英文學名
    queries = [com_name, sci_name]
    
    for q in queries:
        try:
            url = f"https://zh.wikipedia.org/wiki/{q}"
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'lxml')
                
                # 抓圖
                img_url = "https://via.placeholder.com/300x200?text=No+Image"
                og_image = soup.find("meta", property="og:image")
                if og_image:
                    img_url = og_image["content"]
                
                # 抓簡介 (只抓第一段)
                desc_text = "暫無詳細介紹。"
                mw_content = soup.find("div", class_="mw-parser-output")
                if mw_content:
                    # 找所有 p，過濾掉空的
                    paragraphs = mw_content.find_all("p", recursive=False)
                    for p in paragraphs:
                        text = p.get_text().strip()
                        if len(text) > 10 and not text.startswith("座標"):
                            # 簡單清理
                            text = re.sub(r'\[.*?\]', '', text) # 去掉 [1][2]
                            text = re.sub(r'（.*?）', '', text) # 去掉學名括號
                            desc_text = text[:150] + "..." if len(text) > 150 else text
                            break
                
                data = {'img': img_url, 'desc': desc_text}
                WIKI_CACHE[sci_name] = data
                return data, False
        except Exception:
            continue

    # 最後手段
    default_data = {
        'img': "https://via.placeholder.com/300x200?text=Bird+Image",
        'desc': f"目前無法取得 {com_name} 的維基百科資料。"
    }
    WIKI_CACHE[sci_name] = default_data
    return default_data, False

def format_obs_date(obs_dt):
    """將 2023-10-27 08:30 轉為 10/27 08:30"""
    try:
        dt = datetime.strptime(obs_dt, "%Y-%m-%d %H:%M")
        return dt.strftime("%m/%d %H:%M")
    except:
        return obs_dt

def find_snap_hotspot(obs_lat, obs_lng, obs_loc_name):
    """
    智慧磁吸邏輯 V2:
    1. 距離 < SNAP_RADIUS_KM (2.0)
    2. 且 地點名稱 (obs_loc_name) 包含 熱點關鍵字 (keywords)
    滿足這兩點才回傳熱點，否則回傳 None
    """
    best_match = None
    min_dist = SNAP_RADIUS_KM # 初始門檻
    
    for county, spots in HOT_SPOTS_DATA.items():
        for spot in spots:
            dist = haversine(obs_lat, obs_lng, spot['lat'], spot['lng'])
            
            if dist < SNAP_RADIUS_KM:
                # 檢查關鍵字匹配
                # 邏輯：只要 location name 中包含任一 keyword 即可
                is_name_match = False
                
                # 1. 檢查熱點全名是否在其中
                if spot['name'] in obs_loc_name:
                    is_name_match = True
                
                # 2. 檢查關鍵字列表
                if not is_name_match and 'keywords' in spot:
                    for kw in spot['keywords']:
                        if kw in obs_loc_name:
                            is_name_match = True
                            break
                
                # 只有當「距離夠近」且「名稱相關」才吸附
                if is_name_match:
                    if dist < min_dist:
                        min_dist = dist
                        best_match = spot
                        
    return best_match

# ==========================================
# 5. 主程式邏輯
# ==========================================
def main():
    print("🚀 [1/3] 開始爬取 eBird 資料 (V13.3 - Smart Snap V2)...")
    
    all_observations = []
    
    # --- 戰術 A: 廣域掃描 (County) ---
    for county_code in TAIWAN_COUNTIES:
        url = f"https://api.ebird.org/v2/data/obs/{county_code}/recent"
        params = {
            'back': 21,  # 抓過去 21 天
            'maxResults': 2000,
            'sppLocale': 'zh-TW', # 強制繁體中文名稱
            'detail': 'full'
        }
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                # 標記來源縣市 (供除錯用)
                for d in data:
                    d['_source_county'] = county_code
                all_observations.extend(data)
                print(f"   - {county_code}: 取得 {len(data)} 筆")
            else:
                print(f"   - {county_code}: 失敗 {r.status_code}")
        except Exception as e:
            print(f"   - {county_code}: 錯誤 {e}")
        
        time.sleep(0.5) # 禮貌性延遲

    # --- 戰術 B: 定點打擊 (Hotspot Geo Search) ---
    # 針對某些跨縣市或容易被漏掉的熱點，直接用圓心掃描
    print("   - 執行定點補強掃描...")
    extra_hotspots = []
    for county, spots in HOT_SPOTS_DATA.items():
        for spot in spots:
            url = "https://api.ebird.org/v2/data/obs/geo/recent"
            params = {
                'lat': spot['lat'],
                'lng': spot['lng'],
                'dist': GEO_SEARCH_DIST_KM, # 3km 半徑
                'back': 21,
                'sppLocale': 'zh-TW',
                'maxResults': 500
            }
            try:
                r = requests.get(url, headers=HEADERS, params=params, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    # 補上縣市標籤 (猜測)
                    for d in data:
                        d['_source_county'] = county
                    extra_hotspots.extend(data)
            except:
                pass
            time.sleep(0.2)
            
    # 合併並去重 (用 subId 當 Key)
    print(f"🚀 [2/3] 資料整合與清洗...")
    unique_obs = {}
    
    # 先處理廣域資料
    for obs in all_observations:
        unique_obs[obs['subId']] = obs
        
    # 再處理定點資料 (如果有重複會覆蓋，沒差)
    for obs in extra_hotspots:
        unique_obs[obs['subId']] = obs
        
    print(f"   - 總計不重複紀錄: {len(unique_obs)} 筆")
    
    # 開始轉換格式與抓 Wiki
    final_bird_list = []
    processed_count = 0
    
    for subId, obs in unique_obs.items():
        processed_count += 1
        if processed_count % 100 == 0:
            print(f"   - 處理進度: {processed_count}/{len(unique_obs)}")
            
        # 排除沒名字的
        if 'comName' not in obs or not obs['comName']:
            continue
            
        # 取得座標
        lat = obs.get('lat')
        lng = obs.get('lng')
        locName = obs.get('locName', '')
        
        # --- 執行 V2 智慧磁吸 ---
        target_spot = find_snap_hotspot(lat, lng, locName)
        
        if target_spot:
            # 符合吸附條件 (距離近 + 名稱相關) -> 使用熱點座標與名稱
            final_lat = target_spot['lat']
            final_lng = target_spot['lng']
            final_locName = target_spot['name'] # 統一叫「關渡自然公園」
        else:
            # 不符合 -> 保持原樣
            final_lat = lat
            final_lng = lng
            final_locName = locName

        # 抓 Wiki (有 Cache)
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

    print(f"\n🚀 [3/3] 存檔中...")
    
    # 台灣時間
    tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    
    final_json = {
        "update_at": tw_time,
        "recent": final_bird_list,
        "hotspots": HOT_SPOTS_DATA
    }
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
    
    total_time = time.time() - START_TIME
    print(f"✅ 完成！耗時 {total_time:.2f} 秒，共寫入 {len(final_bird_list)} 筆資料。")

if __name__ == "__main__":
    main()
