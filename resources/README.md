## Resources
Contains files used to initialize each environment and execute programs in them. Their contents are.

### Class name equivalence (`class_name_equivalence.json`)

This file contains a dictionary mapping from names occurring in scripts to "equivalent" names (class_name) found in Unity scenes. For example,

`"fruit": ["watermelon", "apple", "banana"]`

means that for

`[Find] <fruit> (1)`

executor will choose between objects named fruit, watermelon, apple, or banana.

Note that adding keys to value list is not necessary (i.e., `"fridge": ["fridge"]` or `"fruit": ["fruit", "watermelon", "apple", "banana"]`)
since this is done automatically.

### Object properties (`object_properties.json`)

This file contains a dictionary mapping from object names to their properties, see [../simulation/README.md](../simulation/README.md) enum class for a list of all
supported properties. Example:

`"oven": ["CAN_OPEN", HAS_SWITCH", CONTAINERS", HAS_PLUG"]`

### Object properties (`object_properties.json`)

This file contains a dictionary mapping from object names to states they can have, see [../simulation/README.md](../simulation/README.md) enum class for a list of all
supported states.


### Object placing (`object_script_placing.json`)

This file contains a dictionary from object names to a list of their possible placings. A placing is defined as a dictionary with keys 

* `destination`: specifies a destination object
* `relation`: either "ON" or "INSIDE"
* `room`: room name where the desination object must occur (or null for object in any room) 

Example

```json
{
	"juice": [{
		"destination": "kitchen_counter",
		"relation": "ON",
		"room": null
	},
	{
		"destination": "table",
		"relation": "ON",
		"room": "kitchen"
	}]
}
```

