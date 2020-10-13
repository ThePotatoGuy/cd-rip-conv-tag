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

