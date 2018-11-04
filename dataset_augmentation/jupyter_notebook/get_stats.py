import json
import ipdb
import numpy as np
from collections import Counter
from glob import glob

# precond_path = glob('../programs_processed_precond_nograb_morepreconds/initstate/*/*.json')
# #precond_path = glob('*/initstate/*/*/*.json')
# print(len(precond_path))


# precond_str_list = []
# for path in precond_path:
#     precond_str = []
#     precond = json.load(open(path, 'r'))
#     for precond_i in precond:
#         for k, v in precond_i.items():
#             if k in ['is_off', 'is_on', 'closed', 'open', 'sitting', 'plugged', 'unplugged', 'free', 'occupied']:
#                 obj1 = v[0].lower().replace(' ', '_')
#                 precond_str.append('{}.{}'.format(obj1, k))
#             elif k in ['location', 'atreach', 'inside', 'in']:
#                 obj1 = v[0][0].lower().replace(' ', '_')
#                 obj2 = v[1][0].lower().replace(' ', '_')
#                 precond_str.append('{}.{}.{}'.format(obj1, k, obj2))
#             else:
#                 print(k)
#     precond_str_list.append(precond_str)


# def log(cnt, n):
#     if n < 0:
#         n = len(cnt)

#     total_n = sum([v for k, v in cnt.most_common(n)])
#     for i, (k, v) in enumerate(cnt.most_common(n)):
#         print('{}: {} ({:.2f}%)'.format(k, v, v/total_n*100.))
#         if i > 20: break
#     print('-'*30)


# precond_str_list = [i for l in precond_str_list for i in l]
# cnt = Counter(precond_str_list)
# log(cnt, -1)

# while True:
#     keyword = input("keywords: ")
#     #keyword = 'plate.location'
#     cnt = Counter([i for i in filter(lambda v: keyword in v, precond_str_list)])
#     log(cnt, 50)

def probs(orig_list):
    object_names = list(set([obj.split('.')[0] for obj in orig_list]))
    return_map = {}
    for obj in object_names:
        nlist = [x for x in orig_list if x.split('.')[0] == obj]
        cnt = Counter(nlist)
        n = len(cnt)
        total_n = sum([v for k, v in cnt.most_common(n)])
        for i, (k, v) in enumerate(cnt.most_common(n)):
            object_relation = k
            proportion = v/total_n*100.
            return_map[object_relation] = proportion
    return return_map


def get_stats(path_name):
    precond_path = glob(path_name)
    precond_str_list = []
    precond_str_title = {}
    for path in precond_path:
        precond_str = []
        precond = json.load(open(path, 'r'))
        program_name = path.replace('initstate', 'withoutconds').replace('.json', '.txt')
        with open(program_name, 'r') as f:
            lines = f.readlines()
            title = lines[0].strip()
        for precond_i in precond:
            for k, v in precond_i.items():
                if k in ['is_off', 'is_on', 'closed', 'open', 'sitting', 
                         'plugged', 'unplugged', 'free', 'occupied']:
                    obj1 = v[0].lower().replace(' ', '_')
                    precond_str.append('{}.{}'.format(obj1, k))
                elif k in ['location', 'atreach', 'inside', 'in']:
                    obj1 = v[0][0].lower().replace(' ', '_')
                    obj2 = v[1][0].lower().replace(' ', '_')
                    precond_str.append('{}.{}.{}'.format(obj1, k, obj2))
                else:
                    print(k)
        precond_str_list.append(precond_str)
        if title not in precond_str_title:
            precond_str_title[title] = []
        precond_str_title[title].append(precond_str)

    precond_str_list = [i for l in precond_str_list for i in l]
    precond_str_title = {titlename: [i for l in value for i in l] for titlename, value in precond_str_title.items()}

    # Compute distribution per list and per title
    precond_str_list_distr = probs(precond_str_list)
    precond_str_title_distr = {title: probs(values) for title, values in precond_str_title.items()} 
    return precond_str_list_distr, precond_str_title_distr, list(precond_str_title_distr)

def distance_program_titles(stats1, stats2):
    # Computes the distance between programs from 2 titles
    objects_intersection = set(list(stats1)).intersection(set(list(stats2)))
    if len(objects_intersection) < 4:
        return -1

    v1 = [stats1[x]/100. for x in objects_intersection]
    v2 = [stats2[x]/100. for x in objects_intersection]

    return (np.linalg.norm(np.array(v1) - np.array(v2)))/len(objects_intersection)

