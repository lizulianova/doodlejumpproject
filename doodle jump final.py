import pygame
import os
import sys
from random import randint

FPS = 10
N = 0
running = True 
pygame.init()
screen = pygame.display.set_mode((600, 600))
WIDTH = 600
HEIGHT = 600
clock = pygame.time.Clock()
tile_width = tile_height = 50
JUMP_POWER = 30 #прыжок doodle
GRAVITY = 5 # Сила, которая будет тянуть doodle вниз
MOVE_SPEED = 7 #право-лево
NCLOUD = 0 #количество облаков, с которыми столкнулся doodle
lastcloud = None # последнее облако, с которыми столкнулся doodle
time = pygame.time.Clock()


 
def terminate():
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
        image = image.convert_alpha()
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey)
        return image        
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)


def load_level(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
 
    # и подсчитываем максимальную длину    
    max_width = max(map(len, level_map))
 
    # дополняем каждую строку пустыми клетками ('.')    
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))

    
tile_images = pygame.transform.scale(load_image('cloud.png'), (80, 50))
player_image = pygame.transform.scale(load_image('doodle.png'), (80, 80))
# основной персонаж
player = None
             
# группы спрайтов
all_sprites = pygame.sprite.Group()
clouds_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
vertical_group = pygame.sprite.Group()
down_group = pygame.sprite.Group()
up_group = pygame.sprite.Group()


class Border(pygame.sprite.Sprite):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(all_sprites)
        if x1 == x2:  # боковые стенки
            self.add(vertical_group)
            self.image = pygame.Surface([1, y2 - y1])
            self.rect = pygame.Rect(x1, y1, 1, y2 - y1)        
        else:  # нижняя стенка
            self.add(down_group)
            self.image = pygame.Surface([x2 - x1, 1])
            self.rect = pygame.Rect(x1, y1, x2 - x1, 1)
            
down_border = Border(0, HEIGHT, WIDTH, HEIGHT)
up_border = Border(0, HEIGHT, WIDTH, HEIGHT)
left_border = Border(0, 0, 0, HEIGHT)
right_border = Border(WIDTH, 0, WIDTH, HEIGHT)

class Cloud(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        global N
        super().__init__(clouds_group, all_sprites)
        self.image = tile_images
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.speed = randint(1, 2)
        self.mask = pygame.mask.from_surface(self.image)
        self.n = N + 1
        N = N + 1
        
        
    def update(self):
            if self.rect.y < HEIGHT:
                self.rect.y += self.speed
            else:
                self.rect.y = 0
                
                
    def killme(self):
        self.kill()    
     
     
class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        global GRAVITY
        global  MOVE_SPEED
        global JUMP_POWER
        global NCLOUD
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 15, tile_height * pos_y + 5)
        self.mask = pygame.mask.from_surface(self.image)
        self.yvel = 0 # скорость вертикального перемещения
        self.xvel = 0
        self.onGround = False #проверка поверхности 
            
    def update(self, left, right, up):
        global NCLOUD
        global lastcloud
        global GRAVITY
        clouds = pygame.sprite.spritecollide(self, clouds_group, False)
        for cloud in clouds:
            if (cloud.rect.y > self.rect.y and cloud.rect.x < self.rect.x
            and cloud.rect.x + 80 > self.rect.x + 50):
                self.onGround = True
                self.yvel = cloud.speed
                self.xvel = 0
                if cloud.n != lastcloud:
                    lastcloud = cloud.n
                    NCLOUD += 1
                    
        borders_vert = pygame.sprite.spritecollide(self, vertical_group, False)
        if borders_vert:
            self.xvel = 0
            
        border_down = pygame.sprite.spritecollide(self, down_group, False)
        if border_down:
            finish_screen()
            
        if up:
            if self.onGround: # прыгаем, только когда можем оттолкнуться от земли
                self.yvel = -JUMP_POWER
            else:
                self.yvel = 0
        if left:
            if self.onGround:
                self.xvel -= MOVE_SPEED # Лево = x - n
        if right:
            if self.onGround:
                self.xvel += MOVE_SPEED # Право = x + n
        if not self.onGround:
            self.yvel +=  GRAVITY
        fly_down = pygame.sprite.collide_rect(self, up_border)
        if fly_down:
            for cloud in clouds:
                cloud.speed *= 3    
        self.onGround = False # Мы не знаем, когда мы на земле   
        self.rect.y += self.yvel        
        self.rect.x += self.xvel # переносим свои положение на xvel

        
    def mv_player(self, side):
        mup = mleft = mright = False
        if side[pygame.K_UP]:
            mup = True
        if side[pygame.K_LEFT]:
            mleft = True
        if side[pygame.K_RIGHT]:
            mright = True
        self.update(mleft, mright, mup)
        
        
    def killme(self):
        self.kill()

class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0
 
    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.y += self.dy
 
    # позиционировать камеру на объекте target
    def update(self, target):
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)


def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Cloud('cloud', x, y)
            elif level[y][x] == '@':
                new_player = Player(x, y)
    # вернем игрока, а также размер поля в клетках            
    return new_player, x, y


def start_screen():
    global player
    intro_text = ["           ПРАВИЛА ИГРЫ         ",
                  "", "   управлять героем вы можете", 
                  "при помощи комбинаций кнопок",
                  "      UP, DOWN, LEFT, RIGHT", '',
                  "для начала игры нажмите SPACE"]
 
    fon = pygame.transform.scale(load_image('sky.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
        
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player, x, y = generate_level(load_level('map.txt'))
                    all_sprites.draw(screen)
                    clouds_group.draw(screen)
                    player_group.draw(screen)
                    run = False
        pygame.display.flip()
        clock.tick(FPS)
    
        
def finish_screen():
    global player
    global NCLOUD
    global lastcloud
    f = open("data/" + 'record.txt', mode='r', encoding="utf-8")    
    lines = f.readlines()
    record = lines[0]
    f.close()
    intro_text = ["Game over!", "",
                  "Ваши очки" + ' ' + str(NCLOUD),
                  "Рекорд" + ' ' + record, "", "",
                  "Для продолжения игры нажмите SPACE"]
    fon = pygame.transform.scale(load_image('sky.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
    if int(record) < NCLOUD:
        f = open("data/" + 'record.txt', mode='w', encoding="utf-8")
        f.write(str(NCLOUD))
        f.close()
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pygame.display.flip()
                    NCLOUD = 0
                    lastcloud = None
                    player = None
                    for el in clouds_group:
                        el.killme()
                    for el in player_group:
                        el.killme()
                    start_screen()
                    run = False
        pygame.display.flip()
        clock.tick(FPS)
        
start_screen()
camera = Camera()
while running:
    time.tick(FPS)
    pygame.display.flip()      
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False  
        elif event.type == pygame.KEYDOWN:
            player.mv_player(pygame.key.get_pressed())
    clouds_group.update()
    player.update(False, False, False)
    fon = pygame.transform.scale(load_image('sky.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    all_sprites.draw(screen)
    clouds_group.draw(screen)            
    player_group.draw(screen)
            
                
                
terminate()