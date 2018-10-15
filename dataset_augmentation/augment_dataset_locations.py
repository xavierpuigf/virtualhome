# Augments the dataset by replacing object containers with other containers where these objects tipically go
import random
import copy
import os
import glob
import numpy as np
import json

from tqdm import tqdm
from scipy.io import *

import ipdb


random.seed(123)
thres = 300
write_augment_data = False

if write_augment_data:
    augmented_data_dir = 'augmented_program_location'
    if not os.path.exists(augmented_data_dir):
        os.makedirs(augmented_data_dir)



object_states = {}

dict_cont = {}

with open('object_script_placing.json', 'r') as f:
    info_locations = json.loads(f.read())

# maps every object, and relation to all the possible objects
merge_dict = {}
all_conts = 0
for obj_name in info_locations.keys():
    children = info_locations[obj_name]
    for it, child in enumerate(children):
        other_object = child['destination']
        relation = child['relation']
        if (obj_name, relation) not in merge_dict.keys():
            merge_dict[(obj_name, relation)] = []
        merge_dict[(obj_name, relation)].append(other_object)


def recursiveSelection(cont, it, curr_list):
    if it == len(cont):
        return [curr_list]
    res = []
    for idi in range(cont[it]):
        res += recursiveSelection(cont, it+1, curr_list+[idi])
    return res

def write_data(ori_path, all_new_progs):
    
    # make_dirs
    sub_dir = ori_path.split('/')[-2]
    old_name = ori_path.split('/')[-1].split('.')[0]
    new_dir = os.path.join(augmented_data_dir, 'withoutconds', sub_dir, old_name)
    assert not os.path.exists(new_dir), ipdb.set_trace()
    os.makedirs(new_dir)

    for j, new_progs in enumerate(all_new_progs):
        new_f = open('{}/{}.txt'.format(new_dir, j), 'w')
        for lines in new_progs:
            new_f.write(lines)
        new_f.close()    


def write_precond(ori_path, all_new_preconds):
    
    # make_dirs
    sub_dir = ori_path.split('/')[-2]
    old_name = ori_path.split('/')[-1].split('.')[0]
    new_dir = os.path.join(augmented_data_dir, 'initstate', sub_dir, old_name)
    assert not os.path.exists(new_dir), ipdb.set_trace()
    os.makedirs(new_dir)

    for j, new_precond in enumerate(all_new_preconds):
        new_f = open('{}/{}.json'.format(new_dir, j), 'w')
        json.dump(new_precond, new_f)
        new_f.close()   


# For every program, check the objects that can be replaced
files = glob.glob('programs_processed_precond_nograb_morepreconds/withoutconds/*/*.txt')
n_all_progs = 0
temp = []
precondtorelation = {
    'in': 'ON',
    'inside': 'IN'
}

all_cont = 1
for file_name in tqdm(files):
    with open(file_name, 'r') as f:
        augmented_progs_i = []
        augmented_preconds_i = []
        
        lines = f.readlines() 
        prog_orig = lines
        lines = lines[4:]
    newobjname2old = {'character': 'character'}
    # Obtain all the object instance of a given program
    for line in lines:
        if '<' not in line:
            continue
        content = line.split('<')
        for el in content[1:]:
            obj_name_orig = el.split('>')[0]
            num_name = el.split('(')[1].split(')')[0]
            obj_name = obj_name_orig.lower().replace(' ', '_')
            newobjname2old[obj_name] = obj_name_orig

    with open(file_name.replace('withoutconds', 'initstate').replace('.txt', '.json'),
              'r') as fst:
        state = json.load(fst)
   
    # for every object, we list the objects that are inside, on etc.
    # they will need to be replaced by objects where the others follow the same
    # property
    relations_per_object = {}
    for cstate in state:
        precond = cstate.keys()[0]
        if precond in ['inside', 'in']:
            relation = precondtorelation[precond]
            object1 = cstate[precond][0][0].lower().replace(' ', '_')
            container = tuple(cstate[precond][1])
            container = (container[0].lower().replace(' ', '_'), container[1])
            if container not in relations_per_object.keys():
                relations_per_object[container] = []
            relations_per_object[container] += [(object1, relation)]

    # Given all the containers, check which objects can go there
    object_replace_map = {}
    for container in relations_per_object.keys():
        replace_candidates = [] 
        for object_and_relation in relations_per_object[container]:
            if object_and_relation in merge_dict.keys():
                replace_candidates.append(merge_dict[object_and_relation])

        # do a intersection of all the replace candidates
        intersection = []
        object_replace_map[container] = [container[0]]
        if len(replace_candidates) > 0  and len([l for l in replace_candidates if len(l) == 0]) == 0: # if there are objects we can replace
            intersection = list(set.intersection(*[set(l) for l in replace_candidates]))
            candidates = list(intersection)
            candidates = [x for x in candidates if x != container[0]]
            if len(candidates) > 0:
                cont = random.randint(1, min(len(candidates), 5)) # always including `container'
                # sample candidates
                if cont > 1:
                    object_replace = random.sample(candidates, cont-1)
                    object_replace_map[container] += object_replace
                    all_cont *= cont

    #ipdb.set_trace()
    objects_prog = object_replace_map.keys()
    npgs = 0
    # Cont has, for each unique object, the number of objects we will replace it with
    cont = []
    for obj_and_id in objects_prog:
        cont.append(len(object_replace_map[obj_and_id]))


    ori_precond = state
    # We obtain all the permutations given cont

    recursive_selection = recursiveSelection(cont, 0, [])

    # For every permutation, we compute the new program
    for rec_id in recursive_selection:
        # change program
        new_lines = prog_orig
        for iti, obj_and_id in enumerate(objects_prog):
            orign_object, idi = obj_and_id
            object_new = object_replace_map[obj_and_id][rec_id[iti]]
            object_to_replace_oldname = newobjname2old[orign_object]
            new_lines = [x.replace('<{}> ({})'.format(object_to_replace_oldname, idi), 
                                   '<{}> ({})'.format(object_new, idi)) for x in new_lines]
        
        augmented_progs_i.append(new_lines)

        # change precond
        precond_modif = copy.deepcopy(ori_precond)
        
        for iti, obj_and_id in enumerate(objects_prog):
            orign_object, idi = obj_and_id
            object_new = object_replace_map[obj_and_id][rec_id[iti]]

            for preconds in precond_modif:
                for precond_relation, precond_objects in preconds.items():
                    if precond_relation in ['location', 'inside', 'atreach', 'in']:
                        src_object_name, tgt_object_name = precond_objects
                        src_need_to_change = src_object_name[0].lower().replace(' ', '_') == orign_object
                        tgt_need_to_change = tgt_object_name[0].lower().replace(' ', '_') == orign_object
                        if src_need_to_change:
                            precond_objects[0][0] = object_new
                        if tgt_need_to_change:
                            precond_objects[1][0] = object_new
                    
                    elif precond_relation in ['is_on', 'is_off', 'open', 'closed', 'plugged', 'unplugged']:
                        object_name = precond_objects
                        need_to_change = object_name[0].lower().replace(' ', '_') == orign_object
                        if need_to_change:
                            precond_objects[0] = object_new
                    else:
                        print(precond_relation, precond_objects)
                    
        augmented_preconds_i.append(precond_modif)
        npgs += 1
        if npgs > thres:
            break

    n_all_progs += npgs

    # The current program
    all_conts += all_cont

    if write_augment_data:
        write_data(file_name, augmented_progs_i)
        write_precond(file_name, augmented_preconds_i)

print ('Number of programs', all_conts, n_all_progs)
