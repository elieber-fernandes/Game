import pygame
import math
import random
import asyncio
import os
import json
import sys


os.environ["PYGBAG_PIXEL_RATIO"] = "1"  # Força um DPI fixo compatível
os.environ["SDL_HINT_EMSCRIPTEN_ASYNCIFY"] = "1"  # Evita travamentos

pygame.init()

WIDTH, HEIGHT = 800, 600  # Tamanho fixo
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)


pygame.display.set_caption("Space Journey")

# Função para carregar imagens com verificação de erro
def load_image(file_path, fallback_color=(255, 0, 0)):
    try:
        if os.path.exists(file_path):
            return pygame.image.load(file_path)
        else:
            print(f"❌ Arquivo não encontrado: {file_path}")
            # Criar uma superfície de fallback
            surf = pygame.Surface((50, 50))
            surf.fill(fallback_color)
            return surf
    except pygame.error as e:
        print(f"❌ Erro ao carregar imagem {file_path}: {e}")
        # Criar uma superfície de fallback
        surf = pygame.Surface((50, 50))
        surf.fill(fallback_color)
        return surf

# Carregar imagens com tratamento de erro
bg_img = load_image('back.png')
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
enemy_img1 = load_image("polvo.png", (255, 0, 0))
enemy_img2 = load_image("polvo2.png", (255, 0, 0))
tank_img = load_image("Ship_2.png", (0, 255, 0))
shooter_img1 = load_image("shooter_1.png", (255, 0, 0))
shooter_img2 = load_image("shooter_2.png", (255, 0, 0))
meteor_img1 = load_image("meteor_img1.png", (139, 69, 19))
meteor_img2 = load_image("meteor_img2.png", (139, 69, 19)) 
meteor_img3 = load_image("meteor_img3.png", (139, 69, 19)) 

pygame.mixer.init()
# Carregar sons com tratamento de erro
try:
    shoot_sound = pygame.mixer.Sound("shoot.ogg")
    explosion_sound = pygame.mixer.Sound("explosion.ogg")
    tank_moving = pygame.mixer.Sound("ship_moving.ogg")
except pygame.error as e:
    print(f"❌ Erro ao carregar sons: {e}")
    # Criar um som vazio como fallback
    shoot_sound = pygame.mixer.Sound(buffer=bytearray(44100))  # 1 segundo de silêncio
    explosion_sound = pygame.mixer.Sound(buffer=bytearray(44100))
    tank_moving = pygame.mixer.Sound(buffer=bytearray(44100))

high_score = 0
FIREBASE_URL = "https://space-journey-27f32-default-rtdb.firebaseio.com/records.json"

# =================== RequestHandler para PyGBag =================== #
class RequestHandler:
    def __init__(self):
        self.is_emscripten = sys.platform == "emscripten"
        if self.is_emscripten:
            self._js_code = """
window.Fetch = {}
window.Fetch.POST = function * POST (url, data)
{
    console.log('POST: ' + url + ' Data: ' + data);
    var request = new Request(url, {headers: {'Accept': 'application/json','Content-Type': 'application/json'},
        method: 'POST',
        body: data});
    var content = 'undefined';
    fetch(request)
   .then(resp => resp.text())
   .then((resp) => {
        console.log(resp);
        content = resp;
   })
   .catch(err => {
         console.log("Erro na requisição:");
         console.log(err);
    });
    while(content == 'undefined'){ yield; }
    yield content;
}
window.Fetch.GET = function * GET (url)
{
    console.log('GET: ' + url);
    var request = new Request(url, { method: 'GET' });
    var content = 'undefined';
    fetch(request)
   .then(resp => resp.text())
   .then((resp) => {
        console.log(resp);
        content = resp;
   })
   .catch(err => {
         console.log("Erro na requisição:");
         console.log(err);
    });
    while(content == 'undefined'){ yield; }
    yield content;
}
            """
            try:
                import platform
                platform.window.eval(self._js_code)  # Executa o código JS no navegador
            except AttributeError:
                self.is_emscripten = False

    async def post(self, url, data):
        if self.is_emscripten:
            import platform
            gen = platform.window.Fetch.POST(url, json.dumps(data))
            while True:
                try:
                    return next(gen)
                except StopIteration as result:
                    return result.value
        else:
            import httpx # type: ignore
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                return response.text

    async def get(self, url):
        if self.is_emscripten:
            import platform
            gen = platform.window.Fetch.GET(url)
            while True:
                try:
                    return next(gen)
                except StopIteration as result:
                    return json.loads(result.value) if result.value else {}
        else:
            import httpx # type: ignore
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.json()

