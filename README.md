# Base Station Location Optimization
This project aims to recommend effective deployment locations for police emergency response cars. When an emergency ‘999’ call is made, a car will be dispatched from its base location to respond. The time between the placing of the call and the arrival of a car at an incident can be critical in preventing crimes and protecting citizens. Given that response resources are finite and incident occurrences are not uniformly distributed, the choice of base location can have a significant impact on the ability of cars to respond quickly to incidents.

Of the teams which tackled this law enforcement vehicle location problem in the IS421 Enterprise Analytics for Decision Support course, we were awarded Best Performing Team for achieving the lowest risks for both normal and high demand evaluation cases.

We provide Python scripts for quick execution from the command line, while the interim SmartDeploy web application is hosted at https://smart-deploy.herokuapp.com. 

## Getting Started

### Prerequisites
- Python 3.6
- [IBM ILOG CPLEX Optimization Studio](https://www.ibm.com/sg-en/analytics/cplex-optimizer)

### Installing
```
python -m venv eads
source eads/bin/activate
pip install -r requirements.txt
```

## Running
Default 15 cars:

`python solve.py [data_dir] [radius] [day]`

Optional flag to specify number of cars available for deployment:

`python solve.py [data_dir] [radius] [day] [num_cars]`

### Evaluation
Official Submission Portal: https://ucp.unicen.smu.edu.sg/gv/students/evaluate/

Internal script: `python evaluate.py [data_file] [solution_file]`

## To-do
- [ ] Cloud deployment fix
- [ ] UI Improvements

## Acknowledgements
Team: Patrick Lim, Jane Seah, Koh Zhi Rong, Tan Kim Chye, and Sim Li Jin

Supervisor: Professor Lau Hoong Chuin, School of Information Systems, Singapore Management University

Sponsor: Dr Jonathan Chase, Fujitsu-SMU Urban Computing and Engineering (UNiCEN) Corp. Lab
