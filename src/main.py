# TODO stuff size and position
# TODO resize everything to check if something missed
# FIXME accumulate auras while burning
# FIXME why cryo in loop (reaction_trigger(), check)
# FIXME low FPS vs burning
# TODO bloom, quicken, frozen


import os
import path
import pygame


####### Constants #######

# Elements order depends on files order in path.ELEMENTS
ANEMO, CRYO, DENDRO, ELECTRO, GEO, HYDRO, PYRO = 0, 1, 2, 3, 4, 5, 6

AURA_TAX = 0.8

REACTION_MODIFIER = {
    'normal': 1,
    'forward': 2,
    'reverse': 0.5,
    'Swirl': 0.5,
    'Crystalize': 0.5
}

REACTION_CONSUMER = {
    'Electro-Charged': 0.4
}

ELEMENT_COLOR = {
    ANEMO: (115, 248, 206),
    GEO: (255, 203, 99),
    PYRO: (252, 156, 13),
    HYDRO: (63, 197, 255),
    ELECTRO: (220, 157, 247),
    CRYO: (152, 255, 254),
    DENDRO: (0, 158, 86)
}

REACTION_COLOR = {
    'Swirl': (115, 248, 206),
    'Crystalize': (255, 155, 0),
    'Vaporize': (238, 202, 129),
    'Overload': (248, 138, 155),
    'Melt': (255, 202, 96),
    'Electro-Charged': (220, 157, 247),
    'Frozen': (156, 255, 255),
    'Superconduct': (187, 180, 255),
    'Burning': (252, 156, 13),
    'Bloom': (0, 231, 75),
    'Quicken': (0, 231, 86)
}

CAPTION = 'Aura Visualizer'
CNVW = 800              # canvas width
CNVH = 600              # canvas height
ELMS = 65               # element icon size
AURS = 250              # aura size
LOGW = 250              # reaction log panel width
FPS = 60
FNTS_TXT = 22           # reaction log font size
FNTS_BTN = 30           # buttons font size
TXTC = (255, 255, 255)  # text color
BGRC = (37, 37, 37)        # background color
RLRC = (37, 37, 37)        # ruler tick marks color


####### Global variables #######

aura_list = []
electro_charged, frame_electro_charged = False, 0
burning, frame_burning = False, 0

canvas = 0
btn_1A, btn_2B, btn_4C = [False] * 3
element_img_list = []
reaction_log_list = []
running = True
clock = 0
fps = 0


####### Classes #######

class ReactionText:

    def __init__(self, reaction):
        self.text = reaction
        self.color = REACTION_COLOR[reaction] if reaction in REACTION_COLOR \
            else TXTC


class Aura:

    def __init__(self, aura, U, decay_U, element, aura_count):
        if element in [ANEMO, GEO]:
            self.aura = False
        else:
            self.aura = aura
        self.U = U * AURA_TAX
        self.decay_U = decay_U
        self.element = element
        self.aura_count = aura_count

    def decay(self):
        if self.aura:
            if self.decay_U == 'A':
                self.U -= 1 / (decay_rate(1) * fps)
            elif self.decay_U == 'B':
                self.U -= 1 / (decay_rate(2) * fps)
            elif self.decay_U == 'C':
                self.U -= 1 / (decay_rate(4) * fps)
            if self.element == DENDRO and burning:
                self.U -= 1 / (decay_rate(2) * fps)
        if self.U <= 0:
            self.U = 0
            self.aura = False


####### Functions #######

# Logical functions

def decay_rate(gauge):
    if gauge in [1, 2, 4]:
        return (2.5 * gauge + 7) / (AURA_TAX * gauge)


def get_decay_rate():
    if btn_1A:
        return {'unit': 1, 'notation': 'A'}
    elif btn_2B:
        return {'unit': 2, 'notation': 'B'}
    elif btn_4C:
        return {'unit': 4, 'notation': 'C'}


def consume_gauge(modifier, aura_slot):
    aura_list[aura_slot].U -= get_decay_rate()['unit'] * modifier


def double_aura(aura1, aura2):
    if aura1.element == HYDRO and aura2 == ELECTRO \
            or aura1.element == ELECTRO and aura2 == HYDRO \
            or aura1.element == PYRO and aura2 == DENDRO \
            or aura1.element == DENDRO and aura2 == PYRO:
        U, d = get_decay_rate().values()
        if aura1.aura_count in [1, 2]:
            aura_list.append(Aura(True, U, d, aura2, 3 - aura1.aura_count))


