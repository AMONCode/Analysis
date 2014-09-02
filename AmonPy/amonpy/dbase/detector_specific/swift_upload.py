import pyfits
import MySQLdb as mdb
import getpass
import swift_functions as swift
import math
import glob
from scipy.interpolate import interp1d
import itertools
from argparse import ArgumentParser
import sys

def parse_command_line():
    parser = ArgumentParser()#)usage='run_archival [--host address] [--username username] [--database name] [--output-config int] [ALERT CONFIG CHOICE] [ADDITIONAL OPTIONS]')
    parser.add_argument("--attitude-files", default='/usr/local/amon/data_storage/Swift_Sub_Sub/attitude_files/monthly_files', help="Path to attitude files directory default: /usr/local/amon/data_storage/Swift_Sub_Sub/attitude_files/monthly_files")
    parser.add_argument("--fits-files", default='/usr/local/amon/data_storage/Swift_Sub_Sub/monthly_data', help="Path to fits files directory [default: /usr/local/amon/data_storage/Swift_Sub_Sub/monthly_data]")
    parser.add_argument("--pvalue-file", default='pvalue_table.txt', help="Path to SNR to P-Value table [default: pvalue_table.txt]")
    parser.add_argument("-H", "--host", metavar="address", default='db.hpc.rcc.psu.edu', 
            help="Database host address [default: db.hpc.rcc.psu.edu]")
    # TODO Add feature to pull username from login information so that the
    # username option is optional, similar to how MySQL is used from the command
    # line
    parser.add_argument("-u", "--username", metavar="username", help="Database username")
    parser.add_argument("-d", "--database", metavar="name", help="Name of database")

    return parser.parse_args()

class attitude:
	''' Class to interpolate latitude, longitude, and elevation values from data taken from Swift attitude files The relevant data from the attitude files are currently grouped in txt files with four columns, in this order: time, latitude, longitude, elevation
	'''
	def __init__(self,pos_files):
		# Store the list of files, as well as start counting which
		# element in the list is currently being used. 
		self.file_locs = pos_files 
		self.file_num = 0
		self.compute_interpolate_position()
                self.files_exhausted = False

	def compute_interpolate_position(self):
		# Opens the files, stores the information in lists, then
		# creates interpolated class objects for latitude, longitude,
		# and elevation
		print 'Opening monthly attitude file %s' % self.file_locs[self.file_num]
		monthly_data = open(self.file_locs[self.file_num],'r')
		position_data = []
		for row in monthly_data.readlines():
			position_data.append([float(value) for value in row.split(' ')])
		position_data_izip = itertools.izip(*position_data)
		self.attitude_time = position_data_izip.next()
		latitude = position_data_izip.next()
		longitude = position_data_izip.next()
		elevation = position_data_izip.next()
		self.interp_latitude = interp1d(self.attitude_time,latitude)
		self.interp_longitude = interp1d(self.attitude_time,longitude)
		self.interp_elevation = interp1d(self.attitude_time,elevation)
		
		# A check to ensure validity of interpolation.  Values
		# interpolated in gaps greater than 600 seconds (invalid_gaps)
		# should not be trusted, values interpolated in gaps between
		# 100 and 600 seconds (warning_gaps) can be trusted, but the
		# user should be made aware that the values will be less
		# accurate 
		attitude_time_check = [time2 - time1 for time1, time2 in zip(self.attitude_time[:-1], self.attitude_time[1:])]
		self.warning_gaps = [arg_gap for arg_gap, gap in enumerate(attitude_time_check) if gap >= 100]
		self.invalid_gaps = [arg_gap for arg_gap in self.warning_gaps if attitude_time_check[arg_gap] >= 600]

	def interpolate_position(self,event):
		# Attempt to interpolate the values of lat, long, and elev with
		# observation time.  If observation time is before the attitude
		# time window starts, set the values to None.  If it's after
		# the attitude time window, go to the next attitude file
		try:
                        if not self.files_exhausted:
                                latitude = (float(self.interp_latitude(event.observation_time)),)*event.num_detection
                                longitude = (float(self.interp_longitude(event.observation_time)),)*event.num_detection
                                elevation = (float(self.interp_elevation(event.observation_time)),)*event.num_detection

                                # Make sure time of observed event takes places in a
                                # complete section of the attitude files.  If not, the
                                # interpolated value can be less accurate or even
                                # wrong.  
                                for warning_arg in self.warning_gaps:
                                        if self.attitude_time[warning_arg] < event.observation_time < self.attitude_time[warning_arg+1]:
                                                event.set_position_flag()
                                                if warning_arg in self.invalid_gaps:
                                                        latitude = (None,)*event.num_detection
                                                        longitude = (None,)*event.num_detection
                                                        elevation = (None,)*event.num_detection
                        else:
                                event.set_position_flag()
                                latitude = (None,)*event.num_detection
                                longitude = (None,)*event.num_detection
                                elevation = (None,)*event.num_detection
			return latitude, longitude, elevation
		except ValueError:
                        self.file_num += 1
                        try:
                                self.compute_interpolate_position()
                        except IndexError:
                                self.files_exhausted = True
                        return self.interpolate_position(event)

