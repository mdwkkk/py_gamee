import pygame


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