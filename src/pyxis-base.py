
import cPickle
import numpy
import pyfits,pyrap.tables
import math

from scipy.ndimage.measurements import *
# important to import from Pyxis, as this takes care of missing displays etc.

import Pyxis
import imager
import ms
import mqt
import std
import json

from Pyxis.ModSupport import *

DEG = 180/math.pi;
ARCMIN = DEG*60;
ARCSEC = ARCMIN*60;
FWHM = math.sqrt(math.log(256));  # which is 2.3548;


MEASURE_PSF = False
MEASURE_SIDELOBES = False
MEASURE_NOISE = True
SIDELOBES_CELL_ARCSEC = 0.5
SIDELOBES_R0_ARCSEC = 900
SIDELOBES_R1_ARCSEC = 1800
RFI = False # do sims with RFI as well
# use first channel of MS by default
ms.CHANRANGE = 0

NPIX_PSF = 1024
CELLSIZE_PSF = ".05arcsec"

# these are used to compute per-visibility noise
#SEFD = 528 
SEFD = 831 #MeerKAT band1b
INTEGRATION = None # None means look in MS 
BANDWIDTH = None   # None means look in MS
WAVELENGTH = 0.21
BASEFREQ = 1.4e+9

STATQUALS = ()

def str2bool(val):
    if val.lower() in 'true yes 1'.split():
        return True
    else: 
        return False

STAND_ALONE_DECONV = ['moresane']

def readCFG(cfg='$CFG'):
    cfg_std = open(II(cfg))
    params = {}
    for line in cfg_std.readlines():
        if not line.startswith('#'):
            line = line.strip()
            key = line.split('=')[0]
            key = key.replace('_dash_','-')
            val = line.split('=')[-1]
            if not line.endswith('='):
                val = val.split(' ')[0]
                if val.lower()!='none':
                    params[key] = val

    options = dict(ms_={},cr_={},im_={},lwimager_={},wsclean_={},casa_={},moresane_={})
    for key in params.keys():
        found = False
        for item in options.keys():
            if not found:
                if key.startswith(item):
                    found=True
                    options[item][key.split(item)[-1]] = params[key].lower()
                    del params[key]
    global OBSERVATORY,POSITIONS,MS_LABEL
    OBSERVATORY = params['observatory'].lower()
    POSITIONS = '%s/%s'%(OBSDIR,_OBS[OBSERVATORY])
    if OBSERVATORY.startswith('jvla'):
       MS_LABEL = OBSERVATORY
       OBSERVATORY = 'VLA'

    global FITS,TIGGER,TDLSEC,KATALOG,SELECT
    skytype = params['skytype'].lower()
    if skytype in ['tigger-lsm','ascii']:  
        TIGGER = True
        v.LSM = params['sky_model']+_SKYTYPE[skytype]
        x.sh('cp %s $LSM'%(params['sky_model']))
        TDLSEC = 'turbo-sim:custom'
    elif skytype =='fits':
        FITS = True
        v.LSM = params['skyname']+_SKYTYPE[skytype]
        x.sh('cp %s $LSM'%(params['sky_model']))
    elif skytype=='katalog':
        TDLSEC = 'turbo-sim:custom'
        v.LSM = '%s/%s'%(KATDIR,_KATALOG[params['katalog_id']])
        if LSM.endswith('.fits'):
            FITS = True
        else:
            TIGGER = True
    elif skytype in ['nvss6deg','scubed1deg']:
        TIGGER = True
        TDLSEC = 'turbo-sim:custom'
        v.LSM = 'katalog/%s.lsm.html'%skytype

    if str2bool(params['add_noise']):
        visnoise = float(params['vis_noise_std']) 
        v.NOISE = visnoise if visnoise else None;

    global OUTPUT_TYPE,COLUMN
    OUTPUT_TYPE = params['output']
    #COLUMN = params['column'].upper()
    _deconv = []
    for dcv in 'lwimager wsclean moresane casa'.split():
       if str2bool(params[dcv]):
          _deconv.append(dcv.lower())
    
    global RADIUS,FLUXRANGE
    RADIUS = float(params['radius'])
    FLUXRANGE = params['fluxrange'].split('-')
    if len(FLUXRANGE)>1:
        FLUXRANGE = map(float,FLUXRANGE)
    elif len(FLUXRANGE)==1:
        FLUXRANGE = [0,float(FLUXRANGE[0])]
    _imager = params['imager'].lower()

    global CHANNELIZE
    CHANNELIZE = int(params['channelise'])

    return options,_imager,_deconv


