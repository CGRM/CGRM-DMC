# Purpose 
Develop several python tools to measure seismic data

# components

## Trim-mseed2SAC 
It can obtain event data(SAC) from continues waveform(mseed).It can
also write the event infos(time,location,magnitude) and station infos(location etc)
into SAC files.
### History
20170408: verify the trimed result and chunk events multiprocessing
20170409: solve exception caused by sampling rate change
20170411: With the help of seisman, SeisPider redesigned mseed2sac.py  
