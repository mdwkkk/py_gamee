import pygame
import sys


class Tower(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups) 

        self.image = pygame.Surface((40, 40))
        self.image.fill((50, 200, 50))
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        pass


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)

        self.image = pygame.Surface((50, 50))
        self.image.fill((255, 50, 50))
        self.rect = self.image.get_rect(center=pos)
        self.speed = 300
        self.pos = pygame.math.Vector2(pos)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        direction = pygame.math.Vector2(0, 0) # Направление движения

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction.y = 1

        if direction.length() > 0:
            direction = direction.normalize()

        self.pos += direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("t")
        self.clock = pygame.time.Clock()
        self.running = True

        self.all_sprites = pygame.sprite.Group()
        self.towers_group = pygame.sprite.Group()

        self.player_enemy = Enemy((400, 300), self.all_sprites)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                Tower(event.pos, self.all_sprites, self.towers_group)


    def update(self, dt):
        self.all_sprites.update(dt)

        # проверка коллизии
        hit = pygame.sprite.spritecollide(self.player_enemy, self.towers_group, True)
        if hit:
            print(f"Уничтожено башен: {len(hit)}")

    def draw(self):
        self.screen.fill((30, 30, 30))
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
    Game().run()