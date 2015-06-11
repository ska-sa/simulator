#Telescope Simulator

Simulates visibilities given a sky model, and then images. 
The visibilities are simulated using [MeqTrees](http://meqtrees.net) 
and/or [LWIMAGER](https://github.com/ska-sa/lwimager). 
You can image using LWIMAGER, [WSCLEAN](http://sourceforge.net/projects/wsclean), or the [CASA](http://casa.nrao.edu/index.shtml) imager (clean task).

## Running the simulator
To run this simulator, you need supply the simulator a configuration file; parameters.json is an example.

## With Docker (Not Recomended)

**This is what you need to install** 

You can find most of debeian packages for most these [here](https://launchpad.net/~radio-astro/+archive/ubuntu/main), or git repositories [here](github.com/ska-sa)

1. Meqtrees Timba  
2. Meqtrees Cattery, Owlcat, Purr  
3. [simms](https://github.com/sphemakh/simms)  
4. Pyxis  
5. LWIMAGER  
6. WSClean  
7. Casacore, casacore data  
8. CASAPY  
9. PyMORESANE  

Once you have all these installed, you can run the simulator in `src` folder. Run it as:
```
pyxis CFG=config_file OUTDIR=output_folder azishe
```
for help run:
```
pyxis help[azishe]
```

# With Docker (Recomended)
Fisrt make sure you have docker(>=1.3); **not the default Ubuntu docker.io package**.   
https://docs.docker.com/installation/ubuntulinux/#ubuntu-trusty-1404-lts-64-bit

Once you got docker set up. You can run the simulator as follows:

1. Download casapy `$ make download`
2. Build container `$ make build`
3. Run simulation `$ make run config=json_config_file`

**Please Note**

* You only have to run `make download` once
* You will need to re-build the container (run `make build`) everytime the pipeline changes
* The container will always be rebuilt using cached data, unless you run `make force-build`,
in which case everything will be rebuilt from scratch.
* You don't have to re-build the container each time you modify your config file. But your config file has to be placed in *input/*

### HaPPy Simulating!
