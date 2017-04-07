#/usr/bin/env python
#-*- coding:utf8 -*-
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
import datetime as dt
import glob
from obspy import read
from obspy import Stream
import os
from obspy.io.sac import SACTrace
import time
# load events catalog
def load_catalog(Data_dir="./Data", Catalog_dirname="./events.csv"):
    """
    Function used to load events catalog file

    Input variables:
    @Data_dir: string     ;Directory of Data
    @Catalog_dirname: string  ;Directory+name of events Catalog_dir

    Output variables:
    @Catalogs: list    ;list of dictionary which contain starttime, latitude,
                        longitude, depth, magnitude
    """
    Catalog_file = open(Catalog_dirname)
    lines = Catalog_file.readlines()

    Catalogs = []
    for line in lines:
        starttime, latitude, longitude, depth, magnitude = ("".join(line)).split()[0:5]
        Catalog = {"starttime":starttime, "latitude":latitude, "longitude":longitude,
                    "depth":depth, "magnitude":magnitude}
        Catalogs.append(Catalog)
    return Catalogs

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
    info_file = open(stationinfo_dirname)
    lines = info_file.readlines()
    stationinfo_list=[]
    for line in lines:
        net, sta, loc, cha = (("".join(line).split())[0]).split(".")[-6:-2]
        stla, stlo, stel, stdp, cmpaz, cmpinc = "".join(line).split()[-6:]
        stationinfo = {"net":net, "sta":sta, "loc":loc, "cha":cha, "stla":stla,
          "stlo":stlo, "stel":stel, "stdp":stdp, "cmpaz":cmpaz, "cmpinc":cmpinc}
        stationinfo_list.append(stationinfo)
    return stationinfo_list


# Obtain data folder name
def starttime_endtime_folder(starttime, Event_last_time = 6000, verbose = True):
    """
    function used to obtain the folder name

    Input variables:
    @starttime: UTCDateTime     ;Time of UTC earthquake starttime

    Output variables:
    @folder_name: list        ;The folder name
    """
    # change string starttime to UTCDateTime
    UTCEvent = UTCDateTime(starttime)
    # Change this UTC time to Beijing Time
    Beijing_Event = UTCEvent + dt.timedelta(hours=8)
    # obtain end time of Beijing time zone
    End_Beijing_Event = Beijing_Event + Event_last_time
    # obtain end time of UTC
    End_UTCEvent = UTCEvent + Event_last_time

    # transfer UTCDatetime to string
    Beijing_Event_str = obtain_YYYYMMDD(Beijing_Event)
    End_Beijing_Event_str = obtain_YYYYMMDD(End_Beijing_Event)

    folder_name = []
    if Beijing_Event_str == End_Beijing_Event_str:
        if verbose:
            print "Event lasted in one day---{}".format(Beijing_Event_str)
        folder_name.append(Beijing_Event_str)
    else:
        if verbose:
            print "Event lasted in two days--{begin}-{end}".format(begin=Beijing_Event_str,
                                                    end=End_Beijing_Event_str)
        folder_name.append(Beijing_Event_str)
        folder_name.append(End_Beijing_Event_str)
    return  UTCEvent, End_UTCEvent, folder_name

def obtain_YYYYMMDD(UTCtime):
    """
    function used to obtain YYYYMMDD
    eg. 20160501

    Input variables:
    @UTCtime: UTCDateTime    ;Time to be translated to string

    Output variables:
    @YYYYMMDD: string        ;Time string transfered from UTCDateTime class
    """
    # divide time to year,month,day
    Year = str(UTCtime.year)
    Month = "{:0>2d}".format(UTCtime.month)
    Day = "{:0>2d}".format(UTCtime.day)
    YYYYMMDD = Year + Month + Day + "/"
    return YYYYMMDD

def obtain_stations_list(folder_dirname,suffix="mseed"):
    """
    obtain stations data lists

    @folder_dirname: string    ;dirname to obtain stations data list
    @stations: list            ;list of dictionary containing info of stations
    """
    Data_list = glob.glob(folder_dirname+"*.{}".format(suffix))
    if not Data_list:
        print "No Data in {}".format(folder_dirname)
    stations = []
    for Data_list_num in Data_list:
        net, sta, loc, cha, btime = (Data_list_num.split("/")[-1]).split(".")[0:5]
        station = {"net":net, "sta":sta, "loc":loc, "cha":cha, "btime":btime}
        stations.append(station)
    return stations

