from xml.dom import minidom
import re
import operator
import myetree.ElementTree as ET
from collections import OrderedDict


# build the indexer, containing the indexes in the transcription where each word occurs
def index_generation(ref):
	
	# initialise the dictionary I
	I = {}

	# load the reference file
	f = open(ref)
	lines = f.readlines()
	f.close()
	
	if not (lines[len(lines)-1].strip('\n')):		# handle newline at the EOF
		lines = lines[0:len(lines)-1]
	# read rows in the ref file
	for i in range(len(lines)):
		# get word from line i-th
		word = re.split('\s+',lines[i].strip('\n'))[4].lower()
		
		if not word in I:			# if unseen so far:
			I[word] = []			# create new entry in dictionary
		# append idx of current line in file
		I[word].append(i)
		
	return lines, I



# search the queries in the transcription file
def search_queries(I, queries, lines, output_file):

	# initialize the output doc creating the root
	attrs = OrderedDict()
	attrs['kwlist_filename'] = 'IARPA-babel202b-v1.0d_conv-dev.kwlist.xml'
	attrs['language'] = 'swahili'
	attrs['system_id'] = ''
	root = ET.Element('kwslist', attrs)

	# open query file
	doc = ET.parse(queries)
	# get all the hits (over all queries)
	kws = doc.getroot().findall('kw')

	# for each hit in the query file
	for kw in kws:
		# get id and text (split in words and save in a list q) of the query
		kwid = kw.get('kwid')
		q = re.split('\s+', kw.find('kwtext').text)
		# ensure all words in query are lowercase
		q = [q[i].lower() for i in range(len(q))]

		# if the first word is in the transcription, then search for the whole query
		if q[0] in I:
			root, detected_kwsl = kw_detected(root, kwid)
			# get info of current word
			qlen = len(q)

			# check all occurrences of the first word in the query
			for i in I[q[0]]:
				# check if query == current block in reference and time intervals are valid
				if kw_same_file(lines, i, qlen, q) and valid_time_gap(lines, i, qlen):
					firstinfo = re.split('\s+', lines[i])
					lastinfo = re.split('\s+', lines[i+qlen-1])
					# print firstinfo
					durs = [float(re.split('\s+', lines[x])[3]) for x in range(i,i+qlen)]
					#durtot = float(lastinfo[2])+durs[-1] - float(firstinfo[2])
					durtot = sum(durs)
					# check what to do w/ score, maybe:
					scores = [float(re.split('\s+', lines[x])[5]) for x in range(i,i+qlen)]
					finalscore = reduce(operator.mul, scores, 1)	# multiply the score on the query I
					# info = {'file':firstinfo[0], 'channel':firstinfo[1], 'tbeg':firstinfo[2], 'dur':str(round(durtot,2)), 'score':firstinfo[5]}
					info = OrderedDict()
					info['file'] = firstinfo[0]
					info['channel'] = firstinfo[1]
					info['tbeg'] = firstinfo[2]
					info['dur'] = str(round(durtot,2))
					info['score'] = str(finalscore)
					info['decision'] = 'YES'
					root, detected_kwsl = append_query_result(root, detected_kwsl, info)

	outdoc = ET.ElementTree(root)
	return outdoc



## handle the OOV words by initializing an empty list in I (maybe????) ??????
#def handle_oov():
#	pass



# add new instance of query in output file
def kw_detected(root, kwid):

#	found=0
	# maybe just:
	for k in root:	# faster way to do this?
		# check if query instance is already present
		if k.attrib['kwid']==kwid:
#			found=1
			return k 	# return query node with id kwid
	# if first occurrence then create a new node 'detected_kwslist'
#	if not found:
	detected_kwsl = ET.SubElement(root, 'detected_kwlist')
	attrs = OrderedDict()
	attrs['kwid'] = kwid
	attrs['oov_count'] = '0'
	attrs['search_time'] = '0.0'
	detected_kwsl.attrib = attrs

	return root, detected_kwsl 	# return current query node with id kwid ?



# verify that the words spotted are from the same file/channel
def kw_same_file(lines, start, qlen, q):

	# get list of words in reference
	if start+qlen>len(lines):
		return 0
	r = [re.split('\s+', lines[x])[4].lower() for x in range(start,start+qlen)]
	# check if it corresponds to query list of words
	if q!=r:
		return 0
	# for each pair of successive words check: filename, channel
	for i in range(start+1, start+qlen):
		f1 = re.split('\s+',lines[i-1])[0]	# filename of w1
		c1 = re.split('\s+',lines[i-1])[1]	# channel of w1
		f2 = re.split('\s+',lines[i-1])[0]	# filename of w2
		c2 = re.split('\s+',lines[i-1])[1]	# channel of w2
		if f1!=f2 or c1!=c2:
			return 0
	return 1		# return true only if no problems while checking in the loop

	

# verify the threshold (0.5s) for the time interval between two words in the same phrase
def valid_time_gap(lines, start, qlen):

	for i in range(start+1, start+qlen): #use range instead
		t1 = float(re.split('\s+',lines[i-1])[2])	# t start of w1
		d1 = float(re.split('\s+',lines[i-1])[3])	# length of w1
		t2 = float(re.split('\s+',lines[i])[2])	#t start of w2

		if round(t2-(t1+d1),2)>0.5:
			return 0
	return 1		# return true only if no problems during time interval checking in the loop




# append a new entry of the word to the correspondent query
def append_query_result(root, detected_kwsl, info):

	kw = ET.SubElement(detected_kwsl, 'kw')
	# attrs = info
	kw.attrib = info
	# print kw.attrib
	
	return root, detected_kwsl



# indent the xml to be read by the scoring function
# function adapted from: https://norwied.wordpress.com/2013/08/27/307/
def indent(elem, level=0):
    i = "\n"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

