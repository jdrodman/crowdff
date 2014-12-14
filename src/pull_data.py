## This module is reponsible for providing methods to manage the entire process of getting authorization from users, pulling data from both Yahoo API and ESPN website, and returning the optimal, best_projected, and chosen lineups for given user in a given week 

from rauth import OAuth1Service
from rauth.utils import parse_utf8_qsl
from bs4 import BeautifulSoup
from operator import itemgetter
import urllib2
import xmltodict
import csv

OAUTH_CONSUMER_KEY = 'dj0yJmk9cGFPR3dLTk01b015JmQ9WVdrOWRtOUdOemhKTnpnbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD00MA--'
OAUTH_SHARED_SECRET = '492d0e9298a3e9d9483ba28db10c8db48e9c1880'
GET_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_token'
AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth/v2/request_auth'
REQUEST_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
BASE_URL = 'http://fantasysports.yahooapis.com/fantasy/v2/'
CALLBACK_URL = 'oob'
#CALLBACK_URL = 'https://crowd-fantasy-football.herokuapp.com/'


def create_auth_file():
    fieldnames = ['user_email', 'access_token', 'access_token_secret', 'session_handle']
    f = open('data/user_auth_info.csv', 'w')
    f.truncate() 
    writer = csv.DictWriter(f, fieldnames = fieldnames)
    writer.writeheader()

def store_credentials(email):
    fieldnames = ['user_email', 'access_token', 'access_token_secret', 'session_handle']
    writer = csv.DictWriter(open('data/user_auth_info.csv', 'a'), fieldnames = fieldnames)
    yahoo = OAuth1Service( consumer_key=OAUTH_CONSUMER_KEY, consumer_secret=OAUTH_SHARED_SECRET, name='yahoo', access_token_url=GET_TOKEN_URL, authorize_url=AUTHORIZATION_URL, request_token_url=REQUEST_TOKEN_URL, base_url= BASE_URL) 
    request_token, request_token_secret = yahoo.get_request_token(data = { 'oauth_callback': CALLBACK_URL })
    auth_url = yahoo.get_authorize_url(request_token) 
    print 'Visit this URL in your browser: ' + auth_url 
    pin = raw_input('Enter PIN from browser: ')
    
    raw_access = yahoo.get_raw_access_token(request_token, request_token_secret, params={"oauth_verifier": pin})
    parsed_access_token = parse_utf8_qsl(raw_access.content)
    access_token = parsed_access_token["oauth_token"]
    access_token_secret = parsed_access_token["oauth_token_secret"]
    session_handle = parsed_access_token["oauth_session_handle"]
    writer.writerow({'user_email': email, 'access_token':access_token, 'access_token_secret':access_token_secret, 'session_handle':session_handle})

def create_session(credentials):
    yahoo = OAuth1Service( consumer_key=OAUTH_CONSUMER_KEY, consumer_secret=OAUTH_SHARED_SECRET, name='yahoo', access_token_url=GET_TOKEN_URL, authorize_url=AUTHORIZATION_URL, request_token_url=REQUEST_TOKEN_URL, base_url= BASE_URL)
    saved_access_token = credentials['access_token']
    saved_access_token_secret = credentials['access_token_secret']
    saved_session_handle = credentials['session_handle']
    
    access_token, access_token_secret = yahoo.get_access_token(saved_access_token, saved_access_token_secret, params={"oauth_session_handle":saved_session_handle})
    
    session = yahoo.get_session((access_token, access_token_secret))
    return session

def make_request(session, request_str):
    r = session.get(request_str)
    data = xmltodict.parse(r.text)
    return data

