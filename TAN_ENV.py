import pickle
import numpy as np

from API import *

import time
import random
from TAN import random_scene, Add, P1, P2, P3, P4, RESOLUTION, decompose

# UP, DOWN, LEFT, RIGHT, SPIN, COMMIT
ACTIONS = ['U', 'D', 'L', 'R', 'S', 'C']

# TAN ENVIRONMENT 
class TAN_ENV:

    def __init__(self):
        print ("hi i live")
        self.tan = None
        self.cur_prog = None
        self.scratch = None
        self.pieces = []

    def render(self):

        committed = np.zeros(self.tan.to_np().shape) if self.cur_prog is None else self.cur_prog.to_np()
        scratch = self.scratch[0](*self.scratch[1:]).to_np()

        together = np.concatenate((self.spec, committed, scratch))
        return together

    def render_pix(self):
        self.tan.render('tan_drawings/spec.png')
        if self.cur_prog is not None:
            self.cur_prog.render('tan_drawings/committed.png')
        self.scratch[0](*self.scratch[1:]).render('tan_drawings/scratch.png')

    def reset(self):
        # the spec
        self.tan = random_scene()
        self.spec = self.tan.to_np()

        # commited, nothing here yet
        self.cur_prog = None

        # we gonna try piece 1 first
        self.pieces = [P2, P3, P4]
        self.scratch = [P1, 1, 0, 0]

        return self.render()

    # get an oracular move from the environment
    def oracle(self):
        cur_piece = self.scratch[0]
        cur_o, cur_x, cur_y = self.scratch[1:]
        pieces = decompose(self.tan)
        for p in pieces:
            if p.__class__.token == cur_piece.token:
                o,x,y = p.o, p.x, p.y
                if o != cur_o:
                    return 'S'
                if cur_x < x:
                    return 'R'
                if cur_x > x:
                    return 'L'
                if cur_y < y:
                    return 'D'
                if cur_y > y:
                    return 'U'
                return 'C'
        assert 0, "should not happen"

    # return nxt state, reward, done
    def step(self, move):
        assert move in ACTIONS
        sm_neg = -0.1

        if move in ['U', 'L', 'D', 'R', 'S']:
            scratch_old = self.scratch
            constr, o, x, y = self.scratch
            if move == 'U':
                y = max(y - 1, 0)
            if move == 'L':
                x = max(x - 1, 0)
            if move == 'D':
                y = min(RESOLUTION - 1, y + 1)
            if move == 'R':
                x = min(RESOLUTION - 1, x + 1)
            if move == 'S':
                o = o % 4 + 1
            self.scratch = [constr, o, x, y]

            tentative = self.scratch[0](*self.scratch[1:])
            if tentative.legal() is False:
                self.scratch = scratch_old

            nxt_state = self.render()
            return nxt_state, sm_neg, False

        if move == 'C':
            if self.cur_prog is None:
                self.cur_prog = self.scratch[0](*self.scratch[1:])
            else:
                to_add = self.scratch[0](*self.scratch[1:])
                self.cur_prog = Add(self.cur_prog, to_add)
                if self.cur_prog.legal() is False:
                    return None, sm_neg, True

            if len(self.pieces) == 0:
                reward = sm_neg
                if self.cur_prog.tan_distance(self.tan.to_np()) == 0:
                    reward = 1.0
                return None, reward, True
            else:
                self.scratch = [self.pieces[0], 1, 0, 0]
                self.pieces = self.pieces[1:]

            next_state = self.render()
            return next_state, sm_neg, False

# ================ training, rollouts and such ==================
def get_rollout(env, policy, max_iter = 50):
    cur_state = env.reset()
    done = False
    trace = []
    iter_k = 0
    while not done:
        iter_k += 1
        if iter_k > max_iter:
            break
        oracle_a = env.oracle()
        a = policy.act(cur_state)
        next_state, r, done = env.step(a)
        trace.append((cur_state, a, oracle_a, r, next_state))
    return trace

def train_dagger(env, student):
    init_state = env.reset()
    s_a_agg = []

    for i in range(10000):

        # learning
        trace = get_rollout(env, student, max_iter = 50)
        state_sample = [x[0] for x in trace]
        action_sample = [x[2] for x in trace]
        s_a_agg += list(zip(state_sample, action_sample))

        if i % 100 == 0:
            print ("======== diagnostics ==========")
            print ("Oracle Actions")
            print (action_sample)
            print ("Student Actions")
            print ([x[1] for x in trace])

        for i in range(10):
            sub_sample = random.sample(s_a_agg, 40)
            sub_states, sub_actions = [x[0] for x in sub_sample], [x[1] for x in sub_sample]
            student.learn_supervised(sub_states, sub_actions)

# =================== something ===================
def test_env():
    tenv = TAN_ENV()
    cur_state = tenv.reset()
    print (cur_state.shape)
    done = False
    while not done:
        # tenv.render_pix()
        oracle_move = tenv.oracle()
        print ("oracle says ", oracle_move)
        a = input('input\n')
        cur_state, r, done = tenv.step(a)
        print ("reward ", r)

def test_ro():
    from fcnet import Agent
    env = TAN_ENV()
    agent = Agent(18*3*3, ACTIONS)

    trace = get_rollout(env, agent, max_iter = 50)
    print (trace)

def test_dagger():
    from fcnet import Agent
    env = TAN_ENV()
    agent = Agent(18*3*3, ACTIONS)

    train_dagger(env, agent)

if __name__ == '__main__':
    # test_env()
    # test_ro()
    test_dagger()

