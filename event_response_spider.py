# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
#      Purpose: Find response files for stations in each event
#       Status: Developing
#   Dependence: Python 3.6
#      Version: ALPHA
# Created Date: 15:58h, 31/01/2018
#        Usage:
#               python event_response_spider.py
#
#
#       Author: Xiao Xiao, https://github.com/SeisPider
#        Email: xiaox.seis@gmail.com
#     Copyright (C) 2017-2017 Xiao Xiao
#-------------------------------------------------------------------------------
"""
Find and rewrite response files for each event
"""
from lib.respider import SourceResponse, logger
from obspy import UTCDateTime
from os.path import join, exists
import os, codecs
import multiprocessing as mp
from multiprocessing import Manager, Process, Pool
import itertools as it


def event_assign(time, database, export_dir="./event"):
    """Create response files for one particular event
    
    Parameter
    =========
    time : `~ObsPy.UTCDateTime`
        Origin Time
    database : `~respider.SourceResponse`
        database including response files
    export_dir : str
        directory of output
    """
    # check directory existences
    subdir = join(export_dir, time.strftime("%Y%m%d%H%M%S"))
    if not exists(subdir):
        os.makedirs(subdir, exist_ok=True)
     
    def network_rewrite(network_resp, subdir):
        """Handle rewrite work of a network
        """
        for key, value in network_resp.items():
            net, sta, loc, cha = key.split(".")
            outputfilename = "_".join(["PZs", net, sta, loc, cha])
            outputfilename = join(subdir,  outputfilename)
            try:
                rewrite_sacpz(value, outputfilename)
            except:
                logger.error("Can't rewrite")
    
    
    responses = database.response_files_extractor(time)
    for response in responses:
        network_rewrite(response, subdir)

def rewrite_sacpz(inputfilename, outputfilename):
    """output sacpz file

    Parameter
    =========
    inputfilename : str
        file location and name of inputted sacpz file
    outputfilename : str
        file location and name of to be wrriten sacpz file
    """
    with codecs.open(inputfilename, 'r', 'gbk') as inputf:
        lines = inputf.readlines()
    
    with codecs.open(outputfilename, 'w') as outputf:
        for line in lines:
            if line[0] == "*":
                continue
            else:
                outputf.writelines(line)

if __name__ == '__main__':
    # import dresponse file location
    sourceresponse = SourceResponse(subdir="./info/Response")

    # import event info
    with open("./catalog_released.csv") as f:
        lines = f.readlines()
    for line in lines:
        origin = UTCDateTime(line.split()[0])
        event_assign(origin, sourceresponse)
        logger.info("Fini. {}".format(origin.strftime("%Y%m%d%H%M%S")))

        


    
