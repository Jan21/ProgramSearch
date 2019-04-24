from ForwardSample import *
from API import *
from pointerNetwork import *
from programGraph import *

import torch.nn.functional as F
import numpy as np


class A2C:
    def __init__(self, model, outerBatch=8, innerBatch=16):
        self.model = model
        self.outerBatch = outerBatch
        self.innerBatch = innerBatch

    def train(self, getSpec, R):
        fs = ForwardSample(self.model)

        # backward compatibility
        self.model._distance = nn.Sequential(self.model._distance[:-1],
                                             nn.Softplus())
        self.model.cuda()
        optimizer = torch.optim.Adam(self.model._distance.parameters(), lr=0.001, eps=1e-3, amsgrad=True)

        losses = []
        lastUpdate = 0
        updateFrequency = 100
        
        while True:
            specs = [getSpec() for _ in range(self.outerBatch) ]

            # for b,s in enumerate(specs):
            #     print("Spec",b)
            #     print(s)
            #     print()

            t0 = time.time()
            with torch.no_grad():
                specEncodings = self.model.specEncoder(np.array([s.execute() for s in specs ]))
                objectEncodings = ScopeEncoding(self.model)
                trajectories = fs.batchedRollout(specs, self.innerBatch,
                                                 objectEncodings=objectEncodings,
                                                 specEncodings=specEncodings)
            #print(f"THROUGHPUT {self.innerBatch*self.outerBatch/(time.time() - t0)} rollouts per second\t{time.time() - t0} seconds to get a batch of rollouts")
            gs = [ [ProgramGraph(t) for t in ts ]
                   for ts in trajectories ]
            # batchSuccess = 0
            # oldSuccess = 0
            # for spec,graphs in zip(specs,gs):

            #     print("for the spec",spec)
            #     for g in graphs:
            #         print(g.prettyPrint())
            #         print(R(spec,g))
            #         batchSuccess += int(R(spec,g))
            #         print()
            #     print()
            #     print("Without batching...")
            #     for _ in range(self.innerBatch):
            #         g = fs.rollout(spec)
            #         if g is None: continue
                    
            #         print(g.prettyPrint())
            #         print(R(spec,g))
            #         oldSuccess += int(R(spec,g))
            #         print()
            #     print()
            #     print()
            # print("COMPARE\t",batchSuccess,oldSuccess)
                
            successes = [ [1.*int(R(spec, g)) for g in _g]
                          for spec,_g in zip(specs, gs) ]

            

            # Build training targets for value
            # Jointly build the vectorized input for the distance head
            valueTrainingTargets = []
            distanceInput = []
            for si,(spec,ts) in enumerate(zip(specs, trajectories)):
                for ti,trajectory in enumerate(ts):
                    succeeded = successes[si][ti]
                    for t in range(len(trajectory) + 1):
                        g = ProgramGraph(trajectory[:t])
                        objects = g.objects(oneParent=self.model.oneParent)
                        oe = objectEncodings.encoding(spec, objects)
                        valueTrainingTargets.append(float(int(succeeded)))
                        distanceInput.append((specEncodings[si], oe))

            distancePredictions = self.model.batchedDistance([oe for se,oe in distanceInput],
                                                             [se for se,oe in distanceInput])
            distanceTargets = self.model.tensor(valueTrainingTargets)
            loss = binary_cross_entropy(-distancePredictions, distanceTargets)

            self.model.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.cpu().data.item())
            
            lastUpdate += 1
            
            if lastUpdate%updateFrequency == 1:
                print(f"Average loss: {sum(losses)/len(losses)}")
                losses = []
                with open('checkpoints/critic.pickle','wb') as handle:
                    pickle.dump(self.model, handle)

                print("Live update of model predictions!")
                k = 0
                for si,spec in enumerate(specs):
                    print(spec)
                    print()

                    for ti,trajectory in enumerate(trajectories[si]):
                        print()
                        print(f"TRAJECTORY #{ti}: Success? {valueTrainingTargets[k]}")
                        for t in range(len(trajectory) + 1):
                            
                            if t == 0:
                                print(f"Prior to any actions, predicted distance is {distancePredictions[k]}")
                            else:
                                print(f"After taking action {trajectory[t - 1]}\t\t{distancePredictions[k]}\tadvantage {math.exp(-distancePredictions[k]) - math.exp(-distancePredictions[k - 1])}")

                            k += 1

                    print()

                assert k == len(valueTrainingTargets)
                    
                    