import glob
import ipdb
import json
import os

original_dir = 'programs_processed_precond_nograb_morepreconds'
programs = glob.glob('{}/withoutconds/*/*.txt'.format(original_dir))
print(len(programs))
names = ['affordance_programs', 'location', 'program_exception']
instr_to_id = {}

def printProgram(script, color):
    return ''

def parseProg(prog):
    result = []
    for elem_l in prog:
        elem = elem_l.strip()
        elem = elem.lower().replace(' ', '_')
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
sim_file = 'similarity_info.json'
stats = [{}, {}, {}, {}, {}]
#if not os.path.isfile(sim_file):
if True:
    for program_name in programs:
        with open(program_name, 'r') as f:
            lines = f.readlines()
            title = lines[0]
            program = lines[4:]
        
        if title not in stats[0].keys(): stats[0][title] = 0
        stats[0][title] += 1
        script_similar = []
        for it, name in enumerate(names):
            script_similar.append([])
            new_dir = program_name.replace(original_dir, 'augmented_{}'.format(name)).replace('.txt', '/')
            new_progs = glob.glob('{}/*.txt'.format(new_dir))
            for new_prog in new_progs:
                with open(new_prog, 'r') as f:
                    lines = f.readlines()
                    newprogram = lines[4:]
                lcs, match = computeLCS(program, newprogram)
                script_similar[it].append([lcs, match, newprogram])
            script_similar[it] = sorted(script_similar[it], key=lambda x: -x[0])
            if title not in stats[-1].keys():
                stats[-1][title] = 0
            if title not in stats[it+1].keys():
                stats[it+1][title] = 0

            stats[it+1][title] += len(new_progs)
            stats[-1][title] += len(new_progs)

        program_sim[program_name] = [title, program, script_similar]

    with open(sim_file, 'w+') as f:
        f.write(json.dumps(program_sim, indent=4))

sim_info = json.load(open(sim_file, 'r')) 
nprogs = []
for it, st in enumerate(stats):
    tuples = [(-t, name, t) for name, t in stats[it].iteritems()]
    progs = 0 
    for t in tuples:
        progs += t[2]
    nprogs.append(progs)
    
stats = {
    'all_progs': nprogs,
    'distr': stats
}
with open('data.js', 'w+') as f:
    f.write('var stats = {};\n var data = {}'.format(json.dumps(stats), json.dumps(sim_info, indent=4)))

