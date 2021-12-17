from numpy.lib.type_check import typename
import pandas as pd
import pulp
import numpy as np
import os
import japanize_matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta, timezone

pd.set_option("display.max_rows", 101)
now = datetime.now()

def merge(pv_yosoku,demand_yosoku,jepx_jisseki):#全てのdfのindexを予測時刻で統一してinputする
    df = pd.merge(pv_yosoku, demand_yosoku,on='予測時刻',how='inner')#innerで処理
    df = pd.merge(df,jepx_jisseki,on='予測時刻',how='inner')#innerで処理
    return df

def maltiplication(x,y):#汎用的な関数として
    z = []
    for i , j in zip(x,y):
        z.append(i*j)
    return z


#ソルバーへの入力は①需要電力予測値,②PV予測値,③JEPX価格,
#これを実行する時刻は1日かつ固定。例えば、22:00(わき上げ開始基準時刻という意味を理解しないといけない！！)
#返す値は、シフトをするか否かとシフトする場合は、昼間のわき上げ開始時刻(9:00～17:00)
def solver_residential_ElecWaterHeater(df_yosoku,heating_basetime):#引数はリストではなく、dataframeとすべき。
    #前準備
    #ここでインデックスを統一して、Nanのある行は削除などをする
    df_yosoku['予測値_PV(kWh)']=df_yosoku['予測値_PV']/2           #ここでkWhへ変換!!!!
    df_yosoku['予測値_demand(kWh)'] = df_yosoku['予測値_demand']/2 #ここでkWhへ変換!!!!
    pv = df_yosoku['予測値_PV(kWh)'].values.tolist()#kWなのかkWhなのか？？？？
    juyou = df_yosoku['予測値_demand(kWh)'].values.tolist()#kWなのかkWhなのか？？？？？
    jepx = df_yosoku['エリアプライス東京(円/kWh)'].values.tolist()
    print(df_yosoku)
    df_yosoku.index = pd.to_datetime(df_yosoku.index)#tolistを使うとunixに変わってしまう
    time=[]
    for i in df_yosoku.index:
        time.append(i.to_pydatetime())#to_pydatetime()が無いとtimestamp型になる。あるとdatetime型
    
    #最初にノンインセンティブを与える
    list_jepx_nonincentive = calc_ElecWaterHeater_NONincetive(df_yosoku)

    #予測需要電力から予測PV発電量を引いたものをjudenとする。
    juden =[]
    for i,j in zip(juyou,pv):
        juden.append(round(i-j,2))

    #その日のJEPX価格の平均値との差異をコマ毎にとって格納する
    #最適化計算には使わないが、グラフ表示に使うので、残しておく
    jepx_ave = np.mean(jepx)
    jepx_ave_difference= [] 
    for i in jepx:
        jepx_ave_difference.append(round(jepx_ave - i,2))


    #卒FIT住宅は自家消費のインセンティブを高くする
    jikashohi_incentive = 25 #単位は円/kWh
    Heater_kwh = 1.0 / 2 #消費電力(kWh)
    jepx_jikaince_Elecnonince_diffirence = calc_ElecWater_jikashohi_incetive(df_yosoku,jikashohi_incentive,list_jepx_nonincentive,Heater_kwh)


    #pulpを含むsolverを呼び出して、最適化で算出された結果をbatt_outinに格納する
    shift_judge,heating_on_off,status = pulp_residential_ElecWaterHeater(juden,pv,jepx_ave,jepx_jikaince_Elecnonince_diffirence,heating_basetime,time,Heater_kwh)

    #変数から、中身を取り出し
    heating_on_off_fig = list(round(c.value(),2) for c in heating_on_off)

    df = pd.DataFrame({'時刻':time,'オンの時刻':heating_on_off_fig,'発電量':df_yosoku['予測値_PV(kWh)']})
    print(df)
    print(df['オンの時刻'].sum())
    #結果をきれいにしてくれる関数    
    df = cleanliness_residetial_ElecWaterHeater(juden,df_yosoku,heating_on_off_fig,jepx_ave_difference,jepx_jikaince_Elecnonince_diffirence,Heater_kwh)
    print(df)

    return df,status


