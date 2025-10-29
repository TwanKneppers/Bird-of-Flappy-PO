"""
The classic game of flappy bird, but now it's selflearning. Implemented in python and pygame,
with NEAT python AI library, following along Tech with Tim's tutorial "AI plays Flappy Bird". Thanx Tim!

Date Modified:  August 12, 2024 & August 21, 2025
Author: meester Bart
"""
import pygame
import random
import os
import neat
import pickle
pygame.font.init()  # init font

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())

gen = 0

class Bird:
    """
    Bird class representing the flappy bird
    """
    MAX_ROTATION = 25
    IMGS = bird_images
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        """
        Initialize the object
        :param x: starting x pos (int)
        :param y: starting y pos (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # degrees to tilt
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        make the bird jump
        :return: None
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        make the bird move
        :return: None
        """
        self.tick_count += 1

        # for downward acceleration
        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2  # calculate displacement

        # terminal velocity
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # tilt down
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        draw the bird
        :param win: pygame window or surface
        :return: None
        """
        self.img_count += 1

        # For animation of bird, loop through three images
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # so when bird is nose diving it isn't flapping
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2


        # tilt the bird
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        """
        gets the mask for the current image of the bird
        :return: None
        """
        return pygame.mask.from_surface(self.img)


class Pipe():
    """
    represents a pipe object
    """
    GAP = 160
    # Verandert van 200 naar 160 voor ruimte tussen buizen
    VEL = 5

    def __init__(self, x):
        """
        initialize pipe object
        :param x: int
        :param y: int
        :return" None
        """
        self.x = x
        self.height = 0

        # where the top and bottom of the pipe is
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False

        self.set_height()

    def set_height(self):
        """
        set the height of the pipe, from the top of the screen
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        move pipe based on vel
        :return: None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        draw both the top and bottom of the pipe
        :param win: pygame window/surface
        :return: None
        """
        # draw top
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # draw bottom
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


    def collide(self, bird, win):
        """
        returns if a point is colliding with the pipe
        :param bird: Bird object
        :return: Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask,top_offset)

        if b_point or t_point:
            return True

        return False

