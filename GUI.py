import pygame

class Text:
    def __init__(self, font: pygame.font.Font, text, color):
        self.color = color
        self.font = font
        self.text = text
        self.rendered_text = self.font.render(self.text, True, color)
        self.width, self.height = self.rendered_text.get_width(), self.rendered_text.get_height()

class Button:
    def __init__(self, screen, x, y, width, height, color, color_hover, text, func):
        self.screen: pygame.Surface = screen
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.text: Text = text
        self.color, self.color_hover = color, color_hover
        self.func = func
        self.is_clicked = False
    
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    @property
    def is_mouse_colliding(self):
        return self.rect.collidepoint(*pygame.mouse.get_pos())

    def draw(self):
        color = self.color if not self.is_mouse_colliding else self.color_hover
        pygame.draw.rect(self.screen, color, self.rect)
        pygame.draw.rect(self.screen, "white", self.rect, 1)
        pygame.draw.rect(self.screen, "black", (self.x + 1, self.y + 1, self.width - 2, self.height - 2), 1)
        self.screen.blit(self.text.rendered_text, (self.x + self.width / 2 - self.text.width / 2, self.y + self.height / 2 - self.text.height / 2))

    def update(self):
        if not self.is_clicked:
            if self.is_mouse_colliding:
                if pygame.mouse.get_pressed()[0]:
                    self.is_clicked = True
                    self.func()
        if not pygame.mouse.get_pressed()[0]:
            self.is_clicked = False

class Label:
    def __init__(self, screen, x, y, text):
        self.screen: pygame.Surface = screen
        self.text: Text = text
        self.x, self.y = x, y

    def draw(self):
        self.screen.blit(self.text.rendered_text, (self.x, self.y))

class GUI:
    def __init__(self, screen):
        self.buttons: list[Button] = []
        self.labels: list[Label] = []
        self.screen = screen

    def update(self):
        for button in self.buttons:
            button.update()
    
    def draw(self):
        for button in self.buttons:
            button.draw()
        for label in self.labels:
            label.draw()