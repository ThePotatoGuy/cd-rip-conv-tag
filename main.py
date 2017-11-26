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
import tempfile
from enum import IntEnum
from enum import Enum

### General constants   ================================================

EXITING = 'Exiting...'
EMAIL = 'andreponce@null.net'
PARSE_OUTPUT_FAILED = '{0:s} did not produce the required output. \
    \nPlease send an email to '+EMAIL+' with the version number of \
    this program and the name and version number of {0:s}.'
NEWLINE = '\n'
TEST_DIR = 'wav'
NUMBER_FORMAT = '{:02d}'
PAUSE_SCREEN = "<Press Enter to continue>"

### Formatting Constants    ============================================

# initalize user prompt formatting
HEADER_BAR = '----------------------------'
CLEAR_SCREEN = "\033[H\033[J"

##  program flow control constants  ====================================

SKIP_PROGRAM_TEST = False
SKIP_CD_INFO = False
SKIP_CD_PARA = False
SKIP_FFMPEG = False
SKIP_MOVE = False

########################################################################
### CLASSES ############################################################
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

    # the source these tags were retrieved from 
    tag_source = None

    # init
    def __init__(self, _tag_source):
        self.album_artist = "Unknown"
        self.album_title = "Untitled"
        self.number_of_tracks = 0
        self.track_artists = list()
        self.track_names = list()
        self.has_multiple_artists = False
        self.tag_source = _tag_source

    # converts this album to a string variant
    def __str__(self):
        outString = ""

        # album
        outString += (
            "Album title: " + self.album_title + "\n" +
            "Album artist: " + self.album_artist + "\n" +
            "Number of tracks: " + str(self.number_of_tracks) + "\n"
        )

        # tracks
        for track_number in range(0, self.number_of_tracks):
            outString += (
                "Track " + str(track_number+1) + ": " + 
                self.track_artists[track_number] + " - " +
                self.track_names[track_number] + "\n"
            )

        return outString


    # function to print the data stored in this class in a nice format
    def printData(self):
        # print album
        print(str(self))


    # function to clear data
    def clear(self):
        self.album_artist = "Unknown"
        self.album_title = "Untitled"
        self.number_of_tracks = 0
        self.track_artists = list()
        self.track_names = list()
        self.has_multiple_artists = False

# enum for menu options
class TagMainMenuOption(IntEnum):
    USE = 1
    SWITCH = 2
    CUSTOM = 3
    OPTION = 4
    QUIT = 0
    INVALID = -1

# enum for Tag display state
class TagDisplayState(Enum):
    CDDB = 1
    CDTEXT = 2
    CUSTOM = 3

########################################################################
### initial tests if program exists ####################################
########################################################################

### program names/commands  ============================================

CMD_CD_INFO = 'cd-info'
CMD_CDPARA = 'cdparanoia'
CMD_FFMPEG = 'ffmpeg'

CMD_VERSION = '--version'

CMDS = (CMD_CD_INFO, CMD_CDPARA, CMD_FFMPEG)

CMD_ERROR = 'ERROR: {:s} not found'