# scan stations in particular folder
def Scan_stations(Data_dir,folder_name):
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
        startfolder_stations_dirname = Data_dir + folder_name[0]
        endfolder_stations_dirname   = startfolder_stations_dirname
        # test if this directory exist
        if not os.path.exists(startfolder_stations_dirname):
            print "Dir {} not exist".format(startfolder_stations_dirname)
            startfolder_stations_list = []
            endfolder_stations_list = []
    else:
        # obtain the data dir+name and check weather this folder is empty
        startfolder_stations_dirname = Data_dir + folder_name[0]
        # test if startfolder_Stations_dirname directory exist
        if not os.path.exists(startfolder_stations_dirname):
            print "Dir {} not exist".format(startfolder_stations_dirname)
            startfolder_stations_list = []
        endfolder_stations_dirname = Data_dir + folder_name[1]
        # test if endfolder_Stations_dirname directory exist
        if not os.path.exists(endfolder_stations_dirname):
            print "Dir {} not exist".format(endfolder_stations_dirname)
            endfolder_stations_list = []

    startfolder_stations_list = obtain_stations_list(startfolder_stations_dirname)
    endfolder_stations_list = obtain_stations_list(endfolder_stations_dirname)
    return startfolder_stations_list, endfolder_stations_list

# trim data and return waveform
def trim_waveform(Data_dir, event, stationinfo_dirname, UTCEvent, End_UTCEvent,
                    folder_name, startfolder_stations_list, endfolder_stations_list,
                                                                verbose=True):
    """
    trim waveform for particular event

    @event: dict            ; event information
    @UTCEvent: UTCDateTime   ;UTC time when the event happened
    @stationinfo_dirname: string   ; string of station info file location
    @End_UTCEvent: UTCDateTime ;UTC time when the event end
    @startfolder_stations_list   ;list of stations dictionary in begintime folder
    @endfolder_stations_list     ;list of stations dictionary in endtime folder
    @waveform: Stream            ;Stream of event waveform
    """
    # return none if stations_list is empty
    if not startfolder_stations_list:
        return None
    if not endfolder_stations_list:
        return None

    # load stationinfo file
    stationinfo_list = load_stationinfo(stationinfo_dirname)

    # obtain event waveform
    if startfolder_stations_list == endfolder_stations_list:
        if verbose:
            print "Event didn't cross days"
        waveform = trim_oneday(Data_dir, event, stationinfo_list,UTCEvent, End_UTCEvent,
                              folder_name,startfolder_stations_list,verbose=True)
    else:
        if verbose:
            print  "Event crossed days"
        waveform=trim_crossdays(Data_dir, event, stationinfo_list, UTCEvent, End_UTCEvent,
                    folder_name,startfolder_stations_list, endfolder_stations_list,
                                                                verbose=True)


def trim_crossdays(Data_dir, event, stationinfo_list, UTCEvent, End_UTCEvent, folder_name,
            startfolder_stations_list, endfolder_stations_list, verbose=True):
    """
    trim waveform if event don't cross days

    @event: dict            ; event information
    @UTCEvent: UTCDateTime       ;UTC time when the event happened
    @End_UTCEvent: UTCDateTime   ;UTC time when the event end
    @startfolder_stations_list:list ;list of stations dictionary in begintime folder
    @waveform:Stream  ;trimed waveform
    @stationinfo_list: list     ;list of station info
    """
    # initialization of waveform_start and waveform_end
    waveform_start = Stream()
    waveform_end = Stream()
    for stationA in startfolder_stations_list:
        filename_start = ".".join([stationA["net"], stationA["sta"], stationA["loc"],
                                    stationA["cha"], stationA["btime"], "mseed"])
        dirname_start = Data_dir + folder_name[0] + filename_start

        # check file existence
        if not os.path.isfile(dirname_start):
            if verbose:
                print "file--{} not exist".format(filename_start)
            continue
        waveform_start = read(dirname_start, starttime=UTCEvent)

        station_file = glob.glob(Data_dir+folder_name[1]+"*"+stationA["net"]+"."
                                        +stationA["sta"]+"*"+stationA["cha"]+"*")
        if not station_file:
            print "No Data in end folder"
            continue
        dirname_end = station_file[0]
        waveform_end = read(dirname_end, endtime=End_UTCEvent)

        # Merge seperated data
        waveform = Stream()
        waveform = waveform_start + waveform_end
        waveform.merge(fill_value=0)
        #todo: write data as SAC format
        if not waveform:
            continue
        writeSAC(waveform, event, folder_name, UTCEvent, stationA, stationinfo_list)




