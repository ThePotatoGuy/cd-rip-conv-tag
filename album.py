import re

from typing import List, Tuple, Optional

from enum import IntEnum
from enum import Enum

import discid

########################################################################
### CLASSES ############################################################
########################################################################


class DiscData(object):
    """
    Contains disc data loaded from cd-info
    """
    first: int
    last: int
    lsns: List[int]
    sectors: int

    OFFSET = 150

    TRACK_LIST_RX = re.compile(".+Track List \((\d+) - (\d+)\)\n")
    TRACK_RX = re.compile("\s*\d+:\s*\d\d:\d\d:\d\d\s*(\d+).+\n")
    TRACK_LEADOUT = re.compile("\s*\d+:\s*\d\d:\d\d:\d\d\s*(\d+)\s*leadout.*\n")

    def __init__(self):
        self.first = -1
        self.last = -1
        self.lsns = []
        self.sectors = -1

    def __len__(self):
        return self.last - self.first + 1

    def parse_track_list(self, data: str) -> Optional[re.Match]:
        """
        Attempts to find, then parses track data if we find it.
        :param data: string to search for track list data
        :return: the match object. If this boolean value is True, then the match was found, otherwise no match found
        """
        match = self.TRACK_LIST_RX.search(data)
        if not match:
            return match

        # match found
        first, last = match.groups()

        # parse to ints
        try:
            self.first = int(first)
            self.last = int(last)
            return match

        except:
            return None

    def parse_tracks(self, data: str, start_pos=0) -> Optional[int]:
        """
        Parses track data. Assumes parse_track_list has already been called
        :param data: string to search for track data
        :param start_pos: starting index to begin search
        :return: ending index of data (match.end()), or NOne if match fails somewhere
        """
        if self.last < 1:
            return None

        last_dex = start_pos
        for idx in range(self.first, self.last+1):
            match = self.TRACK_RX.search(data, last_dex)
            if match:
                lsn = match.groups()[0]
                try:
                    self.lsns.append(int(lsn))
                except:
                    return None

                last_dex = match.end()

        if len(self.lsns) > 0:
            # finally do the leadout check
            match = self.TRACK_LEADOUT.search(data, last_dex)
            if match:
                try:
                    self.sectors = int(match.groups()[0])
                    return match.end()
                except:
                    return None

        return None


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

