import pygame
import sys
import settings

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
    def __init__(self, waypoints, speed, hp, *groups):
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


class OutpostDefenseGame:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
        pygame.display.set_caption("Whiskey Outpost")
        self.clock = pygame.time.Clock()
        self.running = True
        self.waves = [
            {"count": 5, "hp": 100, "speed": 100, "interval": 1.2, "path": settings.WAYPOINTS_1},
            {"count": 10, "hp": 150, "speed": 120, "interval": 1.0, "path": settings.WAYPOINTS_2},
            {"count": 15, "hp": 200, "speed": 150, "interval": 0.8, "path": settings.WAYPOINTS_3},
            {"count": 20, "hp": 250, "speed": 170, "interval": 0.7, "path": settings.WAYPOINTS_1},
            {"count": 25, "hp": 300, "speed": 200, "interval": 0.6, "path": settings.WAYPOINTS_2}
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

        self.credits = 150  # стартовые кредиты
        self.turret_cost = 50  # стоимость одной турели
        self.base_hp = 100  # хп аванпоста
        self.score = 0  # число уничтоженных жуков 


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
        self.screen.blit(credits_surface, (180, 8))
        self.screen.blit(score_surface, (340, 8))
        self.screen.blit(cost_surface, (500, 8))
        self.screen.blit(wave_surface, (660, 8))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if event.pos[1] < 40:
                        continue

                    if self.credits >= self.turret_cost:
                        mouse_x, mouse_y = event.pos
                        grid_x = (mouse_x // settings.TILE_SIZE) * settings.TILE_SIZE
                        grid_y = (mouse_y // settings.TILE_SIZE) * settings.TILE_SIZE
                        center_pos = (grid_x + settings.TILE_SIZE // 2, grid_y + settings.TILE_SIZE // 2)

                        temp_rect = pygame.Rect(grid_x, grid_y, settings.TILE_SIZE, settings.TILE_SIZE)
                        # проверка, чтобы не ставить турель на другую
                        is_occup = any(
                            t.rect.colliderect(temp_rect) for t in self.turrets_group
                        )

                        is_on_path = False
                        for i in range(len(self.current_path) - 1):
                            p1 = self.current_path[i]
                            p2 = self.current_path[i + 1]
                            if temp_rect.clipline(p1, p2):
                                is_on_path = True
                                break

                        if temp_rect.collidepoint(self.current_path[-1]):
                            is_on_path = True

                        if not is_occup and not is_on_path:
                            Turret(center_pos, self.all_sprites, self.turrets_group)
                            self.credits -= self.turret_cost
                        else:
                            print("Невозможно поставить туррель в этой зоне!")
                    else:
                        print("Недостачно кредитов")
                
                elif event.button == 3:
                    mouse_pos = event.pos
                    for turret in self.turrets_group:
                        if turret.rect.collidepoint(mouse_pos):
                            turret.kill()
                            self.credits += self.turret_cost // 4
                            print("Турель продана!")
                            break 

    def update(self, dt):
        if self.base_hp <= 0:
            return

        # Логика управления волнами
        if not self.is_wave_active:
            self.wave_timer -= dt
            if self.wave_timer <= 0:
                self.start_next_wave()
        else:
            wave_data = self.waves[self.current_wave_index]
            
            # Спавн жуков
            if self.bugs_spawned < wave_data["count"]:
                self.spawn_timer += dt

                wave_data = self.waves[self.current_wave_index]
                if self.spawn_timer >= wave_data["interval"]:
                    # Передаем текущий маршрут и усиленные статы
                    AlienBug(
                        self.current_path, 
                        wave_data["hp"],
                        wave_data["speed"],
                        self.all_sprites,
                        self.bugs_group
                        )
                    self.bugs_spawned += 1
                    self.spawn_timer = 0.0

            # Проверка завершения волны
            if self.bugs_finished >= wave_data["count"]:
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
    
    def start_next_wave(self):
        self.is_wave_active = True
        self.bugs_spawned = 0
        self.bugs_finished = 0
        self.current_path = self.waves[self.current_wave_index]["path"]
        
        self.outpost_rect.center = self.current_path[-1]

    def end_wave(self):
        self.is_wave_active = False
        self.current_wave_index += 1
        self.wave_timer = self.wave_delay

        if self.current_wave_index >= len(self.waves):
            print("Все волны отбиты!")
            self.running = False
    
    def draw(self):
        self.draw_grid_and_path()
        self.all_sprites.draw(self.screen)

        self.draw_ui()
        if self.base_hp <= 0:
            game_over_font = pygame.font.SysFont("Arial", 48, bold=True)
            go_surface = game_over_font.render("АВАНПОСТ УНИЧТОЖЕН!", True, (255, 0, 0))
            go_rect = go_surface.get_rect(center=(settings.WIDTH // 2, settings.HEIGHT // 2))
            self.screen.blit(go_surface, go_rect)

        pygame.display.flip()

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
