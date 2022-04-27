""" Utility functions to augment scripts
"""
import pdb
import os
import json

curr_dirname = os.path.dirname(__file__)
with open('{}/../resources/properties_data_all.json'.format(curr_dirname), 'r') as f:
    object_properties = json.load(f)

def parseStrBlock(block_str):
    """ Given a str block [Rinse] <CLEANING SOLUTION> (1)
        parses the block, returning Action, List Obj, List Instance
    """
    action = block_str[1:block_str.find(']')]
    block_str = block_str[block_str.find(']')+3:-1]
    block_split = block_str.split(') <') # each element is name_obj> (num
    obj_names = [block[0:block.find('>')] for block in block_split]
    inst_nums = [block[block.find('(')+1:] for block in block_split]
    action = action.strip()
    obj_names_corr = []
    inst_nums_corr = []
    for i in range(len(obj_names)):
        if len(obj_names[i].strip()) > 0 and len(inst_nums[i].strip()) > 0:
            obj_names_corr.append(obj_names[i])
            inst_nums_corr.append(inst_nums[i])
    return action, obj_names_corr, inst_nums_corr



def hasProperty(obj_name, property_name):
    """ Check if object obj_name has property """
    obj_name_corrected = obj_name.lower().replace(' ', '_')
    return property_name in object_properties[obj_name_corrected]


def insertInstructions(insert_in, contentold):
    ''' inserts insert_in in content_old '''
    content = contentold.copy()
    acum = 0
    for insertval in insert_in:
        content.insert(insertval[0]+acum, insertval[1])
        acum += 1
    return content


def removeInstructions(to_delete, content):
    """ removes indices to_delete from content """
    return [x for i, x in enumerate(content) if i not in to_delete]


class Precond:

    """ Precondition class, storing the preconditions for a program """
    def __init__(self):
        self.precond_dict = {}

    def addPrecond(self, cond, obj1, obj2):
        if cond not in self.precond_dict.keys():
            self.precond_dict[cond] = {}
        if obj1 not in self.precond_dict[cond]:
            
            self.precond_dict[cond][obj1] = set(obj2)
        else:
            # self.precond_dict[cond][obj1] = set(list(self.precond_dict[cond][obj1])+list(obj2))
            old_objects = list(self.precond_dict[cond][obj1])
            self.precond_dict[cond][obj1] = set(old_objects+obj2)
    def printConds(self):
        res = [str(len(self.precond_dict.keys()))]
        for cond in self.precond_dict.keys():
            elem_list = []
            for l in self.precond_dict[cond].keys():

                # if not type(list(self.precond_dict[cond][l])[0]) == tuple:
                #     pdb.set_trace()
                this_str = '{} --> {}'.format(str(l), ' / '.join([str(p) for p in list(self.precond_dict[cond][l])]))
                elem_list.append(this_str)
            elements = ', '.join(elem_list)
            stri = '{}: {}'.format(cond, elements)
            res.append(stri)
        return res

    def printCondsJSON(self):
        conds = []
        for cond in self.precond_dict.keys():
            if cond != 'nearby':
                for it in self.precond_dict[cond].keys():
                    it_lowercase = [it[0].lower().replace(' ', '_'), it[1]]
                    if len(self.precond_dict[cond][it]) == 0:
                        conds.append({cond: it_lowercase})
                    else:
                        for elements in list(self.precond_dict[cond][it]):
                            elements_lower = [elements[0].lower().replace(' ', '_'), elements[1]]
                            conds.append({cond: [it_lowercase, elements_lower]})

        return conds
    def removeCond(self, cond, object_id=None, second=None):
        if object_id is None:
            del self.precond_dict[cond]
        elif second is None:
            del self.precond_dict[cond][object_id]
        else:
            self.precond_dict[cond][object_id].remove(second)
    def obtainCond(self, cond):
        if cond in self.precond_dict.keys():
            return self.precond_dict[cond].keys()
        return []


def write_data(augmented_data_dir, ori_path, all_new_progs, namedir='withoutconds'):
    
    # make_dirs
    sub_dir = ori_path.split('/')[-2]
    old_name = ori_path.split('/')[-1].split('.')[0]
    new_dir = os.path.join(augmented_data_dir, namedir, sub_dir, old_name)
    try:
        os.makedirs(new_dir)
    except:
        pass

    for j, new_progs in enumerate(all_new_progs):
        new_f = open('{}/{}.txt'.format(new_dir, j), 'w')
        nnew_progs = [x+'\n' for x in new_progs]
        for lines in nnew_progs:
            new_f.write(lines)
        new_f.close() 


def write_precond(augmented_data_dir, ori_path, all_new_preconds):
    
    # make_dirs
    sub_dir = ori_path.split('/')[-2]
    old_name = ori_path.split('/')[-1].split('.')[0]
    new_dir = os.path.join(augmented_data_dir, 'initstate', sub_dir, old_name)
    try:
        os.makedirs(new_dir)
    except:
        pass

    for j, new_precond in enumerate(all_new_preconds):
        new_f = open('{}/{}.json'.format(new_dir, j), 'w')
        json.dump(new_precond, new_f)
        new_f.close()


def write_graph(augmented_data_dir, ori_path, state_list, apt_name):

    sub_dir = ori_path.split('/')[-2]
    old_name = ori_path.split('/')[-1].split('.')[0]
    new_dir = os.path.join(augmented_data_dir, 'init_and_final_graphs', apt_name,
                           sub_dir, old_name)
    try:
        os.makedirs(new_dir)
    except:
        pass
    for j in range(len(state_list)):
        new_f = open('{}/{}.json'.format(new_dir, j), 'w')
        json.dump(
                {"init_graph": state_list[j][0],
                 "final_graph": state_list[j][-1]}, new_f)
        new_f.close()

    # state list
    new_dir = os.path.join(augmented_data_dir, 'state_list', apt_name, 
                           sub_dir, old_name)
    try:
        os.makedirs(new_dir)
    except:
        pass
    for j in range(len(state_list)):
        new_f = open('{}/{}.json'.format(new_dir, j), 'w')

        json.dump({"graph_state_list": state_list[j]}, new_f)
        new_f.close()   


def recursiveSelection(cont, it, curr_list):
    # Obtains a list containing all subsets of cont
    if it == len(cont):
        return [curr_list]
    res = []
    for idi in range(cont[it]):
        res += recursiveSelection(cont, it+1, curr_list+[idi])
    return res

