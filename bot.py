#!/usr/bin/python
import sys
import os
import copy

WORM_CNT = 4
DEATH_CONSTANT = 999999999  # if the worm is frozen for this much, he's dead
TIMEOUT = 3.0

F_EMPTY = ' '
F_FLOWER = '.'
F_ICE = '*'
F_BONUS = '+'
F_WALL = '#'

W_UP = 0
W_RIGHT = 1
W_DOWN = 2
W_LEFT = 3

W_A_OFF = map(ord, ['a', 'h', 'o', 'w'])

DIR_LEFT = 'left'
DIR_RIGHT = 'right'
DIR_UP = 'up'
DIR_DOWN = 'down'
X = 0
Y = 1

def str_change(ln, ndx, forwhat):
    return ln[:ndx] + str(forwhat) + ln[ndx + 1:]


class Worm():
    def __init__(self):
        self.segs = []  # worm segments' positions

    def __str__(self):
        return "(%d, %d) -- (%d, %d)" % (self.x, self.y, self.tail_x, self.tail_y, )

    def save_state(self):
        return list(self.segs)

    def load_state(self, state):
        self.segs = state
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
            elif curr_plan_field == my_a_offset + W_DOWN:
                curr_y += 1
            elif curr_plan_field == my_a_offset + W_LEFT:
                curr_x -= 1
            elif curr_plan_field == my_a_offset + W_RIGHT:
                curr_x += 1

            # record position
            self.segs = [(curr_x, curr_y,)] + self.segs

    def project(self, plan):
        for seg in self.segs:
            ln = str_change(plan[seg[1]], seg[0], str(self.id))            
            plan[seg[1]] = ln

        return plan

    def move(self, coords):
        self.x = self.segs[0][X] + coords[X]
        self.y = self.segs[0][Y] + coords[Y]
        self.segs = [(self.x, self.y)] + self.segs[:-1]

    def eat_flower(self):
        self.segs = self.segs + [self.segs[-1]]

                
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
            
            
    def move_worm(self, worm_id, direction):
        if direction == DIR_LEFT:
            self.move_worm_by(worm_id, (-1, 0))
        elif direction == DIR_RIGHT:
            self.move_worm_by(worm_id, (1, 0))
        elif direction == DIR_UP:
            self.move_worm_by(worm_id, (0, -1))
        elif direction == DIR_DOWN:
            self.move_worm_by(worm_id, (0, 1))
            
    def move_worm_by(self, worm_id, coords):
        self.worms[worm_id].move(coords)

    def print_plan(self):
        plan = list(self.plan)
        for w in g.worms:
            w.project(plan)

        self.project_objects(plan)
        
        for ln in plan:
            print ln

if __name__ == "__main__":
    f = open(sys.argv[1], 'rb')
    g = GamePlan()
    g.load(f.read())
    s = g.save_state()

    g.worms[0].eat_flower()
    g.move_worm(0, DIR_DOWN)
    g.print_plan()

    g.move_worm(0, DIR_DOWN)
    g.print_plan()

    g.move_worm(0, DIR_DOWN)
    g.print_plan()
    
    g.move_worm(0, DIR_DOWN)
    g.print_plan()
    print g.worms[0].x
    g.load_state(s)
    g.print_plan()
        
