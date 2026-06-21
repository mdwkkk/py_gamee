import pygame
import settings
import random


class Bullet(pygame.sprite.Sprite):
    """"Класс Пуль"""
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
        """
        Перемещает пулю по прямой линии на основе нормализованного вектора направления
        Удаляет объект из памяти, если пуля выходит за границы экрана
        """
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if not (
            0 <= self.rect.x <= settings.WIDTH and 0 <= self.rect.y <= settings.HEIGHT
        ):  # если пуля улетает за экран, удаляем ее
            self.kill()


class AlienBug(pygame.sprite.Sprite):
    """Родительский класс жука"""
    def __init__(self, waypoints, hp, speed, *groups):
        super().__init__(*groups)
        orig_image = pygame.image.load("assets/bug.png").convert_alpha()
        self.image_def = pygame.transform.scale(orig_image, (50, 50))
        
        image_rt = pygame.image.load("assets/bug_rt.png").convert_alpha()
        self.image_rt = pygame.transform.scale(image_rt, (50, 50))

        image_up = pygame.image.load("assets/bug_up.png").convert_alpha()
        self.image_up = pygame.transform.scale(image_up, (50, 50))
        
        self.image = self.image_def
        self.rect = self.image.get_rect()

        self.waypoints = waypoints
        self.current_wp_index = 0

        offset_x = random.randint(-12, 12)
        offset_y = random.randint(-12, 12)

        # генерация случайных смещений для каждого жука
        self.my_waypoints = []
        for wp in waypoints:
            self.my_waypoints.append(pygame.math.Vector2(wp[0] + offset_x, wp[1] + offset_y))

        self.current_wp_index = 0
        
        # cпавн жука на его рандомной первой точке
        self.pos = pygame.math.Vector2(self.my_waypoints[0]) 
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.speed = speed  # пикселей в секунду
        self.hp = hp
        self.max_hp = hp
        self.damage_to_base = 10
        self.reached_base = False  # флаг прорыва к аванпосту

        self.reward = 10 # кредитов за убийство
        self.score_value = 50

    def take_damage(self, amount):
        """
        Обрабатывает получение и уменьшение урона
        Возвращает True, если хп опустилось до нуля, иначе False
        """
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def update(self, dt):
        """
        Реализует следование по маршруту
        Вычисляет вектор направления к следующей точке, обновляет анимацию поворота 
        """
        # если достигли конца маршрута (аванпоста)
        if self.current_wp_index >= len(self.my_waypoints):
            self.reached_base = True
            return

        # берем текущую цель
        target = self.my_waypoints[self.current_wp_index]
        direction = target - self.pos
        distance = direction.length()

        if distance > 0: 
            if abs(direction.x) > abs(direction.y): # смена модели жуков в зависимости от направления
                if direction.x > 0:
                    self.image = self.image_rt
                else:
                    self.image = self.image_def
            else:
                if direction.y > 0:
                    self.image = self.image_def
                else:
                    self.image = self.image_up
            
            old_center = self.rect.center
            self.rect = self.image.get_rect(center=old_center)
                                            
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
    """Класс жука Танк, наследованный от класса AlienBug"""
    def __init__(self, waypoints, hp, speed, *groups):
        super().__init__(waypoints, hp, speed, *groups)

        orig_image = pygame.image.load("assets/TankBug.png").convert_alpha()
        self.image_def = pygame.transform.scale(orig_image, (75, 75))

        image_up = pygame.image.load("assets/TankBug_up.png").convert_alpha()
        self.image_up = pygame.transform.scale(image_up, (75, 75))

        image_rt = pygame.image.load("assets/TankBug_rt.png").convert_alpha()
        self.image_rt = pygame.transform.scale(image_rt, (75, 75))

        image_lt = pygame.image.load("assets/TankBug_lt.png").convert_alpha()
        self.image_lt = pygame.transform.scale(image_lt, (75, 75))

        self.rect = self.image.get_rect()
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.damage_to_base = 20
        self.reward = 30
        self.score_value = 200

    def take_damage(self, amount):
        damage = max(1, amount - 10)
        return super().take_damage(damage)
    
class Outpost(pygame.sprite.Sprite):
    def __init__(self, pos, *groups):
        super().__init__(*groups)
    
        orig_outpost_100hp_img = pygame.image.load("assets/outpost1.png").convert_alpha()
        self.outpost_100hp_img = pygame.transform.scale(orig_outpost_100hp_img, (200, 200))

        outpost_50hp = pygame.image.load("assets/outpost_50hp.png").convert_alpha()
        self.outpost_50hp_img = pygame.transform.scale(outpost_50hp, (200, 200))
        
        outpost_0hp = pygame.image.load("assets/outpost_0hp.png").convert_alpha()
        self.outpost_0hp_img = pygame.transform.scale(outpost_0hp, (200, 200))
        
        self.image = self.outpost_100hp_img
        self.rect = self.image.get_rect(center=pos)
        
        self.max_hp = 100
        self.hp = self.max_hp
        
    def take_damage(self, amount):
        """
        Обрабатывает получение и уменьше урона базой
        Переключает спрайт в зависимости от числа хп
        """
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0
            
        if 0 < self.hp <= 50:
            self.image = self.outpost_50hp_img
        elif self.hp == 0:
            self.image = self.outpost_0hp_img
            
    def reset_pos(self, new_pos):
        """Обновляет координаты при смене маршрута в новой волне"""
        self.rect.center = new_pos
    

class Turret(pygame.sprite.Sprite):
    """"Класс турели"""
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
        """Ищет и возвращает объект ближайшего врага в пределах радиуса обзора"""
        closest_bug = None
        min_dist = self.radius

        for bug in bugs_group:
            dist = self.pos.distance_to(bug.rect.center)
            if dist < min_dist:
                min_dist = dist
                closest_bug = bug

        return closest_bug

    def update(self, dt, bugs_group, all_sprites, play_sound, shoot_sound, bullets_group):
        """
        Обновляет логику турели: сканирует цели, управляет таймером перезарядки, 
        создает объекты пуль, вызывает воспроизведение звука и меняет спрайт прицеливания
        """
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

        # меняем картинку турели в зависимости от позиции врага (если цель выше по Y, то меняем модельку)
        if self.target:
            if self.target.rect.centery < self.rect.centery:
                self.image = self.image_back
            else:
                self.image = self.image_front


class FloatingText(pygame.sprite.Sprite):
    """Класс всплывающих чисел"""
    def __init__(self, pos, text, font, color, *groups):
        super().__init__(*groups)
        
        self.text_surf = font.render(text, True, color)
        self.image = self.text_surf.copy()
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(0, -40) 
        
        self.timer = 0.0
        self.lifetime = 1.0 

    def update(self, dt):
        # двигаем текст вверх
        self.pos += self.velocity * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.timer += dt
        
        # исчезновение
        if self.timer < self.lifetime:
            alpha = int(255 * (1.0 - (self.timer / self.lifetime)))
            self.image.set_alpha(alpha)
        else:
            self.kill()