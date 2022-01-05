from numpy.lib.function_base import average
import pandas as pd
import pulp
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = "MS Gothic"
from datetime import datetime, date, timedelta


def merge(pv_pre,demand_pre,df_jepx):#全てのdfのindexを予測時刻で統一してinputする
    df = pd.merge(pv_pre, demand_pre,on='日時',how='inner')#innerで処理
    df = pd.merge(df,df_jepx,on='日時',how='inner')#innerで処理
    #print(df)
    return df

def maltiplication(x,y):#汎用的な関数として
    z = []
    for i , j in zip(x,y):
        z.append(i*j)
    return z


#ソルバーへの入力は①需要電力予測値,②PV予測値,③JEPX価格,④EV状態予測,⑤出力や容量など,⑥コマ毎の上限下限SOC
def solver_residential_battery(df_pre,capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,SOC_batt_latest,power_com):#引数はリストではなく、dataframeとすべき。
    #前準備
    #ここでインデックスを統一して、Nanのある行は削除などをする
    pv = df_pre['予測値_PV'].values.tolist()#元々kWh
    juyou = df_pre['予測値_demand'].values.tolist()#元々kWh
    jepx = df_pre['価格'].values.tolist()
    #print(len(pv))
    #print(len(juyou))
    #print(len(jepx))
    #予測需要電力から予測PV発電量を引いたものをjudenとする。
    juden =[]
    for i,j in zip(juyou,pv):
        juden.append(round(i-j,2))

    #その日のJEPX価格の平均値との差異をコマ毎にとって格納する
    jepx_ave = np.mean(jepx)
    jepx_ave_difference= [] 
    for i in jepx:
        jepx_ave_difference.append(round(jepx_ave - i,2))
    print('#########JEPXの平均値との差異#############')
    print(jepx_ave_difference)
    print('######################')

    #卒FIT住宅は自家消費のインセンティブを高くする
    jikashohi_incentive = 25 #単位は円/kWh
    jepx_incentive_diffirence = calc_jikashohi_incetive(df_pre,jikashohi_incentive,power_com)
    print('#########JEPX自家消費インセンティブを含めた平均値との差異#############')
    print(jepx_incentive_diffirence)
    print('######################')
    #pulpを含むsolverを呼び出して、最適化で算出された結果をbatt_outinに格納する
    batt_outin,status = pulp_residential_battery(juden,pv,jepx_ave,jepx_incentive_diffirence,capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,SOC_batt_latest)
        
    #最適化された充放電に基づくSOC値の計算（制約条件とは独立して算出）
    yotei_soc = calc_SOC(batt_outin,SOC_batt_latest,capacity_batt)#各コマの充放電予定量から各コマの予定SOCを算出
    
    #変数から、中身を取り出し
    batt_outin_fig = list(round(c.value(),2) for c in batt_outin)

    #結果をきれいにしてくれる関数    
    df = cleanliness_residetial_battery(capacity_batt,effi_batt,juden,df_pre,SOC_batt_latest,batt_outin_fig,yotei_soc,jepx_ave_difference,jepx_incentive_diffirence,power_com)

    return df,status

