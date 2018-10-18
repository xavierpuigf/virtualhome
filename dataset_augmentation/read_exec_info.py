import glob
import shutil
import os
import json
import ipdb
import re
from collections import Counter

with open('..//executable_info.json', 'r') as f:
    content = json.load(f)

errors = []
titles = []
cont = 0
for elem in content:
        #print elem
        #print content[elem]
        elem_modif = ' '.join(content[elem].split()[1:])
        if 'Script is executable' in elem_modif:
            with open('../' + elem, 'r') as f:
                lines = f.readlines()
                title = lines[0]
            titles.append(title)
            elem = elem.replace('dataset_augmentation/', '')
            elem_state = elem.replace('withoutconds', 'initstate').replace('.txt', '.json')
            new_file = elem.replace('morepreconds', 'morepreconds_executable')
            new_file_state = new_file.replace('withoutconds', 'initstate').replace('.txt', '.json')

            if not os.path.isdir(os.path.dirname(new_file)):
                
                os.makedirs(os.path.dirname(new_file))
                os.makedirs(os.path.dirname(new_file_state))
            shutil.copy(elem, new_file)
            shutil.copy(elem_state, new_file_state)
            cont += 1

        else:

            elem_modif = re.sub('\([^)]*\)', '', elem_modif)
            elem_modif = re.sub('\[[1-9]*\]', '', elem_modif)
            #print(elem)
            #print(elem_modif)
            errors.append(elem_modif)
        #file_input = elem.replace('/Users/andrew/UofT/home_sketch2program/data/', '').replace('withoutconds', 'withconds')
        #with open(file_input, 'r') as f:
        #	aux = f.readlines()
        #print (''.join(aux))
        #print '\n'
        #ipdb.set_trace()
        #print '\n'

cnt = Counter(errors).most_common()
print cont
#print('Reasons failure')
#for el in cnt:
#    print(el)
#
#
#cnt = Counter(titles).most_common()
#print('Titles')
#for el in cnt:
#    print(el)
