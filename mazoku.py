import math

import pyxel

from maze_generator import Maze

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 128

MAP_WIDTH = 16
MAP_HEIGHT = 16
GENERATOR_MAP_WIDTH = int(MAP_WIDTH / 2 - 1)
GENERATOR_MAP_HEIGHT = int(MAP_HEIGHT / 2 - 1)


class Game:
    def __init__(self, game_map):
        self.maze_map = game_map.split("\n")

        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Mazoku")

        self.tp1 = pyxel.frame_count
        self.tp2 = pyxel.frame_count
        self.depth = 24
        self.render_alt = True
        self.show_boundaries = True
        self.show_minimap = False

        self.player_x = 3
        self.player_y = 3
        self.player_z = 1
        self.fov = math.pi / 4
        self.speed = 0.2  # Movement speed
        self.complete = False

    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        self.tp2 = pyxel.frame_count
        delta_time = self.tp2 - self.tp1
        self.tp1 = self.tp2

        if not self.complete:
            if pyxel.btn(pyxel.KEY_W):
                self.move_forward(delta_time)

            if pyxel.btn(pyxel.KEY_S):
                self.move_backward(delta_time)

            if pyxel.btn(pyxel.KEY_A):
                self.player_z -= 0.05 * delta_time

            if pyxel.btn(pyxel.KEY_D):
                self.player_z += 0.05 * delta_time

        if pyxel.btnr(pyxel.KEY_R):
            self.maze_map = Maze.generate(
                GENERATOR_MAP_WIDTH, GENERATOR_MAP_HEIGHT
            ).split("\n")
            self.complete = False

        if pyxel.btnr(pyxel.KEY_M):
            self.show_minimap = not self.show_minimap

    def draw(self):
        if not self.complete:
            start = 0
            if self.render_alt:
                start = 1
            self.render_alt = not self.render_alt

            for x in range(start, SCREEN_WIDTH, 2):
                # For each column, calculate the ray angle projected
                ray_angle = (self.player_z - self.fov / 2) + (
                    x / SCREEN_WIDTH
                ) * self.fov

                ray_distance = 0
                ray_hit_wall = False
                ray_hit_exit = False
                ray_boundary = False

                view_x = math.sin(ray_angle)
                view_y = math.cos(ray_angle)

                while not ray_hit_wall and ray_distance < self.depth:
                    ray_distance += 0.1

                    # Check if ray is out of map bounds
                    test_x = int(self.player_x + view_x * ray_distance)
                    test_y = int(self.player_y + view_y * ray_distance)

                    if (
                        test_x < 0
                        or test_x >= MAP_WIDTH
                        or test_y < 0
                        or test_y >= MAP_HEIGHT
                    ):
                        ray_hit_wall = True
                        ray_distance = self.depth
                    else:
                        # Ray is still inside map space, check if the ray cell is a wall
                        if (
                            self.maze_map[test_y][test_x] == "#"
                            or self.maze_map[test_y][test_x] == "%"
                        ):
                            ray_hit_wall = True

                            if self.maze_map[test_y][test_x] == "%":
                                ray_hit_exit = True

                            # Cast rays from each wall corner to find boundaries
                            wall_rays = []
                            for wx in range(2):
                                for wy in range(2):
                                    try:
                                        vx = test_x + wx - self.player_x
                                        vy = test_y + wy - self.player_y
                                        d = math.sqrt(vx**2 + vy**2)
                                        dot = (view_x * vx / d) + (view_y * vy / d)
                                        wall_rays.append((d, dot))
                                    except ZeroDivisionError:
                                        pass

                            # Sort to find the closest
                            wall_rays.sort()

                            # Look for small angles with closest corners
                            bound = 0.01
                            if (
                                math.acos(wall_rays[0][1]) < bound
                                or math.acos(wall_rays[1][1]) < bound
                            ):
                                ray_boundary = True

                # Calculate distances to ceiling and floor
                ceiling = SCREEN_HEIGHT / 2 - SCREEN_HEIGHT / ray_distance
                floor = SCREEN_HEIGHT - ceiling

                # Using Pyxel image bank as display buffer
                shade = 0
                for y in range(SCREEN_HEIGHT):
                    if y < ceiling:
                        pyxel.pset(x, y, pyxel.COLOR_BLACK)
                    elif y > ceiling and y <= floor:
                        # Compute wall shading
                        if ray_distance < self.depth / 6:
                            if ray_hit_exit:
                                shade = pyxel.COLOR_LIME
                            else:
                                shade = pyxel.COLOR_WHITE
                        elif ray_distance < self.depth / 4:
                            if ray_hit_exit:
                                shade = pyxel.COLOR_GREEN
                            else:
                                if x % 2:
                                    shade = (
                                        pyxel.COLOR_WHITE
                                        if y % 2
                                        else pyxel.COLOR_BLACK
                                    )
                                else:
                                    shade = (
                                        pyxel.COLOR_BLACK
                                        if y % 2
                                        else pyxel.COLOR_WHITE
                                    )
                        elif ray_distance < self.depth / 3:
                            if ray_hit_exit:
                                shade = pyxel.COLOR_GREEN
                            else:
                                shade = pyxel.COLOR_BROWN
                        elif ray_distance < self.depth / 2:
                            if ray_hit_exit:
                                shade = pyxel.COLOR_BROWN
                            else:
                                if x % 2:
                                    shade = (
                                        pyxel.COLOR_BROWN
                                        if y % 2
                                        else pyxel.COLOR_BLACK
                                    )
                                else:
                                    shade = (
                                        pyxel.COLOR_BLACK
                                        if y % 2
                                        else pyxel.COLOR_BROWN
                                    )
                        elif ray_distance < self.depth:
                            shade = pyxel.COLOR_BLACK

                        # Change the shade of boundary between walls
                        if self.show_boundaries and ray_boundary:
                            shade = pyxel.COLOR_BLACK

                        pyxel.pset(x, y, shade)
                    else:
                        # Compute floor shading
                        b = 1 - (y - SCREEN_HEIGHT / 2) / (SCREEN_HEIGHT / 2)
                        if b < 0.25:
                            shade = pyxel.COLOR_LIGHT_BLUE
                        elif b < 0.5:
                            if x % 2:
                                shade = (
                                    pyxel.COLOR_LIGHT_BLUE
                                    if y % 2
                                    else pyxel.COLOR_NAVY
                                )
                            else:
                                shade = (
                                    pyxel.COLOR_NAVY
                                    if y % 2
                                    else pyxel.COLOR_LIGHT_BLUE
                                )
                        elif b < 0.75:
                            shade = pyxel.COLOR_DARK_BLUE
                        elif b < 0.9:
                            if x % 2:
                                shade = (
                                    pyxel.COLOR_DARK_BLUE
                                    if y % 2
                                    else pyxel.COLOR_BLACK
                                )
                            else:
                                shade = (
                                    pyxel.COLOR_BLACK
                                    if y % 2
                                    else pyxel.COLOR_DARK_BLUE
                                )
                        else:
                            shade = pyxel.COLOR_BLACK

                        pyxel.pset(x, y, shade)
        else:
            pyxel.cls(0)
            pyxel.text(
                SCREEN_WIDTH / 2 - 32,
                SCREEN_HEIGHT / 2 - 32,
                "Maze completed!",
                pyxel.COLOR_WHITE,
            )
            pyxel.text(
                SCREEN_WIDTH / 2 - 58,
                SCREEN_HEIGHT / 2 - 16,
                "Press R to generate a new maze",
                pyxel.COLOR_WHITE,
            )

        # Draw minimap
        if self.show_minimap:
            startx = 2
            starty = SCREEN_HEIGHT - MAP_WIDTH * 2
            for nx in range(MAP_HEIGHT - 1):
                for ny in range(MAP_WIDTH - 1):
                    cell = self.maze_map[ny][nx]
                    if cell == "#":
                        col = pyxel.COLOR_GRAY
                    elif cell == "%":
                        col = pyxel.COLOR_PEACH
                    else:
                        col = pyxel.COLOR_WHITE
                    pyxel.rect(nx * 2 + startx, ny * 2 + starty, 2, 2, col)
            px = int(self.player_x)
            py = int(self.player_y)
            pyxel.rect(px * 2 + startx, py * 2 + starty, 2, 2, pyxel.COLOR_CYAN)

    def move_forward(self, delta_time):
        new_x = self.player_x + math.sin(self.player_z) * self.speed * delta_time
        new_y = self.player_y + math.cos(self.player_z) * self.speed * delta_time

        if self.entered_exit(new_x, new_y):
            self.complete = True
        else:
            if not self.collides(new_x, new_y):
                self.player_x = new_x
                self.player_y = new_y

    def move_backward(self, delta_time):
        new_x = self.player_x - math.sin(self.player_z) * self.speed * delta_time
        new_y = self.player_y - math.cos(self.player_z) * self.speed * delta_time

        if self.entered_exit(new_x, new_y):
            self.complete = True
        else:
            if not self.collides(new_x, new_y):
                self.player_x = new_x
                self.player_y = new_y

    def collides(self, x, y):
        return self.maze_map[int(y)][int(x)] == "#"

    def entered_exit(self, x, y):
        return self.maze_map[int(y)][int(x)] == "%"


if __name__ == "__main__":
    game = Game(Maze.generate(GENERATOR_MAP_WIDTH, GENERATOR_MAP_HEIGHT))
    game.run()
