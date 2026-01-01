import requests
import json
import os
import time
import sys
import traceback

# ==========================================
# 1. 基本設定
# ==========================================
EBIRD_API_KEY = '1mpok1sjosl5'  # 建議未來可改用 GitHub Secrets 隱藏
WIKI_CACHE = {}
START_TIME = time.time()

# 台灣所有縣市代碼
TAIWAN_COUNTIES = [
    'TW-TPE', 'TW-NWT', 'TW-KLU', 'TW-TYU', 'TW-HSQ', 'TW-HSZ', 'TW-MIA', 
    'TW-TXG', 'TW-CWH', 'TW-NTO', 'TW-YUL', 'TW-CHY', 'TW-CYI', 'TW-TNN', 
    'TW-KHH', 'TW-PIF', 'TW-ILA', 'TW-HUA', 'TW-TTT', 'TW-PEN', 'TW-KIN', 'TW-LIE'
]

# ⚠️ [修改點 1] 改用相對路徑，讓它在 GitHub 或本地都能找到 static 資料夾
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(BASE_DIR, 'static')
FILE_PATH = os.path.join(TARGET_DIR, 'birds_data.json')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# ==========================================
# 2. 🌟 完整全台熱點資料
# ==========================================
HOT_SPOTS_DATA = {
    "台北市": [
        {"name": "華江雁鴨自然公園", "lat": 25.0374, "lng": 121.4910, "desc": "冬季雁鴨大本營", "potential": [{"name":"小水鴨", "sci":"Anas crecca"}, {"name":"琵嘴鴨", "sci":"Spatula clypeata"}, {"name":"蒼鷺", "sci":"Ardea cinerea"}]},
        {"name": "台北植物園", "lat": 25.0310, "lng": 121.5086, "desc": "都市生態綠洲", "potential": [{"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"黑冠麻鷺", "sci":"Gorsachius melanolophus"}, {"name":"紅冠水雞", "sci":"Gallinula chloropus"}]},
        {"name": "大安森林公園", "lat": 25.0296, "lng": 121.5358, "desc": "市中心觀察鳳頭蒼鷹", "potential": [{"name":"鳳頭蒼鷹", "sci":"Accipiter trivirgatus"}, {"name":"鵲鴝", "sci":"Copsychus saularis"}, {"name":"五色鳥", "sci":"Psilopogon nuchalis"}]},
        {"name": "關渡自然公園", "lat": 25.1188, "lng": 121.4708, "desc": "北台灣最大濕地", "potential": [{"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"小鷿鷈", "sci":"Tachybaptus ruficollis"}, {"name":"大白鷺", "sci":"Ardea alba"}]},
        {"name": "芝山文化生態綠園", "lat": 25.1052, "lng": 121.5303, "desc": "猛禽救傷中心", "potential": [{"name":"領角鴞", "sci":"Otus lettia"}, {"name":"大冠鷲", "sci":"Spilornis cheela"}, {"name":"台灣藍鵲", "sci":"Urocissa caerulea"}]},
        {"name": "陽明山二子坪步道", "lat": 25.1861, "lng": 121.5262, "desc": "適合全家人的山鳥觀察點", "potential": [{"name":"台灣藍鵲", "sci":"Urocissa caerulea"}, {"name":"竹雞", "sci":"Bambusicola thoracicus"}, {"name":"繡眼畫眉", "sci":"Alcippe morrisonia"}]},
        {"name": "社子島濕地", "lat": 25.1086, "lng": 121.4651, "desc": "河口水鳥觀察", "potential": [{"name":"反嘴鴴", "sci":"Recurvirostra avosetta"}, {"name":"高蹺鴴", "sci":"Himantopus himantopus"}, {"name":"中杓鷸", "sci":"Numenius phaeopus"}]}
    ],
    "新北市": [
        {"name": "碧潭風景區", "lat": 24.9534, "lng": 121.5372, "desc": "黑鳶穩定觀察點", "potential": [{"name":"黑鳶", "sci":"Milvus migrans"}, {"name":"翠鳥", "sci":"Alcedo atthis"}, {"name":"磯鷸", "sci":"Actitis hypoleucos"}]},
        {"name": "野柳地質公園", "lat": 25.2064, "lng": 121.6905, "desc": "過境鳥一級戰區", "potential": [{"name":"戴勝", "sci":"Upupa epops"}, {"name":"藍磯鶇", "sci":"Monticola solitarius"}, {"name":"黃眉黃鶲", "sci":"Ficedula narcissina"}]},
        {"name": "金山清水濕地", "lat": 25.2289, "lng": 121.6315, "desc": "候鳥遷徙重要中繼站", "potential": [{"name":"東方白鸛", "sci":"Ciconia boyciana"}, {"name":"小白鷺", "sci":"Egretta garzetta"}, {"name":"唐白鷺", "sci":"Egretta eulophotes"}]},
        {"name": "烏來福山部落", "lat": 24.8398, "lng": 121.5434, "desc": "中低海拔溪流鳥類", "potential": [{"name":"鉛色水鶇", "sci":"Phoenicurus fuliginosus"}, {"name":"河烏", "sci":"Cinclus pallasii"}, {"name":"紫嘯鶇", "sci":"Myophonus insularis"}]},
        {"name": "貢寮田寮洋濕地", "lat": 25.0135, "lng": 121.9338, "desc": "大型猛禽出沒", "potential": [{"name":"灰澤鵟", "sci":"Circus cyaneus"}, {"name":"小辮鴴", "sci":"Vanellus vanellus"}, {"name":"花嘴鴨", "sci":"Anas zonorhyncha"}]},
        {"name": "板橋鹿角溪人工濕地", "lat": 24.9667, "lng": 121.4194, "desc": "大漢溪畔生態復育", "potential": [{"name":"彩鷸", "sci":"Rostratula benghalensis"}, {"name":"白腹秧雞", "sci":"Amaurornis phoenicurus"}, {"name":"褐頭鷦鶯", "sci":"Prinia inornata"}]}
    ],
    "桃園市": [
        {"name": "許厝港濕地", "lat": 25.0931, "lng": 121.1895, "desc": "國家級重要濕地", "potential": [{"name":"小燕鷗", "sci":"Sternula albifrons"}, {"name":"黑尾鷸", "sci":"Limosa limosa"}, {"name":"東方環頸鴴", "sci":"Charadrius alexandrinus"}]},
        {"name": "大園水田區", "lat": 25.0667, "lng": 121.2000, "desc": "廣闊農田，鷸鴴科眾多", "potential": [{"name":"小辮鴴", "sci":"Vanellus vanellus"}, {"name":"鷹斑鷸", "sci":"Tringa glareola"}, {"name":"雲雀鴴", "sci":"Glareola maldivarum"}]},
        {"name": "石門水庫風景區", "lat": 24.8143, "lng": 121.2464, "desc": "低海拔林鳥", "potential": [{"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"頭烏線", "sci":"Alcippe brunnea"}, {"name":"小彎嘴", "sci":"Pomatorhinus musicus"}]},
        {"name": "八德埤塘自然生態公園", "lat": 24.9388, "lng": 121.3125, "desc": "埤塘水鳥生態", "potential": [{"name":"小鷿鷈", "sci":"Tachybaptus ruficollis"}, {"name":"紅冠水雞", "sci":"Gallinula chloropus"}, {"name":"白鶺鴒", "sci":"Motacilla alba"}]},
        {"name": "龍潭大池", "lat": 24.8643, "lng": 121.2104, "desc": "市區埤塘觀察", "potential": [{"name":"小白鷺", "sci":"Egretta garzetta"}, {"name":"夜鷺", "sci":"Nycticorax nycticorax"}, {"name":"蒼鷺", "sci":"Ardea cinerea"}]}
    ],
    "新竹縣市": [
        {"name": "金城湖賞鳥區", "lat": 24.8144, "lng": 120.9168, "desc": "香山濕地核心區", "potential": [{"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"反嘴鴴", "sci":"Recurvirostra avosetta"}, {"name":"尖尾鴨", "sci":"Anas acuta"}]},
        {"name": "觀霧國家森林遊樂區", "lat": 24.5057, "lng": 121.1162, "desc": "中高海拔霧林帶", "potential": [{"name":"帝雉", "sci":"Syrmaticus mikado"}, {"name":"白頭鶇", "sci":"Turdus albocinctus"}, {"name":"火冠戴菊", "sci":"Regulus goodfellowi"}]},
        {"name": "十七公里海岸線 (香山濕地)", "lat": 24.7801, "lng": 120.9123, "desc": "大型候鳥棲地", "potential": [{"name":"大杓鷸", "sci":"Numenius arquata"}, {"name":"翻石鷸", "sci":"Arenaria interpres"}, {"name":"灰斑鴴", "sci":"Pluvialis squatarola"}]},
        {"name": "新竹市十九公頃大草原", "lat": 24.7821, "lng": 120.9254, "desc": "草地鳥種觀察", "potential": [{"name":"小雲雀", "sci":"Alauda gulgula"}, {"name":"大草鶯", "sci":"Graminicola striatus"}, {"name":"棕扇尾鶯", "sci":"Cisticola juncidis"}]},
        {"name": "尖石鄉司馬庫斯", "lat": 24.5794, "lng": 121.3323, "desc": "山區特有種 birding", "potential": [{"name":"黃羽鸚嘴", "sci":"Suthora verreauxi"}, {"name":"白耳畫眉", "sci":"Heterophasia auricularis"}, {"name":"青背山雀", "sci":"Parus monticolus"}]}
    ],
    "苗栗縣": [
        {"name": "雪見遊憩區", "lat": 24.4239, "lng": 121.0069, "desc": "寬敞林道，特有種畫眉", "potential": [{"name":"白耳畫眉", "sci":"Heterophasia auricularis"}, {"name":"黃腹琉璃", "sci":"Niltava vivida"}, {"name":"冠羽畫眉", "sci":"Yuhina brunneiceps"}]},
        {"name": "後龍溪口石斑大橋", "lat": 24.6087, "lng": 120.7654, "desc": "知名冬候鳥觀察點", "potential": [{"name":"黑臉鵐", "sci":"Emberiza spodocephala"}, {"name":"紅喉歌鴝", "sci":"Calliope calliope"}, {"name":"黃鶺鴒", "sci":"Motacilla flava"}]},
        {"name": "通霄楓樹里", "lat": 24.4854, "lng": 120.7123, "desc": "石虎與猛禽棲地", "potential": [{"name":"灰面鵟鷹", "sci":"Butastur indicus"}, {"name":"蜂鷹", "sci":"Pernis ptilorhynchus"}, {"name":"鳳頭蒼鷹", "sci":"Accipiter trivirgatus"}]},
        {"name": "三義鄉龍騰斷橋", "lat": 24.3584, "lng": 120.7754, "desc": "森林性鳥類", "potential": [{"name":"大冠鷲", "sci":"Spilornis cheela"}, {"name":"綠鳩", "sci":"Treron sieboldii"}, {"name":"竹雞", "sci":"Bambusicola thoracicus"}]},
        {"name": "明德水庫風景區", "lat": 24.5854, "lng": 120.8954, "desc": "湖泊鳥類", "potential": [{"name":"小白鷺", "sci":"Egretta garzetta"}, {"name":"魚鷹", "sci":"Pandion haliaetus"}, {"name":"夜鷺", "sci":"Nycticorax nycticorax"}]}
    ],
    "台中市": [
        {"name": "大雪山林道 23.5K", "lat": 24.2384, "lng": 120.9431, "desc": "藍腹鷴穩定觀察點", "potential": [{"name":"藍腹鷴", "sci":"Lophura swinhoii"}, {"name":"白耳畫眉", "sci":"Heterophasia auricularis"}, {"name":"藪鳥", "sci":"Liocichla steerii"}]},
        {"name": "大雪山林道 50K 小雪山天池", "lat": 24.2831, "lng": 121.0118, "desc": "高海拔鳥類天堂", "potential": [{"name":"帝雉", "sci":"Syrmaticus mikado"}, {"name":"火冠戴菊", "sci":"Regulus goodfellowi"}, {"name":"栗背林鴝", "sci":"Tarsiger johnstoniae"}]},
        {"name": "高美濕地保護區", "lat": 24.3120, "lng": 120.5492, "desc": "國際級濕地", "potential": [{"name":"黑嘴鷗", "sci":"Chroicocephalus saundersi"}, {"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"大杓鷸", "sci":"Numenius arquata"}]},
        {"name": "台中都會公園", "lat": 24.2053, "lng": 120.5964, "desc": "觀察紅尾伯勞", "potential": [{"name":"紅尾伯勞", "sci":"Lanius cristatus"}, {"name":"極北柳鶯", "sci":"Phylloscopus borealis"}, {"name":"黃鸝", "sci":"Oriolus chinensis"}]},
        {"name": "武陵農場", "lat": 24.3639, "lng": 121.3106, "desc": "溪流與高山森林", "potential": [{"name":"鴛鴦", "sci":"Aix galericulata"}, {"name":"鉛色水鶇", "sci":"Phoenicurus fuliginosus"}, {"name":"河烏", "sci":"Cinclus pallasii"}]},
        {"name": "東勢林場遊樂區", "lat": 24.2882, "lng": 120.8642, "desc": "低海拔林鳥", "potential": [{"name":"台灣藍鵲", "sci":"Urocissa caerulea"}, {"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"綠鳩", "sci":"Treron sieboldii"}]}
    ],
    "南投縣": [
        {"name": "合歡山松雪樓週邊", "lat": 24.1378, "lng": 121.2798, "desc": "最高海拔賞鳥點", "potential": [{"name":"岩鷚", "sci":"Prunella collaris"}, {"name":"酒紅朱雀", "sci":"Carpodacus formosanus"}, {"name":"金翼白眉", "sci":"Trochalopteron morrisonianum"}]},
        {"name": "塔塔加遊客中心", "lat": 23.4862, "lng": 120.8841, "desc": "新中橫高點", "potential": [{"name":"星鴉", "sci":"Nucifraga caryocatactes"}, {"name":"火冠戴菊", "sci":"Regulus goodfellowi"}, {"name":"褐頭花翼", "sci":"Fulvetta formosana"}]},
        {"name": "奧萬大國家森林遊樂區", "lat": 23.9555, "lng": 121.1718, "desc": "楓林與山雀科", "potential": [{"name":"青背山雀", "sci":"Parus monticolus"}, {"name":"赤腹山雀", "sci":"Sittiparus castaneoventris"}, {"name":"黃山雀", "sci":"Parus holsti"}]},
        {"name": "杉林溪森林生態渡假園區", "lat": 23.6393, "lng": 120.7954, "desc": "紋翼畫眉穩定觀察", "potential": [{"name":"紋翼畫眉", "sci":"Actinodura morrisoniana"}, {"name":"狀元鳥", "sci":"Pericrocotus solaris"}, {"name":"小鱗胸鷦鷯", "sci":"Pnoepyga pusilla"}]},
        {"name": "溪頭自然教育園區", "lat": 23.6734, "lng": 120.7964, "desc": "森林特有種", "potential": [{"name":"藪鳥", "sci":"Liocichla steerii"}, {"name":"白耳畫眉", "sci":"Heterophasia auricularis"}, {"name":"冠羽畫眉", "sci":"Yuhina brunneiceps"}]}
    ],
    "彰化縣": [
        {"name": "福寶濕地生態園區", "lat": 24.0326, "lng": 120.3697, "desc": "水鳥與酪農區", "potential": [{"name":"彩鷸", "sci":"Rostratula benghalensis"}, {"name":"小燕鷗", "sci":"Sternula albifrons"}, {"name":"高蹺鴴", "sci":"Himantopus himantopus"}]},
        {"name": "八卦山賞鷹平台", "lat": 24.0722, "lng": 120.5539, "desc": "春分賞灰面鵟鷹", "potential": [{"name":"灰面鵟鷹", "sci":"Butastur indicus"}, {"name":"赤腹鷹", "sci":"Accipiter soloensis"}, {"name":"大冠鷲", "sci":"Spilornis cheela"}]},
        {"name": "漢寶濕地", "lat": 24.0167, "lng": 120.3500, "desc": "廣大潮間帶泥灘", "potential": [{"name":"黑腹濱鷸", "sci":"Calidris alpina"}, {"name":"紅胸濱鷸", "sci":"Calidris ruficollis"}, {"name":"青足鷸", "sci":"Tringa nebularia"}]},
        {"name": "大肚溪口野生動物保護區", "lat": 24.2123, "lng": 120.4854, "desc": "國寶級濕地", "potential": [{"name":"大杓鷸", "sci":"Numenius arquata"}, {"name":"黑臉鵐", "sci":"Emberiza spodocephala"}, {"name":"蒼鷺", "sci":"Ardea cinerea"}]},
        {"name": "彰化溪州公園", "lat": 23.8541, "lng": 120.5123, "desc": "平原公園鳥種", "potential": [{"name":"黑領椋鳥", "sci":"Gracupica nigricollis"}, {"name":"紅鳩", "sci":"Streptopelia tranquebarica"}, {"name":"家八哥", "sci":"Acridotheres tristis"}]}
    ],
    "雲林縣": [
        {"name": "湖本生態合作社 (八色鳥故鄉)", "lat": 23.6895, "lng": 120.6171, "desc": "夏候鳥八色鳥熱點", "potential": [{"name":"八色鳥", "sci":"Pitta nympha"}, {"name":"藍喉太陽鳥", "sci":"Aethopyga gouldiae"}, {"name":"朱鸝", "sci":"Oriolus traillii"}]},
        {"name": "林內觸口 (國三旁)", "lat": 23.7608, "lng": 120.6133, "desc": "清明節猛禽過境鷹河", "potential": [{"name":"灰面鵟鷹", "sci":"Butastur indicus"}, {"name":"赤腹鷹", "sci":"Accipiter soloensis"}, {"name":"鳳頭蒼鷹", "sci":"Accipiter trivirgatus"}]},
        {"name": "成龍濕地", "lat": 23.5535, "lng": 120.1651, "desc": "地層下陷藝術濕地", "potential": [{"name":"反嘴鴴", "sci":"Recurvirostra avosetta"}, {"name":"白琵鷺", "sci":"Platalea alba"}, {"name":"小水鴨", "sci":"Anas crecca"}]},
        {"name": "椬梧滯洪池", "lat": 23.5439, "lng": 120.1697, "desc": "南部重要度冬水鳥區", "potential": [{"name":"鸕鶿", "sci":"Phalacrocorax carbo"}, {"name":"魚鷹", "sci":"Pandion haliaetus"}, {"name":"赤頸鴨", "sci":"Mareca penelope"}]},
        {"name": "濁水溪口 (麥寮段)", "lat": 23.8519, "lng": 120.2283, "desc": "開闊沙洲與澤鵟", "potential": [{"name":"東方澤鵟", "sci":"Circus spilonotus"}, {"name":"黑翅鳶", "sci":"Elanus caeruleus"}, {"name":"短耳鴞", "sci":"Asio flammeus"}]}
    ],
    "嘉義縣市": [
        {"name": "鰲鼓濕地森林園區", "lat": 23.5064, "lng": 120.1192, "desc": "全台最大濕地", "potential": [{"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"鸕鶿", "sci":"Phalacrocorax carbo"}, {"name":"琵嘴鴨", "sci":"Spatula clypeata"}]},
        {"name": "阿里山小笠原山展望台", "lat": 23.5103, "lng": 120.8049, "desc": "日出與帝雉穩定點", "potential": [{"name":"帝雉", "sci":"Syrmaticus mikado"}, {"name":"星鴉", "sci":"Nucifraga caryocatactes"}, {"name":"栗背林鴝", "sci":"Tarsiger johnstoniae"}]},
        {"name": "布袋鹽田濕地", "lat": 23.3769, "lng": 120.1556, "desc": "數萬隻水鳥棲地", "potential": [{"name":"紅嘴鷗", "sci":"Chroicocephalus ridibundus"}, {"name":"高蹺鴴", "sci":"Himantopus himantopus"}, {"name":"紅腹濱鷸", "sci":"Calidris canutus"}]},
        {"name": "嘉義市蘭潭風景區", "lat": 23.4721, "lng": 120.4854, "desc": "市區近郊森林鳥", "potential": [{"name":"小鷿鷈", "sci":"Tachybaptus ruficollis"}, {"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"綠鳩", "sci":"Treron sieboldii"}]},
        {"name": "嘉義市植物園", "lat": 23.4854, "lng": 120.4654, "desc": "市區賞鳥好去處", "potential": [{"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"黑冠麻鷺", "sci":"Gorsachius melanolophus"}, {"name":"紅嘴黑鵯", "sci":"Hypsipetes leucocephalus"}]}
    ],
    "台南市": [
        {"name": "七股黑面琵鷺賞鳥亭", "lat": 23.0892, "lng": 120.0608, "desc": "黑琵度冬核心區", "potential": [{"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"大白鷺", "sci":"Ardea alba"}, {"name":"裡海燕鷗", "sci":"Hydroprogne caspia"}]},
        {"name": "官田水雉生態教育園區", "lat": 23.1878, "lng": 120.2974, "desc": "水雉復育地", "potential": [{"name":"水雉", "sci":"Hydrophasianus chirurgus"}, {"name":"彩鷸", "sci":"Rostratula benghalensis"}, {"name":"黃頭鷺", "sci":"Bubulcus ibis"}]},
        {"name": "台江國家公園四草濕地", "lat": 23.0250, "lng": 120.1333, "desc": "紅樹林與反嘴鴴", "potential": [{"name":"反嘴鴴", "sci":"Recurvirostra avosetta"}, {"name":"大杓鷸", "sci":"Numenius arquata"}, {"name":"小白鷺", "sci":"Egretta garzetta"}]},
        {"name": "將軍鹽田濕地", "lat": 23.2033, "lng": 120.1033, "desc": "重要冬候鳥棲地", "potential": [{"name":"紅腹濱鷸", "sci":"Calidris canutus"}, {"name":"黑尾鷸", "sci":"Limosa limosa"}, {"name":"灰斑鴴", "sci":"Pluvialis squatarola"}]},
        {"name": "北門井仔腳瓦盤鹽田", "lat": 23.2354, "lng": 120.1084, "desc": "夕陽與燕鷗群", "potential": [{"name":"黑腹燕鷗", "sci":"Chlidonias hybrida"}, {"name":"紅嘴鷗", "sci":"Chroicocephalus ridibundus"}, {"name":"裡海燕鷗", "sci":"Hydroprogne caspia"}]}
    ],
    "高雄市": [
        {"name": "茄萣濕地公園", "lat": 22.8906, "lng": 120.1917, "desc": "近距離觀賞黑琵", "potential": [{"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"反嘴鴴", "sci":"Recurvirostra avosetta"}, {"name":"赤頸鴨", "sci":"Mareca penelope"}]},
        {"name": "衛武營都會公園", "lat": 22.6196, "lng": 120.3431, "desc": "都市之肺觀察猛禽", "potential": [{"name":"黃鸝", "sci":"Oriolus chinensis"}, {"name":"鳳頭蒼鷹", "sci":"Accipiter trivirgatus"}, {"name":"翠鳥", "sci":"Alcedo atthis"}]},
        {"name": "高雄左營蓮池潭", "lat": 22.6784, "lng": 120.2954, "desc": "市中心湖泊鳥類", "potential": [{"name":"小鷿鷈", "sci":"Tachybaptus ruficollis"}, {"name":"白腰草鷸", "sci":"Tringa ochropus"}, {"name":"夜鷺", "sci":"Nycticorax nycticorax"}]},
        {"name": "澄清湖風景區", "lat": 22.6621, "lng": 120.3541, "desc": "森林與水鳥", "potential": [{"name":"魚鷹", "sci":"Pandion haliaetus"}, {"name":"綠鳩", "sci":"Treron sieboldii"}, {"name":"五色鳥", "sci":"Psilopogon nuchalis"}]},
        {"name": "高雄洲際濕地公園", "lat": 22.7054, "lng": 120.3021, "desc": "水雉在高雄的家", "potential": [{"name":"水雉", "sci":"Hydrophasianus chirurgus"}, {"name":"紅冠水雞", "sci":"Gallinula chloropus"}, {"name":"小白鷺", "sci":"Egretta garzetta"}]}
    ],
    "屏東縣": [
        {"name": "墾丁國家公園龍鑾潭", "lat": 21.9772, "lng": 120.7423, "desc": "南台灣雁鴨勝地", "potential": [{"name":"鳳頭潛鴨", "sci":"Aythya fuligula"}, {"name":"澤鳧", "sci":"Aythya fuligula"}, {"name":"花嘴鴨", "sci":"Anas zonorhyncha"}]},
        {"name": "社頂自然公園凌霄亭", "lat": 21.9568, "lng": 120.8197, "desc": "秋季起鷹觀察點", "potential": [{"name":"赤腹鷹", "sci":"Accipiter soloensis"}, {"name":"灰面鵟鷹", "sci":"Butastur indicus"}, {"name":"燕隼", "sci":"Falco subbuteo"}]},
        {"name": "大鵬灣國家風景區", "lat": 22.4468, "lng": 120.4727, "desc": "潟湖濕地", "potential": [{"name":"紅嘴鷗", "sci":"Chroicocephalus ridibundus"}, {"name":"小白鷺", "sci":"Egretta garzetta"}, {"name":"蒼鷺", "sci":"Ardea cinerea"}]},
        {"name": "滿州鄉憲之橋", "lat": 22.0221, "lng": 120.8454, "desc": "灰面鵟鷹落鷹點", "potential": [{"name":"灰面鵟鷹", "sci":"Butastur indicus"}, {"name":"蜂鷹", "sci":"Pernis ptilorhynchus"}, {"name":"大冠鷲", "sci":"Spilornis cheela"}]},
        {"name": "墾丁鵝鑾鼻公園", "lat": 21.9021, "lng": 120.8521, "desc": "最南端過境鳥點", "potential": [{"name":"岩鷺", "sci":"Egretta sacra"}, {"name":"藍磯鶇", "sci":"Monticola solitarius"}, {"name":"紅尾伯勞", "sci":"Lanius cristatus"}]}
    ],
    "基隆市": [
        {"name": "基隆港海洋廣場", "lat": 25.1311, "lng": 121.7402, "desc": "黑鳶近距離觀察", "potential": [{"name":"黑鳶", "sci":"Milvus migrans"}, {"name":"磯鷸", "sci":"Actitis hypoleucos"}, {"name":"小白鷺", "sci":"Egretta garzetta"}]},
        {"name": "和平島公園", "lat": 25.1606, "lng": 121.7638, "desc": "岩鷺穩定觀察點", "potential": [{"name":"岩鷺", "sci":"Egretta sacra"}, {"name":"藍磯鶇", "sci":"Monticola solitarius"}, {"name":"遊隼", "sci":"Falco peregrinus"}]},
        {"name": "基隆情人湖公園", "lat": 25.1554, "lng": 121.7054, "desc": "森林鳥種豐富", "potential": [{"name":"大冠鷲", "sci":"Spilornis cheela"}, {"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"紅嘴黑鵯", "sci":"Hypsipetes leucocephalus"}]},
        {"name": "八斗子潮境公園", "lat": 25.1421, "lng": 121.8021, "desc": "觀察遊隼", "potential": [{"name":"遊隼", "sci":"Falco peregrinus"}, {"name":"岩鷺", "sci":"Egretta sacra"}, {"name":"家燕", "sci":"Hirundo rustica"}]},
        {"name": "基隆中正公園", "lat": 25.1321, "lng": 121.7521, "desc": "市區森林綠帶", "potential": [{"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"綠鳩", "sci":"Treron sieboldii"}, {"name":"黑冠麻鷺", "sci":"Gorsachius melanolophus"}]}
    ],
    "宜蘭縣": [
        {"name": "蘭陽溪口 (東港)", "lat": 24.7088, "lng": 121.8295, "desc": "宜蘭河口水鳥重地", "potential": [{"name":"小燕鷗", "sci":"Sternula albifrons"}, {"name":"翻石鷸", "sci":"Arenaria interpres"}, {"name":"黑尾鷸", "sci":"Limosa limosa"}]},
        {"name": "宜蘭五十二甲溼地", "lat": 24.6654, "lng": 121.8225, "desc": "穗花棋盤腳與水雉", "potential": [{"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"水雉", "sci":"Hydrophasianus chirurgus"}, {"name":"高蹺鴴", "sci":"Himantopus himantopus"}]},
        {"name": "蘇澳無尾港水鳥保護區", "lat": 24.6083, "lng": 121.8437, "desc": "淡水與海水交匯", "potential": [{"name":"花嘴鴨", "sci":"Anas zonorhyncha"}, {"name":"小水鴨", "sci":"Anas crecca"}, {"name":"魚鷹", "sci":"Pandion haliaetus"}]},
        {"name": "太平山翠峰林道", "lat": 24.5026, "lng": 121.6095, "desc": "特有種鳥類天堂", "potential": [{"name":"帝雉", "sci":"Syrmaticus mikado"}, {"name":"火冠戴菊", "sci":"Regulus goodfellowi"}, {"name":"褐頭花翼", "sci":"Fulvetta formosana"}]},
        {"name": "壯圍鄉下埔溼地", "lat": 24.8368, "lng": 121.7997, "desc": "水田與鷺科", "potential": [{"name":"紫鷺", "sci":"Ardea purpurea"}, {"name":"蒼鷺", "sci":"Ardea cinerea"}, {"name":"中白鷺", "sci":"Ardea intermedia"}]},
        {"name": "礁溪時潮大塭底", "lat": 24.8037, "lng": 121.7877, "desc": "休耕水田盛宴", "potential": [{"name":"黑面琵鷺", "sci":"Platalea minor"}, {"name":"白眉鴨", "sci":"Spatula querquedula"}, {"name":"青足鷸", "sci":"Tringa nebularia"}]}
    ],
    "花蓮縣": [
        {"name": "太魯閣布洛灣台地", "lat": 24.1720, "lng": 121.5723, "desc": "峽谷台地觀察黃山雀", "potential": [{"name":"黃山雀", "sci":"Parus holsti"}, {"name":"赤腹山雀", "sci":"Sittiparus castaneoventris"}, {"name":"青背山雀", "sci":"Parus monticolus"}]},
        {"name": "花蓮溪口濕地", "lat": 23.9421, "lng": 121.6056, "desc": "河口重要濕地", "potential": [{"name":"小燕鷗", "sci":"Sternula albifrons"}, {"name":"黑臉鵐", "sci":"Emberiza spodocephala"}, {"name":"環頸雉", "sci":"Phasianus colchicus"}]},
        {"name": "鯉魚潭風景區", "lat": 23.9284, "lng": 121.5054, "desc": "湖泊鳥類與山鳥", "potential": [{"name":"小鷿鷈", "sci":"Tachybaptus ruficollis"}, {"name":"翠鳥", "sci":"Alcedo atthis"}, {"name":"綠鳩", "sci":"Treron sieboldii"}]},
        {"name": "美崙山公園", "lat": 23.9854, "lng": 121.6154, "desc": "市區森林綠帶", "potential": [{"name":"烏頭翁", "sci":"Pycnonotus taivanus"}, {"name":"五色鳥", "sci":"Psilopogon nuchalis"}, {"name":"繡眼畫眉", "sci":"繡眼畫眉"}, {"name":"黃眉黃鶲", "sci":"Ficedula narcissina"}, {"name":"紫綬帶", "sci":"Terpsiphone atrocaudata"}]},
        {"name": "大龍澗林道", "lat": 24.0521, "lng": 121.4521, "desc": "山區特有種", "potential": [{"name":"台灣藍鵲", "sci":"Urocissa caerulea"}, {"name":"藪鳥", "sci":"Liocichla steerii"}, {"name":"冠羽畫眉", "sci":"Yuhina brunneiceps"}]}
    ],
    "台東縣": [
        {"name": "池上大坡池", "lat": 23.1186, "lng": 121.2215, "desc": "斷層湖與雁鴨", "potential": [{"name":"水雉", "sci":"Hydrophasianus chirurgus"}, {"name":"花嘴鴨", "sci":"Anas zonorhyncha"}, {"name":"小鷿鷈", "sci":"Tachybaptus ruficollis"}]},
        {"name": "知本濕地", "lat": 22.6854, "lng": 121.0564, "desc": "東部重要水鳥區", "potential": [{"name":"環頸雉", "sci":"Phasianus colchicus"}, {"name":"黃鶺鴒", "sci":"Motacilla flava"}]}
    ],
    "澎湖縣": [
        {"name": "澎湖青螺濕地", "lat": 23.6021, "lng": 119.6454, "desc": "海濱候鳥觀察點", "potential": [{"name":"小燕鷗", "sci":"Sternula albifrons"}, {"name":"中杓鷸", "sci":"Numenius phaeopus"}]}
    ],
    "金門縣": [
        {"name": "金門慈湖", "lat": 24.4654, "lng": 118.2754, "desc": "數萬鸕鶿歸巢壯觀景象", "potential": [{"name":"鸕鶿", "sci":"Phalacrocorax carbo"}, {"name":"褐翅鴉鵑", "sci":"Centropus sinensis"}]},
        {"name": "金門金沙溪口", "lat": 24.4854, "lng": 118.4254, "desc": "多樣化水鳥與翠鳥", "potential": [{"name":"斑點魚狗", "sci":"Ceryle rudis"}, {"name":"蒼鷺", "sci":"Ardea cinerea"}]}
    ],
    "連江縣": [
        {"name": "馬祖東引北海坑道", "lat": 26.3754, "lng": 120.4854, "desc": "神話之鳥夏季繁殖地", "potential": [{"name":"黑嘴端鳳頭燕鷗", "sci":"Thalasseus bernsteini"}]}
    ]
}

# ==========================================
# 3. 百科抓取與進度條
# ==========================================

def get_wiki_data(sci_name, common_name):
    """ 從維基百科獲取圖片與簡介，優先使用快取 """
    if sci_name in WIKI_CACHE: return WIKI_CACHE[sci_name], True
    
    # 嘗試用中文俗名搜尋 (命中率較高)
    params = {
        "action": "query", "format": "json", "prop": "pageimages|extracts",
        "titles": common_name, "pithumbsize": 400, "exintro": True, "explaintext": True, "redirects": 1
    }
    try:
        resp = requests.get("https://zh.wikipedia.org/w/api.php", params=params, timeout=5).json()
        pages = resp.get("query", {}).get("pages", {})
        for k, v in pages.items():
            if k != "-1":
                data = {
                    "img": v.get("thumbnail", {}).get("source", ""),
                    "desc": v.get("extract", "暫無詳細介紹")[:150] + "..." # 限制長度
                }
                WIKI_CACHE[sci_name] = data
                return data, False
    except: pass
    
    # 失敗回傳空值
    empty = {"img": "", "desc": "暫無詳細介紹"}
    WIKI_CACHE[sci_name] = empty
    return empty, False

def main():
    # 確保 static 資料夾存在
    if not os.path.exists(TARGET_DIR): os.makedirs(TARGET_DIR)
    
    # 1. 載入舊資料快取 (加速 wiki 查詢，非必要但可優化)
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                # 這裡單純為了 cache wiki，若無需求可略過
                pass
        except: pass

    print(f"\n🚀 [1/3] 啟動全台鳥況更新...")
    
    # ⚠️ [修改點 2] 改為 List 結構，以符合 index.html 的 .filter() 需求
    all_recent_birds = [] 
    
    total_obs = 0
    start_time = time.time()

    # 2. 抓取 eBird 資料
    for i, code in enumerate(TAIWAN_COUNTIES):
        t0 = time.time()
        try:
            sys.stdout.write(f"\r   正在掃描: {code} ... ")
            sys.stdout.flush()
            
            url = f"https://api.ebird.org/v2/data/obs/{code}/recent?back=14&detail=full"
            r = requests.get(url, headers={'X-eBirdApiToken': EBIRD_API_KEY}, timeout=15)
            
            if r.status_code == 200:
                obs_list = r.json()
                
                for obs in obs_list:
                    # 抓取百科 (同步)
                    wiki, _ = get_wiki_data(obs.get('sciName'), obs.get('comName'))
                    
                    # 每個鳥資料都直接加入大 List
                    all_recent_birds.append({
                        'id': obs.get('subId'),
                        'name': obs.get('comName'),
                        'sciName': obs.get('sciName'),
                        'locName': obs.get('locName'),
                        'lat': obs.get('lat'),
                        'lng': obs.get('lng'),
                        'date': obs.get('obsDt'), # YYYY-MM-DD HH:MM
                        'speciesCode': obs.get('speciesCode'),
                        'county': code,
                        'wikiImg': wiki['img'],
                        'wikiDesc': wiki['desc']
                    })
                
                count = len(obs_list)
                total_obs += count
                sys.stdout.write(f"✅ {count} 筆 (耗時 {time.time()-t0:.1f}s)\n")
            else:
                sys.stdout.write(f"❌ API 錯誤: {r.status_code}\n")
            time.sleep(0.3)
        except Exception as e:
            sys.stdout.write(f"⚠️ 異常: {e}\n")

    print(f"\n🚀 [2/3] 同步更新熱門鳥點百科...")
    hotspot_start = time.time()
    for city, spots in HOT_SPOTS_DATA.items():
        for spot in spots:
            if 'desc' not in spot: spot['desc'] = "知名賞鳥地點"
            for bird in spot.get('potential', []):
                wiki, _ = get_wiki_data(bird['sci'], bird['name'])
                bird['wikiImg'] = wiki['img']
                bird['wikiDesc'] = wiki['desc']
    print(f"   完成 (耗時 {time.time()-hotspot_start:.1f}s)")

    # 3. 存檔
    final_json = {
        "update_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "recent": all_recent_birds, # ⚠️ 這裡現在是 List，地圖才能正常讀取
        "hotspots": HOT_SPOTS_DATA
    }
    
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
    
    total_time = time.time() - start_time
    print(f"\n🎉 全部完成！")
    print(f"   - 總耗時: {total_time:.1f} 秒")
    print(f"   - 總筆數: {total_obs} 筆新紀錄")
    print(f"   - 檔案位置: {FILE_PATH}")
    
    # ⚠️ [修改點 3] 移除 input()，避免 GitHub Action 卡住
    # input("\n按 Enter 鍵結束視窗...")

if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()
        # input("發生錯誤，按 Enter 結束...")