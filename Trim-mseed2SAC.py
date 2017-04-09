#!/usr/bin/env python
# -*- coding:utf8 -*-
"""
Scripts used to trim earthquake event waveform from continues waveform

Files of miniSEED should be organized as <net>.<sta>.<loc>.<cha>.<starttime>.mseed
 eg. JX.WAA.00.BHZ.20160501000004.mseed

All these files collected in one day folder named as YYYYMMDD
 eg. 20160501

@Data_dir: string     ;Directory of Data
@Catalog_dirname: string  ;Directory+name of events Catalog_dir
"""
from obspy import UTCDateTime
import datetime as dt
import glob
from obspy import read
from obspy import Stream
import os
from obspy.io.sac import SACTrace
import multiprocessing as mp
import itertools as it
# load events catalog


def load_catalog(data_dir="./Data", catalog_dirname="./events.csv"):
    """
    Function used to load events catalog file

    Input variables:
    @Data_dir: string     ;Directory of Data
    @Catalog_dirname: string  ;Directory+name of events Catalog_dir

    Output variables:
    @Catalogs: list    ;list of dictionary which contain starttime, latitude,
                        longitude, depth, magnitude
    """

    with open(catalog_dirname) as f:
        lines = f.readlines()

    catalogs = []
    for line in lines:
        starttime, latitude, longitude, depth, magnitude = line.split()[0:5]
        catalog = {"starttime": starttime, "latitude": latitude, "longitude": longitude,
                   "depth": depth, "magnitude": magnitude}
        catalogs.append(catalog)
    return catalogs

def load_stationinfo(stationinfo_dirname):
    """
    function used to load the station info.

    @file_dirname: string      ;string contain the location of station info file
    @stationinfo_list: list     ;list of station info
    """
    if not os.path.isfile(stationinfo_dirname):
        print "file not exist!\n"
        stationinfo_dirname = raw_input("Please input file location:\n")

    # init file object
    with open(stationinfo_dirname) as f:
        lines = f.readlines()

    stationinfo = {}
    for line in lines:
        net, sta = (line.split()[0]).split(".")

        stla, stlo, stel, stdp = line.split()[-4:]
        key = ".".join([net, sta])
        value = {"stla": stla, "stlo": stlo, "stel": stel, "stdp": stdp}
        stationinfo[key] = value
    return stationinfo


# Obtain data folder name
def starttime_endtime_folder(starttime_in_utc, event_last_time=6000, verbose=True):
    """
    function used to obtain the folder name

    Input variables:
    @starttime_in_UTC: UTCDateTime     ;Time of UTC earthquake starttime

    Output variables:
    @folder_name: list        ;The folder name
    """
    # change string starttime_in_UTC to UTCDateTime
    utcevent = UTCDateTime(starttime_in_utc)
    # obtain end time of UTC
    end_utcevent = utcevent + event_last_time

    # Change this UTC time to Beijing Time(BJT_Event)
    bjt_event = utcevent + dt.timedelta(hours=8)
    # obtain end time of Beijing time zone
    end_bjt_event = bjt_event + event_last_time

    # transfer UTCDatetime to string
    bjt_event_str = bjt_event.strftime("%Y%m%d")
    end_bjt_event_str = end_bjt_event.strftime("%Y%m%d")

    folder_name = []
    if bjt_event_str == end_bjt_event_str:
        if verbose:
            msg = "Event lasted in one day--{}".format(bjt_event_str)
            print msg
        folder_name.append(bjt_event_str)
    else:
        if verbose:
            msg = "Event lasted in two days--{}-{}".format(bjt_event_str,
                                                           end_bjt_event_str)
            print msg
        folder_name.append(bjt_event_str)
        folder_name.append(end_bjt_event_str)
    return utcevent, end_utcevent, folder_name


