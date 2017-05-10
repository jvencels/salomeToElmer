# salomeToElmer
This is a script for exporting mesh from Salome to Elmer.

* **Salome** (http://www.salome-platform.org/) is an open-source pre- and postprocessing platform. In my opinion it is the best free meshing platform available.

* **Elmer** (https://www.csc.fi/web/elmer) is an open source multiphysical simulation software. 

This script is based on *salomeToOpenFOAM.py* written by Nicolas Edh
https://github.com/nicolasedh/salomeToOpenFOAM

## Why you might need this script?
Typically users export Salome mesh in *.unv* format and then import it into Elmer. The problem is that *.unv* format does not support pyramids (5 nodal elements). These elements typically arise in mixed tetra and hexa 3D meshes. *salomeToElmer* script exports mesh directly to Elmer's native mesh.* format.

## Requirements
Tested on Ubuntu 14.04. and Salome 8.2.0

## How to
* Select mesh you want to export
* File -> Load Script...
* Select *salomeToElmer.py*
