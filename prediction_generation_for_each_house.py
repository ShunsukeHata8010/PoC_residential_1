from numpy.testing._private.utils import print_assert_equal
import requests 
import json 
import pandas as pd
import datetime
from sklearn.linear_model import LinearRegression
import math
import os

now = datetime.datetime.now()
pi = math.pi

def HaisenLoss(x,pv_yoryo,rekka,ΔT,kasekisai,effi_PCS,effi_trans,loss_haisen_teikaku):#xは発電量[kW/kWp]。配線や機器ロス共にここでkW倍を行っている
    x = x * pv_yoryo * (1-rekka) * (1-(ΔT-18.4)*0.31/100)
    if x > pv_yoryo /kasekisai / effi_PCS:#PV出力がPCS容量(出力側)を超えていたらピークカット
        x =  pv_yoryo /kasekisai / effi_PCS
    #そうでなければそのまま
    y = x*effi_PCS*effi_trans - x*loss_haisen_teikaku*(x/pv_yoryo)**2 #各種ロスの計算
    return y

def TaiyoKodo(Ido,Keido,J,Ts):#結果としてこの関数は使っていない。
    θ = Keido #東経
    φ = Ido #北緯
    pi = math.pi
    ω = 2*pi/365
    #r = 1/( 1.000110 + 0.034221*math.cos(ω*J) + 0.001280*math.sin(ω*J) + 0.000719*math.cos(2*ω*J) + 0.000077*math.sin(2*ω*J))**0.5
    #太陽赤緯(時刻は関係無し)
    δ = 0.33281-22.984*math.cos(ω*J) - 0.34990*math.cos(2*ω*J) - 0.13980*math.cos(3*ω*J)+ 3.7872* math.sin(ω*J) + 0.03250*math.sin(2*ω*J) + 0.07187*math.sin(3*ω*J)
    """
    print('r:',r)
    print('太陽赤緯：',round(δ,2)) 
    """
    e = 0.0072*math.cos(ω*J) - 0.0528*math.cos(2*ω*J ) - 0.0012*math.cos(3*ω*J)- 0.1229 *math.sin(ω*J) - 0.1565*math.sin(2*ω*J) - 0.0041*math.sin(3*ω*J)
    T = Ts + (θ-135)/15 +e #eは均時差
    t = 15*T - 180
    δ = δ / 180 * pi #太陽赤緯をラジアン表記へ
    t = t / 180 * pi #時角をラジアン表記へ
    φ = φ / 180 * pi #緯度をラジアン表記へ
    #print(φ,δ,t)
    α = math.asin(math.sin(φ)*math.sin(δ) + math.cos(φ)*math.cos(δ)*math.cos(t))
    A_x = math.cos(δ)*math.sin(t)/math.cos(α)
    A_y = (math.sin(α)*math.sin(φ) - math.sin(δ))/math.cos(α)/math.cos(φ)
    A = math.atan2(A_x , A_y)+pi  #太陽方位は北:0度、東:90度、南:180度、西:270度。 
    return α*180/pi,A*180/pi #とりあえず度で返す

def KageHandan(α,A,x,y,h,Φ):#入力は度単位とする。夜は影とは判断しない仕様。
    #α:太陽高度,A:太陽方位,x:影物体までの直線距離,y:影物体の長さ,h:影物体の高さ,Φ:ソーラーから見た時の物体の方位
    z = (x**2 + (y/2)**2)**(1/2) #ソーラーと物体の端との距離
    if x ==0:
        return "nokage"
    else:
        Θ = math.atan((y/2) / x) #ソーラーと物体の端との角度
    Θ = Θ *180/pi #度単位へ変換
    l = h * math.tan((90-α)*pi/180) #影の長さ
    #print('α:',α,'A:',A,'z:',z,'Θ:',Θ,'l:',l)
    #print('Φ-Θ:',Φ-Θ,'Φ+Θ:',Φ+Θ)
    if Φ-Θ < A <Φ+Θ and l >x:#ここの比較は度単位で。
        #太陽の方位が物体とソーラーの角度内に入っているかつ影の長さがソーラーと物体の距離の平均長より長ければ
        return "kage" 
    else:
        return "nokage"


