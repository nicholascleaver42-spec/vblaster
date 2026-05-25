import pygame
import sys
import random
import json

pygame.init()

# Constants
WIDTH, HEIGHT = 500, 600
FPS = 60

PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_SPEED = 8
PLAYER_Y = HEIGHT - 60

ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30
ENEMY_SPEED_BASE = 3
SPAWN_RATE_BASE = 60

BULLET_WIDTH = 6
BULLET_HEIGHT = 16
BULLET_SPEED_BASE = 12
FIRE_RATE_BASE = 100

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)        # 1-hit enemy
ORANGE = (255, 165, 0)   # 2-hit enemy
BLUE = (0, 100, 255)     # 3-hit enemy
YELLOW = (255, 255, 0)
PURPLE = (150, 33, 209)
LIGHTGREEN = (148, 255, 141) #4-hit
TURQOISE = (0, 153, 153)     #5-hit

# Set up display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Vertical Shooter - Enemy Types")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 48)
small_font = pygame.font.SysFont("Arial", 20)


def save_game(player_x, xp, level, xp_to_next, enemies, bullets, filename="savegame.json"):
    game_state = {
        "player_x": player_x,
        "xp": xp,
        "level": level,
        "xp_to_next": xp_to_next,
        "enemies": enemies,
        "bullets": bullets
    }
    try:
        with open(filename, "w") as f:
            json.dump(game_state, f)
    except:
        print("Failed to save")


