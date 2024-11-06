import pandas as pd

from data_functions import read_198_alert_list, read_new_bets, read_preprocess_syndicate_bets
from bet_processing import max_bet_rate, alert_ip_check, combine_similar_bets, syndicate_bet_compare, rmm_sharp_bet_compare
from customer_class import Customer


def customer_stat(bets_df):
    customer_list = []

    unique_customer_list = bets_df[['Customer id', 'Customer name']].drop_duplicates().values.tolist()

    for cus in unique_customer_list:

        ## Process the bets of each customer
        single_customer_bet_df = bets_df[bets_df['Customer name'] == cus[1]].reset_index(drop=True)
        
        # create new customer
        new_customer = Customer(cus[0], cus[1], single_customer_bet_df)
        
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

output = customer_df.drop(['all_bets', 'settled_bets', 'bet_time_dict', 'lifetime_pnl_change'], axis=1)
output = output.sort_values('last_bet_time', ascending=False)
output.to_csv('result/Customer stat.csv', index=False)

start_time = pd.Timestamp('2024-10-01 00:00:00+00:00', tz='UTC')
end_time = pd.Timestamp('2024-11-01 00:00:00+00:00', tz='UTC')

oct_bets_df = processed_bets_df[(processed_bets_df['Place date'] > start_time) & (processed_bets_df['Place date'] < end_time)]
oct_customer_df = customer_stat(oct_bets_df)

