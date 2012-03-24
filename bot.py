#!/usr/bin/python
import sys
import os
import time
from heapq import heappush, heappop

WORM_CNT = 4
DEATH_CONSTANT = 999999999  # if the worm is frozen for this much, he's dead
TIMEOUT = 3.0

F_EMPTY = ' '
F_FLOWER = '.'
F_ICE = '*'
F_BONUS = '+'
F_WALL = '#'
F_W1 = '1'
F_W2 = '2'
F_W3 = '3'
F_W4 = '4'

SCORES = {F_FLOWER: 10, F_ICE: 7, F_BONUS: 5, None: -1}
UNEATABLE_STUFF = {F_WALL: True, F_W1: True, F_W2: True, F_W3:True , F_W4: True}

W_UP = 0
W_RIGHT = 1
W_DOWN = 2
W_LEFT = 3
W_A_OFF = map(ord, ['a', 'h', 'o', 'w'])

DIR_LEFT = -1
DIR_RIGHT = 1
DIR_UP = 2
DIR_DOWN = -2
DIRECTIONS = [DIR_LEFT, DIR_RIGHT, DIR_UP, DIR_DOWN]

M_LEFT = 'l'
M_RIGHT = 'r'
M_STAY = '.'
M_TABLE = [DIR_LEFT, DIR_UP, DIR_RIGHT, DIR_DOWN]

X = 0
Y = 1

def str_change(ln, ndx, forwhat):
    return ln[:ndx] + str(forwhat) + ln[ndx + 1:]

def opposite_direction(d):
    return d * -1

class Worm():
    def __init__(self):
        self.segs = []  # worm segments' positions

    def __str__(self):
        return "(%d, %d) -- (%d, %d)" % (self.x, self.y, self.tail_x, self.tail_y, )

    def save_state(self):
        return (self.last_move, self.points, self.frozen, self.bonus, list(self.segs))

    def load_state(self, state):
        self.last_move, self.points, self.frozen, self. bonsu, self.segs = state
        self.x = self.segs[0][X]
        self.y = self.segs[0][Y]
        self.tail_x = self.segs[-1][X]
        self.tail_y = self.segs[-1][Y]
        
    
    def get_positions(self, plan):
        # to "learn" where the worm's segments are we need to
        # start from the tail and follow up to head

        curr_x, curr_y = self.tail_x, self.tail_y
        my_a_offset = W_A_OFF[self.id]

        self.segs = [(curr_x, curr_y,)]
        while not (curr_x == self.x and curr_y == self.y):
            # move
            curr_plan_field = ord(plan[curr_y][curr_x])
            
            if curr_plan_field == my_a_offset + W_UP:
                curr_y -= 1
                self.last_move = DIR_UP
            elif curr_plan_field == my_a_offset + W_DOWN:
                curr_y += 1
                self.last_move = DIR_DOWN
            elif curr_plan_field == my_a_offset + W_LEFT:
                curr_x -= 1
                self.last_move = DIR_LEFT
            elif curr_plan_field == my_a_offset + W_RIGHT:
                curr_x += 1
                self.last_move = DIR_RIGHT

            # record position
            self.segs = [(curr_x, curr_y,)] + self.segs
            
    def get_directions(self):
        res = list(DIRECTIONS)
        res.remove(opposite_direction(self.last_move))
        return res

    def project(self, plan):
        for seg in self.segs:
            ln = str_change(plan[seg[1]], seg[0], str(self.id))            
            plan[seg[1]] = ln

        return plan

    def move(self, coords):
        if coords[0] == 1:
            self.last_move = DIR_RIGHT
        elif coords[0] == -1:
            self.last_move == DIR_LEFT
        elif coords[1] == 1:
            self.last_move = DIR_DOWN
        elif coords[1] == -1:
            self.last_move = DIR_UP
            
        self.x = self.segs[0][X] + coords[X]
        self.y = self.segs[0][Y] + coords[Y]
        self.segs = [(self.x, self.y)] + self.segs[:-1]

    def eat_flower(self):
        self.segs = self.segs + [self.segs[-1]]

    def get_move_change(self, m):
        if self.last_move == m:
            return M_STAY

        if self.last_move == DIR_LEFT:
            if m == DIR_UP:
                return M_RIGHT
            elif m == DIR_DOWN:
                return M_LEFT
            else:
                print >>sys.stderr, 'WEIRD MOVE:', self.last_move, m
                return M_STAY #raise Exception()
            
        if self.last_move == DIR_RIGHT:
            if m == DIR_UP:
                return M_LEFT
            elif m == DIR_DOWN:
                return M_RIGHT
            else:
                print >>sys.stderr, 'WEIRD MOVE:', self.last_move, m
                return M_STAY #raise Exception()
            
        if self.last_move == DIR_UP:
            if m == DIR_LEFT:
                return M_LEFT
            elif m == DIR_RIGHT:
                return M_RIGHT
            else:
                print >>sys.stderr, 'WEIRD MOVE:', self.last_move, m
                return M_STAY #raise Exception()
            
        if self.last_move == DIR_DOWN:
            if m == DIR_LEFT:
                return M_RIGHT
            elif m == DIR_RIGHT:
                return M_LEFT
            else:
                print >>sys.stderr, 'WEIRD MOVE:', self.last_move, m
                return M_STAY #raise Exception()
        
        lm_ndx = M_TABLE.index(self.last_move)
        nm_ndx = M_TABLE.index(m)

        if lm_ndx == 3 and nm_ndx != 3:
            nm_ndx += 3
            
        diff = lm_ndx - nm_ndx

        print >>sys.stderr, lm_ndx, nm_ndx, diff
        sys.stderr.flush()
            
        if diff == 0:
            return M_STAY
        elif diff > 0:
            return M_LEFT
        else:
            return M_RIGHT
                
