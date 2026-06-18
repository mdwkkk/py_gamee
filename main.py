import pygame
import sys
import settings
import random

class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, damage, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, settings.COLOR_BULLET, (3, 3), 3)
        self.rect = self.image.get_rect(center=start_pos)

        self.pos = pygame.math.Vector2(start_pos)
        self.damage = damage
        self.speed = 600

        target_vect = pygame.math.Vector2(target_pos)
        direction = target_vect - self.pos
        if direction.length() > 0:
            self.direction = direction.normalize()
        else:
            self.direction = pygame.math.Vector2(1, 0)

    def update(self, dt):
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if not (
            0 <= self.rect.x <= settings.WIDTH and 0 <= self.rect.y <= settings.HEIGHT
        ):  # если пуля улетает за экран, удаляем ее
            self.kill()


class AlienBug(pygame.sprite.Sprite):
    def __init__(self, waypoints, hp, speed, *groups):
        super().__init__(*groups)
        orig_image = pygame.image.load("assets/bug.png").convert_alpha()
        self.image = pygame.transform.scale(orig_image, (50, 50))
        self.rect = self.image.get_rect()

        self.waypoints = waypoints
        self.current_wp_index = 0

        # Начальная позиция - первый вейпоинт
        self.pos = pygame.math.Vector2(self.waypoints[self.current_wp_index])
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.speed = speed  # пикселей в секунду
        self.hp = hp

        self.reached_base = False  # флаг прорыва к аванпосту

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def update(self, dt):
        # Если достигли конца маршрута (аванпоста)
        if self.current_wp_index >= len(self.waypoints):
            self.reached_base = True
            return

        # Берем текущую цель
        target = pygame.math.Vector2(self.waypoints[self.current_wp_index])
        direction = target - self.pos
        distance = direction.length()

        # Шаг движения за этот кадр
        move_step = self.speed * dt

        if distance <= move_step:
            # Если шаг перепрыгивает цель, просто ставим жука точно в цель
            self.pos = target
            self.current_wp_index += 1  # Переключаемся на следующую точку
        else:
            # Иначе двигаемся в сторону цели
            direction = direction.normalize()
            self.pos += direction * move_step

        self.rect.center = (round(self.pos.x), round(self.pos.y))

class TankBug(AlienBug):
    def __init__(self, waypoints, hp, speed, *groups):
        super().__init__(waypoints, hp, speed, *groups)

        orig_image = pygame.image.load("assets/TankBug.png").convert_alpha()
        self.image = pygame.transform.scale(orig_image, (75, 75))
        self.rect = self.image.get_rect()
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def take_damage(self, amount):
        damage = max(1, amount - 10)
        return super().take_damage(damage)
    

class Turret(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        img_front = pygame.image.load("assets/turret_front.png").convert_alpha()
        img_back = pygame.image.load("assets/turret_back.png").convert_alpha()
        self.image_front = pygame.transform.scale(img_front, (50, 50))
        self.image_back = pygame.transform.scale(img_back, (50, 50))
        self.image = self.image_front
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)

        self.radius = 125  # радиус обзора
        self.target = None  # цель

        # характеристики для стрельбы
        self.damage = 35  # урон за один выстрел
        self.cooldown = 0.4  # задержка между выстрелами
        self.shoot_timer = 0.0

    def find_target(self, bugs_group):
        closest_bug = None
        min_dist = self.radius

        for bug in bugs_group:
            dist = self.pos.distance_to(bug.rect.center)
            if dist < min_dist:
                min_dist = dist
                closest_bug = bug

        return closest_bug

    def update(self, dt, bugs_group, all_sprites, bullets_group):
        self.target = self.find_target(bugs_group)  # находим цель
        self.shoot_timer += dt  # обновляем таймер перезарядки
        if self.target and self.shoot_timer >= self.cooldown:
            Bullet(
                self.rect.center,
                self.target.rect.center,
                self.damage,
                all_sprites,
                bullets_group,
            )
            self.shoot_timer = 0.0

        # меняем картинку турели в зависимости от позиции врага
        if self.target:
            if self.target.rect.centery < self.rect.centery:
                self.image = self.image_back
            else:
                self.image = self.image_front


