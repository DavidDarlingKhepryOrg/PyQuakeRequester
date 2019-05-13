# -*- coding: utf-8 -*-

# ========================================================================
#
# Copyright � 2016 Khepry Quixote
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ========================================================================

import argparse
import csv
import datetime
import io
import json
import os
import requests
import sys

from pprint import pprint
from time import time

import reverse_geocoder as rg

pgm_name = 'GeoCoderRev2.py'
pgm_version = '1.0'

quotemode_choices = ['QUOTE_MINIMAL', 'QUOTE_NONE', 'QUOTE_ALL', 'QUOTE_NONNUMERIC']


def delimiter_xlator(delimiter_str):
    delimiter_val = ','

    if delimiter_str == '\\t' or delimiter_str == '\t':
        delimiter_val = '\t'

    return delimiter_val


def quotemode_xlator(quote_mode_str):
    quote_mode_val = csv.QUOTE_MINIMAL

    if quote_mode_str.upper() == 'QUOTE_MINIMAL':
        quote_mode_val = csv.QUOTE_MINIMAL
    elif quote_mode_str.upper() == 'QUOTE_ALL':
        quote_mode_val = csv.QUOTE_ALL
    elif quote_mode_str.upper() == 'QUOTE_NONE':
        quote_mode_val = csv.QUOTE_NONE
    elif quote_mode_str.upper() == 'QUOTE_NONNUMERIC':
        quote_mode_val = csv.QUOTE_NONNUMERIC

    return quote_mode_val


def get_datetime_value(value, pattern, null_value):
    value = value.strip()
    try:
        value = datetime.datetime.strptime(value, pattern)
    except ValueError:
        value = null_value
    return value


def get_float_value(value, null_value):
    value = value.strip()
    if value != '':
        try:
            rtn_value = float(value)
        except:
            rtn_value = null_value
    else:
        rtn_value = null_value
    return rtn_value


def get_int_value(value, null_value):
    value = value.strip()
    if value != '':
        try:
            rtn_value = int(float(value))
        except:
            rtn_value = null_value
    else:
        rtn_value = null_value
    return rtn_value


def get_magnitude_values(value, null_value):
    mag = 0
    magInt = 0
    mags = [0] * 10

    value = value.strip()

    if value != '':
        try:
            mag = float(value)
            if mag < 0:
                mag = 0.0
            magInt = int(mag)
            mags[magInt] = 1
        except:
            pass

    return mag, magInt, mags


arg_parser = argparse.ArgumentParser(prog='%s' % pgm_name, description='Reverse geo-code an ANSS ComCat-formatted earthquake CSV file.')

arg_parser.add_argument('--src-file-path', required=False, help='source file path', default='F:/Fracking/Data/Quakes/ANSS_ComCat_Quakes_19000101_20191231.csv')
arg_parser.add_argument('--src-delimiter', default=',', help='source file delimiter character')
arg_parser.add_argument('--src-quotechar', default='"', help='source file quote character')
arg_parser.add_argument('--src-quotemode', dest='src_quotemode_str', default='QUOTE_MINIMAL', choices=quotemode_choices,
                        help='source file quoting mode (default: %s)' % 'QUOTE_MINIMAL')
arg_parser.add_argument('--src-date-ymd-separator', default='-', help='source date year, month, day separator (default: /)')

arg_parser.add_argument('--dtg-parse-pattern', default='%Y-%m-%d %H:%M:%S', help='Date-Time-Group Pattern (default: %Y-%m-%d %H:%M:%S)')

arg_parser.add_argument('--out-file-path', default=None, help='output file path (default: None, same path as source file)')
arg_parser.add_argument('--out-delimiter', default=',', help='output file delimiter character')
arg_parser.add_argument('--out-quotechar', default='"', help='output file quote character')
arg_parser.add_argument('--out-quotemode', dest='out_quotemode_str', default='QUOTE_MINIMAL', choices=quotemode_choices,
                        help='output file quoting mode (default: %s)' % 'QUOTE_MINIMAL')