def anemo_trigger(slot):
    if aura_list[slot].element in [ELECTRO, HYDRO, PYRO, CRYO]:
        consume_gauge(REACTION_MODIFIER['Swirl'], slot)
        record_to_log('Swirl')


def geo_trigger(slot):
    if aura_list[slot].element in [ELECTRO, HYDRO, PYRO, CRYO]:
        consume_gauge(REACTION_MODIFIER['Crystalize'], slot)
        record_to_log('Crystalize')


def electro_trigger():
    global electro_charged, frame_electro_charged
    for i in [-1, -2]:
        if aura_list[i].element == PYRO:
            consume_gauge(REACTION_MODIFIER['normal'], i)
            record_to_log('Overload')
        if aura_list[i].element == CRYO:
            consume_gauge(REACTION_MODIFIER['normal'], i)
            record_to_log('Superconduct')
        if aura_list[i].element == DENDRO:
            record_to_log('Quicken')
    for i in [-1, -2]:
        if aura_list[i].element == HYDRO:
            double_aura(aura_list[i], ELECTRO)
            record_to_log('Electro-Charged')
            aura_list[-1].U -= REACTION_CONSUMER['Electro-Charged']
            aura_list[-2].U -= REACTION_CONSUMER['Electro-Charged']
            frame_electro_charged = 0
            electro_charged = True
            break


def hydro_trigger():
    global electro_charged, frame_electro_charged
    for i in [-1, -2]:
        if aura_list[i].element == PYRO:
            consume_gauge(REACTION_MODIFIER['forward'], i)
            record_to_log('Vaporize')
        if aura_list[i].element == DENDRO:
            record_to_log('Bloom')
    for i in [-1, -2]:
        if aura_list[i].element == ELECTRO:
            double_aura(aura_list[i], HYDRO)
            record_to_log('Electro-Charged')
            aura_list[-1].U -= REACTION_CONSUMER['Electro-Charged']
            aura_list[-2].U -= REACTION_CONSUMER['Electro-Charged']
            frame_electro_charged = 0
            electro_charged = True
            break


def pyro_trigger():
    global burning, frame_burning
    for i in [-1, -2]:
        if aura_list[i].element == CRYO:
            consume_gauge(REACTION_MODIFIER['forward'], i)
            record_to_log('Melt')
        if aura_list[i].element == HYDRO:
            consume_gauge(REACTION_MODIFIER['reverse'], i)
            record_to_log('Vaporize')
        if aura_list[i].element == ELECTRO:
            consume_gauge(REACTION_MODIFIER['normal'], i)
            record_to_log('Overload')
    for i in [-1, -2]:
        if aura_list[i].element == DENDRO:
            double_aura(aura_list[i], PYRO)
            record_to_log('Burning')
            frame_burning = 0
            burning = True
            break


def cryo_trigger(slot):
    if aura_list[slot].element == ELECTRO:
        consume_gauge(REACTION_MODIFIER['normal'], slot)
        record_to_log('Superconduct')
    if aura_list[slot].element == PYRO:
        consume_gauge(REACTION_MODIFIER['reverse'], slot)
        record_to_log('Melt')


def dendro_trigger():
    global burning, frame_burning
    for i in [-1, -2]:
        if aura_list[i].element == PYRO:
            double_aura(aura_list[i], DENDRO)
            record_to_log('Burning')
            frame_burning = 0
            burning = True
            break
    for i in [-1, -2]:
        if aura_list[i].element == HYDRO:
            record_to_log('Bloom')
        if aura_list[i].element == ELECTRO:
            record_to_log('Quicken')


def electro_charged_tick():
    global electro_charged, frame_electro_charged
    if electro_charged:
        if frame_electro_charged == 5 * round(fps / 5) and len(aura_list) >= 2:
            frame_electro_charged = 0
            aura_list[-1].U -= REACTION_CONSUMER['Electro-Charged']
            aura_list[-2].U -= REACTION_CONSUMER['Electro-Charged']
            record_to_log('Electro-Charged')
        if aura_list[-1].U <= 0 or aura_list[-2].U <= 0:
            electro_charged = False
            frame_electro_charged = (
                5 * round(fps / 5)) + 1