def load_game(filename="savegame.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return None


def main():
    player_x = WIDTH // 2 - PLAYER_WIDTH // 2
    xp = 0
    level = 1
    xp_to_next = 100

    fire_rate = FIRE_RATE_BASE
    bullet_speed = BULLET_SPEED_BASE
    damage = 1

    chain_cooldown = 0
    CHAIN_BASE_COOLDOWN = 180          # frames between chain attacks (~1.5 sec)
    chain_length = 2                  # how many enemies one bolt hits
    extra_chains = 0                  # 0, 1, or 2 (max 2)
    chain_damage = 1                  # synced with normal damage

    stats = {
        "fire_rate": fire_rate,
        "bullet_speed": bullet_speed,
        "player_speed": PLAYER_SPEED,
        "damage": damage,
        "chain_length": chain_length,
        "extra_chains": extra_chains
    }

    game_over = False
    game_won = False
    paused = False
    leveling_up = False
    upgrade_options = []
    used_upgrades = set()

    enemies = []           # Now stored as [x, y, health]
    spawn_timer = 0
    enemy_speed = ENEMY_SPEED_BASE
    spawn_rate = SPAWN_RATE_BASE

    bullets = []
    fire_timer = 0

    chain_visuals = []        # Will store list of points for each chain
    visual_timer = 0

    

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if (game_over or game_won) and event.key == pygame.K_r:
                    return main()
                
                if event.key == pygame.K_p and not leveling_up:
                    paused = not paused
                
                # Level Up Choice
                if leveling_up:
                    if event.key == pygame.K_1:
                        apply_upgrade(upgrade_options[0], stats, used_upgrades)
                        leveling_up = False
                    elif event.key == pygame.K_2:
                        apply_upgrade(upgrade_options[1], stats, used_upgrades)
                        leveling_up = False
                    elif event.key == pygame.K_3:
                        apply_upgrade(upgrade_options[2], stats, used_upgrades)
                        leveling_up = False

                # Save / Load while paused
                if paused and not leveling_up:
                    if event.key == pygame.K_s:
                        save_game(player_x, xp, level, xp_to_next, enemies, bullets)
                    if event.key == pygame.K_l:
                        loaded = load_game()
                        if loaded:
                            player_x = loaded["player_x"]
                            xp = loaded["xp"]
                            level = loaded["level"]
                            xp_to_next = loaded.get("xp_to_next", 100)
                            enemies.clear()
                            enemies.extend(loaded.get("enemies", []))
                            bullets.clear()
                            bullets.extend(loaded.get("bullets", []))

    # ======================
    # GAME STATE CHECKS
    # ======================
        if game_over:
            screen.fill(BLACK)
            game_over_text = big_font.render("GAME OVER", True, RED)
            final_text = font.render(f"Final Level: {level} | XP: {xp}", True, WHITE)
            restart_text = font.render("Press R to Restart", True, WHITE)

            screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 80))
            screen.blit(final_text, (WIDTH//2 - final_text.get_width()//2, HEIGHT//2 - 10))
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 50))
            pygame.display.update()
            clock.tick(10)
            continue

        if game_won:
            screen.fill(BLACK)
            win_text = big_font.render("YOU WIN!", True, (0, 255, 100))
            level_text = font.render(f"Final Level: {level}", True, WHITE)
            thanks_text = font.render("Congratulations!", True, WHITE)
            restart_text = font.render("Press R to Play Again", True, WHITE)
            
            screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2 - 100))
            screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 - 30))
            screen.blit(thanks_text, (WIDTH//2 - thanks_text.get_width()//2, HEIGHT//2 + 10))
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 80))
            
            pygame.display.update()
            clock.tick(10)
            continue

        if paused:
            # Pause Screen code...
            screen.fill(BLACK)
            pygame.draw.rect(screen, GREEN, (player_x, PLAYER_Y, PLAYER_WIDTH, PLAYER_HEIGHT))
            for enemy in enemies:
                color = BLUE if len(enemy) > 2 and enemy[2] == 3 else ORANGE if len(enemy) > 2 and enemy[2] == 2 else RED
                pygame.draw.rect(screen, color, (enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT))
            for bullet in bullets:
                pygame.draw.rect(screen, YELLOW, (bullet[0], bullet[1], BULLET_WIDTH, BULLET_HEIGHT))

            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            pause_text = big_font.render("PAUSED", True, WHITE)
            instruction = font.render("P - Resume    S - Save    L - Load", True, WHITE)
            screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 60))
            screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 20))
            pygame.display.update()
            clock.tick(10)
            continue

        if leveling_up:
            draw_level_up_screen(upgrade_options, level)
            pygame.display.update()
            clock.tick(30)
            continue

    # ======================
    # NORMAL GAME LOGIC GOES HERE
    # ======================
    # (Player movement, auto shooting, enemy spawning, movement, collisions, etc.)

        # === PLAYER MOVEMENT ===
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player_x += PLAYER_SPEED

        if player_x < 0: player_x = 0
        if player_x > WIDTH - PLAYER_WIDTH: player_x = WIDTH - PLAYER_WIDTH

        # === AUTO SHOOTING ===
        fire_timer += 1
        if fire_timer >= stats['fire_rate']:
            fire_timer = 0
            bullet_x = player_x + PLAYER_WIDTH // 2 - BULLET_WIDTH // 2
            bullet_y = PLAYER_Y - BULLET_HEIGHT
            bullets.append([bullet_x, bullet_y])

        # === ENEMY SPAWNING ===
        spawn_timer += 1
        if spawn_timer >= spawn_rate:
            spawn_timer = 0
            enemy_x = random.randint(0, WIDTH - ENEMY_WIDTH)
            
            # Decide enemy type based on level
            if level >= 5 and random.random() < 0.35:
                health = 5
            elif level >= 4 and random.random() < 0.45:
                health = 4
            elif level >= 3 and random.random() < 0.55:          
                health = 3
            elif level >= 2 and random.random() < 0.65:         
                health = 2
            else:
                health = 1
                
            enemies.append([enemy_x, -ENEMY_HEIGHT, health])

        # === ENEMY MOVEMENT ===
        for enemy in enemies[:]:
            enemy[1] += enemy_speed
            if enemy[1] > HEIGHT:
                enemies.remove(enemy)

        # === BULLET MOVEMENT ===
        for bullet in bullets[:]:
            bullet[1] -= bullet_speed
            if bullet[1] < -BULLET_HEIGHT:
                bullets.remove(bullet)

        # === CHAIN LIGHTNING ===
        chain_cooldown += 1
        if chain_cooldown >= CHAIN_BASE_COOLDOWN:
            chain_cooldown = 0
            xp_from_chain = fire_chain_lightning(
                enemies, 
                stats['damage'], 
                stats['chain_length'], 
                stats['extra_chains'], 
                player_x, 
                PLAYER_Y, 
                chain_visuals
            )
            xp += xp_from_chain
            
            
        # === COLLISIONS ===
        for bullet in bullets[:]:
            bullet_rect = pygame.Rect(bullet[0], bullet[1], BULLET_WIDTH, BULLET_HEIGHT)
            for enemy in enemies[:]:
                enemy_rect = pygame.Rect(enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT)
                if bullet_rect.colliderect(enemy_rect):
                    bullets.remove(bullet)
                    enemy[2] -= stats['damage']                    # Reduce health
                    
                    if enemy[2] <= 0:
                        enemies.remove(enemy)
                        xp += 10
                    # If health > 0, enemy stays but changes color (handled in drawing)
                    break

        # Enemy vs Player
        player_rect = pygame.Rect(player_x, PLAYER_Y, PLAYER_WIDTH, PLAYER_HEIGHT)
        for enemy in enemies[:]:
            enemy_rect = pygame.Rect(enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT)
            if player_rect.colliderect(enemy_rect):
                game_over = True
                break

        # === LEVEL UP LOGIC ===
        if xp >= xp_to_next:
            xp = 0
            level += 1
            xp_to_next = int(xp_to_next * 1.1)
            upgrade_options = get_upgrade_options(used_upgrades)
            leveling_up = True

            # WIN CONDITION
            if level >= 10:
                game_won = True
                leveling_up = False

            spawn_rate = max(15, spawn_rate - 5)

            enemy_speed = min(7.5, enemy_speed + 0.5)

        # === DRAWING ===
        screen.fill(BLACK)

        pygame.draw.rect(screen, GREEN, (player_x, PLAYER_Y, PLAYER_WIDTH, PLAYER_HEIGHT))

        # Draw Enemies with color based on health
        for enemy in enemies:
            if enemy[2] == 5:
                color = TURQOISE
            elif enemy[2] == 4:
                color = LIGHTGREEN
            elif enemy[2] == 3:
                color = BLUE
            elif enemy[2] == 2:
                color = ORANGE
            else:
                color = RED
            pygame.draw.rect(screen, color, (enemy[0], enemy[1], ENEMY_WIDTH, ENEMY_HEIGHT))

        for bullet in bullets:
            pygame.draw.rect(screen, YELLOW, (bullet[0], bullet[1], BULLET_WIDTH, BULLET_HEIGHT))

        ui_text = font.render(f"Level: {level}   XP: {xp}/{xp_to_next}", True, WHITE)
        screen.blit(ui_text, (10, 10))

        # === DRAW CHAIN LIGHTNING VISUALS ===
        for chain in chain_visuals[:]:
            if len(chain) >= 2:
                # Draw glowing line
                pygame.draw.lines(screen, PURPLE, False, chain, width=5)
                pygame.draw.lines(screen, (200, 200, 255), False, chain, width=2)  # Highlight
                
            # Remove old visuals after a few frames
            visual_timer += 1
            if visual_timer > 8:          # Show for ~8 frames
                chain_visuals.remove(chain)
                visual_timer = 0

        pygame.display.update()
        clock.tick(FPS)


