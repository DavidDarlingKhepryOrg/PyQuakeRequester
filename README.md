# PyGeoCoderRev

Python reverse geo-coder for NCEDC-formatted comma-separated-value earthquake files.

## Synopsis

This project, as currently implemented, is intended to reverse-geocode NCEDC-formatted earthquake comma-separated-value (CSV) files.  Reverse-geocoding is the process of obtaining administrative units (e.g. country, state, county/province, city/village) from latitude and longitude (lat-long) coordinates.  With a modicum of effort, this program could be modified so as to reverse-geocode most any file or database table.

## Source(s) of Earthquake Data in CSV format

- [ANSS Composite Catalog Search](http://www.ncedc.org/anss/catalog-search.html)
  - Choose `Catalog in CSV format`
  - Enter `Start date,time` value with a comma separating the date (yyyy/MM/dd) and time (HH:mm:ss) value
  - Enter `End date,time` value with a comma separating the date (yyyy/MM/dd) and time (HH:mm:ss) value, leaving this blank to default to today's date, time value.
  - Enter `Minimum magnitude` value, recommended minimum value, especially for fracking research, is 2.0 or less
  - Leave `Maximum magnitude` blank so that all earthquakes above the `Minimum magnitude` will be included
  - Choose `Send output to an anonymous FTP file on the NCEDC` within the "Select output mechanism" section
  - Enter `10000000` in the `Line limit on output` box (i.e. 10,000,000 rows max)
  - Click on the `Submit request` button
  - On the "NCEDC_Search_Results" web page that appears after the `Submit request` button is pressed, wait until a `Url` link appears, right-click on it and click on the `Save link as...` sub-menu item, and save the file to a location of your choosing.
  - The saved file mentioned in the bullet above is the file to which you'll point the `GeoCoderRev.py` script when you invoke it to reverse-geocode the rows therein. 

## Invoking the `GeoCoderRev.py` program

- The simplest invocation of the program is as follows:
  - Navigate the folder holding the `PyGeoCoderRev` project.
  - Open a command terminal from within that folder
    - Windows: `Shift-Right-click` within the project's folder, choose `Open command window here`
    - Linux (Ubuntu with `nautilus-open-terminal` installed): `Right-click` within the project's folder, choose `Open terminal`
    - Linux (Ubuntu without `nautilus-open-terminal` installed): `Ctrl-Alt-T`, then navigate to the project's folder
  - Within the command terminal, enter the following command:
    - `python GeoCoderRev.py --src-file-path=/path/to/the/downloaded/NCEDC/earthquake/CSV/file --out-file-path=/path/to/the/resulting/reverse-geocoded/NCEDC/earthquake/CSV/file`
    
## Command-line arguments
    
The `GeoCoderRev.py` program has more command-line options than just the two shown in the example above, a quick explanation of them follows:
  
- `--src-file-path`: The path to the raw NCEDC-formatted earthquake source file in CSV format.
- `--src-delimiter`: The character that separates each value within the file. The default is a comma `,`.
- `--src-quotechar`: The character that surrounds each value within the file, should it contain a delimiter. The default is a double-quote `"`.
- `--src-quotemode`: The quoting mode, which defaults to `QUOTE_MINIMAL`.  Valid choices are `QUOTE_MINIMAL`, `QUOTE_NONE`, `QUOTE_ALL`, `QUOTE_NONNUMERIC`.
  
- `--out-file-path`: The path to the reverse-geocoded NCEDC-formatted earthquake output file in CSV format.
- `--out-delimiter`: The character that separates each value within the file. The default is a comma `,`.
- `--out-quotechar`: The character that surrounds each value within the file, should it contain a delimiter. The default is a double-quote `"`.
- `--out-quotemode`: The quoting mode, which defaults to `QUOTE_MINIMAL`.  Valid choices are `QUOTE_MINIMAL`, `QUOTE_NONE`, `QUOTE_ALL`, `QUOTE_NONNUMERIC`.
  
- `--max-rows`: Mostly intended to be used for testing purposes, this integer argument defaults to `0`, which means unlimited rows will be processed.  Any positive integer above zero will result in just that many rows being processed, for example `10` means only ten rows would be processed.
- `--flush-rows`: This integer value controls how often a progress message is output to the console as well as when any buffered rows are "flushed" to the output file.
- `-h` or `--help`: Specifying this argument will output command-line usage information to the console, which describes the command-line arguments for this program, and then terminates the program without any further processing.
  
## License
  
Copyright � 2016 Khepry Quixote
 
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
  