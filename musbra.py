
import musicbrainzngs

from album import AlbumData

APP = "cd-rip-conv-tag"
VER = "0.1.0"
EMAIL = "potato@desu.zone"

# set user agent string
musicbrainzngs.set_useragent(APP, VER, EMAIL)


def disc_id_to_Album(disc_id: str) -> AlbumData:
    """
    Takes a disc id and creates an AlbumData from it
    :param disc_id: disc ID string
    :return: AlbumData object, may be None if failures occured
    """
    data = musicbrainzngs.get_releases_by_discid(disc_id)
    # TODO
    print(repr(data))

