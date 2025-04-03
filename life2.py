#!/usr/bin/python3

# Life2
# TODO think of a better name. or don't.

# press space to pause and resume, escape to quit

# tabs > spaces, set your editor appropriately if you plan on hacking this

# TODO auto-save and load
# TODO click specific organism to learn more about it
# TODO left click to make noise (debug/for fun)
# TODO right click to spawn an organism, or mutate one (debug/for fun)
# TODO create lots and lots of info out options

# TODO possible bug where an organism lost an "a" gene and it seemed like the whole species did? maybe a byref issue somewhere? may also be responsible for certain mass extinction events, need to explore this

import pygame
import math, random, time, copy, string

# begin user-configurable constants
# graphics options
WINDOW_SIZE_X = 1280
WINDOW_SIZE_Y = 720
FULLSCREEN = False
TILE_DRAW_RADIUS = 16
LIFE_UNIT_SIZE_RADIUS = 1
DRAW_START_X = TILE_DRAW_RADIUS * 0.5
DRAW_START_Y = TILE_DRAW_RADIUS * 0.75
SHOW_RADIATION = False
DARK_CHASM_COLOR = (0, 0, 0)
DARK_LAND_COLOR = (105, 93, 77)
DARK_WATER_COLOR = (0, 51, 102)
LIT_CHASM_COLOR = (26, 26, 26)
LIT_LAND_COLOR = (184, 164, 135)
LIT_WATER_COLOR = (0, 89, 179)
RADIATION_COLOR = (0, 255, 255)
LIFE_USE_BRIGHT_COLORS_ONLY = True
SHOW_STATUS_TEXT = True
# speed options. delays measured in seconds
RENDER_GRID_INITIALIZATION = False
DELAY_PER_INIT_STEP = 0.0
RENDER_EVERY_X_SUN_STEPS = 1
DELAY_PER_RENDERED_SUN_STEP = 0.0
RENDER_EACH_ORGANISM_TURN = False
DELAY_PER_ORGANISM = 0.0
RENDER_EACH_ORGANISM_ACTION = False
DELAY_PER_ORGANISM_ACTION = 0.0
# world options
RANDOM_SEED = None
GRID_SIZE_X = 46
GRID_SIZE_Y = 30
SMOOTHING_PASSES = 32
SUN_SIDE_LENGTH = int(GRID_SIZE_Y * 0.4)
SOLAR_RADIATION_CHANCE = 0.01
COSMIC_RADIATION_CHANCE = 0.0001
# life options
ABIOGENESIS_CHANCE_WATER = 0.01
ABIOGENESIS_CHANCE_LAND = 0.0001
ABIOGENESIS_STARTING_ENERGY = 1.0
GROWTH_LOG_BASE = math.e
PHOTOSYNTHESIS_ENERGY_GAIN = 1.0
METABOLISM_ENERGY_LOSS_FACTOR = 0.01
METABOLISM_ENERGY_LOSS_MINIMUM = 0.000001	# inert virus cleanup
MUTATION_CHANCE_WATER = 0.01
MUTATION_CHANCE_LAND = 0.1
EATING_ENERGY_GAIN_FACTOR = 0.5
REPRODUCTION_CHANCE = 0.01
# log options
LOG_TO_CONSOLE = True
LOG_STATUS_ON_RENDER = True
# end user-configurable constants

