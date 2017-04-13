 
# CGRM-DMC

Collection of scripts to help manager CGRM-DMC database.

## Scripts

### mseed2sac.py

**Dependency**
* Python3.6
* Obspy1.0.2

**Fucntion**
- cut event data in SAC format from continuous waveform database in mseed format.
- write event information (origin time, location, magnitude) into SAC files
- write station information (location etc.) into SAC files.

### re-head.py
- re-write header of SAC files

## History

- 20170408: verify the trimed result and chunk events multiprocessing
- 20170409: solve exception caused by sampling rate change
- 20170411: With the help of seisman, SeisPider redesigned mseed2sac.py