def load_from_json(fname='$CFG',set_globals=True):
    """ load simulation from a json config file """
    
    with open(II(fname)) as jsn_std:
        params = json.load(jsn_std)
    # remove empty strings
    for key in params.keys():
        if params[key] =="":
            del params[key]

    get_opts = lambda prefix: filter(lambda a: a[0].startswith(prefix), params.items()) 

    ms_dict = dict([(key.split('ms_')[-1],val) for (key,val) in get_opts('ms_') ] )
    im_dict = dict([(key,val) for (key.split('_im')[-1],val) in get_opts('im_') ] )

    _deconv = {}
    for dcv in 'lwimager wsclean moresane casa'.split():
        if params[dcv]:
            _deconv.update( {dcv:dict([(key.split(dcv+'_')[-1],val) for (key,val) in get_opts(dcv+'_') ] )} )

    if set_globals:
        # I do this in different phases to avoid confusion
        
        # Start with simulation related things
        global FITS,TIGGER,TDLSEC,KATALOG,SELECT,ADDNOISE,NOISE

        TDLSEC = 'turbo-sim:custom'
        ADDNOISE = params['add_noise']
        NOISE = params['vis_noise_std']

        if params['sky_type'].lower() is 'fits':
            FITS = params['sky_model']
        elif params['sky_type'].lower() in 'tigger-lsm tigger ascii':
            TIGGER = params['sky_model']

        #TODO(Sphe) update form to allow katalog_id=0, i.e don't use katalog
        if params['katalog_id']: 
            KATALOG = '%s/%s'%(KATDIR,_KATALOG[params['katalog_id']])
    
        global FLUXRANGE,RADIUS
        FLUXRANGE = map(float,params['fluxrange'].split('-'))
        RADIUS = params['radius']

        global OUTPUT,CHANNELIZE,IMAGER,USE_DEFAULT_IMAGING_SETTINGS
        CHANNELIZE = params['channelise']
        OUTPUT_TYPE = params['output']
        IMAGER = params['imager'].lower()
        USE_DEFAULT_IMAGING_SETTINGS = params['use_default_im']

        global OBSERVATORY,POSITIONS,MS_LABEL
        OBSERVATORY = params['observatory'].lower()
        POSITIONS = '%s/%s'%(OBSDIR,_OBS[OBSERVATORY])
        if OBSERVATORY.startswith('jvla'):
            MS_LABEL = OBSERVATORY
            OBSERVATORY = 'VLA'

    return ms_dict, im_dict, _deconv

        
def verify_sky(fname):
    ext = fname.split('.')[-1]
    if ext.lower() == 'fits':
        return 'FITS'
    elif ext.lower() == 'txt' or fname.endswith('.lsm.html'):
        return 'TIGGER'
    else:
        raise TypeError('Sky model "%s" has to be either one of FITS,ASCII,Tigger Model (lsm.html) '%fname)


