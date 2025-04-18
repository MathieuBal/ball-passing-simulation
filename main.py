import pygame
import random
import math

# Initialisation de Pygame
pygame.init()

# Constantes
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
PLAYER_RADIUS = 10
BALL_RADIUS = 5
TEAM_A_COLOR = (0, 0, 255)  # Bleu
TEAM_B_COLOR = (255, 0, 0)  # Rouge
BALL_COLOR = (255, 165, 0)  # Orange
START_BACKGROUND_COLOR = (0, 128, 0)  # Vert
END_BACKGROUND_COLOR = (128, 128, 128)  # Gris
FRAME_RATE = 60
PLAYER_SPEED = 2
BALL_SPEED = 3
CROSSER_SIZE = 20
CROSSER_SPEED = 2
number_of_players_per_team = 10

# Configuration de la fenêtre
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Ball Passing Simulation')

# Initialisation des joueurs
players = []

# Initialisation du compteur de passes
passes_count = {'A': 0, 'B': 0}

PASS_DELAY = 1000  # Temps d'attente en millisecondes avant de pouvoir passer la balle

# Fonction pour créer des joueurs sans chevauchement
def create_non_overlapping_players(team, team_color):
    count = 0
    while count < number_of_players_per_team:
        overlapping = False
        new_player = {
            'pos': [random.randint(PLAYER_RADIUS, SCREEN_WIDTH - PLAYER_RADIUS),
                    random.randint(PLAYER_RADIUS, SCREEN_HEIGHT - PLAYER_RADIUS)],
            'destination': [random.randint(PLAYER_RADIUS, SCREEN_WIDTH - PLAYER_RADIUS),
                            random.randint(PLAYER_RADIUS, SCREEN_HEIGHT - PLAYER_RADIUS)],
            'has_ball': False,
            'can_receive': True,
            'team': team,
            'color': team_color,
            'wait_time': 0,
            'last_passed_to': None,
            'size': PLAYER_RADIUS,
        }
        for player in players:
            distance = math.hypot(player['pos'][0] - new_player['pos'][0],
                                  player['pos'][1] - new_player['pos'][1])
            if distance < 2 * PLAYER_RADIUS:
                overlapping = True
                break
        if not overlapping:
            players.append(new_player)
            count += 1

create_non_overlapping_players('A', TEAM_A_COLOR)
create_non_overlapping_players('B', TEAM_B_COLOR)

# Initialisation des balles pour chaque équipe
balls = {
    'A': {
        'pos': players[0]['pos'].copy(),
        'target_player': None
    },
    'B': {
        'pos': players[number_of_players_per_team]['pos'].copy(),
        'target_player': None
    }
}

# Attribution de la balle au premier joueur de chaque équipe
players[0]['has_ball'] = True
players[number_of_players_per_team]['has_ball'] = True
balls['A']['target_player'] = players[0]
balls['B']['target_player'] = players[number_of_players_per_team]

# Déplacement des joueurs
def move_players():
    for player in players:
        dir_x = player['destination'][0] - player['pos'][0]
        dir_y = player['destination'][1] - player['pos'][1]
        distance = math.hypot(dir_x, dir_y)
        if distance < PLAYER_SPEED:
            player['destination'] = [random.randint(PLAYER_RADIUS, SCREEN_WIDTH - PLAYER_RADIUS),
                                     random.randint(PLAYER_RADIUS, SCREEN_HEIGHT - PLAYER_RADIUS)]
        else:
            dir_x /= distance
            dir_y /= distance
            player['pos'][0] += dir_x * PLAYER_SPEED
            player['pos'][1] += dir_y * PLAYER_SPEED

