from __future__ import annotations
import random
import matplotlib.pyplot as plt
import numpy as np

plt.ion()

MAX_BOTS = 64
END_BOTS = 8
BOT_SIZE = 72
MIND_SIZE = 64
HEALTH_UP = 10
HEALTH_MAX = 120
FOOD_START = 20
POISON_START = 20
FOOD_POISON_RATE = 2
MAX_TICKS = 100000
MAX_FOOD = 50
MAX_POISON = 50
TARGET_FOOD = 110
TARGET_POISON = 110

ADR = MIND_SIZE
X_POS = MIND_SIZE + 1
Y_POS = MIND_SIZE + 2
HP = MIND_SIZE + 3
GEN = MIND_SIZE + 4
C_BLUE = MIND_SIZE + 5
C_GREEN = MIND_SIZE + 6
ANGLE = MIND_SIZE + 7

class Cell:
    EMPTY = 0
    FOOD = 1
    POISON = 2
    WALL = 3

FIXED_GENOME = [17, 9, 1, 61, 1, 1, 26, 57, 56, 3, 54] + [0] * 53


class World:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.grid = []
        self.bots = []
        self.tick = 0

    def init(self):
        self.grid = [[Cell.EMPTY for _ in range(self.w)] for _ in range(self.h)]
        self.tick = 0
        for x in range(self.w):
            self.grid[0][x] = Cell.WALL
            self.grid[self.h-1][x] = Cell.WALL
        for y in range(self.h):
            self.grid[y][0] = Cell.WALL
            self.grid[y][self.w-1] = Cell.WALL
        self.add_items(FOOD_START, POISON_START)
        self.add_walls()


    def count_items(self):
        food = poison = 0
        for row in self.grid:
            for cell in row:
                if cell == Cell.FOOD:
                    food += 1
                elif cell == Cell.POISON:
                    poison += 1
        return food, poison


    def balance(self):
        food, poison = self.count_items()
        while food < TARGET_FOOD:
            if not self.add_random(Cell.FOOD):
                break
            food += 1
        while poison < TARGET_POISON:
            if not self.add_random(Cell.POISON):
                break
            poison += 1


    def add_walls(self):
        cx, cy = self.w // 2, self.h // 2
        for dy in range(-3, 4):
            y = cy + dy
            if self.in_world(cx, y):
                self.grid[y][cx] = Cell.WALL
        for dx in range(-3, 4):
            x = cx + dx
            if self.in_world(x, cy):
                self.grid[cy][x] = Cell.WALL
        y_left = self.h // 3
        for x in range(7):
            if self.in_world(x, y_left):
                self.grid[y_left][x] = Cell.WALL
        x_top = (2 * self.w) // 3
        for y in range(7):
            if self.in_world(x_top, y):
                self.grid[y][x_top] = Cell.WALL


    def in_world(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h


    def add_items(self, food, poison):
        for _ in range(food):
            self.add_random(Cell.FOOD)
        for _ in range(poison):
            self.add_random(Cell.POISON)


    def add_random(self, cell_type):
        for _ in range(200):
            x = random.randint(1, self.w - 2)
            y = random.randint(1, self.h - 2)
            if self.grid[y][x] == Cell.EMPTY:
                for b in self.bots:
                    if b.alive() and b.mem[X_POS] == x and b.mem[Y_POS] == y:
                        break
                else:
                    self.grid[y][x] = cell_type
                    return True
        return False


    def add_food_poison(self):
        food, poison = self.count_items()
        for _ in range(FOOD_POISON_RATE):
            if random.random() < 0.5:
                if food >= MAX_FOOD:
                    continue
                t = Cell.FOOD
                food += 1
            else:
                if poison >= MAX_POISON:
                    continue
                t = Cell.POISON
                poison += 1
            self.add_random(t)


    def set_empty(self, x, y):
        if self.in_world(x, y):
            self.grid[y][x] = Cell.EMPTY


    def set_food(self, x, y):
        if self.in_world(x, y):
            self.grid[y][x] = Cell.FOOD


    def set_poison(self, x, y):
        if self.in_world(x, y):
            self.grid[y][x] = Cell.POISON


    def check_cell(self, x, y, self_bot):
        if not self.in_world(x, y):
            return 1
        for b in self.bots:
            if b is not self_bot and b.alive() and b.mem[X_POS] == x and b.mem[Y_POS] == y:
                return 2
        cell = self.grid[y][x]
        if cell == Cell.POISON:
            return 0
        if cell == Cell.WALL:
            return 1
        if cell == Cell.FOOD:
            return 3
        return 4


    def place_bots(self, bots):
        self.bots = []
        used = set()
        for bot in bots:
            for _ in range(200):
                x = random.randint(1, self.w - 2)
                y = random.randint(1, self.h - 2)
                if self.grid[y][x] != Cell.EMPTY:
                    continue
                if (x, y) in used:
                    continue
                bot.mem[X_POS] = x
                bot.mem[Y_POS] = y
                used.add((x, y))
                bot.world = self
                self.bots.append(bot)
                break


    def add_special_bot(self, bot):
        used = {(b.mem[X_POS], b.mem[Y_POS]) for b in self.bots if b.alive()}
        for _ in range(200):
            x = random.randint(1, self.w - 2)
            y = random.randint(1, self.h - 2)
            if self.grid[y][x] != Cell.EMPTY:
                continue
            if (x, y) in used:
                continue
            bot.mem[X_POS] = x
            bot.mem[Y_POS] = y
            bot.world = self
            self.bots.append(bot)
            return
        bot.mem[X_POS] = 0
        bot.mem[Y_POS] = 0
        self.bots.append(bot)


    def update(self):
        self.tick += 1
        for b in self.bots:
            if b.alive():
                b.step()
        self.balance()



class Bot:
    def __init__(self, genes, mutant=False, fixed=False):
        self.mem = [0] * BOT_SIZE
        for i in range(MIND_SIZE):
            self.mem[i] = genes[i]
        self.world = None
        self.mutant = mutant
        self.fixed = fixed
        self.reset()


    def copy_genes(self):
        return self.mem[:MIND_SIZE]


    def heal(self, h):
        hp = self.mem[HP] + h
        if hp > HEALTH_MAX:
            hp = HEALTH_MAX
        self.mem[HP] = hp
        return hp


    def damage(self, h):
        hp = self.mem[HP] - h
        if hp < 0:
            hp = 0
        self.mem[HP] = hp
        return hp


    def inc_addr(self, a):
        addr = self.mem[ADR] + a
        if addr >= MIND_SIZE:
            addr -= MIND_SIZE
        self.mem[ADR] = addr


    def get_x(self, n):
        x = self.mem[X_POS]
        n = (n + self.mem[ANGLE]) % 8
        if n in (0, 6, 7):
            x -= 1
        elif n in (2, 3, 4):
            x += 1
        return x


    def get_y(self, n):
        y = self.mem[Y_POS]
        n = (n + self.mem[ANGLE]) % 8
        if n < 3:
            y -= 1
        elif n in (4, 5, 6):
            y += 1
        return y


    def move(self, n):
        w = self.world
        x = self.get_x(n)
        y = self.get_y(n)
        h = w.check_cell(x, y, self)
        if h == 4:
            w.set_empty(self.mem[X_POS], self.mem[Y_POS])
            self.mem[X_POS] = x
            self.mem[Y_POS] = y
        if h == 3:
            w.set_empty(self.mem[X_POS], self.mem[Y_POS])
            self.mem[X_POS] = x
            self.mem[Y_POS] = y
            self.heal(HEALTH_UP)
            w.add_food_poison()
        if h == 0:
            self.damage(310)
            w.set_poison(self.mem[X_POS], self.mem[Y_POS])
            return
        if self.damage(1) > 0:
            self.inc_addr(h + 1)
        else:
            w.set_empty(self.mem[X_POS], self.mem[Y_POS])


    def fire(self, n):
        w = self.world
        x = self.get_x(n)
        y = self.get_y(n)
        h = w.check_cell(x, y, self)
        if h == 3:
            w.set_empty(x, y)
            self.heal(HEALTH_UP)
            w.add_food_poison()
        if h == 0:
            w.set_food(x, y)
        if self.damage(1) > 0:
            self.inc_addr(h + 1)
        else:
            w.set_empty(self.mem[X_POS], self.mem[Y_POS])


    def step(self):
        if self.mem[HP] == 0 or self.world is None:
            return
        for _ in range(10):
            if self.mem[HP] == 0:
                break
            cmd = self.mem[self.mem[ADR]]
            if cmd < 8:
                self.move(cmd)
                return
            if cmd < 16:
                self.fire(cmd)
                return
            if cmd < 24:
                x = self.get_x(cmd)
                y = self.get_y(cmd)
                r = self.world.check_cell(x, y, self)
                self.inc_addr(r + 1)
                continue
            if cmd < 32:
                self.mem[ANGLE] = (self.mem[ANGLE] + cmd % 8) % 8
                self.inc_addr(1)
                continue
            self.inc_addr(cmd)
        if self.damage(1) == 0:
            self.world.set_empty(self.mem[X_POS], self.mem[Y_POS])


    def reset(self):
        self.mem[ADR] = 0
        self.mem[HP] = 35
        self.mem[ANGLE] = random.randint(0, 7)


    def alive(self):
        return self.mem[HP] > 0



class GA:
    def __init__(self, size):
        self.size = size
        self.bots = []


    def init(self):
        self.bots = []
        for _ in range(self.size):
            self.bots.append(Bot([random.randint(0, 63) for _ in range(MIND_SIZE)]))


    def select(self):
        self.bots.sort(key=lambda b: (b.mem[GEN], b.mem[HP]), reverse=True)
        return self.bots[:END_BOTS]


    def reproduce(self, parents):
        new_bots = []
        for parent in parents[:END_BOTS]:
            for _ in range(7):
                clone = Bot(parent.copy_genes())
                clone.mem[GEN] = parent.mem[GEN] + 1
                new_bots.append(clone)
            genes = parent.copy_genes()
            for _ in range(random.randint(1, 10)):
                genes[random.randint(0, MIND_SIZE - 1)] = random.randint(0, 63)
            mutant = Bot(genes, mutant=True)
            mutant.mem[GEN] = parent.mem[GEN] + 1
            new_bots.append(mutant)
        self.bots = new_bots



class Sim:
    def __init__(self, w=50, h=30):
        self.w = w
        self.h = h
        self.world = None
        self.ga = None
        self.special_bot = None
        self.history_ticks = []
        self.paused = False


    def on_key(self, event):
        if event.key == " ":
            self.paused = not self.paused


    def init_world(self):
        self.world = World(self.w, self.h)
        self.world.init()


    def load_bots(self):
        for bot in self.ga.bots:
            bot.reset()
        self.world.place_bots(self.ga.bots)
        self.special_bot = Bot(FIXED_GENOME, fixed=True)
        self.special_bot.reset()
        self.world.add_special_bot(self.special_bot)


    def run_gen(self, gen):
        tick = 0
        while tick < MAX_TICKS:
            if not self.paused:
                self.world.update()
                tick += 1
                if len([b for b in self.ga.bots if b.alive()]) <= END_BOTS:
                    break
            plt.pause(0.001)
        return tick


    def update_plot(self):
        plt.clf()
        plt.plot(self.history_ticks, color='black', linewidth=0.5)

        if len(self.history_ticks) > 20:
            window = 20
            smooth = np.convolve(self.history_ticks, np.ones(window)/window, mode='valid')
            plt.plot(range(window-1, window-1 + len(smooth)),
                     smooth, color='red', linewidth=1.5)

        plt.title("Ticks per Generation")
        plt.xlabel("Generation")
        plt.ylabel("Ticks")
        plt.grid(True, color='lightgray', linewidth=0.5)
        plt.pause(0.001)


    def run(self, gens):
        fig = plt.figure("Evolution Graph", facecolor='white')
        fig.canvas.mpl_connect("key_press_event", self.on_key)

        for gen in range(gens):
            self.init_world()
            self.load_bots()
            ticks = self.run_gen(gen)
            print(f"Gen {gen}: {ticks} ticks")
            self.history_ticks.append(ticks)
            self.update_plot()
            best = self.ga.select()
            self.ga.reproduce(best)

        plt.ioff()
        plt.show()


def main():
    sim = Sim(50, 30)
    sim.ga = GA(MAX_BOTS)
    sim.ga.init()
    sim.run(5000)

if __name__ == "__main__":
    main()
