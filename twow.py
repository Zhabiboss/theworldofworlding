import os
import pygame
import pymunk
import pymunk.pygame_util
import math
import random
import json
import sys
from GUI import *

pygame.init()

class Particle:
    def __init__(self, engine, position, velocity, lifespan, color):
        self.x, self.y = position
        self.vx, self.vy = velocity
        self.lifespan = lifespan
        self.color = color
        self.engine = engine
        self.texture = pygame.Surface((10, 10))
        self.texture.fill(color)
        self.timer = 0
        self.dead = False
        pygame.draw.rect(self.texture, (0, 0, 0), (0, 0, 10, 10), 1)

    def update(self):
        self.x += self.vx * self.engine.dt
        self.y += self.vy * self.engine.dt
        self.timer += self.engine.dt
        if self.timer >= self.lifespan:
            self.dead = True

    def draw(self):
        self.engine.screen.blit(self.texture, (self.x - 5, self.y - 5))

class fonts:
    small_font = pygame.font.Font("Resources/fonts/CONSOLA.TTF", 16)
    normal_font = pygame.font.Font("Resources/fonts/CONSOLA.TTF", 32)

class Engine:
    def __init__(self, screen, fps = 500):
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.screen = screen
        self.running = True
        self.clock = pygame.time.Clock()
        self.space = pymunk.Space()
        self.space.gravity = (0, 980)  # Gravity directed downwards
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.fps = fps
        self.player: Player = None
        self.objects: list[Object | Spike | FinishLine] = []
        self.textures = {"player": pygame.transform.scale(pygame.image.load("Resources/player.png"), (50, 50)),
                         "object": pygame.image.load("Resources/object.png")}  # Dictionary to hold textures
        self.small_font = fonts.small_font
        self.initial_player_position = (0, 0)
        self.particles: list[Particle] = []
        self.time = 0
        self.quit_type = None

    def add_texture(self, name, filepath):
        try:
            self.textures[name] = pygame.image.load(filepath)
        except pygame.error as e:
            print(f"Error loading texture {name}: {e}")

    def add_object(self, object):
        self.objects.append(object)
        self.space.add(object.body, object.shape)

    def add_player(self, player):
        self.player = player
        self.space.add(self.player.body, self.player.shape)
        self.initial_player_position = player.body.position.x, player.body.position.y

    def get_colliding_objects(self):
        colliding_objects = []
        # Use the player's shape to check for collisions
        bb = self.player.shape.bb  # Get the bounding box of the player
        # Query the space for overlapping shapes
        query = self.space.bb_query(bb, self.player.shape.filter)
        for shape in query:
            if shape != self.player.shape:
                colliding_objects.append(shape.type)
        return colliding_objects

    def blit_rotate(self, image, pos, originPos, angle):

        # offset from pivot to center
        image_rect = image.get_rect(topleft = (pos[0] - originPos[0], pos[1]-originPos[1]))
        offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
        
        # roatated offset from pivot to center
        rotated_offset = offset_center_to_pivot.rotate(-angle)

        # roatetd image center
        rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)

        # get a rotated image
        rotated_image = pygame.transform.rotate(image, angle)
        rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

        # rotate and blit the image
        self.screen.blit(rotated_image, rotated_image_rect)
    
        # draw rectangle around the image
        #pygame.draw.rect(surf, (255, 0, 0), (*rotated_image_rect.topleft, *rotated_image.get_size()), 2)

    @property
    def dt(self):
        return 1 / self.clock.get_fps() if self.clock.get_fps() != 0 else 1 / self.fps

    def run(self):
        while True:
            quit_ = False
            self.quit_type = None
            self.is_key_pressed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    self.is_key_pressed = True
                    if event.key == pygame.K_SPACE:
                        self.player.body.velocity = (self.player.body.velocity[0], max(-600, self.player.body.velocity[1] - 300))
                    if event.key == pygame.K_ESCAPE:
                        quit_ = True
                        self.quit_type = "quit"

            self.space.step(self.dt)
            self.screen.fill((0, 0, 0))

            for obj in self.objects:
                if obj.texture_name and obj.texture_name in self.textures:
                    texture = pygame.transform.scale(self.textures[obj.texture_name], obj.size)
                    self.screen.blit(texture, (obj.body.position.x - obj.size[0] // 2, obj.body.position.y - obj.size[1] // 2))
                else:
                    if obj.shape.type == "object": color = (100, 100, 100)
                    if obj.shape.type == "spike": color = (255, 0, 0)
                    if obj.shape.type == "finish": color = (0, 255, 0)
                    pygame.draw.rect(self.screen, color,
                                    (obj.body.position.x - obj.size[0] // 2, obj.body.position.y - obj.size[1] // 2, obj.size[0], obj.size[1]))

            self.player.update(self.is_key_pressed)

            if "spike" in self.get_colliding_objects():
                for i in range(random.randint(5, 10)):
                    self.particles.append(Particle(self, (self.player.body.position.x, self.player.body.position.y),
                                                   (random.randint(-300, 300), random.randint(-300, 300)), 0.5, (255, 0, 0)))
                self.space.remove(self.player.shape)
                self.add_player(Player(self, self.initial_player_position, self.player.texture_name))

            if "finish" in self.get_colliding_objects():
                quit_ = True
                self.quit_type = "finish"

            if self.player.texture_name:
                self.blit_rotate(self.textures[self.player.texture_name], (self.player.body.position.x, self.player.body.position.y), (25, 25), -math.degrees(self.player.body.angle))
            else:
                surf = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.rect(surf, (0, 255, 0), (0, 0, 50, 50))
                self.blit_rotate(surf, (self.player.body.position.x, self.player.body.position.y), (25, 25), -math.degrees(self.player.body.angle))

            for particle in self.particles:
                particle.update()
                particle.draw()
                if particle.dead:
                    self.particles.remove(particle)

            text_1 = self.small_font.render(f"fps: {self.clock.get_fps() :.1f}", True, "white", "black")
            self.screen.blit(text_1, (0, 0))
            text_2 = self.small_font.render(f"difference: {round(self.clock.get_fps() - self.fps)}" if self.clock.get_fps() <= self.fps else \
                                            f"difference: +{round(self.clock.get_fps() - self.fps)}", True, "white", "black")
            self.screen.blit(text_2, (0, text_1.get_height()))
            text_3 = self.small_font.render(f"time: {round(self.time, 2)}", True, "white", "black")
            self.screen.blit(text_3, (0, text_1.get_height() + text_2.get_height()))

            if quit_: break

            pygame.display.flip()
            self.clock.tick(self.fps)
            self.time += self.dt


class Player:
    def __init__(self, engine, position, texture_name = None):
        self.body = pymunk.Body(body_type = pymunk.Body.DYNAMIC)
        self.body.position = position
        self.shape = pymunk.Poly.create_box(self.body, (50, 50))
        self.shape.density = 1
        self.shape.elasticity = 0.8
        self.shape.friction = 8.0
        self.texture_name = texture_name
        self.engine = engine

    def update(self, is_key_pressed):
        keys = pygame.key.get_pressed()
        
        # Determine the desired horizontal velocity
        vx = 0
        vy = 0
        if keys[pygame.K_a]:
            if keys[pygame.K_LCTRL]:
                vx -= 5 * self.engine.dt * 60       #   The 60 unit multiplier is added, because the engine was tested without deltaTime on 60+-5 fps.
            vx -= 15 * self.engine.dt * 60          #   This was done to prevent the player from overaccelerating when holding the control keys
        if keys[pygame.K_d]:                        #   at high fps. Even though the physics engine is calculating the space state using the
            if keys[pygame.K_LCTRL]:                #   deltaTime the velocity is being added at each holding frame with the same amount as at 60fps,
                vx += 5 * self.engine.dt * 60       #   so the deltaTime still has to be applied when calculating player movement.
            vx += 15 * self.engine.dt * 60
        if keys[pygame.K_s]:
            vy += 45 * self.engine.dt * 60

        # Apply horizontal velocity while maintaining current vertical velocity
        self.body.velocity = (min(max(-600, self.body.velocity[0] + vx), 600), self.body.velocity[1] + vy)
        
        if is_key_pressed:
            if keys[pygame.K_q]:
                self.body.velocity = (max(-600, self.body.velocity[0] - 300), self.body.velocity[1])
            if keys[pygame.K_e]:
                self.body.velocity = (min(600, self.body.velocity[0] + 300), self.body.velocity[1])

class Object:
    def __init__(self, position, size, texture_name = None):
        self.body = pymunk.Body(body_type = pymunk.Body.STATIC)
        self.body.position = position
        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.friction = 8.0
        self.shape.elasticity = 0.4
        self.texture_name = texture_name
        self.size = size
        self.shape.type = "object"

class Spike:
    def __init__(self, position, size, texture_name = None):
        self.body = pymunk.Body(body_type = pymunk.Body.STATIC)
        self.body.position = position
        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.friction = 8.0
        self.shape.elasticity = 0.4
        self.texture_name = texture_name
        self.size = size
        self.shape.type = "spike"

class FinishLine:
    def __init__(self, position, size, texture_name = None):
        self.body = pymunk.Body(body_type = pymunk.Body.STATIC)
        self.body.position = position
        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.friction = 8.0
        self.shape.elasticity = 0.4
        self.texture_name = texture_name
        self.size = size
        self.shape.type = "finish"

def load_level(engine: Engine, level_file_path: str):
    with open(level_file_path, "r") as level:
        content = level.read()
        content = content.replace("\n", "").split(";")
        for line in content:
            if line.startswith("player"):
                _, x, y = line.split(" ")
                engine.add_player(Player(engine, (float(x), float(y)), "player"))
            if line.startswith("object"):
                _, x, y, width, height = line.split(" ")
                engine.add_object(Object((float(x), float(y)), (float(width), float(height))))
            if line.startswith("spike"):
                _, x, y, width, height = line.split(" ")
                engine.add_object(Spike((float(x), float(y)), (float(width), float(height))))
            if line.startswith("finish"):
                _, x, y, width, height = line.split(" ")
                engine.add_object(FinishLine((float(x), float(y)), (float(width), float(height))))
        
        level.close()

class LevelEditor:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width, self.height = self.screen.get_width(), self.screen.get_height()
        self.objects = []
        self.spikes = []
        self.finishes = []
        self.player_pos = (self.width // 2, self.height // 2)
        self.current_object_type = "object"
        self.states = []
        self.selected_object = None
        self.clock = pygame.time.Clock()
        self.content = ""

    @property
    def dt(self):
        return 1 / self.clock.get_fps() if self.clock.get_fps() != 0 else 1 / self.fps
        
    def run(self):
        while True:
            quit_ = False

            self.screen.fill((0, 0, 0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.current_object_type == "object":
                        self.objects.append([*pygame.mouse.get_pos(), 50, 50])
                        self.selected_object = len(self.objects) - 1
                    if self.current_object_type == "spike":
                        self.spikes.append([*pygame.mouse.get_pos(), 50, 50])
                        self.selected_object = len(self.spikes) - 1
                    if self.current_object_type == "finish":
                        self.finishes.append([*pygame.mouse.get_pos(), 50, 50])
                        self.selected_object = len(self.finishes) - 1
                    if self.current_object_type == "player":
                        self.player_pos = pygame.mouse.get_pos()
                    
                    self.states.append((self.objects, self.spikes))

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        quit_ = True

                    if event.key == pygame.K_z:
                        if self.states != []:
                            self.objects = self.states[-1][0]
                            self.spikes = self.states[-1][1]
                    
                    if event.key == pygame.K_o:
                        self.current_object_type = "object"
                        self.selected_object = len(self.objects)
                    
                    if event.key == pygame.K_p:
                        self.current_object_type = "spike"
                        self.selected_object = len(self.spikes)

                    if event.key == pygame.K_f:
                        self.current_object_type = "finish"
                        self.selected_object = len(self.finishes)

                    if event.key == pygame.K_l:
                        self.current_object_type = "player"

                    if event.key == pygame.K_SPACE:
                        content = f"player {self.player_pos[0]} {self.player_pos[1]};\n"
                        for object in self.objects:
                            content += f"object {object[0]} {object[1]} {object[2]} {object[3]};\n"
                        for spike in self.spikes:
                            content += f"spike {spike[0]} {spike[1]} {spike[2]} {spike[3]};\n"
                        for finish in self.finishes:
                            content += f"finish {finish[0]} {finish[1]} {finish[2]} {finish[3]};\n"
                        self.content = content
            
                
            keys = pygame.key.get_pressed()
            if not keys[pygame.K_LCTRL]:
                if keys[pygame.K_w]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][3] += self.dt * 120
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][3] += self.dt * 120
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][3] += self.dt * 120
                if keys[pygame.K_s]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][3] -= self.dt * 120
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][3] -= self.dt * 120
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][3] -= self.dt * 120
                if keys[pygame.K_a]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][2] -= self.dt * 120
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][2] -= self.dt * 120
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][2] -= self.dt * 120
                if keys[pygame.K_d]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][2] += self.dt * 120
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][2] += self.dt * 120
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][2] += self.dt * 120
            else:
                if keys[pygame.K_w]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][1] -= self.dt * 180
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][1] -= self.dt * 180
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][1] -= self.dt * 180
                if keys[pygame.K_s]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][1] += self.dt * 180
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][1] += self.dt * 180
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][1] += self.dt * 180
                if keys[pygame.K_a]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][0] -= self.dt * 180
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][0] -= self.dt * 180
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][0] -= self.dt * 180
                if keys[pygame.K_d]:
                    if self.current_object_type == "object":
                        if self.objects != []: self.objects[self.selected_object][0] += self.dt * 180
                    if self.current_object_type == "spike":
                        if self.spikes != []: self.spikes[self.selected_object][0] += self.dt * 180
                    if self.current_object_type == "finish":
                        if self.finishes != []: self.finishes[self.selected_object][0] += self.dt * 180

            for object in self.objects:
                pygame.draw.rect(self.screen, (100, 100, 100), (object[0] - object[2] / 2, object[1] - object[3] / 2, object[2], object[3]))
            for spike in self.spikes:
                pygame.draw.rect(self.screen, (255, 0, 0), (spike[0] - spike[2] / 2, spike[1] - spike[3] / 2, spike[2], spike[3]))
            for finish in self.finishes:
                pygame.draw.rect(self.screen, (0, 255, 0), (finish[0] - finish[2] / 2, finish[1] - finish[3] / 2, finish[2], finish[3]))
            
            pygame.draw.rect(self.screen, (0, 0, 255), (self.player_pos[0] - 25, self.player_pos[1] - 25, 50, 50))

            if quit_: break

            pygame.display.update()
            self.clock.tick()