def get_upgrade_options(used_upgrades):
    """Return 3 upgrade choices, respecting limits"""
    all_upgrades = [
        ("Faster Shooting", "fire_rate", -40),
        ("More Damage", "damage", 1),
        ("Longer Chain", "chain_length", 1),
        ("Extra Chain Bolt", "extra_chains", 1),
    ]
    
    # Filter out upgrades that have already been used (if limited)
    available = []
    for upgrade in all_upgrades:
        name, stat, value = upgrade
        if stat in ["chain_length", "extra_chains"]:
            if stat in used_upgrades:
                continue  # Don't offer this upgrade again
        available.append(upgrade)
    
    # If we have less than 3 available, fill with normal upgrades
    if len(available) < 3:
        available.extend(all_upgrades[:3])  # fallback
    
    return random.sample(available, 3)


def apply_upgrade(upgrade, stats, used_upgrades):
    """Apply the chosen upgrade"""
    name, stat, value = upgrade
    print(f"Upgrade Applied: {name}")
    
    if stat == "fire_rate":
        stats['fire_rate'] = max(5, stats['fire_rate'] + value)
    elif stat == "damage":
        stats['damage'] += value
    elif stat == 'chain_length':
        stats['chain_length'] +=  min(1, stats['chain_length'] + value)
        used_upgrades.add("chain_length")
    elif stat == 'extra_chains':
        stats['extra_chains'] += min(1, stats['extra_chains'] + value)
        used_upgrades.add("extra_chains")
        # More upgrades can be added here later

def fire_chain_lightning(enemies, damage, chain_length, extra_chains, player_x, player_y, chain_visuals):
    if not enemies:
        return 0
    
    xp_gained = 0
    all_chains = []
    
    for _ in range(1 + extra_chains):           # Main chain + extra chains
        if len(enemies) == 0:
            break
            
        chain_path = [(player_x + PLAYER_WIDTH//2, PLAYER_Y)]
        hits_remaining = chain_length
        used_in_this_chain = []
        
        # Get all valid targets
        available = [e for e in enemies if e[2] > 0]
        
        if not available:
            break
            
        current = random.choice(available)
        
        while hits_remaining > 0 and available:
            chain_path.append((current[0] + ENEMY_WIDTH//2, current[1] + ENEMY_HEIGHT//2))
            
            current[2] -= damage
            hits_remaining -= 1
            used_in_this_chain.append(current)
            
            if current[2] <= 0:
                if current in enemies:
                    enemies.remove(current)
                    xp_gained += 10
            
            # === AGGRESSIVE TARGETING ===
            # Rebuild available list, excluding already hit in this chain
            available = [e for e in enemies if e not in used_in_this_chain and e[2] > 0]
            
            if available:
                # Bias toward enemies with lower health for more kills
                available.sort(key=lambda e: e[2])
                current = available[0]          # Pick weakest enemy
            else:
                break
        
        # Only add chain if it actually hit something
        if len(chain_path) > 1:
            all_chains.append(chain_path)
    
    chain_visuals.extend(all_chains)
    return xp_gained


def draw_level_up_screen(options, level):
    screen.fill(BLACK)
    
    title = big_font.render(f"LEVEL {level} UP!", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))
    
    prompt = font.render("Choose your upgrade:", True, WHITE)
    screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, 130))

    for i, (name, _, _) in enumerate(options):
        text = small_font.render(f"{i+1}. {name}", True, WHITE)
        screen.blit(text, (WIDTH//2 - 120, 190 + i*50))

    controls = font.render("Press 1, 2, or 3 to choose", True, (200, 200, 200))
    screen.blit(controls, (WIDTH//2 - controls.get_width()//2, 340))


if __name__ == "__main__":
    main()