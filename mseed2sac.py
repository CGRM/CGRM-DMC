class Client(object):
    def __init__(self, catalog, stationinfo, seeddir, sacdir):
        self.catalog = catalog
        self.stationinfo = stationinfo
        self.seeddir = seeddir
        self.sacdir = sacdir

        self.events = read_catalog()
        self.stations = read_stations()

    def read_catalog():
        pass

    def read_stations():
        pass

    def _read_mseed(self, station, dirnames, starttime, duration):
        if len(dirnames) == 1: # one day
            st = read(dirnames[0] + "*.net.sta.*")
        elif len(dirnames) == 2: # two day
            st = read(dirnames[0] + "*.net.sta.*") + read(dirnames[1] + "*.net.sta.*")
        st.merge()
        st.trim(starttime, endtime) # can also trim in read(), not sure it works for two day case
        return st

    def write_sac(trace, station):
        # trace can contain 3-component data
        pass

    def get_waveform(self, starttime, duration):
        # return a list: one or two dirname
        dirnames = get_dirname(starttime, duration)
        for station in self.stations: # loop over all stations maybe better
            trace = _read_mseed(station)
            writesac(trace, station)

if __name__ == '__main__':
    client = Client("catalog", "station.info", "SEEDDIR", "SACDIR")

    for event in client.events:
        client.get_waveform(starttime, duration)
