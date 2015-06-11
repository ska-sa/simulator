## Rodrigues compatibale simulation pipeline 
## sphesihle makhathini [sphemakh@gmail.com]

import Pyxis
import ms
import mqt 
import im
import imager
import lsm
import im.argo as argo
from Pyxis.ModSupport import *

import pyfits
import Tigger
import numpy
import os
import numpy
import math
import json
from Simms import simms
import time

import im.moresane


PI = math.pi
FWHM = math.sqrt( math.log(256) )


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
        argo.predict_vis(lsmname, wprojplanes=128, column=_column)

        if noise:
            simnoise(noise=noise,addToCol=_column,column=column)
    else:
        args = ["${ms.MS_TDL} ${lsm.LSM_TDL}"] + list(args)

        options = {}
        options['ms_sel.output_column'] = _column

        if noise:
            options['noise_stddev'] = noise

        mqt.run(TURBO_SIM, job='_tdl_job_1_simulate_MS',
                config=tdlconf, section=tdlsec, options=options, args=args,**kw)

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


def azishe(config='$CFG'):

    # Get parameters from json file    
    with open(II(config)) as jsn_std:
        params = json.load(jsn_std)

    # Remove empty strings and convert unicode characters to strings
    for key in params.keys():
        if params[key] =="":
            del params[key] 
        elif isinstance(params[key],unicode):
            params[key] = str(params[key]).lower()

    get_opts = lambda prefix: filter(lambda a: a[0].startswith(prefix), params.items())

    # Retrieve MS and imager options
    ms_dict = dict([(key.split('ms_')[-1],val) for (key,val) in get_opts('ms_') ] )
    im_dict = dict([(key.split('im_')[-1],val) for (key,val) in get_opts('im_') ] )

    # Seperate deconvolution settings
    _deconv = {}
    for dcv in 'lwimager wsclean moresane casa'.split():
        if params[dcv]:
            _deconv.update( {dcv:dict([(key.split(dcv+'_')[-1],val) for (key,val) in get_opts(dcv+'_') ] )} )
    
    # Set imaging options
    im.IMAGER = imager.IMAGER = params['imager'].lower()
    for opt in 'npix weight robust mode stokes'.split():
        if opt in im_dict.keys():
            setattr(im,opt,im_dict.pop(opt))
    im.cellsize = '%farcsec'%(im_dict.pop('cellsize'))
    im.stokes = im.stokes.upper()

    weight_fov = im_dict.pop('weight_fov')
    if weight_fov:
        im.weight_fov = '%farcmin'%weight_fov
    
    # Create empty MS
    synthesis = ms_dict.pop('synthesis')
    scalenoise = 1
    if synthesis > 12:
        scalenoise = math.sqrt(12.0/synthesis)
    
    msname = II('rodrigues%f.MS'%(time.time())) 
    obs = params['observatory'].lower()
    antennas = _OBS[obs]
    
    freq0 = ms_dict.pop('freq0')*1e6
    dfreq = ms_dict.pop('dfreq')*1e3
    direction = "J2000,%s,%s"%(ms_dict.pop('ra'),ms_dict.pop('dec'))
    simms.create_empty_ms(msname=msname,synthesis=synthesis,freq0=freq0,
                dfreq=dfreq,tel=obs,pos='%s/%s'%(OBSDIR,antennas),
                direction=direction,**ms_dict)
    if exists(msname):
        v.MS = msname
    else:
        abort("Something went wrong while creating the empty MS. Please check logs for details")

    makedir(DESTDIR)
    ms.plot_uvcov(ms=.1,width=10,height=10,dpi=150,save="$OUTFILE-uvcov.png")

    # Set noise for simulation
    spwtab = ms.ms(subtable="SPECTRAL_WINDOW")
    freq0 = spwtab.getcol("CHAN_FREQ")[ms.SPWID,0]
    spwtab.close()
    if params['add_noise']:
        noise =  compute_vis_noise(sefd=get_sefd(freq0)) * scalenoise
    else:
        noise = 0

    # Simulate Visibilities
    _katalog = params['katalog_id']
    if _katalog:
        katalog = '%s/%s'%(KATDIR,_KATALOG[params['katalog_id']])

        lsmname = II('${OUTDIR>/}${MS:BASE}.lsm.html')

        radius = float(params['radius'])
        fluxrange = params['fluxrange'].split('-')
        if len(fluxrange)>1:
            fluxrange = map(float,fluxrange)
        elif len(fluxrange)==1:
            fluxrange = [0,float(fluxrange[0])]

        
        select = ''
        fits = verify_sky(katalog) == 'FITS'
        if radius or fluxrange:
            if radius: select += '--select="r<%fdeg" '%radius
            if fluxrange: 
                select += '--select="I<%f" '%fluxrange[1]
                select += '--select="I>%f" '%fluxrange[0]
        if not fits:
            x.sh('tigger-convert $select --recenter=$direction $katalog $lsmname -f')
        else:
            from pyrap.measures import measures
            dm = measures()
            direction = dm.direction('J2000',ms_opts[ra],ms_opts[dec])
            ra = np.rad2deg(direction['m0']['value'])
            dec = np.rad2deg(direction['m1']['value'])
            hdu = pyfits.open(temp_file)
            hdu[0].hdr['CRVAL1'] = ra
            hdu[0].hdr['CRVAL2'] = dec
            hdu.writeto(tmp_file,clobber=True)

        simsky(lsmname=lsmname,tdlsec='turbo-sim:custom',noise=noise,column='CORRECTED_DATA')

    skymodel = params['sky_model']
    if skymodel:
        simsky(lsmname=skymodel,noise=0 if katalog else noise,addToCol='CORRECTED_DATA')

    ## Finally Lets image
    # make dirty map
    im.make_image(psf=True,**im_dict)

    # Deconvolve
    for deconv in _deconv:
	global IMAGER
	IMAGER = deconv
        if deconv in STAND_ALONE_DECONV:
            #TODO(sphe) Will have to correct this later
            dirty_im = im.DIRTY_IMAGE   
            psf_im = im.PSF_IMAGE
            im.IMAGER = deconv.lower()
            im.moresane.deconv(image_prefix="moresane_qaz123",psf_image=psf_im, dirty_image=dirty_im, path="runsane", **_deconv[deconv])
        else:
            im.IMAGER = deconv.lower()
            im.make_image(dirty=False,restore=_deconv[deconv],restore_lsm=False,**im_dict)

    xo.sh('tar -czvf ${OUTDIR>/}${MS:BASE}.tar.gz $msname')
            

