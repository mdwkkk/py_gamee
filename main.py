import pygame
import sys
import settings
import random
from sprites import Bullet, AlienBug, TankBug, Turret, FloatingText
from ui import Button, ImageButton


class OutpostDefenseGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
        pygame.display.set_caption("Whiskey Outpost")
        self.clock = pygame.time.Clock()
        self.running = True
        self.waves = [
            {
                "normal_count": 5, "normal_hp": 100, "normal_speed": 100,
             "tank_count": 0, "tank_hp": 0, "tank_speed": 0,
              "interval": 1.2, "road": settings.WAYPOINTS_3
              },
            {
                "normal_count": 10, "normal_hp": 80, "normal_speed": 130,
             "tank_count": 2, "tank_hp": 300, "tank_speed": 70,
              "interval": 1.0, "road": settings.WAYPOINTS_2
              },
            {
                "normal_count": 15, "normal_hp": 150, "normal_speed": 130,
             "tank_count": 5, "tank_hp": 500, "tank_speed": 60,
              "interval": 0.8, "road": settings.WAYPOINTS_3
              },
        ]
        self.current_wave_index = 0
        self.current_road = self.waves[self.current_wave_index]["road"]

        self.music_enabled = True
        self.sfx_enabled = True

        pygame.mixer.music.load("assets/sounds/post_apocalyptic.mp3")
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.1)

        self.sound_shoot = pygame.mixer.Sound("assets/sounds/laserLarge_002_(shoot).ogg")
        self.sound_hit = pygame.mixer.Sound("assets/sounds/Heavy Magical Explosion_SI 03_base_damage.wav")
        #self.sound_gameover = pygame.mixer.Sound("путь звука конца игры")

        self.sound_shoot.set_volume(0.1)
        self.sound_hit.set_volume(0.2)
        #self.sound_gameover.set_volume(0.5)

        orig_bg_img = pygame.image.load("assets/game_bg.png").convert()
        self.background = pygame.transform.scale(orig_bg_img, (settings.WIDTH, settings.HEIGHT))

        orig_outpost_100hp_img = pygame.image.load("assets/outpost1.png").convert_alpha()
        self.outpost_100hp_img = pygame.transform.scale(orig_outpost_100hp_img, (200, 200))

        outpost_50hp = pygame.image.load("assets/outpost_50hp.png").convert_alpha()
        self.outpost_50hp_img = pygame.transform.scale(outpost_50hp, (200, 200))
        
        outpost_0hp = pygame.image.load("assets/outpost_0hp.png").convert_alpha()
        self.outpost_0hp_img = pygame.transform.scale(outpost_0hp, (200, 200))
        
        self.outpost_img = self.outpost_100hp_img
        self.outpost_rect = self.outpost_img.get_rect(center=self.current_road[-1])

        orig_road_vert = pygame.image.load("assets/road_vert.png").convert_alpha()
        orig_road_gor = pygame.image.load("assets/road_gor.png").convert_alpha()
        orig_road_ltup = pygame.image.load("assets/road_ugol_ltup.png").convert_alpha()
        orig_road_ltdw = pygame.image.load("assets/road_ugol_ltdw.png").convert_alpha()
        orig_road_rtup = pygame.image.load("assets/road_ugol_rtup.png").convert_alpha()
        orig_road_rtdw = pygame.image.load("assets/road_ugol_rtdw.png").convert_alpha()

        r_size = (settings.ROAD_SIZE, settings.ROAD_SIZE)
        self.road_vert = pygame.transform.scale(orig_road_vert, r_size)
        self.road_gor = pygame.transform.scale(orig_road_gor, r_size)
        self.road_ltup = pygame.transform.scale(orig_road_ltup, r_size)
        self.road_ltdw = pygame.transform.scale(orig_road_ltdw, r_size)
        self.road_rtup = pygame.transform.scale(orig_road_rtup, r_size)
        self.road_rtdw = pygame.transform.scale(orig_road_rtdw, r_size)
        
        self.road_draw = []
        
        self.grid_surface = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
        alpha_level = 60  
        grid_color_alpha = (*settings.COLOR_GRID, alpha_level)

        for x in range(0, settings.WIDTH, settings.TILE_SIZE):
            pygame.draw.line(self.grid_surface, grid_color_alpha, (x, 0), (x, settings.HEIGHT))
        for y in range(0, settings.HEIGHT, settings.TILE_SIZE):
            pygame.draw.line(self.grid_surface, grid_color_alpha, (0, y), (settings.WIDTH, y))

        self.all_sprites = pygame.sprite.Group()
        self.turrets_group = pygame.sprite.Group()
        self.bugs_group = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()

        self.spawn_timer = 0.0
        self.spawn_interval = 0.8

        self.bugs_spawned = 0
        self.bugs_finished = 0 # убитые + дошедшие до аванпоста

        self.wave_delay = 5.0 # пауза между волнами
        self.wave_timer = self.wave_delay
        self.is_wave_active = False

        self.credits = 50  # стартовые кредиты
        self.turret_cost = 50  # стоимость одной турели
        self.base_hp = 100  # хп аванпоста
        self.score = 0  # число уничтоженных жуков 

        self.state = "MENU"

        # ui элементы (кнопки, лого и т.д)
        self.ui_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.menu_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.hp_font = pygame.font.SysFont("Arial", 12, bold=True)
        center_x = settings.WIDTH // 2

        orig_panel = pygame.image.load("assets/panel_1.png").convert_alpha()
        self.panel_h = 100
        self.panel_img = pygame.transform.scale(orig_panel, (settings.WIDTH, self.panel_h))

        orig_menu_bg = pygame.image.load("assets/menu_bg.png").convert()
        self.menu_bg_img = pygame.transform.scale(orig_menu_bg, (settings.WIDTH, settings.HEIGHT))

        orig_logo = pygame.image.load("assets/logo.png").convert_alpha()
        self.logo_img = pygame.transform.scale(orig_logo, (400, 230)) 
        self.logo_rect = self.logo_img.get_rect(center=(settings.WIDTH // 2, 140))

        orig_start = pygame.image.load("assets/start.png").convert_alpha()
        self.start_img = pygame.transform.scale(orig_start, (280, 125))
        
        orig_start_hover = pygame.image.load("assets/start_hover.png").convert_alpha()
        self.start_hover_img = pygame.transform.scale(orig_start_hover, (280, 125))

        orig_exit = pygame.image.load("assets/exit.png").convert_alpha()
        self.exit_img = pygame.transform.scale(orig_exit, (280, 125))

        orig_exit_hover = pygame.image.load("assets/exit_hover.png").convert_alpha()
        self.exit_hover_img = pygame.transform.scale(orig_exit_hover, (280, 125))

        orig_pause_img = pygame.image.load("assets/pause.png").convert_alpha()
        self.pause_img = pygame.transform.scale(orig_pause_img, (300, 130)) 
        self.pause_rect = self.pause_img.get_rect(center=(settings.WIDTH // 2, 130))

        orig_continue_img = pygame.image.load("assets/continue.png").convert_alpha()
        self.continue_img = pygame.transform.scale(orig_continue_img, (300, 120))

        orig_continue_hover = pygame.image.load("assets/continue_hover.png").convert_alpha()
        self.continue_hover_img = pygame.transform.scale(orig_continue_hover, (300, 120))

        orig_menu = pygame.image.load("assets/menu.png").convert_alpha()
        self.menu_img = pygame.transform.scale(orig_menu, (300, 120))

        orig_menu_hover = pygame.image.load("assets/menu_hover.png").convert_alpha()
        self.menu_hover_img = pygame.transform.scale(orig_menu_hover, (300, 120))

        orig_music_on = pygame.image.load("assets/music_on.png").convert_alpha()
        orig_music_off = pygame.image.load("assets/music_off.png").convert_alpha()
        self.orig_music_on_img = pygame.transform.scale(orig_music_on, (100, 100))
        self.orig_music_off_img = pygame.transform.scale(orig_music_off, (100, 100))

        orig_music_on_hover = pygame.image.load("assets/music_on_hover.png").convert_alpha()
        orig_music_off_hover = pygame.image.load("assets/music_off_hover.png").convert_alpha()
        self.orig_music_on_hover_img = pygame.transform.scale(orig_music_on_hover, (100, 100))
        self.orig_music_off_hover_img = pygame.transform.scale(orig_music_off_hover, (100, 100))

        orig_sfx_on = pygame.image.load("assets/sound_on.png").convert_alpha()
        orig_sfx_off = pygame.image.load("assets/sound_off.png").convert_alpha()
        self.sfx_on_img = pygame.transform.scale(orig_sfx_on, (117, 117))
        self.sfx_off_img = pygame.transform.scale(orig_sfx_off, (117, 117))

        orig_sfx_on_hover = pygame.image.load("assets/sound_on_hover.png").convert_alpha()
        orig_sfx_off_hover = pygame.image.load("assets/sound_off_hover.png").convert_alpha()
        self.sfx_on_hover_img = pygame.transform.scale(orig_sfx_on_hover, (117, 117))
        self.sfx_off_hover_img = pygame.transform.scale(orig_sfx_off_hover, (117, 117))

        self.btn_start = ImageButton(
            x=center_x,
            y=300, 
            image=self.start_img, 
            hover_image=self.start_hover_img, 
            action=self.start_game
        )
        
        self.btn_quit = ImageButton(
            x = center_x,
            y = 420,
            image=self.exit_img,
            hover_image=self.exit_hover_img,
            action=self.quit_game
        )

        self.btn_continue = ImageButton(
            x = center_x,
            y = 250,
            image=self.continue_img,
            hover_image=self.continue_hover_img,
            action=self.pause
        )
        
        self.btn_menu = ImageButton(
            x = center_x,
            y = 390,
            image=self.menu_img,
            hover_image=self.menu_hover_img,
            action=self.menu
        )

        self.menu_btn_music = ImageButton(
            x=75, 
            y=settings.HEIGHT - 70, 
            image=self.orig_music_on_img, 
            hover_image=self.orig_music_on_img, 
            action=self.toggle_music
        )

        self.btn_music = ImageButton(
            x=center_x - 55, 
            y=515, 
            image=self.orig_music_on_img, 
            hover_image=self.orig_music_on_img, 
            action=self.toggle_music
        )
        
        self.menu_btn_sfx = ImageButton(
            x = 190,
            y=settings.HEIGHT - 70,
            image=self.sfx_on_img,
            hover_image=self.sfx_on_img,
            action=self.toggle_sfx
        )

        self.btn_sfx = ImageButton(
            x=center_x + 65, 
            y=515, 
            image=self.sfx_on_img,
            hover_image=self.sfx_on_img,
            action=self.toggle_sfx
        )
        
        self.reset_game()
    
    def reset_game(self):
        """Сбрасывает весь прогресс для новой игры"""
        self.all_sprites = pygame.sprite.Group()
        self.turrets_group = pygame.sprite.Group()
        self.bugs_group = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group()

        self.outpost_img = self.outpost_100hp_img

        self.credits = 50
        self.base_hp = 100
        self.max_base_hp = 100
        self.score = 1000
        
        self.current_wave_index = 0
        self.waves = [
            {
                "normal_count": 5, "normal_hp": 100, "normal_speed": 100,
             "tank_count": 0, "tank_hp": 0, "tank_speed": 0,
              "interval": 1.2, "road": settings.WAYPOINTS_3
              },
            {
                "normal_count": 10, "normal_hp": 80, "normal_speed": 130,
             "tank_count": 2, "tank_hp": 300, "tank_speed": 70,
              "interval": 1.0, "road": settings.WAYPOINTS_2
              },
            {
                "normal_count": 15, "normal_hp": 150, "normal_speed": 130,
             "tank_count": 5, "tank_hp": 500, "tank_speed": 60,
              "interval": 0.8, "road": settings.WAYPOINTS_3
              },
        ]
        self.current_wave_data = self.waves[self.current_wave_index]
        self.current_road = self.current_wave_data["road"]
        self.outpost_rect = self.outpost_img.get_rect(center=self.current_road[-1])
        self.outpost_rect.center = self.current_road[-1]
        self._draw_road_graphics()
        
        self.wave_timer = 5.0
        self.is_wave_active = False
        self.spawn_timer = 0.0

        self.notify_text = "" # всплывающие сообщения
        self.notify_timer = 0.0
        self.notify_time_len = 2.0
    
    def start_game(self):
        self.reset_game()
        self.state = "PLAYING"
    
    def menu(self):
        self.state = "MENU"

    def quit_game(self):
        self.running = False

    def pause(self):
        if self.state == "PLAYING":
            self.state = "PAUSED"
        elif self.state == "PAUSED":
            self.state = "PLAYING"

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.state in ["PLAYING", "PAUSED"]:
                    self.pause()
            
            if self.state == "MENU":
                self.btn_start.handle_event(event)
                self.btn_quit.handle_event(event)
                self.menu_btn_music.handle_event(event)
                self.menu_btn_sfx.handle_event(event)
            elif self.state == "PAUSED":
                self.btn_continue.handle_event(event)
                self.btn_menu.handle_event(event)
                self.btn_music.handle_event(event)
                self.btn_sfx.handle_event(event)
            elif self.state == "GAME_OVER":
                self.btn_menu.handle_event(event)
            elif self.state == "VICTORY":
                self.btn_menu.handle_event(event)
            elif self.state == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if event.pos[1] < 40:
                            continue

                        if self.credits >= self.turret_cost:
                            grid_x = (event.pos[0] // settings.TILE_SIZE) * settings.TILE_SIZE
                            grid_y = (event.pos[1] // settings.TILE_SIZE) * settings.TILE_SIZE
                            center_pos = (grid_x + settings.TILE_SIZE // 2, grid_y + settings.TILE_SIZE // 2)

                            if self._is_valid_position(center_pos):
                                Turret(center_pos, self.all_sprites, self.turrets_group)
                                self.credits -= self.turret_cost
                            else:
                                self.show_notify("Невозможно поставить турель в этой зоне!")
                        else:
                            self.show_notify("Недостаточно кредитов")
                    
                    elif event.button == 3:
                        mouse_pos = event.pos
                        for turret in self.turrets_group:
                            if turret.rect.collidepoint(mouse_pos):
                                turret.kill()
                                self.credits += self.turret_cost // 4
                                self.show_notify("Турель продана!")
                                break

    def update(self, dt):
        if self.state != "PLAYING":
            return
        
        # уведомления
        if self.notify_timer > 0:
            self.notify_timer -= dt
            if self.notify_timer <= 0:
                self.notify_text = ""

        # управление волнами
        if not self.is_wave_active:
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.start_next_wave()
        else:
            wave_data = self.waves[self.current_wave_index]
            
            # спавн жуков
            if self.bugs_spawned < self.сount_wave_bugs:
                self.spawn_timer += dt

                wave_data = self.waves[self.current_wave_index]
                if self.spawn_timer >= wave_data["interval"]:
                    # Передаем текущий маршрут и усиленные статы
                    bug = self.spawn_ochered[self.bugs_spawned]
                    if bug["type"] == "tank":
                        TankBug(
                        self.current_road, 
                        bug["hp"],
                        bug["speed"],
                        self.all_sprites,
                        self.bugs_group
                        )
                    else:
                        AlienBug(
                            self.current_road, 
                            bug["hp"],
                            bug["speed"],
                            self.all_sprites,
                            self.bugs_group
                            )
                        
                    self.bugs_spawned += 1
                    self.spawn_timer = 0.0

            # проверка завершения волны
            if self.bugs_finished >= self.сount_wave_bugs:
                self.end_wave()

        # обновление жуков и пуль
        self.bugs_group.update(dt)
        self.bullets_group.update(dt)
        self.floating_texts.update(dt)

        # обновление турелей
        for turret in self.turrets_group:
            turret.update(dt, self.bugs_group, self.all_sprites, self.play_sound,  self.sound_shoot, self.bullets_group)

        # проверка нанес ли жук урон по базе
        for bug in list(self.bugs_group):
            if bug.reached_base:
                self.base_hp -= 10
                if 0 < self.base_hp <= 50:
                    self.outpost_img = self.outpost_50hp_img
                elif self.base_hp == 0:
                    self.outpost_img = self.outpost_0hp_img
                self.bugs_finished += 1
                self.play_sound(self.sound_hit)
                bug.kill()
                if self.base_hp < 0:
                    self.base_hp = 0

        # обработка попаданий
        # False означает "не удалять жука автоматически"
        # True означает "удалить пулю при попадании"
        hits = pygame.sprite.groupcollide(
            self.bugs_group, self.bullets_group, False, True
        )

        for bug, bullets in hits.items():
            for bullet in bullets:
                if bug.take_damage(bullet.damage):
                    self.credits += bug.reward
                    self.score += bug.score_value
                    FloatingText(
                        bug.rect.center,
                        f"+{bug.reward}$",
                        self.hp_font, 
                        (50, 255, 50),
                        self.all_sprites,
                        self.floating_texts
                    )
                    self.bugs_finished += 1
                
        if self.base_hp <= 0:
            self.state = "GAME_OVER"

    def start_next_wave(self):
        self.is_wave_active = True
        self.bugs_spawned = 0
        self.bugs_finished = 0
        
        self.current_road = self.waves[self.current_wave_index]["road"]
        self.current_wave_data = self.waves[self.current_wave_index]
        self.outpost_rect.center = self.current_road[-1]
        self._draw_road_graphics()

        self.spawn_ochered = []
        
        for _ in range(self.current_wave_data["normal_count"]):
            self.spawn_ochered.append(
                {
                    "type": "normal",
                    "hp": self.current_wave_data["normal_hp"],
                    "speed": self.current_wave_data["normal_speed"]
                }
            )
        
        for _ in range(self.current_wave_data["tank_count"]):
            self.spawn_ochered.append(
                {
                    "type": "tank",
                    "hp": self.current_wave_data["tank_hp"],
                    "speed": self.current_wave_data["tank_speed"]
                }
            )
        random.shuffle(self.spawn_ochered)
        
        self.сount_wave_bugs = len(self.spawn_ochered)
        # если турель оказалась на пути врагов, то смещаем ее
        for turret in list(self.turrets_group):
            if not self._is_valid_position(turret.rect.center, ignore_turret=turret):
                moved = False
                
                # ищем свободное место в радиусе от 1 до 3 клеток вокруг
                for radius in range(1, 4):
                    for dx in range(-radius, radius + 1):
                        for dy in range(-radius, radius + 1):
                            new_x = turret.rect.centerx + (dx * settings.TILE_SIZE)
                            new_y = turret.rect.centery + (dy * settings.TILE_SIZE)
                            new_pos = (new_x, new_y)

                            # проверка клетки
                            if self._is_valid_position(new_pos, ignore_turret=turret):
                                turret.rect.center = new_pos
                                turret.pos = pygame.math.Vector2(new_pos)
                                moved = True
                                break # прерываем цикл по dy
                        if moved: 
                            break # прерываем цикл по dx
                    if moved: 
                        break # прерываем цикл по radius

                if not moved:
                    turret.kill()
                    self.show_notify("Турель уничтожена!")

    def end_wave(self):
        self.is_wave_active = False
        self.current_wave_index += 1
        self.wave_timer = self.wave_delay

        if self.current_wave_index >= len(self.waves):
            self.state = "VICTORY"

    def _is_valid_position(self, center_pos, ignore_turret=None):
        grid_x = center_pos[0] - settings.TILE_SIZE // 2
        grid_y = center_pos[1] - settings.TILE_SIZE // 2
        if not (0 <= grid_x < settings.WIDTH and 110 <= grid_y < settings.HEIGHT):
            return False

        temp_rect = pygame.Rect(grid_x, grid_y, settings.TILE_SIZE, settings.TILE_SIZE)
        for t in self.turrets_group:
            if t is not ignore_turret and t.rect.colliderect(temp_rect):
                return False

        for i in range(len(self.current_road) - 1):
            p1 = self.current_road[i]
            p2 = self.current_road[i + 1]
            if temp_rect.clipline(p1, p2):
                return False
        
        if temp_rect.collidepoint(self.current_road[-1]):
            return False

        return True

    def draw(self):
        if self.state in ["PLAYING", "PAUSED", "GAME_OVER", "VICTORY"]:
            self.draw_grid_and_road()
            self.all_sprites.draw(self.screen)
            self._draw_hp_bars()
            self.draw_ui()

        if self.state == "MENU":
            self.screen.blit(self.menu_bg_img, (0, 0))
            self.screen.blit(self.logo_img, self.logo_rect)
            self.btn_start.draw(self.screen)
            self.btn_quit.draw(self.screen)
            self.menu_btn_music.draw(self.screen)
            self.menu_btn_sfx.draw(self.screen)

        elif self.state == "PAUSED":
            overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.pause_img, self.pause_rect)
        
            self.btn_continue.draw(self.screen)
            self.btn_menu.draw(self.screen)
            self.btn_music.draw(self.screen)
            self.btn_sfx.draw(self.screen)

        elif self.state == "GAME_OVER":
            overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((50, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            go_surf = self.title_font.render("АВАНПОСТ УНИЧТОЖЕН!", True, (255, 50, 50))
            self.screen.blit(go_surf, go_surf.get_rect(center=(settings.WIDTH//2, 150)))
            self.btn_menu.draw(self.screen)

        elif self.state == "VICTORY":
            overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 40, 0))
            self.screen.blit(overlay, (0, 0))
            
            vic_surf = self.title_font.render("ВСЕ ВОЛНЫ ОТБИТЫ!", True, (255, 215, 0))
            self.screen.blit(vic_surf, vic_surf.get_rect(center=(settings.WIDTH//2, 150)))
            
            score_surf = self.menu_font.render(f"Итоговый счет: {self.score}", True, (255, 255, 255))
            self.screen.blit(score_surf, score_surf.get_rect(center=(settings.WIDTH//2, 230)))
            self.btn_menu.draw(self.screen)

        pygame.display.flip()

    # рисовка графики дороги
    def _draw_road_graphics(self):
        self.road_draw = []
        full_road = []

        for i in range(len(self.current_road) - 1):
            p1 = pygame.math.Vector2(self.current_road[i])
            p2 = pygame.math.Vector2(self.current_road[i+1])

            direction = p2 - p1
            dist = int(direction.length())
            if dist == 0:
                continue
            direction = direction.normalize()

            for step in range(0, dist, settings.TILE_SIZE):
                point = p1 + direction * step
                coord = (round(point.x), round(point.y))
                if not full_road or full_road[-1] != coord:
                    full_road.append(coord)

        last_coord = (round(self.current_road[-1][0]), round(self.current_road[-1][1]))
        if not full_road or full_road[-1] != last_coord:
            full_road.append(last_coord)

        for i in range(len(full_road)):
            current = full_road[i]

            if i == 0:
                next_t = full_road[i+1]
                img = self.road_vert if current[0] == next_t[0] else self.road_gor
            elif i == len(full_road) - 1:
                pred_t = full_road[i-1]
                img = self.road_vert if current[0] == pred_t[0] else self.road_gor
            else:
                next_t = full_road[i+1]
                pred_t = full_road[i-1]
                if next_t[0] == pred_t[0]:
                    img = self.road_vert
                elif next_t[1] == pred_t[1]:
                    img = self.road_gor
                else:
                    is_left = (pred_t[0] < current[0]) or (next_t[0] < current[0])
                    is_right = (pred_t[0] > current[0]) or (next_t[0] > current[0])
                    is_up = (pred_t[1] < current[1]) or (next_t[1] < current[1])
                    is_down = (pred_t[1] > current[1]) or (next_t[1] > current[1])

                    if is_left and is_up:
                        img = self.road_ltup
                    elif is_right and is_up:
                        img = self.road_rtup
                    elif is_left and is_down:
                        img = self.road_ltdw
                    elif is_right and is_down:
                        img = self.road_rtdw

            rect = img.get_rect(center=current)
            self.road_draw.append((img, rect)) 


    def _draw_hp_bars(self):
        if self.base_hp > 0:
            bar_w, bar_h = 80, 8
            fill = (self.base_hp / self.max_base_hp) * bar_w
            
            outline_rect = pygame.Rect(0, 0, bar_w, bar_h)
            outline_rect.centerx = self.outpost_rect.centerx
            outline_rect.bottom = self.outpost_rect.top - 10

            fill_rect = pygame.Rect(outline_rect.x, outline_rect.y, fill, bar_h)

            pygame.draw.rect(self.screen, (150, 0, 0), outline_rect)
            pygame.draw.rect(self.screen, (0, 200, 0), fill_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), outline_rect, 1)

            hp_text = self.hp_font.render(str(int(self.base_hp)), True, settings.COLOR_TEXT)
            hp_rect = hp_text.get_rect(midleft=(outline_rect.left - 25, outline_rect.centery))
            self.screen.blit(hp_text, hp_rect)
        
        for bug in self.bugs_group:
            if bug.hp > 0:
                bar_w, bar_h = 40, 5
                
                current_hp = max(0, bug.hp)
                fill = (current_hp / bug.max_hp) * bar_w
                
                outline_rect = pygame.Rect(0, 0, bar_w, bar_h)
                outline_rect.centerx = bug.rect.centerx
                outline_rect.bottom = bug.rect.top - 5
                
                fill_rect = pygame.Rect(outline_rect.x, outline_rect.y, fill, bar_h)

                pygame.draw.rect(self.screen, (150, 0, 0), outline_rect)
                pygame.draw.rect(self.screen, (0, 200, 0), fill_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), outline_rect, 1)

                hp_text = self.hp_font.render(str(int(current_hp)), True, settings.COLOR_TEXT)
                hp_rect = hp_text.get_rect(midleft=(outline_rect.left - 25, outline_rect.centery))
                self.screen.blit(hp_text, hp_rect)

    def draw_grid_and_road(self):
        self.screen.blit(self.background, (0, 0))

        # отрисовка сетки
        self.screen.blit(self.grid_surface, (0, 0))

        # отрисовка дороги 
        for img, rect in self.road_draw:
            self.screen.blit(img, rect)

        self.screen.blit(self.outpost_img, self.outpost_rect)

    def draw_ui(self):
        self.screen.blit(self.panel_img, (0, 0))

        bar_x = 83
        bar_y = 43
        bar_w = 145
        bar_h = 26 
        
        fill = (self.base_hp / self.max_base_hp) * bar_w
        fill_rect = pygame.Rect(bar_x, bar_y, fill, bar_h)

        hp_color = (0, 200, 0) if self.base_hp > 30 else (200, 0, 0)
        pygame.draw.rect(self.screen, hp_color, fill_rect)

        hp_text = self.ui_font.render(f"{int(self.base_hp)} / {int(self.max_base_hp)}", True, (255, 255, 255))
        hp_rect = hp_text.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2))
        self.screen.blit(hp_text, hp_rect)

        color_val = (240, 200, 100)

        cred_text = self.ui_font.render(f"{self.credits}", True, color_val)
        self.screen.blit(cred_text, (335, 45)) 

        score_text = self.ui_font.render(f"{self.score}", True, color_val)
        self.screen.blit(score_text, (485, 45))

        cost_text = self.ui_font.render(f"{self.turret_cost}", True, color_val)
        self.screen.blit(cost_text, (650, 45))

        wave_text = self.ui_font.render(f"{self.current_wave_index + 1}/{len(self.waves)}", True, color_val)
        self.screen.blit(wave_text, (805, 45))

        if self.notify_text:
            notif_surf = self.ui_font.render(self.notify_text, True, (255, 100, 100))
            notif_rect = notif_surf.get_rect(center=(settings.WIDTH // 2, 110))
            
            bg_rect = notif_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_rect, border_radius=5)
            self.screen.blit(notif_surf, notif_rect)
        
        if not self.is_wave_active:
            if self.current_wave_index == 0:
                timer_text = f"НАЧАЛО ЧЕРЕЗ: {max(0, self.wave_timer):.0f} СЕК"
            else:
                timer_text = f"СЛЕДУЮЩАЯ ВОЛНА ЧЕРЕЗ: {max(0, self.wave_timer):.0f} СЕК"
                
            timer_surf = self.ui_font.render(timer_text, True, (0, 0, 0)) 
            timer_rect = timer_surf.get_rect(center=(settings.WIDTH // 2, 150))
            timer_bg = timer_rect.inflate(30, 15)
            
            pygame.draw.rect(self.screen, (240, 220, 140, 180), timer_bg, border_radius=8)
            pygame.draw.rect(self.screen, (0, 0, 0), timer_bg, 2, border_radius=8) 
            self.screen.blit(timer_surf, timer_rect)
        
    def play_sound(self, sound):
        if self.sfx_enabled and sound is not None:
            sound.play()
    
    # фоновая музыка
    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            pygame.mixer.music.unpause()
            new_img = self.orig_music_on_img
        else:
            pygame.mixer.music.pause()
            new_img = self.orig_music_off_img
            
        self.btn_music.image = new_img
        self.btn_music.hover_image = new_img
        self.menu_btn_music.image = new_img
        self.menu_btn_music.hover_image = new_img

    # звуковые эффекты
    def toggle_sfx(self):
        self.sfx_enabled = not self.sfx_enabled
        
        if self.sfx_enabled:
            new_img = self.sfx_on_img
        else:
            new_img = self.sfx_off_img
            
        self.btn_sfx.image = new_img
        self.btn_sfx.hover_image = new_img
        self.menu_btn_sfx.image = new_img
        self.menu_btn_sfx.hover_image = new_img

    def show_notify(self, text):
        self.notify_text = text
        self.notify_timer = self.notify_time_len

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    OutpostDefenseGame().run()
