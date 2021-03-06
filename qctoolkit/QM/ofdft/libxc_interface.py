import qctoolkit as qtk
import pkgutil
import grid_points as gp
from libxc_dict import xc_dict
import os


inpPath = os.path.realpath(__file__)
inpPath = os.path.split(inpPath)[0]
xcpath = os.path.join(inpPath, 'libxc_exc.so')
xc_found = os.path.exists(xcpath)
if xc_found:
  from libxc_exc import libxc_exc
  from libxc_vxc import libxc_vxc
  from libxc_fxc import libxc_fxc
else:
  pass

def libxc_report(inp, xc_id, flag):
  for k, v in xc_dict.iteritems():
    if v == xc_id:
      key = k
      qtk.report("libxc_%s" % flag, "xc: %s, id: %d\n" % (key, xc_id))
      break

def get_xcid(xcFlag):
  if type(xcFlag) is int:
    if xcFlag not in xc_dict.values():
      qtk.exit("libxc functional id number %d is not valid" % xcFlag)
    else:
      xc_id = xcFlag
  elif type(xcFlag) is str:
    if xcFlag not in xc_dict:
      qtk.exit("libxc functional id %s is not valid" % xcFlag)
    else:
      xc_id = xc_dict[xcFlag]
  return xc_id

def coord_rho_sigma(inp, rhoSigma):
  coords = inp.grid.points
  if rhoSigma is None:
    rho = gp.getRho(inp, coords)
    sigma = gp.getSigma(inp, coords)
  else:
    rho, sigma = rhoSigma
  return coords, rho, sigma

def exc(inp, xcFlag=1, rhoSigma = None, report=True):
  xc_id = get_xcid(xcFlag)
  if report:
    libxc_report(inp, xc_id, 'exc')
  coords, rho, sigma = coord_rho_sigma(inp, rhoSigma)
  return libxc_exc(rho, sigma, len(coords), xc_id)

def vxc(inp, xcFlag=1, rhoSigma = None, report=True):
  xc_id = get_xcid(xcFlag)
  if report:
    inp.libxc_report(xc_id, 'vxc')
  coords, rho, sigma = coord_rho_sigma(inp, rhoSigma)
  return libxc_vxc(rho, sigma, len(coords), xc_id)

def fxc(inp, xcFlag=1, rhoSigma = None, report=True):
  xc_id = get_xcid(xcFlag)
  if report:
    inp.libxc_report(xc_id, 'fxc')
  coords, rho, sigma = coord_rho_sigma(inp, rhoSigma)
  return libxc_fxc(rho, sigma, len(coords), xc_id)