def set_defaults(msname='$MS',psf=False):
    """ Extract some basic information about the data"""

    tab = ms.ms()
    uvmax = max( tab.getcol("UVW")[:2].sum(0)**2 )
    res = 1.22*((2.998e8/freq)/maxuv)/2.
    im.cellsize = "%farcsec"%(numpy.rad2deg(res/6)*3600)
    im.stokes = 'I' # make a brightness map by default
    im.npix = 2048
    im.mode = 'channel'
    im.IMAGE_CHANNELIZE = 0


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


def verify_sky(fname):
    ext = fname.split('.')[-1]
    if ext.lower() == 'fits':
        return 'FITS'
    elif ext.lower() == 'txt' or fname.endswith('.lsm.html'):
        return 'TIGGER'
    else:
        raise TypeError('Sky model "%s" has to be either one of FITS,ASCII,Tigger Model (lsm.html) '%fname)

def compute_vis_noise (sefd):
    """Computes nominal per-visibility noise"""

    sefd = sefd or SEFD
    tab = ms.ms()
    spwtab = ms.ms(subtable="SPECTRAL_WINDOW")

    freq0 = spwtab.getcol("CHAN_FREQ")[ms.SPWID,0]
    wavelength = 300e+6/freq0
    bw = spwtab.getcol("CHAN_WIDTH")[ms.SPWID,0]
    dt = tab.getcol("EXPOSURE",0,1)[0]
    dtf = (tab.getcol("TIME",tab.nrows()-1,1)-tab.getcol("TIME",0,1))[0]

    # close tables properly, else the calls below will hang waiting for a lock...
    tab.close()
    spwtab.close()

    info(">>> $MS freq %.2f MHz (lambda=%.2fm), bandwidth %.2g kHz, %.2fs integrations, %.2fh synthesis"%(freq0*1e-6,wavelength,bw*1e-3,dt,dtf/3600))
    noise = sefd/math.sqrt(2*bw*dt)
    info(">>> SEFD of %.2f Jy gives per-visibility noise of %.2f mJy"%(sefd,noise*1000))

    return noise 
