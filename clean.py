import pandas as pd
import numpy as np
from dateutil.parser import parse

def change_pos_position(season): #some season have position labeled as pos
    try:
        season['Position']=season['Pos']
        season.drop('Pos',axis=1,inplace=True)
    except:
        pass

def create_hometeam(season):
    """
    input: dataframe of season

    create hometeam feature

    output: none
    """
    grouped = season.groupby('game_id')
    home_team=[]
    for group in list(grouped.groups.fromkeys(season['game_id']).keys()): #need the game_id in the same order as the dataframe
        values = grouped.groups[group].get_values()
        #with how espn box scores work, the away team is listed first and hometeam second
        home_team.append([False if season.iloc[values]['team'].iloc[i] ==  season.iloc[values]['team'].iloc[0] else True for i in range(len(values))])
    home_team = [item for sublist in home_team for item in sublist] #need to flatten list of lists into just a single list
    season['home_team']=pd.Series(home_team)

def calc_days_from_opener(season):
    """
    input: dataframe of season

    make days after opener feature to use for rest

    output: none
    """
    season['date']=pd.Series([parse(season['date'][i]) for i in range(len(season))])
    season['days_after_opener'] = season['date']-season['date'].min() #get a time delta for the number of days after the opener
    season.drop('date',axis=1,inplace=True)

def make_splits(season):
    """
    input: dataframe of season

    split FG, FT, 3PT into makes and attempts

    output: none
    """

    season.fillna('0',inplace=True) #string so it can be split later
    season['Min']=season['Min'].map(lambda x: '0' if x.find('DNP')!= -1 else x) #some seasons have DNP, need to replace with 0
    season['Min']=season['Min'].map(lambda x: '0' if x.find('Did')!= -1 else x) #others have Did not play, also need to replace it

    season['FT_made']=season['FT'].map(lambda x: x.split('-')[0])
    season['FT_attempts']=season['FT'].map(lambda x: x.split('-')[-1]) #-1 because when filled na with '0' it is not 1

    season['3PT_made']=season['3PT'].map(lambda x: x.split('-')[0])
    season['3PT_attempts']=season['3PT'].map(lambda x: x.split('-')[-1]) #-1 because when filled na with '0' it is not 1

    season['FG_made']=season['FG'].map(lambda x: x.split('-')[0])
    season['FG_attempts']=season['FG'].map(lambda x: x.split('-')[-1]) #-1 because when filled na with '0' it is not 1

    season.drop(['FT','FG','3PT'],axis=1,inplace=True) #drop the string of makes - attempts

def convert_to_int(season):
    """
    input: dataframe of season

    convert numerical stats to into

    output: dataframe with ints
    """
    season=season[season['Min']!='--'] #drop rows where all stats are ---
    season['+/-']=season['+/-'].map(lambda x: '0' if x == '--' else x) #some seasons don't have +/-
    season[['+/-','home_team','AST','BLK','DREB','Min','OREB','PF','PTS','REB','STL','TO','FT_made',
            'FT_attempts','3PT_made','3PT_attempts','FG_made','FG_attempts']]=season[['+/-','home_team',
            'AST','BLK','DREB','Min','OREB','PF','PTS','REB','STL','TO','FT_made',
            'FT_attempts','3PT_made','3PT_attempts','FG_made','FG_attempts']].astype(int) #convert to int
    return season

def add_total_score(season):
    """
    input: dataframe of season

    add a total score feature to DataFrame

    output: dataframe with total score
    """
    grouped_games_score = season.groupby('game_id')
    game_totals=pd.DataFrame(grouped_games_score.sum()['PTS'])
    game_totals['Total_PTS']=game_totals['PTS']  #These two lines are because name 'PTS' needs to be changed
    game_totals.drop('PTS',axis=1,inplace=True)  #
    season=season.join(game_totals,on='game_id') #join totals to the right game id
    return season