def simsky(msname='$MS', lsmname='$LSM', tdlsec='$TDLSEC', tdlconf='$TDLCONF',
           column='$COLUMN', noise=0, args=[],
           addToCol=None,**kw):
    """ Simulates visibilities into an MS """

    msname, lsmname, column, tdlsec, tdlconf = interpolate_locals('msname lsmname'
        ' column tdlsec tdlconf')
    
    fits = True if verify_sky(lsmname) is 'FITS' else False

    v.MS = msname
    v.LSM = lsmname

    _column = 'MODEL_DATA' if addToCol else column

    if fits:
        _column = 'MODEL_DATA' if noise else column
        predict_from_fits(lsmname, wprojplanes=128, column=_column)

        if noise:
            simnoise(noise=noise,addToCol=_column,column=column)
    else:
        args = ["${ms.MS_TDL} ${lsm.LSM_TDL}"] + list(args)

        options = {}
        options['ms_sel.output_column'] = _column

        if noise:
            options['noise_stddev'] = noise

        options.update(kw)
        mqt.run(TURBO_SIM, job='_tdl_job_1_simulate_MS',
                config=tdlconf, section=tdlsec, options=options, args=args)

    if addToCol:
        tab = ms.msw()
        col1 = tab.getcol(addToCol)
        col2 = tab.getcol('MODEL_DATA')
        comb = col1 + col2
        nrows = len(comb)
        rowchunk = nrows//5

        for row0 in range(0,nrows,rowchunk):
            nr = min(nrows-row0,rowchunk)
            info('MODEL_DATA + $addToCol --> $column : rows %d-%d'%(row0,row0+nr) )
            tab.putcol(column,comb[row0:row0+nr],row0,nr)
        tab.close()

document_globals(simsky,"MS LSM COLUMN TDLSEC TDLCONF")    



def get_sefd(freq=650e6):
    freq0 = freq*1e-6 # work in MHz
    if np.logical_and(freq0>=580,freq0<=1020): 
        band = '1b'
    elif np.logical_and(freq0>=900,freq0<=1670): 
        band = '2'
    else : 
        warn('$freq0 MHz is is not within MeerKAT frequency range. Using SEFD for band 1b')
        band = '1b'
    return _SEFD['MKT'][band]

import fcntl

def compute_vis_noise (noise=0,sefd=SEFD):
  """Computes nominal per-visibility noise"""
  tab = ms.ms();
  spwtab = ms.ms(subtable="SPECTRAL_WINDOW");
  global BASEFREQ
  BASEFREQ = freq0 = spwtab.getcol("CHAN_FREQ")[ms.SPWID,0];
  global WAVELENGTH
  WAVELENGTH = 300e+6/freq0
  bw = BANDWIDTH or spwtab.getcol("CHAN_WIDTH")[ms.SPWID,0];
  dt = INTEGRATION or tab.getcol("EXPOSURE",0,1)[0];
  dtf = (tab.getcol("TIME",tab.nrows()-1,1)-tab.getcol("TIME",0,1))[0]
  # close tables properly, else the calls below will hang waiting for a lock...
  tab.close();
  spwtab.close();
  info(">>> $MS freq %.2f MHz (lambda=%.2fm), bandwidth %.2g kHz, %.2fs integrations, %.2fh synthesis"%(freq0*1e-6,WAVELENGTH,bw*1e-3,dt,dtf/3600));
  if not noise:
    noise = sefd/math.sqrt(2*bw*dt);
    info(">>> SEFD of %.2f Jy gives per-visibility noise of %.2f mJy"%(sefd,noise*1000));
  else:
    info(">>> using per-visibility noise of %.2f mJy"%(noise*1000));
  return noise;

def get_weight_opts (weight):
  """Parses a weight specification such as "robust=0,fov=10,taper=1" into a dict 
  of lwimager options. Used by compute_psf_and_noise() below"""
  opts = dict(weight=weight)
  # weight could have additional options: robust=X, fov=X, taper=X
  ws = weight.split(",");
  wo = dict([ keyval.split("=") for keyval in ws if "=" in keyval ]);
  opts['weight'] = ws[0] if "=" not in ws[0] else ws[0].split("=")[0];
  robust = wo.get('robust',wo.get('briggs',None));
  if robust is not None:
    opts['robust'] = robust = float(robust);
  if 'fov' in wo:
    fov = float(wo['fov']);
    opts['weight_fov'] = "%farcmin"%fov;
  taper = float(wo.get('taper',0)) or TAPER;
  if taper:
    opts['filter'] = "%farcsec,%farcsec,0deg"%(taper,taper);
  weight_txt = opts['weight'];
  quals = [ weight_txt ];  # qualifiers for _writestat
  if opts['weight'] != "natural":
    #opts.setdefault('weight_fov',FOV);
    if 'robust' in opts:
      weight_txt += "%+.1f"%opts['robust'];
      quals = [ "robust=%.1f"%opts['robust'] ];
    if 'weight_fov' in opts:
      info('>>>> %s'%(opts['weight_fov']))
      weight_txt += " FoV %s"%opts['weight_fov'].replace("arcsec","\"").replace("arcmin","'");
      quals.append("fov=%s"%opts['weight_fov']);
  if taper:
    weight_txt += " taper %.1f\""%taper;
    quals.append("taper=%.1f"%taper);
  else:
    quals.append("taper=0");
  return opts,weight_txt,quals;