def main():
	random.seed(RANDOM_SEED)
	pygame.init()
	if FULLSCREEN:
		surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
	else:
		surface = pygame.display.set_mode((WINDOW_SIZE_X, WINDOW_SIZE_Y))
	pygame.display.set_caption("Life2")
	game_grid = Grid(GRID_SIZE_X, GRID_SIZE_Y)
	if RENDER_GRID_INITIALIZATION:
		game_text = ""
		if SHOW_STATUS_TEXT: game_text = "Initializing..."
		render(surface, game_grid, game_text)
		time.sleep(DELAY_PER_INIT_STEP)
	for i in range(SMOOTHING_PASSES):
		game_grid.smooth()
		if RENDER_GRID_INITIALIZATION:
			render(surface, game_grid, game_text)
			time.sleep(DELAY_PER_INIT_STEP)
	game_grid.create_sun(SUN_SIDE_LENGTH)
	if RENDER_GRID_INITIALIZATION:
		render(surface, game_grid, game_text)
		time.sleep(DELAY_PER_INIT_STEP)
	time_count = 0
	running = True
	paused = False
	while running:
		for event in pygame.event.get():	# poll for events
			if event.type == pygame.QUIT:	# the user clicked X to close the window
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				elif event.key == pygame.K_SPACE:
					paused = not paused
		if not paused:
			time_count += 1
			game_grid = sun_step(game_grid)
			organisms = game_grid.organisms()
			if time_count % RENDER_EVERY_X_SUN_STEPS == 0:
				game_text = ""
				if SHOW_STATUS_TEXT:
					game_text += "Time: " + str(time_count) + " "
					game_text += "Organisms: " + str(len(organisms)) + " "
					largest_o = None
					largest_o_size = -1
					biomass_dict = {}	# {genome: [count, sum_of_size]}
					for o in organisms:
						if o.size > largest_o_size:
							largest_o = o
							largest_o_size = o.size
						genome = "".join(o.genes)
						if genome in biomass_dict:
							previous_data = biomass_dict[genome]
							biomass_dict[genome] = [previous_data[0] + 1, previous_data[1] + o.size]
						else:
							biomass_dict[genome] = [1, o.size]
					if largest_o:
						game_text += "- "
						game_text += "Largest organism: ["
						game_text += "ID#: " + str(largest_o.id) + " "
						game_text += "Location: (" + str(largest_o.x_pos) + ", " + str(largest_o.y_pos) + ") "
						game_text += "Size: " + str("{:.1f}".format(largest_o.size)) + " "
						game_text += "Genome: " + "".join(largest_o.genes) + "] "
					if biomass_dict:
						largest_biomass_genome = ""
						largest_biomass_count = -1
						largest_biomass_size = -1
						for g, d in biomass_dict.items():
							if d[1] > largest_biomass_size:
								largest_biomass_genome = g
								largest_biomass_count = d[0]
								largest_biomass_size = d[1]
						game_text += "- "
						game_text += "Most biomass: ["
						game_text += "Organisms: " + str(largest_biomass_count) + " "
						game_text += "Average size: " + str("{:.1f}".format(largest_biomass_size / largest_biomass_count)) + " "
						game_text += "Genome: " + largest_biomass_genome + "] "
				render(surface, game_grid, game_text)
				time.sleep(DELAY_PER_RENDERED_SUN_STEP)
			for o in organisms:
				# take actions based on its expressed genes
				xg = o.genes[:(int(o.size) + 1)]
				for g in xg:
					if o.is_alive():
						action = g[0]
						direction = g[1]
						# directions, for actions that use them:
						# 0: random ("directionless")
						# 1: 1 o'clock /
						# 2: 3 o'clock -
						# 3: 5 o'clock \
						# 4: 7 o'clock /
						# 5: 9 o'clock -
						# 6: 11 o'clock \
						# 7: here
						# 8: direction of most recent stimulus, if any. if none, do nothing
						# 9: direction opposite most recent stimulus, if any (if 7, use 0). if none, do nothing
						if direction == "8" and o.stimulus: direction = o.stim_direction
						if direction == "9" and o.stimulus: direction = opposite_direction(o.stim_direction)
						if direction == "0": direction = random.choice("1234567")
						if action == "a":	# TODO test each of these actions and make sure they actually work
							# photosynthesize
							if game_grid.tile[o.x_pos][o.y_pos].is_lit:
								if o == game_grid.tile[o.x_pos][o.y_pos].largest_organism():
									o.adjust_energy(PHOTOSYNTHESIS_ENERGY_GAIN)
						elif action == "b":
							# sense land
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								o.notice(game_grid.tile[nx][ny].terrain == "land", direction)
							elif direction == "7":	# if 8 or 9, then skip because there's no stimulus to follow. if there were, we'd have changed it above
								o.notice(game_grid.tile[o.x_pos][o.y_pos].terrain == "land", direction)
						elif action == "c":
							# sense water
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								o.notice(game_grid.tile[nx][ny].terrain == "water", direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].terrain == "water", direction)
						elif action == "d":
							# look for sunlight
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if game_grid.tile[nx][ny].is_lit:
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].is_lit, direction)
						elif action == "e":
							# look for small organisms. can only see nearby tiles and sunlit tiles
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if i == 0 and game_grid.tile[nx][ny].contains_smaller_than(o.size):
										found = True
									if game_grid.tile[nx][ny].is_lit and game_grid.tile[nx][ny].contains_smaller_than(o.size):
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].contains_smaller_than(o.size), direction)
						elif action == "f":
							# look for large organisms
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if i == 0 and game_grid.tile[nx][ny].contains_larger_than(o.size):
										found = True
									if game_grid.tile[nx][ny].is_lit and game_grid.tile[nx][ny].contains_larger_than(o.size):
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].contains_larger_than(o.size), direction)
						elif action == "g":
							# look for familiar organisms
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if i == 0 and game_grid.tile[nx][ny].contains_similar_to(o):
										found = True
									if game_grid.tile[nx][ny].is_lit and game_grid.tile[nx][ny].contains_similar_to(o):
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].contains_similar_to(o), direction)
						elif action == "h":
							# look for unfamiliar organisms
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if i == 0 and game_grid.tile[nx][ny].contains_different_from(o):
										found = True
									if game_grid.tile[nx][ny].is_lit and game_grid.tile[nx][ny].contains_different_from(o):
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].contains_different_from(o), direction)
						elif action == "i":
							# look for photosynthesizing organisms
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if i == 0 and game_grid.tile[nx][ny].contains_photosynthesizing_organism():
										found = True
									if game_grid.tile[nx][ny].is_lit and game_grid.tile[nx][ny].contains_photosynthesizing_organism():
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].contains_photosynthesizing_organism(), direction)
						elif action == "j":
							# look for organisms that move
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if i == 0 and game_grid.tile[nx][ny].contains_mobile_organism():
										found = True
									if game_grid.tile[nx][ny].is_lit and game_grid.tile[nx][ny].contains_mobile_organism():
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].contains_mobile_organism(), direction)
						elif action == "k":
							# look for organisms that bite
							if direction in "123456":
								nx, ny = o.x_pos, o.y_pos
								found = False
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if i == 0 and game_grid.tile[nx][ny].contains_biting_organism():
										found = True
									if game_grid.tile[nx][ny].is_lit and game_grid.tile[nx][ny].contains_biting_organism():
										found = True
								o.notice(found, direction)
							elif direction == "7":
								o.notice(game_grid.tile[o.x_pos][o.y_pos].contains_biting_organism(), direction)
						elif action == "l":
							# walk
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								if game_grid.tile[nx][ny].terrain == "land":
									game_grid.relocate_organism(o, nx, ny)
							elif direction == "7":
								pass
						elif action == "m":
							# run, stopping at another organism or as far as possible if none
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								for i in range(int(o.size)+1):
									if not game_grid.tile[nx][ny].terrain == "land": break
									game_grid.relocate_organism(o, nx, ny)
									game_grid.noise(o.x_pos, o.y_pos, o.size)
									if game_grid.tile[o.x_pos][o.y_pos].contains_organisms(): break
									nx, ny = game_grid.neighbor(nx, ny, direction)
							elif direction == "7":
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "n":
							# run as far as possible
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								for i in range(int(o.size)+1):
									if not game_grid.tile[nx][ny].terrain == "land": break
									game_grid.relocate_organism(o, nx, ny)
									game_grid.noise(o.x_pos, o.y_pos, o.size)
									nx, ny = game_grid.neighbor(nx, ny, direction)
							elif direction == "7":
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "o":
							# float
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								if game_grid.tile[nx][ny].terrain == "water":
									game_grid.relocate_organism(o, nx, ny)
							elif direction == "7":
								pass
						elif action == "p":
							# swim, stopping at another organism or as far as possible if none
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								for i in range(int(o.size)+1):
									if not game_grid.tile[nx][ny].terrain == "water": break
									game_grid.relocate_organism(o, nx, ny)
									game_grid.noise(o.x_pos, o.y_pos, o.size)
									if game_grid.tile[o.x_pos][o.y_pos].contains_organisms(): break
									nx, ny = game_grid.neighbor(nx, ny, direction)
							elif direction == "7":
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "q":
							# swim as far as possible
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								for i in range(int(o.size)+1):
									if not game_grid.tile[nx][ny].terrain == "water": break
									game_grid.relocate_organism(o, nx, ny)
									game_grid.noise(o.x_pos, o.y_pos, o.size)
									nx, ny = game_grid.neighbor(nx, ny, direction)
							elif direction == "7":
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "r":
							# fly, stopping at another organism or as far as possible if none
							if direction in "123456":
								found_organism = False
								nx, ny = o.x_pos, o.y_pos
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
									if game_grid.tile[nx][ny].contains_organisms():
										game_grid.relocate_organism(o, nx, ny)
										game_grid.noise(o.x_pos, o.y_pos, o.size)
										found_organism = True
										break
								if not found_organism:
									for i in range(int(o.size)+1):
										if not game_grid.tile[nx][ny].terrain == "chasm":
											game_grid.relocate_organism(o, nx, ny)
											game_grid.noise(o.x_pos, o.y_pos, o.size)
											break
										nx, ny = game_grid.neighbor(nx, ny, opposite_direction(direction))
							elif direction == "7":
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "s":
							# fly as far as possible
							if direction in "123456":
								for i in range(int(o.size)+1):
									nx, ny = game_grid.neighbor(nx, ny, direction)
								for i in range(int(o.size)+1):
									if not game_grid.tile[nx][ny].terrain == "chasm":
										game_grid.relocate_organism(o, nx, ny)
										game_grid.noise(o.x_pos, o.y_pos, o.size)
										break
									nx, ny = game_grid.neighbor(nx, ny, opposite_direction(direction))
							elif direction == "7":
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "t":
							# eat the smallest organism
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								o.eat(game_grid.tile[nx][ny].smallest_organism(), EATING_ENERGY_GAIN_FACTOR)
								game_grid.noise(o.x_pos, o.y_pos, o.size)
							elif direction == "7":
								o.eat(game_grid.tile[o.x_pos][o.y_pos].smallest_organism(except_for=o), EATING_ENERGY_GAIN_FACTOR)
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "u":
							# eat the largest organism
							if direction in "123456":
								nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
								o.eat(game_grid.tile[nx][ny].largest_organism(), EATING_ENERGY_GAIN_FACTOR)
								game_grid.noise(o.x_pos, o.y_pos, o.size)
							elif direction == "7":
								o.eat(game_grid.tile[o.x_pos][o.y_pos].largest_organism(except_for=o), EATING_ENERGY_GAIN_FACTOR)
								game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "v":
							# reproduce
							if random.random() < REPRODUCTION_CHANCE:
								if direction in "123456":
									nx, ny = game_grid.neighbor(o.x_pos, o.y_pos, direction)
									if not game_grid.tile[nx][ny].terrain == "chasm":
										game_grid.tile[nx][ny].move_in(Organism(nx, ny, o.size, GROWTH_LOG_BASE, o.genes))
										game_grid.noise(o.x_pos, o.y_pos, o.size)
										o.adjust_energy(-1 * o.size)
								elif direction == "7":
									game_grid.tile[o.x_pos][o.y_pos].move_in(Organism(o.x_pos, o.y_pos, o.size, GROWTH_LOG_BASE, o.genes))
									game_grid.noise(o.x_pos, o.y_pos, o.size)
									o.adjust_energy(-1 * o.size)
						elif action == "w":
							# do nothing
							pass
						elif action == "x":
							# make noise
							game_grid.noise(o.x_pos, o.y_pos, o.size)
						elif action == "y":
							# waste energy
							o.adjust_energy(-1)
						else:
							# die
							o.adjust_energy(-1 * o.energy)
					if RENDER_EACH_ORGANISM_ACTION and RENDER_EVERY_X_SUN_STEPS == 1:
						game_text = ""
						if SHOW_STATUS_TEXT:
							game_text += "Time: " + str(time_count) + " "
							game_text += "Organisms: " + str(len(organisms)) + " "
							game_text += "- "
							game_text += "ID#: " + str(o.id) + " "
							game_text += "Location: (" + str(o.x_pos) + ", " + str(o.y_pos) + ") "
							game_text += "Size: " + str("{:.1f}".format(o.size)) + " "
							game_text += "Energy: " + str("{:.1f}".format(o.energy)) + " "
							game_text += "Genome: [" + "".join(o.genes[:(int(o.size) + 1)]) + "]" + "".join(o.genes[(int(o.size) + 1):]) + " "
						render(surface, game_grid, game_text)
						time.sleep(DELAY_PER_ORGANISM_ACTION)
				o.ignore()
				o.adjust_energy(-1 * METABOLISM_ENERGY_LOSS_FACTOR * (o.size))
				if o.size == 0: o.adjust_energy(-1 * METABOLISM_ENERGY_LOSS_MINIMUM)
				if RENDER_EACH_ORGANISM_TURN and RENDER_EVERY_X_SUN_STEPS == 1:
					game_text = ""
					if SHOW_STATUS_TEXT:
						game_text += "Time: " + str(time_count) + " "
						game_text += "Organisms: " + str(len(organisms)) + " "
						game_text += "- "
						game_text += "ID#: " + str(o.id) + " "
						game_text += "Location: (" + str(o.x_pos) + ", " + str(o.y_pos) + ") "
						game_text += "Size: " + str("{:.1f}".format(o.size)) + " "
						game_text += "Energy: " + str("{:.1f}".format(o.energy)) + " "
						game_text += "Genome: [" + "".join(o.genes[:(int(o.size) + 1)]) + "]" + "".join(o.genes[(int(o.size) + 1):]) + " "
					render(surface, game_grid, game_text)
					time.sleep(DELAY_PER_ORGANISM)
	pygame.quit()

