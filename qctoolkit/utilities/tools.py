from math import pi ,sin, cos, ceil
from qctoolkit.molecule import Molecule
import numpy as np
import qctoolkit as qtk
import yaml
import pickle
import hashlib
import copy

def Molecules(file_name, **kwargs):
  """read nested xyz file and return molecule list"""
  xyz = open(file_name, 'r')
  content = xyz.readlines()
  content = [line.replace('\t', ' ') for line in content]
  xyz.close()

  itr = 0
  more_data = True
  mols = []

  while more_data:
    try:
      N = int(content[itr])
      prop_list = content[itr + 1]
      try:
          prop_list = np.array(prop_list.split(' ')).astype(float)
      except Exception as err:
          qtk.warning(str(err))
          prop_list = prop_list
      coord_list = content[itr + 2 : itr + N + 2]
      coord = [filter(None,[a for a in entry.split(' ')])
               for entry in coord_list]
      type_list = list(np.array(coord)[:,0])
      type_list = [str(elem) for elem in type_list]
      Z = np.array([qtk.n2Z(elem) for elem in type_list])
      R = np.array(coord)[:,1:4].astype(float)
      mol_data = {}
      for var in ['N', 'type_list', 'Z', 'R']:
        mol_data[str(var)] = eval(var)
      itr += N + 2
      mols.append(qtk.Molecule(molecule_data = mol_data))
    except Exception as err:
      qtk.progress(
        "Molecules", 
        "%d molecules have been loaded with message %s." % (len(mols), str(err))
      )
      more_data = False
      

  return mols

def primitiveCell(symmetry):
  if symmetry == 'fcc':
    return 0.5 * np.array([
      [0, 1, 1],
      [1, 0, 1],
      [1, 1, 0],
    ])
  elif symmetry == 'bcc':
    return 0.5 * np.array([
      [-1,  1,  1],
      [ 1, -1,  1],
      [ 1,  1, -1],
    ])
  else:
    qtk.warning('symmetry %s not found' % symmetry)
    return np.ones(3)

def scale2cart(cell_vec, R_scale):

  assert len(cell_vec) == 3
  assert len(cell_vec[0]) == 3

  R_cart = []
  for R_s in np.asarray(R_scale):
    R_cart.append(
      np.sum(R_s[:, np.newaxis] * np.asarray(cell_vec), axis=0).tolist()
    )
  return np.asarray(R_cart)

def md5sum(fname):
  def hash_bytestr_iter(bytesiter, hasher, ashexstr=True):
      for block in bytesiter:
          hasher.update(block)
      return (hasher.hexdigest() if ashexstr else hasher.digest())
  
  def file_as_blockiter(afile, blocksize=65536):
      with afile:
          block = afile.read(blocksize)
          while len(block) > 0:
              yield block
              block = afile.read(blocksize)
  
  out = hash_bytestr_iter(
    file_as_blockiter(open(fname, 'rb')), hashlib.md5()
  )

  return out

def flatten(container):
  for i in container:
    if isinstance(i, (list,tuple)):
      for j in flatten(i):
        yield j
    else:
      yield i

def pdump(obj, name):
  try:
    with open(name, 'wb') as pfile:
      pickle.dump(obj, pfile)
  except TypeError:
    qtk.warning('possible issues with ctypes extensions')
    obj = copy.deepcopy(obj)
    structure = qtk.get_nested_structure(obj)


def get_nested_structure(obj):
  nested = True
  structure = []
  ind_list = []
  cursor = obj

  def get_structure(cursor, structure):
    if type(cursor) is list:
      if len(cursor) > 0:
        if type(cursor[0]) is list:
          for c in cursor:
            structure.append([])
            get_structure(c, structure[-1])
        else:
          structure.append(len(cursor))
      else:
        structure.append(0)

  if type(cursor) is list:
    get_structure(cursor, structure)

  return structure

def getitem_nested(obj, *ind):
  if type(ind) is list: ind
  out = obj
  for i in ind:
    out = out[i]
  return out

#def get_nested_ind(structure):
#  nested = True
#  ind = []
#  
#  while nested:
#    if type(structure) is list: 
#      if len(structure) > 0:
#        if type(structure[0]) is int:
#          for s in structure:
#            ind.append(range(s))
#    else:
    
    

def get_nested_ind(structure):
  ind = [[]]
  
  def get_list(cursor, ind):
    if type(cursor) is list:
      if len(cursor) > 0:
        if type(cursor[0]) is list:
          print cursor
          for i in range(len(cursor)):
            c = cursor[i]
            print ind[-1]
            ind[-1].append(i)
            get_list(c, ind)
        else:
          ind.append([])

  cursor = structure
  if type(cursor) is list:
    get_list(cursor, ind)

  return ind
  