def madnoise(fitsname,channelise=0,freq_axis=False):
    """ estimate image noise """
    cdf = 1.4826 # cumulative distribution function of normal distribution
    data = imdata(fitsname,channelise=channelise,freq_axis=freq_axis)
    return np.median( abs( data-np.median(data) ) ) *cdf


def measure_image_noise (noise=0,scale_noise=1.0,add_noise=False,rowchunk=1000000,use_old_noise_map=False,mad=False,**kw):
    info(' >>> Making noise map')
    if add_noise:
        simnoise(rowchunk=rowchunk,scale_noise=scale_noise,noise=noise) 
    noiseimage = II('$OUTFILE-${im.weight}-noise.fits')
    make_noise_map = True
    if use_old_noise_map:
        if os.path.exists(noiseimage): 
            info('Using existing noise map: $noiseimage')
            make_noise_map = False
        else: make_noise_map = True
    if make_noise_map:
        imager.make_image(column='MODEL_DATA',dirty_image=noiseimage,**kw)
    noise = pyfits.open(noiseimage)[0].data.std()
    info(">>>   rms pixel noise is %g uJy"%(noise*1e+6))
    return noise


def measure_sdl(r0,r1,**kw):
    r0 = r0 or int(SIDELOBES_R0_ARCSEC/SIDELOBES_CELL_ARCSEC)
    r1 = r1 or int(SIDELOBES_R1_ARCSEC/SIDELOBES_CELL_ARCSEC)
    npix = r1*2
    bigpsf = II('$OUTFILE-${im.weight}-bigpsf.fits')

    imager.make_image(dirty_image=bigpsf,dirty=dict(data="psf",cellsize="%farcsec"%SIDELOBES_CELL_ARCSEC,npix=npix),**kw);
    data = pyfits.open(bigpsf)[0].data[0,0,...];
    radius = numpy.arange(npix)-r1
    radius = numpy.sqrt(radius[numpy.newaxis,:]**2+radius[:,numpy.newaxis]**2)
    mask = (radius<=r1)&(radius>=r0)
    rms = data[mask].std();
    data = None;
    r0,r1 = r0/3600.,r1/3600.;
    info(">>>   rms far sidelobes is %g (%.2f<=r<=%.2fdeg"%(rms,r0,r1));
    return rms,r0,r1


def simnoise (noise=0,rowchunk=100000,skipnoise=False,addToCol=None,scale_noise=1.0,column='MODEL_DATA'):
  conf = MS.split('_')[0]
  spwtab = ms.ms(subtable="SPECTRAL_WINDOW")
  freq0 = spwtab.getcol("CHAN_FREQ")[ms.SPWID,0]/1e6
  tab = ms.msw()
  dshape = list(tab.getcol('DATA').shape)
  nrows = dshape[0]
  noise = noise or compute_vis_noise()
  if addToCol: colData = tab.getcol(addToCol)
  for row0 in range(0,nrows,rowchunk):
    nr = min(rowchunk,nrows-row0)
    dshape[0] = nr
    data = noise*(numpy.random.randn(*dshape) + 1j*numpy.random.randn(*dshape)) * scale_noise
    if addToCol: 
       data+=colData[row0:(row0+nr)]
       info(" $addToCol + noise --> $column (rows $row0 to %d)"%(row0+nr-1))
    else : info("Adding noise to $column (rows $row0 to %d)"%(row0+nr-1))
    tab.putcol(column,data,row0,nr);
  tab.close() 