def graph_residential_battery(df,power_com):
    #グラフにしたいカラムを全部リストにしてしまう。
    #print(df)
    koma = df.index.tolist()#Series型からlistへの変換
    juden = df['前_受電電力'].values.tolist()#Series型からlistへの変換
    juden_ato = df['最適後_受電電力'].values.tolist()#Series型からlistへの変換
    batt_outin = df['蓄電池_充放電量'].values.tolist()#Series型からlistへの変換
    jepx =df['価格'].values.tolist()
    jepx_ave_difference = df['JEPX平均差額'].values.tolist()#Series型からlistへの変換
    
    #平均より高い時をプラスにするため異符号にする
    jepx_ave_difference_2=[]
    for i in jepx_ave_difference:
       jepx_ave_difference_2.append(i*-1)
    jepx_ave_difference=jepx_ave_difference_2

    #平均より高い時をプラスにするため異符号にする
    jepx_jika = df['JEPX平均差額(自家消費動機有)'].values.tolist()#Series型からlistへの変換
    jepx_jika_2=[]
    for i in jepx_jika:
       jepx_jika_2.append(i*-1)
    jepx_jika=jepx_jika_2
    
    soc_ba = df['蓄電池SOC'].values.tolist()#Series型からlistへの変換
    batt_losskouryo_2 = df['蓄電池SOC_充放電ロス考慮'].values.tolist()#Series型からlistへの変換
    pv = df['予測_PV(kWh)'].values.tolist()

    #描画用
    fig = plt.figure(figsize=(10,6),dpi=100)
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)
    ax3 = ax1.twinx()
    plt.setp(ax1.get_xticklabels(), rotation=30, ha='right')
    plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')
    plt.setp(ax1.get_xticklabels(), fontsize=7)
    plt.setp(ax2.get_xticklabels(), fontsize=7)

    ax1.grid(True)
    ax1.plot(juden,c='m',label="最適前_受電電力[kWh](-は逆潮流)")
    ax1.plot(juden_ato,c='m',label="最適後_受電電力[kWh](-は逆潮流)",linestyle="dashed")
    ax1.plot(pv,c='y',label="PV発電量[kWh]")

    koma_2=[]
    for i in koma:
        koma_2.append(str(i))
    ax1.bar(koma_2,batt_outin,color='red',label='蓄電池_出力[kWh](+が充電)')
    #ax3.plot(jepx_ave_difference,c='g',label="電力市場価格_日平均との差額(+が平均より高い)")
    ax3.plot(jepx,c='g',label="JEPX(円/kWh)_"+power_com)
    #ax3.plot(jepx_jika,c='g',label="JEPX_自家消費(+が平均より安い)",linestyle="dashed")
    
    size = len(koma_2)

    ax1.set_xlim(0,size) #x軸範囲指定
    """
    #y軸の範囲を各項目の最大値×1.2で自動設定
    ##自家消費考慮なしのjepxの平均値の話
    max_jepx_ave_difference =  max(jepx_ave_difference)
    min_jepx_ave_difference = min(jepx_ave_difference)
    max_jepx_ave_difference = round(max_jepx_ave_difference*1.2)
    min_jepx_ave_difference = round(min_jepx_ave_difference*1.2)
    ##自家消費考慮ありのjepxの平均値の話
    max_jepx_jika =  max(jepx_jika)
    min_jepx_jika = min(jepx_jika)
    max_jepx_jika = round(max_jepx_jika * 1.1)
    min_jepx_jika = round(min_jepx_jika*1.1)
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
    """

    min_jepx = min(jepx)
    max_jepx = max(jepx)
    ave_jepx = average(jepx)

    if abs(max_jepx-ave_jepx) >= abs(ave_jepx - min_jepx):
        max_y_axis = ave_jepx + abs(max_jepx-ave_jepx)
        min_y_axis = ave_jepx - abs(max_jepx-ave_jepx)
    else:
        max_y_axis = ave_jepx + abs(ave_jepx - min_jepx)
        min_y_axis = ave_jepx - abs(ave_jepx - min_jepx)

    ax1.set_ylim(-2,2) #y軸範囲指定
    ax3.set_xlim(0,size) #x軸範囲指定
    #ax3.set_ylim(min_jepx,max_jepx) #y軸範囲指定(負の絶対値と正の絶対値は合わせておいた方がよい)
    ax3.set_ylim(min_y_axis,max_y_axis) #y軸範囲指定(負の絶対値と正の絶対値は合わせておいた方がよい)
    
    xlabel = 'コマ'
    ylabel = 'kWh'
    ax1.set_xlabel(xlabel,fontname="MS Gothic")#x軸の名前
    ax1.set_ylabel(ylabel,fontname="MS Gothic") #y軸の名前
    ax3.set_xlabel(xlabel,fontname="MS Gothic")#x軸の名前
    ax3.set_ylabel('円/kWh',fontname="MS Mincho") #y軸の名前
    ax1.legend(fontsize=8,loc='upper center') #凡例を入れるlocで場所、ない場合自動になる。'upper center'
    ax3.legend(fontsize=10)#凡例を入れる

    ax3.FontName = 'Times New Roman'
    #plt.show()

    #ax2.figure(figsize=(10,6),dpi=100)
    ax2.grid(True)
    ax2.plot(koma_2,soc_ba,c='r',label="蓄電池充電率[%]")
    #ax2.plot(batt_losskouryo_2,c='r',label="充放電効率を考慮した蓄電池SOC[%]",linestyle="dashed")

    ax2.set_xlim(0,size) #x軸範囲指定
    ax2.set_ylim(0,1) #y軸範囲指定
    xlabel = 'コマ'
    ylabel = 'SOC'
    ax2.set_xlabel(xlabel,fontname="MS Gothic")#x軸の名前
    ax2.set_ylabel(ylabel,fontname="MS Gothic") #y軸の名前
    ax2.legend()#凡例を入れる
    fig.tight_layout() 
    plt.show()


def calc_SOC(batt_outin,SOC_batt_latest,capacity_batt):
    #蓄電池関連データ
    batt_shoki = SOC_batt_latest #
    batt_youryo = capacity_batt

    x = []
    y = []
    yotei_soc =[]

    x = [c.value() for c in batt_outin]
    y = [sum(x[:i+1]) for i in range(len(x))]

    for i in y:
        yotei_soc.append(round((batt_shoki*batt_youryo +i)/batt_youryo,3))

    return yotei_soc

