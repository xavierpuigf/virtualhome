import sys
import json


path_json = sys.argv[1]
query_help = '''
 Options:
    trace: sets trace
    name: return all the objects with class name 
    save: save the last result in a variable 
    node: prints things about this node in every step
    edges: check all the edges for an id
'''
with open(path_json, 'r') as f:
    graph = json.load(f)
variables = {}
curr_result = None
while(True):
    query = input('\n\nEnter one of the options or help (h):\n')
    if query == 'h':
        print(query_help)
    if query == 'name':
        class_name = input('Enter the class name\n')
        step_id = input('Enter a step\n')
        step_id = int(step_id)
        nodes = graph['graph_state_list'][step_id]['nodes']
        nodes_interest = [x for x in nodes if class_name in x['class_name']]
        curr_result = nodes_interest

    if query == 'node':
        node_id = input('Enter node id\n')
        steps = input('Enter step number, or all (-1)\n')
        node_id = int(node_id)
        steps = int(steps)
        if steps == -1:
            nodes = [graph['graph_state_list'][it]['nodes'] for it in range(len(graph['graph_state_list']))]
        else:
            nodes = [graph['graph_state_list'][steps]['nodes']]

        nodes = [nd for node_step in nodes for nd in node_step if nd['id'] == node_id]
        for it, node in enumerate(nodes):
            print(node)
        curr_results = nodes

    if query == 'edges':
        node_id = input('Enter node id that should appear in the edge\n')
        steps = input('Enter step number, or all (-1)\n')
        relation = input('Enter relation, or all possible (-1)\n')
        steps = int(steps)
        node_id = int(node_id)
        
        if steps == -1:
            edges = [graph['graph_state_list'][it]['edges'] for it in range(len(graph['graph_state_list']))]
        else:
            edges = [graph['graph_state_list'][steps]['edges']]

        edges = [nd for edge in edges for nd in edge if nd['from_id'] == node_id or nd['to_id'] == node_id]
        if relation != '-1':
            edge_id = [nd for edge in edges for nd in edge if nd['relation_type'] == relation]
        for it, edge in enumerate(edges):
            print(it, '------')
            print(edge)
        curr_results = edges

            

    if query == 'save':
        var_name = input('Enter the variable name to save this\n')
        variables[var_name] = last_results

    last_results = curr_result
    if query != 'h':
        print(last_results)
        print('type "curr_result" to inspect the last result, the graph is also saved in "graph"\n')