SKIPNOISE = False


def apply_rfi_flagging (rfihist='RFIdata/rfipc.cp'):
  """Applies random flagging based on baseline length. Flagging percentages are taken
  from the rfihist file"""
  info("applying mock RFI flagging to $MS");
  # import table of flagging percentages
  (baselines,pc) = cPickle.load(file(rfihist));
  info("max fraction is %.2f, min is %.2f"%(pc.max(),pc.min()));
  # binsize is in km
  binsize = baselines[0]*1000;
  info("baseline binsize is %.2fm"%binsize);
  # open MS, get the per-row baseline length, 
  tab = ms.msw();
  uvw = tab.getcol('UVW')
  uvw = numpy.sqrt((uvw**2).sum(1))
  info("max baseline is %f"%uvw.max())
  # convert it to uvbin 
  uvbin = numpy.int64(uvw/binsize)
  info("max uv-bin is %d, we have %d bins tabulated"%(uvbin.max(),len(pc)));
  uvbin[uvbin>=len(pc)] = len(pc)-1
  # uvbin gives the number of the baseline bin in the 'pc' table above
  # now pull out a random number [0,1} for each row
  rr = numpy.random.random_sample(len(uvw))
  ## compute per-row threshold by looking up 'pc' array using the uvbin
  thr = pc[uvbin]
  ## kill the unlucky rows
  unlucky = rr<thr
  info(">>> mock RFI applied, flagged fraction is %.2f"%(float(unlucky.sum())/len(thr)));
  tab.putcol("FLAG_ROW",unlucky);

  
def clear_flags ():
  tab = ms.msw();
  tab.putcol("FLAG_ROW",numpy.zeros(tab.nrows(),bool));
  info("cleared all flags in $MS");
  
import numpy.random  
  
MSLIST_Template = '${OUTDIR>/}mslist.txt'

DOALL = False

def _addms(msname = "$MS"):
  """ Keeps track of MSs when making MSs using multiple threds.
    The MS names are stored into a file which can be specified 
    via MSLIST on the command line. The list of MSs can then be 
    returned as python list using the function get_mslist().
    "DOALL" must be set to True for this feature to be enabled"""
  try :
    ms_std = open(MSLIST,"r")
    line = ms_std.readline().split("\n")[0]
    ms_std.close()
  except IOError: line = ''
  ms_std = open(MSLIST,"w")
  line+= ",%s"%msname if len(line.split()) > 0 else msname
  ms_std.write(line)
  ms_std.close()
  info("New MS list : $line")
document_globals(_addms,"DOALL");

def get_mslist(filename):
  """ See help for _addms"""
  ms_std = open(filename)
  mslist = ms_std.readline().split('\n')[0].split(',')
  info('>>>>>>>>>>>>> $mslist')
  return mslist

define("MAKEMS_REDO",False,"if False, makems will omit existing MSs");
define("MAKEMS_OUT","MS","place MSs in this subdirectory");


def predict_from_fits (cube,padding=1.5,noise=0,column='DATA',wprojplanes=0):
    import im.lwimager
    im.lwimager.predict_vis(image=cube,padding=padding,copy=False,column=column,wprojplanes=wprojplanes);
    if noise > 0:
        simnoise(addToCol=column,noise=noise)


def flag_stepped_timeslot (step=3):
    """Flags every Nth timeslot"""
    nant = ms.ms(subtable="ANTENNA").nrows();
    tab = ms.msw();
    nb = nant*(nant+1)/2
    frow = tab.getcol("FLAG_ROW");
    nr = len(frow);
    nt = len(frow)/nb;
    info("$MS has $nr rows, $nant antennas, $nb baselines and $nt timeslots, flagging every $step timeslots");
    frow = frow.reshape([nt,nb]);
    frow[::step,:] = True;
    tab.putcol("FLAG_ROW",frow.reshape((nr,)));

