import pygame
import random
import sys
import json

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 400
FPS = 60

BULLET_WIDTH = 6
BULLET_HEIGHT = 16
BULLET_SPEED = 12
FIRE_RATE = 15

ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30
ENEMY_SPEED = 3
SPAWN_RATE = 60

PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_SPEED = 8
PLAYER_Y = HEIGHT - 60  # Fixed position near bottom

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vertical Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 48)

def save_game(player_x, score, enemies, bullets, filename="savegame.json"):
    game_state = {
        "player_x": player_x,
        "score": score,
        "enemies": enemies,
        "bullets": bullets
    }
    try:
        with open(filename, "w") as f:
            json.dump(game_state, f)
        print("Game saved!")
    except:
        print("Failed to save game")


def load_game(filename="savegame.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        print("No save file found or failed to load")
        return None


def main():
    # Player setup
    player_x = WIDTH // 2 - PLAYER_WIDTH // 2
    score = 0
    game_over = False
    paused = False

    #Enemy setup
    enemies = []
    spawn_timer = 0

    #Bullet setup
    bullets = []
    fire_timer = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if game_over and event.key == pygame.K_r:
                    return main()  # Restart the game
                
                if event.key == pygame.K_p:
                    paused = not paused

                if paused:
                    if event.key == pygame.K_s:        # Press S to Save
                        save_game(player_x, score, enemies, bullets)
                    if event.key == pygame.K_l:        # Press L to Load
                        loaded = load_game()
                        if loaded:
                            player_x = loaded["player_x"]
                            score = loaded["score"]
                            enemies.clear()
                            enemies.extend(loaded["enemies"])
                            bullets.clear()
                            bullets.extend(loaded["bullets"])

        if game_over:
            # Game Over Screen
            screen.fill(BLACK)
            game_over_text = big_font.render("GAME OVER", True, RED)
            score_text = font.render(f"Final Score: {score}", True, WHITE)
            restart_text = font.render("Press R to Restart", True, WHITE)
            
            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 80))
            screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 10))
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))
            pygame.display.update()
            clock.tick(10)
            continue

        if paused:
            # First, draw the current game state (frozen)
            screen.fill(BLACK)

            # Draw Player
            pygame.draw.rect(screen, GREEN, (player_x, PLAYER_Y, PLAYER_WIDTH, PLAYER_HEIGHT))

            # Draw Enemies
            for enemy in enemies:
                pygame.draw.rect(screen, RED, (enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT))

            # Draw Bullets
            for bullet in bullets:
                pygame.draw.rect(screen, YELLOW, (bullet[0], bullet[1], BULLET_WIDTH, BULLET_HEIGHT))

            # Draw Score
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))

            # === Semi-transparent overlay ===
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)                    # 0 = fully transparent, 255 = solid
            overlay.fill((0, 0, 0))                   # Black overlay
            screen.blit(overlay, (0, 0))

            # === Pause Text ===
            pause_text = big_font.render("PAUSED", True, WHITE)
            instruction = font.render("P - Resume    S - Save    L - Load", True, WHITE)
            
            screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 60))
            screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 20))

            pygame.display.update()
            clock.tick(10)
            continue
        
        # === PLAYER MOVEMENT ===
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_x += PLAYER_SPEED

        # Keep player within screen bounds
        if player_x < 0:
            player_x = 0
        if player_x > WIDTH - PLAYER_WIDTH:
            player_x = WIDTH - PLAYER_WIDTH

        #AUTO SHOOTING
        fire_timer += 1
        if fire_timer >= FIRE_RATE:
            fire_timer = 0
            #create bullet at center of player
            bullet_x = player_x + PLAYER_WIDTH // 2 - BULLET_WIDTH // 2
            bullet_y = PLAYER_Y - BULLET_HEIGHT
            bullets.append([bullet_x, bullet_y])
        
        #Enemy spawning
        spawn_timer += 1
        if spawn_timer >= SPAWN_RATE:
            spawn_timer = 0
            enemy_x = random.randint(0, WIDTH - ENEMY_WIDTH)
            enemies.append([enemy_x, -ENEMY_HEIGHT])

        #Enemy movement
        for enemy in enemies[:]:
            enemy[1] += ENEMY_SPEED

            #Remove enemy if it goes off the bottom
            if enemy[1] > HEIGHT:
                enemies.remove(enemy)
        
        #BULLET MOVEMENT
        for bullet in bullets[:]:
            bullet[1] -= BULLET_SPEED
            if bullet[1] < -BULLET_HEIGHT:
                bullets.remove(bullet)

            #COLLISIONS
            #bullet v. enemy
            for bullet in bullets[:]:
                bullet_rect = pygame.Rect(bullet[0], bullet[1], BULLET_WIDTH, BULLET_HEIGHT)

                for enemy in enemies[:]:
                    enemy_rect = pygame.Rect(enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT)

                    if bullet_rect.colliderect(enemy_rect):
                        #hit! remove both bullet and enemy
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if enemy in enemies:
                            enemies.remove(enemy) # type: ignore
                        score += 10
                        break
            #enemy v player
            player_rect = pygame.Rect(player_x, PLAYER_Y, PLAYER_WIDTH, PLAYER_HEIGHT)

            for enemy in enemies[:]:
                enemy_rect = pygame.Rect(enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT)

                if player_rect.colliderect(enemy_rect):
                    game_over = True
                    break

        # === DRAWING ===
        screen.fill(BLACK)

        # Draw Player
        pygame.draw.rect(screen, GREEN, 
                        (player_x, PLAYER_Y, PLAYER_WIDTH, PLAYER_HEIGHT))
        
        #Draw Enemies
        for enemy in enemies:
            pygame.draw.rect(screen, RED,
                             (enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT))
            
        #Draw bullets
        for bullet in bullets:
            pygame.draw.rect(screen, YELLOW,
                             (bullet[0], bullet[1], BULLET_WIDTH, BULLET_HEIGHT))

        # Draw Score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()