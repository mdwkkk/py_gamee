import pygame
import math
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
        self.max_hp = hp
        self.reached_base = False  # флаг прорыва к аванпосту

        self.reward = 10 # кредитов за убийство
        self.score_value = 50

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

        self.reward = 30
        self.score_value = 200

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

    def update(self, dt, bugs_group, all_sprites, play_sound, shoot_sound, bullets_group):
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
            play_sound(shoot_sound)
            self.shoot_timer = 0.0

        # меняем картинку турели в зависимости от позиции врага
        if self.target:
            if self.target.rect.centery < self.rect.centery:
                self.image = self.image_back
            else:
                self.image = self.image_front