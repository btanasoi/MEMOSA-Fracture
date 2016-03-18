
import string
from mpi4py import MPI
from numpy import *
import pdb

tectype = {
        'tri' : 'FETRIANGLE',
        'quad' : 'FEQUADRILATERAL',
        'tetra' : 'FETETRAHEDRON',
        'hexa' : 'FEBRICK'
        }

def dumpTecplotEntireFractureDomain(nmesh, meshesLocal, meshesGlobal, mtype, tFields,file_name, title_name,Total_count):
  #cell sites
  cellSites = []
  for n in range(0,nmesh):
     cellSites.append( meshesGlobal[n].getCells() )

  #face sites
  faceSites = []
  for n in range(0,nmesh):
     faceSites.append( meshesGlobal[n].getFaces() )

  #node sites
  nodeSites = []
  for n in range(0,nmesh):
     nodeSites.append( meshesGlobal[n].getNodes() )

  #get connectivity (faceCells)
  faceCells = []
  for n in range(0,nmesh):
     faceCells.append( meshesGlobal[n].getConnectivity( faceSites[n], cellSites[n] ) )
 
  #get connectivity ( cellNodes )
  cellNodes = []
  for n in range(0,nmesh):
     cellNodes.append( meshesGlobal[n].getCellNodes() )

  #coords
  coords = []
  for n in range(0,nmesh):
     coords.append( meshesGlobal[n].getNodeCoordinates().asNumPyArray() )
 
  cellSitesLocal = []
  for n in range(0,nmesh):
     cellSitesLocal.append( meshesLocal[n].getCells() )

  fractureFields = []
  for n in range(0,nmesh):
     fractureFields.append( tFields.phasefieldvalue[cellSitesLocal[n]].asNumPyArray() )    


  fracturegradFields = []
  for n in range(0,nmesh):
     fracturegradFields.append( tFields.phasefieldGradient[cellSitesLocal[n]].asNumPyArray() )

	   
  #opening global Array 
  fractureFieldGlobal = []
  fracturegradFieldGlobal = []

  for n in range(0,nmesh):
    selfCount = cellSites[n].getSelfCount()
    fractureFieldGlobal.append( zeros((selfCount,1), float) ) #if it is velocoity (selfCount,3) 
    fracturegradFieldGlobal.append( zeros((selfCount,3), float) ) #if it is velocity (selfCount,3)
    meshLocal = meshesLocal[n]
    localToGlobal = meshLocal.getLocalToGlobalPtr().asNumPyArray()
    tFieldGlobal  = fractureFieldGlobal[n]
    tgradFieldGlobal  = fracturegradFieldGlobal[n]  
    tFieldLocal   = fractureFields[n]
    tgradFieldLocal   = fracturegradFields[n]
    #fill local part of cells
    selfCount = cellSitesLocal[n].getSelfCount()
    for i in range(0,selfCount):
       globalID               = localToGlobal[i]
       tFieldGlobal[globalID] = tFieldLocal[i]
       tgradFieldGlobal[globalID] = tgradFieldLocal[i]
    MPI.COMM_WORLD.Allreduce(MPI.IN_PLACE, [tFieldGlobal,MPI.DOUBLE], op=MPI.SUM)
    MPI.COMM_WORLD.Allreduce(MPI.IN_PLACE, [tgradFieldGlobal,MPI.DOUBLE], op=MPI.SUM)    
  if MPI.COMM_WORLD.Get_rank() == 0:
     f = open(file_name, 'a')

     f.write("Title = \" tecplot mesh \" \n")
     f.write("variables = \"x\", \"y\", \"z\", \"PhaseFieldValue\" \n")
     for n in range(0,nmesh):
        ncell  = cellSites[n].getSelfCount()
        nnode  = nodeSites[n].getCount()
        f.write("Zone T = \"%s\" N = %s E = %s DATAPACKING = BLOCK, VARLOCATION = ([4-20]=CELLCENTERED), ZONETYPE=%s\n" %
               (title_name,  nodeSites[n].getCount(), ncell, tectype[mtype])) 
        f.write("StrandID=1, SolutionTime="+str(Total_count)+"\n")       
        #write x
        for i in range(0,nnode):
          f.write(str(coords[n][i][0])+"    ")
	  if ( i % 5 == 4 ):
	     f.write("\n")
        f.write("\n")	  
     
        #write y
        for i in range(0,nnode):
           f.write(str(coords[n][i][1])+"    ")
           if ( i % 5 == 4 ):
	      f.write("\n")
        f.write("\n")	  

        #write z
        for i in range(0,nnode):
           f.write(str(coords[n][i][2])+"    ")
           if ( i % 5 == 4 ):
	      f.write("\n")
        f.write("\n")	 

        #write phasefieldvalue 
        tFieldGlobal = fractureFieldGlobal[n]
        for i in range(0,ncell):
           f.write( str(tFieldGlobal[i][0]) + "    ")
	   if ( i % 5  == 4 ):
	      f.write("\n")
        f.write("\n")

        #connectivity
        for i in range(0,ncell):
           nnodes_per_cell = cellNodes[n].getCount(i)
           for node in range(0,nnodes_per_cell):
	      f.write( str(cellNodes[n](i,node)+1) + "     ")
           f.write("\n")
	
        f.close()

