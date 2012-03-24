#!/usr/bin/python
import sys
import os

WORM_CNT = 4

class Worm():
    pass

class GamePlan:
    def parse_params(self, line):
        return map(int, line.split(' '))
    
    def load(self, txt):
        lines = txt.split('\n')

        # load the first 4 lines with parameters of the game and the gameplane
        line_num = 0
        self.round_number, self.max_round, self.flowers_left = self.parse_params(lines[line_num])
        line_num += 1
        self.plan_width, self.plan_height = self.parse_params(lines[line_num])
        line_num += 1
        self.worms = []
        for i in range(WORM_CNT):
            worm = Worm()
            worm.x, worm.y, worm.tail_x, worm.tail_y, worm.frozen, worm.bonus, worm.points = \
              self.parse_params(lines[line_num])
            self.worms += [worm]
            line_num += 1
            
            
        self.plan = lines[line_num:]


if __name__ == "__main__":
    f = open(sys.argv[1], 'rb')
    g = GamePlan()
    g.load(f.read())
    print g.worms[0].x
        
