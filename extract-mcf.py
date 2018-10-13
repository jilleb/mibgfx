#----------------------------------------------------------
#--- Quick 'n' dirty MCF file extractor
#
# File:        extract-mcf.py
# Author:      Jille, sVn
# Revision:    4
# Purpose:     Discover Pro MIB2 mcf file exporter
# Comments:    Usage: extract-mcf.py
# Credits:     Partially based on code supplied by booto @ 
# 			   https://goo.gl/GqSfpt
#----------------------------------------------------------

import struct
import sys
import os
import zlib
from PIL import Image
from progressbar import ProgressBar, Percentage, Bar

current_folder = os.path.dirname(os.path.realpath(__file__))
print                                                                                                 
print" __  __  _____ ______   ________   _________ _____            _____ _______ ____  _____   "
print"|  \/  |/ ____|  ____| |  ____\ \ / /__   __|  __ \     /\   / ____|__   __/ __ \|  __ \  "
print"| \  / | |    | |__    | |__   \ V /   | |  | |__) |   /  \ | |       | | | |  | | |__) | "
print"| |\/| | |    |  __|   |  __|   > <    | |  |  _  /   / /\ \| |       | | | |  | |  _  /  "
print"| |  | | |____| |      | |____ / . \   | |  | | \ \  / ____ \ |____   | | | |__| | | \ \  "
print"|_|  |_|\_____|_|      |______/_/ \_\  |_|  |_|  \_\/_/    \_\_____|  |_|  \____/|_|  \_\ "
print"                                                                                          "
                                                                                                
resources_location = raw_input("Path of Resources folder(no entry = current folder): ")
if (resources_location == ""):
	resources_location = current_folder
elif not os.path.exists(resources_location):
	print "Folder does not exist."
	sys.exit(1)

print "Resources root folder is: " + resources_location
print 

def list_files(startpath):
	for root, dirs, files in os.walk(startpath):
		level = root.replace(startpath, '').count(os.sep)
		indent = '_' * 4 * (level)
		print('{}{}/'.format(indent, os.path.basename(root)))
		subindent = ' ' * 4 * (level + 1)
		#for f in files:
		#	print('{}{}'.format(subindent, f))

skin_selection = raw_input("Which skin folder (0-5)?: ") 

parse_idmap = "n"

# todo: make this nicer
if (skin_selection == "0"):
	mcf_path = resources_location + "\\skin0\\"
	parse_idmap = raw_input ("Parse imageidmap.res and move files to folders? (y/n): ") 
elif (skin_selection == "1"):
	mcf_path = resources_location + "\\skin1\\"
elif (skin_selection == "2"):
	mcf_path = resources_location + "\\skin2\\"
elif (skin_selection == "3"):
	mcf_path = resources_location + "\\skin3\\"
elif (skin_selection == "4"):
	mcf_path = resources_location + "\\skin4\\"
elif (skin_selection == "5"):
	mcf_path = resources_location + "\\skin5\\"
else:
	print "Wrong selection."
	sys.exit(1)

if not os.path.exists(mcf_path):
	print "Folder does not exist."
	sys.exit(1)

print	
print "Unpacking: " + mcf_path

out_dir = mcf_path + "extracted\\"
if not os.path.exists(out_dir):
  os.mkdir(out_dir)
  
out_dir = out_dir + "unsorted\\"
if not os.path.exists(out_dir):
  os.mkdir(out_dir)
  
if (parse_idmap == "y"):
	idMap_path = mcf_path + "imageidmap.res"
	idMapFile = open(idMap_path, "rb")
	seek = idMapFile.seek
	read = idMapFile.read

	# read header
	seek(12)
	data = read(4)
	#print 'Header: ' + data
	if (data != "Skr0"):
		print 'Error: not an imageidmap.res file'

	#read the UID
	seek(16)
	data = read(4)
	(UID,) = struct.unpack('<I', data) 
	print 'UID: ' + str(UID)

	#read the number of IDs
	seek(24)
	data = read(4)
	(num_mifIDs,) = struct.unpack('<I', data)
	print 'Number of IDs: ' + str(num_mifIDs)

	# start of TOC
	seek(32)

	#start loop
	i = 0
	id_array = []

	while (i < num_mifIDs):
		data = read(4)
		(path_len,) =  struct.unpack('<I', data)
		#the lenght of the path is in number of characters, but since it's utf binary data, x2
		path_len = (path_len*2)
		#read the path, for as long as the lenght of this string
		path = read(path_len).decode('utf-16')
		id_array.append(path.replace("/", "\\"))
		seek (4,1)
		i = i + 1

	data = read(4)
	(num_mifIDs2,) = struct.unpack('<I', data)
	#print 'Number of IDs: ' + str(num_mifIDs2)

	if (num_mifIDs2 != num_mifIDs):
		print 'Warning, the table is probably corrupt, expected:' + num_mifIDs
		
	j = 0
	
	sorted_dir = mcf_path + "extracted\\sorted\\"

	batchfile = open(mcf_path+"extracted\\move_files.bat","w") 
	batchfile.write("@echo off \n")
	batchfile2 = open(mcf_path+"extracted\\sorted_to_unsorted.bat","w") 
	batchfile2.write("@echo off \n")
	print "Writing batchfile to " + mcf_path + "extracted\\"
	while (j < num_mifIDs2):
		data = read(4)
		(mifID,) =  struct.unpack_from('<I', data,0)
	#	print str(mifID) + id_array[j]
		file_id = mifID -1
		batchfile.write ("echo f | xcopy /f /y .\\skin0\\extracted\\unsorted\\img_" + str(file_id) + ".png" + " .\\skin0\\extracted\\sorted\\" + id_array[j] + " >nul \n")
		batchfile2.write ("echo f | xcopy /f /y .\\sorted\\" + id_array[j] + " .\\unsorted\\img_" + str(file_id) + ".png \n" )

		j = j+1
	batchfile.close()
	batchfile2.close()
	
