# Tools: Unit Conversions

This library contains unit conversion functions that can be used in any project script.

## Project structure

```text
code/
├── tools/
│   └── unit_conversions.py
├── Propulsion/
│   └── power_estimate.py
└── other folders/
    └── your_script.py
```

## How to use

At the beginning of your Python script, **copy and paste the following code**:

```python

######################################################
import sys
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / "tools").is_dir():
        sys.path.append(str(parent))
        break

from tools.unit_conversions import *
from tools.reusable_functions import *
#######################################################

```

That's it!

You can now use the conversion functions directly in your code. If new files are added to tools, you may also import them by adding :
```python
from tools.new_file import *
#######################################################

```

For example:

```python
speed = knots_to_mps(100)
distance = ft_to_m(300)
```

## Important

- Keep the `tools` folder and `unit_conversions.py` in their original locations.
- Add the code above to every script that uses the conversion functions.
- Make sure you have pulled the latest project files from GitHub.