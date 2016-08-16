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

# CD-TEXT specific constants

###	cd-info functions	================================================

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
def displayUserTagMenu(cddb_list, cd_text_list):
	print('nothing here yet')

# function to check if the given cddb text matched, which means we have
# tags.
# @param cddb_text	- cd-info's CDDB output
# @returns true if we have a cddb match, false otherwise
# TODO change this to use parseCDDBKey
def hasCDDB(cddb_text):
	cddb_text_as_lines = cddb_text.splitlines()
	
	for line in cddb_text_as_lines:
		if CMD_CD_INFO+':' in line:
			# spliting the line by spaces helps us check the number of
			# matches. When the third token is a 0, then we have no
			# matches, otherwise we have at least 1
			tokens = line.split()
			return tokens[2] != str(0)
				
	return False

# function to parse tags from CDDB
# @param cddb_text	- cd-info's CDDB output
# @returns list of tuples where the first tuple is (album_name, artist)
# 	and all following tuples consist of (track_name, artist)
def parseCDDB(cddb_text):
	print('nothing here yet')
	
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
	
# function to parse the tracks from CDDB
# @param cddb_text	- cd-info's CDDB output
# @param start		- the starting index to search for tracks
# @returns tuple consisting of
#	- list of track names
#	- list of track artists
#	- boolean where true means multiple artists, false means one artist
def parseCDDBTracks(cddb_text, start=0):
	print('nothing here yet')

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
def parseCDTEXT(cd_text):
	print('nothing here yet')
	
# function to print the tuple data returned from the above parsing
# methods
# @param tag_tups	- the tuple data returned from the above parse 
# methods
def printTagTuples(tag_tups):
	print('nothing here yet')

###	begin cd-info program flow	========================================

# The following code tests the parsing of cd-info ouptut

test_output = open('cd-info-sample-output','r')
test_output_text = test_output.read()

test_results = parseCDDBAlbumArtist(test_output_text)
test_results_2 = parseCDDBAlbumTitle(test_output_text)

print(test_results)
print(test_results_2)


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





