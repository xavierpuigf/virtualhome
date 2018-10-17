
import os
import re
import json

from glob import glob
from matplotlib import pyplot as plt
from collections import Counter
from termcolor import colored
from joblib import Parallel, delayed

import ipdb


plot = False
root_dirs = '/Users/andrew/UofT/home_sketch2program/dataset_augmentation/programs_processed_precond_nograb_morepreconds'
program_dir_name = 'executable_programs'
graph_dir_name = 'init_and_final_graphs'

patt_number = '\((.+?)\)'


def check_number_of_objects():

    program_txt_paths = glob(os.path.join(root_dirs, program_dir_name, '*/*.txt'))
    program_length_list = []
    program_instance_list = []
    for path in program_txt_paths:
        with open(path, 'r') as f:
            program_txt = f.read()
            program_txt = program_txt.split('\n')
            program = program_txt[4:]
            program_length = len(program)
            program_length_list.append(program_length)

            id_list = []
            for line in program:
                line = line.stripe().lower()

                number_match = re.search(patt_number, line)
                while number_match:
                    number_name = number_match.group(1)
                    id_list.append(number_name.split('.')[1])
                    number_match = re.search(patt_number, number_match.string[number_match.end(1):])
            program_instance_list.append(set(id_list))
    ipdb.set_trace()
    print()



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
    print(colored("Top 10", 'cyan'))
    for title, count in cnt.most_common()[:10]:
        print("{}: {}".format(title, count))

    print(colored("Bottom 10", 'cyan'))
    for title, count in cnt.most_common()[-10:]:
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
    check_number_of_objects()