def pulp_residential_ElecWaterHeater(juden,pv,jepx_ave,jepx_jikaince_Elecnonince_diffirence,heating_basetime,time,Heater_kwh):
    size = len(pv)#pvでも、judenでも同じ長さのはず
    #蓄電池関連データ
    
    heating_basetime = 22 #夜の何時か？
    normal_heating_duration = 8#夜間だけでわき上げするときに要する時間(何時間わき上げるか)
    daytime_heating_duration = 4#日中にシフトするときのわき上げ時間（何時間わき上げるか）
    nighttime_heating_duration = normal_heating_duration - daytime_heating_duration
    
    juden_mae_max = np.max(juden)
    #最大化と定義
    prob = pulp.LpProblem('sample',sense = pulp.LpMaximize)
    
    #daytime_heating_starttime = pulp.LpVariable('daytime_heating_starttime',lowBound = 9, upBound = 17,cat='Integer')
    #heating_on_off = [pulp.LpVariable('a{}'.format(i),lowBound = 0, upBound = 1,cat='Integer') for i in range(size)]
    heating_on_off = [pulp.LpVariable('a{}'.format(i),cat='Binary') for i in range(size)]
    #z_bat = [pulp.LpVariable('z_bat{}'.format(i),lowBound = 0,cat='Continuous') for i in range(size)]
    #z変数については、こちらを参照。http://www.nct9.ne.jp/m_hiroi/light/pulp07.html

    #heating_on_offを考慮した後の受電電力（これだと変数が引っ付いて来てくれる）
    juden_ato = []

    #Heater_kwhをちゃんと考慮する必要あり。heating_on_offは0,1でしかない
    for i,j in zip (juden,heating_on_off):
        juden_ato.append(i + j * Heater_kwh)

    #heating_on_offのそこまでの総和が入ったリストを作る。
    sum_on = []
    sum_on = [sum(heating_on_off[:i+1]) for i in range(len(heating_on_off))]

    ##################制約条件#####################
    #1.オンの時間の総和は８時間→sum_onの最後のコマが翌日の24時までのオンの数
    prob += sum_on[len(sum_on)-1] == normal_heating_duration * 2 #1コマ30分なので×2
    
    #2.当日のheating_basetimeから4時間は絶対にオン
    #今のところ、heating_basetimeが23時、22時など翌日ではないものしか対応していない。。
    today = now.date()
    tomorrow = today + timedelta(days=1)
    #01:30=01:00～01:30だということに留意!
    for heating_on,time in zip(heating_on_off,time):
        if time.date() == today:#当日分の設定
            for i in range(24-heating_basetime):
                if time.hour == heating_basetime + i and time.minute==30:#23:30までしか処理できない
                    prob += heating_on == 1
                if time.hour == heating_basetime + i+1 and time.minute==0:#23:00までしか処理できない
                    prob += heating_on == 1
        elif time.date() == tomorrow:#翌日 = 00:30(=00:00～00:30)以降のコマの設定だが、前日24:00も翌日00:00なのでこちらで処理
            for i in range(nighttime_heating_duration-(24-heating_basetime)):
                if time.hour ==  0+i and time.minute==30:#
                    prob += heating_on == 1
                if time.hour ==  0+i+1 and time.minute==0:
                    prob += heating_on == 1
                if time.hour ==  0 and time.minute==0:#翌日00:00の処理
                    prob += heating_on == 1
    #3.そのままオンにし続けるか？9:00～17:00でスタート時間を選択する。連続daytime_heating_duration時間が制約条件
    #→結果をみて後で判断
    
    print(jepx_jikaince_Elecnonince_diffirence)
    #目的関数
    #PuLPでは目的関数や制約条件の定義に max() やabs()を使用できない!!!
    #lpSumはリストの各要素の総和
    prob += pulp.lpSum(maltiplication(juden_ato,jepx_jikaince_Elecnonince_diffirence)) 
    #これを最大化しようする。

    status = prob.solve()
    shift_judge =1 

    return shift_judge,heating_on_off,status

def calc_ElecWater_jikashohi_incetive(df_yosoku,jikashohi_incentive,list_jepx_nonincentive,Heater_kwh):
    #######卒FIT住宅は自家消費のインセンティブを高くする#######
    #エコキュートの場合、エコキュートの消費電力が、「PV発電量(+)-エコキュート以外の消費電力(+)」を超える分は買電となる
    #そのため、超えた分は自家消費インセンティブを無くす
    print(df_yosoku)
    jepx_incentive=[]#PV発電量がある時間帯は一律,自家消費インセンティブ分、引く。df_pv_jepxがpv発電量予測とjepx予測が並んだDataFrame
    #jikashohi_incentive = 15 #単位は円/kWh
    
    for pv,demand,price in zip(df_yosoku['予測値_PV(kWh)'],df_yosoku['予測値_demand(kWh)'],list_jepx_nonincentive):
        if pv==0:
            jepx_incentive.append(price)
        if pv>0:
            if Heater_kwh > (pv-demand):#エコキュートわき上げ消費電力が買電につながる場合
                jepx_incentive.append(price-jikashohi_incentive +(Heater_kwh-(pv-demand))*price)
            else:
                jepx_incentive.append(price-jikashohi_incentive)
    
    jepx_incentive_ave = np.mean(jepx_incentive)
    
    jepx_jikaince_Elecnonince_diffirence=[]
    for i in jepx_incentive:
        jepx_jikaince_Elecnonince_diffirence.append(round(jepx_incentive_ave - i,2))
    
    return jepx_jikaince_Elecnonince_diffirence

