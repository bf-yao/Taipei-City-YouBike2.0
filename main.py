from bs4 import BeautifulSoup
import requests
import folium
import numpy as np
import pandas as pd

## function ##
#地址轉經緯度
def getLocation(url):
    response=requests.get(url)
    soup=BeautifulSoup(response.text,"html.parser")
    text=soup.prettify()
    initial_pos=text.find(";window.APP_INITIALIZATION_STATE")
    data=text[initial_pos+36:initial_pos+82]
    num_data=STR_to_NUM(data)
    print(num_data)
    return num_data
#取得的經緯度字串轉數字
def STR_to_NUM(data):
    temp = data.split(',')
    num1=temp[2][:-1]
    return [float(temp[1]),float(num1)]
#計算地球上兩點距離
def cal_distance(lat1, lng1, lat2, lng2):
    r = 6371
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lng2 - lng1)
    a = np.sin(delta_phi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2)**2
    res = r * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 -a)))
    return np.round(res, 2)

## main ##
#載入youbike即時資訊json檔
youbike_json = 'https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json'
df = pd.read_json(youbike_json)
site_name = df["sna"]
sbi = df["sbi"]
bemp = df["bemp"]
lat_bike = df["lat"]
lng_bike = df["lng"]

#使用者輸入地址並轉換成經緯度
print("請輸入您的地址:")
location_input = input()
url = "https://www.google.com/maps/place?q="+location_input
user_location = getLocation(url)

distance_to_search = 0

#確保使用者輸入的是合法值才丟進distance_to_search
while distance_to_search == 0 :
    try:
        print("請輸入您想查詢的距離(公里)範圍 (0.1-2.0)")
        temp = float(input())
        if temp > 0. and temp <= 2.:          
            distance_to_search = temp 
        else:
            print("您所輸入的值不在範圍中，請再輸入一次")       
    except ValueError as e:
        print("您所輸入的值不合法，原因為:",e)
        
#建立地圖
now_location = [user_location[1], user_location[0]]
fmap = folium.Map(location=now_location, zoom_start=16, control_scale=True)
iframe = folium.IFrame("目前位置")
popup_now_location = folium.Popup(iframe, min_width=100, max_width=300)
fmap.add_child(folium.Marker
               (location = now_location, 
                popup = popup_now_location, 
                icon = folium.Icon(icon="fa-map-marker", color="red", prefix="fa")
               )
              )

#算出youbike跟輸入地址之距離，符合的話就印出站名、可借、可還數量
i = 0
count = 0 #計算站點數
#初始化pandas表格資訊
df_site_name = [] 
df_sbi = []
df_bemp = []

for i in range(len(site_name)):
    d = cal_distance(user_location[1], user_location[0], lat_bike[i], lng_bike[i])
    sn = site_name[i].replace("YouBike2.0_", "") #站點
    lat_map = lat_bike[i] #緯度
    lng_map = lng_bike[i] #經度
    sbi_map = sbi[i] #可借車位
    bemp_map = bemp[i] #可還車位
    iframe = folium.IFrame("站點:"+sn+"<br>"+"可借車位:"+str(sbi_map)+"<br>"+"可還車位:"+str(bemp_map))
    popup = folium.Popup(iframe, min_width=200, max_width=300)
    if(d <= distance_to_search):
        count += 1
        df_site_name.append(sn)
        df_sbi.append(sbi_map)
        df_bemp.append(bemp_map)

        #判斷可借車位如果>=5，用綠標顯示，否則維持藍標
        if sbi_map >= 5: 
            fmap.add_child(folium.Marker
                            (location = [lat_map, lng_map],
                                popup = popup,
                                icon = folium.Icon(icon="fa-bicycle", color="green", prefix="fa")
                            )
                          )
        else:
            fmap.add_child(folium.Marker
                            (location = [lat_map, lng_map],
                                popup = popup,
                                icon = folium.Icon(icon="fa-bicycle", color="blue", prefix="fa")
                            )
                          )
#印出找出的結果
result = {
            "站點" : df_site_name,
            "可借車位" : df_sbi,
            "可還車位" : df_bemp
        }

#初始化pandas的dataFrame
df_result = pd.DataFrame(result, columns=["站點", "可借車位", "可還車位"])
df_result.index = df_result.index+1 #index從1開始標
pd.set_option('display.unicode.east_asian_width', True) #pandas版面自動對齊
print("-"*50)
print(df_result)
df_result.to_csv("result.csv", encoding="utf_8_sig") #輸出結果轉為csv檔

print("-"*50)
print("共找到"+str(count)+"個站點")
fmap.save("map1.html")