# Trouver le coéquipier le plus proche pouvant recevoir la balle
def find_closest_teammate(current_player, team):
    min_distance = float('inf')
    closest_player = None
    for teammate in players:
        if teammate['team'] == team and teammate != current_player and teammate['can_receive']:
            if 'last_passed_to' in current_player and current_player['last_passed_to'] is not None:
                if teammate == players[current_player['last_passed_to']]:
                    continue
            current_time = pygame.time.get_ticks()
            if teammate['wait_time'] > current_time:
                continue
            distance = math.hypot(teammate['pos'][0] - current_player['pos'][0], teammate['pos'][1] - current_player['pos'][1])
            if distance < min_distance:
                min_distance = distance
                closest_player = teammate
    return closest_player

# Vérifie la collision entre un joueur et un obstacle
def check_collision(player, crosser):
    crosser_x1, crosser_y1 = crosser['pos']
    crosser_x2, crosser_y2 = crosser_x1 + CROSSER_SIZE, crosser_y1 + CROSSER_SIZE
    player_x, player_y = player['pos']
    player_radius = player['size']
    closest_x = max(crosser_x1, min(player_x, crosser_x2))
    closest_y = max(crosser_y1, min(player_y, crosser_y2))
    distance = math.hypot(closest_x - player_x, closest_y - player_y)
    return distance < player_radius

# Vérifie la collision entre deux joueurs
def check_player_collision(player1, player2):
    distance = math.hypot(player1['pos'][0] - player2['pos'][0],
                          player1['pos'][1] - player2['pos'][1])
    return distance < (player1['size'] + player2['size'])

# Repousse deux joueurs en collision
def repulse_players(player1, player2):
    dx = player1['pos'][0] - player2['pos'][0]
    dy = player1['pos'][1] - player2['pos'][1]
    distance = math.hypot(dx, dy)
    if distance == 0:
        dx, dy = 1, 0
    else:
        dx, dy = dx / distance, dy / distance
    repulse_distance = PLAYER_RADIUS * 2
    player1['destination'] = [player1['pos'][0] + dx * repulse_distance, player1['pos'][1] + dy * repulse_distance]
    player2['destination'] = [player2['pos'][0] - dx * repulse_distance, player2['pos'][1] - dy * repulse_distance]
    player1['destination'][0] = max(PLAYER_RADIUS, min(player1['destination'][0], SCREEN_WIDTH - PLAYER_RADIUS))
    player1['destination'][1] = max(PLAYER_RADIUS, min(player1['destination'][1], SCREEN_HEIGHT - PLAYER_RADIUS))
    player2['destination'][0] = max(PLAYER_RADIUS, min(player2['destination'][0], SCREEN_WIDTH - PLAYER_RADIUS))
    player2['destination'][1] = max(PLAYER_RADIUS, min(player2['destination'][1], SCREEN_HEIGHT - PLAYER_RADIUS))

# Déplacement de la balle vers le joueur cible
def move_ball(ball, team):
    if ball['target_player']:
        dir_x = ball['target_player']['pos'][0] - ball['pos'][0]
        dir_y = ball['target_player']['pos'][1] - ball['pos'][1]
        distance = math.hypot(dir_x, dir_y)
        if distance < BALL_SPEED:
            current_player = ball['target_player']
            current_player['has_ball'] = False
            current_player['size'] = int(PLAYER_RADIUS * 1.5)
            current_player['can_receive'] = False
            current_player['wait_time'] = pygame.time.get_ticks() + PASS_DELAY
            closest_player = find_closest_teammate(current_player, team)
            if closest_player:
                passes_count[team] += 1
                closest_player['last_passed_to'] = players.index(current_player)
                ball['target_player'] = closest_player
                closest_player['has_ball'] = True
                closest_player['wait_time'] = pygame.time.get_ticks() + PASS_DELAY
                event_id = pygame.USEREVENT + players.index(closest_player)
                pygame.time.set_timer(event_id, 1000, loops=3)
        else:
            dir_x /= distance
            dir_y /= distance
            ball['pos'][0] += dir_x * BALL_SPEED
            ball['pos'][1] += dir_y * BALL_SPEED

# Autoriser un joueur à recevoir de nouveau la balle
def enable_receiving(player_index):
    players[player_index]['can_receive'] = True
    players[player_index]['last_passed_to'] = None