def sun_step(game_grid):
	# move the sun and apply radiation to a new grid.
	new_game_grid = copy.deepcopy(game_grid)
	for i in range(game_grid.size_x):
		for j in range(game_grid.size_y):
			nx, ny = game_grid.neighbor2(i, j)
			if game_grid.tile[nx][ny].is_lit:
				new_game_grid.tile[i][j].sunrise()
				if random.random() < (SOLAR_RADIATION_CHANCE + COSMIC_RADIATION_CHANCE):
					new_game_grid.tile[i][j].blast()
				else:
					new_game_grid.tile[i][j].cool()
			else:
				new_game_grid.tile[i][j].sunset()
				if random.random() < (COSMIC_RADIATION_CHANCE):
					new_game_grid.tile[i][j].blast()
				else:
					new_game_grid.tile[i][j].cool()
	# then remove dead organisms and apply abiogenesis and mutations,
	# all of which can be safely done directly on the new grid since nothing is moving.
	for i in range(new_game_grid.size_x):
		for j in range(new_game_grid.size_y):
			for o in new_game_grid.tile[i][j].organisms:
				if not o.is_alive(): new_game_grid.tile[i][j].organisms.remove(o)
			if new_game_grid.tile[i][j].is_rad:
				o = new_game_grid.tile[i][j].largest_organism()
				if not o:
					if new_game_grid.tile[i][j].terrain == "water" and random.random() < ABIOGENESIS_CHANCE_WATER:
						new_game_grid.tile[i][j].move_in(Organism(i, j, ABIOGENESIS_STARTING_ENERGY, GROWTH_LOG_BASE))
					elif new_game_grid.tile[i][j].terrain == "land" and random.random() < ABIOGENESIS_CHANCE_LAND:
						new_game_grid.tile[i][j].move_in(Organism(i, j, ABIOGENESIS_STARTING_ENERGY, GROWTH_LOG_BASE))
				else:
					if new_game_grid.tile[i][j].terrain == "water" and random.random() < MUTATION_CHANCE_WATER:
						o.mutate()
					elif new_game_grid.tile[i][j].terrain == "land" and random.random() < MUTATION_CHANCE_LAND:
						o.mutate()
	return new_game_grid