#水平全天日射量から傾斜面日射量を算出する関数
def KeishaNissha(Ido,Keido,J,Ts,θa,X,H,kage_x,kage_y,kage_h,kage_Φ):#J:1/1から通算日数,Ts:その時間,θa:パネル角度,X:パネル方位,H:水平面日射量
    θ = Keido #東経
    φ = Ido #北緯
    pi = math.pi
    ω = 2*pi/365
    r = 1/( 1.000110 + 0.034221*math.cos(ω*J) + 0.001280*math.sin(ω*J) + 0.000719*math.cos(2*ω*J) + 0.000077*math.sin(2*ω*J))**0.5
    #太陽赤緯(時刻は関係無し)
    δ = 0.33281-22.984*math.cos(ω*J) - 0.34990*math.cos(2*ω*J) - 0.13980*math.cos(3*ω*J)+ 3.7872* math.sin(ω*J) + 0.03250*math.sin(2*ω*J) + 0.07187*math.sin(3*ω*J)
    """
    print('r:',r)
    print('太陽赤緯：',round(δ,2)) 
    """
    e = 0.0072*math.cos(ω*J) - 0.0528*math.cos(2*ω*J ) - 0.0012*math.cos(3*ω*J)- 0.1229 *math.sin(ω*J) - 0.1565*math.sin(2*ω*J) - 0.0041*math.sin(3*ω*J)
    T = Ts + (θ-135)/15 +e #eは均時差
    t = 15*T - 180
    δ = δ / 180 * pi #太陽赤緯をラジアン表記へ
    t = t / 180 * pi #時角をラジアン表記へ
    φ = φ / 180 * pi #緯度をラジアン表記へ
    #print(φ,δ,t)
    α = math.asin(math.sin(φ)*math.sin(δ) + math.cos(φ)*math.cos(δ)*math.cos(t))
    H0 = 1.367 * (1/r)**2*math.sin(α) #単位はkW
    """
    print('時角：',round(t*180/pi,2)) 
    print('高度：',round(α*180/pi,2)) 
    print('大気外全天日射量:',round(H0,2),'kW')
    """
    #H = Hb + Hd
    #水平面全天日射量を直達成分（水平面直達日射量）と散乱成分（水平面散乱日射量）に分離する。
    #Hbが直達成分、Hdが散乱成分
    if (H/H0) < 0.22:
        #print('H/H0 < 0.22')
        Hd = H - 0.09*H*H/H0
    if 0.22 < (H/H0) <= 0.80:
        #print('0.22 < H/H0 <= 0.80')
        Hd = 0.9511*H - 0.1604*H**2/H0 +4.388*H**3/(H0)**2- 16.638*H**4/(H0)**3 + 12.366*H**5/(H0)**4
    if (H/H0) > 0.80:
        #print('H/H0 > 0.80')
        Hd = 0.165 * H

    Hb = H - Hd
    #print('H:',H,'Hb:',Hb,'Hd:',Hd)
    θa = θa/180 * pi #パネル角度をラジアン表記へ
    p = 0.2 #アルベド
    X = X/180 *pi #ラジアン表記へ
    cosθz = math.sin(φ)*math.sin(δ) + math.cos(φ)*math.cos(δ)*math.cos(t)
    θz = math.acos(cosθz)
    cosθ1 =(math.sin(φ)*math.cos(θa) - math.cos(φ)*math.sin(θa)*math.cos(X))*math.sin(δ) + (math.cos(φ)*math.cos(θa) + math.sin(φ)*math.sin(θa)*math.cos(X))*math.cos(δ)*math.cos(t) + math.cos(δ)*math.sin(θa)*math.sin(X)*math.sin(t)
    θ1 = math.acos(cosθ1)
    """
    print('α:',round(α*180/pi,2))
    print('θz:',round(θz*180/pi,2))
    print('θa:',round(θa*180/pi,2))
    print('θ1:',round(θ1*180/pi,2))
    print('cos(θ1):',round(math.cos(θ1),2))
    print('cos(θz):',round(math.cos(θz),2))
    """
    #方位考慮無しの斜面直達日射量（直接法モデル）
    #hb = Hb*(math.cos(θ1)/math.cos(θz))
    #太陽の方位
    A_x = math.cos(δ)*math.sin(t)/math.cos(α)
    A_y = (math.sin(α)*math.sin(φ) - math.sin(δ))/math.cos(α)/math.cos(φ)
    A = math.atan2(A_x , A_y) #とりあえず傾斜面日射量に対してはpi無しが正解
    #方位考慮有りの傾斜直達日射量
    bunshi = math.sin(α)*math.cos(θa) +math.cos(α)*math.sin(θa)*math.cos(X-A)
    bunbo = math.sin(φ)*math.sin(δ)+math.cos(φ)*math.cos(δ)*math.cos(t)
    hb =Hb*(bunshi / bunbo)
    #print('太陽方位 A:',round(A *180 /pi,2))
    #斜面反射日射量（均一反射モデル）
    hr = H * ｐ*(1-math.cos(θa)) / 2
    #斜面散乱日射量（等方性モデル）
    hd = Hd*(1 + math.cos(θa)) / 2
    #影計算の前にここで低太陽高度時の補正をしておく。
    h = hb + hr + hd
    #print('方位無のh:',round(h,2),'hb:',round(hb,2),'hr:',round(hr,2),'hd',round(hd,2))
    #print('h:',round(hb+hr+hd,2),'hb:',round(hb,2),'hr:',round(hr,2),'hd',round(hd,2))
    #低太陽高度時の補正(hが異常値であれば、合意的な範囲に修正。保険として入れている)
    if H*0.6 < h < H*1.6:
        h = h
    if h <= H*0.6:
        h = H*0.9
    if H*1.6 <= h:
        h = H*1.1
    #hが異常値のときhbが異常であるため、影の時hb=0としても問題無い。
    α = α*180/pi #度単位へ変換
    A = A*180/pi+180 #度単位へ変換と180度ずらす
    kage=KageHandan(α,A,kage_x,kage_y,kage_h,kage_Φ)
    if kage == 'kage':
        #print('時間:',Ts,'影！！！！！！！！！！！！')
        #print('h:',round(hb+hr+hd,2),'hb:',round(hb,2),'hr:',round(hr,2),'hd',round(hd,2))
        h = hr + hd
    elif kage =='nokage':
        #print('時間:',Ts,'影なし')
        #print('h:',round(hb+hr+hd,2),'hb:',round(hb,2),'hr:',round(hr,2),'hd',round(hd,2))
        h = h
    #print('h:',round(h,2))
    return round(h,5)
