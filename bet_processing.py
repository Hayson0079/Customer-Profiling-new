import pandas as pd
from fuzzywuzzy import fuzz

### Set up 'Max bet rate'
def max_bet_rate(bets_df):
    bets_df['Max bet rate'] = bets_df['Customer stake'] / bets_df['Max stake']

    return bets_df

### Combine similar bets per customer
def combine_similar_bets(bets_df):
    # Non 'Settled' bets
    non_settled_bets_df = bets_df[bets_df['State'] != "Settled"]

    # Settled bets
    sorted_bets_df = bets_df[bets_df['State'] == "Settled"].sort_values(by = ['Customer id', 'Place date', 'Market id', 'Selection id', 'IR'])
    grouped = sorted_bets_df.groupby('Customer id')

    result_list = []

    # group bets placed within 1 min per unique market, selection and IR time
    for _, group in grouped:
        columns_check = ['Market id', 'Selection id', 'IR']
        prev_time = None
        prev_bet = None
        combine_bet_list = []

        for index, row in group.iterrows():
            if (prev_time == None) or (((row['Place date'] - prev_time).total_seconds() <= 60) and (prev_bet[columns_check].to_dict() == row[columns_check].to_dict())):
                combine_bet_list.append(row)
                    
            else:
                result_list.append(bet_combine(combine_bet_list))
                combine_bet_list = [row]
                
            prev_time = row['Place date']
            prev_bet = row

        if combine_bet_list:
            result_list.append(bet_combine(combine_bet_list))

    settled_bets_df = pd.DataFrame(result_list)
    output = pd.concat([settled_bets_df, non_settled_bets_df], axis=0, ignore_index=True).sort_values('Place date').reset_index(drop=True)
    output['Level stake PnL'] = output['Customer P/L'] / output['Customer stake']

    return output

### Combine list of Series bet to one single bet (Function in 'combine_similar_bets()')
def bet_combine(bet_list):
    combined_bet = bet_list[0].to_dict()

    for col in ['Bet id', 'Plat bet id']:
        combined_bet[col] = '_'.join([str(s[col]) for s in bet_list])

    for col in ['Customer stake', 'Company stake', 'Possible payout', 'Customer P/L', 'CompanyPT P/L', ]:
        combined_bet[col] = sum(b[col] for b in bet_list)

    combined_bet['Odds'] = combined_bet['Possible payout'] / combined_bet['Customer stake']

    return combined_bet


### Alert IP check
def alert_ip_check(bets_df, alert_ip_list):
    bets_df['Alert IP bet'] = bets_df['IP'].isin(alert_ip_list)

    return bets_df


