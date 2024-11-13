from typing import Optional, Union
from datetime import datetime
import pandas as pd

main_market = ['Match Odds', 'Asian Handicap', 'Asian Over/Under', 'Total Goals']

tier_1_league = ['England Premier League', 'Primera Division', 'Serie A', 'Ligue 1', 'Bundesliga', \
                'UEFA Champions League', 'UEFA Europa League', 'CONMEBOL Copa America', 'UEFA Super Cup', \
                'Germany Super Cup', 'Community Shield', 'Super Copa']


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
        
        # market, league, bet_time dict & lifetime PnL
        self.market_dict = self.settled_bets['Market'].value_counts().to_dict()
        self.league_dict = self.settled_bets['League'].value_counts().to_dict()
        self.bet_time_dict, self.lifetime_pnl_change = self._update_betTime_dict_pnl_list_old(self.settled_bets)

        # market, league distribution
        self.no_of_main_market = self.settled_bets['Market'].isin(main_market).sum()
        self.no_of_ht_market = self.settled_bets['Market'].str.contains("Half Time").sum()
        self.no_of_corner_market = self.settled_bets['Market'].str.contains("Corners").sum()
        self.no_of_booking_market = self.settled_bets['Market'].str.contains("Bookings").sum()
        self.no_of_tier_1_league = self.settled_bets['League'].isin(tier_1_league).sum()
        
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
        self.main_market_rate = (self.no_of_main_market / self.no_of_settled_bet) if self.no_of_settled_bet != 0 else 0
        self.ht_market_rate = (self.no_of_ht_market / self.no_of_settled_bet) if self.no_of_settled_bet != 0 else 0
        self.corner_market_rate = (self.no_of_corner_market / self.no_of_settled_bet) if self.no_of_settled_bet != 0 else 0
        self.booking_market_rate = (self.no_of_booking_market / self.no_of_settled_bet) if self.no_of_settled_bet != 0 else 0
        self.tier_1_league_rate = (self.no_of_tier_1_league / self.no_of_settled_bet) if self.no_of_settled_bet != 0 else 0
        self.bet_frequency = (self.no_of_bet / self.no_of_unique_placing_day) if self.no_of_unique_placing_day != 0 else 0
        self.roi = (self.total_pnl / self.total_settled_stake) if self.total_settled_stake != 0 else 0
        self.roi_level_stake = (self.total_level_stake_pnl / self.total_level_stake) if self.total_level_stake != 0 else 0
        
        
    def to_dict(self):
        return self.__dict__

    
    def _update_betTime_dict_pnl_list(self, settled_bets_df: pd.DataFrame):
        settled_bets_df = settled_bets_df.sort_values(by='Place date', ascending = True)

        # bet time period dict
        group = [-float('inf'), 0, 30*60, 120*60, 240*60, 480*60, 24*60*60, float('inf')]
        group_name = ['no_of_ir_bet', 'no_of_KO_30_KO_bet', 'no_of_KO_120_KO_30_bet', 'no_of_KO_240_KO_120_bet', \
                    'no_of_KO_480_KO_240_bet', 'no_of_KO_1day_KO_480_bet', 'no_of_active_KO_1day_bet']

        settled_bets_df['bet_time_diff'] = (settled_bets_df['Match date'] - settled_bets_df['Place date']).dt.total_seconds()

        settled_bets_df['bet_time_period'] = pd.cut(settled_bets_df['bet_time_diff'], bins = group, labels = group_name)

        bet_time_dict = settled_bets_df['bet_time_period'].value_counts().to_dict()

        # cum pnl
        settled_bets_df['cumulative_pnl'] = settled_bets_df['Customer P/L'].shift(fill_value=0).cumsum()
        cum_pnl_list = settled_bets_df['cumulative_pnl'].to_list()

        return bet_time_dict, cum_pnl_list
        

    def _update_betTime_dict_pnl_list_old(self, settled_bets_df: pd.DataFrame):
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
        
        for index, row in settled_bets_df.iterrows():
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
        
        return bet_time_dict, pnl_list