class Button:
    def __init__(self, x, y, width, height, text, font, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        
        # цвета-заглушки (пока нет картинок)
        self.color = (50, 50, 50)
        self.hover_color = (100, 100, 100)
        self.text_color = settings.COLOR_TEXT
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                self.action()

class ImageButton:
    def __init__(self, x, y, image, hover_image=None, action=None):
        self.image = image
        self.hover_image = hover_image if hover_image else image 
        self.rect = self.image.get_rect(center=(x, y)) 
        
        self.action = action
        self.is_hovered = False

    def draw(self, surface):
        current_image = self.hover_image if self.is_hovered else self.image
        surface.blit(current_image, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                self.action()

class OutpostDefenseGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
        pygame.display.set_caption("Whiskey Outpost")
        self.clock = pygame.time.Clock()
        self.running = True
        self.waves = [
            {
                "normal_count": 5, "normal_hp": 100, "normal_speed": 100,
             "tank_count": 0, "tank_hp": 0, "tank_speed": 0,
              "interval": 1.2, "path": settings.WAYPOINTS_1
              },
            {
                "normal_count": 10, "normal_hp": 80, "normal_speed": 130,
             "tank_count": 2, "tank_hp": 300, "tank_speed": 70,
              "interval": 1.0, "path": settings.WAYPOINTS_2
              },
            {
                "normal_count": 15, "normal_hp": 150, "normal_speed": 130,
             "tank_count": 5, "tank_hp": 500, "tank_speed": 60,
              "interval": 0.8, "path": settings.WAYPOINTS_1
              },
        ]
        self.current_wave_index = 0
        self.current_path = self.waves[self.current_wave_index]["path"]

        self.ui_font = pygame.font.SysFont("Arial", 22, bold=True)
        orig_terrain_img = pygame.image.load("assets/terrain.png").convert()
        self.terrain_tile = pygame.transform.scale(
            orig_terrain_img, (settings.TILE_SIZE, settings.TILE_SIZE)
        )
        orig_outpost_img = pygame.image.load("assets/outpost1.png").convert_alpha()
        self.outpost_img = pygame.transform.scale(orig_outpost_img, (130, 130))
        self.outpost_rect = self.outpost_img.get_rect(center=self.current_path[-1])

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

        self.menu_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        center_x = settings.WIDTH // 2
        btn_w, btn_h = 250, 60

        orig_menu_bg = pygame.image.load("assets/menu_bg.png").convert()
        self.menu_bg_img = pygame.transform.scale(orig_menu_bg, (settings.WIDTH, settings.HEIGHT))

        orig_logo = pygame.image.load("assets/logo.png").convert_alpha()
        self.logo_img = pygame.transform.scale(orig_logo, (400, 230)) 
        self.logo_rect = self.logo_img.get_rect(center=(settings.WIDTH // 2, 150))

        orig_start = pygame.image.load("assets/start.png").convert_alpha()
        self.start_img = pygame.transform.scale(orig_start, (280, 110))
        
        orig_start_hover = pygame.image.load("assets/start_hover.png").convert_alpha()
        self.start_hover_img = pygame.transform.scale(orig_start_hover, (280, 110))

        orig_exit = pygame.image.load("assets/exit.png").convert_alpha()
        self.exit_img = pygame.transform.scale(orig_exit, (300, 130))

        orig_exit_hover = pygame.image.load("assets/exit_hover.png").convert_alpha()
        self.exit_hover_img = pygame.transform.scale(orig_exit_hover, (300, 130))

        orig_pause_img = pygame.image.load("assets/pause.png").convert_alpha()
        self.pause_img = pygame.transform.scale(orig_pause_img, (300, 130)) 
        self.pause_rect = self.pause_img.get_rect(center=(settings.WIDTH // 2, 150))

        self.btn_start = ImageButton(
            x=center_x,
            y=300, 
            image=self.start_img, 
            hover_image=self.start_hover_img, 
            action=self.start_game
        )
        
        self.btn_quit = ImageButton(
            x = center_x,
            y = 410,
            image=self.exit_img,
            hover_image=self.exit_hover_img,
            action=self.quit_game
        )
        left_x = center_x - btn_w // 2
        
        self.btn_resume = Button(left_x, 250, btn_w, btn_h, "ПРОДОЛЖИТЬ", self.menu_font, self.pause)
        self.btn_menu = Button(left_x, 340, btn_w, btn_h, "В ГЛАВНОЕ МЕНЮ", self.menu_font, self.menu)
        
        self.reset_game()
    
    def reset_game(self):
        """Сбрасывает весь прогресс для новой игры"""
        self.all_sprites = pygame.sprite.Group()
        self.turrets_group = pygame.sprite.Group()
        self.bugs_group = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()

        self.credits = 50
        self.base_hp = 100
        self.score = 0
        
        self.current_wave_index = 0
        self.waves = [
            {
                "normal_count": 5, "normal_hp": 100, "normal_speed": 100,
             "tank_count": 0, "tank_hp": 0, "tank_speed": 0,
              "interval": 1.2, "path": settings.WAYPOINTS_1
              },
            {
                "normal_count": 10, "normal_hp": 80, "normal_speed": 130,
             "tank_count": 2, "tank_hp": 300, "tank_speed": 70,
              "interval": 1.0, "path": settings.WAYPOINTS_2
              },
            {
                "normal_count": 15, "normal_hp": 150, "normal_speed": 130,
             "tank_count": 5, "tank_hp": 500, "tank_speed": 60,
              "interval": 0.8, "path": settings.WAYPOINTS_1
              },
        ]
        self.current_wave_data = self.waves[self.current_wave_index]
        self.current_path = self.current_wave_data["path"]
        self.outpost_rect = self.outpost_img.get_rect(center=self.current_path[-1])
        
        self.wave_timer = 5.0
        self.is_wave_active = False
        self.spawn_timer = 0.0
    
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
            elif self.state == "PAUSED":
                self.btn_resume.handle_event(event)
                self.btn_menu.handle_event(event)
            elif self.state == "GAME_OVER":
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
                                print("Невозможно поставить турель в этой зоне!")
                        else:
                            print("Недостаточно кредитов")
                    
                    elif event.button == 3:
                        mouse_pos = event.pos
                        for turret in self.turrets_group:
                            if turret.rect.collidepoint(mouse_pos):
                                turret.kill()
                                self.credits += self.turret_cost // 4
                                print("Турель продана!")
                                break
                            
    def start_next_wave(self):
        self.is_wave_active = True
        self.bugs_spawned = 0
        self.bugs_finished = 0
        
        self.current_path = self.waves[self.current_wave_index]["path"]
        self.current_wave_data = self.waves[self.current_wave_index]
        self.outpost_rect.center = self.current_path[-1]

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
                    print("Турель уничтожена!")

    def end_wave(self):
        self.is_wave_active = False
        self.current_wave_index += 1
        self.wave_timer = self.wave_delay

        if self.current_wave_index >= len(self.waves):
            print("Все волны отбиты!")
            self.running = False

    def update(self, dt):
        if self.state != "PLAYING":
            return
        
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
                        self.current_path, 
                        bug["hp"],
                        bug["speed"],
                        self.all_sprites,
                        self.bugs_group
                        )
                    else:
                        AlienBug(
                            self.current_path, 
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

        # обновление турелей
        for turret in self.turrets_group:
            turret.update(dt, self.bugs_group, self.all_sprites, self.bullets_group)

        # проверка нанес ли жук урон по базе
        for bug in list(self.bugs_group):
            if bug.reached_base:
                self.base_hp -= 10
                self.bugs_finished += 1
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
                    self.credits += 15
                    self.score += 1
                    self.bugs_finished += 1
                
        if self.base_hp <= 0:
            self.state = "GAME_OVER"
    
    def _is_valid_position(self, center_pos, ignore_turret=None):
        grid_x = center_pos[0] - settings.TILE_SIZE // 2
        grid_y = center_pos[1] - settings.TILE_SIZE // 2
        if not (0 <= grid_x < settings.WIDTH and 40 <= grid_y < settings.HEIGHT):
            return False

        temp_rect = pygame.Rect(grid_x, grid_y, settings.TILE_SIZE, settings.TILE_SIZE)
        for t in self.turrets_group:
            if t is not ignore_turret and t.rect.colliderect(temp_rect):
                return False

        for i in range(len(self.current_path) - 1):
            p1 = self.current_path[i]
            p2 = self.current_path[i + 1]
            if temp_rect.clipline(p1, p2):
                return False
        
        if temp_rect.collidepoint(self.current_path[-1]):
            return False

        return True
    
    
    
    def draw_grid_and_path(self):
        for x in range(0, settings.WIDTH, settings.TILE_SIZE):
            for y in range(0, settings.HEIGHT, settings.TILE_SIZE):
                self.screen.blit(self.terrain_tile, (x, y))

        # отрисовка сетки
        for x in range(0, settings.WIDTH, settings.TILE_SIZE):
            pygame.draw.line(self.screen, settings.COLOR_GRID, (x, 0), (x, settings.HEIGHT))
        for y in range(0, settings.HEIGHT, settings.TILE_SIZE):
            pygame.draw.line(self.screen, settings.COLOR_GRID, (0, y), (settings.WIDTH, y))

        # отрисовка дороги
        if len(self.current_path) > 1:
            pygame.draw.lines(self.screen, settings.COLOR_CANYON, False, self.current_path, settings.TILE_SIZE)

        # отрисовка базы на последней точке маршрута
        self.screen.blit(self.outpost_img, self.outpost_rect)

    def draw(self):
        if self.state in ["PLAYING", "PAUSED", "GAME_OVER"]:
            self.draw_grid_and_path()
            self.all_sprites.draw(self.screen)
            self.draw_ui()

        if self.state == "MENU":
            self.screen.blit(self.menu_bg_img, (0, 0))
            self.screen.blit(self.logo_img, self.logo_rect)
            self.btn_start.draw(self.screen)
            self.btn_quit.draw(self.screen)

        elif self.state == "PAUSED":
            overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.pause_img, self.pause_rect)
        
            self.btn_resume.draw(self.screen)
            self.btn_menu.draw(self.screen)

        elif self.state == "GAME_OVER":
            overlay = pygame.Surface((settings.WIDTH, settings.HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((50, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            go_surf = self.title_font.render("АВАНПОСТ УНИЧТОЖЕН!", True, (255, 50, 50))
            self.screen.blit(go_surf, go_surf.get_rect(center=(settings.WIDTH//2, 150)))
            self.btn_menu.draw(self.screen)

        pygame.display.flip()

    def draw_ui(self):
        pygame.draw.rect(self.screen, settings.COLOR_UI_BAR, (0, 0, settings.WIDTH, 40))
        hp_text = f"АВАНПОСТ: {self.base_hp}"
        credits_text = f"КРЕДИТЫ: ${self.credits}"
        score_text = f"УНИЧТОЖЕНИЕ: {self.score}"
        cost_text = f"ТУРРЕЛЬ: ${self.turret_cost}"
        wave_text = f"ВОЛНА: {self.current_wave_index + 1}/{len(self.waves)}"

        hp_surface = self.ui_font.render(
            hp_text, True, (255, 50, 50) if self.base_hp <= 30 else settings.COLOR_TEXT
        )
        credits_surface = self.ui_font.render(credits_text, True, (0, 128, 0))
        score_surface = self.ui_font.render(score_text, True, settings.COLOR_TEXT)
        cost_surface = self.ui_font.render(cost_text, True, (150, 150, 150))
        wave_surface = self.ui_font.render(wave_text, True, (255, 200, 0))

        self.screen.blit(hp_surface, (20, 8))
        self.screen.blit(credits_surface, (200, 8))
        self.screen.blit(score_surface, (380, 8))
        self.screen.blit(cost_surface, (590, 8))
        self.screen.blit(wave_surface, (760, 8))

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