# Affiche un message à l'écran
def display_text(message, position, font_size):
    font = pygame.font.Font(None, font_size)
    text = font.render(message, True, (255, 255, 255))
    text_rect = text.get_rect(center=position)
    screen.blit(text, text_rect)

# Compte à rebours avant de commencer
def countdown():
    for i in range(3, 0, -1):
        screen.fill(START_BACKGROUND_COLOR)
        display_text(str(i), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 100)
        for player in players:
            pygame.draw.circle(screen, player['color'], player['pos'], player['size'])
        for ball_key in balls:
            pygame.draw.circle(screen, BALL_COLOR, balls[ball_key]['pos'], BALL_RADIUS)
        pygame.display.flip()
        pygame.time.wait(1000)

# Affiche le nombre de passes à la fin
def show_passes_count():
    screen.fill(START_BACKGROUND_COLOR)
    display_text(f"Team Bleu passes: {passes_count['A']}", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 25), 50)
    display_text(f"Team Rouge passes: {passes_count['B']}", (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 25), 50)
    pygame.display.flip()
    pygame.time.wait(5000)

# Initialisation des obstacles
crossers = []
crosser_timer = random.randint(3000, 5000)

# Ajouter un obstacle mobile
def add_crosser():
    crosser = {
        'pos': [0, random.randint(0, SCREEN_HEIGHT)],
        'color': TEAM_A_COLOR if random.choice([True, False]) else TEAM_B_COLOR,
        'speed': CROSSER_SPEED
    }
    crossers.append(crosser)

# Interpolation de la couleur du fond
def interpolate_color(start_color, end_color, t):
    return tuple(start_color[i] + (end_color[i] - start_color[i]) * t for i in range(3))

# Début de la simulation
countdown()

start_time = pygame.time.get_ticks()
background_lerp_t = 0
running = True
clock = pygame.time.Clock()

# Boucle principale du jeu
while running:
    if pygame.time.get_ticks() - start_time > 60000:
        show_passes_count()
        break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type >= pygame.USEREVENT and event.type < pygame.USEREVENT + number_of_players_per_team * 2:
            player_index = event.type - pygame.USEREVENT
            enable_receiving(player_index)
        elif event.type == pygame.USEREVENT:
            add_crosser()

    for player in players:
        for crosser in crossers:
            if check_collision(player, crosser):
                player['destination'] = [random.randint(PLAYER_RADIUS, SCREEN_WIDTH - PLAYER_RADIUS),
                                         random.randint(PLAYER_RADIUS, SCREEN_HEIGHT - PLAYER_RADIUS)]

    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            if check_player_collision(players[i], players[j]):
                repulse_players(players[i], players[j])

    crosser_timer -= clock.get_time()
    if crosser_timer <= 0:
        add_crosser()
        crosser_timer = random.randint(3000, 5000)

    for crosser in crossers[:]:
        crosser['pos'][0] += crosser['speed']
        if crosser['pos'][0] > SCREEN_WIDTH:
            crossers.remove(crosser)

    background_lerp_t += 1 / (FRAME_RATE * 60)
    background_color = interpolate_color(START_BACKGROUND_COLOR, END_BACKGROUND_COLOR, background_lerp_t)

    move_players()
    move_ball(balls['A'], 'A')
    move_ball(balls['B'], 'B')

    for player in players:
        if player['size'] > PLAYER_RADIUS:
            player['size'] -= 1
        else:
            player['size'] = PLAYER_RADIUS

    screen.fill(background_color)
    for player in players:
        pygame.draw.circle(screen, player['color'], player['pos'], player['size'])
    for ball_key in balls:
        pygame.draw.circle(screen, BALL_COLOR, balls[ball_key]['pos'], BALL_RADIUS)
    for crosser in crossers:
        pygame.draw.rect(screen, crosser['color'], pygame.Rect(crosser['pos'][0], crosser['pos'][1], CROSSER_SIZE, CROSSER_SIZE))

    pygame.display.flip()
    clock.tick(FRAME_RATE)

pygame.quit()
