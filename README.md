python script that checks for a cd in the drive, rips it, converts the files to flac, writes the tags (if possible), and then deletes the temporary wav files.

Programs called:
*	cd-info
*	cdparanoia
*	ffmpeg

This script will also check if those programs exist before executing. 

This is only tested in a Linux environment (Arch Linux)
