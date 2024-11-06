import pandas as pd

from data_functions import read_customer_info

customer_stat = pd.read_csv('result/Customer stat.csv')
customer_info = read_customer_info()

combined_stat = pd.merge(customer_stat, customer_info[['Customer id', 'Level name']], 
                         left_on = 'id', right_on = 'Customer id', how = 'inner').drop('Customer id', axis = 1)


level_list = ['SHARP ACC', 'ROBOTIC ACC', 'WEAK', 'Default']
learning_stat = combined_stat[combined_stat['Level name'].isin(level_list)]

learning_stat['Level type'], unique_value = pd.factorize(learning_stat['Level name'])
learning_data = learning_stat.drop(['id', 'name', 'last_bet_time', 'market_dict', 'league_dict', 'Level name'], axis=1)

cor = learning_data.corr()
grouped = learning_data.groupby('Level type').agg(['mean', 'median'])