### RMM sharp account bet comapre
def rmm_sharp_bet_compare(bets_df, rmm_sharp_accounts_list):
    # add new columns to df
    bets_df['Follow sharp bet'] = False
    bets_df['Point diff with following sharp bet'] = None
    bets_df['Opposite sharp bet'] = False
    bets_df['Opposite odds'] = None
    bets_df['Sharp bet ID'] = None

    # max bet diff time between sharp bet & normal bet
    min_before_after = 5

    # oppposite markets (following = all markets)
    sharp_opp_markets = ["Asian Handicap", "Asian Handicap - Half Time",
                     "Asian Over/Under", "Asian Over/Under - Half Time", 
                     "Total Goals", "Asian Handicap - Corners", "Asian Over/Under - Corners", 
                     "Asian Handicap - Corners - Half Time", "Asian Over/Under - Corners - Half Time"]
    
    sharp_bets_df = bets_df[(bets_df['Customer name'].isin(rmm_sharp_accounts_list)) & (bets_df['State'] == "Settled")]
    non_sharp_bets_df = bets_df[~((bets_df['Customer name'].isin(rmm_sharp_accounts_list)) & (bets_df['State'] == "Settled"))]

    for _, sharp_bet in sharp_bets_df.iterrows():
        # following check
        following_normal_bet = non_sharp_bets_df[(non_sharp_bets_df['Market id'] == sharp_bet['Market id']) & \
                                        (non_sharp_bets_df['Selection id'] == sharp_bet['Selection id']) & \
                                        (non_sharp_bets_df['Match time'] == sharp_bet['Match time']) & \
                                        (abs(non_sharp_bets_df['Place date'] - sharp_bet['Place date']).dt.total_seconds() <= min_before_after*60)]

        if not(following_normal_bet.empty):
            for _, target_bet in following_normal_bet.iterrows():
                bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Follow sharp bet'] = True
                bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Point diff with following sharp bet'] = target_bet['Odds'] - sharp_bet['Odds']
                bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Sharp bet ID'] = sharp_bet['Bet id']

        # oppositing check
        if sharp_bet['Market'] in sharp_opp_markets:
            opp_selection_id = sharp_bet['Selection id'] - 1 if sharp_bet['Selection id'] % 2 != 0 else sharp_bet['Selection id'] + 1

            oppositing_normal_bet = non_sharp_bets_df[(non_sharp_bets_df['Market id'] == sharp_bet['Market id']) & \
                                        (non_sharp_bets_df['Selection id'] == opp_selection_id) & \
                                        (non_sharp_bets_df['Match time'] == sharp_bet['Match time']) & \
                                        (abs(non_sharp_bets_df['Place date'] - sharp_bet['Place date']).dt.total_seconds() <= min_before_after*60)]
            
            if not(oppositing_normal_bet.empty):
                for _, target_bet in oppositing_normal_bet.iterrows():
                    bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Opposite sharp bet'] = True
                    bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Opposite odds'] = sharp_bet['Odds']
                    bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Sharp bet ID'] = sharp_bet['Bet id']

    return bets_df


### Get unique DB market table (Function in )
def unique_198_match_market_table(customer_bets):
    customer_bets = customer_bets[customer_bets['Match time'] == "-"]

    desired_market = ["Asian Handicap", "Asian Over/Under", "Asian Over/Under - Half Time", "Asian Handicap - Half Time", 
                      "Total Goals", "Total Goals - Half Time", "Match Odds", "Match Odds - Half Time", "Match 1X2", "Match 1X2 - Half Time"]
    
    filtered_customer_bets = customer_bets[customer_bets['Market'].isin(desired_market)]
    table = filtered_customer_bets.drop_duplicates(subset='Market id', keep='first').reset_index(drop=True)
    table[['Home name','Away name']] = table['Match'].str.split(' v ', expand=True)

    return table[['League','Match', 'Match id', 'Match date', 'Market', 'Market id', 'Home name', 'Away name']]


