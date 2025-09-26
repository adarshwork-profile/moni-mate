import requests
from bs4 import BeautifulSoup as bs
import time
from datetime import datetime, timedelta
import pandas as pd
import re
from pathlib import Path
import os,json
from django.core.mail import send_mail
from django.conf import settings
from core.models import UserProfile


# Additional Fns 

def timestamps():
    # current date
    cr_date = datetime(datetime.now().year, datetime.now().month, 1)

    # 10 year back 1 Jan
    past_date = datetime(datetime.now().year - 10, 1, 1)

    # conversion to UNIX timestamps
    return (int(time.mktime(cr_date.timetuple())),int(time.mktime(past_date.timetuple())))
# debugging message function
def debug(msg,DEBUG=True):
    if DEBUG:
        print(msg)


# Data Variables
BASE_DIR = Path(__file__).resolve().parent
# print(BASE_DIR)


# Main run function
def data_updater(dbg,crrnt=False):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    if crrnt:
        # updating current nifty50 value
        cr_nfty_url = 'https://economictimes.indiatimes.com/markets/indices/nifty-50'
        cr_nfty_res = requests.get(cr_nfty_url, headers = headers)
        debug(f'DEBUG > Nifty webpage response> {cr_nfty_res.status_code}',dbg)
        nfty_soup = bs(cr_nfty_res.text, 'html.parser')
        cr_nfty = float(nfty_soup.find('p',id='lastTradedPrice').text.replace(',',''))
        debug(f'Current nifty value : {cr_nfty}')

        # updating current P/E | 
        cr_pe_url = 'https://www.screener.in/company/NIFTY/'
        cr_pe_res = requests.get(cr_pe_url, headers=headers)
        debug(f'DEBUG > current pe webpage response: {cr_pe_res.status_code}',dbg)
        pe_soup = bs(cr_pe_res.content,'html.parser')
        cr_pe = float(pe_soup.select_one('#top-ratios > li:nth-child(4) > span.nowrap.value > span').text)
        debug(f'Current PE: {cr_pe}')

        return cr_nfty,cr_pe


    # updating current gdp
    cr_gdp_url = 'https://www.macrotrends.net/global-metrics/countries/IND/india/gdp-gross-domestic-product'
    
    cr_gdp_res = requests.get(cr_gdp_url,headers=headers)
    debug(f'DEBUG > current gdp webpage response: {cr_gdp_res.status_code}',dbg)
    gdp_soup = bs(cr_gdp_res.text, 'html.parser')
    cr_gdp = float(gdp_soup.select_one('#main_content > div.col-xs-5 > table > tbody > tr:nth-child(1) > td:nth-child(2)').text.replace('$','').replace('B','').replace(',',''))
    cr_gdp = cr_gdp * 1000000000 # converting to actuall digits.
    # conveting to INR.
    convr_url = f'https://www.exchange-rates.org/exchange-rate-history/usd-inr-{datetime.now().year}'
    debug(f'DEBUG > Convr rate url:  {convr_url}',dbg)
    convr_res = requests.get(convr_url,headers=headers)
    debug(f'DEBUG > Convr rate response: {convr_res}',dbg)
    convr_soup = bs(convr_res.text,'html.parser')
    convr_table = convr_soup.find('table',class_='history-rate-summary')
    convr_rows = convr_table.find_all('td')
    text = convr_rows[3].get_text(strip=True)
    mat = re.search(r'\d+\.\d+|\d+',text)
    if mat:
        convr_rate = round(float(mat.group()),2)
        debug(f'DEBUG > Current convr rate: {convr_rate}',dbg)
    else:
        print('Conversion rate not found | no match!')
        convr_rate = 0
    cr_gdp = cr_gdp * convr_rate # conversion
    debug(f'Curent GDP: {cr_gdp}')

    # updating P/E median -
    # manual update. required data rendered through javascript on button click
    cr_pe_url = 'https://www.screener.in/company/NIFTY/'
    avg_pe = float(input(f'Go to website: {cr_pe_url}\nFrom PE Ratio chart select year to be 10 Y &  the enter the median amount here\n>'))
    debug(f'Average PE: {avg_pe}')

    # updating avg nifty50
    cr_date,past_date = timestamps()
    debug(f'DEBUG > Current date {cr_date} | Past Date {past_date}',dbg)
    avg_nfty_url = f'https://finance.yahoo.com/quote/%5ENSEI/history/?&frequency=1mo&period1={past_date}&period2={cr_date}'
    debug(f'DEBUG > Avg nifty url {avg_nfty_url}',dbg)
    avg_nfty_res = requests.get(avg_nfty_url,headers=headers)
    debug(f'DEBUG > Avg nifty webpage response {avg_nfty_res}',dbg)
    nfty_soup = bs(avg_nfty_res.text,'html.parser')
    rows = nfty_soup.find_all('tr', class_='yf-j5d1ld')
    debug(f'DEBUG > got {len(rows)} rows of nifty high values.',dbg)
    nfty_highs = []
    for row in rows:
        tds = row.find_all('td')
        if len(tds)>=3:
            data = tds[2].get_text(strip=True).replace(',','')
            debug(f'DEBUG > Current nifty high > {data}',dbg)
            nfty_highs.append(float(data))
    avg_nfty = round(sum(nfty_highs)/len(rows),2)
    debug(f'Avg Nifty : {avg_nfty}')

    # updating avg gdp
    dwnld_url = 'https://www.macrotrends.net/global-metrics/countries/IND/india/gdp-gross-domestic-product'
    file_loc = input(f'\nGo to website: {dwnld_url}\nDownload GDP Historical Data\nRemove unwanted years and additional data\nEnter loc of the csv file > ')
    data = pd.read_csv(file_loc)
    avg_gdp_data = {}
    for i in range(11):
       avg_gdp_data[int(data.loc[i]['Date'].split('-')[-1])] = round(float(data.loc[i][' GDP (Billions of US $)']),2)
    # converting gdp data to INR
    debug('Converting GDP data to INR.')
    for year,gdp in avg_gdp_data.items():
        gdp = gdp * 1000000000
        #print(gdp)
        convr_url = f'https://www.exchange-rates.org/exchange-rate-history/usd-inr-{year}'
        debug(f'DEBUG > Convr rate url:  {convr_url}',dbg)
        convr_res = requests.get(convr_url,headers=headers)
        debug(f'DEBUG > Convr rate response: {convr_res}',dbg)
        convr_soup = bs(convr_res.text,'html.parser')
        convr_table = convr_soup.find('table',class_='history-rate-summary')
        convr_rows = convr_table.find_all('td')
        text = convr_rows[3].get_text(strip=True)
        mat = re.search(r'\d+\.\d+|\d+',text)
        if mat:
            convr_rate = round(float(mat.group()),2)
            debug(f'DEBUG > Current convr rate: {convr_rate}',dbg)
        else:
            print('Conversion rate not found | no match!')
            convr_rate = 0
        avg_gdp_data[year] = round(convr_rate * gdp ,4) # gdp converted to inr
        debug(f'DEBUG > GDP in INR({year}) = {round(convr_rate * gdp,4)}',dbg)
        time.sleep(1)
    # calculating avg 
    avg_gdp = sum(avg_gdp_data.values())/len(avg_gdp_data)
    #print(gdp_avg)
    debug(f'Avg GDP: {avg_gdp}')

    # updating file
    file_data = {'current_gdp':cr_gdp,'avg_nifty':avg_nfty,'avg_gdp':avg_gdp,'avg_pe':avg_pe}
    debug(f'DEBUG > File data: {file_data}',dbg)

    return file_data

