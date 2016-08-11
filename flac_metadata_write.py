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

import io
import os
import subprocess

###	General constants	================================================

EXITING = 'Exiting...'

###	program names/commands	============================================

CMD_CD_INFO = 'cd-info'
CMD_CDPARA = 'cdparanoia'
CMD_FFMPEG = 'ffmpeg'

CMD_VERSION = '--version'

CMDS = (CMD_CD_INFO, CMD_CDPARA, CMD_FFMPEG)

CMD_ERROR = 'ERROR: {:s} not found'

###	initial test if program exists	====================================
print('Checking if required programs exist...')

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
	
###	pull cd-text if possible using cd-info	============================
print('Getting tag data from disc...')

# cd-info specific flags
CMD_CD_INFO_FLAG_NO_DEV_INFO = '--no-device-info'
CMD_CD_INFO_FLAG_NO_DISC_MODE = '--no-disc-mode'

# cd-info keywords
STDOUT_CD_INFO_CDDB_START = 'CD Analysis Report'

# call the cd-info cmd
cd_info_output_split = subprocess.run([CMD_CD_INFO,CMD_CD_INFO_FLAG_NO_DEV_INFO,CMD_CD_INFO_FLAG_NO_DISC_MODE], stdout=subprocess.PIPE, universal_newlines=True).stdout.partition(STDOUT_CD_INFO_CDDB_START)

if not cd_info_output_split[2]:
	print('
print(cd_info_output_split[2])