### Brokerage syndicate bet comapre
def syndicate_bet_compare(bets_df, syndicate_bets):
    db_rmm_market_table = unique_198_match_market_table(bets_df)
    db_syndicate_bets = syndicate_bets[syndicate_bets['Status'] == "UnLive"]
    settled_bets_df = bets_df[bets_df['State'] == "Settled"]

    for _, syn_bet in db_syndicate_bets.iterrows():
        syn_market = find_desired_market_name(syn_bet)
        match_day_market = db_rmm_market_table[(db_rmm_market_table['Match date'] == syn_bet['Kick Off Time']) & \
                                               (db_rmm_market_table['Market'].isin(syn_market))]
        
        desired_market_detail = find_desired_market_id(match_day_market, syn_bet)

        if desired_market_detail['check']:
            for market_id in desired_market_detail['rmm_market_id']:
                # following check
                following_normal_bet = bets_df[(bets_df['Market id'] == market_id) & \
                                                (bets_df['Selection'] == desired_market_detail['rmm_follow_selection']) & \
                                                (bets_df['Match date'] == syn_bet['Kick Off Time']) & \
                                                (bets_df['Match time'] == "-")]

                if not(following_normal_bet.empty):
                    for _, target_bet in following_normal_bet.iterrows():
                        if all(bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Follow sharp bet'] == False):
                            bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Follow sharp bet'] = True
                            bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Point diff with following sharp bet'] = target_bet['Odds'] - syn_bet['Price']
                            bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Sharp bet ID'] = syn_bet['Code']

                # oppositing check
                if desired_market_detail['rmm_opposite_selection']:
                    oppositing_normal_bet = bets_df[(bets_df['Market id'] == market_id) & \
                                            (bets_df['Selection'] == desired_market_detail['rmm_opposite_selection']) & \
                                            (bets_df['Match date'] == syn_bet['Kick Off Time']) & \
                                            (bets_df['Match time'] == "-")]
                    
                    if not(oppositing_normal_bet.empty):
                        for _, target_bet in oppositing_normal_bet.iterrows():
                            if all(bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Opposite sharp bet'] == False):
                                bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Opposite sharp bet'] = True
                                bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Opposite odds'] = syn_bet['Price']
                                bets_df.loc[(bets_df['Bet id'] == target_bet['Bet id']), 'Sharp bet ID'] = syn_bet['Code']
    
    return bets_df


### Convert rmm market name from syndicate bet (Funciton in 'syndicate_bet_compare()')
def find_desired_market_name(row):
    # Match Odds
    if row['HCP'] == "1x2":
        if row['FT/HT'] == "FT":
            return ["Match Odds", "Match 1X2"]
        else:
            return ["Match Odds - Half Time", "Match 1X2 - Half Time"]

    # Handicap 
    elif row['Selection'] in ["Home", "Away"]:
        if row['FT/HT'] == "FT":
            return ["Asian Handicap"]
        else:
            return ["Asian Handicap - Half Time"]
    
    # Over/Under, Total Goals
    elif row['Selection'] in ["Over", "Under"]:
        if row['FT/HT'] == "FT":
            return ["Asian Over/Under", "Total Goals"]
        else:
            return ["Asian Over/Under - Half Time", "Total Goals - Half Time"]
            
    else: 
        return []

### Find the rmm match id for the syndicate bet (Function in 'syndicate_bet_compare()')
def find_desired_market_id(match_day_match, syn_bet):
    threshold = 70
    result = {'check': False,
              'rmm_market_id': [],
              'rmm_follow_selection': None,
              'rmm_opposite_selection': None}
    
    for index, row in match_day_match.iterrows():
        if (fuzz.ratio(syn_bet['Home'], row['Home name']) >= threshold) and \
            (fuzz.ratio(syn_bet['Away'], row['Away name']) >= threshold):
            result['check'] = True
            result['rmm_market_id'].append(row['Market id'])
            result['rmm_follow_selection'], result['rmm_opposite_selection'] = selection_convert(syn_bet['Selection'], syn_bet['HCP'], row['Home name'], row['Away name'])

    return result

## Convert syd hcp selection (Function in 'find_desired_market_id()')
def selection_convert(side, hcp, home, away):
    fol_sel = None
    opp_sel = None

    # Match Odds
    if hcp == "1x2":
        if (side == "Home") or (side == "HT Home"):
            fol_sel = home

        elif (side == "Away") or (side == "HT Away"):
            fol_sel = away

        else:
            fol_sel = "Draw"

    # HCP or OU
    else:
        if (side == "Home") or (side == "HT Home"):
            fol_sel = home + convert_hcp(hcp)
            opp_sel = away + convert_hcp(hcp*-1)
            
        elif (side == "Away") or (side == "HT Away"):
            fol_sel = away + convert_hcp(hcp)
            opp_sel = home + convert_hcp(hcp*-1)

        elif (side == "Over") or (side == "HT Over"):
            fol_sel = "Over " + str(hcp) + " goals"
            opp_sel = "Under " + str(hcp) + " goals"

        elif (side == "Under") or (side == "HT Under"):
            fol_sel = "Under " + str(hcp) + " goals"
            opp_sel = "Over " + str(hcp) + " goals"

    return fol_sel, opp_sel

## Convert syd hcp selection (Function in 'selection_convert()')
def convert_hcp(x):
    if x < 0:
        return f" {int(x) if x.is_integer() else x}"
    elif x > 0:
        return f" +{int(x) if x.is_integer() else x}"
    else:
        return ""