def get_team_avgs(season):
    """
    input: dataframe of season

    get teams average stats

    output: dataframe containing average stats
    """
    grouped_teams = season.groupby('team')
    game_avgs=pd.DataFrame(grouped_teams.sum())
    game_avgs = game_avgs[['AST','BLK','DREB','OREB','PF','REB','STL','TO',
            'FT_made','FT_attempts','3PT_made','3PT_attempts','FG_made','FG_attempts']]/(len(season.groupby(['game_id','team']).mean())/30)
    game_avgs['AVG_score']=grouped_teams.sum()['PTS']/(len(season.groupby(['game_id','team']).mean())/30)
    game_avgs['Possessions']=game_avgs['FG_attempts']+game_avgs['TO'] #add estimate for possessions
    return game_avgs



def get_avgs_home_vs_away(season):
    """
    input: dataframe of season

    get team average stats based on away vs home games

    output: dataframe containing these stats
    """
    small_df=season[['game_id','team','home_team','Total_PTS']]
    grouped_teams_home = season[season['home_team']==1].groupby('team')
    grouped_teams_away = season[season['home_team']==0].groupby('team')
    avgs_home = grouped_teams_home.sum()[['+/-','AST','BLK','DREB','OREB','PF','REB','STL','TO',
            'FT_made','FT_attempts','3PT_made','3PT_attempts','FG_made','FG_attempts']]/(len(season.groupby(['game_id','team']).mean())/60)
    avgs_home['+/-']=avgs_home['+/-']/5
    avgs_home['AVG_score']=grouped_teams_home.sum()['PTS']/(len(season.groupby(['game_id','team']).mean())/60)
    avgs_home['Possessions']=avgs_home['FG_attempts']+avgs_home['TO'] #add estimate for possessions
    avgs_away = grouped_teams_away.sum()[['+/-','AST','BLK','DREB','OREB','PF','REB','STL','TO',
            'FT_made','FT_attempts','3PT_made','3PT_attempts','FG_made','FG_attempts']]/(len(season.groupby(['game_id','team']).mean())/60)
    avgs_away['+/-']=avgs_away['+/-']/5
    avgs_away['AVG_score']=grouped_teams_away.sum()['PTS']/(len(season.groupby(['game_id','team']).mean())/60)
    avgs_away['Possessions']=avgs_away['FG_attempts']+avgs_away['TO'] #add estimate for possessions

    # joined_data = small_df.join(avgs,on=['team','home_team'])
    # grouped_join = joined_data.groupby(['game_id','team']).mean()
    return avgs_home,avgs_away #grouped_join


def change_teamname(season):
    """
    input: dataframe of season

    Supersonics switched cities and names to Thunder, Bobcats to Hornets

    output: none
    """

    season['team']=season['team'].map(lambda x: 'Thunder' if x == 'SuperSonics' else x) #supersonics to Thunder
    season['team']=season['team'].map(lambda x: 'Hornets' if x == 'Bobcats' else x) #bobcats to hornets

def change_hornets_pelicans(season): #use for 2004-2013
    """
    input: dataframe of season

    The Hornets refer to two different teams. From 2002-2013 it was
    New Orleans, which are now the pelicans

    output: none
    """
    season['team']=season['team'].map(lambda x: 'Pelicans' if x == 'Hornets' else x)




def all_clean(season): #seasons 2014-2018
    """
    input: dataframe of season

    combine all functions into one

    output: cleaned dataframe
    """
    change_pos_position(season) #make sure position labeled correctly
    change_teamname(season) #changes supersonics and bobcats
    create_hometeam(season) #create hometeam feature
    calc_days_from_opener(season) #create days feature
    make_splits(season) #change the stats that are in for 'x-y' to two features with 'x' and 'y'
    season=convert_to_int(season) #convert all to ints
    season=add_total_score(season) #add total scores
    return season

def all_clean_pels(season): #seasons 2004-2013
    """
    input: dataframe of season

    combine all functions into one for when the pelicans were the hornets

    output: cleaned dataframe
    """
    change_pos_position(season) #make sure position labeled correctly
    change_hornets_pelicans(season) #when new orleans was the hornets, change to pelicans
    change_teamname(season) #changes supersonics and bobcats
    create_hometeam(season) #create hometeam feature
    calc_days_from_opener(season) #create days feature
    make_splits(season) #change the stats that are in for 'x-y' to two features with 'x' and 'y'
    season=convert_to_int(season) #convert all to ints
    season=add_total_score(season) #add total scores
    return season
