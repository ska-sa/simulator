## Simulator Pipeline
## Sphesihle Makhathini sphemakh@gmail.com

import ms
import mqt
import lsm
import im
from simms import simms

mqt.MULTITHREAD = 8
FITS = False
TIGGER = False
KATALOG = False
CLEAN = False
LSM = None
SELECT = None
NOISE = None
COLUMN = 'CORRECTED_DATA'

TOTAL_SYNTHESIS = None

OBSERVATORY = None
POSITIONS = None


def azishe(cfg='$CFG',make_image=True):
    """ The driver for simulator """

    cfg = interpolate_locals('cfg')
    ms_opts, im_opts, _deconv = load_from_json(cfg)
    
    global IMAGER
    __import__('im.%s'%IMAGER)
    for item in _deconv:
        __import__('im.%s'%item)
    
    # convert frequencies to Hz. This assumes [freq0,dfreq] = MHz,kHz
    freq0 = ms_opts['freq0']*1e6
    del ms_opts['freq0']
    dfreq = ms_opts['dfreq']*1e3
    del ms_opts['dfreq']
    
    synthesis = ms_opts['synthesis']

    if synthesis> 12:
        ms_opts['synthesis'] = 12.0
        scalenoise = math.sqrt(synthesis/12.0)
    else:
        scalenoise = 1
    if not os.path.exists(MAKEMS_OUT):
        x.mkdir(MAKEMS_OUT)
    
    msname = II('${MAKEMS_OUT>/}smakh%f.MS'%(time.time()))
    simms.simms(freq0=freq0,msname=msname,dfreq=dfreq,pos=POSITIONS,pos_type='casa',
                         tel=OBSERVATORY,**ms_opts)
    v.MS = msname
    
    #plot uv-coverage
    makedir(DESTDIR)
    ms.plot_uvcov(ms=.1,width=10,height=10,dpi=150,save="$OUTFILE-uvcov.png")
    
    ms.set_default_spectral_info()

    if ADDNOISE:
        noise = NOISE or compute_vis_noise(sefd=get_sefd(freq0)) * scalenoise
    else:
        noise = 0

    if TIGGER or FITS:
        simsky(lsmname=FITS or TIGGER, noise=noise)
        noise = 0 # we don't want to add the noise twice

    if KATALOG:
        fits = True if verify_sky(KATALOG) is 'FITS' else False

        tmp_std = tempfile.NamedTemporaryFile(suffix='.fits' if fits else '.lsm.html')
        tmp_std.flush()
        tmp_file = tmp_std.name

        # construct selection to give to tigger-convert
        select = ''
        if RADIUS or FLUXRANGE:
            if RADIUS: select += '--select="r<%fdeg" '%RADIUS
            if FLUXRANGE: 
                select += '--select="I<%f" '%FLUXRANGE[1]
                select += '--select="I>%f" '%FLUXRANGE[0]
        if not fits:
            x.sh('tigger-convert %s --recenter=J2000,%s,%s %s %s -f'%(select,ms_opts['ra'],ms_opts['dec'],KATALOG,tmp_file))
            #xo.sh('cp $tmp_file current.lsm.html')
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

        simsky(lsmname=tmp_file,addToCol=COLUMN,noise=noise)

    tmp_std.close()

    im.IMAGE_CHANNELIZE = CHANNELIZE
    # Set these here to have a standard way of accepting them in the form
    for opt in 'npix cellsize weight robust wprojplanes stokes weight_fov mode'.split():
        if opt in im_opts:
            if opt == 'stokes':
                setattr(im,opt,im_opts[opt].upper())
            elif opt in ['npix']:
                setattr(im,opt,int(im_opts[opt]))
            elif opt in ['robust']:
                setattr(im,opt,float(im_opts[opt]))
            elif opt == 'cellsize':
                setattr(im,opt,im_opts[opt]+'arcsec')
            elif opt == 'weight_fov':
                setattr(im,opt,im_opts[opt]+'arcmin')
            else: 
                setattr(im,opt,im_opts[opt])
            del im_opts[opt]

    
    if USE_DEFAULT_IMAGING_SETTINGS:
        im_defaults(OBSERVATORY)

    call_imager = eval('im.%s.make_image'%IMAGER)
    dirty_image = II('${OUTFILE}-dirty.fits')
    call_imager(dirty=True,psf=True,psf_image='${OUTFILE}-psf.fits',dirty_image=dirty_image,**im_opts)
    noise = madnoise(dirty_image,channelise=CHANNELIZE,freq_axis=0)
    info('Noise estimate from dirty image: %.3g mJy'%(noise*1e3))

    for deconv in _deconv:
        restore = _deconv[deconv]

        if deconv in 'wsclean casa lwimager'.split():
            IMAGER = deconv
            try:
                im.threshold = '%.3gJy'%(float(restore['sigmalevel'])*noise)
                del restore['sigmalevel']
            # set niter vey high to ensure threshold is reached
                im.niter = 10000 
                del restore['niter']
            except KeyError:
                im.threshold = restore['threshold']+'Jy'
                del restore['threshold']

        if IMAGER=='casa':
            for key,val in restore.iteritems():
                if key in ['niter']:
                    restore[key] = int(val)
                else:
                   try: restore[key] = float(val)
                   except ValueError: "do nothing"
        if deconv in STAND_ALONE_DECONV :
            im_opts['algorithm'] = deconv

        call_imager = eval('im.%s.make_image'%IMAGER)
        call_imager(dirty=False,imager=deconv,restore=restore,restore_lsm=False,**im_opts)


def im_defaults(obs):
    obs = obs.lower()

    if obs == 'meerkat':
        im.npix = 2048
        im.cellsize = '2.5arcsec'
        im.weight = 'briggs'
        im.robust = 0

    elif obs == 'kat-7':
        im.npix = 512
        im.cellsize = '30arcsec'
        im.weight = 'briggs'
        im.robust = 0

    elif obs == 'vla':
        im.npix = 1024
        im.cellsize = '2arcsec'
        im.weight = 'briggs'
        im.robust = 0