"""影検証用
J =30
Ts =16
H = 0.53
θa =10
X=0
KeishaNissha(Ido,Keido,J,Ts,θa,X,H)
"""
#メインの関数
def calc_generation(Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,rekka,ΔT,kasekisai,effi_PCS,effi_trans,loss_haisen_teikaku,kage_x,kage_y,kage_h,kage_Φ):
    API_KEY = "3f21c45b9d939bd765ae3e6d39d98278"
    api = "http://api.yumake.jp/2.1/forecastMsm.php?lat={緯度}&lon={経度}&key={APIキー}&format={形式名}&callback={callback関数名}"
    url = api.format(緯度=Ido,経度=Keido, APIキー=API_KEY,形式名="json",callback関数名="test") 
    response = requests.get(url)
    #json形式にするための微修正（textだけでは、冒頭と後ろに余計なものが付いている）
    r = response.text.replace('test(', '')
    r2 = r.replace(');','')
    #json形式として一時保存
    with open('json形式一時保存.json', 'w') as f:
        print(r2, file=f)
    #ファイルをオープンしてdataにjson形式としてロード
    f = open("json形式一時保存.json","r",encoding="utf-8")
    data= json.load(f)

    df = pd.DataFrame()

    for value in data['forecast']:
        keys = []
        vals = []
        for k, v in value.items():
            keys.append( k )
            vals.append( v )
        tmp_se = pd.Series( vals, index=keys )
        df = df.append( tmp_se, ignore_index=True )

    df = df.rename(columns={'forecastDateTime': '予報時刻', 'weather': '天気','windDir':'風向','windSpeed':'風速','precipitation':'降水量','temperature':'気温','meanSeaLevelPressure':'海面更正気圧','relativeHumidity':'湿度','lcdc':'下層雲量','mcdc':'中層雲量','hcdc':'上層雲量','tcdc':'全層雲量','solarRadiation':'日射量','windDirStr':'風向16方位'})
    df = df.drop([0,1,2])
    df = df.reset_index(drop=True)
    df['予測時刻'] = now.strftime('%Y%m%d_%H%M') 
    ΔT_jisseki=18.4
    df['温度補正係数'] = 1-(df['気温']+ΔT_jisseki-25)*0.31/100
    #print(df['予報時刻'])
    θa = panel_kakudo
    X = panel_houi

    data_keishanisha = []
    for time,suihei in zip(df['予報時刻'],df['日射量']):
        s = time.replace('+09:00','')
        s = s.replace(s[10],' ')
        dt_now = datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
        dt1 = datetime.date(year=dt_now.year, month=1, day=1)
        td = dt_now.date() - dt1 #datetime.timedelta型
        J =td.days +0.5 #これでint型になっている
        Ts = dt_now.hour
        ####ここに影計算プログラムを入れる。インプットは、J,Ts
        H = suihei/1000 #kW/㎡単位へ 
        keishanisha = KeishaNissha(Ido,Keido,J,Ts,θa,X,H,kage_x,kage_y,kage_h,kage_Φ)#J:1/1から通算日数,Ts:その時間,θa:パネル角度,X:パネル方位,H:水平面日射量
        data_keishanisha.append(keishanisha)

    df['傾斜面日射量'] =data_keishanisha

    #学習元ファイルも同じディレクトリにいれている。   
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    df_data = pd.read_csv('発電実績_福岡宮城青森.csv',encoding="shift_jis")

    #df = df.fillna(0)
    df_data = df_data.dropna(how='any')
    #ドロップするIndexを取得→明らかな異常値のドロップ
    drop_index_high = df_data.index[(df_data['日射量 [kW/m2]'] <0.6) | (df_data['日射量 [kW/m2]']/df_data['DC電力[kW/kWp]']>1.5)| (df_data['日射量 [kW/m2]']/df_data['DC電力[kW/kWp]']<0.8)]
    drop_index_mid = df_data.index[(df_data['日射量 [kW/m2]'] <0.1 )| (df_data['日射量 [kW/m2]'] >0.6) | (df_data['日射量 [kW/m2]']/df_data['DC電力[kW/kWp]']>1.5)| (df_data['日射量 [kW/m2]']/df_data['DC電力[kW/kWp]']<0.8)]
    drop_index_low = df_data.index[ (df_data['日射量 [kW/m2]'] >0.1) | (df_data['日射量 [kW/m2]']/df_data['DC電力[kW/kWp]']>1.5)| (df_data['日射量 [kW/m2]']/df_data['DC電力[kW/kWp]']<0.8)]
    #条件にマッチしたIndexを削除(ドロップ)
    df_data_high = df_data.drop(drop_index_high)
    df_data_mid = df_data.drop(drop_index_mid)
    df_data_low = df_data.drop(drop_index_low)
    x_high = df_data_high.iloc[:,[10,12]] #説明変数の設定 10番目=日射量、12番目=温度補正係数
    y_high = df_data_high.iloc[:,11] #目的関数の設置。11番目=DC発電量[kW\kWp]
    x_mid = df_data_mid.iloc[:,[10,12]] #説明変数の設定 10番目=日射量、12番目=温度補正係数
    y_mid = df_data_mid.iloc[:,11] #目的関数の設置。11番目=DC発電量[kW\kWp]
    x_low = df_data_low.iloc[:,[10,12]] #説明変数の設定 10番目=日射量、12番目=温度補正係数
    y_low = df_data_low.iloc[:,11] #目的関数の設置。11番目=DC発電量[kW\kWp]
    # 学習用データとする
    x_train_high = x_high
    y_train_high = y_high
    x_train_mid = x_mid
    y_train_mid = y_mid
    x_train_low = x_low
    y_train_low = y_low

    # 学習 直線回帰
    model_high = LinearRegression(normalize=True)
    model_high.fit(x_train_high, y_train_high)
    model_mid = LinearRegression(normalize=True)
    model_mid.fit(x_train_mid, y_train_mid)
    model_low = LinearRegression(normalize=True)
    model_low.fit(x_train_low, y_train_low)
    #予測する。ここで格納。配線ロスの関数の呼び出し。
    data = []
    for nissha,ondohosei in zip(df['傾斜面日射量'],df['温度補正係数']):
        x_test = [[nissha,ondohosei]]
        if nissha > 0.6:
            data.append(HaisenLoss(sum(model_high.predict(x_test)),pv_yoryo,rekka,ΔT,kasekisai,effi_PCS,effi_trans,loss_haisen_teikaku))
        if 0.1 <= nissha <=0.6:
            data.append(HaisenLoss(sum(model_mid.predict(x_test)),pv_yoryo,rekka,ΔT,kasekisai,effi_PCS,effi_trans,loss_haisen_teikaku))
        if 0.005 < nissha <0.1:
            data.append(HaisenLoss(sum(model_low.predict(x_test)),pv_yoryo,rekka,ΔT,kasekisai,effi_PCS,effi_trans,loss_haisen_teikaku))
        if nissha <= 0.005:#ゼロ発電量の閾値を0.005kW/㎡に設定
            data.append(0)

    df['予測発電量[kWh/kW]'] =data
    data = []

    for time in df['予報時刻']:
        s = time.replace('+09:00','')
        s = s.replace(s[10],' ')
        dt_now = datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')#この時点ではdatetime型
        #dt_now = dt.fromtimestamp(dt_now) #unixtimeになっているので、通常日時へ変換。
        data.append(dt_now)

    df['予報時刻']=data

    df_x = pd.DataFrame()
    num = len(df)
    data=[]
    data_2=[]
    data_3=[]