class MenuBaseplate:
    def __init__(self, screen):
        self.screen = screen
        self.gui = GUI(self.screen)
        
    def run(self):
        while True:
            self.screen.fill((0, 0, 0))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.gui.update()
            self.gui.draw()

            pygame.display.update()

def generate_random_level_name():
    name = ""
    name += random.choice(["realistic", "unmatched", "hydrogen", "aerogelic", "light", "heavy", "rainy", "iron", "questionable", "great", "amazing", "2d", "absolute", "bad", "terrible", "horrible", "revised", "educational", "destructive", "restored", "astrological", "astronomic", "isoteric"]) + " "
    name += random.choice(["engine-made", "worlded", "giga", "mega", "ultra", "google", "systematic", "downward", "upward", "unexplored", "warped", "cursed", "blessed", "blursed", "screeching", "screaming", "silent", "loud", "quiet", "terrific", "compact", "multi purpose"]) + " "
    name += random.choice(["level", "map", "world", "player-area", "can", "hellscape", "ruins", "game", "spike pit", "land", "island", "street", "country", "continent", "house", "eraser", "pencil", "pen", "pencil case", "tablet", "frog", "cat", "dog", "zebra", "horse", "dumbell"]) + " "
    name += str(random.randint(0, 99999))
    return name

class MainMenu(MenuBaseplate):
    def __init__(self, screen):
        super().__init__(screen)
        def load_buttons():
            level_count = 0
            with open("Data/level_records.json", "r") as file:
                self.high_scores = json.loads(file.read())
                file.close()
            for file in os.listdir("Levels"):
                if file.endswith(".wowlvl"):
                    if not file[:-7] in self.high_scores:
                        self.high_scores[file[:-7]] = "None"

                    def start_level(file = file):
                        settings = json.loads(open("Resources/settings.json", "r").read())
                        fps = settings["fps"]
                        engine = Engine(self.screen, fps)
                        load_level(engine, f"Levels/{file}")
                        engine.run()
                        if engine.quit_type == "finish":
                            highscore = round(engine.time, 2)

                            if self.high_scores[file[:-7]] == "None" or highscore < self.high_scores[file[:-7]]:
                                self.high_scores[file[:-7]] = highscore
                                with open("Data/level_records.json", "w") as file_:
                                    file_.write(json.dumps(self.high_scores, indent = 4))
                                    file_.close()
                                load_buttons()

                    self.__setattr__(f"{file[:-7]}_level", start_level) # __setattr__ bc no way i am doing that in any other way
                    self.gui.buttons.append(Button(self.screen, 
                                                0, 50 * level_count, 1080, 50, 
                                                "white", "lime", 
                                                Text(fonts.normal_font, f"{file[:-7]} | time: {self.high_scores[file[:-7]]}", "black"),
                                                self.__getattribute__(f"{file[:-7]}_level")))
                    level_count += 1
            self.gui.buttons.append(Button(self.screen, 0, 50 * level_count, 1080, 50, "white", "lime", Text(fonts.normal_font, "Start level editor", "black"), self.start_level_editor))

        load_buttons()
                            
    def start_level_editor(self):
        level_editor = LevelEditor(self.screen)
        level_editor.run()
        content = level_editor.content
        name = generate_random_level_name() + ".wowlvl"
        with open(name, "w") as file:
            file.write(content)
            file.close()
        print(f"saved new level as {name}")

if __name__ == "__main__":
    res = width, height = 1080, 720
    screen = pygame.display.set_mode(res)
    menu = MainMenu(screen)
    menu.run()