arg_parser.add_argument('--out-header-row', default='Y', choices=['Y', 'N'], help='output a header row to file (default: Y)')
arg_parser.add_argument('--out-db-null-value', default=None, help='output null value (default: NULL)')
arg_parser.add_argument('--out-es-null-value', default=None, help='output null value (default: NULL)')
arg_parser.add_argument('--out-elastic-search', default='N', choices=['Y', 'N'], help='output to ElasticSearch index (default: N)')

arg_parser.add_argument('--es-host-url', default='localhost', help='ElasticSearch host URL')
arg_parser.add_argument('--es-port-number', default='9200', help='ElasticSearch port number')
arg_parser.add_argument('--es-index-name', default='quakes', help='ElasticSearch index name')

arg_parser.add_argument('--out-file-name-folder', default=None, help='output file name folder (default: None')
arg_parser.add_argument('--out-file-name-prefix', default='ANSS_ComCat_earthquakes', help='output file name prefix (default: ANSS_ComCat_earthquakes')
arg_parser.add_argument('--out-file-name-suffix', default='_reverse_geocoded', help='output file name suffix (default: _reverse_geocoded)')
arg_parser.add_argument('--out-file-name-extension', default='.csv', help='output file name extension (default: .csv)')
arg_parser.add_argument('--out-date-ymd-separator', default='-', help='output date year, month, day separator (default: -)')

arg_parser.add_argument('--max-rows', type=int, default=0, help='maximum rows to process, 0 means unlimited')
arg_parser.add_argument('--flush-rows', type=int, default=1000, help='flush rows interval')

arg_parser.add_argument('--version', action='version', version='version=%s %s' % (pgm_name, pgm_version))

try:
    args = arg_parser.parse_args()
except Exception as e:
    print(e)

args.out_header_row = args.out_header_row.upper();

if args.out_file_path is None:
    if args.out_file_name_folder is None:
        args.out_file_name_folder = os.path.dirname(args.src_file_path)

if args.max_rows > 0:
    args.out_file_path = os.path.join(args.out_file_name_folder,
                                      args.out_file_name_prefix + args.out_file_name_suffix + '_' + str(args.max_rows) + args.out_file_name_extension)
else:
    args.out_file_path = os.path.join(args.out_file_name_folder, args.out_file_name_prefix + args.out_file_name_suffix + args.out_file_name_extension)

args.src_quotemode_enm = quotemode_xlator(args.src_quotemode_str)
args.out_quotemode_enm = quotemode_xlator(args.out_quotemode_str)

args.src_delimiter = delimiter_xlator(args.src_delimiter)
args.out_delimiter = delimiter_xlator(args.out_delimiter)

args.max_rows = abs(args.max_rows)
args.flush_rows = abs(args.flush_rows)

if args.src_file_path.startswith('~'):
    args.src_file_path = os.path.expanduser(args.src_file_path)
args.src_file_path = os.path.abspath(args.src_file_path)

if args.out_file_path.startswith('~'):
    args.out_file_path = os.path.expanduser(args.out_file_path)
args.out_file_path = os.path.abspath(args.out_file_path)

print('Reverse-geocoding source ANSS ComCat earthquakes file: "%s"' % args.src_file_path)
print('Outputting to the target ANSS ComCat earthquakes file: "%s"' % args.out_file_path)
print('')

print('Command line args:')
pprint(vars(args))
print('')

es_actions = []

if args.out_elastic_search == 'Y':
    from elasticsearch import Elasticsearch, helpers

# beginning time hack
bgn_time = time()

# initialize
# row counters
row_count = 0
out_count = 0