def obtain_stations_list(folder_dirname, suffix="mseed"):
    """
    obtain stations data lists

    @folder_dirname: string    ;dirname to obtain stations data list
    @stations: list            ;list of dictionary containing stations info
    """
    dirname = os.path.join(folder_dirname, "*.{}".format(suffix))
    data_list = glob.glob(dirname)
    if not data_list:
        print "No Data in {}".format(folder_dirname)
    stations = []
    for data in data_list:
        net, sta, loc, cha, btime = os.path.basename(data).split(".")[0:5]
        station = {"net": net, "sta": sta,
                   "loc": loc, "cha": cha, "btime": btime}
        stations.append(station)
    return stations

# scan stations in particular folder


def scan_stations(data_dir, folder_name):
    """
    function used to scan stations

    Input variables:
    @Data_dir: string       ;The directory of Data
    @folder_name: list      ;The folder name list [0]-starttime folder    \
                                                  [1]-endtime folder

    Output variables:
    @startfolder_stations_list   ;list of stations dictionary in begintime folder
    @endfolder_stations_list     ;list of stations dictionary in endtime folder
    """
    if len(folder_name) == 1:
        strtfolder_dirname = os.path.join(data_dir, folder_name[0])
        endfolder_dirname = strtfolder_dirname
        # test if this directory exist
        if not os.path.exists(strtfolder_dirname):
            print "Dir {} not exist".format(strtfolder_dirname)
            strtfolder_list = []
            endfolder_list = []
    else:
        # obtain the data dir+name and check weather this folder is empty
        strtfolder_dirname = os.join(data_dir, folder_name[0])
        # test if startfolder_Stations_dirname directory exist
        if not os.path.exists(strtfolder_dirname):
            print "Dir {} not exist".format(strtfolder_dirname)
            strtfolder_list = []
        endfolder_dirname = os.join(data_dir, folder_name[1])
        # test if endfolder_Stations_dirname directory exist
        if not os.path.exists(endfolder_dirname):
            print "Dir {} not exist".format(endfolder_dirname)
            endfolder_list = []

    strtfolder_list = obtain_stations_list(strtfolder_dirname)
    endfolder_list = obtain_stations_list(endfolder_dirname)
    return strtfolder_list, endfolder_list

# trim data and return waveform


def trim_waveform(data_dir, event, stationinfo, utcevent, end_utcevent,
                  folder_name, strtfolder_list, endfolder_list, output_dir,
                  verbose=False):
    """
    trim waveform for particular event

    @event: dict            ; event information
    @UTCEvent: UTCDateTime   ;UTC time when the event happened
    @stationinfo_dirname: string   ; string of station info file location
    @End_UTCEvent: UTCDateTime ;UTC time when the event end
    @startfolder_stations_list ;list of stations dictionary in begintime folder
    @endfolder_stations_list     ;list of stations dictionary in endtime folder
    @waveform: Stream            ;Stream of event waveform
    @output_dir:string          ;dirname of event data
    """
    # return none if stations_list is empty
    if not strtfolder_list:
        return
    if not endfolder_list:
        return

    # obtain event waveform
    if strtfolder_list == endfolder_list:
        if verbose:
            print "Event didn't cross days"
        trim_oneday(data_dir, event, stationinfo, utcevent, end_utcevent,
                    folder_name, strtfolder_list, output_dir, verbose=True)
    else:
        if verbose:
            print "Event crossed days"
        trim_crossdays(data_dir, event, stationinfo, utcevent, end_utcevent,
                       folder_name, strtfolder_list, endfolder_list, output_dir,
                       verbose=True)
    return


