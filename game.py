import pygame
import sys

# настойки базы
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40

# Цветовая палитра Марса
COLOR_SAND = (175, 80, 50)       # Ржавый песок
COLOR_PATH = (100, 40, 20)       # Глубокий каньон (дорога)
COLOR_GRID = (190, 95, 60)       # Линии сетки
COLOR_BUG = (150, 255, 100)      # Кислотно-зеленый пришелец
COLOR_DOME = (50, 150, 255)      # Купол базы

# Маршрут врагов (Координаты центров тайлов)
WAYPOINTS = [
    (0, 100), (200, 100), (200, 460), 
    (600, 460), (600, 300), (800, 300)
]

class AlienBug(pygame.sprite.Sprite):
    def __init__(self, waypoints, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        # Рисуем жука 
        pygame.draw.circle(self.image, COLOR_BUG, (15, 15), 15)
        self.rect = self.image.get_rect()
        
        self.waypoints = waypoints
        self.current_wp_index = 0
        
        # Начальная позиция - первый вейпоинт
        self.pos = pygame.math.Vector2(self.waypoints[self.current_wp_index])
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        self.speed = 150  # пикселей в секунду

    def update(self, dt):
        # Если достигли конца маршрута (Купола)
        if self.current_wp_index >= len(self.waypoints):
            self.kill() # Жук исчезает (потом добавлю нанесение урона базе)
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
        
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (100, 100, 100), (20, 20), 16)
        pygame.draw.rect(self.image, (200, 200, 200), (16, 4, 8, 16))

        self.rect = self.image.get_rect(center=pos)

        # характеристики для стрельбы
        self.radius = 100 # обзор
        self.cooldown = 1.0 # скорость стрельбы
        self.current_time = 0.0
    
    def update(self, dt):
        pass

class MarsBaseGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mars Base Defense")
        self.clock = pygame.time.Clock()
        self.running = True

        self.all_sprites = pygame.sprite.Group()
        self.turrets_group = pygame.sprite.Group()
        
        # Спавним тестового жука
        AlienBug(WAYPOINTS, self.all_sprites)

    def draw_grid_and_path(self):
        self.screen.fill(COLOR_SAND)
        
        # отрисовка сетки
        for x in range(0, WIDTH, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, TILE_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (WIDTH, y))

        # отрисовка дороги
        if len(WAYPOINTS) > 1:
            pygame.draw.lines(self.screen, COLOR_PATH, False, WAYPOINTS, TILE_SIZE)

        # отрисовка купола на последней точке маршрута
        dome_pos = WAYPOINTS[-1]
        pygame.draw.circle(self.screen, COLOR_DOME, dome_pos, 40)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt):
        self.all_sprites.update(dt)

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
    MarsBaseGame().run()