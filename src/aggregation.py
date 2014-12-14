#This script is responsible for iterating through the crowd and calling the corresposnding methods in pull_data.py to aggregate the user and projected accuracies of each user over the course of the season  

from pull_data import *
from accuracy import *
import csv

FINAL_WEEK = 13

reader = csv.DictReader(open('data/user_auth_info.csv', 'rU'))
fieldnames = ['user_email', 'team_key', 'user_accuracy', 'projection_accuracy', 'survey_results']
f = open('data/results.csv', 'a')
#f.truncate()
writer = csv.DictWriter(f, fieldnames = fieldnames)
#writer.writeheader()
i = 0
for row in reader:
    i += 1
    print 'Processing fanstasy data for user %d...' %i 
    user = row['user_email']
    credentials = {'access_token':row['access_token'], 'access_token_secret':row['access_token_secret'], 'session_handle':row['session_handle']}
    session = create_session(credentials)
    
    team_accuracies = {}
    for week in xrange(1, FINAL_WEEK+1):
        lineups = get_user_lineups(session, week)
        for team in lineups:
            if team not in team_accuracies:
                team_accuracies[team] = {'user': {'N':0, 'D':0}, 'proj': {'N':0, 'D':0}}
            
            chosen_lineup = lineups[team]['chosen_lineup']
            projected_lineup = lineups[team]['projected_lineup']
            optimal_lineup = lineups[team]['optimal_lineup']
            user_N, user_D = get_lineup_accuracy(chosen_lineup, optimal_lineup)
            proj_N, proj_D = get_lineup_accuracy(projected_lineup, optimal_lineup)
            
            team_accuracies[team]['user']['N'] += user_N
            team_accuracies[team]['user']['D'] += user_D
            team_accuracies[team]['proj']['N'] += proj_N
            team_accuracies[team]['proj']['D'] += proj_D
    
    for team in team_accuracies:
        out_row = {
            'user_email': user, 
            'team_key': team, 
            'user_accuracy': 100*team_accuracies[team]['user']['N']/team_accuracies[team]['user']['D'], 
            'projection_accuracy': 100*team_accuracies[team]['proj']['N']/team_accuracies[team]['proj']['D'],
            'survey_results': None
        }
        writer.writerow(out_row)
    
            
        
        
        
        
    
    