def trim_crossdays(data_dir, event, stationinfo, utcevent, end_utcevent,
                   folder_name, strtfolder_list, endfolder_list, output_dir,
                   verbose=True):
    """
    trim waveform if event don't cross days

    @event: dict            ; event information
    @UTCEvent: UTCDateTime       ;UTC time when the event happened
    @End_UTCEvent: UTCDateTime   ;UTC time when the event end
    @startfolder_stations_list:list ;list of stations dictionary in begintime folder
    @waveform:Stream  ;trimed waveform
    @stationinfo_list: list     ;list of station info
    @output_dir:string          ;dirname of event data
    """
    # initialization of waveform_start and waveform_end
    waveform_start = Stream()
    waveform_end = Stream()
    for staA in strtfolder_list:

        # check if this work has been done?
        patname = ".".join(
            ["*", staA["net"], staA["sta"], "*", staA["cha"], "SAC"])
        full_path = os.path.join(output_dir, patname)
        if os.path.exists(full_path):
            print "{} exist: skiping!".format(patname)
            return

        # Obtain location of file to began to trim
        flnm_strt = ".".join([staA["net"], staA["sta"], staA["loc"],
                              staA["cha"], staA["btime"], "mseed"])
        dirnm_strt = os.path.join(data_dir, folder_name[0], flnm_strt)

        # check file existence
        if not os.path.isfile(dirnm_strt):
            if verbose:
                print "file--{} not exist".format(flnm_strt)
            continue
        waveform_start = read(dirnm_strt, starttime=utcevent)

        Loc_end = os.path.join(data_dir, folder_name[1], patname)
        sta_fl = glob.glob(Loc_end)
        if not sta_fl:
            print "No Data in {}".format(folder_name[1])
            continue
        dirnm_end = sta_fl[0]
        waveform_end = read(dirnm_end, endtime=end_utcevent)

        # Merge seperated data
        waveform = Stream()
        waveform = waveform_start + waveform_end
        try:
            waveform.merge(fill_value=0)
        except Exception:
            msg = "merge error of {} {}".format(dirnm_strt, flnm_strt)
            with open(os.path.join(output_dir, "Log.list"), "a") as f:
                f.write(msg)
            continue

        # todo: write data as SAC format
        if not waveform:
            continue
        writeSAC(waveform, event, folder_name, utcevent, staA, stationinfo,
                 output_dir)


def trim_oneday(data_dir, event, stationinfo, utcevent, end_utcevent,
                folder_name, strtfolder_list, output_dir, verbose=True):
    """
    trim waveform if event don't cross days

    @event: dict            ; event information
    @UTCEvent: UTCDateTime       ;UTC time when the event happened
    @End_UTCEvent: UTCDateTime   ;UTC time when the event end
    @strtfolder_list:list ;list of stations dictionary in begintime folder
    @waveform:Stream  ;trimed waveform
    @output_dir:string          ;dirname of event data
    @stationinfo_list: list     ;list of station info
    """
    for sta in strtfolder_list:
        # check if this work has been done?
        patname = ".".join(
            ["*", sta["net"], sta["sta"], "*", sta["cha"], "SAC"])
        full_path = os.path.join(output_dir, patname)
        if os.path.exists(full_path):
            print "{} exist: skiping!".format(patname)
            return

        flnm = ".".join([sta["net"], sta["sta"], sta["loc"], sta["cha"],
                         sta["btime"], "mseed"])
        dirnm = os.path.join(data_dir, folder_name[0], flnm)
        if not os.path.isfile(dirnm):
            if verbose:
                print "Warning: {} not exist".format(flnm)
            continue
        waveform = read(dirnm, starttime=utcevent, endtime=end_utcevent)
        if not waveform:
            continue
        writeSAC(waveform, event, folder_name, utcevent, sta, stationinfo,
                 output_dir)


