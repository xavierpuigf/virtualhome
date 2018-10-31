
import os
import re
import json
import numpy as np

from glob import glob
from matplotlib import pyplot as plt
from collections import Counter
from termcolor import colored
from joblib import Parallel, delayed

import ipdb


plot = False
root_dirs = 'dataset_augmentation/programs_processed_precond_nograb_morepreconds'
program_dir_name = 'executable_programs'
graph_dir_name = 'init_and_final_graphs'

patt_number = '\((.+?)\)'


def check_unique_progs():

    all_progs_path = 'train_progs_precond.json'
    train_dataset = json.load(open(all_progs_path))
    train_paths = list(train_dataset.keys())
    graph_paths = ['TrimmedTestScene{}_graph'.format(i+1) for i in range(6)]

    unique_paths = []
    for p in train_paths:
        for g in graph_paths:
            if g in p:
                unique_paths.append(p.replace('/'+g, ''))

    unique_paths = list(set(unique_paths))
    f = open('train_unique_progs_paths.txt', 'w')
    for p in unique_paths:
        f.write(p)
        f.write('\n')
    f.close()


def check_prog_unity():

    f = open('train_unique_progs_paths.txt')
    unique_paths = f.read().split('\n')
    unique_paths.pop()

    
    unique_progs_and_path = []
    train_dataset = json.load(open('train_progs_precond.json'))
    for path in unique_paths:
        for data_path in train_dataset:
            if data_path.endswith('/'.join(path.split('/')[-2:])):
                unique_progs_and_path.append([train_dataset[data_path], data_path])
                break


    object_prefabs = json.load(open('resources/object_prefabs.json'))
    available_obs = [k.lower().replace(' ', '_') for k in object_prefabs.keys()]
    class_name_equivalence = json.load(open('resources/class_name_equivalence.json'))
    static_objects = ['bathroom', 'floor', 'wall', 'ceiling', 'rug', 'curtains', 'ceiling_lamp', 'wall_lamp', 
                        'bathroom_counter', 'bathtub', 'towel_rack', 'wall_shelf', 'stall', 'bathroom_cabinet', 
                        'toilet', 'shelf', 'door', 'doorjamb', 'window', 'lightswitch', 'bedroom', 'table_lamp', 
                        'chair', 'bookshelf', 'nightstand', 'bed', 'closet', 'coatrack', 'coffee_table', 
                        'pillow', 'hanger', 'character', 'kitchen', 'maindoor', 'tv_stand', 'kitchen_table', 
                        'bench', 'kitchen_counter', 'sink', 'power_socket', 'tv', 'clock', 'wall_phone', 
                        'cutting_board', 'stove', 'oventray', 'toaster', 'fridge', 'coffeemaker', 'microwave', 
                        'livingroom', 'sofa', 'coffee_table', 'desk', 'cabinet', 'standing_mirror', 'globe', 
                        'mouse', 'mousemat', 'cpu_screen', 'cpu_case', 'keyboard', 'ceilingfan', 
                        'kitchen_cabinets', 'dishwasher', 'cookingpot', 'wallpictureframe', 'vase', 'knifeblock', 
                        'stovefan', 'orchid', 'long_board', 'garbage_can', 'photoframe', 'balance_ball', 'closet_drawer']
    
    patt_objs = '\<(.+?)\>'
    valid_paths = []
    for prog, path in unique_progs_and_path:
        object_match = re.search(patt_objs, prog)
        objs = []
        while object_match:
            objs.append(object_match.group(1))
            object_match = re.search(patt_objs, object_match.string[object_match.end(1):])

        objs = list(set(objs))
        valid = True
        for obj in objs:
            if obj in class_name_equivalence:
                all_alias = class_name_equivalence[obj] + [obj]
            else:
                all_alias = [obj]

            if not any([o.lower().replace(' ', '_') in available_obs or o.lower().replace(' ', '_') in static_objects for o in all_alias]):
                valid = False
                break

        if valid:
            valid_paths.append(path)


    graph_paths = ['TrimmedTestScene{}_graph'.format(i+1) for i in range(6)]
    unique_paths = []
    for p in valid_paths:
        for g in graph_paths:
            if g in p:
                unique_paths.append(p.replace('/'+g, ''))

    f = open('train_unique_unity_progs_paths.txt', 'w')
    for p in unique_paths:
        f.write(p)
        f.write('\n')
    f.close()