# if the source file exists
if os.path.exists(args.src_file_path):

    if args.out_elastic_search == 'Y':
        # make sure ES is up and running
        res = requests.get('http://' + args.es_host_url + ':' + args.es_port_number)
        pprint(res.content)
        # connect to the ElasticSearch cluster
        es = Elasticsearch([{'host': args.es_host_url, 'port': args.es_port_number}])
        # delete the quakes index
        es.indices.delete(index=args.es_index_name, ignore=[400, 404])

    # open the target file for writing
    with io.open(args.out_file_path, 'w', newline='') as out_file:

        # open the source file for reading
        with io.open(args.src_file_path, 'r', newline='') as src_file:

            # open a CSV file dictionary reader object
            csv_reader = csv.DictReader(src_file, delimiter=args.src_delimiter, quotechar=args.src_quotechar, quoting=args.src_quotemode_enm)

            # obtain the field names from
            # the first line of the source file
            fieldnames = csv_reader.fieldnames

            # append various deriviative
            # fields to field names list

            if 'time' in fieldnames:
                fieldnames[fieldnames.index('time')] = 'Event_DTG'
            if 'id' in fieldnames:
                fieldnames[fieldnames.index('id')] = 'Event_ID'
            if 'updated' in fieldnames:
                fieldnames[fieldnames.index('updated')] = 'Updated_DTG'
            if 'Event_Year' not in fieldnames:
                fieldnames.append('Event_Year')
            if 'Event_Month' not in fieldnames:
                fieldnames.append('Event_Month')
            if 'Event_Day' not in fieldnames:
                fieldnames.append('Event_Day')
            if 'Event_Hour' not in fieldnames:
                fieldnames.append('Event_Hour')
            if 'Event_Min' not in fieldnames:
                fieldnames.append('Event_Min')
            if 'Event_Sec' not in fieldnames:
                fieldnames.append('Event_Sec')
            if 'cc' not in fieldnames:
                fieldnames.append('cc')
            if 'admin1' not in fieldnames:
                fieldnames.append('admin1')
            if 'admin2' not in fieldnames:
                fieldnames.append('admin2')
            if 'name' not in fieldnames:
                fieldnames.append('name')
            if 'magInt' not in fieldnames:
                fieldnames.append('magInt')
            if 'mag0' not in fieldnames:
                fieldnames.append('mag0')
            if 'mag1' not in fieldnames:
                fieldnames.append('mag1')
            if 'mag2' not in fieldnames:
                fieldnames.append('mag2')
            if 'mag3' not in fieldnames:
                fieldnames.append('mag3')
            if 'mag4' not in fieldnames:
                fieldnames.append('mag4')
            if 'mag5' not in fieldnames:
                fieldnames.append('mag5')
            if 'mag6' not in fieldnames:
                fieldnames.append('mag6')
            if 'mag7' not in fieldnames:
                fieldnames.append('mag7')
            if 'mag8' not in fieldnames:
                fieldnames.append('mag8')
            if 'mag9' not in fieldnames:
                fieldnames.append('mag9')

            # instantiate the CSV dictionary writer object with the modified field names list
            csv_writer = csv.DictWriter(out_file, delimiter=args.out_delimiter, quotechar=args.out_quotechar, quoting=args.out_quotemode_enm,
                                        fieldnames=fieldnames)

            # output the header row
            if args.out_header_row == 'Y':
                csv_writer.writeheader()

            # beginning time hack
            bgn_time = time()

            # reader row-by-row
            for row in csv_reader:

                row_count += 1

                # tweak column to null
                # if it's not a valid date-time stamp
                if row['Event_DTG'] is not None and row['Event_DTG'].endswith('.000'):
                    row['Event_DTG'] = row['Event_DTG'][:-5].replace(args.src_date_ymd_separator, args.out_date_ymd_separator).replace('T', ' ')
                if row['Updated_DTG'] is not None and row['Updated_DTG'].endswith('.000'):
                    row['Updated_DTG'] = row['Updated_DTG'][:-5].replace(args.src_date_ymd_separator, args.out_date_ymd_separator).replace('T', ' ')
                # print('Event_DTG: %s' % row['Event_DTG'])
                event_dtg = get_datetime_value(row['Event_DTG'], args.dtg_parse_pattern, args.out_db_null_value)
                # only output rows with valid DTGs
                if event_dtg != args.out_db_null_value:
                    # remove last 3 characters (.00)
                    # so that the timestamp will be more
                    # suitable for importation into databases
                    row['Event_Year'] = event_dtg.year
                    row['Event_Month'] = event_dtg.month
                    row['Event_Day'] = event_dtg.day
                    row['Event_Hour'] = event_dtg.hour
                    row['Event_Min'] = event_dtg.minute
                    row['Event_Sec'] = event_dtg.second

                    # tweak columns to NULL
                    # if they're not numeric
                    row['depth'] = get_float_value(row['depth'], args.out_db_null_value)
                    row['nst'] = get_int_value(row['nst'], args.out_db_null_value)
                    row['gap'] = get_float_value(row['gap'], args.out_db_null_value)
                    row['dmin'] = get_float_value(row['dmin'], args.out_db_null_value)

                    row['mag'], row['magInt'], mags = get_magnitude_values(row['mag'], args.out_db_null_value)
                    row['mag0'] = mags[0]
                    row['mag1'] = mags[1]
                    row['mag2'] = mags[2]
                    row['mag3'] = mags[3]
                    row['mag4'] = mags[4]
                    row['mag5'] = mags[5]
                    row['mag6'] = mags[6]
                    row['mag7'] = mags[7]
                    row['mag8'] = mags[8]
                    row['mag9'] = mags[9]

                    # remove DateTime column
                    row.pop('DateTime', None)

                    # convert string lat/lon
                    # to floating-point values
                    latitude = float(row['latitude'])
                    longitude = float(row['longitude'])

                    row['latitude'] = get_float_value(row['latitude'], args.out_db_null_value)
                    row['longitude'] = get_float_value(row['longitude'], args.out_db_null_value)

                    # instantiate coordinates tuple
                    coordinates = (latitude, longitude)

                    # search for the coordinates
                    # returning the cc, admin1, admin2, and name values
                    # using a mode 1 (single-threaded) search
                    results = rg.search(coordinates, mode=1)  # default mode = 2

                    # if results obtained
                    if results is not None:
                        # result-by-result
                        for result in results:
                            # map result values
                            # to the row values
                            row['cc'] = result['cc']
                            row['admin1'] = result['admin1']
                            row['admin2'] = result['admin2']
                            row['name'] = result['name']
                            # output a row
                            if args.out_header_row == 'Y' or row_count > 1:
                                csv_writer.writerow(row)
                                out_count += 1
                                if args.out_elastic_search == 'Y':
                                    # es.index(index=args.es_index_name, doc_type='quake', id=out_count, body=body)
                                    action = {'_index': args.es_index_name, '_type': 'quake', '_id': out_count, '_source': json.dumps(row)}
                                    es_actions.append(action)
                    else:
                        # map empty values
                        # to the row values
                        row['cc'] = ''
                        row['admin1'] = ''
                        row['admin2'] = ''
                        row['name'] = ''
                        # output a row
                        if args.out_header_row == 'Y' or row_count > 1:
                            csv_writer.writerow(row)
                            out_count += 1
                            if args.out_elastic_search == 'Y':
                                # es.index(index=args.es_index_name, doc_type='quake', id=out_count, body=body)
                                action = {'_index': args.es_index_name, '_type': 'quake', '_id': out_count, '_source': json.dumps(row)}
                                es_actions.append(**row)

                # if row count equals or exceeds max rows
                if args.max_rows > 0 and row_count >= args.max_rows:
                    # break out of reading loop
                    break

                # if row count is modulus
                # of the flush count value
                if row_count % args.flush_rows == 0:

                    # flush accumulated
                    # rows to target file
                    out_file.flush()

                    if args.out_elastic_search == 'Y' and len(es_actions) > 0:
                        helpers.bulk(es, es_actions)
                        es_actions.clear()

                    # ending time hack
                    end_time = time()
                    # compute records/second
                    seconds = end_time - bgn_time
                    if seconds > 0:
                        rcds_per_second = row_count / seconds
                    else:
                        rcds_per_second = 0
                    # output progress message
                    message = "Processed: {:,} rows in {:,.0f} seconds @ {:,.0f} records/second".format(row_count, seconds, rcds_per_second)
                    print(message)

else:

    print('ANSS ComCat formatted Earthquake file not found: "%s"' % args.src_file_path)

if args.out_elastic_search == 'Y' and len(es_actions) > 0:
    helpers.bulk(es, es_actions)
    es_actions.clear()

# ending time hack
end_time = time()
# compute records/second
seconds = end_time - bgn_time
if seconds > 0:
    rcds_per_second = row_count / seconds
else:
    rcds_per_second = row_count
# output end-of-processing messages
message = "Processed: {:,} rows in {:,.0f} seconds @ {:,.0f} records/second".format(row_count, seconds, rcds_per_second)
print(message)
print('Output file path: "%s"' % args.out_file_path)
print("Processing finished, {:,} rows output!".format(out_count))