def get_league_info(session):
    
    leagues_info = {}
    request_str = 'users;use_login=1/games;game_keys=nfl/leagues/settings'
    data = make_request(session, request_str)
    leagues = data['fantasy_content']['users']['user']['games']['game']['leagues']
    if int(leagues['@count']) == 1: league_list = [leagues['league']]
    else: league_list = leagues['league']
    for league in league_list:
        settings = league['settings']
        stat_modifiers = settings['stat_modifiers']['stats']['stat']
        stat_cats = settings['stat_categories']['stats']['stat']
        
        #find stat_id for reception category
        stat_id = None
        for stat in stat_cats:
            if str(stat['display_name']) == 'Rec':
                stat_id = stat['stat_id']
                break
        
        #find point value of a reception
        rec_val = 0
        for stat in stat_modifiers:
            if stat['stat_id'] == stat_id:
                rec_val = float(stat['value'])
                break
        
        #determine league type based on point value of a reception
        league_type = ''
        if rec_val == 1.0: league_type = 'PPR'
        elif rec_val == 0.5: league_type = 'HALF_PPR'
        elif rec_val == 0.0: league_type = 'STANDARD'
        else: league_type = 'OTHER'
        
        #get roster position info
        roster_positions = settings['roster_positions']['roster_position']
        roster_pos_count = {}
        for position in roster_positions:
            roster_pos_count[str(position['position'])] = int(position['count'])
        
        leagues_info[int(league['league_id'])] = {'scoring_type':league_type, 'roster_positions':roster_pos_count}
        
    return leagues_info
   
def get_user_lineups(session, week):
    #return a dict of dictiornaries conataining actual and projected points of players on a roster in a given week
    request_str = 'users;use_login=1/games;game_keys=nfl/leagues/teams/roster;week=%s/players/stats' % week
    data = make_request(session, request_str)
    stats = {}
    leagues = data['fantasy_content']['users']['user']['games']['game']['leagues']
    if int(leagues['@count']) == 1: league_list = [leagues['league']]
    else: league_list = leagues['league']
    leagues_info = get_league_info(session)
    for league in league_list: 
        league_id = int(league['league_id'])
        teams = league['teams']
        if int(teams['@count']) == 1: team_list = [teams['team']]
        else: team_list = teams['team']
        for team in team_list:
            roster_stats = {}
            player_list = team['roster']['players']['player']
            chosen_lineup = {}
            roster_positions = leagues_info[league_id]['roster_positions']
            for pos in roster_positions: chosen_lineup[pos] = []
            for player in player_list:
                positions = player['eligible_positions']['position']
                if isinstance(positions, unicode): positions = [positions]
                name = str(player['name']['full'])
                if 'DEF' in positions: name = str(player['editorial_team_abbr'])
                selected_position = player['selected_position']['position']
                chosen_lineup[selected_position].append(name)
                actual_points = float(player['player_points']['total'])
                league_type = leagues_info[league_id]['scoring_type']
                player_team = str(player['editorial_team_abbr'])
                projected_points = 0.0
                if selected_position != 'BN' and selected_position != 'IR': 
                    projected_points = get_projected_points(name, player_team, selected_position, week, league_type)
                for pos in positions:
                    pos = str(pos)
                    if pos not in roster_stats: roster_stats[pos] = []
                    roster_stats[pos].append({'name':name, 'actual_points':actual_points, 'projected_points':projected_points})
                if 'W/R/T' in roster_stats: del roster_stats['W/R/T']
                
            del chosen_lineup['BN']
            if 'IR' in chosen_lineup.keys(): del chosen_lineup['IR']
            optimal_lineup, projected_lineup = get_lineups_from_stats(roster_stats, roster_positions)
                        
            stats[str(team['team_key'])] = {'optimal_lineup':optimal_lineup, 'chosen_lineup':chosen_lineup, 'projected_lineup':projected_lineup}
                                  
    return stats
            
