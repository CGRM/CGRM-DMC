# CGRM-DMC

Collection of scripts to help manage CGRM-DMC database.

## Dependency

1. Python >= 3.4
2. Obspy >= 1.0.2
3. SAC
4. GMT5

## List of files

### Data

- [catalog_released.csv](./catalog_released.csv): event catalog used in scripts
- [database.csv](./info/database.csv): event catalog used in SQL database
- [CENC.info](./info/CENC.info): path info of database
- [CN-border-La.dat](./info/CN-border-La.dat): China boundary used in [plot_event_map.pl](./plot_event_map.pl) and [plot_station_map.sh](./plot_station_map.sh)
- [mismatch.txt](./info/mismatch.txt): mismatch between database and response
- [station.revision.txt](./info/station.revision.txt): station information (**Confidential data!!!**)

### scripts

- `mseed2sac.py`: cut event data in SAC format from continuous waveform database
  in miniSEED format
- `catalog2database.py`: convert [catalog_released.csv](./catalog_released.csv) to [database.csv](./database.csv)
- `rewrite_sac.py`: read and rewrite SAC files to fix epicentral distance difference between obspy and SAC
- `path_info.pl`: extract path info of database
- `plot_event_map.pl`: distribution of events
- `plot_station_map.sh`: distribution of stations
- `check_header.pl`: check and modify header of Level1 database (memory issues)
- `check_header1.pl`: check and modify header of Level1 database (with `check_header2.pl`)
- `check_header2.pl`: check and modify header of Level1 database (with `check_header1.pl`)
- `check_mismatch.pl`: check mismatch between database and response.

## Data Release Notes

1.  Move data to `/data/Level1`
2.  Add event catalog to `catalog_realeased.csv`
3.  Run `catalog2database.py` to generate `database.csv`
4.  Run `plot_event_map.pl` to generate event map
5.  Update SQL database with the lastest `database.csv`
6.  Update event map on web
7.  Send email notification and add news on web

## History

- 2017-05-12: Add tool of trimming data and other drawing scripts
- 2018-01-31: Add script of checking and modifying header of Level1 database
- 2018-02-03: Add station information at `./info/station.revision.txt`
- 2018-03-31: Add path information at `./info/CENC.info`
- 2018-03-31: Update about scripts of checking and modifying header of Level1 database 
