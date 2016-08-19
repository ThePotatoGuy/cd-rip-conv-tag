"""
@author Andre Allan Ponce
@email andreponce@null.net

python script that checks for a cd in the drive, rips it, converts
the files to flac, writes the tags (if possible), and then deletes 
the temporary wav files.

The tags written will be basic (album title, album artist, track title,
track artist)

Programs called:
	cd-info
	cdparanoia
	ffmpeg

This script will also check if those programs exist before executing 
"""

import io
import os
import subprocess

###	General constants	================================================

EXITING = 'Exiting...'
EMAIL = 'andreponce@null.net'
PARSE_OUTPUT_FAILED = 'The {0:s} program did not produce the required output. \nPlease send an email to '+EMAIL+' with the version number of this program and the name and version number of {0:s}.'
NEWLINE = '\n'

###	Formatting Constants	============================================

# initalize user prompt formatting
HEADER_BAR = '----------------------------'

##	program flow control constants	====================================

SKIP_PROGRAM_TEST = True
SKIP_CD_INFO = False
SKIP_CD_PARA = True
SKIP_FFMPEG = True

########################################################################
###	CLASSES	############################################################
########################################################################

## struct style object to hold album data
class AlbumData:
	# album data
	album_artist = 'Unknown'
	album_title = 'Untitled'
	number_of_tracks = 0
	
	# track data
	track_names = list()
	track_artists = list() # only used if has_multiple_artists is true
	
	# boolean to say if this album has multiple artists or not
	# (i.e: different tracks have different artists (various artists)
	has_multiple_artists = False
	
	# function to print the data stored in this class in a nice format
	def printData(self):
		# print album
		print("Album title: "+self.album_title)
		print("Album artist: "+self.album_artist)
		print("Number of tracks: "+str(self.number_of_tracks))
		
		# print tracks
		for track_number in range(0,self.number_of_tracks):
			print("Track "+str(track_number+1)+": ",end="")
			
			if(self.has_multiple_artists):
				print(self.track_artists[track_number],end="")
			else:
				print(self.album_artist,end="")
				
			print(" - "+self.track_names[track_number])

########################################################################
###	initial tests if program exists	####################################
########################################################################

###	program names/commands	============================================

CMD_CD_INFO = 'cd-info'
CMD_CDPARA = 'cdparanoia'
CMD_FFMPEG = 'ffmpeg'

CMD_VERSION = '--version'

CMDS = (CMD_CD_INFO, CMD_CDPARA, CMD_FFMPEG)

CMD_ERROR = 'ERROR: {:s} not found'

