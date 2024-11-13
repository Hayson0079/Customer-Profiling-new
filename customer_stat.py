import pandas as pd

from data_functions import read_198_alert_list, read_new_bets, read_preprocess_syndicate_bets
from bet_processing import max_bet_rate, alert_ip_check, combine_similar_bets, syndicate_bet_compare, rmm_sharp_bet_compare
from customer_class import Customer


def customer_stat(bets_df):
    customer_list = []

    for unique_customer, single_customer_bet_df in bets_df.groupby(['Customer id', 'Customer name']):
        # create each unique Customer
        new_customer = Customer(unique_customer[0], unique_customer[1], single_customer_bet_df)

        # append new customer to the output list
        customer_list.append(new_customer.to_dict())

    return pd.DataFrame(customer_list).sort_values('last_bet_time', ascending=False).reset_index(drop=True)


all_bets = read_new_bets()
alert_ip_list = read_198_alert_list()[0]
syndicate_bets = read_preprocess_syndicate_bets()

all_bets = alert_ip_check(all_bets, alert_ip_list)
combined_all_bets = combine_similar_bets(all_bets)

rmm_sharp_accounts = ["oscar8800", "client32", "ys1010"]
rmm_compared_bets_df = rmm_sharp_bet_compare(combined_all_bets, rmm_sharp_accounts)
processed_bets_df = syndicate_bet_compare(rmm_compared_bets_df, syndicate_bets)
processed_bets_df = max_bet_rate(processed_bets_df)

customer_df = customer_stat(processed_bets_df)

def market_league_analysis(customer_stat_df):
    result_df = customer_stat_df[['name', 'no_of_settled_bet', 'market_dict', 'league_dict']]
    result_df[['most_frequent_market', 'market_amount']] = customer_stat_df['market_dict'].apply(find_largest_dict_entry).apply(pd.Series) 
    result_df['market %'] = round(result_df['market_amount'] / result_df['no_of_settled_bet'] * 100, 2)

    result_df[['most_frequent_league', 'league_amount']] = customer_stat_df['league_dict'].apply(find_largest_dict_entry).apply(pd.Series)
    result_df['league %'] = round(result_df['league_amount'] / result_df['no_of_settled_bet'] * 100, 2)

    return result_df

def find_largest_dict_entry(row):
    if not(bool(row)):
        return None, None
    
    else:
        max_key = max(row, key= row.get)
        max_value = row[max_key]
        return max_key, max_value