def calc_ElecWaterHeater_NONincetive(df_yosoku):
    #######5:00～9:00=05:30～09:00の8コマに対して入れさせないインセンティブを与える#######
    non_incentive =[]
    for time,price in zip(df_yosoku.index,df_yosoku['エリアプライス東京(円/kWh)']):
        if time.hour ==5 and time.minute==30:
            print(time)
            non_incentive.append(price + 100)
        elif time.hour ==6 or time.hour ==7 or time.hour ==8:
            print(time)
            non_incentive.append(price + 100)
        elif time.hour ==9 and time.minute==00:
            print(time)
            non_incentive.append(price + 100)
        else:
            non_incentive.append(price)

    return non_incentive

def cleanliness_residetial_ElecWaterHeater(juden,df_yosoku,heating_on_off_fig,jepx_ave_difference,jepx_jikaince_Elecnonince_diffirence,Heater_kwh):
    juden_ato_opt = []
    for i,j in zip (juden,heating_on_off_fig):
        juden_ato_opt.append(round(i + j * Heater_kwh,2))
    #listをシリーズに変えていく
    koma = pd.Series(list(df_yosoku.index)) #インデックスはindexで取得する
    #heating_on_off_figは0,1でしかないので、
    heating_on_off_kwh=[]
    for i in heating_on_off_fig:
        heating_on_off_kwh.append(i*Heater_kwh)
    
    heating_on_off_kwh = pd.Series(heating_on_off_kwh)
    jepx = pd.Series(jepx_ave_difference)
    juden_mae = pd.Series(juden)
    juden_ato = pd.Series(juden_ato_opt)
    jepx_jikaince_Elecnonince_diffirence = pd.Series(jepx_jikaince_Elecnonince_diffirence)
    df = pd.DataFrame()
    df['コマ'] = koma
    df = df.set_index('コマ')
    df_1 = pd.concat([koma,juden_mae,heating_on_off_kwh,juden_ato,jepx,jepx_jikaince_Elecnonince_diffirence], axis=1)
    df_1 = df_1.rename(columns={0:'コマ',1:'前_受電電力',2:'エコキュート',3:'最適後_受電電力',4:'JEPX平均差額',5:'JEPX平均差額(自家消費動機など有)'})
    df_1 = df_1.set_index('コマ')
    df = pd.concat([df,df_1],axis=1)
    df = pd.concat([df,df_yosoku['予測値_demand(kWh)'],df_yosoku['予測値_PV(kWh)'],df_yosoku['エリアプライス東京(円/kWh)']],axis=1)
    df = df.rename(columns={'予測値_demand(kWh)':'予測_需要電力(kWh)','予測値_PV(kWh)':'予測_PV(kWh)','エリアプライス東京(円/kWh)':'実績_JEPX'})
    df = df.dropna(how='any')#1つでもNanの要素がある行を削除

    return df

