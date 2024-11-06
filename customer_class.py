from typing import Optional, Union
from datetime import datetime
import pandas as pd


class Customer:
    def __init__(self, customer_id: str, customer_name: str, bets_df: pd.DataFrame):
        # basic info
        self.id = customer_id
        self.name = customer_name
        self.last_bet_time = bets_df['Place date'].max()
        
        # transaction records
        self.all_bets = bets_df
        
        self.settled_bets = bets_df[bets_df['State'] == "Settled"]
        
        # bet count 
        self.no_of_bet = bets_df.shape[0]
        self.no_of_diff_bet = bets_df.drop_duplicates(subset=['Market id', 'Selection id', 'Match time']).shape[0]
        self.no_of_settled_bet = self.settled_bets.shape[0]
        self.no_of_rejected_bet = bets_df[bets_df['State'] == "Rejected"].shape[0]
        self.no_of_voided_bet = bets_df[bets_df['State'] == "Voided"].shape[0]
        self.no_of_ir_settled_bet = bets_df[(bets_df['IR'].notnull()) & (bets_df['State'] == "Settled")].shape[0]
        self.no_of_ir_rejected_bet = bets_df[(bets_df['IR'].notnull()) & (bets_df['State'] == "Rejected")].shape[0]
        self.no_of_ir_voided_bet = bets_df[(bets_df['IR'].notnull()) & (bets_df['State'] == "Voided")].shape[0]
        self.no_of_win_bet = self.settled_bets[self.settled_bets['Result'].isin(["Win", "WinHalf"])].shape[0]
        self.no_of_lose_bet = self.settled_bets[self.settled_bets['Result'].isin(["Lose", "LoseHalf"])].shape[0]
        self.no_of_draw_bet = self.settled_bets[self.settled_bets['Result'] == "Draw"].shape[0]
        self.no_of_ir_win_bet = self.settled_bets[(self.settled_bets['IR'].notnull()) & (self.settled_bets['Result'].isin(["Win", "WinHalf"]))].shape[0]
        self.no_of_ir_lose_bet = self.settled_bets[(self.settled_bets['IR'].notnull()) & (self.settled_bets['Result'].isin(["Lose", "LoseHalf"]))].shape[0]
        self.no_of_ir_draw_bet = self.settled_bets[(self.settled_bets['IR'].notnull()) & (self.settled_bets['Result'] == "Draw")].shape[0]
        self.no_of_alert_IP_bet = bets_df['Alert IP bet'].sum()
        
        # sharp bet count
        self.no_of_db_following_sharp_bet = bets_df['Follow sharp bet'].sum()
        self.no_of_db_oppositing_sharp_bet = bets_df['Opposite sharp bet'].sum()

        # stake & pnl
        self.total_settled_stake = self.settled_bets['Customer stake'].sum()
        self.total_pnl = bets_df['Customer P/L'].sum()
        self.total_level_stake = self.no_of_settled_bet
        self.total_level_stake_pnl = round(bets_df['Level stake PnL'].sum(), 2)
        
        # unique placing date count 
        self.no_of_unique_placing_day = (self.settled_bets['Place date'].dt.date).nunique()
        
        # market, league, bet_time distribution & lifetime PnL
        self.market_dict, self.league_dict, self.bet_time_dict, self.lifetime_pnl_change = self._update_market_league_betTime_dict_pnl_list(self.settled_bets)
        
        # Rate
        self.rejected_bet_rate = (self.no_of_rejected_bet / self.no_of_bet) if self.no_of_bet != 0 else 0
        self.alert_IP_rate = (self.no_of_alert_IP_bet / self.no_of_bet) if self.no_of_bet != 0 else 0
        self.avg_max_bet_rate = bets_df['Max bet rate'].mean()
        self.follow_sharp_bet_rate = (self.no_of_db_following_sharp_bet / self.no_of_bet) if self.no_of_bet != 0 else 0
        self.opposite_sharp_bet_rate = (self.no_of_db_oppositing_sharp_bet / self.no_of_bet) if self.no_of_bet != 0 else 0
        self.avg_point_diff_with_sharp_bet = (bets_df['Point diff with following sharp bet'].sum() / self.no_of_db_following_sharp_bet) if self.no_of_db_following_sharp_bet != 0 else 0
        self.avg_mean_stake = self.settled_bets['Customer stake'].mean()
        self.avg_median_stake = self.settled_bets['Customer stake'].median()
        self.avg_pnl = self.settled_bets['Customer stake'].mean()
        self.avg_level_stake_pnl = self.settled_bets['Level stake PnL'].mean()
        self.ir_bet_rate = (self.no_of_ir_settled_bet / self.no_of_settled_bet) if self.no_of_settled_bet != 0 else 0
        self.bet_frequency = (self.no_of_bet / self.no_of_unique_placing_day) if self.no_of_unique_placing_day != 0 else 0
        self.roi = (self.total_pnl / self.total_settled_stake) if self.total_settled_stake != 0 else 0
        self.roi_level_stake = (self.total_level_stake_pnl / self.total_level_stake) if self.total_level_stake != 0 else 0
        
        
    def to_dict(self):
        return self.__dict__

    
    def _update_market_league_betTime_dict_pnl_list(self, settled_bets_df: pd.DataFrame):
        market_dict = {}
        league_dict = {}
        bet_time_dict = {
            'no_of_ir_bet': 0,
            'no_of_KO_30_KO_bet': 0,
            'no_of_KO_120_KO_30_bet': 0,
            'no_of_KO_240_KO_120_bet': 0,
            'no_of_KO_480_KO_240_bet': 0,
            'no_of_KO_1day_KO_480_bet': 0,
            'no_of_active_KO_1day_bet': 0
        }
        pnl_list = [0]

        settled_bets_df = settled_bets_df.sort_values(by='Place date', ascending = True)

        
        for index, row in settled_bets_df.iterrows():
            # mareket dict
            if row['Market'] in market_dict.keys():
                market_dict[row['Market']] += 1

            else:
                market_dict[row['Market']] = 1

            # league dict
            if row['League'] in league_dict.keys():
                league_dict[row['League']] += 1

            else:
                league_dict[row['League']] = 1

            # betTime dict
            time_diff = (row['Match date'] - row['Place date']).total_seconds()
            
            if time_diff < 0:
                bet_time_dict['no_of_ir_bet'] += 1
            
            elif time_diff < 30*60:
                bet_time_dict['no_of_KO_30_KO_bet'] += 1
                
            elif time_diff < 120*60:
                bet_time_dict['no_of_KO_120_KO_30_bet'] += 1
                
            elif time_diff < 240*60:
                bet_time_dict['no_of_KO_240_KO_120_bet'] += 1
                
            elif time_diff < 480*60:
                bet_time_dict['no_of_KO_480_KO_240_bet'] += 1
                
            elif time_diff < 24*60*60:
                bet_time_dict['no_of_KO_1day_KO_480_bet'] += 1
            
            else:
                bet_time_dict['no_of_active_KO_1day_bet'] += 1

            # lifetime PnL
            pnl_list.append(pnl_list[len(pnl_list) - 1] + row['Customer P/L'])
        
        return market_dict, league_dict, bet_time_dict, pnl_list
        

    