def pload(name):
  with open(name, 'rb') as pfile:
    return pickle.load(pfile)

def save(*args, **kwargs):
  return pdump(*args, **kwargs)

def load(*args, **kwargs):
  return pload(*args, **kwargs)

def CoulombMatrix(molecule, dim=None):
  mol = toMolecule(molecule)
  if dim is None:
    dim = mol.N
  if dim < mol.N:
    qtk.exit("Coulomb matrix dimension must greater than" +\
             " the number of atoms")
  M = np.zeros((dim, dim))
  for i in range(mol.N):
    for j in range(i, mol.N):
      if i == j:
        M[i, j] = 0.5 * mol.Z[i] ** 2.4
      else:
        Rij = np.linalg.norm(mol.R[i] - mol.R[j])
        M[i, j] = mol.Z[i] * mol.Z[j] / Rij
        M[j, i] = M[i, j]
  order = list(np.argsort(sum(M ** 2)))
  order.reverse()
  out = M[:, order]
  return out[order, :]

def R(theta, u):
  u = np.array(u) / np.linalg.norm(u)
  return np.array(
    [[cos(theta) + u[0]**2 * (1-cos(theta)), 
      u[0] * u[1] * (1-cos(theta)) - u[2] * sin(theta), 
      u[0] * u[2] * (1-cos(theta)) + u[1] * sin(theta)],
     [u[0] * u[1] * (1-cos(theta)) + u[2] * sin(theta),
      cos(theta) + u[1]**2 * (1-cos(theta)),
      u[1] * u[2] * (1-cos(theta)) - u[0] * sin(theta)],
     [u[0] * u[2] * (1-cos(theta)) - u[1] * sin(theta),
      u[1] * u[2] * (1-cos(theta)) + u[0] * sin(theta),
      cos(theta) + u[2]**2 * (1-cos(theta))]]
  )

def fractionalMatrix(celldm_list):
  a = celldm_list[0]
  b = celldm_list[1]
  c = celldm_list[2]
  ca = celldm_list[3] # cos(alpha)
  cb = celldm_list[4] # cos(beta)
  cc = celldm_list[5] # cos(gamma)
  #sa = np.sqrt(1-ca**2) # sin(alpha) = sqrt(1-cos(alpha)^2)
  sc = np.sqrt(1-cc**2) # sin(gamma) = sqrt(1-cos(gamma)^2)
  #cw = (cb - ca*cc)/(sa*sc)
  #sw = np.sqrt(1-cw**2)
  v = np.sqrt(1 - ca**2 - cb**2 - cc**2 + 2*ca*cb*cc)

  # fractional transformation from wiki
  return np.array(
    [
      [a, b*cc, c*cb],
      [0, b*sc, c*(ca - cb*cc)/sc],
      [0, 0, c*v/sc],
    ]
  )

def cellVec2celldm(v):
  a = np.linalg.norm(v[0])
  b = np.linalg.norm(v[1])
  c = np.linalg.norm(v[2])
  cosA = np.dot(v[1], v[2]) / (b*c)
  cosB = np.dot(v[0], v[2]) / (a*c)
  cosC = np.dot(v[0], v[1]) / (a*b)
  return [a, b, c, cosA, cosB, cosC]

#  return np.array(
#    [
#      [a * sc * sw, 0, 0],
#      [a * cc, b, c * ca],
#      [a * sc * cw, 0, c * sa],
#    ]
#  )

def unscaledCelldm(celldm, scale):
  celldm_new = [celldm[i]/scale[i] for i in range(3)]
  angle = celldm[3:]
  celldm_new.extend(angle)
  return celldm_new
  
def lattice2celldm(lattice):
  celldm = [round(np.linalg.norm(a), 8) for a in lattice]
  for i in range(3):
    j = (i + 1) % 3
    k = (i + 2) % 3
    vj = lattice[j] / celldm[j]
    vk = lattice[k] / celldm[k]
    celldm.append(round(np.dot(vj, vk), 8))
  return celldm

def celldm2lattice(celldm, mode = None, **kwargs):
  scale = [1,1,1]
  if 'scale' in kwargs:
    scale = kwargs['scale']
  celldm = unscaledCelldm(celldm, scale)
  if mode is None:
    fm = fractionalMatrix(celldm)
    return np.dot(fm, np.eye(3)).T
  elif mode is 'cube_to_fcc':
    a = np.array([celldm[0], 0, 0])
    b = np.array([0, celldm[1], 0])
    c = np.array([0, 0, celldm[2]])
    v0 = 0.5 * b + 0.5 * c
    v1 = 0.5 * a + 0.5 * c
    v2 = 0.5 * a + 0.5 * b
    return np.vstack([v0, v1, v2])
  elif mode is 'cube_to_bcc':
    a = np.array([celldm[0], 0, 0])
    b = np.array([0, celldm[1], 0])
    c = np.array([0, 0, celldm[2]])
    v0 = -0.5 * a + 0.5 * b + 0.5 * c
    v1 =  0.5 * a - 0.5 * b + 0.5 * c
    v2 =  0.5 * a + 0.5 * b - 0.5 * c
    return np.vstack([v0, v1, v2])