def imdata(fitsname,channelise=0,freq_axis=False):
    hdu = pyfits.open(fitsname)
    hdr = hdu[0].header
    data = hdu[0].data
    naxis = hdr['NAXIS']
    img = [0]*(naxis-2) + [slice(None)]*2
    if channelise and freq_axis is not False:
        img[freq_axis] = range(channelise)
    return data[img]

   
def fitsInfo(fits):
    hdr = pyfits.open(fits)[0].header
    ra = hdr['CRVAL1'] 
    dec = hdr['CRVAL2']
    naxis = hdr['NAXIS']
    if naxis>3: 
        freq_ind = 3 if hdr['CTYPE3'].startswith('FREQ') else 4
    else: 
        freq_ind = 3
        if hdr['CRTYPE3'].startswith('FREQ') is False: 
            freq_axis = False
            return (ra,dec),freq_axis,naxis
    nchan = hdr['NAXIS%d'%freq_ind]
    dfreq = hdr['CDELT%d'%freq_ind]
    freq0 = hdr['CRVAL%d'%freq_ind] + hdr['CRPIX%d'%freq_ind]*dfreq
    return (ra,dec),(freq0,dfreq,nchan),naxis


def swap_stokes_freq(fitsname,freq2stokes=False):
  info('Checking STOKES and FREQ in FITS file, might need to swap these around.')
  hdu = pyfits.open(fitsname)[0]
  hdr = hdu.header
  data = hdu.data
  if hdr['NAXIS']<4: 
    warn('Editing fits file [$fitsname] to make it usable by the pipeline.')
    isfreq = hdr['CTYPE3'].startswith('FREQ')
    if not isfreq : abort('Fits header has frequency information')
    hdr.update('CTYPE4','STOKES')
    hdr.update('CDELT4',1)
    hdr.update('CRVAL4',1)
    hdr.update('CUNIT4','Jy/Pixel')
    data.resize(1,*data.shape)
  if freq2stokes:
    if hdr["CTYPE3"].startswith("FREQ") : return 0;
    else:
      hdr0 = hdr.copy()
      hdr.update("CTYPE4",hdr0["CTYPE3"])
      hdr.update("CRVAL4",hdr0["CRVAL3"])
      hdr.update("CDELT4",hdr0["CDELT3"])
      try :hdr.update("CUNIT4",hdr0["CUNIT3"])
      except KeyError: hdr.update('CUNIT3','Hz    ')
   #--------------------------
      hdr.update("CTYPE3",hdr0["CTYPE4"])
      hdr.update("CRVAL3",hdr0["CRVAL4"])
      hdr.update("CDELT3",hdr0["CDELT4"])
      try :hdr.update("CUNIT3",hdr0["CUNIT4"])
      except KeyError: hdr.update('CUNIT4','Jy/Pixel    ')
      warn('Swapping FREQ and STOKES axes in the fits header [$fitsname]. This is a SoFiA work arround.')
      pyfits.writeto(fitsname,np.rollaxis(data,1),hdr,clobber=True)
  elif hdr["CTYPE3"].startswith("FREQ"):
    hdr0 = hdr.copy()
    hdr.update("CTYPE3",hdr0["CTYPE4"])
    hdr.update("CRVAL3",hdr0["CRVAL4"])
    hdr.update("CDELT3",hdr0["CDELT4"])
    try :hdr.update("CUNIT3",hdr0["CUNIT4"])
    except KeyError: hdr.update('CUNIT3','Jy/Pixel    ')
   #--------------------------
    hdr.update("CTYPE4",hdr0["CTYPE3"])
    hdr.update("CRVAL4",hdr0["CRVAL3"])
    hdr.update("CDELT4",hdr0["CDELT3"])
    try :hdr.update("CUNIT4",hdr0["CUNIT3"])
    except KeyError: hdr.update('CUNIT4','Hz    ')
    warn('Swapping FREQ and STOKES axes in the fits header [$fitsname]. This is a  MeqTrees work arround.')
    pyfits.writeto(fitsname,np.rollaxis(data,1),hdr,clobber=True)
  return 0