class observation:
	'''
	Class to store all of the information needed by the MySQL database for a set of observations at a given time.
	Information will be stored in tuples, and each observation in a given detection will have its own tuple element
	i.e. if there are two observations at the same time, the time tuple will be a 2 element tuple of identical times
	'''
	def __init__(self, row, data_list_arg, pvalue_interp_class, positions):
		# First check with observations have valid SNR values, those
		# are the only events we care about.  The fits file may have
		# observations without SNR values, which are useless to us.  In
		# addition, the file is set up to have up to 20 observations at
		# a time, which is rarely the case.  Many columns in the file
		# have arrays of 20 elements, and any that aren't being used
		# have Nan elements.  e.g. if there's only 2 events, an array
		# may look like [value1, value2, NaN, NaN,...,NaN]
		self.snr = tuple(snr for snr in row[data_list_arg['SNR']] if not math.isnan(snr))

		# Check how many detections were made at the time of this
		# observation
		self.num_detection = len(self.snr)

		# Set Swift stream number as 1, and use hardcoded revision
		# number and stream revision number of 0
		self.stream_config = (1,) * self.num_detection
		self.rev = (0,) * self.num_detection
		self.stream_rev = (0,) * self.num_detection

		# Get the observation time, which is in seconds since the
		# launch of the Swift satellite.  Use met2day function in
		# swift_custom_module to split into time stamp and msec
		# components Currently set to use random time stamps
		self.observation_time = row[data_list_arg['TIME']]
                # TODO Add command line option to decide if using random time
                # stamps or real ones
		#self.time = (swift.met2day(self.observation_time)[0],) * self.num_detection
		self.time = swift.random_time_stamp(self.num_detection)
		self.time_msec = (swift.met2day(self.observation_time)[1],) * self.num_detection

		# Get the ra and dec of the source
		self.ra_obj = tuple(ra for ra in row[data_list_arg['RA_OBJ']][:self.num_detection])
		self.dec_obj = tuple(dec for dec in row[data_list_arg['DEC_OBJ']][:self.num_detection])

		# Get the ra and dec of the center of the decector
		self.ra_cent = (row[data_list_arg['RA_CENT']],) * self.num_detection
		self.dec_cent = (row[data_list_arg['DEC_CENT']],) * self.num_detection

		# Set the type of event and psf_type
		self.db_type = ('observation',) * self.num_detection
		self.psf_type = ('fisher',) * self.num_detection

		# Interpolate the pvalue from the SNR
		#FIXME Currently, if snr < 2.6005, pvalue will be 0.  
		self.pvalue = tuple(float(pvalue_interp_class(snr)) for snr in self.snr)

                # Set uncertainties
                # FIXME sigma_time commented out until an estimate of GRB
                # duration (sigma_t in the database) is found
                #self.sigma_time = (60,) * self.num_detection
                self.sigma_r = (0.05,) * self.num_detection

                # Set position flag to false.  If a problem arises in the
                # attitude files s.t. latitute, longitude, and elevation cannot
                # be accurately computed, this flag will be triggered
                self.position_flag = 0
	
	def set_pos_id(self, id_interval_start, positions):
		# Sets position and event_id attributes This event_id is only
		# valid within the file that the events are coming from.  A
		# constant (possibly 0) will be added to all event_id's before
		# being uploaded to the database to maintain a consistent id
		# numbering
		self.event_id = tuple(id_interval_start + id_increment for id_increment in xrange(self.num_detection))

		#Interpolate latitude, longitude, and elevation values
		#self.latitude, self.longitude, self.elevation = positions.interpolate_position(self.observation_time,self.num_detection,self.event_id[0])
		self.latitude, self.longitude, self.elevation = positions.interpolate_position(self)

        def set_position_flag(self):
                self.position_flag = 1