def fractional2xyz(R_scale, lattice_celldm):
  scale = [ceil(i) for i in np.max(R_scale,axis=0)]
  for i in range(len(scale)):
    if scale[i] == 0: scale[i] = 1
  dim = np.array(lattice_celldm).shape
  if len(dim) == 2:
    assert dim == (3, 3)
    lattice = np.array(lattice_celldm) / np.array(scale)
  else:
    assert dim == (6,)
    lattice = celldm2lattice(lattice_celldm) / np.array(scale)
  R = np.dot(R_scale, lattice)
  return np.array(R)

#def fractional2xyz(R_scale, celldm, scale=[1,1,1]):
#  celldm = unscaledCelldm(celldm, scale)
#  fm = fractionalMatrix(celldm)
#  return np.dot(fm, R_scale.T).T

def xyz2fractional(R, celldm, scale=[1,1,1]):
  celldm = unscaledCelldm(celldm, scale)
  fm = fractionalMatrix(celldm)
  return np.dot(np.linalg.inv(fm), R.T).T

def convE(source, units, separator=None):
  def returnError(ioStr, unitStr):
    msg = 'supported units are:\n'
    for key in Eh.iterkeys():
      msg = msg + key + '\n'
    qtk.report(msg, color=None)
    qtk.exit(ioStr + " unit: " + unitStr + " is not reconized")

  EhKey = {
    'ha': 'Eh',
    'eh': 'Eh',
    'hartree': 'Eh',
    'ry': 'Ry',
    'j': 'J',
    'joule': 'J',
    'kj/mol': 'kJ/mol',
    'kjmol': 'kJ/mol',
    'kjm': 'kJ/mol',
    'kj': 'kJ/mol', # assume no kilo Joule!
    'kcal/mol': 'kcal/mol',
    'kcalmol': 'kcal/mol',
    'kcal': 'kcal/mol', # assume no kcal!
    'kcm': 'kcal/mol',
    'ev': 'eV',
    'cminv': 'cmInv',
    'cminverse': 'cmInv',
    'icm': 'cmInv',
    'cm-1': 'cmInv',
    'k': 'K',
    'kelvin': 'K',
  }
 
  Eh = {
    'Eh': 1.0,
    'Ry': 2.0,
    'eV': 27.211396132,
    'kcal/mol': 627.509469,
    'cmInv': 219474.6313705,
    'K': 3.15774646E5,
    'J': 4.3597443419E-18,
    'kJ/mol': 2625.49962
  }

  if not separator:
    separator='-'
  unit = units.split(separator)
  if len(unit) != 2:
    qtk.exit("problem with unit separator '%s'" % separator)
  if unit[0].lower() != 'hartree' and unit[0].lower() != 'eh':
    if unit[0].lower() in EhKey:
      unit0 = EhKey[unit[0].lower()]
      source = source / Eh[unit0]
    else: returnError('input', unit[0])
  if unit[1].lower() not in EhKey: 
    returnError('output', unit[1])
  else:
    unit1 = EhKey[unit[1].lower()]
  return source * Eh[unit1], unit1

def imported(module):
  try:
    __import__(module)
  except ImportError:
    return False
  else:
    return True

def toMolecule(input_data, **kwargs):
  if type(input_data) is not Molecule:
    try:
      return Molecule(input_data, **kwargs)
    except:
      pass
  else:
    return input_data

def numberToBase(n, b):
  if n == 0:
    return [0]
  digits = []
  while n:
    digits.append(int(n % b))
    n /= b
  return digits[::-1]

def partialSum(iterable):
  total = 0
  for i in iterable:
    total += i
    yield total

def listShape(input_list):
  if type(input_list) == list:
    if type(input_list[0]) != list:
      return len(input_list)
    else:
      return [listShape(sublist) for sublist in input_list]

def stack(*args, **kwargs):

  max_shape = args[0].shape
  for A in args[1:]:
    max_shape = np.maximum(max_shape, A.shape)

  def padded(C, shape):
    new = np.zeros(shape)
    insert = [slice(C.shape[dim]) for dim in range(C.ndim)]
    new[insert] = C
    return new

  return np.stack([padded(A, max_shape) for A in args], **kwargs)
