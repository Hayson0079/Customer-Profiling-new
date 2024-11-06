import pandas as pd
import os
import numpy as np

### Read the customer info download from RMM 'Customer Level' page
def read_customer_info():
    # read customer info xlsx file
    file_path =  'data/198 customer info.xlsx'
    customer_info = pd.read_excel(file_path)

    '''
    # convert str date back to datetime format
    customer_info['Register date'] = pd.to_datetime(customer_info['Register date'], format='%Y-%m-%d %H:%M:%S%Z', errors='coerce')
    
    # Set up new reg day for old customer
    start_date = pd.Timestamp('2024-01-01 00:00:00+00:00')
    customer_info['Reg day'] = np.where(customer_info['Register date'] < start_date, start_date, customer_info['Register date'])
    '''

    return customer_info[['Customer id', 'Customer name', 'Level name', 'Register date', 'Bet state', 'Pending state']]


### Read the alert IP and customer ids generated from RMM side
def read_198_alert_list():
    # read alert xlsx file
    file_path =  'data/Robotic alert.xlsx'
    ip_alert = pd.read_excel(file_path, sheet_name = 'IP')
    customer_alert = pd.read_excel(file_path, sheet_name = 'Account')
    
    return ip_alert['IP'].to_list(), customer_alert['Customer id'].to_list()


### Read the historical bet data (csv) downloaded from RMM site
def read_new_bets():
    directory = 'data/Bets'

    new_bet_df = pd.DataFrame()

    # combine all new bet files
    for folder in os.listdir(directory):
        for filename in os.listdir(os.path.join(directory, folder)):
            file_path = os.path.join(directory, folder, filename)
            df = pd.read_excel(file_path)
            new_bet_df = pd.concat([new_bet_df, df])

    new_bet_df = new_bet_df[(new_bet_df['Sport'] == "Soccer") & (new_bet_df['Platform'] == "FootballBook") & (new_bet_df['Level'] != "Tester")]

    new_bet_df['Match date'] = pd.to_datetime('2024/' + new_bet_df['Match date'], format='%Y/%m/%d %H:%M', errors='coerce')
    
    for date in ['Place date', 'Accepted date', 'Settled date']:
        new_bet_df[date] = pd.to_datetime('2024-' + new_bet_df[date], format='%Y-%m-%d %H:%M:%S%z', errors='coerce')
    
    new_bet_df['Match date'] = new_bet_df['Match date'].dt.tz_localize('UTC')
    new_bet_df = new_bet_df.sort_values(by = 'Place date', ascending = False)

    
    return new_bet_df


### Read syndicate bets and pre-processing
def read_preprocess_syndicate_bets():
    # read all syndicate bets
    syndicate_bets = pd.read_excel('data/Syndicate bets.xlsx')

    # filter desired customer 
    syndicate_customer_list = ["BT013","BT026","BT044","BT072","BT073"]
    filtered_syndicate_bets = syndicate_bets[(syndicate_bets['Code'].isin(syndicate_customer_list)) & 
                                            (syndicate_bets['Result'] != "Void")].reset_index(drop=True)

    # conert str to float
    for col in ['Stake', 'Payout', 'HKD Stake', 'HKD Payout', 'Level Stake', 'Level Payout']:
        filtered_syndicate_bets[col] = filtered_syndicate_bets[col].str.replace(',', '').astype(float)

    # convert HK odds to Euro odds
    filtered_syndicate_bets['Price'] = round((filtered_syndicate_bets['Price'] + 1), 2) 

    # convert time to utc datetime
    for col in ['Bet Time', 'Kick Off Time']:
        filtered_syndicate_bets[col] = pd.to_datetime(filtered_syndicate_bets[col]).dt.tz_localize('UTC')

    # convert HCP to float value
    filtered_syndicate_bets['HCP'] = filtered_syndicate_bets['HCP'].apply(parse_number)
    filtered_syndicate_bets['FT/HT'] = filtered_syndicate_bets['FT/HT'].str.strip()

    # combine duplicated bets
    processed_syndicate_bets = combine_duplicate_bets(filtered_syndicate_bets)

    return processed_syndicate_bets.sort_values('Bet Time', ascending=False).reset_index(drop=True)


### Convert HCP to RMM format (Function in 'read_preprocess_syndicate_bets()')
def parse_number(hcp):
    try:
        if '/' in hcp:
            parts = hcp.split('/')
            numerator = float(parts[0])
            denominator = float(parts[1])

            if hcp[0] == "-":
                return round((numerator - denominator) / 2, 2)
            else:
                return round((numerator + denominator) / 2, 2)
            
        else:
            return float(hcp)
            
    except:
        return hcp
    
### Combine duplicate bets (Function in 'read_preprocess_syndicate_bets()')
def combine_duplicate_bets(bets_df):
    bets_df = bets_df.sort_values('Bet Time', ascending=False)
    bets_df['Unique bet'] = bets_df['Kick Off Time'].astype(str) + bets_df['League'] + bets_df['Home'] + \
                            bets_df['Away'] + bets_df['FT/HT'] + bets_df['Selection'] + \
                            bets_df['HCP'].astype(str) + bets_df['Status'] + bets_df['Live Mins']

    duplicate_bet_list = bets_df[bets_df.duplicated(subset=['Unique bet'], keep=False)]['Unique bet'].drop_duplicates().tolist()

    combine_bets_df = bets_df[~bets_df['Unique bet'].isin(duplicate_bet_list)]

    for uid in duplicate_bet_list:
        dup_bets = bets_df[bets_df['Unique bet'] == uid].reset_index(drop=True)

        new_combined_bet = dup_bets.iloc[0].to_dict()

        for col in ['Stake', 'Payout', 'HKD Stake', 'HKD Payout']:
            new_combined_bet[col] = dup_bets[col].sum()

        new_combined_bet['Price'] = round(((dup_bets['Stake'] * dup_bets['Price']).sum() / dup_bets['Stake'].sum()), 3)
            
        new_combined_bet['Level Payout'] = round((new_combined_bet['Payout'] / new_combined_bet['Stake'] * 1000), 2)
            
        combine_bets_df = pd.concat([combine_bets_df, pd.DataFrame([new_combined_bet])], ignore_index=True)

    return combine_bets_df


'''
def read_processed_bets():
    directory = 'result/Processed Bets'

    processed_bet_df = pd.DataFrame()

    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path)
        processed_bet_df = pd.concat([processed_bet_df, df])

    for col in ['Match date', 'Single Place date']:
        processed_bet_df[col] = pd.to_datetime(processed_bet_df[col])

    return processed_bet_df.sort_values('Single Place date', ascending=False)
'''
