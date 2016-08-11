"""
@author Andre Allan Ponce

python script that checks for a cd in the drive, rips it, converts
the files to flac, writes the tags (if possible), and then deletes 
the temporary wav files.

Programs called:
	cd-info
	cdparanoia
	ffmpeg

This script will also check if those programs exist before executing 
"""


import os


test = os.getcwd()

current_items = os.scandir(test)

for item in current_items:
	print(item.name +" "+ str(item.stat().st_mode))