def check_number_of_objects():

    program_txt_paths = glob(os.path.join(root_dirs, program_dir_name, '*/*.txt'))

    program_instance_list = []
    for path in program_txt_paths:
        with open(path, 'r') as f:
            program_txt = f.read()
            program_txt = program_txt.split('\n')
            program = program_txt[4:]

            id_list = []
            for line in program:
                line = line.strip().lower()

                number_match = re.search(patt_number, line)
                while number_match:
                    number_name = number_match.group(1)
                    id_list.append(number_name.split('.')[1])
                    number_match = re.search(patt_number, number_match.string[number_match.end(1):])
            program_instance_list.append(set(id_list))

    n_instance_list = np.array([len(l) for l in program_instance_list])
    mean_n_instance = np.sum(n_instance_list) / len(n_instance_list)
    print("Average number of instance in the program = {:.2f}, std = {:.2f}, max = {}, min = {}".format(mean_n_instance, np.std(n_instance_list), np.max(n_instance_list), np.min(n_instance_list)))


def evaluate_f1_scores(graph1_state, graph2_state, program1_id_list, program2_id_list):
    """
        graph1_state: the prediction graph
        graph2_state: the ground truth graph
        program1_id_list: the id that appear in prediction (exclude character node)
        program2_id_list: the id that appear in the ground truth (exclude character node)
    """

    character_id = [i["id"] for i in filter(lambda v: v['class_name'] == 'character', graph1_state["nodes"])]
    room_id = [i["id"] for i in filter(lambda v: v['category'] == 'Rooms', graph1_state["nodes"])]

    program1_id_list += character_id
    program2_id_list += character_id
    program1_id_list_wo_room = set([i for i in filter(lambda v: v not in room_id, program1_id_list)])
    program2_id_list_wo_room = set([i for i in filter(lambda v: v not in room_id, program2_id_list)])

    def _convert_to_tuple(graph, id_list):

        attribute_tuples = []
        for node in graph["nodes"]:
            if node["id"] in id_list:
                for state in node["states"]:
                    attribute_tuples.append((node["id"], state))

        relation_tuples = []
        for edge in graph["edges"]:
            if edge["from_id"] in id_list or edge["to_id"] in id_list:
                relation_tuples.append((edge["relation_type"], edge["from_id"], edge["to_id"]))

        return attribute_tuples, relation_tuples

    def _find_match(attribute_pred_tuple, relation_pred_tuple,  attribute_gt_tuple, relation_gt_tuple):

        attribute_match = 0
        for tuple in attribute_pred_tuple:
            if tuple in attribute_gt_tuple:
                attribute_match += 1

        relation_match = 0
        for tuple in relation_pred_tuple:
            if tuple in relation_gt_tuple:
                relation_match += 1

        return attribute_match, relation_match

    attribute_precision_list, relation_precision_list, total_precision_list = [], [], []
    attribute_recall_list, relation_recall_list, total_recall_list = [], [], []
    attribute_f1_list, relation_f1_list, total_f1_list = [], [], []

    all_lists = [attribute_precision_list, relation_precision_list, total_precision_list, 
                attribute_recall_list, relation_recall_list, total_recall_list, 
                attribute_f1_list, relation_f1_list, total_f1_list]

    def _append_all_values(v):
        if isinstance(v, float):
            for l in all_lists:
                l.append(v)
        else:
            for i, l in zip(v, all_lists):
                l.append(i)

    if graph1_state is None:
        return 0, 0, 0, 0, 0, 0, 0, 0, 0

    attribute_pred_tuple, relation_pred_tuple = _convert_to_tuple(graph1_state, program1_id_list_wo_room)
    attribute_gt_tuple, relation_gt_tuple = _convert_to_tuple(graph2_state, program2_id_list_wo_room)
    attribute_pred_tuple = set(attribute_pred_tuple)
    relation_pred_tuple = set(relation_pred_tuple)
    attribute_gt_tuple = set(attribute_gt_tuple)
    relation_gt_tuple = set(relation_gt_tuple)
    attribute_match, relation_match = _find_match(attribute_pred_tuple, relation_pred_tuple,  attribute_gt_tuple, relation_gt_tuple)

    if attribute_match != 0:
        attribute_precision = attribute_match / len(attribute_pred_tuple)
        attribute_recall = attribute_match / len(attribute_gt_tuple)
        attribute_f1 = 2 * attribute_precision * attribute_recall / (attribute_precision + attribute_recall)
    else:
        attribute_precision, attribute_recall, attribute_f1 = 0, 0, 0

    if relation_match != 0:
        relation_precision = relation_match / len(relation_pred_tuple)
        relation_recall = relation_match / len(relation_gt_tuple)
        relation_f1 = 2 * relation_precision * relation_recall / (relation_precision + relation_recall)
    else:
        relation_precision, relation_recall, relation_f1 = 0, 0, 0

    if (relation_match + attribute_match) != 0:
        total_precision = (relation_match + attribute_match) / (len(attribute_pred_tuple) + len(relation_pred_tuple))
        total_recall = (relation_match + attribute_match) / (len(attribute_gt_tuple) + len(relation_gt_tuple))
        total_f1 = 2 * total_precision * total_recall / (total_precision + total_recall)
    else:
        total_precision, total_recall, total_f1 = 0, 0, 0

    return attribute_precision, relation_precision, total_precision, attribute_recall, relation_recall, total_recall, attribute_f1, relation_f1, total_f1

    
