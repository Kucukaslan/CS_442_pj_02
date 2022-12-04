# CS 442 Project 2

## Running the project
Make sure that redis is running by
```redic-cli ping```

The program is named `main.py`.
Usage: python3 main.py <np> <datafile> <delta> <totcount> <logfile> <maxtime>
Example:
 python3 main.py 5 DATAFILE 100 25 LOGFILE 1000

We also provided a makefile that you can use both running and cleaning the processes.
We `strongly` suggest you to call `make k` before running the program to clean
the remnants from other executions that improperly killed.
To kill all the processes created by current and previous executions simply call
```bash
make k
```
which also cleans the redis DB to prepare a clean DB for next execution.

## Version  Information

* redis version = 6.2.6 (also tested with 5.0.3)

* python version = 3.7.4 (also tested with 3.10.6)

```
> lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 20.04.5 LTS
Release:        20.04
Codename:       focal
```

## Team Members

* 21902298 Giray Akyol
* 21901779 Muhammed Can Küçükaslan
* 21601899 Hakan Sivük  
