
def get_info_from_userlist(df_user,i):
    name = df_user['name'].iloc[i]
    id =df_user['Product ID'].iloc[i]
    address=df_user['場所'].iloc[i]
    power_com =df_user['電力管内'].iloc[i]
    Ido = df_user['緯度'].iloc[i]
    Keido =df_user['経度'].iloc[i]
    panel_kakudo=df_user['パネル角度'].iloc[i]
    panel_houi=df_user['方位'].iloc[i]
    pv_yoryo = df_user['PV容量'].iloc[i]  #PV容量[kW]
    kasekisai =df_user['PV容量'].iloc[i]/df_user['PCS容量'].iloc[i] #過積載率[小数表記！！]
    rekka = 0.007*df_user['経過年数'].iloc[i] #劣化率[1年あたり0.7%×経過年数](小数表記！！)
    effi_PCS = df_user['PCS効率'].iloc[i] #PCS効率(小数表記！！)
    effi_trans = df_user['トランス効率'].iloc[i]   #トランス効率(小数表記！！)
    loss_haisen_teikaku=df_user['定格出力時の配線ロス'].iloc[i]    #定格出力時の配線ロス率(小数表記！！)
    ΔT = df_user['ΔT'].iloc[i]
    kage_x=df_user['PVと影物体の直線距離'].iloc[i] #ソーラーと影物体の直線距離(最短距離) 国富工場の環境：7m
    kage_y=df_user['影物体の横の長さ'].iloc[i] #影物体の横の長さ 国富工場の環境：100m
    kage_h=df_user['影物体の高さ'].iloc[i] #影物体の高さ。影物体が無い時は0にしておけばよい。国富工場の環境：12m(4階建て,1階あたり3～5m)
    kage_Φ=df_user['PVから見た時の影物体の方位'].iloc[i] #ソーラーから見た時の影物体の方位。方位は北:0度、東:90度、南:180度、西:270度。国富工場の環境：280度
    facility_name = df_user['名称'].iloc[i]
    capacity_batt = df_user['蓄電池_容量[kWh]'].iloc[i]
    outputpower_batt =df_user['蓄電池_放電出力[kW]'].iloc[i]
    inputpower_batt =df_user['蓄電池_充電出力[kW]'].iloc[i]
    maxSOC_batt = df_user['蓄電池_利用可能最大SOC'].iloc[i]
    minSOC_batt =df_user['蓄電池_利用可能最小SOC'].iloc[i]
    effi_batt =df_user['蓄電池_充放電効率'].iloc[i]
    flag_pv = df_user['PV'].iloc[i]
    flag_battery = df_user['蓄電池'].iloc[i]
    flag_ecocute = df_user['エコキュート'].iloc[i]
    flag_smart =df_user['スマメ'].iloc[i]

    return name,id,address,power_com,Ido,Keido,panel_kakudo,panel_houi,pv_yoryo,kasekisai,\
        rekka,effi_PCS,effi_trans,loss_haisen_teikaku,ΔT,kage_x,kage_y,kage_h,kage_Φ,facility_name,\
            capacity_batt,outputpower_batt,inputpower_batt,maxSOC_batt,minSOC_batt,effi_batt,\
                flag_smart,flag_pv,flag_battery,flag_ecocute