class Base:
    """
    Represents the moving floor of the game
    """
    VEL = 5
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        """
        Initialize the object
        :param y: int
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        move floor so it looks like its scrolling
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Draw the floor. This is two images that move together.
        :param win: the pygame surface/window
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def blitRotateCenter(surf, image, topleft, angle):
    """
    Rotate a surface and blit it to the window
    :param surf: the surface to blit to
    :param image: the image surface to rotate
    :param topLeft: the top left position of the image
    :param angle: a float value for angle
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    draws the windows for the main game loop
    :param win: pygame window surface
    :param bird: a Bird object
    :param pipes: List of pipes
    :param score: score of the game (int)
    :param gen: current generation
    :param pipe_ind: index of closest pipe
    :return: None
    """
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # draw bird
        bird.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # generations
    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # alive
    score_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    pygame.display.update()

# Deze functie evalueert de vogels en geeft ze een fitness score
def eval_genomes(genomes, config):
    """
    runs the simulation of the current population of
    birds and sets their fitness based on the distance they
    reach in the game.
    """
    # win is vereist voor pygame
    global WIN, gen
    win = WIN
    # Elke keer dat een nieuwe generatie getest wordt gaat dit 1 omhoog
    gen += 1

    # In deze arrays worden de netwerken, vogels en genomes opgeslagen met een index, zo hoort de net bij index 1 bij het vogeltje op index 1 en het genome op index 1
    nets = []
    birds = []
    ge = []

    # Deze for loop maakt vogels, netwerken en de fitness van genomes aan en zet ze in de correcte array
    for genome_id, genome in genomes:
        genome.fitness = 0
        # In de variabele net wordt een netwerk opgeslagen met de genome en config als blauwdruk opgeslagen
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(genome)

    # In deze variabele worden de vloer (base), pijpen en score opgeslagen
    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    # Dit is een object dat de verlopen tijd per frame bijhoudt
    clock = pygame.time.Clock()

    run = True
    # Deze while loop bevat de main game loop en blijft lopen zolang run true is en er vogeltjes over zijn
    while run and len(birds) > 0:
        # Dit stelt een limiet op het maximum fps met behulp van de verlopen tijd sinds het vorige frame
        clock.tick(100)
        # Verandert van 60 naar 100 voor meer fps

        # Als de app gesloten wordt zorgt deze code ervoor dat ook alles van pygame sluit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        
        pipe_ind = 0
        # Als er nog vogels leven
        if len(birds) > 0:
            # Als er een pijp in de pipes array zit en het vogeltje voorbij de pijp is, dan wordt vanaf hier naar de volgende pijp in de array gekeken door middel van pipe_ind
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        # Leest de vogels met hun index af uit de birds array
        for x, bird in enumerate(birds):
            # Verhoogt de fitness van alle nog levende vogels en beweegt ze
            ge[x].fitness += 0.1
            bird.move()

            # Geeft data aan het neural net en slaat de uitvoer op
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            # Kijkt of de output van het neural net groter is dan de thresholdvalue, zo ja, dan springt de vogel
            if output[0] > 0.5:
                bird.jump()

        # Beweegt de vloer
        base.move()
 
        rem = []
        add_pipe = False
        # Voor elke pijp  in de array pipes
        for pipe in pipes:
            # Beweegt de pijp
            pipe.move()

            # Deze for loop kijkt voor elke vogel of hij een pijp aanraakt, zo ja, dan gaat hij dood
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            # Als de pijp links buiten het scherm is wordt hij aan de verwijder (rem) array toegevoegd
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            # Als de vogels de pijp voorbij zijn, dan wordt de variabele om een nieuw toe te voegen (add_pipe) op true gezet
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        # Als de vogels voorbij de pijp zijn
        if add_pipe:
            # Score gaat omhoog met 1
            score += 1

            # De fitness van de genome gaat omhoog
            for genome in ge:
                genome.fitness += 5

            # Een nieuwe pijp wordt aan de array toegevoegd
            pipes.append(Pipe(WIN_WIDTH))


        # Elke pijp in de verwijder (rem) array wordt verwijderd
        for r in rem:
            pipes.remove(r)

        # Als een vogel de grond raakt gaat hij dood
        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

            # code zodat de vogels stoppen op een score en direct de evaluate functie sluit, los van de generatie
            # eval functie loop sluit als alle vogels dood zijn en de fitness hoger is dan de threshold in de config-feedforward.txt
            if score > 150:
                genome.fitness = 1000
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        # De functie om het beeld te tekenen wordt aangeroepen
        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

# Deze functie zorgt ervoor dat de best bird game afgebeeld wordt
def bestGameDraw(win, bird, pipes, base, score):
    """
    draws the windows for the main game loop
    :param win: pygame window surface
    :param bird: a Bird object
    :param pipes: List of pipes
    :param score: score of the game (int)
    :return: None
    """
    # Dit tekent de achtergrond
    win.blit(bg_img, (0,0))

    # Dit tekent alle pijpen in de pipes array
    for pipe in pipes:
        pipe.draw(win)

    # Deze functies worden aangeroepen om de grond (base) en de vogel (bird) te tekenen
    base.draw(win)
    bird.draw(win)

    # Hiermee wordt de score afgebeeld
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # Deze functie update het hele scherm met de wijziginen die met de code hierboven worden afgebeeld
    pygame.display.update()

# Hier wordt het game over scherm getekend
def end_screen(win):
    """
    display an end screen when the player loses
    :param win: the pygame window surface
    :return: None
    """
    # Run op true zetten zorgt ervoor dat er weer een 'game loop' plaats kan vinden
    run = True
    # Dit vult een variabele met een uitleg tekst
    text_label = END_FONT.render("Space to Quit", 1, (255,255,255))
    # Deze while loop is de nieuwe 'game loop'
    while run:
        # Als er een knop op het toetsenbord wordt ingedrukt sluit de while loop
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                run = False

        # Dit tekent de tekst die eerder werdt opgeslagen
        win.blit(text_label, (WIN_WIDTH/2 - text_label.get_width()/2, 500))
        # Deze functie update het scherm met de wijzigingen die met de code hierboven worden afgebeeld
        pygame.display.update()

    # De window wordt gesloten en de code stopt
    pygame.quit()
    quit()

# Deze code speelt het beste vogeltje af
def bestGame(config):
    # win is vereist voor pygame
    global WIN
    win = WIN

    # De score en en vogel worden aangemaakt en in een variabele gezet
    score = 0
    bird = Bird(230,350)

    # Het vogeltje opgeslagen in ChickenDinner.txt wordt hier opgehaald en in een variabele gezet
    with open("ChickenDinner.txt", "rb") as save:
       bestBird = pickle.load(save)

    # Het neurale net van het beste vogeltje wordt aangemaakt
    net = neat.nn.FeedForwardNetwork.create(bestBird, config)

    # De vloer en pijpen worden aangemaakt
    base = Base(FLOOR)
    pipes = [Pipe(700)]

    # Dit is een object dat de verlopen tijd per frame bijhoudt
    clock = pygame.time.Clock()

    run = True
    # Deze while loop bevat de main game loop
    while run:
        # Dit stelt een limiet op het maximum fps met behulp van de verlopen tijd sinds het vorige frame
        clock.tick(100)

        # Als de app gesloten wordt zorgt deze code ervoor dat ook alles van pygame sluit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        # Als er een pijp in de pipes array zit en het vogeltje voorbij de pijp is, dan wordt vanaf hier naar de volgende pijp in de array gekeken door middel van pipe_ind
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # Beweegt het vogeltje
        bird.move()

        # Geeft data aan het neural net en slaat de uitvoer op
        output = net.activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

        # Kijkt of de output van het neural net groter is dan de thresholdvalue, zo ja, dan springt de vogel
        if output[0] > 0.5:
            bird.jump()

        # Beweegt de vloer
        base.move()

        rem = []
        add_pipe = False
        # Voor elke pijp  in de array pipes
        for pipe in pipes:
            # Beweegt de pijp
            pipe.move()

            # Als de pijp links buiten het scherm is wordt hij aan de verwijder (rem) array toegevoegd
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

             # Als de vogel de pijp voorbij is, dan wordt de variabele om een nieuw toe te voegen (add_pipe) op true gezet
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

         # Als de vogels voorbij de pijp zijn
        if add_pipe:
            # Score gaat omhoog met 1
            score += 1
            
            # Een nieuwe pijp wordt aan de array toegevoegd
            pipes.append(Pipe(WIN_WIDTH))

        # Elke pijp in de verwijder (rem) array wordt verwijderd
        for r in rem:
            pipes.remove(r)

        # Als de vogel een pijp raakt, dan stopt de game loop
        if pipe.collide(bird, win):
            break

        # Als de vogel de vloer raaktstopt de gameloop
        if bird.y + bird_images[0].get_height() - 10 >= FLOOR:
            break

        # De functie om het beeld te tekenen wordt aangeroepen
        bestGameDraw(WIN, bird, pipes, base, score)
    # De functie om het game over scherm te tekenen wordt aangeroepen
    end_screen(win)

def run(config_file):
    """
    runs the NEAT algorithm to train a neural network to play flappy bird.
    :param config_file: location of config file
    :return: None
    """

    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(5))


    # De gebruiker wordt gevraagd of die een vogel wilt trainen of afspelen
    keuzeVraag = input("Typ 0 om te trainen, typ 1 om de beste vogel te laten spelen")

    # Als er geen correct antwoord gegeven is wordt de vraag opnieuw gesteld
    while (keuzeVraag != "0" and keuzeVraag != "1"):
        keuzeVraag = input("Typ 0 om te trainen, typ 1 om de beste vogel te laten spelen")

    # Als de gebruiker wilt trainen
    if (keuzeVraag == "0"):
        # De train functie wordt maximaal 50 keer aangeroepen en de beste vogel wordt opgeslagen in winner
        winner = p.run(eval_genomes, 50)

        # De statistieken van de beste vogel worden geprint in de console
        print('\nBest genome:\n{!s}'.format(winner))

        # Slaat de beste vogel op in ChickenDinner.txt
        with open("ChickenDinner.txt", "wb") as save:
            pickle.dump(winner, save)

    # Als de gebruiker een vogel wilt afspelen, maar er geen vogel bestand bestaat, dan sluit het programma en wordt de gebruiker verteld om een vogel te trainen
    elif (keuzeVraag == "1" and os.path.isfile("ChickenDinner.txt") == False):
        print("Er bestaat geen beste vogel, probeer eerst te trainen")
        quit()

    # Als de gebruiker een vogel wilt afspelen, maar het vogel bestand leeg is, dan sluit het programma en wordt de gebruiker verteld om een vogel te trainen
    elif (keuzeVraag == "1" and os.path.getsize("ChickenDinner.txt") == 0):
        print("Er bestaat geen beste vogel, probeer eerst te trainen")
        quit()

    # Als de gebruiker een vogel wilt afspelen, wordt de afspeel functie aangeroepen
    elif (keuzeVraag == "1"):
        bestGame(config)


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
    pygame.quit()
