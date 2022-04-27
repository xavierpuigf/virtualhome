import json
import os
from tqdm import tqdm

def get_syn(cname, namequiv):
	if cname in namequiv:
		return namequiv[cname]

	return []

def transf(name):
	return name.replace(" ", "").replace("_", "")

cfile = os.path.dirname(os.path.abspath(__file__))

with open(f'{cfile}/../resources/properties_data.json', 'r') as f:
	prop_data = json.load(f)

with open(f'{cfile}/../resources/class_name_equivalence.json', 'r') as f:
	cname_equiv = json.load(f)


# Build nameequiv
nameequiv = {}
for name_e in cname_equiv:
	nameequiv[transf(name_e)] = [transf(ne) for ne in cname_equiv[name_e]]

prop_data_all = {}
for pname in tqdm(prop_data):
	properties = prop_data[pname]
	classname = pname.lower().replace("_", "")
	prop_data_all[classname] = properties
	cnamered = classname.replace(" ", "")
	synonims = get_syn(classname, nameequiv)
	for namesyn in synonims:
		prop_data_all[namesyn] = properties
	if cnamered != classname:
		prop_data_all[cnamered] = properties
		cnamesyn = get_syn(cnamered, nameequiv)
		for cnamesyn in synonims:
			prop_data_all[cnamesyn] = properties

print(len(prop_data_all))
with open(f'{cfile}/../resources/properties_data_all.json', 'w+') as f:
	f.write(json.dumps(prop_data_all, indent=4))