def opposite_direction(direction):
	if direction == "1": return "4"
	elif direction == "2": return "5"
	elif direction == "3": return "6"
	elif direction == "4": return "1"
	elif direction == "5": return "2"
	elif direction == "6": return "3"
	else: return "0"

def render(surface, game_grid, text):
	draw_hex_grid(surface, game_grid, TILE_DRAW_RADIUS)
	draw_text(surface, text)
	pygame.display.flip()
	if LOG_STATUS_ON_RENDER: log_text(text)

def draw_hex_grid(surface, game_grid, radius):	# horizontal-stacked orientation
	in_radius = radius * math.cos(math.pi / 6)
	surface.fill("black")
	for i in range(game_grid.size_x):
		for j in range(game_grid.size_y):
			color = pygame.Color(255,0,255)
			if game_grid.tile[i][j].terrain == "land": color = pygame.Color(DARK_LAND_COLOR)
			if game_grid.tile[i][j].terrain == "water": color = pygame.Color(DARK_WATER_COLOR)
			if game_grid.tile[i][j].terrain == "chasm": color = pygame.Color(DARK_CHASM_COLOR)
			if game_grid.tile[i][j].terrain == "land" and game_grid.tile[i][j].is_lit: color = pygame.Color(LIT_LAND_COLOR)
			if game_grid.tile[i][j].terrain == "water" and game_grid.tile[i][j].is_lit: color = pygame.Color(LIT_WATER_COLOR)
			if game_grid.tile[i][j].terrain == "chasm" and game_grid.tile[i][j].is_lit: color = pygame.Color(LIT_CHASM_COLOR)
			x, y = DRAW_START_X, DRAW_START_Y
			if j % 2 == 1: x += in_radius
			draw_hex(surface, color, (x+(i*in_radius*2), y+(j*radius*1.5)), radius, 0)
			largest_organism = game_grid.tile[i][j].largest_organism()
			if largest_organism:
				pygame.draw.circle(surface, largest_organism.color, (x+(i*in_radius*2), y+(j*radius*1.5)), largest_organism.size * LIFE_UNIT_SIZE_RADIUS, 0)
				pygame.draw.circle(surface, "black", (x+(i*in_radius*2), y+(j*radius*1.5)), largest_organism.size * LIFE_UNIT_SIZE_RADIUS, 1)
	if SHOW_RADIATION:	# second pass for radiation highlights
		for i in range(game_grid.size_x):
			for j in range(game_grid.size_y):
				x, y = DRAW_START_X, DRAW_START_Y
				if j % 2 == 1: x += in_radius
				if game_grid.tile[i][j].is_rad: draw_hex(surface, RADIATION_COLOR, (x+(i*in_radius*2), y+(j*radius*1.5)), radius, 1)