mcf_file = mcf_path + "images.mcf"		
data = open(mcf_file,'rb').read()
offset = 0
counterRGBA = 0
counterL = 0
counterLA = 0


(magic,) = struct.unpack_from('<4s', data, offset) # '<4s'  =  '<' little-endian, 's' is type char, '6s' Array of 6 chars; get first entry of the returned tuple
if magic != '\x89\x4d\x43\x46': # corresponds to MCF file starting
	print 'Incorrect MCF file!'
	sys.exit(1)
	
offset = 32
(size_of_TOC,) = struct.unpack_from('<I', data, offset) 
#print 'Size of TOC: ' + str(size_of_TOC)

data_start = size_of_TOC + 52
#print ("Data start: %d"%(data_start))

offset = 48
(num_files,) = struct.unpack_from('<I', data, offset)
print ("Number of files: %d"%(num_files))

#TOC
offset = 52
for image_id in range (0, int(num_files)):
	(file_type, file_id, file_offset, file_size) = struct.unpack_from('<4sIII', data, offset) # file_size = meta information (size of 40) + zsize
	#print ("filetype %s file_id %d offset %d size %d"%(file_type, file_id, file_offset, file_size)) 
	offset = offset + 16

offset = data_start

pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=num_files).start()
  
#print ("type; file_id; always_8; zsize; max_pixel_count; always_1; unknown_hash; width; height; image_mode; always__1")
for image_id in range(0, int(num_files)):
	(unknown_hash1, type, file_id, always_8, zsize, max_pixel_count, always_1, unknown_hash2, width, height, image_mode, always__1) = struct.unpack_from('<I4sIIIIIIhhhh', data, offset)
	#max_pixel_count = width * height and mulitplied by 1 on L-Mode and mulitplied by 4 on RGBA-Mode
	
	#print ("%d;%s;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d"%(unknown_hash1, type, file_id, always_8, zsize, max_pixel_count, always_1, unknown_hash2, width, height, image_mode, always__1))
	
	zlib_data_offset = offset+40
	zlib_image = data[zlib_data_offset:zlib_data_offset+zsize]
	zlib_decompress = zlib.decompress(zlib_image)

	try:
		if (image_mode == 4096):
			im = Image.frombuffer('L', (width, height), zlib_decompress, 'raw', 'L', 0, 1)
			counterL = counterL + 1
		if (image_mode == 4356):
			im = Image.frombuffer('RGBA', (width, height), zlib_decompress, 'raw', 'RGBA', 0, 1)
			counterRGBA = counterRGBA + 1
			
		im.save(os.path.join(out_dir, 'img_%d.png'%image_id))
	except:
		print ("error on %d;%s;%d;%d;%d;%d;%d;%d;%d;%d;%d;%d"%(unknown_hash1, type, file_id, always_8, zsize, max_pixel_count, always_1, unknown_hash2, width, height, image_mode, always__1))
	
	offset = offset+zsize+40
	pbar.update(image_id)
pbar.finish()

counter = counterL+counterLA+counterRGBA
rest = int(num_files) - counter
print("\nExtracting %s done\n%d of %d images were extracted" %(mcf_path, counter, num_files))
print("%d RGBA images\n%d LA-mode images\n%d L-mode images"%(counterRGBA, counterLA, counterL))
print
print "All files are extracted to: " + out_dir
if rest > 0:
	print("%d were not exported for some reason" %(rest))
	
#todo: put all parse_idmap together
if (parse_idmap == "y"):
	run_batch = raw_input("Do you want to copy all files to the right folder structure? (y/n): ")
	if (run_batch == "y"):
		print "Running batchfile in the background, please wait."
		os.system(mcf_path + "extracted\\move_files.bat")
		print "Batchfile done."
		print "All files are sorted in: " + sorted_dir
		print
		show_contents = raw_input("Do you want to see the contents of the sorted folder? (y/n): ")
		
		if (show_contents == "y"):
			list_files(sorted_dir)