def burning_tick():
    global frame_burning, burning
    if burning:
        if frame_burning == FPS / 4 and len(aura_list) >= 2:
            frame_burning = 0
            record_to_log('Burning')
            # reapply 1A Pyro every tick
            for i in [-1, -2]:
                if aura_list[-3 - i].element == DENDRO \
                        and aura_list[i].element == PYRO \
                        and aura_list[i].U <= AURA_TAX * 1:
                    aura_list[i] = Aura(True, 1, 'A', PYRO, 3 + i)
                    break
        if aura_list[-1].U <= 0 or aura_list[-2].U <= 0:
            burning = False
            frame_burning = FPS / 4 + 1


def apply_aura(element):
    # return True or False based on 'Has any aura been applied or refreshed?'

    # if no aura, then apply an element
    if not aura_list[-1].aura:
        U, d = get_decay_rate().values()
        aura_list.append(Aura(True, U, d, element, 1))
        return True

    # if there a same aura existed, then refresh it
    for i in [-1, -2]:
        if element == aura_list[i].element \
                and aura_list[i].aura \
                and aura_list[i].U < AURA_TAX * get_decay_rate()['unit']:
            aura_list[i] = Aura(True, get_decay_rate()['unit'],
                                aura_list[i].decay_U, element, aura_list[i].aura_count)
            return True
    return False


def update_frames():
    global frame_electro_charged, frame_burning
    frame_electro_charged += 1
    frame_burning += 1


# View functions

def aura_display_size(aura_count):
    if aura_count == 1:
        if len(aura_list) == 2:     # 1 aura - middle
            return (CNVW - LOGW - AURS) / 2, CNVH / 2.8 - AURS / 2 - 30
        if len(aura_list) == 3:     # 2 auras, 1st - left
            return (CNVW - LOGW) / 2 - AURS, CNVH / 2.8 - AURS / 2 - 30
    if aura_count == 2:             # 2 auras, 2nd - right
        return (CNVW - LOGW) / 2, CNVH / 2.8 - AURS / 2 - 30


def record_to_log(reaction_text):
    reaction_log_list.insert(0, ReactionText(reaction_text))


def display_aura(aura):
    if aura.aura:
        img = pygame.transform.scale(
            element_img_list[aura.element], (AURS, AURS))
        canvas.blit(img, aura_display_size(aura.aura_count))


def display_unit_bar(aura):
    if aura.aura:
        pygame.draw.rect(canvas, (ELEMENT_COLOR[aura.element]), pygame.Rect(
            0, CNVH - (100 * aura.aura_count), aura.U * (CNVW / 4), 30))


def display_number_and_notation(aura):
    if aura.aura:
        font = pygame.font.Font(path.FONT_JAJP, FNTS_TXT)
        img = font.render(
            '{:.2f}'.format(aura.U) + aura.decay_U, True, TXTC)
        canvas.blit(img, (10, CNVH - (100 * aura.aura_count) - 40))


def update_aura_list():
    for i in range(len(aura_list)):
        if aura_list[i].aura:
            display_aura(aura_list[i])
            aura_list[i].decay()
            display_unit_bar(aura_list[i])
            display_number_and_notation(aura_list[i])


def reaction_trigger(_mouse_x, _mouse_y):
    if CNVH - ELMS < _mouse_y < CNVH:
        for i in range(2):
            slot = - i - 1
            if ELMS * ANEMO < _mouse_x < ELMS * (ANEMO + 1):
                anemo_trigger(slot)
            if ELMS * GEO < _mouse_x < ELMS * (GEO + 1):
                geo_trigger(slot)
            if ELMS * CRYO < _mouse_x < ELMS * (CRYO + 1):
                cryo_trigger(slot)
        if ELMS * DENDRO < _mouse_x < ELMS * (DENDRO + 1):
            dendro_trigger()
        if ELMS * PYRO < _mouse_x < ELMS * (PYRO + 1):
            pyro_trigger()
        if ELMS * ELECTRO < _mouse_x < ELMS * (ELECTRO + 1):
            electro_trigger()
        if ELMS * HYDRO < _mouse_x < ELMS * (HYDRO + 1):
            hydro_trigger()


def play_sound(sound_name):
    if sound_name == 'bark':
        pygame.mixer.Sound(path.SOUND_BARK).play()


