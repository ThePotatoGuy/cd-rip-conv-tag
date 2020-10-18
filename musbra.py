
from typing import Optional

import musicbrainzngs

from album import AlbumData


NAME_CDDB = 'CDDB'

APP = "cd-rip-conv-tag"
VER = "0.1.0"
EMAIL = "potato@desu.zone"

# set user agent string
musicbrainzngs.set_useragent(APP, VER, EMAIL)


def _disc_id_out(disc_id: str) -> dict:
    """
    grabs all data we need from disc id. This is for debugging purposes
    :param disc_id: disc id
    :return: data in dict
    """
    return musicbrainzngs.get_releases_by_discid(disc_id, includes=["artists"])


def disc_id_to_Album(disc_id: str) -> Optional[AlbumData]:
    """
    Takes a disc id and creates an AlbumData from it.
    NOTE: we pull the first available release.
    :param disc_id: disc ID string
    :return: AlbumData object, may be None if failures occured
    """
    releases = musicbrainzngs.get_releases_by_discid(
        disc_id,
        includes=["artists", "recordings", "artist-credits"]
    ).get(
        "disc", {}
    ).get(
        "release-list", []
    )

    if len(releases) < 1:
        return None

    data = release_to_Album(releases[0])
    if data is not None:
        data.disc_id = disc_id

    return data


def parse_artist_data(rel_data: dict) -> str:
    """
    Parses release data into the artist string
    :param rel_data: release data
    :return: string. Will be default for album data if not found
    """
    artist_data = rel_data.get("artist-credit", [])
    if len(artist_data) < 1:
        return AlbumData.def_album_artist

    return artist_data[0].get(
        "artist", {}
    ).get(
        "name", AlbumData.def_album_artist
    )


def parse_track_artist(track_data: dict) -> str:
    """
    Parses track data into a track artist
    :param track_data: track data
    :return: track artist. will be empty if problems
    """
    artist_data = track_data.get("artist-credit", [])
    if len(artist_data) < 1:
        return ""

    return artist_data[0].get(
        "artist", {}
    ).get(
        "name", ""
    )


def parse_track_list(rel_data: dict) -> list:
    """
    Parses release data into track list
    :param rel_data: release data
    :return: track list as list. May be empty if problems.
    """
    medium_data = rel_data.get("medium-list")
    if medium_data is None or len(medium_data) < 1:
        return []

    return medium_data[0].get("track-list", [])


def parse_track_name(track_data: dict) -> str:
    """
    Parses track data into a track name
    :param track_data: track data
    :return: track naem as string. will be default for album data if not found
    """
    return track_data.get("recording", {}).get("title", AlbumData.def_album_title)


def release_to_Album(rel_data: dict) -> Optional[AlbumData]:
    """
    Converts releaes data to an album
    :param rel_data: release data (dict)
    :return: AlbumData object, or None if failures occured
    """
    data = AlbumData(NAME_CDDB)
    data.album_title = rel_data.get("title", AlbumData.def_album_title)
    data.album_artist = parse_artist_data(rel_data)

    # get tracks
    track_data = parse_track_list(rel_data)
    if len(track_data) < 1:
        return None

    data.number_of_tracks = len(track_data)
    for track in track_data:
        data.add_track(parse_track_name(track), parse_track_artist(track))

    data.check_multiple()

    return data