def pulp_residential_battery(juden,pv,jepx_ave,jepx_incentive_diffirence,capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,SOC_batt_latest):
    size = len(pv)#pvでも、judenでも同じ長さのはず
    #蓄電池関連データ
    batt_shoki = SOC_batt_latest #
    batt_SOC_L = minSOC_batt
    batt_SOC_U = maxSOC_batt
    batt_effi = 1 - effi_batt # 1-としていることに注意!!!
    batt_power_hou = outputpower_batt/2#kWhにするために÷2
    batt_power_juu = inputpower_batt/2#kWhにするために÷2
    batt_youryo = capacity_batt

    #print(batt_shoki,batt_SOC_L,batt_SOC_U,batt_effi,batt_power_hou,batt_power_juu,batt_youryo)

    juden_mae_max = np.max(juden)
    #最大化と定義
    prob = pulp.LpProblem('sample',sense = pulp.LpMaximize)
    print('Pulp実行中１：AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    #リスト形式で変数を定義。
    #print('蓄電池の下限出力：',batt_power_hou)
    #print('蓄電池の上限出力：',batt_power_juu)
    batt_outin = [pulp.LpVariable('a{}'.format(i),lowBound = batt_power_hou, upBound = batt_power_juu,cat='Continuous') for i in range(size)]
    z_bat = [pulp.LpVariable('z_bat{}'.format(i),lowBound = 0,cat='Continuous') for i in range(size)]
    #z変数については、こちらを参照。http://www.nct9.ne.jp/m_hiroi/light/pulp07.html
    print('Pulp実行中２：BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')

    juden_ato = []
    #batt_outinを考慮した後の受電電力（これだと変数が引っ付いて来てくれる）
    for i,j in zip (juden,batt_outin):
        juden_ato.append(i + j)

    #batt_inoutのそこまでの総和が入ったリストを作る。
    soc_batt = []
    soc_batt = [sum(batt_outin[:i+1]) for i in range(len(batt_outin))]

    ##################制約条件#####################
    #1.SOCに対する制約
    for x in soc_batt:#一旦充放電ロス無視して。#上限SOCと下限SOCを仕様から拾ってくるタイプ.。
        prob += (batt_shoki*batt_youryo + (x))/batt_youryo <= batt_SOC_U
        prob += (batt_shoki*batt_youryo + (x))/batt_youryo >= batt_SOC_L
    #2.予測の受電電力がゼロ以下であれば、蓄電池は放電しない(=充電してよい)という制約
    for x,y in zip(juden,batt_outin):
        if x<=0:
            prob +=y >=0
    #3.「予測受電電力がゼロより大きく」かつ「PVがゼロのとき」は受電電力がゼロまでは放電してよい
    for x,y,z in zip(juden,pv,juden_ato):
        if x>0 and y==0:
            prob += z>=0
    #4.PVがゼロより大きければであれば、蓄電池は放電しないという制約
    for x,y in zip(pv,batt_outin):
        if x>0:#ゼロ含めると当然、infeasibleになる。
            prob +=y >=0
    """
    #5.PVが発電しているときは、売電はPVの発電量より少なくなくてはならない。
    #PV分以上には逆潮流しないが、買電がPV多ければ放電することもある。4or5という設定。
    for x,y in zip(pv,juden_ato):
       if x>0:
          prob += y>=-x
    """
    #6.PVがゼロより大きければ、蓄電池はPVの発電量以上には充電しない。
    for x,y in zip(pv,batt_outin):
        if x>0:#ゼロ含めると当然、infeasibleになる。
            prob +=y <=x
    #7.ピークに対する制約。機器動作前の受電電力対して、何%減を目指すのかもしくはkWhの絶対値。
    for y in juden_ato:#容量市場拠出金の削減のように特定の時間帯を指定する場合は、リストを用意する必要あり。
        prob += y <= juden_mae_max  #最適化前のピーク値×何割というバターン
    #    prob += y <= 10 #上限ピーク値で指定(kW)
        #prob += y >=0 #逆潮流禁止にするならここはゼロ(kW)。逆潮流ありならマイナスで指定(kW)。全部自家消費用。

    #充放電による経済的損失を計算。充放電時で符号が異なるためz係数を用いて表現。＝pulp内でif分は使えない。
    for x,i in zip(batt_outin,z_bat):
        prob += x * batt_effi * jepx_ave >= -i #1コマ単価がjepx単価の平均値に対する充放電損失を表現
        prob += x * batt_effi * jepx_ave <= i #こちらとセットで絶対値を表現

    print('Pulp実行中３：CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC')
    #目的関数
    #PuLPでは目的関数や制約条件の定義に max() やabs()を使用できない!!!
    prob += pulp.lpSum(maltiplication(batt_outin,jepx_incentive_diffirence)) - pulp.lpSum(z_bat)
    #これを最大化しようする。
    print('Pulp実行中４：DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD')
    status = prob.solve()
    #pulp.solvers.PulpSolverErrorの時は宣言した変数に重複などある可能性。
    print('Pulp実行中５：EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
    return batt_outin,status

def calc_jikashohi_incetive(df_pre,jikashohi_incentive,power_com):
    #######卒FIT住宅は自家消費のインセンティブを高くする#######
    jepx_incentive=[]#PV発電量がある時間帯は一律,自家消費インセンティブ分、引く。df_pv_jepxがpv発電量予測とjepx予測が並んだDataFrame
    #jikashohi_incentive = 15 #単位は円/kWh
    
    for i,j,k in zip(df_pre['予測値_PV'],df_pre['予測値_demand'],df_pre['価格']):
        if i==0:#発電量がゼロの時
            jepx_incentive.append(k)
        elif i>0:#発電量がゼロではなく、
            if i>j:#余剰が発生するとき
                jepx_incentive.append(k-jikashohi_incentive)
            else:#余剰が発生しないとき
                jepx_incentive.append(k)
            
    jepx_incentive_ave = np.mean(jepx_incentive)
    
    jepx_incentive_diffirence=[]
    for i in jepx_incentive:
        jepx_incentive_diffirence.append(round(jepx_incentive_ave - i,2))
    
    return jepx_incentive_diffirence


def cleanliness_residetial_battery(capacity_batt,effi_batt,juden,df_pre,SOC_batt_latest,batt_outin_fig,yotei_soc,jepx_ave_difference,jepx_incentive_diffirence,power_com):
    batt_shoki = SOC_batt_latest #
    batt_effi = 1 - effi_batt # 1-としていることに注意!!!
    batt_youryo = capacity_batt
    
    juden_ato_opt = []
    for i,j in zip (juden,batt_outin_fig):
        juden_ato_opt.append(round(i + j,2))
    #listをシリーズに変えていく
    koma = pd.Series(list(df_pre.index)) #インデックスはindexで取得する
    batt_outin = pd.Series(batt_outin_fig)
    soc_ba = pd.Series(yotei_soc)
    jepx = pd.Series(jepx_ave_difference)
    juden_mae = pd.Series(juden)
    juden_ato = pd.Series(juden_ato_opt)
    jepx_incentive_diffirence = pd.Series(jepx_incentive_diffirence)
    df = pd.DataFrame()
    df['コマ'] = koma
    df = df.set_index('コマ')
    df_1 = pd.concat([koma,juden_mae,batt_outin,juden_ato,soc_ba,jepx,jepx_incentive_diffirence], axis=1)
    df_1 = df_1.rename(columns={0:'コマ',1:'前_受電電力',2:'蓄電池_充放電量',3:'最適後_受電電力',4:'蓄電池SOC',5:'JEPX平均差額',6:'JEPX平均差額(自家消費動機有)'})
    df_1 = df_1.set_index('コマ')
    df = pd.concat([df,df_1],axis=1)
    df = pd.concat([df,df_pre['予測値_demand'],df_pre['予測値_PV'],df_pre['価格']],axis=1)
    df = df.rename(columns={'予測値_demand':'予測_需要電力(kWh)','予測値_PV':'予測_PV(kWh)'})
    df = df.dropna(how='any')#1つでもNanの要素がある行を削除
    batt_losskouryo_1 = df['蓄電池_充放電量'].values.tolist()
    batt_losskouryo_2 = []

    #最適化した結果の充放電量に基づいた充放電量効率を加味したSOCの算出。
    #本当は、最適化の中でこれを表現したいがpulpの使い勝手悪く、結果を後で確認し、異常値であれば再度、最適化するという方法を取る
    count = 0
    for i in batt_losskouryo_1:
        if count==0:
            if i>=0:
                batt_losskouryo_2.append(round((batt_shoki*batt_youryo+i*(1-batt_effi))/batt_youryo,3))
            if i<0:
                batt_losskouryo_2.append(round((batt_shoki*batt_youryo+i* (1+batt_effi))/batt_youryo,3))
        if count>0:
            if i>=0:
                batt_losskouryo_2.append(round((batt_losskouryo_2[count-1]*batt_youryo+i*(1-batt_effi))/batt_youryo,3))
            if i<0:
                batt_losskouryo_2.append(round((batt_losskouryo_2[count-1]*batt_youryo+i*(1+batt_effi))/batt_youryo,3))
        count = count +1 

    df['蓄電池SOC_充放電ロス考慮'] = batt_losskouryo_2
    #print(df)
    return df