# -*- coding: utf-8 -*-
"""
Created on Tue Sep 26 16:02:09 2017

@author: Khepry Quixote
"""
import argparse
import requests
import sys


from datetime import datetime, timedelta
from monthdelta import monthdelta
from pprint import pprint
from time import sleep

# handle incoming parameters,
# pushing their values into the
# args dictionary for later usage

arg_parser = argparse.ArgumentParser(description='Obtain earthquakes via ReSTful interface')

arg_parser.add_argument('--bgn_date',
                        type=str,
                        default='1898-01-01',
                        help='starting date')
arg_parser.add_argument('--max_date',
                        type=str,
                        default='2020-01-01',
                        help='maximum date')
arg_parser.add_argument('--iteration_type',
                        type=str,
                        default='years',
                        choices=('days', 'weeks', 'months', 'years'),
                        help='iteration type (e.g. days, weeks, months, years)')
arg_parser.add_argument('--how_many_iterations',
                        type=int,
                        default=5,
                        help='how many iterations')
arg_parser.add_argument('--minmagnitude',
                        type=float,
                        default=0.0,
                        help='minimum magnitude (0 or greater)')
arg_parser.add_argument('--sleep_seconds',
                        type=int,
                        default=5,
                        help='sleep seconds')

args = arg_parser.parse_args()


def get_next_dates_list(bgn_date_parm,
                        max_date_parm,
                        iteration_type,
                        how_many_iterations):
    bgn_end_dates_list = []
    date_time = bgn_date_parm
    for i in range(0, how_many_iterations):
        bgn_date_parm = date_time.strftime('%Y-%m-%d')
        try:
            if iteration_type == 'days':
                date_time += timedelta(days=1)
                end_date = (date_time + timedelta(days=1)).strftime('%Y-%m-%d')
            elif iteration_type == 'weeks':
                date_time += timedelta(weeks=1)
                end_date = date_time.strftime('%Y-%m-%d')
            elif iteration_type == 'months':
                date_time += monthdelta(months=1)
                end_date = date_time.strftime('%Y-%m-%d')
            elif iteration_type == 'years':
                date_time += monthdelta(months=12)
                end_date = date_time.strftime('%Y-%m-%d')
            else:
                date_time += timedelta(days=1)
                end_date = (date_time + timedelta(days=1)).strftime('%Y-%m-%d')
            if datetime.strptime(end_date, '%Y-%m-%d') < max_date:
                bgn_end_dates_list.append((bgn_date_parm, end_date))
            else:
                bgn_end_dates_list.append((bgn_date_parm, max_date.strftime('%Y-%m-%d')))
                break
        except Exception as e:
            sys.stderr.write('Exception: %s' % e)
    return bgn_end_dates_list


bgn_date = datetime.strptime(args.bgn_date, '%Y-%m-%d')
max_date = datetime.strptime(args.max_date, '%Y-%m-%d')
bgn_end_dates_list = get_next_dates_list(bgn_date,
                                    max_date,
                                    args.iteration_type,
                                    args.how_many_iterations)

for bgn_end_date in bgn_end_dates_list:
    url = 'https://earthquake.usgs.gov/fdsnws/event/1/count?minmagnitude=%d&starttime=%s&endtime=%s' % (args.minmagnitude, bgn_end_date[0], bgn_end_date[1])
    print(url)
    try:
        response = requests.get(url)
        count = response.content
        print(count.decode('utf-8'))
    except Exception as e:
        print('Bad response. Got an error code:', e)
    sleep(args.sleep_seconds)
