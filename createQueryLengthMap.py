import myetree.ElementTree as ET
import re
import sys


query_file = 'lib/kws/queries.xml'
outmap_file = 'querylength.map'


doc = ET.parse(query_file)
kws = doc.getroot().findall('kw')

# build a dictionary to store the number (cont) of queries of length n:
#    counter[n] = cont
counter = {}

with open(outmap_file, 'w') as f:
	
	# for each query in the file
	for kw in kws:
		# get the query id: KW202-id
		idx = re.split('-', kw.get('kwid'))[-1]
		# load the list of words
		query = [x.lower() for x in re.split('\s+', kw.find('kwtext').text)]
		# evaluate the number of words
		n = len(query)
		if n not in counter:
			counter[n] = 0
		counter[n] += 1
		line = ' '.join([str(n), str(idx), str(counter[n])])
		f.write(line+'\n')

print 'counter', counter
print 'sum', sum([counter[x] for x in counter.keys()])
