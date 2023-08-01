import  pandas as pd
from datetime import timedelta,date,datetime
from calendar import day_name
from time import sleep
from threading import Thread
from os import getcwd


def FilteredSymbolList():
    sym_details = pd.read_csv("https://public.fyers.in/sym_details/NSE_FO.csv")
    sym_details.columns =  ['epoch_time','symbol_name','o','h','c','l','exg_time','date','expiry_date','symbol','10','11','underlying_price','underlying_name','underlying','strike_price','call_put','abc','None']
    def filterWeeklyexpiry():
        for i in range(8):
                my_date = date.today()+timedelta(i)
                a = day_name[my_date.weekday()]
                if a == 'Thursday':
                    expiry_date = my_date
                    break
        for i in range(10):
            expiry_date = expiry_date - timedelta(i)
            expiry_date_epoch =  int((datetime.strptime(f'{expiry_date} 20:00:00', '%Y-%m-%d %H:%M:%S')).timestamp())
            sym_details_temp = sym_details.loc[sym_details['expiry_date'] == expiry_date_epoch]
            if  len(sym_details_temp) != 0 :
                return sym_details_temp
    return filterWeeklyexpiry()
    
def ThreadRapper(objc,fyers,fyersSocket):
    def doNothing():
        pass
    
    level,usymbol,highl,lowl,UNdl_ToKen,qty,target,typ,dir =  [objc[k] for k in ('level','symbol','h_LeVel','l_LeVel','UNdl_ToKen','qty','target','typ',"dir")]

    def onCrossing(msg): 
        print(msg[0]['ltp'])
        if  msg[0]['ltp'] <= highl and msg[0]['ltp'] >= lowl :
                fyersSocket.websocket_data = doNothing
                data = {
                            "symbol":usymbol,
                            "qty":qty,
                            "type":2, 
                            "side":-1,
                            "productType":"MARGIN",
                            "limitPrice":0,
                            "stopPrice":0,
                            "validity":"DAY",
                            "disclosedQty":0,
                            "offlineOrder":"False",
                            "stopLoss":0,
                            "takeProfit":0
                        }
                try:
                    sourceFile = open(f"{getcwd()}/orders.txt", 'a')
                except:
                    sourceFile = open(f"{getcwd()}/orders.txt", "x")
                print(data, file = sourceFile)
                sourceFile.close()

                 
    def onCloseCall(msg):
        if (msg[0]["timestamp"] % 3600 // 60) % 15 == 0 and msg[0]["ltp"] >= level:
            fyersSocket.websocket_data = onCrossing
            print("closed call")
                
    def onClosePut(msg):
        if (msg[0]["timestamp"] % 3600 // 60) % 15 == 0 and msg[0]["ltp"] <= level:
            fyersSocket.websocket_data = onCrossing
            print("closed put")

    if typ == "o" and dir == "s":
        fyersSocket.websocket_data = onCloseCall
    if typ == "o" and dir == "r":
        fyersSocket.websocket_data = onClosePut
    if typ == "c" :
        fyersSocket.websocket_data = onCrossing
        
    def subscribe_new_symbol(symbol_list,fyersSocket):        
        fyersSocket.subscribe(symbol=symbol_list, data_type="symbolData")  
    t = Thread(target=subscribe_new_symbol, args=([UNdl_ToKen],fyersSocket,))
    t.start()

    while True:   
        sleep(20)  

def get_ITM(sym_details,level,UnDL,CP,bool):   
    optionsData = sym_details
    optionsData = optionsData.loc[optionsData['underlying_name'] == UnDL]
    optionsData = optionsData.loc[optionsData['call_put'] == CP]
    optionsData = optionsData.sort_values('strike_price', ascending= bool)
    if CP == 'CE':
        optionsData = optionsData.loc[optionsData['strike_price'] < int(level)]
    else:
        optionsData = optionsData.loc[optionsData['strike_price'] > int(level)]   
    return optionsData["symbol"].tolist()[0]


def CreateOrderData(filteredSymbolList,orderDataDict):
    level = int(orderDataDict['level'])
    type = orderDataDict['type']
    direction = orderDataDict['direction']
    quantity = int(orderDataDict['quantity']) 
    target = int(orderDataDict['target'])
    
    if  direction == 'Support' and level <= 25000:
        ITM = get_ITM(filteredSymbolList,level,'NIFTY','CE',False)
        UNdl_ToKen = 'NSE:NIFTY50-INDEX'
        h_LeVel = level+1
        l_LeVel = level-5
        quantity = int(quantity)*50
    elif  direction == 'Support' and level >= 25000:
        ITM = get_ITM(filteredSymbolList,level,'BANKNIFTY','CE',False)
        UNdl_ToKen = 'NSE:NIFTYBANK-INDEX'
        h_LeVel =  level+2
        l_LeVel =  level-10
        quantity = int(quantity)*25
    elif  direction == 'Resistance' and level <= 25000:
        ITM = get_ITM(filteredSymbolList,level,'NIFTY','PE',True)
        UNdl_ToKen = 'NSE:NIFTY50-INDEX'
        h_LeVel =  level+5
        l_LeVel =  level-1
        quantity = int(quantity)*50
    elif  direction == 'Resistance' and level >= 25000:
        ITM = get_ITM(filteredSymbolList,level,'BANKNIFTY','PE',True)
        UNdl_ToKen = 'NSE:NIFTYBANK-INDEX'
        h_LeVel =  level+10
        l_LeVel =  level-2
        quantity = int(quantity)*25

    return { 
            'level':level,  
            'symbol' : ITM , 
            'h_LeVel' : h_LeVel , 
            'l_LeVel' : l_LeVel ,
            'UNdl_ToKen':UNdl_ToKen,
            'qty':quantity,
            'target':target,
            "typ":type,
            "dir":direction
            } 