def draw_hex(surface, color, center_position, radius, width):	# horizontal-stacked orientation. width=0 means a filled-in polygon
	x, y = center_position
	points = []
	for i in range(6):
		points.append( (x + radius * math.cos((2 * math.pi * i / 6) + (math.pi / 2)), y + radius * math.sin((2 * math.pi * i / 6) + (math.pi / 2))) )
	pygame.draw.polygon(surface, color, points, width)

def draw_text(surface, text):
	font = pygame.font.Font()
	text_image = font.render(text, True, "white")
	surface.blit(text_image, (3, WINDOW_SIZE_Y - 12))

def log_text(text):
	if LOG_TO_CONSOLE:
		print(text)

class Tile:
	def __init__(self, terrain_type="random", lit=False, irradiated=False):
		self.terrain = terrain_type
		if terrain_type == "random": self.terrain = random.choice(["land", "water", "chasm"])
		self.is_lit = lit
		self.is_rad = irradiated
		self.organisms = []
	def sunrise(self):
		self.is_lit = True
	def sunset(self):
		self.is_lit = False
	def blast(self):
		self.is_rad = True
	def cool(self):
		self.is_rad = False
	def move_in(self, organism):
		# these are called by Grid.relocate_organism, prefer that where possible
		self.organisms.append(organism)
	def move_out(self, organism):
		self.organisms.remove(organism)
	def largest_organism(self, except_for=None):
		size = -math.inf
		largest = None
		for o in self.organisms:
			if o.is_alive() and o.size > size and o is not except_for:
				size = o.size
				largest = o
		return largest
	def smallest_organism(self, except_for=None):
		size = math.inf
		smallest = None
		for o in self.organisms:
			if o.is_alive() and o.size < size and o is not except_for:
				size = o.size
				smallest = o
		return smallest
	def noise(self, volume, direction):
		for o in self.organisms:
			if o.noise_volume < volume:
				o.notice(True, direction, volume)
	def contains_organisms(self):
		has_one = False
		for o in self.organisms:
			if o.is_alive():
				has_one = True
		return has_one
	def contains_smaller_than(self, size):
		has_one = False
		for o in self.organisms:
			if o.is_alive() and o.size < size:
				has_one = True
		return has_one
	def contains_larger_than(self, size):
		has_one = False
		for o in self.organisms:
			if o.is_alive() and o.size > size:
				has_one = True
		return has_one
	def contains_similar_to(self, organism):
		has_one = False
		for o in self.organisms:
			if o.is_alive() and o.looks_the_same_as(organism) and o is not organism:
				has_one = True
		return has_one
	def contains_different_from(self, organism):
		has_one = False
		for o in self.organisms:
			if o.is_alive() and o.looks_different_from(organism):
				has_one = True
		return has_one
	def contains_photosynthesizing_organism(self):
		has_one = False
		for o in self.organisms:
			if o.is_alive():
				xg = o.genes[:(int(o.size) + 1)]
				if "a" in "".join(xg):
					has_one = True
		return has_one
	def contains_mobile_organism(self):
		has_one = False
		for o in self.organisms:
			if o.is_alive():
				xg = o.genes[:(int(o.size) + 1)]
				for c in "lmnopqrs":
					if c in "".join(xg):
						has_one = True
		return has_one
	def contains_biting_organism(self):
		has_one = False
		for o in self.organisms:
			if o.is_alive():
				xg = o.genes[:(int(o.size) + 1)]
				for c in "tu":
					if c in "".join(xg):
						has_one = True
		return has_one

