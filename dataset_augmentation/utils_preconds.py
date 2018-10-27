import pdb
import json
object_properties = json.load(open('../resources/object_script_properties_data.json', 'r'))


def hasProperty(obj_name, property_name):
    obj_name_corrected = obj_name.lower().replace(' ', '_')
    return property_name in object_properties[obj_name_corrected]


def insertInstructions(insert_in, contentold):
    content = contentold.copy()
    acum = 0
    for insertval in insert_in:
        content.insert(insertval[0]+acum, insertval[1])
        acum += 1
    return content

def removeInstructions(to_delete, content):
	return [x for i, x in enumerate(content) if i not in to_delete]

class Precond:
    def __init__(self):
        self.precond_dict = {}

    def addPrecond(self, cond, obj1, obj2):
        if cond not in self.precond_dict.keys():
            self.precond_dict[cond] = {}
        if obj1 not in self.precond_dict[cond]:
            
            self.precond_dict[cond][obj1] = set(obj2)
        else:
            # self.precond_dict[cond][obj1] = set(list(self.precond_dict[cond][obj1])+list(obj2))
            if len(self.precond_dict[cond][obj1]) == 0:
                self.precond_dict[cond][obj1] = set(obj2)
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
                    if len(self.precond_dict[cond][it]) > 1:
                        pdb.set_trace()
                    if len(self.precond_dict[cond][it]) == 0:
                        conds.append({cond: it_lowercase})
                    else:
                        elements = list(self.precond_dict[cond][it])[0]
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
