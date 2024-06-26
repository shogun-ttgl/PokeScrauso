import pygame
from settings import *
from logic.cameraGroup.bush import Bush
from logic.cameraGroup.tree_top import TreeTop

class CameraGroup(pygame.sprite.Group):
    def __init__(self, screen):
        super().__init__()
        self.display_surface = screen

        #Dimensions
        self.half_w = self.display_surface.get_width() // 2
        self.half_h = self.display_surface.get_height() // 2

        #Game variables
        self.level_num = 0
        self.zone_num = 0
        self.last_player_collision_verse = "down" #Direzione che aveva il giocatore nell'ultimo cambio di zona
                                                  #utilizzata per implementare una funzione rudimentale di frustum culling
        #Camera offset
        self.offset = pygame.math.Vector2()

        #Dichiarazione di variabili temporanee per gli offset
        self.offset_pos_sprites = 0
        self.offset_pos_ground = 0

        #Camera zoom
        self.zoom_scale = INITIAL_ZOOM
        self.internal_surface_size = INTERNAL_SURFACE_SIZE #Per garantire che la camera possa zoomare si fanno tutte le operazioni di draw su una superficie interna che verrà poi scalata
        self.internal_surface = pygame.Surface(self.internal_surface_size, pygame.SRCALPHA)
        self.internal_surface_rect = self.internal_surface.get_rect(center = (self.half_w, self.half_h))
        self.internal_surface_size_vector = pygame.math.Vector2(self.internal_surface_size) #
        self.internal_offset = pygame.math.Vector2(0,0)
        self.internal_offset.x = self.internal_surface_size_vector.x // 2 - self.half_w
        self.internal_offset.y = self.internal_surface_size_vector.y // 2 - self.half_h

        #Ground images
        self.ground_surf_1_1 = pygame.image.load("graphics/world_sprites/1_1.png").convert_alpha()
        self.ground_surf_1_2 = pygame.image.load("graphics/world_sprites/1_2.png").convert_alpha()
        self.ground_surf_1_3 = pygame.image.load("graphics/world_sprites/1_3.png").convert_alpha()
        self.ground_surf_1_4 = pygame.image.load("graphics/world_sprites/1_4.png").convert_alpha()
        self.ground_surfaces_1 = [self.ground_surf_1_1, self.ground_surf_1_2, self.ground_surf_1_3, self.ground_surf_1_4]  

        self.ground_rect_1_1 = self.ground_surf_1_1.get_rect(topleft = (0,0))
        self.ground_rect_1_2 = self.ground_surf_1_2.get_rect(topleft = (self.ground_rect_1_1.bottomleft[0] + 1055, self.ground_rect_1_1.bottomleft[1]))
        self.ground_rect_1_3 = self.ground_surf_1_3.get_rect(topleft = (self.ground_rect_1_2.bottomleft[0] + 95, self.ground_rect_1_2.bottomleft[1]))
        self.ground_rect_1_4 = self.ground_surf_1_4.get_rect(topleft = (self.ground_rect_1_3.bottomleft[0] + 500, self.ground_rect_1_3.bottomleft[1] - 500))
        self.ground_rects_1 = [self.ground_rect_1_1, self.ground_rect_1_2, self.ground_rect_1_3, self.ground_rect_1_4]

        #Collision maps (per debugging da togliere)
        self.first_level_first_zone = pygame.image.load("graphics/collision_maps/1_1.png").convert_alpha()
        self.first_level_first_zone.set_alpha(192)
        self.first_level_second_zone = pygame.image.load("graphics/collision_maps/1_2.png").convert_alpha()
        self.first_level_second_zone.set_alpha(192)
        self.first_level_third_zone = pygame.image.load("graphics/collision_maps/1_3.png").convert_alpha()
        self.first_level_third_zone.set_alpha(192)
        self.first_level_fourth_zone = pygame.image.load("graphics/collision_maps/1_4.png").convert_alpha()
        self.first_level_fourth_zone.set_alpha(192)
        self.first_level_maps = [self.first_level_first_zone, self.first_level_second_zone, self.first_level_third_zone, self.first_level_fourth_zone]

        self.first_level_first_zone_rect = self.first_level_first_zone.get_rect(topleft = (0,0))
        self.first_level_second_zone_rect = self.first_level_second_zone.get_rect(topleft = (self.ground_rect_1_1.bottomleft[0] + 1055, self.ground_rect_1_1.bottomleft[1]))
        self.first_level_third_zone_rect = self.first_level_third_zone.get_rect(topleft = (self.ground_rect_1_2.bottomleft[0] + 95, self.ground_rect_1_2.bottomleft[1]))
        self.first_level_fourth_zone_rect = self.first_level_fourth_zone.get_rect(topleft = (self.ground_rect_1_3.bottomleft[0] + 500, self.ground_rect_1_3.bottomleft[1] - 500))
        self.first_level_maps_rects = [self.first_level_first_zone_rect, self.first_level_second_zone_rect, self.first_level_third_zone_rect, self.first_level_fourth_zone_rect]

        #Variabili per rendering
        self.ground_surfaces = self.ground_surfaces_1
        self.ground_rects = self.ground_rects_1

        #Variabili per collisioni
        self.last_player_pos_offsetted = pygame.math.Vector2()

    def keyboard_zoom_control(self):
        keys = pygame.key.get_pressed()
        if keys[ZOOM_OUT_KEY] and self.zoom_scale < ZOOM_SCALE_LIMITS[1]:
            self.zoom_scale += ZOOM_SCALING_VELOCITY
        elif keys[ZOOM_IN_KEY] and self.zoom_scale > ZOOM_SCALE_LIMITS[0]:
            self.zoom_scale -= ZOOM_SCALING_VELOCITY

    def center_target_camera(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

    def calculate_new_player_relative_coords(self): #pygame.math.Vector2 - pygame.math.Vector2 
        return self.last_player_pos_offsetted - (self.ground_rects[self.zone_num].topleft + self.offset + self.internal_offset)

    def draw_ground_zones(self):
        print("zone_num", self.zone_num, "zone_num-- =", self.zone_num - 1, "zone_num++ =", self.zone_num + 1, "last_verse", self.last_player_collision_verse)
        
        # Determine the range of zones to draw based on conditions
        start_zone = max(self.zone_num - 1, 0)  # Ensure we don't go below 0
        end_zone = min(self.zone_num + 1, len(self.ground_surfaces) - 1)  # Ensure we don't go beyond the last index
        
        # Loop through the determined range and blit each zone
        for zone_index in range(start_zone, end_zone + 1):
            offset_pos_ground = self.ground_rects[zone_index].topleft + self.offset + self.internal_offset
            self.internal_surface.blit(self.ground_surfaces[zone_index], offset_pos_ground)  
        
        #Draws the collision maps for debugging purposes
        self.internal_surface.blit(self.first_level_maps[self.zone_num], self.ground_rects[self.zone_num].topleft + self.offset + self.internal_offset)

    def custom_draw(self, player):

        self.keyboard_zoom_control()
        self.center_target_camera(player)

        self.internal_surface.fill(BACKGROUND_COLOR)

        #Elementi passivi
        self.draw_ground_zones()
        
        #Elementi attivi
        for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
            self.offset_pos_sprites = sprite.rect.topleft - self.offset + self.internal_offset
            if sprite == player: self.last_player_pos_offsetted = sprite.rect.midbottom - self.offset + self.internal_offset #Distinguo il player per poterne calcolare le coordinate relative
            self.internal_surface.blit(sprite.image, self.offset_pos_sprites) #Calcolo con il punto midbottom per non prendere in considerazione i circa 30 pixel di altezza del player

        #print("Zona num", self.zone_num, "at", datetime.datetime.now())

        scaled_surface = pygame.transform.scale(self.internal_surface, self.internal_surface_size_vector * self.zoom_scale)
        scaled_rect = scaled_surface.get_rect(center = (self.half_w, self.half_h))
        self.display_surface.blit(scaled_surface, scaled_rect)

    def load_secondary_sprites(self):
        #Tree tops
        self.tree_tops_1 = [
            [TreeTop(self, (100, 100)), TreeTop(self, (200, 200)), TreeTop(self, (300, 300))],
            [TreeTop(self, (400, 400)), TreeTop(self, (500, 500)), TreeTop(self, (600, 600))]
        ]