### program testing functions   ========================================
#*** program test MAIN
# function that checks if the required programs we need are installed
# in this system.
# EXIT NOTE: this function will exit the program if a required program 
#   is missing
def checkProgram():
    for cmd in CMDS:
        try:
            cmd_list = list()
            cmd_list.append(cmd)
            
            if cmd != CMD_FFMPEG: 
                # cd-info and cdparanoia need version flag
                cmd_list.append(CMD_VERSION)
                
            subprocess.run(
                cmd_list, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
                
        except FileNotFoundError:
            print(CMD_ERROR.format(cmd))
            print(EXITING)
            exit(1)

### begin program testing flow  ========================================

if SKIP_PROGRAM_TEST:
    print('Skipping required program check'+HEADER_BAR)
else:
    print('Checking if required programs exist...'+HEADER_BAR)
    checkProgram()
    
########################################################################
### pull tags if possible using cd-info ################################
########################################################################

### cd-info constants   ================================================

# cd-info specific flags
CMD_CD_INFO_FLAG_NO_DEV_INFO = '--no-device-info'
CMD_CD_INFO_FLAG_NO_DISC_MODE = '--no-disc-mode'

# cd-info keywords
STDOUT_CD_INFO_CDDB_START = 'CD Analysis Report'

# cd-info menu text
TAGS_FOUND = '\n{:s} tags found\n'
TAGS_NOT_FOUND = '\nNo {:s} tags found\n'
TAGS_REFUSE = "Okay, I won\'t use these tags"
NAME_CDDB = 'CDDB'
NAME_CD_TEXT = 'CD-TEXT'
NAME_CUSTOM = "CUSTOM"

# user tag menu
USER_TAG_MENU = (
    CLEAR_SCREEN + "\n" +
    HEADER_BAR + "\n" +
    "   {:s} Tags:\n" +
    HEADER_BAR + "\n\n" +
    "{:s}\n\n" + # album toString goes here
    "Menu options:\n" +
    "   1) - Use these tags\n" +
    "   2) - View {:s} tags\n" +
    "   3) - View/Edit custom tags\n" +
    "   4) - Apply album artist to track artists (CANNOT BE UNDONE)\n" +
    "\nQuit options:\n" +
    "   0) - Quit program"
)
CHOOSE_MENU_OPTION = "Choose menu option above: "
INVALID_MENU_OPTION = "'{:s}' is not a valid menu choice"
NO_EMPTY_TAGS = "Can't select empty tags"
CUSTOM_TAG_PROMPT = "<Press Enter to begin writing custom tags>"

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

### cd-info functions   ================================================


# functon that applies the given artist to all the track artists in 
# the given AlbumData object
def applyArtistToAll(artist, album):
    for track_number in range(0, album.number_of_tracks):
        album.track_artists[track_number] = artist


# function to clean text so its approripate for ffmpeg
# IN:
#   @param text - text to clean
#
# OUT:
#   @returns cleaned text
def cleanText(text):
    text = text.replace("/", "(slash)")
    text = text.replace("\\", "(backslash)")
    return text


# function to check if every element in the given list is a -1
# ASSUMES the given list has at least 1 element
# @param _list  - the list to check
# @return True if every element is -1, False if not
def isEveryElementMinusOne(_list):
    return isEveryElementThisElement(_list,-1)

# function to check if every element in the given list is the same
# ASSUMES the given list has at least 1 element
# @param _list  - the list to check
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
# @param _list  - the list to check
# @param item   - the item to check if _list is same
# @returns True if every element in _list is item, False if not
def isEveryElementThisElement(_list, item):
    if _list[0] == item:
        return isEveryElementTheSame(_list)
    return False

# function to prompt and ask them if they would like to use the 
# displayed tags.
# @returns:
#   0 when the user enters 'Y' or 'y' or any char other than 'N', 'n',
#       'q', 'Q'
#   1 when the user enters 'Q' or 'q'
#   -1 when the user enters 'N' or 'n'
# TODO make this a menu instead
def confirmUserTagSelection():
    user_answer = input('Do you want to use these tags? (Y/n/q/o): ')
    if user_answer.casefold() == 'n': # no
        return -1
    elif user_answer.casefold() == 'q': # quit
        return 1
    elif user_answer.casefold() == 'o': # special case for now
        return 2
    # else assume user accepts
    return 0
    
# function to prompt and ask user if they would like to continue to use
# program or quit 
# this is meant to happen in case no tags were selected
# @param allow_retry    - boolean, when true display and parse retry
#   option, otherwise do not display or parse retry option
# @returns:
#   0 when the user enters 'Y' or 'y'
#   1 when the user enters 'Q' or 'q' or any char other than 'Y', 'y',
#       'R', 'r'
#   -1 when the user enters 'R' or 'r'
#   2 when the user enters 'W' or 'w'
def confirmUserNoTagContinue(allow_retry):
    prompt = 'No tags were selected. {0:s}\nWould you like to continue \
        without applying tags{1:s},write your own tags, or quit? (y/{2:s}w/Q): '
    
    if allow_retry:
        prompt = prompt.format('Tags were found from '+CMD_CD_INFO+'.',
            ', retry selecting tags,','r/')
    else:
        prompt = prompt.format('','','')
        
    user_answer = input(prompt)
    if user_answer.casefold() == 'y': # continue
        return 0
    elif user_answer.casefold() == 'r': # retry
        return -1
    elif user_answer.casefold() == 'w': # write in tags
        return 2
    # else assume user quits
    return 1
    
# displays the premenu, notigyinf user what tags we found (if any)
# @param cddb_data - AlbumData retrieved from CDDB
# @param cd_text_data - AlbumData retrieved from CDTEXT
# @returns the TagDisplayState we should start in
def displayUserTagPreMenu(cddb_data, cd_text_data):
    # by default, start in CDDB state
    start_state = TagDisplayState.CDDB

    if cddb_data is None:
        print(TAGS_NOT_FOUND.format(NAME_CDDB))

        # if no cddb_data, then default to CDTEXT state
        start_state = TagDisplayState.CDTEXT
    else:
        print(TAGS_FOUND.format(NAME_CDDB))

    if cd_text_data is None:
        print(TAGS_NOT_FOUND.format(NAME_CD_TEXT))
    else:
        print(TAGS_FOUND.format(NAME_CD_TEXT))

    if cddb_data is None and cd_text_data is None:
        nothing = input(CUSTOM_TAG_PROMPT)

        # if no cddb or cdtext, default to custom tags
        start_state = TagDisplayState.CUSTOM
    else:
        nothing = input(PAUSE_SCREEN)

    return start_state

# displays user tag menu options and prompts user
# @param curr_tag_name - name of the tags we want to display
# @param curr_tags - Album of the current tags
# @param switch_tag_name - name of the tags we want the switch option to
#   display
# @returns:
#   a TagMainMenuOption enum
# TODO change the menu options into a dict, so we can pick and choose which
#   options to display
def displayUserTagMenuOptions(
        curr_tag_name,
        curr_tags,
        switch_tag_name):

    done = False
    while not done:
        print(USER_TAG_MENU.format(curr_tag_name, str(curr_tags), switch_tag_name))

        # get user input
        user_selection = input(CHOOSE_MENU_OPTION).strip()
        try:
            # retrieve enum of user choice
            user_choice = parseTagMainMenuOption(int(user_selection))

            # if the user choice was invalid, better say something
            if user_choice is TagMainMenuOption.INVALID:
                print(INVALID_MENU_OPTION.format(user_selection))
            else:
                # otherwise we are done, so just return out of here
                return user_choice

        except:
            print(INVALID_MENU_OPTION.format(user_selection))


# function to check if the given cddb text matched, which means we have
# tags.
# @param cddb_text  - cd-info's CDDB output
# @returns true if we have a cddb match, false otherwise
def hasCDDB(cddb_text):
    CDDB_start = parseCDDBKey(cddb_text, CMD_CD_INFO+":")
    # spliting the line by spaces helps us check the number of
    # matches. When the third token is a 0, then we have no
    # matches, otherwise we have at least 1
    #print(CDDB_start)
    tokens = CDDB_start[0].split()
    return tokens[1] != str(0)
    
#*** cd-info MAIN function 
# function that calls cd-info and parses the output
# EXIT NOTE: this function calls a function that may exit the program
# EXIT NOTE: this function will exit the program if cd-info's output 
#   produces unexpected results
# EXIT NOTE: this function will exit the program if user wishes to abort
#   program
# @param text)in    - string to parse instead of calling subprocess. 
# @returns an AlbumData class that consists of the tags generated,
#   or None if no tags were found or selected
def generateTags(text_in=None):
    cd_info_report = None
    if text_in is None:
        # call cd-info and retrieve output
        # splits the output along the CD Analysis report line
        cd_info_report = subprocess.run(
            [
                CMD_CD_INFO,
                CMD_CD_INFO_FLAG_NO_DEV_INFO,
                CMD_CD_INFO_FLAG_NO_DISC_MODE
            ],
            stdout=subprocess.PIPE, 
            universal_newlines=True
        ).stdout.partition(STDOUT_CD_INFO_CDDB_START)
    else: # use text_in as cd-info output
        cd_info_report = text_in.partition(STDOUT_CD_INFO_CDDB_START)
    
    # exit program if CD Analysis report is missing from text
    if not cd_info_report[2]:
        print(PARSE_OUTPUT_FAILED.format(CMD_CD_INFO))
        exit(1)
        
    # split the CD analysis report into CDDB and CD-TEXT
    cd_info_report_split = cd_info_report[2].partition('\n\n')
    cddb_text = cd_info_report_split[0]
    cd_text_text = cd_info_report_split[2]
    
    # initalize cddb and cdtext albumdata
    cddb_tags = None
    cd_text_tags = None
    
    # check for cddb and cdtext and parse if they are found
    if hasCDDB(cddb_text):
        cddb_tags = parseCDDB(cddb_text)
    if cd_text_text:
        #print(cd_text_text)
        cd_text_tags = parseCDTEXT(cd_text_text)
        
    tags_confirmed = False
    while not tags_confirmed:
        # display menu to prompt usr for tag selection
        selected_tags = runUserTagMenu(cddb_tags,cd_text_tags)
        
        # if no tags are selected and no tags were found, prompt user if
        # they would like to continue program or quit.
        # if no tags are selected and tags were found, prompt user if 
        # they would like to retry selecting tags, continue program, or 
        # quit
        # user_answer = None
        # if selected_tags is None:
        #    if cddb_tags is None and cd_text_tags is None:
        #        user_answer = confirmUserNoTagContinue(False)
        #    else:
        #        user_answer = confirmUserNoTagContinue(True)
       # 
       # if user_answer is not None and user_answer == 1: # user quits
       #     print(EXITING)
       #     exit(1)
       # elif user_answer is not None and user_answer == 2: 
       #     # user wants to manuall enter tags
       #     entered_tags = getEnteredTags()
       #     print("\nEntered Tags:")
       #     entered_tags.printData()
       #     use_tags = input("\nUse these tags (y/N): ")
       #     if use_tags.casefold() == 'y':
       #         return entered_tags
       #     else:
       #         entered_tags.clear()
#
#        elif user_answer is None or user_answer == 0: 
            # user selected tags or wishes to continue
        return selected_tags


# function that allows user to enter in tags
# @returns AlbumData class
# if user wishes to abort this, just ctrl+C
def getEnteredTags():

    #clear screen
    print(CLEAR_SCREEN)

    # an album
    album = AlbumData(NAME_CUSTOM)

    # first track count
    album.number_of_tracks = getTrackCount()

    # also album title
    album.album_title = getInput("Enter album title: ")

    # quickly ask user for album artist?
    print("Do not enter album artist if you have various artists\n")
    user_answer = getInput("Do we have an album artist (y/N): ")
    if user_answer.casefold() == 'y':
        album.has_multiple_artists = False
        album.album_artist = getInput("Enter album artist: ")
    else:
        album.has_multiple_artists = True

    for track in range(0,album.number_of_tracks):
        album.track_names.append(getInput("Enter track {:d} title: ".format(track+1)))
        if album.has_multiple_artists:
            album.track_artists.append(getInput("Enter track aritst: "))
        else:
            album.track_artists.append(album.album_artist)
    return album

# get track count
# @returns number of tracks
def getTrackCount():
    while True:
        track_count = getInput("How many tracks: ")
        if track_count.isdigit():
            return int(track_count)
        else:
            print("'" + track_count + "' is not a valid track count")


# function that gets an input string from the user
# @param prompt - the prompt to display to tuser
# @returns a string entered by user
# (NO VALDIATIOn)
def getInput(prompt):
    return input(prompt).strip()

# function to parse tags from CDDB
# @param cddb_text  - cd-info's CDDB output
# @returns an AlbumData built from the CDDB output
def parseCDDB(cddb_text):
    album = AlbumData(NAME_CDDB)
    
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
# @param cddb_text  - cd-info's CDDB output
# @param start      - the starting index to search for album artist
# @returns tuple consisting of:
#   - album artist
#   - starting index of the album artist line
#   - ending index of the album artist line
def parseCDDBAlbumArtist(cddb_text, start=0):
    return parseCDDBKey(cddb_text, CDDB_ALBUM_ARTIST, start)
    
# function to parse the album title from CDDB
# @param cddb_text  - cd-info's CDDB output
# @param start      - the starting index to search for album title
# @returns tuple consisting of:
#   - album title
#   - starting index of the album title line
#   - ending index of the album title line
def parseCDDBAlbumTitle(cddb_text, start=0):
    return parseCDDBKey(cddb_text, CDDB_ALBUM_TITLE, start)
    
# function to parse a key from the CDDB
# @param cddb_text  - cd-info's CDDB output
# @param key        - the choice of data to find
# @param start      - the starting index to search for album artist
# @returns tuple consisting of:
#   - entry
#   - starting index of the entry line
#   - ending index of the entry line
def parseCDDBKey(cddb_text, key, start=0):
    
    # retrieve the line that has the key
    key_index = cddb_text.find(key,start)
    key_end_index = cddb_text.find(NEWLINE,key_index+len(key))
    #print(str(key_index)+":"+str(key_end_index)+":"+str(len(key)))
    
    # cutout the data from that key and strip the surrounding single
    # quotes
    entry = cddb_text[
        key_index+len(key):key_end_index].strip().strip("\'")
    
    return (cleanText(entry),key_index,key_end_index)
    
# function to parse a track artist from CDDB
# @param cddb_text  - cd-infpo's CDDB output
# @param start      - the starting index to search for album title
# @returns tuple consisting of:
#   - track artist
#   - starting index of the track artist line
#   - ending index of the track artist line
def parseCDDBTrackArtist(cddb_text, start=0):
    return parseCDDBKey(cddb_text, CDDB_TRACK_ARTIST, start)
    
# function to parse the tracks from CDDB
# @param cddb_text  - cd-info's CDDB output
# @param start      - the starting index to search for tracks
# @returns tuple consisting of
#   - list of track names
#   - list of track artists
#   - boolean where true means multiple artists, false means one artist
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
        
    return (
        track_titles,
        track_artists, 
        (not isEveryElementTheSame(track_artists))
    )

# function to parse a track title from CDDB
# @param cddb_test  - cd-info's CDDB output
# @param start      - the starting index to search for track title
# @returns tuple consisting of:
#   - track title
#   - starting index of the track title line
#   - ending index of the track title line
def parseCDDBTrackTitle(cddb_text, start=0):
    return parseCDDBKey(cddb_text, CDDB_TRACK_TITLE, start)

# function to parse tags from CD-TEXT
# @param cd_text    - cd-info's CD-TEXT output
# @returns an AlbumData built from the CD-TEXT output
#
# CD-TEXT Rules:
#   - if the CD-TEXT for a track is missing its TITLE, "TRACK #" will 
#   be used for the track title.
#   - if the CD-TEXT for a track is missing its PERFORMER, the PERFORMER
#   text for Disc will be used for the track artist, or "UNKNOWN" if 
#   Disc does not have the PERFORMER attribute.
#   - if the CD-TEXT for Disc is missing TITLE, "UNTITLED" will be used
#   for the album title.
#   - if the CD-TEXT for Disc is missing PERFORMER, "UNKNOWN" will be
#   used for the album artist.
def parseCDTEXT(cd_text):
    album = AlbumData(NAME_CD_TEXT)
    
    # parsing album data
    disc_info = parseCDTEXTDisc(cd_text)
    album.album_title = disc_info[0]
    album.album_artist = disc_info[1]
#    print(disc_info[1])
    
    # parse track data
    track_info = parseCDTEXTTracks(cd_text,disc_info[3],disc_info[1])
    album.track_names = track_info[0]
    album.track_artists = track_info[1]
    album.has_multiple_artists = track_info[2]
    album.number_of_tracks = len(album.track_names)
   
    # if dont have album artist, but have complete artists for every track,
    # set album artist to that artist
    if album.album_artist == CD_TEXT_UNK and not album.has_multiple_artists:
        album.album_artist = album.track_artists[0]

    return album
    
# function to parse Disc tags from CD-TEXT
# @param cd_text    - cd-info's CD-TEXT output
# @param start      - starting index to search for Disc information
# @returns tuple consisting of:
#   - album title
#       -- will be "UNTITLED" if Disc is missing TITLE
#   - album artist (performer)
#       -- will be "UNKNOWN" if Disc is missing PERFORMER
#   - starting index of the disc data section
#   - ending index of the disc data section
def parseCDTEXTDisc(cd_text, start=0):
    # retrieve disc data begin and endind index
    disc_data_begin = parseCDTEXTKey(cd_text,CD_TEXT_DISC,start)
    disc_data_end = parseCDTEXTKey(
        cd_text,
        CD_TEXT_NAME,
        disc_data_begin[2]
    )
    disc_data_begin_index = disc_data_begin[2]
    disc_data_end_index = disc_data_end[1]
    
    # retrieve disc data
    disc_title_data = parseCDTEXTKey(
        cd_text,
        CD_TEXT_TITLE,
        disc_data_begin_index,
        disc_data_end_index
    )
    disc_artist_data = parseCDTEXTKey(
        cd_text,
        CD_TEXT_ARTIST,
        disc_data_begin_index,
        disc_data_end_index
    )
    
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
        
    return (
        disc_title,
        disc_artist,
        disc_data_begin_index,
        disc_data_end_index
    )
    
# function to parse a CD-TEXT key from cd-info's CD-TEXT output
# @param cd_text    - cd-info's CD-TEXT output
# @param key        - the key to search for
# @param start      - starting index to search for the key
# @param end        - ending index to search for the key
# @returns a tuple consisting of:
#   - entry (data that follows the key)
#   - starting index of the entry line
#   - ending index of the entry line
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
        entry = cd_text[
            key_index+len(key):key_end_index].strip().strip("\'")
    
        return (cleanText(entry),key_index,key_end_index)
        
    return (-1,-1,-1) # if we didnt find the key
    
# function to parse a Track's tags from CD-TEXT
# @param cd_text        - cd-info's CD-TEXT output
# @param track_number   - the track number we are trying to find
# @param start          - starting index to search for the key
# @param album_artist   - the album artist. only used if an album artist
#   exists, replaces UNKNOWN tags
# @returns a tuple consisting of:
#   - track title
#       -- will be "TRACK #", where track_number is #, if TITLE not 
#           found
#   - track artist
#       -- will be "UNKNOWN" if PERFORMER not found
#   - starting index of the track data section
#   - ending index of the track data section
def parseCDTEXTTrack(cd_text, track_number, start=0, album_artist=None):
    # retreive track begin and end index
    track_data_begin = parseCDTEXTKey(cd_text,CD_TEXT_NAME,start)
    track_data_end = parseCDTEXTKey(
        cd_text,
        CD_TEXT_NAME,
        track_data_begin[2]
    )
    is_last_section = isEveryElementMinusOne(track_data_end)
    
    track_data_begin_index = track_data_begin[2]
    track_data_end_index = track_data_end[1]
    if is_last_section:
        track_data_end_index = len(cd_text)
    
    # retrieve track data
    track_title_data = parseCDTEXTKey(
        cd_text,
        CD_TEXT_TITLE,
        track_data_begin_index,
        track_data_end_index
    )
    track_artist_data = parseCDTEXTKey(
        cd_text,
        CD_TEXT_ARTIST,
        track_data_begin_index,
        track_data_end_index
    )
#    print(track_artist_data)
    
    # decide which datas are there or not
    track_title = ''
    track_artist = ''
    if isEveryElementMinusOne(track_title_data):
        track_title = CD_TEXT_TRK.format(track_number)
    else:
        track_title = track_title_data[0]
    if isEveryElementMinusOne(track_artist_data):
        if album_artist is None:
            track_artist = CD_TEXT_UNK
        else:
            track_artist = album_artist
    else:
        track_artist = track_artist_data[0]
        
    return (
        track_title,
        track_artist,
        track_data_begin_index,
        track_data_end_index
    )
    
# function to parse Track tags from CD-TEXT
# @param cd_text    - cd-info's CD-TEXT output
# @param start      - starting index to search for Track information
# @param album_artist - the album artist to replace missing performers
# @returns tuple consisiting of:
#   - list of track titles
#       -- missing TRACK will be "TRACK #"
#   - list of track artists (performers)
#       -- missing PERFORMER will be "UNKNOWN"
#   - boolean where true means multiple artists, false means not
#       -- if all PERFORMER is "UNKNOWN", this will be False
def parseCDTEXTTracks(cd_text, start=0, album_artist=None):
    starting_point = start
    track_titles = list()
    track_artists = list()
    track_count = 1
    
    # continue parsing tracks until no more tracks left
    while starting_point < len(cd_text):
        track_found = parseCDTEXTTrack(
            cd_text,
            track_count,
            starting_point,
            album_artist
        )
        track_titles.append(track_found[0])
        track_artists.append(track_found[1])
        starting_point = track_found[3]
        track_count += 1
        
    return (
        track_titles,
        track_artists,
        (not isEveryElementTheSame(track_artists))
    )

# parsese the given TagMainMenuoption into an appropriate enum
# assumes the given option is an int
# @param choice - the choice we are checking
# @returns the TagMainMenuOption enum that is appropriate
def parseTagMainMenuOption(choice):
    try:
        # if the value is an appropriate enum, this will be successful
        return TagMainMenuOption(choice)
    except:
        # otherwise just return the invalid choice
        return TagMainMenuOption.INVALID

# function to display a tag selection/vewing menu to the user
# EXIT NOTE: this function will exit the program if the user selects the
#   quit option
# @param cddb_data      - athe AlbumData class generated from parsing
#   CDDB output
# @param cd_text_data   - the AlbumData class generated from parsing
#   CD-TEXT output
# @returns the selected AlbumData class or None if none were selected
def runUserTagMenu(cddb_data, cd_text_data):

    done = False
    selected_tags = None
    prev_state = None
    custom_tags = None

    state = displayUserTagPreMenu(cddb_data, cd_text_data)

    # assume we have at least one tag to display at this point
    while not done:

        # display tag menu differntly based on state
        if state is TagDisplayState.CDDB:
            selected_tags = cddb_data
            user_choice = (
                displayUserTagMenuOptions(NAME_CDDB, selected_tags, 
                    NAME_CD_TEXT)
            )
        elif state is TagDisplayState.CDTEXT:
            selected_tags = cd_text_data
            user_choice = (
                displayUserTagMenuOptions(NAME_CD_TEXT, selected_tags,
                    NAME_CDDB)
            )
        elif state is TagDisplayState.CUSTOM:
            # TODO custom menu gets more options 
            custom_tags = getEnteredTags()

            selected_tags = custom_tags

            # special logic to handle custom tags
            if prev_state is TagDisplayState.CDTEXT:
                prev_name = NAME_CD_TEXT
            else:
                prev_name = NAME_CDDB
                prev_state = TagDisplayState.CDDB
            user_choice = (
                displayUserTagMenuOptions(NAME_CUSTOM, selected_tags,
                    prev_name)
            )

        # now handle user choices
        if user_choice is TagMainMenuOption.USE:
            if selected_tags is None:
                print(NO_EMPTY_TAGS)
                nothing = input(PAUSE_SCREEN)
            else:
                return selected_tags

        elif user_choice is TagMainMenuOption.SWITCH:
            cust_state = prev_state
            prev_state = state
            if state is TagDisplayState.CDDB:
                state = TagDisplayState.CDTEXT
            elif state is TagDisplayState.CDTEXT:
                state = TagDisplayState.CDDB
            else:
                state = cust_state

        elif user_choice is TagMainMenuOption.CUSTOM:
            prev_state = state
            state = TagDisplayState.CUSTOM
        elif user_choice is TagMainMenuOption.OPTION:
            if selected_tags is not None:
                applyArtistToAll(selected_tags.album_artist, selected_tags)
        elif user_choice is TagMainMenuOption.QUIT:
            done = True
            print(EXITING)
            exit(0)



### begin cd-info program flow  ========================================

# The following code uses a test file instead of actual progarm use
# this will be commented at some point
#test_output = open('cd-info-sample-output','r')
#test_output_text = test_output.read()

tags = None
if SKIP_CD_INFO:
    print('Skipping retrieving tags from '+CMD_CD_INFO)
else:
    print('Reading tags from disc...')
    tags = generateTags()

########################################################################
### rip tracks using cdparanoia and convert/write tags using ffmpeg ####
########################################################################
# we are usinga  context manager to create and use a temporary directory
# as a result, we need to combine cdparanoia and ffmpeg functions in the
# same place so the cnotext manager can encompass both processes.

### cdparanoia/ffmpeg constants ========================================

# cdparanoia specific flags
CMD_CDPARA_FLAG_BATCH = '-B'
CMD_CDPARA_FLAG_SELECT_ALL = '--'

# ffmpeg specific flags
CMD_FFMPEG_FLAG_INPUT = '-i'
CMD_FFMPEG_FLAG_METADATA = '-metadata'
CMD_FFMPEG_FLAG_TITLE = 'title='
CMD_FFMPEG_FLAG_ARTIST = 'artist='
CMD_FFMPEG_FLAG_ALBUM = 'album='
CMD_FFMPEG_FLAG_TRACK = "track="
CMD_FFMPEG_FLAG_AUDIO_STREAM = '-c:a'
CMD_FFMPEG_FLAG_FLAC_AUDIO = 'flac'
EXT_FLAC = '.flac'

# ffmpeg errors
FFMPEG_TRACK_COUNT_ERROR = 'ERROR: Number of tracks found on disc do \
not match number of tracks ripped from disc'

# additional cmds
CMD_MV = 'mv'
CMD_MV_FLAC_WILD = '*.flac'

FFMPEG_PROMPT_TRACK_SKIP = 'Would you like to apply tags anyway? (The extra \
tags will be ignored) (y/N)'

### cdparanoia/ffmpeg functions ========================================

# function to prompt user and ask them if they would like to apply tags even
# if a track count error was found.
# @returns:
#   0 if the user enters 'y' or 'Y'
#   1 if the user enters 'n' or 'N' (or any other character)
def confirmUserTrackSkip():
    user_answer = input(FFMPEG_PROMPT_TRACK_SKIP)
    if user_answer.casefold() == 'y':   # yes
        return 0
    # else assume user does not accept
    return 1

#*** ffmpeg MAIN function
# function that calls ffmpeg to convert wav files into flacs and write
# their tags
# EXIT NOTE: this function will exit if the tracks found in directory
#   do not match the number of tracks read from disc
# @param tags       - AlbumData class that holds the tags we will write
# @param wav_dir    - the directory of wav files to convert
def convertTracks(tags, wav_dir=TEST_DIR):
    
    # we are assuming that for each track in AlbumData, there is a
    # corresponding wav file. We also assume os.listdir() will show us
    # tracks alphabetically
    # also its easier to send ffmpeg to files in a folder than send
    # its output to a different folder other than current working direct
    wav_tracks = sorted(os.listdir(wav_dir))
    
    """
    for index in range(0,tags.number_of_tracks):
        artist = tags.album_artist
        if tags.has_multiple_artists:
            artist = (tags.track_artists)[index]
        print(' '.join([CMD_FFMPEG_FLAG_AUDIO_STREAM,CMD_FFMPEG_FLAG_FLAC_AUDIO,CMD_FFMPEG_FLAG_METADATA,CMD_FFMPEG_FLAG_TITLE+(tags.track_names)[index]+CMD_FFMPEG_FLAG_ENDQUOTE,CMD_FFMPEG_FLAG_METADATA,CMD_FFMPEG_FLAG_ARTIST+artist+CMD_FFMPEG_FLAG_ENDQUOTE,CMD_FFMPEG_FLAG_METADATA,CMD_FFMPEG_FLAG_ALBUM+tags.album_title+CMD_FFMPEG_FLAG_ENDQUOTE,CMD_FFMPEG_FLAG_ENDQUOTE+NUMBER_FORMAT.format(index+1)+'_'+artist+" - "+(tags.track_names)[index]+EXT_FLAC+CMD_FFMPEG_FLAG_ENDQUOTE]))
    """

    # quit if numbers of tracks do not match up
    if tags.number_of_tracks != len(wav_tracks):
        print(FFMPEG_TRACK_COUNT_ERROR)
        if confirmUserTrackSkip() != 0:
            print(EXITING)
            exit(1)
        else:
            print('Ignoring extra tags...')
    
    index = 0
    for wav_track in wav_tracks:
        artist = (tags.track_artists)[index]
            
        # this command does an ffmpeg convert and tag write
        # it looks like:
        # ffmpeg -i <input file> -metadata title="Title" -metadata 
        #   artist="Artist" -metadata album="Album" 
        #   -metadata track=## -c:a flac <output>
        subprocess.run(
            [
                CMD_FFMPEG,
                CMD_FFMPEG_FLAG_INPUT,
                wav_dir+'/'+wav_track,
                CMD_FFMPEG_FLAG_METADATA,
                CMD_FFMPEG_FLAG_TITLE+(tags.track_names)[index],
                CMD_FFMPEG_FLAG_METADATA,
                CMD_FFMPEG_FLAG_ARTIST+artist,
                CMD_FFMPEG_FLAG_METADATA,
                CMD_FFMPEG_FLAG_ALBUM+tags.album_title,
                CMD_FFMPEG_FLAG_METADATA,
                CMD_FFMPEG_FLAG_TRACK+str(index+1),
                CMD_FFMPEG_FLAG_AUDIO_STREAM,
                CMD_FFMPEG_FLAG_FLAC_AUDIO,
                NUMBER_FORMAT.format(index+1)+'_'+artist+" - "+ \
                (tags.track_names)[index]+EXT_FLAC
            ]
        )
        
        index += 1
        
# function to move the flac files in the current directory into a folder
# so it has the format:
# <artist> - <album>
# @param tags   - the AlbumData that represents this album
def moveFlacsToFolder(tags):
    dir_name = tags.album_artist+' - '+tags.album_title
    os.mkdir(dir_name)
    subprocess.run(
        CMD_MV+' '+CMD_MV_FLAC_WILD+' "'+dir_name+'"', 
        shell=True
    )

#*** cdparanoia MAIN function:
# function that calls cdparanoia and rips tracks.
# @param wav_dir    - the directory to store the ripped tracks
def ripTracks(wav_dir=TEST_DIR):
    # change dir and begni ripping
    os.chdir(wav_dir)
    subprocess.run(
        [
            CMD_CDPARA,
            CMD_CDPARA_FLAG_BATCH,
            CMD_CDPARA_FLAG_SELECT_ALL
        ]
    )
    os.chdir('..')

### cdparanoia/ffmpeg flow  ============================================
# since we are usinga context manager to handle our temp dir, this
# context continues into flac conversion and tag writing.
# TODO
with tempfile.TemporaryDirectory(dir='.') as wav_dir:
    if SKIP_CD_PARA:
        print('Skipping ripping tracks'+HEADER_BAR)
    else:
        print('Ripping tracks from disc...'+HEADER_BAR)
        ripTracks(wav_dir)
        
    if SKIP_FFMPEG:
        print('Skipping converting tracks')
    else:
        print('Converting tracks to flac...'+HEADER_BAR)
        convertTracks(tags,wav_dir)
    moveFlacsToFolder(tags)
        
