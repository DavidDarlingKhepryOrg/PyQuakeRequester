# -*- coding: utf-8 -*-
"""
Created on Tue Sep 26 16:02:09 2017

@author: Khepry Quixote
"""
import argparse
import csv
import io
import os
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
                        default='1900-01-01',
                        help='starting date')
arg_parser.add_argument('--end_date',
                        type=str,
                        default='2019-12-31',
                        help='ending date')
arg_parser.add_argument('--iteration_type',
                        type=str,
                        default='years',
                        choices=('days', 'weeks', 'months', 'years'),
                        help='iteration type (e.g. days, weeks, months, years)')
arg_parser.add_argument('--how_many_iterations',
                        type=int,
                        default=0,
                        help='how many iterations')

arg_parser.add_argument('--method',
                        type=str,
                        default='query',
                        choices=('count', 'query'),
                        help='method to use')
arg_parser.add_argument('--format',
                        type=str,
                        default='csv',
                        choices=('csv', 'geojson', 'kml', 'quakeml', 'text', 'xml'),
                        help='format of output')
arg_parser.add_argument('--min_magnitude',
                        type=float,
                        help='minimum magnitude (0 or greater)')
arg_parser.add_argument('--max_magnitude',
                        type=float,
                        help='maximum magnitude (0 or greater)')
arg_parser.add_argument('--min_depth',
                        type=float,
                        default=-100,
                        help='minimum depth in kilometers (-100 to 1000)')
arg_parser.add_argument('--max_depth',
                        type=float,
                        default=1000,
                        help='maximum depth in kilometers (-100 to 1000)')
arg_parser.add_argument('--sleep_seconds',
                        type=int,
                        default=1,
                        help='sleep seconds')

arg_parser.add_argument('--tgt_path',
                        type=str,
                        default='F:/Fracking/Data/Quakes/',
                        help='target file path')
arg_parser.add_argument('--tgt_file_basename',
                        type=str,
                        default='ANSS_ComCat_Quakes_19000101_20191231',
                        help='target file base name')
arg_parser.add_argument('--tgt_file_append',
                        type=str,
                        default=False,
                        help='target file append')
arg_parser.add_argument('--tgt_file_extension',
                        type=str,
                        default='.csv',
                        help='target file extension')
arg_parser.add_argument('--tgt_col_delimiter',
                        type=str,
                        default=',',
                        help='target column delimiter')
arg_parser.add_argument('--tgt_col_quotechar',
                        type=str,
                        default='"',
                        help='target column quote character')

args = arg_parser.parse_args()

max_rows_per_query = 20000

prev_query_row_count = None


def get_next_smaller_iteration_type(interval):
    if interval == 'years':
        interval = 'months'
    elif interval == 'months':
        interval = 'weeks'
    elif interval == 'weeks':
        interval = 'days'
    return interval


def get_next_end_date(cur_date_parm,
                      iteration_type_parm):
    date_time = cur_date_parm
    next_end_date = None
    try:
        if iteration_type_parm == 'days':
            date_time += timedelta(days=1)
            next_end_date = date_time
        elif iteration_type_parm == 'weeks':
            date_time += timedelta(weeks=1)
            next_end_date = date_time
        elif iteration_type_parm == 'months':
            date_time += monthdelta(months=1)
            next_end_date = date_time
        elif iteration_type_parm == 'years':
            date_time += monthdelta(months=12)
            next_end_date = date_time
        else:
            date_time += timedelta(days=1)
            next_end_date = (date_time + timedelta(days=1))
    except Exception as e:
        sys.stderr.write('Exception: %s' % e)

    return next_end_date


if args.tgt_path.startswith('~'):
    args.tgt_path = os.path.expanduser(args.tgt_path)
tgt_file_name = os.path.join(args.tgt_path, args.tgt_file_basename + args.tgt_file_extension)
print('tgt_file_name: %s' % tgt_file_name)

# open the target file for write
with io.open(tgt_file_name, 'w', newline='') as tgt_file:
    first_pass = True

    base_url = 'https://earthquake.usgs.gov/fdsnws/event/1/'
    base_url += 'count?' if args.method == 'count' else 'query?'
    base_url += 'format=%s' % args.format
    base_url += '&mindepth=%d' % args.min_depth
    base_url += '&maxdepth=%d' % args.max_depth
    base_url += '&minmagnitude=%d' % args.min_magnitude if args.min_magnitude is not None else ''
    base_url += '&maxmagnitude=%d' % args.max_magnitude if args.max_magnitude is not None else ''

    bgn_date = datetime.strptime(args.bgn_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    cur_bgn_date = bgn_date
    iteration_type = args.iteration_type
    while cur_bgn_date <= end_date:
        end_date_parm = get_next_end_date(cur_bgn_date, iteration_type)
        end_date_parm -= timedelta(days=1)
        url = '%s&starttime=%s&endtime=%s' % (base_url, cur_bgn_date.strftime('%Y-%m-%d'), end_date_parm.strftime('%Y-%m-%d'))
        print(url)
        try:
            response = requests.get(url)
            if response.ok:
                content_decoded = response.content.decode('utf-8')
                print(content_decoded)
                if first_pass:
                    if content_decoded.strip() != '':
                        tgt_file.write(content_decoded.strip() + '\n')
                        tgt_file.flush()
                        first_pass = False
                else:
                    if content_decoded[content_decoded.find('\n') + 1:].strip() != '':
                        # TODO: Add logic to switch from 'months' to weeks when the row_count exceeds half of max_query_rows
                        prev_query_row_count = content_decoded.count('\n')
                        tgt_file.write(content_decoded[content_decoded.find('\n') + 1:].strip() + '\n')
                        tgt_file.flush()
                cur_bgn_date = end_date_parm + timedelta(days=1)
            else:
                if response.content.decode('utf-8').find('matching events exceeds search limit') > -1:
                    iteration_type = get_next_smaller_iteration_type(iteration_type)

        except Exception as e:
            print('Bad response. Got an error code:', e)

        sleep(args.sleep_seconds)

    tgt_file.close()

print('Processing finished!')