class GamePlan:
    def parse_params(self, line):
        return map(int, line.split(' '))
    
    def load(self, txt):
        lines = txt.split('\n')
        line_num = 0

        # load the first 4 lines with parameters of the game and the gameplan
        self.round_number, self.max_round, self.flowers_left = self.parse_params(lines[line_num])
        line_num += 1
        self.plan_width, self.plan_height = self.parse_params(lines[line_num])
        line_num += 1

        # load the parameters of each of the worms
        self.worms = []
        for i in range(WORM_CNT):
            worm = Worm()
            worm.id = i
            worm.x, worm.y, worm.tail_x, worm.tail_y, worm.frozen, worm.bonus, worm.points = \
              self.parse_params(lines[line_num])
            self.worms += [worm]
            line_num += 1
            
        # bitmap representation of the gameplan    
        self.plan = lines[line_num:]

        # get the precise positions of the worms segments so that we are able to compute
        # with it in our algorithm
        for worm in self.worms:
            worm.get_positions(self.plan)

        # get the position of the map elements like flowers, ices, ...
        # and erase everything apart from the walls so that we don't have to copy the walls
        self.flowers = []
        self.ices = []
        self.bonuses = []
        for row_id in range(len(self.plan)):
            new_ln = ""
            for col_id in range(len(self.plan[row_id])):
                curr_field = self.plan[row_id][col_id]                
                if not curr_field in [F_WALL, F_EMPTY]:
                    curr_coords = [(col_id, row_id,)]
                    if curr_field == F_FLOWER:
                        self.flowers += curr_coords
                    elif curr_field == F_ICE:
                        self.ices += curr_coords
                    elif curr_field == F_BONUS:
                        self.bonuses += curr_coords
                        
                    new_ln += F_EMPTY
                else:
                    new_ln += curr_field
                    
            self.plan[row_id] = new_ln

    def project_objects(self, plan):
        for flower in self.flowers:
            plan[flower[1]] = str_change(plan[flower[1]], flower[0], F_FLOWER)
        for ice in self.ices:
            plan[ice[1]] = str_change(plan[ice[1]], ice[0], F_ICE)
        for bonus in self.bonuses:
            plan[bonus[1]] = str_change(plan[bonus[1]], bonus[0], F_BONUS)

    def save_state(self):
        worms_state = []
        for worm in self.worms:
            worms_state += [worm.save_state()]

        return (worms_state, list(self.flowers), list(self.ices), list(self.bonuses))

    def load_state(self, state):
        worms_state, self.flowers, self.ices, self.bonuses = state
        for worm_state_id in range(len(worms_state)):
            self.worms[worm_state_id].load_state(worms_state[worm_state_id])

    def get_worm_directions(self, worm_id):
        return self.worms[worm_id].get_directions()
            
    def move_worm(self, worm_id, direction, eatmode = False):              
        if direction == DIR_LEFT:
            move_vector = (-1, 0)
        elif direction == DIR_RIGHT:
            move_vector = (1, 0)
        elif direction == DIR_UP:
            move_vector = (0, -1)
        elif direction == DIR_DOWN:
            move_vector = (0, 1)
        future_pos = (self.worms[worm_id].x + move_vector[0], 
                      self.worms[worm_id].y + move_vector[1])
        
        # check other worms because it is unpleasant to crash into them (or into ourselves)
        for worm in self.worms:
            for seg in worm.segs:                
                if seg == future_pos:
                    return F_WALL         
            
        self.move_worm_by(worm_id, move_vector)
        
        # check out if we ate something to get the right score
        pos = (self.worms[worm_id].x, self.worms[worm_id].y)
        if self.plan[pos[1]][pos[0]] == F_WALL:
            return F_WALL
            
        for f in self.flowers:
            if f == pos:
                if eatmode:
                    self.flowers.remove(f)
                return F_FLOWER
        for i in self.ices:
            if i == pos:
                if eatmode:
                    self.ices.remove(i)
                return F_ICE
        for b in self.bonuses:
            if b == pos:
                if eatmode:
                    self.bonuses.remove(i)
                return F_BONUS

    def move_worm_by(self, worm_id, coords):
        self.worms[worm_id].move(coords)

    def print_plan(self):
        plan = list(self.plan)
        for w in self.worms:
            w.project(plan)

        self.project_objects(plan)
        
        for ln in plan:
            print ln

