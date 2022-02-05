# LexTools
Collection of generally useful code

- **python/LexTools** - general python tools
- **bashTools.sh** - tools for bash scripts and bash CLI
- **cppTools.h** - general cpp tools 

# Bash
To add functions into any bash shell, run
```bash
source ~/LexTools/bashTools.sh
```

# Python
## Python tools
I am not interested in making this package installable right now so add the `python/` directory to PYTHONPATH or run
```
source ~/LexTools/python/add_to_python_path.sh
```
Then you can import LexTools like any other package
```
import LexTools
```

## Testing
**Python**
To run unit tests on python tools, run `pytest` inside `python/`.
This requires installing pytest package.

**Bash**
Use `shunit`

# ATLAS Tools
Some of the ROOT functionality requires setting up `atlasrootstyle`. In the same directory containing LexTools, run
```bash
git clone ssh://git@gitlab.cern.ch:7999/alarmstr/AtlasRootStyle.git
cd AtlasRootStyle
git remote add upstream ssh://git@gitlab.cern.ch:7999/atlas-publications-committee/atlasrootstyle.git
cd ..
```

