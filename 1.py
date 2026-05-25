import pygame
import sys

# --- НОВЫЕ КЛАССЫ СУЩНОСТЕЙ ---

class Tower(pygame.sprite.Sprite):
    def __init__(self, pos):
        # Обязательно вызываем конструктор родительского класса!
        super().__init__() 
        
        # Строго обязательные имена атрибутов: image и rect
        self.image = pygame.Surface((40, 40))
        self.image.fill((50, 200, 50))
        self.rect = self.image.get_rect(center=pos)

    def update(self):
        # Башня пока ничего не делает, но позже здесь будет логика поиска врагов и выстрела
        pass


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill((255, 50, 50))
        self.rect = self.image.get_rect(center=pos)
        self.speed = 5

    def update(self):
        # Инкапсуляция: враг САМ проверяет кнопки и двигает СЕБЯ.
        # Классу Game больше не нужно знать, как именно ходит враг.
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed


# --- ОБНОВЛЕННЫЙ ИГРОВОЙ ЦИКЛ ---

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Tower Defense: ООП и Спрайты")
        self.clock = pygame.time.Clock()
        self.running = True

        # Создаем группы. 
        # all_sprites нужна для отрисовки всего разом.
        self.all_sprites = pygame.sprite.Group()
        
        # Создаем героя-врага и добавляем в группу
        self.player_enemy = Enemy((400, 300))
        self.all_sprites.add(self.player_enemy)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Создаем башню-объект и просто кидаем её в группу
                new_tower = Tower(event.pos)
                self.all_sprites.add(new_tower)

    def update(self):
        # МАГИЯ 1: Одна строка заставляет всех врагов, башни и будущие пули
        # выполнить свою индивидуальную логику!
        self.all_sprites.update()

    def draw(self):
        self.screen.fill((30, 30, 30))
        
        # МАГИЯ 2: Pygame сам достает image и rect у каждого объекта
        # и рисует их на screen. Никаких циклов for!
        self.all_sprites.draw(self.screen)
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = Game()
    app.run()