class Grid:
	# horizontally-stacked hexes. wobbly going straight up and down, which affects the math to determine which hexes are neighbors
	# |x0,y0| 1,0 | 2,0 | 3,0 |
	#    | 0,1 | 1,1 | 2,1 | 3,1 |
	# | 0,2 | 1,2 | 2,2 | 3,2 |
	#    | 0,3 | 1,3 | 2,3 | 3,3 |
	def __init__(self, size_x, size_y):
		# generate a list[x][y] of random unlit Tiles
		self.size_x = size_x
		self.size_y = size_y
		self.tile = []
		for i in range(size_x):
			self.tile.append([])
			for j in range(size_y):
				self.tile[i].append(Tile())
	def smooth(self):
		# randomly change the terrain type of Tiles based on their neighbors, smoothing out the randomness in the grid
		for i in range(self.size_x):
			for j in range(self.size_y):
				terrain_list = []
				terrain_list.append(self.tile[i][j].terrain)
				nx, ny = self.neighbor1(i, j)
				terrain_list.append(self.tile[nx][ny].terrain)
				nx, ny = self.neighbor2(i, j)
				terrain_list.append(self.tile[nx][ny].terrain)
				nx, ny = self.neighbor3(i, j)
				terrain_list.append(self.tile[nx][ny].terrain)
				nx, ny = self.neighbor4(i, j)
				terrain_list.append(self.tile[nx][ny].terrain)
				nx, ny = self.neighbor5(i, j)
				terrain_list.append(self.tile[nx][ny].terrain)
				nx, ny = self.neighbor6(i, j)
				terrain_list.append(self.tile[nx][ny].terrain)
				self.tile[i][j].terrain = random.choice(terrain_list)
	def create_sun(self, sun_size):
		# add the sun to an otherwise dark grid. starts in the center and spirals outward. creates the sun at the eastern end of the grid at the equator
		# TODO consider making it a circle instead of a hexagon.
		next_x = self.size_x - sun_size - 1
		next_y = int(self.size_y / 2)
		for i in range(sun_size):
			self.tile[next_x][next_y].sunrise()
			next_x, next_y = self.neighbor1(next_x, next_y)
			for j in range(i):
				self.tile[next_x][next_y].sunrise()
				next_x, next_y = self.neighbor3(next_x, next_y)
			for j in range(i):
				self.tile[next_x][next_y].sunrise()
				next_x, next_y = self.neighbor4(next_x, next_y)
			for j in range(i):
				self.tile[next_x][next_y].sunrise()
				next_x, next_y = self.neighbor5(next_x, next_y)
			for j in range(i):
				self.tile[next_x][next_y].sunrise()
				next_x, next_y = self.neighbor6(next_x, next_y)
			for j in range(i):
				self.tile[next_x][next_y].sunrise()
				next_x, next_y = self.neighbor1(next_x, next_y)
			for j in range(i):
				self.tile[next_x][next_y].sunrise()
				next_x, next_y = self.neighbor2(next_x, next_y)
	def neighbor1(self, x, y):
		# return the coordinates of the 1 o'clock neighbor of the given x,y coordinates on this grid.
		# modulo math should cause the grid to wrap around donut-style. (probably wonky at the top and bottom edges if size_y is odd.) TODO make sure the wraparound works properly
		if y % 2 == 0:
			return x, (y-1) % self.size_y
		else:
			return (x+1) % self.size_x, (y-1) % self.size_y
	def neighbor2(self, x, y):
		# 3 o'clock
		return (x+1) % self.size_x, y
	def neighbor3(self, x, y):
		# 5 o'clock
		if y % 2 == 0:
			return x, (y+1) % self.size_y
		else:
			return (x+1) % self.size_x, (y+1) % self.size_y
	def neighbor4(self, x, y):
		# 7 o'clock
		if y % 2 == 0:
			return (x-1) % self.size_x, (y+1) % self.size_y
		else:
			return x, (y+1) % self.size_y
	def neighbor5(self, x, y):
		# 9 o'clock
		return (x-1) % self.size_x, y
	def neighbor6(self, x, y):
		# 11 o'clock
		if y % 2 == 0:
			return (x-1) % self.size_x, (y-1) % self.size_y
		else:
			return x, (y-1) % self.size_y
	def neighbor(self, x, y, direction):
		if direction == "1": return self.neighbor1(x, y)
		if direction == "2": return self.neighbor2(x, y)
		if direction == "3": return self.neighbor3(x, y)
		if direction == "4": return self.neighbor4(x, y)
		if direction == "5": return self.neighbor5(x, y)
		if direction == "6": return self.neighbor6(x, y)
		return None	# TODO should probably throw an exception here instead...
	def organisms(self):
		organism_list = []
		for i in range(self.size_x):
			for j in range(self.size_y):
				for o in self.tile[i][j].organisms:
					if o.is_alive(): organism_list.append(o)
		return sorted(organism_list, key=lambda o: o.id)
	def relocate_organism(self, organism, new_x, new_y):
		old_x, old_y = organism.x_pos, organism.y_pos
		self.tile[old_x][old_y].move_out(organism)
		self.tile[new_x][new_y].move_in(organism)
		organism.change_position(new_x, new_y)
	def noise(self, x, y, volume):
		current_x, current_y = x, y
		self.tile[current_x][current_y].noise(volume, "7")
		current_x, current_y = self.neighbor1(x, y)
		self.tile[current_x][current_y].noise(volume, "4")	# direction should be toward the noise, which is back toward this tile
		current_x, current_y = self.neighbor2(x, y)
		self.tile[current_x][current_y].noise(volume, "5")
		current_x, current_y = self.neighbor3(x, y)
		self.tile[current_x][current_y].noise(volume, "6")
		current_x, current_y = self.neighbor4(x, y)
		self.tile[current_x][current_y].noise(volume, "1")
		current_x, current_y = self.neighbor5(x, y)
		self.tile[current_x][current_y].noise(volume, "2")
		current_x, current_y = self.neighbor6(x, y)
		self.tile[current_x][current_y].noise(volume, "3")

