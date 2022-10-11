import re

from typing import List, Tuple, Optional, Match

from enum import IntEnum
from enum import Enum

import discid

def clean_str(text):
    return text.replace("/", "(slash)").replace("<", "(lthan)").replace(
            ">", "(gthan)").replace(":", "(colon)").replace(
            '"', "(dubquote)").replace("\\", "(bslash)").replace(
            "|", "(pipe)").replace("?", "(qmark)").replace(
            "*", "(asterisk)")

########################################################################
### CLASSES ############################################################
########################################################################


class DiscData(object):
    """
    Contains disc data loaded from cd-info
    """
    #first: int
    #last: int
    #lsns: List[int]
    #sectors: int

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

    @staticmethod
    def from_cd_info(cd_info: str) -> Tuple[Optional["DiscData"], int]:
        """
        Generates a disc data object from cd info string
        :param cd_info: cd-info string
        :return: tuple of the following format:
            [0] - DiscData object, or None if failures
            [1] - index where we stopped parsing string data.
        """
        data = DiscData()
        start_match = data.parse_track_list(cd_info)
        if start_match is None:
            return None, 0

        endex = data.parse_tracks(cd_info, start_pos=start_match.end())
        if endex is None:
            return None, start_match.end()

        return data, endex

    def parse_track_list(self, data: str) -> Optional[Match]:
        """
        Attempts to find, then parses track data if we find it.
        :param data: string to search for track list data
        :return: the match object. If this boolean value is True, then the match was found, otherwise no match found
        """
        match = self.TRACK_LIST_RX.search(data)
        if not match:
            return None

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

    def to_discid(self) -> str:
        """
        Converts this track data into a disc id for musicbrainz
        :return: discid
        """
        return discid.read().id
        # NOTE: the below seems to create incorrect disc ids
#        return discid.put(
#            self.first,
#            self.last,
#            self.sectors + self.OFFSET,
#            [x + self.OFFSET for x in self.lsns]
#        )


## struct style object to hold album data
class AlbumData:
    def_album_artist = "Unknown"
    def_album_title = "Untitled"

    # album data
    #album_artist: str
    #album_title: str
    #number_of_tracks: int
    
    # track data
    #track_names: list
    #track_artists: list # only used if has_multiple_artists is true
    
    # boolean to say if this album has multiple artists or not
    # (i.e: different tracks have different artists (various artists)
    #has_multiple_artists: bool

    # the source these tags were retrieved from 
    #tag_source: str

    # discid
    #disc_id: str

    # init
    def __init__(self, _tag_source):
        self.album_artist = self.def_album_artist
        self.album_title = self.def_album_title
        self.number_of_tracks = 0
        self.track_artists = list()
        self.track_names = list()
        self.has_multiple_artists = False
        self.tag_source = _tag_source
        self.disc_id = ""

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

    def add_track(self, track_name: str, track_artist: str):
        """
        Adds a track to the track data list.
        :param track_name: track name to add
        :param track_artist: track artist to add. If empty, then we add album artist.
        """
        self.track_names.append(track_name)

        if len(track_artist) < 1:
            track_artist = self.album_artist
        self.track_artists.append(track_artist)

    def clean(self):
        """
        Cleans all tags so they are safe for file names.
        """
        self.album_artist = clean_str(self.album_artist)
        self.album_title = clean_str(self.album_title)
        for idx, artist in enumerate(self.track_artists):
            self.track_artists[idx] = clean_str(artist)
        for idx, name in enumerate(self.track_names):
            self.track_names[idx] = clean_str(name)

    # function to print the data stored in this class in a nice format
    def printData(self):
        # print album
        print(str(self))

    def check_multiple(self):
        """
        Checks for multiple artists
        """
        if len(self.track_artists) > 0:
            c_artist = self.track_artists[0]
            for artist in self.track_artists:
                if artist != c_artist:
                    self.has_multiple_artists = True
                    return

        self.has_multiple_artists = False

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