def get_lineups_from_stats(roster_stats, roster_positions):
    #return the best_projected and post-facto optimal lineups for a given weekly roster with stats
    optimal_lineup = {}
    projected_lineup = {}
    l = {}    
    for position in roster_stats:
        l[position] = [ (player['name'], player['actual_points'], player['projected_points']) for player in roster_stats[position] ]
        optimal_ranked = sorted(l[position], key=itemgetter(1), reverse=True)
        projected_ranked = sorted(l[position], key=itemgetter(2), reverse=True)
                
        optimal_lineup[position] = optimal_ranked[:roster_positions[position]]
        projected_lineup[position] = projected_ranked[:roster_positions[position]]
            
    optimal_flexes = set()
    projected_flexes = set()
    for position in ['WR', 'RB', 'TE']:
        optimal_flexes |= (set(l[position]) - set(optimal_lineup[position]))
        projected_flexes |= (set(l[position]) - set(projected_lineup[position]))

    ranked_optimal_flexes = sorted(list(optimal_flexes), key=itemgetter(1), reverse=True)
    ranked_projected_flexes = sorted(list(projected_flexes), key=itemgetter(2), reverse=True)
    
    if 'W/R/T' in roster_positions:
        optimal_lineup['W/R/T'] = ranked_optimal_flexes[:roster_positions['W/R/T']]
        projected_lineup['W/R/T'] = ranked_projected_flexes[:roster_positions['W/R/T']]
        
    for position in optimal_lineup:
        optimal_lineup[position] = [name for (name, a_point, p_points) in optimal_lineup[position]]
        projected_lineup[position] = [name for (name, a_point, p_points) in projected_lineup[position]]
        
    return optimal_lineup, projected_lineup
        

# pull projected points from parsed espn html 
def get_projected_points(player_name, team, pos, week, league_type):
    if pos == 'DEF': 
        player_name = get_defense_name(player_name)
        team = player_name 
    firstname = player_name.split()[0]
    lastname = player_name.split()[1]
    url = 'http://games.espn.go.com/ffl/tools/projections?&scoringPeriodId=%s&seasonId=2014&search=%s' %(week, lastname)
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page)
    tags0 = soup.body.find_all('tr', attrs={'class' : 'pncPlayerRow playerTableBgRow0'})
    tags1 = soup.body.find_all('tr', attrs={'class' : 'pncPlayerRow playerTableBgRow1'})
    tags = tags0 + tags1
    for tag in tags:
        player_proj = []
        for child in tag.contents:
            player_proj.append(child.get_text())
        if firstname + ' ' + lastname in player_proj[0] and team in player_proj[0]:
            base_points = str(player_proj[-1])
            if base_points == '--': return 0.0
            else: base_points = float(player_proj[-1])
            num_rec = int(player_proj[-4])
            added_value = 0.0
            if league_type == 'PPR': added_value = 1.0*num_rec
            elif league_type == 'HALF_PPR': added_value = 0.5*num_rec
            return base_points + added_value 
     
def get_defense_name(loc_id):
    teams = {
        'Bal':'Ravens',
        'Cin':'Bengals',
        'Cle':'Browns',
        'Pit':'Steelers',
        'Hou':'Texans',
        'Ind':'Colts',
        'Jax':'Jaguars',
        'Ten':'Titans',
        'Buf':'Bills',
        'Mia':'Dolphins',
        'NE':'Patriots',
        'NYJ': 'Jets',
        'Den':'Broncos',
        'KC':'Chiefs',
        'Oak':'Raiders',
        'SD':'Chargers',
        'Chi':'Bears',
        'Det':'Lions',
        'GB':'Packers',
        'Min':'Vikings',
        'Atl':'Falcons',
        'Car':'Panthers',
        'NO':'Saints',
        'TB':'Buccaneers',
        'Dal':'Cowboys',
        'NYG':'Giants',
        'Phi':'Eagles',
        'Was':'Redskins',
        'Ari':'Cardinals',
        'SF':'49ers',
        'Sea':'Seahawks',
        'StL':'Rams'
    }
    
    return teams[loc_id] + ' D/ST'
