# CGRM-DMC

Collection of scripts to help manage CGRM-DMC database.

## Dependency

1. Python >= 3.4
2. Obspy >= 1.0.2
3. SAC
4. GMT5

## List of files

### Data

- [catalog_released.csv](): event catalog used in scripts
- [database.csv](): event catalog used in SQL database
- [station.info](): station information (**Confidential data!!!**)
- [CN-border-La.dat](): China boundary used in [plot_event_map.pl]() and [plot_station_map.sh]()

### scripts

- `mseed2sac.py`: cut event data in SAC format from continuous waveform database
  in miniSEED format
- `catalog2database.py`: convert [catalog_released.csv]() to [database.csv]()
- `re-head.py`: read and rewrite SAC files to fix epicentral distance difference between obspy and SAC
- `plot_event_map.pl`: distribution of events
- `plot_station_map.sh`: distribution of stations

## History

- 20170408: verify the trimed result and chunk events multiprocessing
- 20170409: solve exception caused by sampling rate change
- 20170411: With the help of seisman, SeisPider redesigned mseed2sac.py