###	program testing functions	========================================
def checkProgram():
	for cmd in CMDS:
		try:
			cmd_list = list()
			cmd_list.append(cmd)
			
			if cmd != CMD_FFMPEG: 
				# cd-info and cdparanoia need version flag
				cmd_list.append(CMD_VERSION)
				
			subprocess.run(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				
		except FileNotFoundError:
			print(CMD_ERROR.format(cmd))
			print(EXITING)
			exit(1)

### begin program testing flow	========================================

if SKIP_PROGRAM_TEST:
	print('Skipping required program check')
else:
	print('Checking if required programs exist...')
	checkProgram()
	
########################################################################
###	pull tags if possible using cd-info	################################
########################################################################

### cd-info constants	================================================

# cd-info specific flags
CMD_CD_INFO_FLAG_NO_DEV_INFO = '--no-device-info'
CMD_CD_INFO_FLAG_NO_DISC_MODE = '--no-disc-mode'

# cd-info keywords
STDOUT_CD_INFO_CDDB_START = 'CD Analysis Report'

# CDDB specific constants
CDDB_ALBUM_ARTIST = 'Artist:'
CDDB_ALBUM_TITLE = 'Title:'
CDDB_TRACK_ARTIST = 'artist:'
CDDB_TRACK_TITLE = 'title:'
CDDB_TRACK_BEGIN = 'Number of tracks:'

# CD-TEXT specific constants
CD_TEXT_NAME = 'CD-TEXT'
CD_TEXT_TITLE = 'TITLE:'
CD_TEXT_ARTIST = 'PERFORMER:'
CD_TEXT_DISC = 'Disc:'
CD_TEXT_UNT = 'UNTITLED'
CD_TEXT_UNK = 'UNKNOWN'
CD_TEXT_TRK = 'TRACK {:02d}'

###	cd-info functions	================================================

# function to check if every element in the given list is a -1
# ASSUMES the given list has at least 1 element
# @param _list	- the list to check
# @return True if every element is -1, False if not
def isEveryElementMinusOne(_list):
	return isEveryElementThisElement(_list,-1)

# function to check if every element in the given list is the same
# ASSUMES the given list has at least 1 element
# @param _list	- the list to check
# @return True if every element is the same, False if not
def isEveryElementTheSame(_list):
	element = _list[0]
	
	for item in _list:
		if element != item:
			return False
			
	return True

# function to check if every element in the given list is the same 
# as the given item
# ASSUMES the given list has at least 1 element
# @param _list	- the list to check
# @param item	- the item to check if _list is same
# @returns True if every element in _list is item, False if not
def isEveryElementThisElement(_list, item):
	if _list[0] == item:
		return isEveryElementTheSame(_list)
	return False

# function to prompt and ask them if they would like to use the 
# displayed tags.
# @returns:
#	0 when the user enters 'Y' or 'y' or any char other than 'N', 'n',
#		'q', 'Q'
#	1 when the user enters 'Q' or 'q'
#	-1 when the user enters 'N' or 'n'
def confirmUserTagSelection():
	user_answer = input('Do you want to use these tags? (Y/n/q)')
	if user_answer.casefold() == 'n': # no
		return -1
	elif user_answer.casefold() == 'q': # quit
		return 1
	# else assume user accepts
	return 0
	
# function to display a tag selection/vewing menu to the user
# @param cddb_list		- the tuple data returned from parseCDDB
# @param cd_text_list	- the tuple data returned from parseCDTEXT
# @returns the selected tags or None if none were selected
# TODO
def displayUserTagMenu(cddb_list, cd_text_list):
	print('nothing here yet')

# function to check if the given cddb text matched, which means we have
# tags.
# @param cddb_text	- cd-info's CDDB output
# @returns true if we have a cddb match, false otherwise
def hasCDDB(cddb_text):
	CDDB_start = parseCDDBKey(cddb_text, CMD_CD_INFO+":")
	# spliting the line by spaces helps us check the number of
	# matches. When the third token is a 0, then we have no
	# matches, otherwise we have at least 1
	tokens = CDDB_start[0].split()
	return tokens[2] != str(0)

# function to parse tags from CDDB
# @param cddb_text	- cd-info's CDDB output
# @returns an AlbumData built from the CDDB output
def parseCDDB(cddb_text):
	album = AlbumData()
	
	# begin parsing the individual parts
	# after parsing a part, we need the end index to begin search for
	# the next part
	retrieved_data = parseCDDBAlbumArtist(cddb_text)
	album.album_artist = retrieved_data[0]
	
	retrieved_data = parseCDDBAlbumTitle(cddb_text,retrieved_data[2])
	album.album_title = retrieved_data[0]
	
	retrieved_data = parseCDDBTracks(cddb_text, retrieved_data[2])
	album.track_names = retrieved_data[0]
	album.track_artists = retrieved_data[1]
	album.has_multiple_artists = retrieved_data[2]
	album.number_of_tracks = len(album.track_names)
	
	return album
	
# function to parse the album artist from CDDB
# @param cddb_text	- cd-info's CDDB output
# @param start		- the starting index to search for album artist
# @returns tuple consisting of:
#	- album artist
#	- starting index of the album artist line
#	- ending index of the album artist line
def parseCDDBAlbumArtist(cddb_text, start=0):
	return parseCDDBKey(cddb_text, CDDB_ALBUM_ARTIST, start)
	
# function to parse the album title from CDDB
# @param cddb_text	- cd-info's CDDB output
# @param start		- the starting index to search for album title
# @returns tuple consisting of:
#	- album title
#	- starting index of the album title line
#	- ending index of the album title line
def parseCDDBAlbumTitle(cddb_text, start=0):
	return parseCDDBKey(cddb_text, CDDB_ALBUM_TITLE, start)
	
# function to parse a key from the CDDB
# @param cddb_text	- cd-info's CDDB output
# @param key		- the choice of data to find
# @param start		- the starting index to search for album artist
# @returns tuple consisting of:
#	- entry
#	- starting index of the entry line
#	- ending index of the entry line
def parseCDDBKey(cddb_text, key, start=0):
	
	# retrieve the line that has the key
	key_index = cddb_text.find(key,start)
	key_end_index = cddb_text.find(NEWLINE,key_index+len(key))
	#print(str(key_index)+":"+str(key_end_index)+":"+str(len(key)))
	
	# cutout the data from that key and strip the surrounding single
	# quotes
	entry = cddb_text[key_index+len(key):key_end_index].strip().strip("\'")
	
	return (entry,key_index,key_end_index)
	
# function to parse a track artist from CDDB
# @param cddb_text	- cd-infpo's CDDB output
# @param start		- the starting index to search for album title
# @returns tuple consisting of:
#	- track artist
#	- starting index of the track artist line
#	- ending index of the track artist line
def parseCDDBTrackArtist(cddb_text, start=0):
	return parseCDDBKey(cddb_text, CDDB_TRACK_ARTIST, start)
	
# function to parse the tracks from CDDB
# @param cddb_text	- cd-info's CDDB output
# @param start		- the starting index to search for tracks
# @returns tuple consisting of
#	- list of track names
#	- list of track artists
#	- boolean where true means multiple artists, false means one artist
def parseCDDBTracks(cddb_text, start=0):
	track_data = parseCDDBKey(cddb_text, CDDB_TRACK_BEGIN, start)
	track_count = int(track_data[0])
	
	# parse through the CDDB text, finding tracks
	starting_point = track_data[2]
	track_artists = list()
	track_titles = list()
	for track in range(0,track_count):
		found_artist = parseCDDBTrackArtist(cddb_text,starting_point)
		found_title = parseCDDBTrackTitle(cddb_text,starting_point)
		track_artists.append(found_artist[0])
		track_titles.append(found_title[0])
		starting_point = found_title[2]
		
	return (track_titles, track_artists, (not isEveryElementTheSame(track_artists)))

# function to parse a track title from CDDB
# @param cddb_test	- cd-info's CDDB output
# @param start		- the starting index to search for track title
# @returns tuple consisting of:
#	- track title
#	- starting index of the track title line
#	- ending index of the track title line
def parseCDDBTrackTitle(cddb_text, start=0):
	return parseCDDBKey(cddb_text, CDDB_TRACK_TITLE, start)

# function to parse tags from CD-TEXT
# @param cd_text	- cd-info's CD-TEXT output
# @returns list of tuples where the first tuple is (album_name, artist)
#	and all following tuples consist of (track_name, artist)
#
# CD-TEXT Rules:
#	- if the CD-TEXT for a track is missing its TITLE, "TRACK #" will 
#	be used for the track title.
#	- if the CD-TEXT for a track is missing its PERFORMER, the PERFORMER
#	text for Disc will be used for the track artist, or "UNKNOWN" if 
#	Disc does not have the PERFORMER attribute.
#	- if the CD-TEXT for Disc is missing TITLE, "UNTITLED" will be used
#	for the album title.
#	- if the CD-TEXT for Disc is missing PERFORMER, "UNKNOWN" will be
#	used for the album artist.
# TODO: write this method
def parseCDTEXT(cd_text):
	print('nothing here yet')
	
# function to parse Disc tags from CD-TEXT
# @param cd_text	- cd-info's CD-TEXT output
# @param start		- starting index to search for Disc information
# @returns tuple consisting of:
#	- album title
#		-- will be "UNTITLED" if Disc is missing TITLE
#	- album artist (performer)
#		-- will be "UNKNOWN" if Disc is missing PERFORMER
#	- starting index of the disc data section
#	- ending index of the disc data section
# TODO
def parseCDTEXTDisc(cd_text, start=0):
	# retrieve disc data begin and endind index
	disc_data_begin = parseCDTEXTKey(cd_text,CD_TEXT_DISC,start)
	disc_data_end = parseCDTEXTKey(cd_text,CD_TEXT_NAME,disc_data_begin[2])
	disc_data_begin_index = disc_data_begin[2]
	disc_data_end_index = disc_data_end[1]
	
	# retrieve disc data
	disc_title_data = parseCDTEXTKey(cd_text,CD_TEXT_TITLE,disc_data_begin_index,disc_data_end_index)
	disc_artist_data = parseCDTEXTKey(cd_text,CD_TEXT_ARTIST,disc_data_begin_index,disc_data_end_index)
	
	# decide which datas are there or not
	disc_title = ''
	disc_artist = ''
	if isEveryElementMinusOne(disc_title_data):
		disc_title = CD_TEXT_UNT
	else:
		disc_title = disc_title_data[0]
	if isEveryElementMinusOne(disc_artist_data):
		disc_artist = CD_TEXT_UNK
	else:
		disc_artist = disc_artist_data[0]
		
	return (disc_title,disc_artist,disc_data_begin_index,disc_data_end_index)
	
# function to parse a CD-TEXT key from cd-info's CD-TEXT output
# @param cd_text	- cd-info's CD-TEXT output
# @param key		- the key to search for
# @param start		- starting index to search for the key
# @param end		- ending index to search for the key
# @returns a tuple consisting of:
#	- entry (data that follows the key)
#	- starting index of the entry line
#	- ending index of the entry line
# all values of the tuple will be -1 if the key was not found
def parseCDTEXTKey(cd_text, key, start=0, end=-1):
	if end < 0:
		end = len(cd_text)
	# retrieve the line that has the key
	key_index = cd_text.find(key,start,end)
	if key_index >= 0:
		key_end_index = cd_text.find(NEWLINE,key_index+len(key),end)
	
		# cutout the data from that key and strip the surrounding single
		# quotes
		entry = cd_text[key_index+len(key):key_end_index].strip().strip("\'")
	
		return (entry,key_index,key_end_index)
		
	return (-1,-1,-1) # if we didnt find the key
	
# function to parse a Track's tags from CD-TEXT
# @param cd_text		- cd-info's CD-TEXT output
# @param track_number	- the track number we are trying to find
# @param start			- starting index to search for the key
# @returns a tuple consisting of:
#	- track title
#		-- will be "TRACK #", where track_number is #, if TITLE not found
#	- track artist
#		-- will be "UNKNOWN" if PERFORMER not found
#	- starting index of the track data section
#	- ending index of the track data section
def parseCDTEXTTrack(cd_text, track_number, start=0):
	# retreive track begin and end index
	track_data_begin = parseCDTEXTKey(cd_text,CD_TEXT_NAME,start)
	track_data_end = parseCDTEXTKey(cd_text,CD_TEXT_NAME,track_data_begin[2])
	is_last_section = isEveryElementMinusOne(track_data_end)
	
	track_data_begin_index = track_data_begin[2]
	track_data_end_index = track_data_end[1]
	if is_last_section:
		track_data_end_index = len(cd_text)
	
	# retrieve track data
	track_title_data = parseCDTEXTKey(cd_text,CD_TEXT_TITLE,track_data_begin_index,track_data_end_index)
	track_artist_data = parseCDTEXTKey(cd_text,CD_TEXT_ARTIST,track_data_begin_index,track_data_end_index)
	
	# decide which datas are there or not
	track_title = ''
	track_artist = ''
	if isEveryElementMinusOne(track_title_data):
		track_title = CD_TEXT_TRK.format(track_number)
	else:
		track_title = track_title_data[0]
	if isEveryElementMinusOne(track_artist_data):
		track_artist = CD_TEXT_UNK
	else:
		track_artist = track_artist_data[0]
		
	return (track_title,track_artist,track_data_begin_index,track_data_end_index)
	
# function to parse Track tags from CD-TEXT
# @param cd_text	- cd-info's CD-TEXT output
# @param start		- starting index to search for Track information
# @returns tuple consisiting of:
#	- list of track titles
#		-- missing TRACK will be "TRACK #"
#	- list of track artists (performers)
#		-- missing PERFORMER will be "UNKNOWN"
#	- boolean where true means multiple artists, false means not
#		-- if all PERFORMER is "UNKNOWN", this will be False
# TODO
def parseCDTEXTTracks(cd_text, start=0):
	starting_point = start
	track_titles = list()
	track_artists = list()
	track_count = 1
	
	# continue parsing tracks until no more tracks left
	while starting_point < len(cd_text):
		track_found = parseCDTEXTTrack(cd_text, track_count, starting_point)
		track_titles.append(track_found[0])
		track_artists.append(track_found[1])
		starting_point = track_found[3]
		track_count += 1
		
	return (track_titles,track_artists,(not isEveryElementTheSame(track_artists)))

###	begin cd-info program flow	========================================

# The following code tests the parsing of cd-info ouptut

test_output = open('cd-info-sample-output','r')
test_output_text = test_output.read()
test_results = parseCDTEXTTracks(test_output_text,5190)
print(test_results)


""" # The following code actually does the cmd call

print('Getting tag data from disc...')
# call the cd-info cmd
cd_info_output_split = subprocess.run([CMD_CD_INFO,CMD_CD_INFO_FLAG_NO_DEV_INFO,CMD_CD_INFO_FLAG_NO_DISC_MODE], stdout=subprocess.PIPE, universal_newlines=True).stdout.partition(STDOUT_CD_INFO_CDDB_START)

if not cd_info_output_split[2]: # check if the CD Analysis report text shows in the output
	print(PARSE_OUTPUT_FAILED.format(CMD_CD_INFO))
	exit(1)
	
# split the string again into CDDB and CD-TEXT parts
cd_info_output_split_split = cd_info_output_split[2].partition('\n\n')
cddb_text = cd_info_output_split_split[0]
cd_text_text = cd_info_output_split_split[2]

# initalize cddb and cdtext tuples
cddb_list = None 
cd_text_list = None

## check for cddb and cdtext and parse if they are found:
if hascddb(cddb_text):
	cddb_list = parseCDDB(cddb_text)

if not cd_text_text:
	cd_text_list = parseCDTEXT(cd_text_text)
	
## display menu to allow user to select tags
song_tags = displayUserTagMenu(cddb_list,cd_text_list)
"""





