#This script runs the data collecetion mechansim via terminal

from pull_data import *
import sys

#create_auth_file
email = raw_input('Enter email: ')
store_credentials(email)
