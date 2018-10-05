# Document for the rules of the transition


## Template

### ExampleExecutor
- scrip: action object1 object2
- Pre-condition: 
- Post-condition:
    - remove/add undirected edges:
    - remove/add directed edges:
    - state changes:

### FindExecutor
- script: Find `object`
- Pre-condition: `character` is close to `object`
- Post-condition:
    - add undirected edges: `character`, close to, `object`

### WalkExecutor
- script: Walk `object`
- Pre-condition: `character` is not `sitting`
- Post-condition:
    - remove undirected edges: `character` inside `any_node`, `character` close to `any_nodes`, `character` face `any_nodes`
    - add undirected edges: `character` close to object_contain(`object`) [Need to be verified]
    - add directed edges: `character` inside room_of(`object`)
    - add undirected edges: `character` close to `object`

### SitExecutor
- script: sit `object`
- Pre-condition: `character` close to `object`, `character` is not sitting, `object` is `sittable`
- Post-condition: 
    - add directed edges: `character` on `object`
    - state changes: `character` sitting

### StandUpExecutor
- script: standup
- Pre-condition: `character` is sitting
- Post-condition: `character` not sitting

### GrabExecutor
- script: grab `object`
- Pre-condition: `object` is grabbable, `character` close to object, `object` in another `object2` except room _and_ `object2` is not close, `one_of_hand` is free
- Post-condition: 
    - remove directed and undirected edges: `object` all_relation `any_node`
    - add directed edges: `character` hold `object`
    - add undirected edges: `character` close to one_of_node(`object`, relation=on/inside/close to)object *(not sure)*

### OpenExecutor
- script: open `object`
- Pre-condition: `object` is openable, `character` close to `object`, `one_of_hand` is free, `object` is closed
- Post-condition:
    - state changes: `object` not closed, `object` open

### CloseExecutor (shared with OpenExecutor)
- script: open `object`
- Pre-condition: `object` is openable, `character` close to `object`, `one_of_hand` is free, `object` is open
- Post-condition:
    - state changes: `object` not open, `object` closed

### PutExecutor
- script: put on `object1` `object2`
- Pre-condition: `one_of_hand` hold `object1`, `character` close to `object2`
- Post-condition:
    - remove directed edges: `character` holds `object1`
    - add undirected edges: `character` close to `object2`
    - add directed edges: `object1` on `object2`

### PutInExecutor
- script: put in `object1` `object2`
- Pre-condition: `one_of_hand` hold `object1`, `character` close to `object2`, (`object2` is not opennable or `object2` is open)
- Post-condition:
    - remove directed edges: `character` holds `object1`
    - add undirected edges: `character` close to `object2`
    - add directed edges: `object1` inside `object2`

### SwitchOnExecutor
- script: switch on `object`
- Pre-condition: `object` has_switch, `character` close to `object`, `one_of_hand` is free, `object` is off
- Post-condition: 
    - state changes: `object` not off, `object` is on

### SwitchOffExecutor
- script: switch off `object`
- Pre-condition: `object` has_switch, `character` close to `object`, `one_of_hand` is free, `object` is on
- Post-condition: 
    - state changes: `object` not on, `object` is off

### DrinkExecutor
- script: drink `object`
- Pre-condition: `object` is drinkable, `one_of_hand` hold `object`