def writeSAC(waveform, event, folder_name, utcevent, sta, stationinfo,
             output_dir):
    """
    function used to write data with SAC format

    @event: dict                ; event information
    @waveform: Stream           ;Stream of event waveform
    @sta: dict              ;station dictionary
    @stationinfo_list: list     ;list of station info
    @output_dir:string          ;dirname of event data
    """
    Trace = waveform[0]
    key = ".".join([Trace.stats.network, Trace.stats.station])

    # write missed station info into miss_station.list
    if key not in stationinfo:
        print "Warning: No Station info for {}".format(key)
        with open(os.path.join(output_dir, "Log.list"), "a") as f:
            f.write(key + "no station info")
        return
    # transfer obspy trace to sac trace
    sac_trace_init = SACTrace()
    sac_trace = sac_trace_init.from_obspy_trace(trace=Trace)

    # change some headers about station
    sac_trace.stla = float(stationinfo[key]["stla"])
    sac_trace.stlo = float(stationinfo[key]["stlo"])
    sac_trace.stel = float(stationinfo[key]["stel"])
    sac_trace.stdp = float(stationinfo[key]["stdp"])

    if Trace.stats.channel[-1] == "E":
        sac_trace.cmpaz = 90
        sac_trace.cmpinc = 90
    if Trace.stats.channel[-1] == "N":
        sac_trace.cmpaz = 0
        sac_trace.cmpinc = 90
    if Trace.stats.channel[-1] == "Z":
        sac_trace.cmpaz = 0
        sac_trace.cmpinc = 0

    # change some headers about event
    sac_trace.evla = float(event["latitude"])
    sac_trace.evlo = float(event["longitude"])
    sac_trace.evdp = float(event["depth"])
    sac_trace.mag = float(event["magnitude"])
    # change reference time
    sac_trace.nzyear = utcevent.year
    sac_trace.nzjday = utcevent.julday
    sac_trace.nzhour = utcevent.hour
    sac_trace.nzmin = utcevent.minute
    sac_trace.nzsec = utcevent.second
    sac_trace.nzmsec = utcevent.microsecond / 1000
    sac_trace.o = 0
    sac_trace.iztype = 'io'

    # SAC file lodation
    sub_fldr_nm = utcevent.strftime("%Y%m%d%H%M%S")
    sac_loc = os.path.join(output_dir, sub_fldr_nm)
    if not os.path.exists(sac_loc):
        os.mkdir(sac_loc)
    sac_flnm = [utcevent.strftime("%Y")]
    sac_flnm += [utcevent.strftime("%j")]
    sac_flnm += [utcevent.strftime("%H")]
    sac_flnm += [utcevent.strftime("%M")]
    sac_flnm += [utcevent.strftime("%S")]
    sac_flnm += ["0000"]
    sac_flnm += [str(sac_trace.knetwk), str(sac_trace.kstnm),
                 "00", str(sac_trace.kcmpnm), "M", "SAC"]
    sac_flnm_str = ".".join(sac_flnm)
    sac_pathname = os.path.join(sac_loc, sac_flnm_str)
    sac_trace.write(sac_pathname)
    return


def Tri_ms2SAC((event, stationinfo, data_dir, output_dir)):
    """
    Function used to process particular event

    @event: dict    ;dict concluding serevral important info of particular event
    @stationinfo: dict   ;dict concluding station information
    @Data_dir: string  ;The dirname of mseed data
    @output_dir: string ; The dirname of trimed event data(SAC format)
    """
    # obtain folder name
    utcevent, end_utcevent, folder_name = starttime_endtime_folder(
        event["starttime"])
    # obtain stations in two folders
    strtfolder_list, endfolder_list = scan_stations(data_dir, folder_name)
    # obtain waveform
    trim_waveform(data_dir, event, stationinfo, utcevent, end_utcevent,
                  folder_name, strtfolder_list, endfolder_list, output_dir,
                  verbose=True)


data_dir = "/run/media/seispider/Seagate Backup Plus Drive/"
catalog_dirname = "../bg6.5.csv"
stationinfo_dirname = "../station.info.norm"
output_dir = "../test/"

# load catalog file
catalogs = load_catalog(data_dir=data_dir, catalog_dirname=catalog_dirname)
# load stationinfo file
stationinfo = load_stationinfo(stationinfo_dirname)

MULTIPROCESS = False      # if True:  multiprocess turn on  else: turn of
# how many concurrent processes? (set None to let multiprocessing module
# to decide)
NB_PROCESSES = 3

# ==========================
# multiple parameters for map
# ==========================


def universal_worker(input_pair):
    function, args = input_pair
    return function(*args)


def pool_args(function, *args):
    return zip(it.repeat(function), zip(*args))


if MULTIPROCESS:
    pool = mp.Pool(NB_PROCESSES)
    pool.map(universal_worker, pool_args(Tri_ms2SAC, zip(catalogs,
                                                         it.repeat(stationinfo), it.repeat(data_dir), it.repeat(output_dir))))
else:
    for event in catalogs:
        Tri_ms2SAC((event, stationinfo, data_dir, output_dir))