def graph_residential_ElecWaterHeater(df):
    #グラフにしたいカラムを全部リストにしてしまう。
    koma = df.index.tolist()#Series型からlistへの変換

    juden = df['前_受電電力'].values.tolist()#Series型からlistへの変換
    juden_ato = df['最適後_受電電力'].values.tolist()#Series型からlistへの変換
    ElecWaterHeater = df['エコキュート'].values.tolist()#Series型からlistへの変換
    jepx =df['実績_JEPX'].values.tolist()
    jepx_ave_difference = df['JEPX平均差額'].values.tolist()#Series型からlistへの変換
    
    #平均より高い時をプラスにするため異符号にする
    jepx_ave_difference_2=[]
    for i in jepx_ave_difference:
       jepx_ave_difference_2.append(i*-1)
    jepx_ave_difference=jepx_ave_difference_2

    #平均より高い時をプラスにするため異符号にする
    jepx_jika = df['JEPX平均差額(自家消費動機など有)'].values.tolist()#Series型からlistへの変換
    jepx_jika_2=[]
    for i in jepx_jika:
       jepx_jika_2.append(i*-1)
    jepx_jika=jepx_jika_2
    
    pv = df['予測_PV(kWh)'].values.tolist()

    #描画用
    fig = plt.figure(figsize=(10,6),dpi=100)

    ax1 = fig.add_subplot(1, 1, 1)
    #ax1 = fig.add_subplot(2, 1, 1)#上下２つにグラフにしたいときの上のグラフ
    #ax2 = fig.add_subplot(2, 1, 2)#上下２つにグラフにしたいときの下のグラフ
    ax3 = ax1.twinx()
    plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')
    #plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')
    plt.setp(ax1.get_xticklabels(), fontsize=7)
    #plt.setp(ax2.get_xticklabels(), fontsize=7)

    ax1.grid(True)
    ax1.plot(juden,c='m',label="最適前_受電電力[kWh](-は逆潮流)")
    ax1.plot(juden_ato,c='m',label="最適後_受電電力[kWh](-は逆潮流)",linestyle="dashed")
    ax1.plot(pv,c='y',label="PV発電量[kWh]")

    koma_2=[]
    for i in koma:
        koma_2.append(str(i))
    ax1.bar(koma_2,ElecWaterHeater,color='red',label='エコキュート沸上げ')
    #ax3.plot(jepx_ave_difference,c='g',label="電力市場価格_日平均との差額(+が平均より高い)")
    ax3.plot(jepx,c='g',label="電力市場価格(円/kWh)")
    #ax3.plot(jepx_jika,c='g',label="JEPX_自家消費(+が平均より安い)",linestyle="dashed")
    
    size = len(koma_2)

    ax1.set_xlim(0,size) #x軸範囲指定

    #y軸の範囲を各項目の最大値×1.2で自動設定
    ##自家消費考慮なしのjepxの平均値の話
    max_jepx_ave_difference =  max(jepx_ave_difference)
    min_jepx_ave_difference = min(jepx_ave_difference)
    max_jepx_ave_difference = round(max_jepx_ave_difference*1.2)
    min_jepx_ave_difference = round(min_jepx_ave_difference*1.2)
    ##自家消費考慮ありのjepxの平均値の話
    max_jepx_jika =  max(jepx_jika)
    min_jepx_jika = min(jepx_jika)
    max_jepx_jika = round(max_jepx_jika * 1.2)
    min_jepx_jika = round(min_jepx_jika*1.2)
    #それぞれの絶対値が大きいほうを採用
    if max_jepx_ave_difference >= max_jepx_jika:
        max_jepx = max_jepx_ave_difference
    else:
        max_jepx = max_jepx_jika
    if min_jepx_ave_difference <= min_jepx_jika:
        min_jepx = min_jepx_ave_difference
    else:
        min_jepx = min_jepx_jika
    #y軸範囲指定においては、負の絶対値と正の絶対値は合わせておいた方がよいがわかりやすい
    if abs(max_jepx) >= abs(min_jepx):
        min_jepx = max_jepx*-1
    else:
        max_jepx = min_jepx *-1

    ax1.set_ylim(-2,2) #y軸範囲指定
    ax3.set_xlim(0,size) #x軸範囲指定
    #ax3.set_ylim(min_jepx,max_jepx) #y軸範囲指定(負の絶対値と正の絶対値は合わせておいた方がよい)
    ax3.set_ylim(0,20) #y軸範囲指定(負の絶対値と正の絶対値は合わせておいた方がよい)
    
    xlabel = 'コマ'
    ylabel = 'kWh'
    ax1.set_xlabel(xlabel,fontname="MS Gothic")#x軸の名前
    ax1.set_ylabel(ylabel,fontname="MS Gothic") #y軸の名前
    ax3.set_xlabel(xlabel,fontname="MS Gothic")#x軸の名前
    ax3.set_ylabel('円/kWh',fontname="MS Gothic") #y軸の名前
    ax1.legend(fontsize=8,loc='upper center') #凡例を入れるlocで場所、ない場合自動になる。'upper center'
    ax3.legend(fontsize=10)#凡例を入れる
    #plt.show()

    #ax2.figure(figsize=(10,6),dpi=100)
    #ax2.grid(True)
    #ax2.plot(koma_2,soc_ba,c='r',label="蓄電池充電率[%]")
    #ax2.plot(batt_losskouryo_2,c='r',label="充放電効率を考慮した蓄電池SOC[%]",linestyle="dashed")
    """
    ax2.set_xlim(0,size) #x軸範囲指定
    ax2.set_ylim(0,1) #y軸範囲指定
    xlabel = 'コマ'
    ylabel = 'SOC'
    ax2.set_xlabel(xlabel,fontname="MS Gothic")#x軸の名前
    ax2.set_ylabel(ylabel,fontname="MS Gothic") #y軸の名前
    ax2.legend()#凡例を入れる
    """
    fig.tight_layout() 
    plt.show()


def calc_SOC(batt_outin,SOC_batt_latest,df_info):
    #蓄電池関連データ
    batt_shoki = SOC_batt_latest #
    batt_youryo = df_info['値']['蓄電池_容量[kWh]']

    x = []
    y = []
    yotei_soc =[]

    x = [c.value() for c in batt_outin]
    y = [sum(x[:i+1]) for i in range(len(x))]

    for i in y:
        yotei_soc.append(round((batt_shoki*batt_youryo +i)/batt_youryo,3))

    return yotei_soc