#ここで配線ロス関数を使ってしまうと、二重に計算することになってしまう。
    for i in range(num):
        data.append(round(df.iat[i,18],2))
        data_2.append(round(df.iat[i,17],2))
        if i<num-1:
            if df.iat[i,18] <= df.iat[i+1,18]:#日射量増加傾向のとき
                if df.iat[i,9] <= df.iat[i+1,9]:#雲量が多くなるのであれば、
                    data.append(round((df.iat[i,18]*2+df.iat[i+1,18])/3,2))
                    data_2.append(round((df.iat[i,17]*2+df.iat[i+1,17])/3,2))
                else:#雲量が少なくなるのであれば、
                    data.append(round((df.iat[i,18]+df.iat[i+1,18]*2)/3,2))
                    data_2.append(round((df.iat[i,17]+df.iat[i+1,17]*2)/3,2))
            if df.iat[i,18] > df.iat[i+1,18]:#日射量減少傾向のとき
                if df.iat[i,9] <= df.iat[i+1,9]:#雲量が多くなるのであれば、
                    data.append(round((df.iat[i,18]*2+df.iat[i+1,18])/3,2))
                    data_2.append(round((df.iat[i,17]*2+df.iat[i+1,17])/3,2))
                else:#雲量が少なくなるのであれば、
                    data.append(round((df.iat[i,18]+df.iat[i+1,18]*2)/3,2))
                    data_2.append(round((df.iat[i,17]+df.iat[i+1,17]*2)/3,2))

    for i in range(num):
        data_3.append(df.iat[i,0])
        if i<num-1:
            data_3.append(df.iat[i,0]+datetime.timedelta(hours=0.5))
            #これはtimestamp型＝pandasの中でのdatetime型のようなもの。
            #print(type(df.iat[i,0]+datetime.timedelta(hours=0.5)))
    #予報時刻=exectution date and time,予測時刻=predictated date and time
    
    df_x['予測時刻'] = data_3 
   # df_x['predictated date and time'] = now.strftime('%Y%m%d_%H%M') 
    #df_x['予測傾斜日射量(kW/m2)']=data_2
    df_x['予測値_PV'] = data
    df_x['予報時刻'] = now.strftime('%Y%m%d_%H%M') 
    #df_x =df_x.set_index('予測時刻')

    return df_x