def click_button(_mouse_x, _mouse_y):
    global btn_1A, btn_2B, btn_4C
    y = CNVH - 50
    w = 45
    h = 40
    buttons = [False] * 3
    for i in range(3):
        x = CNVW - 300 + 100 * i
        if x < _mouse_x < x + w:
            if y < _mouse_y < y + h:
                buttons[i] = True
                btn_1A, btn_2B, btn_4C = buttons
                play_sound('bark')


def click_element(_mouse_x, _mouse_y):
    for element in range(len(element_img_list)):
        if ELMS * element < _mouse_x < ELMS * (element + 1) \
                and CNVH - ELMS < _mouse_y < CNVH:
            play_sound('bark')
            if not apply_aura(element):
                reaction_trigger(_mouse_x, _mouse_y)


def click(_mouse_x, _mouse_y):
    click_button(_mouse_x, _mouse_y)
    click_element(_mouse_x, _mouse_y)


def draw_element_imgs():
    for i in range(len(element_img_list)):
        canvas.blit(pygame.transform.scale(
            element_img_list[i], (ELMS, ELMS)), (ELMS * i, CNVH - ELMS))


def draw_rulers():
    for i in [1, 2]:
        for x in range(5):
            pygame.draw.rect(canvas, RLRC, pygame.Rect(
                x * (CNVW / 4) - 2, CNVH - (100 * i), 2, 30))
            if x == 4:
                pygame.draw.rect(canvas, RLRC, pygame.Rect(
                    x * (CNVW / 4) - 3, CNVH - (100 * i), 2, 30))
        for x in range(40):
            pygame.draw.rect(canvas, RLRC, pygame.Rect(
                x * (CNVW / 40) - 2, CNVH - (100 * i), 1, 20))


def draw_buttons():
    font1A = pygame.font.Font(path.FONT_JAJP, FNTS_BTN)
    font1A.set_underline(btn_1A)
    img = font1A.render("1A", True, TXTC)
    canvas.blit(img, (CNVW - 300, CNVH - 50))
    font2B = pygame.font.Font(path.FONT_JAJP, FNTS_BTN)
    font2B.set_underline(btn_2B)
    img = font2B.render("2B", True, TXTC)
    canvas.blit(img, (CNVW - 200, CNVH - 50))
    font4C = pygame.font.Font(path.FONT_JAJP, FNTS_BTN)
    font4C.set_underline(btn_4C)
    img = font4C.render("4C", True, TXTC)
    canvas.blit(img, (CNVW - 100, CNVH - 50))


def draw_reaction_log():
    if len(reaction_log_list) > 0:
        for i in range(len(reaction_log_list)):
            font = pygame.font.Font(path.FONT_JAJP, FNTS_TXT)
            font = font.render(
                reaction_log_list[i].text, True, reaction_log_list[i].color)
            canvas.blit(font, (CNVW - LOGW, (CNVH - LOGW) - 30 * i + 15))


def draw():
    draw_element_imgs()
    update_aura_list()
    draw_rulers()
    draw_buttons()
    draw_reaction_log()


def remove_inactive_auras():
    global aura_list
    aura_list = [aura_list[i] for i in range(
        len(aura_list)) if aura_list[i].aura or aura_list[i].aura_count == 3]


def trim_reaction_log_list():
    global reaction_log_list
    reaction_log_list = [reaction_log_list[i]
                         for i in range(len(reaction_log_list)) if i <= 12]


####### Actual program #######

# initialize

btn_1A = True
for fileName in os.listdir(path.ELEMENTS):
    element_img_list.append(pygame.image.load(path.ELEMENTS + fileName))
pygame.init()
pygame.mixer.init()
canvas = pygame.display.set_mode((CNVW, CNVH))
pygame.display.set_caption(CAPTION)
favicon = pygame.image.load(path.FAVICON)
pygame.display.set_icon(favicon)
aura_list.append(Aura(False, 1, 'A', 7, 3))
clock = pygame.time.Clock()

# game loop

running = True
while running:
    update_frames()

    canvas.fill(BGRC)
    draw()

    electro_charged_tick()
    burning_tick()

    mouse_x, mouse_y = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            click(mouse_x, mouse_y)

    remove_inactive_auras()
    trim_reaction_log_list()

    fps = clock.get_fps()
    pygame.display.update()
    clock.tick(FPS)
