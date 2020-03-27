import json
import pdb

with open('SyntheticStories/MultiAgent/challenge/vh_multiagent_models/analysis/info_demo_scenes_2.json', 'r') as f:
    content = json.load(f)

with open('results_goal_pred.json', 'r') as f:
    pred = json.load(f)

sc_dict = {}



# build inverse map
for val in content['goal_dict'].values():
    scripts = val[1]
    for script_name in scripts:
        convert_name = script_name.split('record/')[1].replace('logs_agent_', '').replace('.json', '')
        if convert_name in sc_dict:
            pdb.set_trace()
        sc_dict[convert_name] = val[0]


# measure performance for every+prog
prog_perf = {}
prec_recall = {}
for prog_name in pred.keys():
    if prog_name not in sc_dict.keys():
        continue

    predicates_pred = pred[prog_name]
    predicates_gt =  sc_dict[prog_name]
    dictionary_predicates = {}

    for p in predicates_pred:
        dictionary_predicates[p[0]] = [p[1], 0]

    for p in predicates_gt.items():
        if p[0] in dictionary_predicates:
            oldp, _ = dictionary_predicates[p[0]]
            dictionary_predicates[p[0]] = [oldp, p[1]]
        else:
            dictionary_predicates[p[0]] = [0, p[1]]

    tp = sum([min(x[0], x[1]) for x in list(dictionary_predicates.values())])
    predc = sum([x[0] for x in list(dictionary_predicates.values())])
    posc = sum([x[1] for x in list(dictionary_predicates.values())])

    precision = tp*1./posc
    recall = tp*1./predc

    prec_recall[prog_name] = [precision, recall]



per_activity = {'total': []}


for prog in prec_recall:
    act_name = prog.split('init7_')[1].split('_50')[0]

    if act_name not in per_activity:
        per_activity[act_name] = []
    per_activity[act_name].append(prec_recall[prog])

    per_activity['total'].append(prec_recall[prog])


import numpy as snp

for task_name in per_activity:
    print(task_name)
    prec = np.mean([x[0] for x in per_activity[task_name]])
    rec = np.mean([x[1] for x in per_activity[task_name]])
    print('Precision', prec)
    print('Recall', rec)
pdb.set_trace()
    




pred_to_task_name = {}
for task_name, preds in content['task_name_to_predicates'].items():
    for predicates in preds:
        for predicate in predicates.split(','):
            pred_to_task_name[predicate.split('.')[0]] = task_name



predicted_task = []
for program, predicates in pred.items():
    first_pred = predicates[0][0]
    predicted_task.append(pred_to_task_name[first_pred])
    programs.append(program.split('/')[-1].split('_')[1:])