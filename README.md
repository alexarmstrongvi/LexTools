# LexTools
Collection of generally useful code

- **ATLAS_sw/** - helpful scripts for tools that require setupATLAS
- **bashTools/** - tools for bash scripts and bash CLI
- **cppTools/** - general cpp tools 
- **pyRootTools** - python tools that require "import ROOT"
- **pyTools** - general python tools
- **rootTools/** - cpp tools that use ROOT 

Some of the ROOT functionality requires setting up `atlasrootstyle`. In the same directory containing LexTools, run
```bash
git clone ssh://git@gitlab.cern.ch:7999/alarmstr/AtlasRootStyle.git
cd AtlasRootStyle
git remote add upstream ssh://git@gitlab.cern.ch:7999/atlas-publications-committee/atlasrootstyle.git
cd ..
```