# Import-run functions
def deviator():
    with(open(os.path.join(BASE_DIR,'assets_data.json'),'r')) as file:
        data = json.load(file)
    
    # admin alert 
    if datetime.now().month == 4 and data['admin-alert']:
        send_mail(
            'Data Update Alert - Moni-Mate (Admin)',
            'Dear admin,\nThis is your alert for updating data for this financial year. Please follow the instructions below:\nGo to hosted platform, navigate to MoniMate>assets & run the "support_func.py file. Then follow the instructions on the screen.\n\nRegards,\nMoni-Mate Team',
            settings.DEFAULT_FROM_EMAIL,
            ['freelance.blackfly123@gmail.com']
        )
        #update file (admin-alert)
        data['admin-alert'] = False
    elif datetime.now().month != 4 and not data['admin-alert']:
        data['admin-alert'] = True
    
    # user alert (asset update )
    alert_dates = [26,27,28,29,30]
    if datetime.now().day in alert_dates and data['user-alert']:
        send_mail(
            'Assets Data Update Notification  -MoniMate',
            "Dear User,\nPlease update your asset's invested & current amount values by visitng the Wealth page on MoniMate application.\nRegards,\nMoniMate Team",
            settings.DEFAULT_FROM_EMAIL,
            [profile.notify_email for profile in UserProfile.objects.all()]
        )
        #update file (user-alert)
        data['user-alert'] = False

    elif datetime.now().day not in alert_dates and not data['user-alert']:
        data['user-alert'] = True
    

    crrnt_nfty,crrnt_pe = data_updater(False,True)
    # print(f'Average Nifty: {data['avg_nifty']}\nAverage GDP:{data['avg_gdp']}\nCurrent GDP:{data['current_gdp']}')
    # expected nifty
    exp_nfty = round(data['current_gdp'] * (data['avg_nifty'] / data['avg_gdp']),4)
    # print(f'Expected nifty {exp_nfty}')
    # nifty deviation %
    nfty_dev = round(((crrnt_nfty - exp_nfty) / exp_nfty) * 100,2)
    # PE deviation
    pe_dev = round(((crrnt_pe - data['avg_pe']) / data['avg_pe']) * 100,2)
    # print(f'nifty deviation: {nfty_dev}\nPE deviation: {pe_dev}')

    # update data file with new changes
    with open(os.path.join(BASE_DIR,'assets_data.json'),'w') as file:
        json.dump(data,file)

    return crrnt_nfty,nfty_dev,pe_dev




    
if __name__ == '__main__':
    # setting up debug
    dbg_inp = input('Type "yes" and hit enter to turn on Debug mode\nelse just hit enter\n>')
    if dbg_inp == 'yes':
        dbg = True
    else:
        dbg = False
    file_data = data_updater(dbg)
    # writing file
    with(open(os.path.join(BASE_DIR,'assets_data.json'),'w')) as file:
        json.dump(file_data,file)
        print('Json file updated successfully.')
