from binance import Client
import pandas as pd
import os
import talib
import quantstats as qs
import matplotlib.pyplot as plt

all_df = pd.DataFrame()
#資料下載
def download_klines(name, interval, coin):
    klines = client.get_historical_klines(symbol=coin, interval=interval, start_str="2017/1/1", end_str='2023/3/21')
    data = pd.DataFrame(klines,
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av',
                                 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
    data.to_csv(name, index=0)
# 新增DataFrame
def add_data(index_data, data):
    index_data['timestamp'] = data['timestamp']
    index_data['close'] = data['close']
    index_data['high'] = data['high']
    index_data['low'] = data['low']
    index_data['open'] = data['open']
    index_data['volume'] = data['volume']
    # 計算指標
    index_data['EMA40'] = talib.SMA(data['close'], timeperiod = 50)
    index_data['EMA200'] = talib.SMA(data['close'], timeperiod=204)
    index_data['RSI'] = talib.RSI(data['close'], timeperiod = 14)
    index_data['ATR'] = talib.ATR(high=data['high'], low=data['low'], close=data['close'], timeperiod=14)
    index_data['ADX'] = talib.ADX(high=data['high'], low=data['low'], close=data['close'], timeperiod=14)
    index_data['upperband'], index_data['lowerband'], index_data['DIF'] = \
        talib.MACD(index_data['close'], fastperiod=200, slowperiod=40, signalperiod=14)
    return index_data
def CPL_SELL(close, STOP):
    b = close
    a = STOP
    p = round(b - a, 2)
    p = (p / b) * 100
    percentage = round(p, 2)
    take_ratio_loss = percentage

    percentage_num = p * 0.01
    percentage_num = round(percentage_num, 4)
    return take_ratio_loss, percentage_num
def CPL_BUY(close, STOP):
    b = close
    a = STOP
    p = round(a - b, 2)
    p = (p / b) * 100
    percentage = round(p, 2)
    take_ratio_loss = percentage

    percentage_num = p * 0.01
    percentage_num = round(percentage_num, 4)

    return take_ratio_loss, percentage_num
# 利潤計算
def fun_profit(percen, start_price, profit_price, money, state, fee):
    if state == 'SELL':
        # 開倉 平倉%%
        take_ratio_loss, percentage_num = CPL_SELL(start_price, profit_price)
        # 平倉多少 金額
        money_num = money * percen
        # 本 + 利潤
        Principal_Profit = money_num + (money_num * percentage_num)
        # 計算手續費
        fee_num = (Principal_Profit * fee) * -1
        # 扣去手續費後最後利潤
        num = money_num * percentage_num + fee_num
        # 剩下持倉金額
        money = money - money_num
        # 最終營利金額, 平倉%%, 平倉多少金額, 剩下持倉金額
        return num, percentage_num, money_num, money
    elif state == 'BUY':
        # 開倉 平倉%%
        take_ratio_loss, percentage_num = CPL_BUY(start_price, profit_price)
        # 平倉多少 金額
        money_num = money * percen
        # 本 + 利潤
        Principal_Profit = money_num + (money_num * percentage_num)
        # 計算手續費
        fee_num = (Principal_Profit * fee) * -1
        # 扣去手續費後最後利潤
        num = money_num * percentage_num + fee_num
        # 剩下持倉金額
        money = money - money_num
        # 最終營利金額, 平倉%%, 平倉多少金額, 剩下持倉金額
        return num, percentage_num, money_num, money
# 1:1止盈計算
def TP1_def(start_price, money, state, fee, index, df):
    # 回踩OB close, 進場金額, 方向, 手續費, 回踩OB num, 資料, OB num , stop price * 0.10%, 斐波止損參數, ATR倍數
    money = money * 2.5
    # 紀錄進場位置
    num = index
    # 計算所有資料數量
    len_data = len(df)

    # 空單進場
    if state == 'SELL':
        take = df.loc[num, 'low'] - (df.loc[num, 'ATR'] * 5)
        stop = df.loc[num, 'high'] + (df.loc[num,'ATR'] * 2)

        while True:
            num += 1
            # 資料跑到底 跳出迴圈
            if num >= len_data and len_data <= num:
                return 0, 0, 0, 0, 0
            elif df.loc[num, 'high'] >= stop and stop <= df.loc[num, 'high']:
                # 最終營利金額, 平倉%%, 平倉多少金額, 剩下持倉金額
                profit_num, percentage_num, money_num, remain = \
                    fun_profit(1, start_price, stop, money, state, fee)
                # TP1出場比例, 進場price, 止損price, 總進金額, 方向, 手續費
                # 止損, 最終虧損多少, 營利%, K棒痠到哪, 平倉多少 金額, 平倉price
                return profit_num, percentage_num, num, money_num, stop
            elif df.loc[num, 'low'] <= take and take >= df.loc[num, 'low']:
                # 最終營利金額, 平倉%%, 平倉多少金額, 剩下持倉金額
                profit_num, percentage_num, money_num, remain = \
                    fun_profit(1, start_price, take, money, state, fee)
                                # TP1出場比例, 進場price, 止損price, 總進金額, 方向, 手續費
                # 最終營利金額, 平倉%%, ,平倉K index位置, 平倉多少金額,平倉位置, 平倉price
                return profit_num, percentage_num, num, money_num, df.loc[num, 'close']
    elif state == 'BUY':
        take = df.loc[num, 'high'] + (df.loc[num, 'ATR'] * 5)
        stop = df.loc[num, 'low'] - (df.loc[num, 'ATR'] * 2)

        while True:
            num += 1
            # 資料跑到底 跳出迴圈
            if num >= len_data and len_data <= num:
                return 0, 0, 0, 0, 0
            elif df.loc[num, 'low'] <= stop and stop >= df.loc[num, 'low']:
                profit_num, percentage_num, money_num, remain = \
                    fun_profit(1, start_price, stop, money, state, fee)
                # TP1出場比例, 進場price, 止損price, 總進金額, 方向, 手續費
                # 止損, 最終虧損多少, 營利%, K棒痠到哪, 平倉多少 金額, 平倉price
                return profit_num, percentage_num, num, money_num, stop
            elif df.loc[num, 'high'] >= take and take <= df.loc[num, 'high']:
                profit_num, percentage_num, money_num, remain = \
                    fun_profit(1, start_price, take, money, state, fee)
                                # TP1出場比例, 進場price, 止損price, 總進金額, 方向, 手續費
                # 止損, 最終虧損多少, 營利%, K棒痠到哪, 平倉多少 金額, 平倉price

                return profit_num, percentage_num, num, money_num, df.loc[num, 'close']
def backtest(df, state, index, len_data, Enter, fee):
    num = index
    # 利潤
    profit_all = 0.0
    # 進場fee
    Enter_fee = (Enter * fee) * -1
    if num >= len_data and len_data <= num:
        return 0, 0, 0, 0, 0
    if state == 'SELL':
        # 止損or止盈, 獲利or虧損多少, 營利%, K棒痠到哪, 平倉多少 金額, 平倉價格
        profit, percentage_num_1,num, money_num, close_price = \
            TP1_def(df.loc[index, 'close'], Enter, state, fee, index, df)
            # 回踩OB close, 進場金額, 方向, 手續費, 回踩OB num, 資料, OB num , stop price * 0.10%, 斐波止損參數, ATR倍數
        # 利潤總數
        profit_all = profit_all + profit
        # 利潤-進場手續費
        profit_all = profit_all + Enter_fee
        #計算 減去fee後最後利潤
        take_ratio_loss_end, percentage_num_end = CPL_BUY(Enter, Enter + profit_all)
        if take_ratio_loss_end < 0 and 0 > take_ratio_loss_end:
            num_pe = -0.2
        elif take_ratio_loss_end > 0 and 0 < take_ratio_loss_end:
            num_pe = 0.2
        elif take_ratio_loss_end == 0:
            num_pe = -0.2
        # 迴圈是否跑完, 最終利潤, 進場資金~進場資金+利潤小數, 進場資金~進場資金+利潤小數%, 標記盈虧
        return 2, profit_all, percentage_num_end, take_ratio_loss_end, num_pe

    elif state == 'BUY':

        # TP1
        # //////////////////////////////////////////////////////////////////////////////////////////////////
        # 止損or止盈, 獲利or虧損多少, 營利%, K棒痠到哪, 平倉多少 金額, 平倉價格
        profit, percentage_num_1,num, money_num, close_price = \
            TP1_def(df.loc[index, 'close'], Enter, state, fee, index, df)
        # 回踩OB close, 進場金額, 方向, 手續費, 回踩OB num, 資料, OB num , stop price * 0.10%, 斐波止損參數, ATR倍數

        # 利潤總數
        profit_all = profit_all + profit
        # 利潤-進場手續費
        profit_all = profit_all + Enter_fee
        #計算 減去fee後最後利潤
        take_ratio_loss_end, percentage_num_end = CPL_BUY(Enter, Enter + profit_all)

        if take_ratio_loss_end < 0 and 0 > take_ratio_loss_end:
            num_pe = -0.1
        elif take_ratio_loss_end > 0 and 0 < take_ratio_loss_end:
            num_pe = 0.1
        elif take_ratio_loss_end == 0:
            num_pe = -0.1
        # 迴圈是否跑完, 最終利潤, 進場資金~進場資金+利潤小數, 進場資金~進場資金+利潤小數%, 標記盈虧
        return 1, profit_all, percentage_num_end, take_ratio_loss_end, num_pe
    return 0, 0, 0, 0, 0
def RSI_ran(state,df, i):
    if state == 'SELL':
        while True:
            i += 1
            if df.loc[i, 'RSI'] < 70 and 70 > df.loc[i, 'RSI']:
                return i
    elif state == 'BUY':
        while True:
            i += 1
            if df.loc[i, 'RSI'] > 30 and 30 < df.loc[i, 'RSI']:
                return i
#判斷有效訂單塊
def OB(df, wallet, Entry_Percentage, fee):
    len_data = len(df) - 1
    BUY_percentage = []
    SELL_percentage = []
    # 加上沒獲利時間
    my_array = []
    # 獲利金額
    my_array_1 = []
    state = []
    take_ratio_loss_array = []
    percentage_num_array = []

    wallet_a = []

    TP_a = []
    #盈虧紀錄
    num_pe_ar = []
    #判斷K線型態
    type_1 = pd.DataFrame()
    i = 0

    while True:
        #壓力
        if df.loc[i, 'RSI'] > 70 and 70 < df.loc[i, 'RSI']:
            i = RSI_ran('SELL', df, i)
            if df.loc[i, 'ADX'] > 25 and 25 < df.loc[i, 'ADX']:
                if df.loc[i - 1, 'ADX'] < df.loc[i, 'ADX'] and df.loc[i, 'ADX'] > df.loc[i - 1, 'ADX']:
                    # if df.loc[i - 1, 'volume'] > df.loc[i, 'volume'] and df.loc[i - 1, 'volume'] < df.loc[i, 'volume']:
                        if df.loc[i, 'lowerband'] < df.loc[i, 'upperband'] and df.loc[i, 'upperband'] > df.loc[i, 'lowerband']:
                            if df.loc[i, 'close'] < df.loc[i, 'EMA200'] and df.loc[i, 'EMA200'] > df.loc[i, 'close']:
                                Enter = (Entry_Percentage * wallet)
                                # 迴圈是否跑完, 最終利潤, 進場資金~進場資金+利潤小數, 進場資金~進場資金+利潤小數%, 標記盈虧

                                result, take_ratio_loss, percentage_num, take_ratio_loss_end, num_pe = \
                                    backtest(df, 'SELL', i, len_data, Enter, fee)
                                if result != 0:
                                    # OB index 位置
                                    type_1 = type_1.append(df.loc[i], ignore_index=True)

                                    # 最終 利潤 或 虧損金額
                                    take_ratio_loss_array.append(take_ratio_loss)
                                    # 進場資金 到 出場後進 資金變動%數
                                    percentage_num_array.append(percentage_num)
                                    # 利潤加入錢包
                                    wallet = wallet + take_ratio_loss
                                    # 方向
                                    state.append('SELL')
                                    # 空單利潤
                                    SELL_percentage.append(take_ratio_loss)
                                    # 紀錄wallet走勢圖
                                    wallet_a.append(wallet)
                                    # 紀錄利潤 沒有進場也記錄
                                    my_array.append(take_ratio_loss)
                                    # 回報率
                                    my_array_1.append(take_ratio_loss)
                                    # TP
                                    TP_a.append(result)
                                    #盈虧紀錄
                                    num_pe_ar.append(num_pe)
        #支撐
        if df.loc[i, 'RSI'] < 30 and 30 > df.loc[i, 'RSI']:
            i = RSI_ran('BUY', df, i)
            if df.loc[i, 'ADX'] > 25 and 25 < df.loc[i, 'ADX']:
                if df.loc[i - 1, 'ADX'] < df.loc[i, 'ADX'] and df.loc[i, 'ADX'] > df.loc[i - 1, 'ADX']:
                    # if df.loc[i - 1, 'volume'] > df.loc[i, 'volume'] and df.loc[i - 1, 'volume'] < df.loc[i, 'volume']:
                        if df.loc[i, 'lowerband'] > df.loc[i, 'upperband'] and df.loc[i, 'upperband'] < df.loc[i, 'lowerband']:
                            if df.loc[i, 'close'] > df.loc[i, 'EMA200'] and df.loc[i, 'EMA200'] < df.loc[i, 'close']:
                                Enter = (Entry_Percentage * wallet)
                                # 迴圈是否跑完, 最終利潤, 進場資金~進場資金+利潤小數, 進場資金~進場資金+利潤小數%, 標記盈虧
                                result, take_ratio_loss, percentage_num, take_ratio_loss_end, num_pe = \
                                    backtest(df, 'BUY', i, len_data, Enter, fee)
                                if result != 0:
                                    # OB index 位置
                                    type_1 = type_1.append(df.loc[i], ignore_index=True)

                                    # 最終 利潤 或 虧損金額
                                    take_ratio_loss_array.append(take_ratio_loss)
                                    # 進場資金 到 出場後進 資金變動%數
                                    percentage_num_array.append(percentage_num)
                                    # 利潤加入錢包
                                    wallet = wallet + take_ratio_loss
                                    # 方向
                                    state.append('BUY')
                                    # 多單利訰
                                    BUY_percentage.append(take_ratio_loss)
                                    # 紀錄wallet走勢圖
                                    wallet_a.append(wallet)
                                    # 回報率 + 0
                                    my_array.append(take_ratio_loss)
                                    # 回報率
                                    my_array_1.append(take_ratio_loss)
                                    # TP
                                    TP_a.append(result)
                                    #盈虧紀錄
                                    num_pe_ar.append(num_pe)
        if i >= len_data-1 and len_data-1 <= i:
            return type_1, state, take_ratio_loss_array, percentage_num_array, my_array, my_array_1, BUY_percentage, SELL_percentage, wallet_a, TP_a, num_pe_ar
        i += 1
    return type_1, state, take_ratio_loss_array, percentage_num_array, my_array, my_array_1, BUY_percentage, SELL_percentage, wallet_a, TP_a, num_pe_ar
#夏普比率
def sharpe_ratio(my_array):
    stock = pd.DataFrame(my_array)
    stock.to_csv('D:/' + coin + '_stock_' + '.csv')
    qs.extend_pandas()
    stock.sharpe()
    SR = qs.stats.sharpe(stock)
    print("sharpe ratio:{}".format(SR))
#最大回測
def drawdown(wallet):
    max_df = qs.stats.max_drawdown(wallet)
    max_df = round(max_df * 100, 2)
    print("最大回測:{}%".format(max_df))
#連續止盈
def wins(df):
    print("連續止盈:{}".format(qs.stats.consecutive_wins(df)))
#連續止損
def losses(df):
    print("連續止損:{}".format(qs.stats.consecutive_losses(df)))
#盈利因子
def profit_factor(df):
    print("盈利因子:{}".format( round(qs.stats.profit_factor(df), 3)))
# 回報/回撤比（Return/DD）
def return_ratio(df):
    return_ = qs.stats.risk_return_ratio(df)
    return_ = round(return_, 4)
    print("回報/回撤比:{}".format(return_))
#交易次數
def Num_of_Trades(df):
    print("交易次數:{}".format(len(df)))
#最初資本
def Initial_Capital(num):
    print("最初資本:{}".format(num))
#最後資本
def Final_Capital(num):
    print("最後資本:{}".format(round(num), 2))
# ROI
def ROI(wallet, Final):
    Return_on_Investment = round((Final - wallet) * 0.01, 2)
    print('ROI:{}%'.format(Return_on_Investment))
# 勝率
def Win_Rate(df):
    df = round(qs.stats.win_rate(df) * 100, 2)
    print("勝率:{}%".format(df))
# BUY and SELL count
def BUY_SELL_num(df):
    Buy_count = df['state'].value_counts().get('BUY', 0)
    SELL_count = df['state'].value_counts().get('SELL', 0)
    print("BUY数量:{}".format(Buy_count))
    print("SELL数量:{}".format(SELL_count))
# BUY and SELL Win Rate
def BUY_SELL_Win_Rate(BUY_df, SELL_df):
    Buy_count = len(BUY_df)
    SELL_count = len(SELL_df)

    BUY_negative_count = (BUY_df['percentage_num'] > 0).sum()
    SELL_negative_count = (SELL_df['percentage_num'] > 0).sum()
    BUY_negative_count = round((BUY_negative_count / Buy_count) * 100, 2)
    SELL_negative_count = round((SELL_negative_count / SELL_count) * 100, 2)

    print("BUY勝率:{}%".format(BUY_negative_count))
    print("SELL勝率:{}%".format(SELL_negative_count))
def negative_sum(df):
    negative_sum = df.loc[df['Value'] < 0, 'Value'].sum()
    integer_sum = df.loc[df['Value'] > 0, 'Value'].sum()

    print("總虧損:{}".format(round(negative_sum, 2)))
    print("總盈利:{}".format(round(integer_sum, 2)))
def profit(wallet, Final):
    print("利潤:{}".format(round(Final - wallet, 2)))
def transaction_data(wallet, OB_data, my_array, return_series_1, BUY_df, SELL_df):
    # 最初資本
    Initial_Capital(wallet)
    # 最後資本
    Final_Capital(OB_data.loc[int(len(OB_data) - 1), 'wallet'])
    #利潤
    profit(wallet, OB_data.loc[int(len(OB_data) - 1), 'wallet'])
    # 勝率
    Win_Rate(return_series_1)
    # 投資回報率
    ROI(wallet, OB_data.loc[int(len(OB_data) - 1), 'wallet'])
    # sharpe_ratio
    sharpe_ratio(my_array)
    # 最大回測
    drawdown(OB_data['wallet'])
    # 連續止盈
    wins(OB_data['percentage_num'])
    # 連續止損
    losses(OB_data['percentage_num'])
    # 盈利因子
    profit_factor(return_series_1)
    # 回報/回撤比（Return/DD）
    return_ratio(OB_data['wallet'])
    # 交易次數
    Num_of_Trades(OB_data['wallet'])
    # BUY and SELL數量
    BUY_SELL_num(OB_data)
    # BUY and SELL勝率
    BUY_SELL_Win_Rate(BUY_df, SELL_df)
    #總盈虧
    negative_sum(return_series_1)
coin = 'BTCUSDT'
interval = '15m'
name = 'D:/' + coin+'_' + interval + '.csv'

fee = 0.00005
wallet = 10000

#出場百分比
percen = 1
#每次進場多少倉位
Entry_Percentage = 1

if os.path.exists(name):
    print()
else:
    api_key = ''
    api_secret = ''
    client = Client(api_key, api_secret)
    download_klines(name, interval, coin)

order = pd.read_csv(name)
index_data = pd.DataFrame()
OB_data = pd.DataFrame()
range_num = len(order)
wallet_pd = pd.DataFrame()

# copy data
df = add_data(index_data, order)

OB_data, state , take_ratio_loss_array, percentage_num_array, my_array , my_array_1, BUY_percentage, SELL_percentage, wallet_a, TP_a, num_pe_ar = \
    OB(df, wallet, Entry_Percentage, fee)
# BUY and SELL
OB_data['state'] = state
# 進出場利潤or損益
OB_data['take_ratio_loss'] = take_ratio_loss_array
# 進出場盈利or虧損比分比
OB_data['percentage_num'] = percentage_num_array
# BUY and SELL數字標籤
OB_data['TP'] = TP_a
# 資金變化
OB_data['wallet'] = wallet_a
# 止盈損標籤
OB_data['num_pe_ar'] = num_pe_ar
# DataFrame儲存.csv
OB_data.to_csv('D:/' + coin + '_data_'+ str('1_1_1.13') + '.csv')



BUY_df = pd.DataFrame()
SELL_df = pd.DataFrame()

BUY_df['percentage_num'] = BUY_percentage
SELL_df['percentage_num'] = SELL_percentage

# 回報率DF
return_series_1 = {'Value':my_array_1}
return_series_1 = pd.DataFrame(return_series_1)


#交易數據
transaction_data(wallet, OB_data, my_array, return_series_1, BUY_df, SELL_df)

plt.plot(OB_data['wallet'])
plt.show()
