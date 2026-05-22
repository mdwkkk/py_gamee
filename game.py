import pygame
import sys


class Tower(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__() 

        self.image = pygame.Surface((40, 40))
        self.image.fill((50, 200, 50))
        self.rect = self.image.get_rect(center=pos)

    def update(self):
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
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Tower Defense: ООП и Спрайты")
        self.clock = pygame.time.Clock()
        self.running = True
        self.all_sprites = pygame.sprite.Group()
        
        self.player_enemy = Enemy((400, 300))
        self.all_sprites.add(self.player_enemy)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                new_tower = Tower(event.pos)
                self.all_sprites.add(new_tower)

    def update(self):
        self.all_sprites.update()

    def draw(self):
        self.screen.fill((30, 30, 30))
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
    Game().run()