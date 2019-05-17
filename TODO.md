# TODO THINGS

## CODE TO DO, Wed:
- [X] test generation of multiple const
	- [ ] determine correct distribution for constant
- [X] test '-' and space delims

- [ ] finetune policy with RL
	- [X] write code
	- [ ] test it, debug and speed

- [X] single network, value and policy head - nah
- [X] start to train with these new fixes on GCP

- [ ] do proper robustfill baseline
	- [X] start training
	test:
	- [ ] refactor beam
	- [ ] throw out invalid progs as they go

- [ ] save version of the data



python launch.py -z "n1-highmem-8" --copy 'models/new_RLvalueonly.p' -g "p100" "RLvalueonly" "python train_scaffold.py --args args_RLvalueonly"

python launch.py -z "n1-highmem-8" --copy 'models/new_RLfinetune.p' -g "p100" "RLfinetune" "python train_scaffold.py --args args_RLfinetune"


## ROBUST FILL REAL TRAINING TESTING
- [X] Parallelize Data Generation
- [X] Formalise Train / Test Scaffold

## ROBUST FILL ABLATION STUDIES 
- [X] With / Without Intermediates (with / without scratch) (maybe lower priority)
- [X] With / Without Value Function 
- [ ] Normal RobustFill (RNN)
- [X] Robustfill which renders and then commits for each line (like Xinyun and Kevin) (also maybe lower priority)
- [X] Beam Search vs A* (pending . . . )
- [X] SMC
- [X] MCTS

## OTHER DOMAINS
- [ ] Numpy Manipulations
- [ ] ??? With Long Programs
- [ ] CAD -- figure out situation there

## WRITING/PITCHING
- [X] write for ICML workshop paper
- [ ] Ask advisors for help pitching our approach

Kevin's input: let's focus more on formalizing the MDP situation and pushing on the search + value function additions, which are what seperate us from prior work