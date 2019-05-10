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
                        default='months',
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


def get_next_dates_list(bgn_date_parm,
                        end_date_parm,
                        iteration_type,
                        how_many_iterations):
    iteration = 0
    bgn_end_dates_list = []
    date_time = bgn_date_parm
    while date_time <= end_date:
        iteration += 1
        # print('date_time: %s, end_date: %s, max_date: %s, how_many_iterations: %s, iteration: %s, iteration_type: %s' % (date_time, end_date, max_date, iteration, how_many_iterations, iteration_type))
        if how_many_iterations == 0 or iteration <= how_many_iterations:
            bgn_date_parm = date_time.strftime('%Y-%m-%d')
            try:
                if iteration_type == 'days':
                    date_time += timedelta(days=1)
                    max_date = (date_time + timedelta(days=1)).strftime('%Y-%m-%d')
                elif iteration_type == 'weeks':
                    date_time += timedelta(weeks=1)
                    max_date = date_time.strftime('%Y-%m-%d')
                elif iteration_type == 'months':
                    date_time += monthdelta(months=1)
                    max_date = date_time.strftime('%Y-%m-%d')
                elif iteration_type == 'years':
                    date_time += monthdelta(months=12)
                    max_date = date_time.strftime('%Y-%m-%d')
                else:
                    date_time += timedelta(days=1)
                    max_date = (date_time + timedelta(days=1)).strftime('%Y-%m-%d')
                print('bgn_date: %s, max_date: %s' % (bgn_date_parm, max_date))
                if datetime.strptime(max_date, '%Y-%m-%d') < end_date:
                    bgn_end_dates_list.append((bgn_date_parm, max_date))
                else:
                    bgn_end_dates_list.append((bgn_date_parm, max_date))
                    break
            except Exception as e:
                sys.stderr.write('Exception: %s' % e)
        else:
            break;
    return bgn_end_dates_list


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
    bgn_end_dates = get_next_dates_list(bgn_date,
                                        end_date,
                                        args.iteration_type,
                                        args.how_many_iterations)

    # pprint(bgn_end_dates)

    for bgn_end_date in bgn_end_dates:
        url = '%s&starttime=%s&endtime=%s' % (base_url, bgn_end_date[0], bgn_end_date[1])
        print(url)
        try:
            response = requests.get(url)
            content_decoded = response.content.decode('utf-8')
            print(content_decoded)
            if first_pass:
                if content_decoded.strip() != '':
                    tgt_file.write(content_decoded.strip() + '\n')
                    tgt_file.flush()
                    first_pass = False
            else:
                if content_decoded[content_decoded.find('\n') + 1:].strip() != '':
                    tgt_file.write(content_decoded[content_decoded.find('\n') + 1:].strip() + '\n')
                    tgt_file.flush()
        except Exception as e:
            print('Bad response. Got an error code:', e)

        sleep(args.sleep_seconds)

    tgt_file.close()

print('Processing finished!')