request_handler = RequestHandler()  # manipulador de requisições



# =================== Firebase =================== #
async def get_player_initials():
    initials = ""  
    font = pygame.font.Font(None, 50)
    input_active = True

    while input_active:
        screen.blit(bg_img, (0, 0))

        # Texto de instrução
        text_prompt = font.render("Digite suas iniciais:", True, (255, 255, 255))
        screen.blit(text_prompt, (WIDTH // 2 - 150, HEIGHT // 2 - 50))

        # Mostra as iniciais digitadas
        text_initials = font.render(initials, True, (255, 255, 0))
        screen.blit(text_initials, (WIDTH // 2 - 50, HEIGHT // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(initials) == 3:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE and len(initials) > 0:
                    initials = initials[:-1]
                elif len(initials) < 3 and event.unicode.isalnum():
                    initials += event.unicode.upper()

        await asyncio.sleep(0)

    return initials


async def save_high_score(name, score):
    data = {"name": name, "score": score}
    try:
        response = await request_handler.post(FIREBASE_URL, data)
        print("✅ Recorde salvo no Firebase!", response)
    except Exception as e:
        print("❌ Erro ao salvar recorde:", e)



async def get_top_scores():
    print("🔄 Buscando recordes no Firebase...")
    try:
        records = await request_handler.get(FIREBASE_URL)
        print("✅ Dados brutos recebidos:", records)

        if not records:
            print("⚠️ Nenhum recorde encontrado!")
            return []

        # Verifica se records é uma string (pode acontecer no ambiente web)
        if isinstance(records, str):
            try:
                records = json.loads(records)
                print("📝 Convertendo string JSON para dicionário:", records)
            except json.JSONDecodeError as e:
                print("❌ Erro ao decodificar JSON:", e)
                return []

        # Verifica se records é um dicionário válido
        if not isinstance(records, dict):
            print("❌ Formato inválido de records:", type(records))
            return []

        # Converte os valores para o formato esperado
        formatted_scores = []
        for record in records.values():
            try:
                formatted_scores.append({
                    "name": str(record.get("name", "???"))[:3],
                    "score": int(record.get("score", 0))
                })
                print("✅ Registro formatado:", formatted_scores[-1])
            except (ValueError, AttributeError) as e:
                print("❌ Erro ao formatar registro:", e, record)

        # Ordena por pontuação
        sorted_scores = sorted(formatted_scores, key=lambda x: x["score"], reverse=True)
        print("🏆 Top scores formatados:", sorted_scores[:10])

        return sorted_scores[:10]
    except Exception as e:
        print("❌ Erro ao conectar ao Firebase:", e)
        print("Tipo do erro:", type(e))
        print("Detalhes adicionais:", str(e))
        return []

# Ajuste também na função save_high_score
async def save_high_score(name, score):
    data = {
        "name": str(name)[:3],  # Garante que terá no máximo 3 caracteres
        "score": int(score)     # Garante que será um número inteiro
    }
    try:
        print("📝 Tentando salvar recorde:", data)
        response = await request_handler.post(FIREBASE_URL, data)
        print("✅ Recorde salvo no Firebase!", response)
        return True
    except Exception as e:
        print("❌ Erro ao salvar recorde:", e)
        print("Tipo do erro:", type(e))
        print("Detalhes adicionais:", str(e))
        return False


async def show_top_scores_screen():
    # Define cores constantes
    COR_TITULO = (21, 101, 230)  # Azul
    COR_PLACAR = (255, 255, 255)  # Branco
    COR_VOLTAR = (255, 0, 0)     # Vermelho
    
    font = pygame.font.Font(None, 50)
    text_titulo = font.render("TOP 10 PONTUAÇÕES", True, COR_TITULO)
    text_voltar = font.render("Pressione ESC para voltar", True, COR_VOLTAR)

    print("🔄 Buscando recordes completos...")
    top_scores = await get_top_scores()
    print("🏆 Top scores carregados:", top_scores)

    centro_x = WIDTH // 2
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        # Limpa a tela e desenha o fundo
        screen.blit(bg_img, (0, 0))
        
        # Título
        titulo_rect = text_titulo.get_rect(center=(centro_x, 50))
        screen.blit(text_titulo, titulo_rect)

        # Mostra placar
        y_offset = 120
        if not top_scores:
            no_scores_text = font.render("Nenhuma pontuação encontrada", True, COR_PLACAR)
            no_scores_rect = no_scores_text.get_rect(center=(centro_x, y_offset))
            screen.blit(no_scores_text, no_scores_rect)
        else:
            for i, record in enumerate(top_scores[:10]):
                try:
                    name = str(record.get("name", "???"))[:3]
                    score = str(record.get("score", "0"))
                    score_text = font.render(f"{i+1}. {name} - {score}", True, COR_PLACAR)
                    score_rect = score_text.get_rect(center=(centro_x, y_offset))
                    screen.blit(score_text, score_rect)
                    y_offset += 40
                except Exception as e:
                    print(f"❌ Erro ao renderizar pontuação {i}:", e)
                    print("Record problemático:", record)

        # Botão voltar
        voltar_rect = text_voltar.get_rect(center=(centro_x, HEIGHT - 50))
        screen.blit(text_voltar, voltar_rect)

        # Atualiza a tela
        pygame.display.flip()

        # Controle de FPS e async sleep
        await asyncio.sleep(0.016)  # Aproximadamente 60 FPS

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.acceleration = 0.3
        self.friction = 0.05
        self.velocity_x = 0
        self.velocity_y = 0
        self.rotation_speed = 3
        self.drift_factor = 0.95
        self.width, self.height = tank_img.get_size()
        self.health = 5
        self.score = 0
        self.bullets = []

    def update(self, keys):
        moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += self.rotation_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= self.rotation_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity_x += self.acceleration * math.cos(math.radians(self.angle))
            self.velocity_y -= self.acceleration * math.sin(math.radians(self.angle))
            moving = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity_x -= (self.acceleration / 2) * math.cos(math.radians(self.angle))
            self.velocity_y += (self.acceleration / 2) * math.sin(math.radians(self.angle))
            moving = True
    
        # Aplica o drift
        self.velocity_x *= self.drift_factor
        self.velocity_y *= self.drift_factor
    
        # Calcula a nova posição
        new_x = self.x + self.velocity_x
        new_y = self.y + self.velocity_y
    
        # Define as margens
        MARGIN_LEFT = 50
        MARGIN_RIGHT = WIDTH - 50
        MARGIN_TOP = 50
        MARGIN_BOTTOM = HEIGHT - 50
    
        global total_offset_x, total_offset_y
    
        # Movimento horizontal
        if new_x < MARGIN_LEFT:
            # Se o jogador tentar passar da margem esquerda
            total_offset_x += self.velocity_x
        elif new_x > MARGIN_RIGHT:
            # Se o jogador tentar passar da margem direita
            total_offset_x += self.velocity_x
        else:
            # Se estiver dentro das margens, atualiza a posição
            self.x = new_x
    
        # Movimento vertical
        if new_y < MARGIN_TOP:
            # Se o jogador tentar passar da margem superior
            total_offset_y += self.velocity_y
        elif new_y > MARGIN_BOTTOM:
            # Se o jogador tentar passar da margem inferior
            total_offset_y += self.velocity_y
        else:
            # Se estiver dentro das margens, atualiza a posição
            self.y = new_y
    
        # Som de movimento
        if moving and not pygame.mixer.get_busy():
            tank_moving.play()
            
    def shoot(self):
        bullet_speed = 7
        bullet_dx = bullet_speed * math.cos(math.radians(self.angle))
        bullet_dy = -bullet_speed * math.sin(math.radians(self.angle))
        self.bullets.append([self.x, self.y, bullet_dx, bullet_dy])
        shoot_sound.play()

    def update_bullets(self, enemies, explosions):
        """ Atualiza os projéteis do jogador e verifica colisões com inimigos e meteoros """
        for bullet in self.bullets[:]:
            bullet[0] += bullet[2]  # Atualiza a posição X do projétil
            bullet[1] += bullet[3]  # Atualiza a posição Y do projétil
    
            # Verifica colisão com meteoros
            for meteor in meteors[:]:  # Usando a lista global de meteoros
                if meteor.check_collision(bullet[0], bullet[1], 5):  # 5 é o raio do projétil
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    explosions.append(Explosion(meteor.x, meteor.y))
                    explosion_sound.play()
                    self.score += 5  # Pontuação por destruir um meteoro
                    meteors.remove(meteor)
                    break  # Sai do loop após encontrar colisão
    
            # Verifica colisão com cada inimigo (código existente)
            for enemy in enemies[:]:
                if enemy.check_collision(bullet[0], bullet[1]):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    enemy.health -= 1
                    if enemy.health <= 0:
                        enemies.remove(enemy)
                        explosions.append(Explosion(enemy.x, enemy.y))
                        explosion_sound.play()
                        self.score += 5  # Pontuação por destruir um inimigo
                    break  # Sai do loop após encontrar colisão
    
            # Remove projéteis que saíram da tela
            self.bullets = [b for b in self.bullets if 0 < b[0] < WIDTH and 0 < b[1] < HEIGHT]

    def draw(self, screen):
        rotated_tank = pygame.transform.rotate(tank_img, self.angle)
        rect = rotated_tank.get_rect(center=(self.x, self.y))
        screen.blit(rotated_tank, rect.topleft)
        
        # Desenha os projéteis
        for bullet in self.bullets:
            pygame.draw.circle(screen, (255, 0, 0), (int(bullet[0]), int(bullet[1])), 5)
        
        # Barra de saúde
        pygame.draw.rect(screen, (255, 0, 0), (10, 10, self.health * 20, 10))
        
        # Placar
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH - 150, 10))
    
    def check_collision_with_enemy(self, enemy):
        distance = math.hypot(self.x - enemy.x, self.y - enemy.y)
        return distance < (self.width // 3 + enemy.size)  # Ajustado para colisão mais precisa


def draw_background(offset_x, offset_y):
    """Desenha o plano de fundo repetidamente para criar o efeito de movimentação infinita."""
    bg_width = bg_img.get_width()
    bg_height = bg_img.get_height()

    # Calcula o deslocamento ajustado para manter o efeito de repetição
    offset_x %= bg_width
    offset_y %= bg_height

    # Desenha o plano de fundo em uma grade 3x3 ao redor do jogador
    for i in range(-1, 2):
        for j in range(-1, 2):
            screen.blit(bg_img, (i * bg_width - offset_x, j * bg_height - offset_y))
#GLOBAL
total_offset_x = 0
total_offset_y = 0
player = Player(WIDTH // 2, HEIGHT // 2)
player.bullets = [] 
enemies = []
explosions = []
spawn_timer = 0
enemy_spawn_rate = 150
score_threshold = 50  # Pontuação necessária para spawnar inimigos atiradores
max_enemies = 5  # Limite de inimigos na tela
shooter_enemy_spawned = False
SAFE_DISTANCE = 180
meteors = []
meteor_spawn_timer = 0
METEOR_SPAWN_RATE = 400  #controlar a frequência

# =================== Tela de Game Over =================== #
async def game_over_screen():
    global player, high_score
    await asyncio.sleep(1)
    if player.score > high_score:
        high_score = player.score  

    print("⌨️ Pedindo iniciais do jogador...")
    name = await get_player_initials()
    print(f"✅ Nome recebido: {name}")

    await save_high_score(name, player.score)

    # Define cores constantes
    COR_TITULO = (255, 0, 0)      # Vermelho 
    COR_SUBTITULO = (21, 101, 230) # Azul
    COR_PLACAR = (255, 255, 255)   # Branco
    COR_REINICIAR = (0, 255, 0)    # Verde

    # Centraliza todos os textos
    centro_x = WIDTH // 2

    font = pygame.font.Font(None, 50)
    text_game_over = font.render("FIM DE JOGO", True, COR_TITULO)
    text_ranking = font.render("CLIQUE AQUI PARA VER TOP 10", True, COR_SUBTITULO)
    text_restart = font.render("Pressione ENTER para reiniciar", True, COR_REINICIAR)

    print("🔄 Buscando recordes...")
    top_scores = await get_top_scores()
    print("🏆 Top scores carregados:", top_scores)

    ranking_rect = text_ranking.get_rect(center=(centro_x, HEIGHT // 3 + 60))

    while True:
        screen.blit(bg_img, (0, 0))
        
        # Posiciona textos usando rect para centralização
        game_over_rect = text_game_over.get_rect(center=(centro_x, HEIGHT // 3))
        screen.blit(text_game_over, game_over_rect)

        # Desenha o botão de ranking
        pygame.draw.rect(screen, COR_SUBTITULO, ranking_rect.inflate(20, 10), 2)  # Borda do botão
        screen.blit(text_ranking, ranking_rect)

        # Texto de reinício na parte inferior
        restart_rect = text_restart.get_rect(center=(centro_x, HEIGHT - 80))
        screen.blit(text_restart, restart_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    restart_game()
                    await main()
                    return
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Verifica se clicou no botão de ranking
                if ranking_rect.collidepoint(event.pos):
                    await show_top_scores_screen()

        await asyncio.sleep(0)

# =================== Reiniciar o Jogo =================== #

        
def restart_game():
    global player, enemies, explosions, spawn_timer, meteors, meteor_spawn_timer
    player = Player(WIDTH // 2, HEIGHT // 2)
    player.health = 5
    player.score = 0
    enemies = []
    explosions = []
    meteors = []
    spawn_timer = 0
    meteor_spawn_timer = 0



class ShooterEnemy:
    def __init__(self, x, y, speed=0):
        self.x = x
        self.y = y
        self.size = 30
        self.speed = speed
        self.health = 2  # Mais resistente
        self.shoot_cooldown = 150  # Tempo entre disparos (frames)
        self.current_cooldown = 0
        self.bullets = []

        # Animação
        self.animation_frames = [
            pygame.transform.scale(shooter_img1, (60, 60)),
            pygame.transform.scale(shooter_img2, (60, 60))
        ]
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 10

    def move_towards_player(self, player_x, player_y):
        angle = math.atan2(player_y - self.y, player_x - self.x)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)

        # Animação
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)

        # Reduz cooldown do tiro
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
        else:
            self.shoot(player_x, player_y)

    def shoot(self, player_x, player_y):
        """ O inimigo dispara um projétil em direção ao jogador """
        bullet_speed = 4
        angle = math.atan2(player_y - self.y, player_x - self.x)
        bullet_dx = bullet_speed * math.cos(angle)
        bullet_dy = bullet_speed * math.sin(angle)
        self.bullets.append([self.x, self.y, bullet_dx, bullet_dy])
        self.current_cooldown = self.shoot_cooldown  # Reinicia cooldown

    def update_bullets(self, player):
        """ Atualiza os tiros do inimigo e verifica colisão com o jogador """
        for bullet in self.bullets[:]:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]

            # Se atingir o jogador, ele perde vida
            if math.hypot(player.x - bullet[0], player.y - bullet[1]) < player.width // 2:
                player.health -= 1
                self.bullets.remove(bullet)

        # Remove projéteis que saíram da tela
        self.bullets = [b for b in self.bullets if 0 < b[0] < WIDTH and 0 < b[1] < HEIGHT]

    def check_collision(self, bullet_x, bullet_y):
        """ Verifica se um projétil do jogador atingiu este inimigo """
        return math.hypot(bullet_x - self.x, bullet_y - self.y) < self.size

    def draw(self, screen):
        """ Desenha o inimigo e seus projéteis """
        enemy_sprite = self.animation_frames[self.current_frame]
        rect = enemy_sprite.get_rect(center=(self.x, self.y))
        screen.blit(enemy_sprite, rect.topleft)

        # Desenha os tiros do inimigo
        for bullet in self.bullets:
            pygame.draw.circle(screen, (255, 0, 0), (int(bullet[0]), int(bullet[1])), 5)




class Enemy:
    def __init__(self, x, y, speed=1):
        self.x = x
        self.y = y
        self.size = 30  # Raio do inimigo
        self.speed = speed
        self.health = 1  # Vida do inimigo
        # Configuração da animação
        self.animation_frames = [
            pygame.transform.scale(enemy_img1, (60, 60)),
            pygame.transform.scale(enemy_img2, (60, 60))
        ]
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 10

    def check_collision(self, bullet_x, bullet_y):
        """ Verifica se um projétil do jogador atingiu este inimigo """
        distance = math.hypot(bullet_x - self.x, bullet_y - self.y)
        return distance < self.size  # Verifica se o projétil está dentro do raio do inimigo

    def move_towards_player(self, player_x, player_y):
        angle = math.atan2(player_y - self.y, player_x - self.x)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)
        
        # Animação
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.animation_frames)

    def draw(self, screen):
        # Desenha o inimigo usando a imagem atual
        enemy_sprite = self.animation_frames[self.current_frame]
        rect = enemy_sprite.get_rect(center=(self.x, self.y))
        screen.blit(enemy_sprite, rect.topleft)
        
        # DEBUG: Desenha o hitbox para depuração
        # pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.size, 1)

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.frames = 15
        self.colors = [(255, 165, 0), (255, 69, 0), (255, 0, 0)]  # Cores da explosão

    def update(self):
        self.frames -= 1
        return self.frames > 0

    def draw(self, screen):
        if self.frames > 0:
            color_idx = min(2, 15 - self.frames) // 5
            color = self.colors[color_idx]
            size = (15 - self.frames) * 3
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)

class Meteor:
    def __init__(self, start_pos, direction, speed=random.uniform(1, 10)):
        self.x, self.y = start_pos
        self.direction = direction
        self.speed = speed
        self.size = 40
        self.health = 4  # Aumentei a resistência do meteoro
        
        self.image = pygame.transform.scale(meteor_img1, (self.size, self.size))
        self.angle = random.randint(0, 360)
        self.rotation_speed = random.uniform(-2, 2)
        
    def update(self):
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed
        # Atualiza a rotação
        self.angle += self.rotation_speed
    
    def check_collision(self, x, y, radius):
        """
        Verifica colisão com projéteis ou outros objetos
        x, y: posição do objeto
        radius: raio do objeto para colisão
        """
        collision_radius = self.size // 2  # Usa metade do tamanho do meteoro
        distance = math.hypot(self.x - x, self.y - y)
        return distance < (collision_radius + radius)
    
    def is_out_of_bounds(self):
        margin = 100
        return (self.x < -margin or self.x > WIDTH + margin or 
                self.y < -margin or self.y > HEIGHT + margin)
    
    def draw(self, screen):
        # Rotaciona a imagem
        rotated_meteor = pygame.transform.rotate(self.image, self.angle)
        # Obtém o retângulo centralizado
        rect = rotated_meteor.get_rect(center=(int(self.x), int(self.y)))
        # Desenha o meteoro
        screen.blit(rotated_meteor, rect.topleft)

# =================== Loop Principal =================== #
async def main():
    global player, total_offset_x, total_offset_y, enemies, explosions, spawn_timer
    clock = pygame.time.Clock()
    going = True
    while going:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                going = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Pressione ESPAÇO para atirar
                    player.shoot()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                if event.key == pygame.K_r:
                    restart_game()
                    await main()
                    return
                
        # Verifica se o jogador ainda está vivo
        if player.health <= 0:
            await game_over_screen()
            return

        screen.fill((0, 0, 0))
        
                # Atualiza o jogador
        keys = pygame.key.get_pressed()
        player.update(keys)

        # Atualiza o deslocamento do plano de fundo
        total_offset_x += player.velocity_x
        total_offset_y += player.velocity_y

        # Desenha o plano de fundo repetidamente
        draw_background(total_offset_x, total_offset_y)

        
        
        # Lógica de spawn de inimigos
        if spawn_timer % enemy_spawn_rate == 0 and len(enemies) < max_enemies:
            while True:
                enemy_x = random.randint(0, WIDTH)
                enemy_y = random.randint(0, HEIGHT)
                if math.hypot(player.x - enemy_x, player.y - enemy_y) > SAFE_DISTANCE:
                    break

            # Spawn de inimigos que atiram aleatoriamente após o jogador atingir 100 pontos
            if player.score >= score_threshold and random.random() < 0.1:  # 30% de chance de spawnar um inimigo que atira
                enemies.append(ShooterEnemy(enemy_x, enemy_y, speed=1))
            else:
                enemies.append(Enemy(enemy_x, enemy_y))
        
        spawn_timer += 1

               # Atualiza e desenha inimigos
        for enemy in enemies[:]:
            enemy.move_towards_player(player.x, player.y)
        
            # Verifica colisão entre o jogador e o inimigo
            if player.check_collision_with_enemy(enemy):
                print("DEBUG: Jogador colidiu com um inimigo!")
                player.health -= 1  # Reduz a vida do jogador
                enemies.remove(enemy)  # Remove o inimigo após a colisão
                explosions.append(Explosion(enemy.x, enemy.y))  # Adiciona uma explosão
        
            if isinstance(enemy, ShooterEnemy):
                enemy.update_bullets(player)  # Atualiza os tiros do inimigo atirador
            enemy.draw(screen)
        
        
        # Lógica de spawn de meteoros
        global meteor_spawn_timer
        meteor_spawn_timer += 1
        
        if meteor_spawn_timer >= METEOR_SPAWN_RATE:
            meteor_spawn_timer = 0
            # Escolhe um lado aleatório da tela para spawnar
            side = random.choice(['top', 'right', 'bottom', 'left'])
            
            if side == 'top':
                x = random.randint(0, WIDTH)
                y = -50
                dir_y = random.uniform(0.5, 1)
                dir_x = random.uniform(-0.5, 0.5)
            elif side == 'right':
                x = WIDTH + 50
                y = random.randint(0, HEIGHT)
                dir_x = random.uniform(-1, -0.5)
                dir_y = random.uniform(-0.5, 0.5)
            elif side == 'bottom':
                x = random.randint(0, WIDTH)
                y = HEIGHT + 50
                dir_y = random.uniform(-1, -0.5)
                dir_x = random.uniform(-0.5, 0.5)
            else:  # left
                x = -50
                y = random.randint(0, HEIGHT)
                dir_x = random.uniform(0.5, 1)
                dir_y = random.uniform(-0.5, 0.5)
            
            # Normaliza o vetor direção
            length = math.sqrt(dir_x**2 + dir_y**2)
            dir_x /= length
            dir_y /= length
            
            meteors.append(Meteor((x, y), (dir_x, dir_y)))
        
        # Atualiza e verifica colisões dos meteoros
        for meteor in meteors[:]:
            meteor.update()
            
            # Colisão com o jogador
            if meteor.check_collision(player.x, player.y, player.width//3):
                player.health -= 2 # Reduz a vida do jogador em 2
                explosions.append(Explosion(meteor.x, meteor.y))
                meteors.remove(meteor)
                continue
            
            # Colisão com inimigos
            for enemy in enemies[:]:
                if meteor.check_collision(enemy.x, enemy.y, enemy.size):
                    enemies.remove(enemy)
                    explosions.append(Explosion(meteor.x, meteor.y))
                    meteors.remove(meteor)
                    break
            
            # Remove meteoros fora da tela
            if meteor.is_out_of_bounds():
                meteors.remove(meteor)
                continue
            
            meteor.draw(screen)
        
        # Atualiza e desenha explosões
        for explosion in explosions[:]:
            if not explosion.update():
                explosions.remove(explosion)  
            explosion.draw(screen)

        # Atualiza e desenha os tiros do jogador
        player.update_bullets(enemies, explosions)
        player.draw(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