def trim_oneday(Data_dir, event, stationinfo_list,  UTCEvent, End_UTCEvent, folder_name,
                                        startfolder_stations_list,verbose=True):
    """
    trim waveform if event don't cross days

    @event: dict            ; event information
    @UTCEvent: UTCDateTime       ;UTC time when the event happened
    @End_UTCEvent: UTCDateTime   ;UTC time when the event end
    @startfolder_stations_list:list ;list of stations dictionary in begintime folder
    @waveform:Stream  ;trimed waveform
    @stationinfo_list: list     ;list of station info
    """
    for station in startfolder_stations_list:
        filename = ".".join([station["net"], station["sta"], station["loc"],
                                    station["cha"], station["btime"], "mseed"])
        dirname = Data_dir + folder_name[0] + filename
        if not os.path.isfile(dirname):
            if verbose:
                print "file--{} not exist".format(filename)
            continue
        waveform = read(dirname, starttime=UTCEvent, endtime=End_UTCEvent)
        if not waveform:
            continue
        writeSAC(waveform, event, folder_name, UTCEvent, station, stationinfo_list)




def writeSAC(waveform, event, folder_name, UTCEvent, station, stationinfo_list):
    """
    function used to write data with SAC format

    @event: dict                ; event information
    @waveform: Stream           ;Stream of event waveform
    @station: dict              ;station dictionary
    @stationinfo_list: list     ;list of station info
    """
    Match = False
    # The waveform may is constructed by several traces-- merge them
    waveform.merge(fill_value=0)
    Trace = waveform[0]
    for station_info in stationinfo_list:
        Match  = (station["net"]==station_info["net"])
        Match *= (station["sta"]==station_info["sta"])
        Match *= (station["loc"]==station_info["loc"])
        Match *= (station["cha"]==station_info["cha"])
        if Match:
            # transfer obspy trace to sac trace
            sac_trace_init = SACTrace()
            sac_trace = sac_trace_init.from_obspy_trace(trace=Trace)

            # change some headers about station
            sac_trace.stla = float(station_info["stla"])
            sac_trace.stlo = float(station_info["stlo"])
            sac_trace.stel = float(station_info["stel"])
            sac_trace.stdp = float(station_info["stdp"])
            sac_trace.cmpaz = float(station_info["cmpaz"])
            sac_trace.cmpinc = float(station_info["cmpinc"])

            # change some headers about event
            sac_trace.evla = float(event["latitude"])
            sac_trace.evlo = float(event["longitude"])
            sac_trace.evdp = float(event["depth"])
            sac_trace.mag = float(event["magnitude"])
            # change reference time
            sac_trace.nzyear = UTCEvent.year
            sac_trace.nzjday = UTCEvent.julday
            sac_trace.nzhour = UTCEvent.hour
            sac_trace.nzmin = UTCEvent.minute
            sac_trace.nzsec = UTCEvent.second
            sac_trace.nzmsec = UTCEvent.microsecond/1000
            sac_trace.o   = 0

            # SAC file lodation
            YY_str =  "{:0>4d}".format(UTCEvent.year)
            MN_str =  "{:0>2d}".format(UTCEvent.month)
            Dy_str =  "{:0>2d}".format(UTCEvent.day)
            jd_str =  "{:0>3d}".format(UTCEvent.julday)
            HH_str =  "{:0>2d}".format(UTCEvent.hour)
            mm_str =  "{:0>2d}".format(UTCEvent.minute)
            SS_str =  "{:0>2d}".format(UTCEvent.second)

            sub_folder_name = YY_str + MN_str + Dy_str + HH_str + mm_str + SS_str
            sac_location = "../Event_data/" + sub_folder_name + "/"
            if not os.path.exists(sac_location):
                os.mkdir(sac_location)
            SAC_filename_list = [YY_str, jd_str, HH_str, mm_str, SS_str, "0000"]
            SAC_filename_list+= [str(sac_trace.knetwk), str(sac_trace.kstnm),
                    "00", str(sac_trace.kcmpnm),"M","SAC"]
            SAC_filename_str = ".".join(SAC_filename_list)
            SAC_Pathname = sac_location + SAC_filename_str
            sac_trace.write(SAC_Pathname)
            break
    if not Match:
        print "No info for station-{}".format(station_info["sta"])


Data_dir = "/run/media/seispider/Seagate Backup Plus Drive/"
Catalog_dirname = "../test.csv"
stationinfo_dirname = "../stations.list"
# load catalog file
Catalogs = load_catalog(Data_dir=Data_dir, Catalog_dirname=Catalog_dirname)
for event in Catalogs:
    # obtain folder name
    UTCEvent, End_UTCEvent, folder_name = starttime_endtime_folder(event["starttime"])
    print folder_name
    # obtain stations in two folders
    startfolder_stations_list,endfolder_stations_list = Scan_stations(Data_dir,
                                                                    folder_name)
    # obtain waveform
    trim_waveform(Data_dir, event, stationinfo_dirname, UTCEvent, End_UTCEvent,
        folder_name,startfolder_stations_list, endfolder_stations_list, verbose=True)