def check_graph_init_and_final_state():

    patt_id = '\.(.+?)\)'
    graph_paths = glob(os.path.join(root_dirs, graph_dir_name, '*/*.json'))

    def _compute(path):

        graph = json.load(open(path, 'r'))
        init_graph = graph["init_graph"]
        final_graph = graph["final_graph"]
        
        path = path.replace(graph_dir_name, program_dir_name).replace('json', 'txt')
        program = '\n'.join(open(path, 'r').read().split('\n')[4:])

        id_list = []
        id_match = re.search(patt_id, program)
        while id_match:
            id_list.append(int(id_match.group(1)))
            id_match = re.search(patt_id, id_match.string[id_match.end(1):])

        results = evaluate_f1_scores(init_graph, final_graph, id_list, id_list)
        return results

    def _average_over_list(l):
        return sum(l) / len(l)

    results = Parallel(n_jobs=os.cpu_count())(delayed(_compute)(path) for path in graph_paths)
    #results = [_compute(path) for path in graph_paths[:100]]

    key = ['attribute_precision', 'relation_precision', 'total_precision', 'attribute_recall', 'relation_recall', 'total_recall', 'attribute_f1', 'relation_f1', 'total_f1']
    values = []
    for i in range(len(key)):
        values.append(_average_over_list([j[i] for j in results]))

    for k, v in zip(key, values):
        print("{}: {}".format(k, v))


def check_title():

    program_txt_paths = glob(os.path.join(root_dirs, program_dir_name, '*/*.txt'))
    title_list = []
    desc_list = []
    program_length_list = []
    for path in program_txt_paths:
        with open(path, 'r') as f:
            program_txt = f.read()
            program_txt = program_txt.split('\n')
            title = program_txt[0]
            desc = program_txt[1]
            program = program_txt[4:]
            program_length = len(program)

            title_list.append(title)
            desc_list.append(desc)
            program_length_list.append(program_length)


    print("Total programs:", len(title_list))
    print("Average program length: {:.2f}".format(sum(program_length_list)/len(program_length_list)))

    print("*"*30)
    cnt = Counter(title_list)
    print("Title:")
    print("-"*30)
    print(colored("Top 20", 'cyan'))
    for title, count in cnt.most_common()[:20]:
        print("{}: {}".format(title, count))

    cnt_values = [v for v in cnt.values()]
    if plot:
        plt.hist(cnt_values, len(set(cnt_values)))
        plt.title('title histrogram')
        plt.show()
    print("*"*30)


if __name__ == '__main__':
    #check_title()
    #check_graph_init_and_final_state()
    #check_number_of_objects()
    #check_unique_progs()
    check_prog_unity()