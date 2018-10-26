import glob
<<<<<<< HEAD
=======
import shutil
import os
>>>>>>> 7a43554e55cdb963ac7138b263633dd475fd0ed0
import json
import ipdb
import re
from collections import Counter

with open('..//executable_info.json', 'r') as f:
    content = json.load(f)

errors = []
titles = []
for elem in content:
        #print elem
        #print content[elem]
        elem_modif = ' '.join(content[elem].split()[1:])
        if 'Script is executable' in elem_modif:
            with open('../' + elem, 'r') as f:
                lines = f.readlines()
                title = lines[0]
            titles.append(title)

        else:
            elem_modif = re.sub('\([^)]*\)', '', elem_modif)
            elem_modif = re.sub('\[[1-9]*\]', '', elem_modif)
            print(elem)
            print(elem_modif)
            errors.append(elem_modif)
        #file_input = elem.replace('/Users/andrew/UofT/home_sketch2program/data/', '').replace('withoutconds', 'withconds')
        #with open(file_input, 'r') as f:
        #	aux = f.readlines()
        #print (''.join(aux))
        #print '\n'
        #ipdb.set_trace()
        #print '\n'

cnt = Counter(errors).most_common()
print('Reasons failure')
for el in cnt:
    print(el)


cnt = Counter(titles).most_common()
print('Titles')
for el in cnt:
    print(el)