def get_swift_data(fits_file_loc, pvalue_interp_class, positions):
	'''
	Obtain the swift data as a list of class objects
	'''
	# Open the fits file, and then find the location of the relevant
	# columns
        print 'Opening monthly fits file %s' % fits_file_loc
        fits_file = pyfits.open(fits_file_loc)[1]
	data_list = ['SNR','TIME','RA_OBJ','DEC_OBJ','RA_CENT','DEC_CENT']
	data_list_arg = {prop: fits_file.columns.names.index(prop) for prop in data_list}

	# Create a list of class objects for all of the detections
	all_events = [observation(row, data_list_arg, pvalue_interp_class, positions) for row in fits_file.data]

	# Get rid of detections with no valid SNR values
	snr_events = [event for event in all_events if event.num_detection]

	# Set event id for databases.  Should be noted that these event ids
	# will only be relative to each other, and a constant will need to be
	# added before loading into the database
	snr_events[0].set_pos_id(1, positions)
	for num, event in enumerate(snr_events[1:]):
		event.set_pos_id(snr_events[num].event_id[-1]+1, positions)
	return snr_events

def interpolate_pvalue(pvalue_file_loc): 
	'''
	Open a file containing snr values and corresponding pvalues.  Use to created interpolate object
	'''
	pvalue_file = open(pvalue_file_loc,'r')
	snr_list = []
	pvalue_list = []
	i = 0
	for line in pvalue_file.readlines():
		[snr, pvalue] = line.split(' ')
		snr_list.append(float(snr))
		pvalue_list.append(float(pvalue))
	pvalue_interp_class = interp1d(snr_list,pvalue_list,bounds_error=False,fill_value=0.0)
	return pvalue_interp_class

def db_load(snr_events, pw, options):
        '''
        Load the data into the MySQL database
        '''

        # Open the connection
	con = mdb.connect(options.host,options.username,pw,options.database)
	with con:
		cur = con.cursor() 

                # Grab the highest id currently in the table event and set the
                # starting id to one higher.  id_start written as is to get an
                # int from a tuple
                start_id = cur.execute("SELECT MAX(id) FROM event;")
                id_start = [int(id) for id in cur.fetchone()][0]

                # Iterate through the events and load them into the database
                # Note that for SQL queries, need to use %s for placeholder
                # because MySQL will convert the value to a literal, not
                # python.
		for i in xrange(len(snr_events)):
                        event_ids = tuple(event_id + id_start for event_id in snr_events[i].event_id)
			mysql_event_statement = "INSERT INTO event(eventStreamConfig_stream, id, rev, time, time_msec, `Dec`, RA, sigmaR, pvalue, type, point_RA, `point_Dec`, \
                                        longitude, latitude, elevation, psf_type, eventStreamConfig_rev) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
			event_data = zip(snr_events[i].stream_config, event_ids, snr_events[i].rev, snr_events[i].time, snr_events[i].time_msec, \
                                        snr_events[i].dec_obj, snr_events[i].ra_obj, snr_events[i].sigma_r, snr_events[i].pvalue, snr_events[i].db_type, \
                                        snr_events[i].ra_cent, snr_events[i].dec_cent, snr_events[i].longitude, snr_events[i].latitude, snr_events[i].elevation, \
                                        snr_events[i].psf_type, snr_events[i].stream_rev)
                        mysql_parameter_statement = "INSERT INTO parameter(name, value, units, event_eventStreamConfig_stream, event_id, event_rev) VALUES \
                                        (%s, %s, %s, %s, %s, %s)"
                        parameter_data = zip(('position_accuracy_warning',)*snr_events[i].num_detection, (snr_events[i].position_flag,)*snr_events[i].num_detection, \
                                        ('no units',)*snr_events[i].num_detection, snr_events[i].stream_config, event_ids, snr_events[i].rev)
			cur.executemany(mysql_event_statement,event_data)
			cur.executemany(mysql_parameter_statement,parameter_data)

###########################################################################################################
###													###
###						Main							###
###													###
###########################################################################################################

# Parse the command line options
options=parse_command_line()

# Get the MySQL database password
pw = getpass.getpass('Database Password:')

#print sorted(glob.glob(options.attitude_files + '/attitude_month*'))
# Get the files needed
positions = attitude(sorted(glob.glob(options.attitude_files + '/attitude_month*')))
pvalue_file_loc = options.pvalue_file
fits_file_locations = sorted(glob.glob(options.fits_files + '/*'))

# Create the interpolated pvalue class to convert from SNR to pvalue
pvalue_interp_class = interpolate_pvalue(pvalue_file_loc)

# Get the events from the fits files
for fits_file in fits_file_locations:
        snr_events = get_swift_data(fits_file, pvalue_interp_class, positions)
        db_load(snr_events, pw, options)