class Organism:
	id = 0
	def __init__(self, x_position, y_position, starting_energy, growth_log_base, genome=[], stimulus=False, stimulus_direction="0", noise_volume=0):
		Organism.id += 1
		self.id = Organism.id
		self.x_pos = x_position
		self.y_pos = y_position
		self.energy = starting_energy
		self.growth_log_base = growth_log_base
		self.size = 0
		self.genes = copy.deepcopy(genome)
		if not self.genes: self._develop_new_gene()
		self.stimulus = stimulus
		self.stim_direction = stimulus_direction
		self.noise_volume = noise_volume
		self.color = pygame.Color(0,0,0)
		self.update_color()
		self.grow()
	def grow(self):
		if self.is_alive():
			if self.size < math.log(self.energy, self.growth_log_base):
				self.size = math.log(self.energy, self.growth_log_base)
	def _develop_new_gene(self):
		gene = random.choice(string.ascii_lowercase) + random.choice(string.digits)
		self.genes.append(gene)
	def adjust_energy(self, amount):
		self.energy += amount
		if self.is_alive(): self.grow()
	def change_position(self, new_x, new_y):
		# this is called by Grid.relocate_organism, prefer that where possible
		self.x_pos = new_x
		self.y_pos = new_y
	def mutate(self):
		mutant_location = random.randrange(len(self.genes))
		mutation_type = random.choice(["substitute", "insert", "delete", "translocate"])
		if mutation_type == "substitute":
			mutant_gene = self.genes.pop(mutant_location)
			if random.random() < 0.5:
				mutant_gene = random.choice(string.ascii_lowercase) + mutant_gene[1]
			else:
				mutant_gene = mutant_gene[0] + random.choice(string.digits)
			self.genes.insert(mutant_location, mutant_gene)
		elif mutation_type == "insert":
			self.genes.insert(mutant_location, random.choice(string.ascii_lowercase) + random.choice(string.digits))
		elif mutation_type == "delete":
			self.genes.pop(mutant_location)
			if not self.genes: self.adjust_energy(-1 * self.energy)
		else:	# "translocate"
			mutant_gene = self.genes.pop(mutant_location)
			self.genes.insert(random.randrange(len(self.genes) + 1), mutant_gene)
		self.update_color()
	def is_alive(self):
		# if it doesn't have at least one full unit of energy left, it dies of starvation.
		# be sure to check this before doing other things... we don't want an army of undead.
		return self.energy >= 1
	def notice(self, stimulus, stimulus_direction, noise_volume=0):
		self.stimulus = stimulus	# whether the thing we're looking for was actually there or not
		self.stim_direction = stimulus_direction
		self.noise_volume = noise_volume
	def ignore(self):
		self.stimulus = False
		self.stim_direction = "0"
		self.noise_volume = 0
	def looks_the_same_as(self, other):
		# compares expressed genes, not all genes, and only compares as far as the smaller organism. things recognized earlier may grow up to be different!
		my_xg = self.genes[:(int(self.size) + 1)]
		other_xg = other.genes[:(int(self.size) + 1)]
		if len(my_xg) > len(other_xg):
			my_xg = my_xg[:len(other_xg)]
		else:
			other_xg = other_xg[:len(my_xg)]
		return my_xg == other_xg
	def looks_different_from(self, other):
		return not self.looks_the_same_as(other)
	def update_color(self):
		hashval = hash("".join(self.genes))
		r = hashval % 256
		hashval = int(hashval / 256)
		g = hashval % 256
		hashval = int(hashval / 256)
		b = hashval % 256
		if LIFE_USE_BRIGHT_COLORS_ONLY:
			if r > g and r > b:
				r = 255
			elif g > b:
				g = 255
			else:
				b = 255
		self.color = pygame.Color(r,g,b)
	def eat(self, target, efficiency):
		if target:
			amount = self.size
			if target.energy < amount: amount = target.energy
			self.adjust_energy(amount * efficiency)
			target.adjust_energy(-1 * amount)

if __name__ == '__main__': main()
