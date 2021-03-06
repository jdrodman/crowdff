Crowdff
=======

Welcome to CrowdFF, a crowd-based research project about Fantasy Football.

CrowdFF pulls the roster data from Yahoo users (who have provided authorization), each week determining the lineup chosen by the user, the best-projected lineup, and the post-facto optimal lineups.  Over the course of a season, users are assigned an aggregated accuracy score and a corresponding projection score based on how similar their chosen and projected lineups are to the optimal lineups.  This allows us to see how well users fare compared to automated projections.      

Here’s everything you need to know about this repository:

The /docs/ directory contains:
- README.md: the document you are currently reading
- Work Flow Diagram.pdf: a flow diagram of the CrowdFF’s end-to-end process
- questionaire.png: a screen shot of the Google survey sent to users
- yahoo_authorization.png: a screen shot of the Yahoo API authorization page that users are directed to in order to provide access to their roster data
- yahoo_approval.png: a screen shot of a sample following page within the Yahoo authorization flow.  Users complete the process by sending the code back to us.
- CrowdFF Figures and Screenshots.pdf: contains a brief demo of the system and a compilation of the figures produced in analyzing the data
- CrowdFF_Logo.png: our designed logo 

The /src/ directory contains the code and scripts used throughout the process:
- pull_data.py: code which provides methods used to manage the entire process of getting authorization from users, pulling data from both Yahoo API and ESPN website, and returning the optimal, best_projected, and chosen lineups for a given user in a given week
- store_creds.py: a script which launches a new user authorization session via Terminal and stores the tokens required for future access in src/data/user_auth_info.csv
- aggregation.py: a script which iterates through the crowd in src/data/user_auth_info.csv and calls the corresponding methods in pull_data.py to aggregate the user and projected accuracies of each user over the course of the season.  It outputs these accuracies to /src/data/results.csv
- accuracy.py: code which contains the main quality module. It provides a method for computing the accuracy of a user or projected roster for a given team in a given week.  It is called from within the aggregation module.
- finalgraph1.html, finalgraph2.html, finalgraph3.html: html code for the Google graphs produced 
- /data/: this directory contains the data used and produced by the system
	- user_auth_info.csv: stores the user authorization credentials necessary to pull roster data
	- results.csv: output of the combined aggregation and quality modules
	- survey_responses.csv: output from the follow-up survey      

NOTE: Due to the public nature of Github repos and the private nature of the data collected, all personal identifications have been redacted.  In addition, the secret access tokens associated with user accounts have been redacted from /data/user_auth_info.csv to prevent public access to users fantasy data.  
    