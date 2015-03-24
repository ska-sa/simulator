#Telescope Simulator

Simulates visibilities given a sky model, and then images. 
The visibilities are simulated using [MeqTrees](http://meqtrees.net) 
and/or [LWIMAGER](https://github.com/ska-sa/lwimager). 
You may image using LWIMAGER, [WSCLEAN](http://sourceforge.net/projects/wsclean), or the [CASA](http://casa.nrao.edu/index.shtml) imager (clean task).

## Running the simulator
To run this simulator, you need supply the simulator a configuration file; parameters.json is an example.

inside src folder run for help:

`$ pyxis help[azishe]`

To run:

`$ $pyxis CFG=json_config_file azishe`

Or using docker:

`$ make`

## Available Telescopes
You may request a Telescope via the github [issues](https://github.com/ska-sa/simulator/issues) service.  

* KAT-7  
* MeerKAT  
* JVLA (A-D configs)
* ASKAP  
