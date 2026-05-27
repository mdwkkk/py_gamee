import pygame
import sys

# настойки базы
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40

# Цветовая Звездного десанта
COLOR_KLENDATHU_ROCK = (80, 60, 50)      # Грунт
COLOR_CANYON = (40, 30, 25)              # Глубокий каньон (Дорога для жуков)
COLOR_GRID = (100, 80, 70)               # сетка
COLOR_ARACHNID = (255, 120, 0)           # Жуки
COLOR_OUTPOST = (150, 150, 150)  
COLOR_BULLET = (255, 255, 0)        # Аванпост

# Маршрут врагов (Координаты центров тайлов)
WAYPOINTS = [
    (0, 100), (200, 100), (200, 460), 
    (600, 460), (600, 300), (800, 300)
]

class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, damage, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, COLOR_BULLET, (3, 3), 3)
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
        if not(0 <= self.rect.x <= WIDTH and 0 <= self.rect.y <= HEIGHT): # если пуля улетает за экран, удаляем ее
            self.kill()

class AlienBug(pygame.sprite.Sprite):
    def __init__(self, waypoints, *groups):
        super().__init__(*groups)
        orig_image = pygame.image.load('assets/bug.png').convert_alpha()
        self.image = pygame.transform.scale(orig_image, (40, 40))
        self.rect = self.image.get_rect()
        
        self.waypoints = waypoints
        self.current_wp_index = 0
        
        # Начальная позиция - первый вейпоинт
        self.pos = pygame.math.Vector2(self.waypoints[self.current_wp_index])
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        self.speed = 150  # пикселей в секунду
        self.hp = 100

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
    
    def update(self, dt):
        # Если достигли конца маршрута (аванпоста)
        if self.current_wp_index >= len(self.waypoints):
            self.kill() # жук исчезает
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
            self.current_wp_index += 1 # Переключаемся на следующую точку
        else:
            # Иначе двигаемся в сторону цели
            direction = direction.normalize()
            self.pos += direction * move_step

        self.rect.center = (round(self.pos.x), round(self.pos.y))

class Turret(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)
        
        img_front = pygame.image.load('assets/turret_front.png').convert_alpha()
        img_back = pygame.image.load('assets/turret_back.png').convert_alpha()
        self.image_front = pygame.transform.scale(img_front, (40, 40))
        self.image_back = pygame.transform.scale(img_back, (40, 40))
        self.image = self.image_front
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)

        self.radius = 125 # радиус обзора
        self.target = None # цель

        # характеристики для стрельбы
        self.damage = 35 # урон за один выстрел
        self.cooldown = 0.4 # задержка между выстрелами
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
        self.target = self.find_target(bugs_group) # находим цель
        self.shoot_timer += dt # обновляем таймер перезарядки
        if self.target and self.shoot_timer >= self.cooldown:
            Bullet(self.rect.center, self.target.rect.center, self.damage, all_sprites, bullets_group)
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
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Whiskey Outpost")
        self.clock = pygame.time.Clock()
        self.running = True

        self.all_sprites = pygame.sprite.Group()
        self.turrets_group = pygame.sprite.Group()
        self.bugs_group = pygame.sprite.Group()
        self.bullets_group = pygame.sprite.Group()
        
        self.spawn_timer = 0.0
        self.spawn_interval = 0.8

    def draw_grid_and_path(self):
        self.screen.fill(COLOR_KLENDATHU_ROCK)
        
        # отрисовка сетки
        for x in range(0, WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (WIDTH, y))

        # отрисовка дороги
        if len(WAYPOINTS) > 1:
            pygame.draw.lines(self.screen, COLOR_CANYON, False, WAYPOINTS, TILE_SIZE)

        # отрисовка базы на последней точке маршрута
        dome_pos = WAYPOINTS[-1]
        pygame.draw.circle(self.screen, COLOR_OUTPOST, dome_pos, 40)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                grid_x = (mouse_x // TILE_SIZE) * TILE_SIZE
                grid_y = (mouse_y // TILE_SIZE) * TILE_SIZE
                center_pos = (grid_x + TILE_SIZE // 2, grid_y + TILE_SIZE // 2)
                
                temp_rect = pygame.Rect(grid_x, grid_y, TILE_SIZE, TILE_SIZE)
                # проверка, чтобы не ставить турель на другую
                if not any(t.rect.colliderect(temp_rect) for t in self.turrets_group):
                    Turret(center_pos, self.all_sprites, self.turrets_group)

    def update(self, dt):
        # спавн жуков
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            AlienBug(WAYPOINTS, self.all_sprites, self.bugs_group)
            self.spawn_timer = 0.0 # Сброс таймера
            
        # обновление жуков и пуль
        self.bugs_group.update(dt)
        self.bullets_group.update(dt)
        
        # обновление турелей
        for turret in self.turrets_group:
            turret.update(dt, self.bugs_group, self.all_sprites, self.bullets_group)

        # обработка попаданий
        # флаг False означает "не удалять жука автоматически"
        # флаг True означает "удалить пулю при попадании"
        hits = pygame.sprite.groupcollide(self.bugs_group, self.bullets_group, False, True)
        
        for bug, bullets in hits.items():
            for bullet in bullets:
                bug.take_damage(bullet.damage)

    def draw(self):
        self.draw_grid_and_path()
        self.all_sprites.draw(self.screen)
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