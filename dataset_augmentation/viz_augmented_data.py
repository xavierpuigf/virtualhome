import glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import ipdb
import json
import os

original_dir = 'programs_processed_precond_nograb_morepreconds'
programs = glob.glob('{}/withoutconds/*/*.txt'.format(original_dir))
print(len(programs))
instr_to_id = {}

def printProgram(script, color):
    return ''

def createHist(data, xlabel, title, imgname, nbins=20):
    # Data is a list of elements
    plt.figure()
    n, bins, patches = plt.hist(data, nbins)
    plt.xlabel(xlabel)
    plt.ylabel('Programs')
    plt.title(title)
    plt.savefig(imgname)

def parseProg(prog):
    result = []
    for elem_l in prog:
        elem = elem_l.strip()
        if elem not in instr_to_id:
            instr_to_id[elem] = len(list(instr_to_id))+1
        result.append(instr_to_id[elem])
    return result

def computeLCS(prog1, prog2):
    # parse the programs
    X = parseProg(prog1)
    Y = parseProg(prog2)
    m = len(X)
    n = len(Y)
    
    # declaring the array for storing the dp values
    L = [[None]*(n+1) for i in range(m+1)]
    longest_L = [[[]]*(n+1) for i in range(m+1)]
    prev_p2 = [[[]]*(n+1) for i in range(m+1)]
    longest = 0
    lcs_set = []

    for i in range(m+1):
        for j in range(n+1):
            if i == 0 or j == 0 :
                L[i][j] = 0
                longest_L[i][j] = []
            elif X[i-1] == Y[j-1]:
                L[i][j] = L[i-1][j-1]+1
                longest_L[i][j] = longest_L[i-1][j-1] + [X[i-1]]
                prev_p2[i][j] = prev_p2[i-1][j-1] + [j-1]
                
                if L[i][j] > longest:
                    lcs_set = []
                    lcs_set.append(longest_L[i][j])
                    longest = L[i][j]
                elif L[i][j] == longest and longest != 0:
                    lcs_set.append(longest_L[i][j])
            else:
                if L[i-1][j] > L[i][j-1]:
                    L[i][j] = L[i-1][j]
                    prev_p2[i][j] = prev_p2[i-1][j]
                    longest_L[i][j] = longest_L[i-1][j]
                else:
                    L[i][j] = L[i][j-1]
                    longest_L[i][j] = longest_L[i][j-1]
                    prev_p2[i][j] = prev_p2[i][j-1]

    if len(lcs_set) == 0:
        return 0., [0]*n 
    else:
        return len(lcs_set[0])*1./max(n,m), prev_p2[-1][-1] 

program_sim = {}
names = ['affordance', 'location', 'program_exception']
sim_file = 'similarity_info.json'
stats = {'LCS': {}, 'Lengths': {}, 'Distr': {}}
for name in names + ['initial', 'total']:
    stats['LCS'][name] = [[], []] # all, exec
    stats['Lengths'][name] = [[], []]
    stats['Distr'][name] = [{}, {}]

# Executable info
with open('../executable_info.json', 'r') as f:
    executable_info = json.load(f)

#if not os.path.isfile(sim_file):
if True:
    for program_name in programs:
        if ('dataset_augmentation/'+program_name in executable_info and 
            'Script is executable' in executable_info['dataset_augmentation/'+program_name]):
            is_executable = True
        else:
            is_executable = False
        with open(program_name, 'r') as f:
            lines = f.readlines()
            title = lines[0]
            program = lines[4:]
        preconds = json.load(open(program_name.replace('.txt', '.json').replace('withoutconds', 'initstate/'), 'r'))
        
        indices_to_collect_stats = [0]
        if is_executable: indices_to_collect_stats.append(1)
        
        for nm in ['initial', 'total']:
            for indi in indices_to_collect_stats:
                if title not in stats['Distr'][nm][indi].keys(): 
                    stats['Distr'][nm][indi][title] = 0
                stats['Distr'][nm][indi][title] += 1
                stats['Lengths'][nm][indi].append(len(program))

        script_similar = {}
        for it, name in enumerate(names):
            script_similar[name] = []
            new_dir = program_name.replace(original_dir, 'augmented_{}'.format(name)).replace('.txt', '/')
            new_progs = glob.glob('{}/*.txt'.format(new_dir))
            for new_prog in new_progs:
                with open(new_prog, 'r') as f:
                    lines = f.readlines()
                    newprogram = lines[4:]
                cond_file = new_prog.replace('withoutconds', 'initstate').replace('txt', 'json')
                print(cond_file)
                newcond = json.load(open(cond_file, 'r'))
                lcs, match = computeLCS(program, newprogram)
                script_similar[name].append([lcs, match, newprogram, newcond])
            script_similar[name] = sorted(script_similar[name], key=lambda x: -x[0])

            for nm in ['total', name]:
                for indi in indices_to_collect_stats:
                    if title not in stats['Distr'][nm][indi].keys(): 
                        stats['Distr'][nm][indi][title] = 0
                    stats['Distr'][nm][indi][title] += len(script_similar[name])
                    stats['Lengths'][nm][indi] += [len(ss[2]) for ss in script_similar[name]]
                    stats['LCS'][nm][indi] += [ss[0] for ss in script_similar[name]]


        program_sim[program_name] = [title, program, script_similar, is_executable, preconds]

    with open(sim_file, 'w+') as f:
        f.write(json.dumps(program_sim, indent=4))

# Generate histograms
nameexec = ['all', 'exec']
for nm in names+['total', 'initial']:
    for it in range(2):
        distribution = stats['Distr'][nm][it]
        elems = distribution.items()
        elems = sorted(elems, key=lambda x: -x[1])
        elems = elems[:25]
        conts = [x[1] for x in elems]
        tnames = [x[0] for x in elems]
        plt.figure()
        plt.plot(tnames, conts)
        plt.xticks(range(len(tnames)), tnames, rotation='vertical')
        plt.tight_layout()


        plt.savefig('viz/distr_{}_{}.png'.format(nm, nameexec[it]))

    createHist(stats['Lengths'][nm][0], 'Program Length', 
               '{} all'.format(nm), 'viz/len_{}_all'.format(nm))
    createHist(stats['Lengths'][nm][1], 'Program Length', 
               '{} exec'.format(nm), 'viz/len_{}_exec'.format(nm))
for nm in names:
    createHist(stats['LCS'][nm][0], 'LCS', 'LCS {} all'.format(nm), 
               'viz/LCS_{}_all'.format(nm))
    createHist(stats['LCS'][nm][1], 'LCS', 'LCS {} exec'.format(nm), 
               'viz/LCS_{}_exec'.format(nm))


sim_info = json.load(open(sim_file, 'r')) 
nprogs = {}
for it, st in stats['Distr'].items():
    tuples = [(-t, name, t) for name, t in stats['Distr'][it][0].items()]
    tuples_exec = [(-t, name, t) for name, t in stats['Distr'][it][1].items()]
    progs = 0 
    for t in tuples:
        progs += t[2]
    progs_exec = 0 
    for t in tuples_exec:
        progs_exec += t[2]

    nprogs[it] = [progs, progs_exec]
    
stats = {
    'all_progs': nprogs,
    'distr': stats
}
with open('data.js', 'w+') as f:
    f.write('var stats = {};\n var data = {}'.format(
        json.dumps(stats), 
        json.dumps({x: sim_info[x] for x in list(sim_info)[::5]}, indent=4)))