class Bot:
    def __init__(self, worm_number, game_plan):
        self.game_plan = game_plan
        self.id = worm_number
                    
class Game:
    def __init__(self, my_id):
        self.my_id = my_id
        
    def load_plan(self, filename):
        f = open(filename, 'rb')
        self.g = GamePlan()
        self.g.load(f.read())
        f.close()
        
    def play_turn(self, state = None):
        state_stack = []
        orig_state = self.g.save_state()
        heappush(state_stack, (0.0, None, orig_state, []))
        start_time = time.time()
        max_score = 0.0
        max_move = None
        max_state = None
        
        # search the state space to find out what the best move is
        while len(state_stack) > 0 and time.time() - start_time < 0.3:            
            score, pth, state, total_path = curr_stack_state = heappop(state_stack)
            self.g.load_state(state)                
            #print [(s[0], s[1]) for s in state_stack]
            for direction in self.g.get_worm_directions(self.my_id):
                if pth is None:
                    pth_curr = direction
                else:
                    pth_curr = pth
                    
                self.g.load_state(state)
                
                what_we_ate = self.g.move_worm(self.my_id, direction)
                if UNEATABLE_STUFF.has_key(what_we_ate):
                    continue

                score_add = SCORES[what_we_ate]
                heappush(state_stack, (score - score_add, pth_curr, self.g.save_state(), total_path + [direction]))
                
                if max_move is None or max_score > score:
                    max_move = pth_curr
                    max_score = score - score_add
                    max_state = self.g.save_state()

        self.g.load_state(orig_state)
        return self.g.worms[self.my_id].get_move_change(max_move), max_move


        
    def play_turn_ab(self):
        states = []
        state = self.g.save_state()
                    
        for d1 in self.g.get_worm_directions(0):
            for d2 in self.g.get_worm_directions(1):
                for d3 in self.g.get_worm_directions(2):
                    for d4 in self.g.get_worm_directions(3):
                        print (d1, d2, d3, d4)
                        self.g.load_state(state)
                        self.g.move_worm(0, d1)
                        self.g.move_worm(1, d2)
                        self.g.move_worm(2, d3)
                        self.g.move_worm(3, d4)
                        states += [self.g.save_state()]

        print len(states)
        
        

if __name__ == "__main__":
    game = Game(int(sys.argv[2]))
    game.load_plan(sys.argv[1])
    if len(sys.argv) == 3:
        print game.play_turn()[0]
    else:
        while 1:
            turn, turn2 = game.play_turn()
            print '--- > moving', turn2
            game.g.move_worm(game.my_id, turn2, eatmode = True)
            game.g.print_plan()
        
        
