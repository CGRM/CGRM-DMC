# CGRM-DMC

Collection of scripts to help manage CGRM-DMC database.

## Dependency

1. Python >= 3.4
2. Obspy >= 1.0.2
3. SAC
4. GMT5

## List of files

### Data

- [catalog_released.csv](catalog_released.csv): event catalog used in scripts
- [database.csv](database.csv): event catalog used in SQL database
- [station.info](): station information (**Confidential data!!!**)
- [CN-border-La.dat](CN-border-LA.dat): China boundary used in [plot_event_map.pl](plot_event_map.pl) and [plot_station_map.sh](plot_station_map.sh)

### scripts

- `mseed2sac.py`: cut event data in SAC format from continuous waveform database
  in miniSEED format
- `catalog2database.py`: convert [catalog_released.csv]() to [database.csv]()
- `rewrite_sac.py`: read and rewrite SAC files to fix epicentral distance difference between obspy and SAC
- `plot_event_map.pl`: distribution of events
- `plot_station_map.sh`: distribution of stations

## Data Release Notes

1.  Move data to `/data/Level1`
2.  Add event catalog to `catalog_realeased.csv`
3.  Run `catalog2database.py` to generate `database.csv`
4.  Run `plot_event_map.pl` to generate event map
5.  Update SQL database with the lastest `database.csv`
6.  Update event map on web
7.  Send email notification and add news on web

## History

- 20170512: Add tool of trimming data and other drawing scripts
