u"""
Script for exporting mesh from Salome to Elmer
"""
# ******************************************************************************
#
#    Copyright (C) 2017-, Juris Vencels
#
#    Authors: Juris Vencels
#    Email:   juris.vencels@gmail.com
#    Web:     http://vencels.com
#    Address: University of Latvia
#             Laboratory for mathematical modelling of 
#                 environmental and technological processes
#             Zellu Str. 23, Riga, LV-1002, Latvia
#
#    Original Date: 05.05.2017
#
#    This script is based on salomeToOpenFOAM.py written by Nicolas Edh
#    https://github.com/nicolasedh/salomeToOpenFOAM
#
# *****************************************************************************
#
#    This script is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    salomeToElmer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program (in the file LICENSE); if not, write to the 
#    Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, 
#    Boston, MA 02110-1301, USA.
#

import sys
import SMESH
from salome.smesh import smeshBuilder
import os,time

def exportToElmer(mesh,dirname='salomeToElmer'):
    u"""
    Elmer's native mesh consists of 5 files.

    mesh.header - first line (# nodes, # all elements, # edge and boundary elements)
                  second line (# element types)
                  third and all following lines (type, # elements of this type)

    mesh.names - body and boundary names with their IDs taken from Salome mesh groups.
                 The last 'empty' belongs to edge and boundary elements that do not
                 belong to user specified groups. 

    mesh.nodes - every line represents one node (node ID, dummy, X, Y, Z)

    mesh.elements - every line represents one volume element (volume element ID,
                    body ID, type, node1, node2, node3, ...)

    mesh.boundary - every line represents one edge or boundary element (edge or 
                    boundary element ID, boundary ID, parent volume element 1, 
                    parent volume element 2, type, node1, node2, ...)
    """
    tstart=time.time()

    if not os.path.exists(dirname):
        os.makedirs(dirname)
    try:
        fileHeader   = open(dirname + "/mesh.header",'w')
        fileNodes    = open(dirname + "/mesh.nodes",'w')
        fileNames    = open(dirname + "/mesh.names",'w')
        fileElements = open(dirname + "/mesh.elements",'w')
        fileBoundary = open(dirname + "/mesh.boundary",'w')
    except Exception:
        print "ERROR: Cannot open files for writting"
        return

    # mesh.header
    fileHeader.write("%d %d %d\n" \
        %(mesh.NbNodes(),mesh.NbVolumes(),mesh.NbEdges()+mesh.NbFaces()))

    elems = {str(k): v for k, v in mesh.GetMeshInfo().items() if v}
    fileHeader.write("%d\n" %(len(elems.values())-1))

    elemTypeNames = {'202': 'Entity_Edge', '303': 'Entity_Triangle', \
                     '404': 'Entity_Quadrangle', '504': 'Entity_Tetra', \
                     '605': 'Entity_Pyramid', '706': 'Entity_Hexagonal_Prism', \
                     '808': 'Entity_Hexa'}

    for nbr, ele in sorted(elemTypeNames.items()):
        if elems.get(ele):
            fileHeader.write("%s %d\n" %(nbr,elems.get(ele)))

    fileHeader.flush()
    fileHeader.close()

    # mesh.nodes
    points=mesh.GetElementsByType(SMESH.NODE)
    for ni in points:
        pos=mesh.GetNodeXYZ(ni)
        fileNodes.write("%d -1 %.12g %.12g %.12g\n" %(ni,pos[0],pos[1],pos[2]))
    fileNodes.flush()
    fileNodes.close()

    # initialize arrays
    invElemType = {v: k for k, v in elemTypeNames.items()}
    invElemIDs = [mesh.NbGroups()+1 for el in range(mesh.NbElements())]
    elemGrp = list(invElemIDs)

    edgeIDs = mesh.GetElementsByType(SMESH.EDGE)
    faceIDs = mesh.GetElementsByType(SMESH.FACE)
    volumeIDs = mesh.GetElementsByType(SMESH.VOLUME)

    elemIDs = edgeIDs + faceIDs + volumeIDs
    NbEdgesFaces = mesh.NbEdges() + mesh.NbFaces()

    if len(elemGrp) != max(elemIDs):
        raise Exception("ERROR: the number of elements does not match!")

    for el in range(mesh.NbElements()):
        invElemIDs[elemIDs[el]-1] = el+1

    # mesh.names
    fileNames.write("! ----- names for bodies -----\n")
    groupID = 1

    for grp in mesh.GetGroups(SMESH.VOLUME):
        fileNames.write("$ %s = %d\n" %(grp.GetName(), groupID))
        for el in grp.GetIDs():
            elemGrp[invElemIDs[el-1]-1] = groupID
        groupID = groupID + 1

    fileNames.write("! ----- names for boundaries -----\n")

    for grp in mesh.GetGroups(SMESH.FACE):
        fileNames.write("$ %s = %d\n" %(grp.GetName(), groupID))
        for el in grp.GetIDs():
            if elemGrp[invElemIDs[el-1]-1] > groupID:
                elemGrp[invElemIDs[el-1]-1] = groupID
        groupID = groupID + 1

    fileNames.write("$ empty = %d\n" %(mesh.NbGroups()+1))

    fileNames.flush()
    fileNames.close()

    # mesh.elements
    for el in mesh.GetElementsByType(SMESH.VOLUME):
        elemType = mesh.GetElementGeomType(el)
        elemTypeNbr = int(invElemType.get(str(elemType)))
        fileElements.write("%d %d %d" %(invElemIDs[el-1]-NbEdgesFaces, \
                                        elemGrp[invElemIDs[el-1]-1],elemTypeNbr))
        for nid in mesh.GetElemNodes(el):
            fileElements.write(" %d" %(nid))
        fileElements.write("\n")

    fileElements.flush()
    fileElements.close()

    # mesh.boundary
    for el in elemIDs[:NbEdgesFaces]:
        elemType = mesh.GetElementGeomType(el)
        elemTypeNbr = int(invElemType.get(str(elemType)))

        x,y,z = mesh.BaryCenter( el )
        parents = mesh.FindElementsByPoint( x,y,z, SMESH.VOLUME )

        if len(parents) is 2:
            fileBoundary.write("%d %d %d %d %d" \
                %(invElemIDs[el-1],elemGrp[invElemIDs[el-1]-1], \
                  invElemIDs[parents[0]-1]-NbEdgesFaces, \
                  invElemIDs[parents[1]-1]-NbEdgesFaces,elemTypeNbr))
        else:
            fileBoundary.write("%d %d %d 0 %d" \
                %(invElemIDs[el-1],elemGrp[invElemIDs[el-1]-1], \
                  invElemIDs[parents[0]-1]-NbEdgesFaces,elemTypeNbr))

        for nid in mesh.GetElemNodes(el):
            fileBoundary.write(" %d" %(nid))
        fileBoundary.write("\n")

    fileBoundary.flush()
    fileBoundary.close()

    print "Done exporting!\n"
    print "Total time: %0.f s\n" %(time.time()-tstart)


def findSelectedMeshes():
    meshes=list()
    smesh = smeshBuilder.New(salome.myStudy)
    nrSelected=salome.sg.SelectedCount() # total number of selected items
    
    foundMesh=False
    for i in range(nrSelected):
        selected=salome.sg.getSelected(i)
        selobjID=salome.myStudy.FindObjectID(selected)
        selobj=selobjID.GetObject()
        if selobj.__class__ == SMESH._objref_SMESH_Mesh or \
                selobj.__class__ == salome.smesh.smeshBuilder.meshProxy :
            mName=selobjID.GetName().replace(" ","_")
            foundMesh=True
            mesh=smesh.Mesh(selobj)
            meshes.append(mesh)

    if not foundMesh:
        print "ERROR: Mesh is not selected"
        return list()
    else:
        return meshes


def main():
    u""" 
    Export selected meshes
    """
    meshes=findSelectedMeshes()
    for mesh in meshes:
        if not mesh == None:
            mName=mesh.GetName()
            outdir=os.getcwd()+"/"+mName
            print "Exporting mesh to " + outdir + "\n"           
            exportToElmer(mesh,outdir)
            
    
if __name__ == "__main__":
    main()
