# Augments the dataset by replacing objects with others having the same affordance
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
    augmented_data_dir = '../augmented_program'
    if not os.path.exists(augmented_data_dir):
        os.makedirs(augmented_data_dir)


synthetic_data = loadmat('../synthetic_data')
object_names = [x[0] for x in synthetic_data['objects'][0].tolist()]
actions = synthetic_data['actions'][0].tolist()
action_names = [action['action_name'].item().item() for action in actions]
action_name2idx = {x:i for i, x in enumerate(action_names)}
object_name2idx = {x.lower().replace(' ', '_'):i for i, x in enumerate(object_names)}

object_states = {}

dict_cont = {}

with open('../object_merged.json', 'r') as f:
    merge_content = json.loads(f.read())

# maps every object to the first object that appears in merge_dict
merge_dict = {}
all_conts = 0
for obj_parent in merge_content.keys():
    children = merge_content[obj_parent]
    for it, child in enumerate(children):
        obj_id = object_name2idx[child]
        fields1 = synthetic_data['fields'][0,0][:, obj_id] 
        fields2 = synthetic_data['fields'][0,1][:, obj_id]
        if it > 0:
            # check that merged objects can be applied to the same actions
            try:
                assert(np.all(fields1 == last_f1))
                assert(np.all(fields2 == last_f2))
            except:
                a1 = np.where(fields1 != last_f1)
                a2 = np.where(fields2 != last_f2)
                if a1[0].shape[0] > 0:
                    print ([action_names[u] for u in a1[0]])
                if a2[0].shape[0] > 0:
                    print ([action_names[u] for u in a2[0]])

        last_f1 = fields1
        last_f2 = fields2
        # maps an object_id to its representative in the group (parent)
        merge_dict[object_name2idx[child]] = object_name2idx[children[0]]

for idi, obj in enumerate(object_names):
    if idi not in merge_dict.keys():
        merge_dict[idi] = idi

# For every object, list of all the objects they are merged with
merge_dict_list = {}
for idi in merge_dict.keys():
    if merge_dict[idi] not in merge_dict_list.keys():
        merge_dict_list[merge_dict[idi]] = []
    merge_dict_list[merge_dict[idi]].append(idi)

def getObjectAffordance(obj_id):
    # Get all the objects that can be used with the same actions as the ones in obj_id
    if merge_dict[obj_id] in dict_cont.keys():
        return len(dict_cont[merge_dict[obj_id]])

    # Look at which actions this object can take, which is the sumer of the actions of the merged objects
    fields1 = np.zeros((synthetic_data['fields'][0,0].shape[0], 1))
    fields2 = np.zeros((synthetic_data['fields'][0,0].shape[0], 1))
    for obj_id_merged in merge_dict_list[merge_dict[obj_id]]:
        fields1 += synthetic_data['fields'][0,0][:, obj_id_merged][:, None]
        fields2 += synthetic_data['fields'][0,1][:, obj_id_merged][:, None]

    objects_1 = (np.logical_xor(fields1, synthetic_data['fields'][0,0])).sum(0)
    objects_2 = (np.logical_xor(fields2, synthetic_data['fields'][0,1])).sum(0)
    elems = ((objects_1 + objects_2) == 0)
    elems_idx = np.where(elems)[0]
    elems_idx_merged = [merge_dict[it] for it in elems_idx]
    obj_same = list(set(elems_idx_merged))
    cont = len(obj_same)

    #print object_names[obj_id], [object_names[it] for it in obj_same], np.sum(fields1), np.sum(fields2)
    dict_cont[merge_dict[obj_id]] = obj_same
    return cont-1

def recursiveSelection(cont, it, curr_list):
    if it == len(cont):
        return [curr_list]
    res = []
    for idi in range(cont[it]):
        res += recursiveSelection(cont, it+1, curr_list+[idi])
    return res

# Build dict_cont
for idi in range(len(object_names)):
    getObjectAffordance(idi)

# Convert dict_cont into a list of lists (with replaceable objects)
list_replace = {}
for idi in dict_cont.keys():
    elems_group = dict_cont[idi]
    representative = sorted(elems_group)[0]
    if len(elems_group) > 1:
        if object_names[representative] in list_replace.keys():
            try:
                assert [object_names[it] for it in elems_group] == list_replace[object_names[representative]]
            except:
                ipdb.set_trace()
        else:
            list_replace[object_names[representative]] = [object_names[it] for it in elems_group]


# build list of objects that can take the same actions
list_replace_list = [list_replace[x] for x in list_replace.keys()]
with open('../object_replace.json', 'w+') as f:
    f.write(json.dumps(list_replace_list, indent=4))


# For every object, map all the objects that can be there
if os.path.isfile('../object_replace_manually_modif.json'):
    object_replace = json.load(open('../object_replace_manually_modif.json', 'r'))
object_replace_dict = {}
for elem in object_replace:
    for object_name in elem:
        assert object_name not in object_replace_dict.keys()
        object_replace_dict[object_name.lower().replace(' ', '_')] = elem


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
files = glob.glob('../programs_processed_precond_nograb/withoutconds/*/*.txt')
n_all_progs = 0
temp = []

for file_name in tqdm(files):
    with open(file_name, 'r') as f:
        augmented_progs_i = []
        augmented_preconds_i = []
        
        lines = f.readlines() 
        prog_orig = lines
        lines = lines[4:]
        objects_prog = []
        newobjname2old = {}
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
                objects_prog.append((obj_name, num_name))           # object, index
        objects_prog = list(set(objects_prog))
        all_cont = 1

        # For every different object instance, see if we can replace it
        object_replace_map = {}
        for objectn, idn in objects_prog:
            object_replace_map[(objectn, idn)] = [objectn]
            if objectn in object_replace_dict.keys():
                cont = random.randint(1, min(len(object_replace_dict[objectn]), 5))     # always including `objectn`
                object_candidates = [x.lower().replace(' ', '_') for x in object_replace_dict[objectn] if x.lower().replace(' ', '_') != objectn] 
                if cont > 1:
                    object_replace = random.sample(object_candidates, cont-1)
                    # For every object instance, the object we will replace with
                    object_replace_map[(objectn, idn)] += object_replace
                    all_cont *= cont

        npgs = 0
        # Cont has, for each unique object, the number of objects we will replace it with
        cont = []
        for obj_and_id in objects_prog:
            cont.append(len(object_replace_map[obj_and_id]))


        ori_precond = json.load(open(file_name.replace('withoutconds', 'initstate').replace('txt', 'json'), 'r'))
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
                        
                        elif precond_relation in ['is_on', 'is_off', 'open']:
                            object_name = precond_objects
                            need_to_change = object_name[0].lower().replace(' ', '_') == orign_object
                            if need_to_change:
                                precond_objects[0] = object_new
                        else:
                            print(precond_relation, precond_objects)
                            ipdb.set_trace()
                        
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
