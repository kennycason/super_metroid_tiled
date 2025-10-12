#!/usr/bin/env python3
"""
Super Metroid Memory Battle Game
A tile-flipping memory game with boss battles and item collection
"""

import pygame
import random
import sys
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000  # Reduced width
SCREEN_HEIGHT = 750  # Reduced height
GRID_SIZE = 10
TILE_SIZE = 64
GRID_START_X = 20  # Moved left
GRID_START_Y = 90  # Moved down 10 pixels
INVENTORY_HEIGHT = 100  # Increased for two rows
INVENTORY_Y = 10  # Moved up
HUD_WIDTH = 300  # Width for right-side combat info
COMBAT_INFO_X = GRID_START_X + (GRID_SIZE * TILE_SIZE) + 20  # Right of grid with 10px spacing
BOSS_HUD_WIDTH = 200  # Width for boss tracker
BOSS_HUD_X = SCREEN_WIDTH - BOSS_HUD_WIDTH - 20  # Top right corner

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
DARKER_GRAY = (51, 51, 51)  # #333 for Log panel background
# Super Metroid themed colors (darker, more authentic)
CRATERIA_LIGHT_BLUE = (100, 150, 200)  # Light blue for Crateria
BRINSTAR_GREEN = (0, 120, 0)      # Darker green for Brinstar
NORFAIR_RED = (180, 40, 40)       # Darker red for Norfair  
MARIDIA_BLUE = (40, 40, 140)      # Darker blue for Maridia
TOURIAN_YELLOW = (160, 140, 0)    # Darker yellow for Tourian
WRECKED_SHIP_PURPLE = (80, 0, 80) # Darker purple for Wrecked Ship
CERES_GRAY = (100, 100, 100)      # Darker gray for Ceres

class TileType(Enum):
    """Types of tiles in the game"""
    EMPTY = "empty"
    ITEM = "item"
    BOSS = "boss"
    ENEMY = "enemy"

class AreaType(Enum):
    """Map areas like Super Metroid"""
    CRATERIA = "crateria"  # Light Blue - Samus Ship (starting area)
    BRINSTAR = "brinstar"  # Green - Kraid, Spore Spawn
    NORFAIR = "norfair"    # Red - Ridley, Crocomire
    MARIDIA = "maridia"    # Blue - Draygon, Botwoon
    TOURIAN = "tourian"    # Yellow/Orange - Mother Brain
    WRECKED_SHIP = "wrecked_ship"  # Purple - Phantoon
    CERES = "ceres"        # Gray - Ceres Station

class TileState(Enum):
    """State of a tile"""
    FACE_DOWN = "face_down"
    FACE_UP = "face_up"
    DESTROYED = "destroyed"

class GameState(Enum):
    """Overall game state"""
    PLAYING = "playing"
    GAME_OVER = "game_over"

def get_display_name(entity_id: str) -> str:
    """Get a nice display name for enemies, bosses, and items (standalone function)"""
    display_names = {
        # Bosses
        "mother_brain_1": "Mother Brain",
        "mother_brain_2": "Mother Brain Phase 2",
        "ridley": "Ridley",
        "kraid": "Kraid",
        "phantoon": "Phantoon",
        "draygon": "Draygon",
        "bomb_torizo": "Bomb Torizo",
        "gold_torizo": "Gold Torizo",
        "spore_spawn": "Spore Spawn",
        "crocomire": "Crocomire",
        "botwoon": "Botwoon",
        "ceres_station": "Ceres Station",
        "samus_ship": "Samus' Ship",
        "golden_four": "Golden Four",
        # Enemies
        "geemer": "Geemer",
        "skree": "Skree",
        "side_hopper": "Side Hopper",
        "ciser": "Ciser",
        # Items - Consumables
        "missiles": "Missiles",
        "supers": "Super Missiles",
        "power_bombs": "Power Bombs",
        "energy_tank": "Energy Tank",
        # Items - Movement
        "morph": "Morph Ball",
        "bomb": "Bombs",
        "hijump": "High Jump Boots",
        "speed": "Speed Booster",
        "spring": "Spring Ball",
        "space": "Space Jump",
        "screw": "Screw Attack",
        # Items - Beams
        "charge": "Charge Beam",
        "spazer": "Spazer Beam",
        "wave": "Wave Beam",
        "ice": "Ice Beam",
        "plasma": "Plasma Beam",
        # Items - Utility
        "grapple": "Grapple Beam",
        "xray": "X-ray Scope",
        # Items - Suits
        "varia": "Varia Suit",
        "gravity": "Gravity Suit"
    }
    return display_names.get(entity_id, entity_id.replace("_", " ").title())

class Tile:
    """Represents a single tile on the grid"""
    def __init__(self, x: int, y: int, tile_type: TileType, item_id: str = "", area: AreaType = None):
        self.x = x
        self.y = y
        self.tile_type = tile_type
        self.item_id = item_id
        self.area = area
        self.state = TileState.FACE_DOWN
        self.health = 0  # For bosses
        self.max_health = 0  # For bosses
        self.frozen = False  # For ice beam freeze effect
        
    def get_screen_position(self) -> Tuple[int, int]:
        """Get the screen position of this tile"""
        screen_x = GRID_START_X + self.x * TILE_SIZE
        screen_y = GRID_START_Y + self.y * TILE_SIZE
        return (screen_x, screen_y)

class Game:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Metroid Memory Battle")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.PLAYING
        self.game_over = False
        self.victory = False
        
        # Game grid
        self.grid: List[List[Tile]] = []
        self.inventory: Dict[str, int] = {}
        self.revealed_tiles: List[Tuple[int, int]] = []  # Track revealed positions
        
        # Combat system
        self.player_energy = 99  # Starting energy
        self.max_energy = 99
        self.combat_log: List[str] = []
        self.boss_turn_timer = 0
        self.boss_turn_interval = 60  # Frames between boss attacks (1 second at 60fps)
        self.player_attack_timer = 0
        self.player_attack_interval = 30  # Player attacks every 0.5 seconds
        self.game_over = False
        
        # Scoring system
        self.score = 0
        self.boss_defeats = {}  # Track boss defeats
        
        # Initialize sprite system
        self.sprite_manager = SpriteManager()
        
        # Initialize game
        self.initialize_game()
        
    def initialize_game(self):
        """Initialize the game grid and inventory"""
        # Create empty grid
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Initialize inventory - consumables have counts, others are boolean
        self.inventory = {
            "missiles": 0,      # Consumable
            "supers": 0,        # Consumable  
            "power_bombs": 0,   # Consumable
            "energy_tank": 0,   # Consumable
            "morph": False,     # Unique item
            "bomb": False,      # Unique item
            "hijump": False,    # Unique item
            "speed": False,     # Unique item
            "grapple": False,   # Unique item
            "xray": False,      # Unique item
            "spring": False,    # Unique item
            "space": False,     # Unique item
            "screw": False,     # Unique item
            "charge": False,    # Unique item (beam)
            "spazer": False,    # Unique item (beam)
            "wave": False,      # Unique item (beam)
            "ice": False,       # Unique item (beam)
            "plasma": False,    # Unique item (beam)
            "varia": False,     # Unique item (suit)
            "gravity": False,   # Unique item (suit)
        }
        
        # Initialize boss defeats tracking (no ship or golden_four)
        boss_list = [
            "bomb_torizo", "spore_spawn", "kraid", "crocomire",
            "phantoon", "botwoon", "draygon", "gold_torizo",
            "ridley", "mother_brain_1", "ceres_station"
        ]
        self.boss_defeats = {boss: 0 for boss in boss_list}
        
        # Populate grid with random tiles
        self.populate_grid()
        
    def populate_grid(self):
        """Fill the grid with themed areas like Super Metroid"""
        # Define themed areas with their bosses and items
        areas = {
            AreaType.CRATERIA: {
                "bosses": ["samus_ship", "bomb_torizo"],
                "unique_items": [],  # No unique items in Crateria
                "consumables": ["missiles", "supers", "power_bombs", "energy_tank"],
                "enemies": ["geemer", "skree"],
                "color": CRATERIA_LIGHT_BLUE
            },
            AreaType.BRINSTAR: {
                "bosses": ["kraid", "spore_spawn"],
                "unique_items": ["morph", "bomb", "charge", "varia", "spazer", "xray"],
                "consumables": ["missiles", "supers", "power_bombs", "energy_tank"],
                "enemies": ["geemer", "skree", "side_hopper"],
                "color": BRINSTAR_GREEN
            },
            AreaType.NORFAIR: {
                "bosses": ["ridley", "crocomire"],
                "unique_items": ["hijump", "speed", "ice", "screw", "wave", "grapple"],
                "consumables": ["missiles", "supers", "power_bombs", "energy_tank"],
                "enemies": ["skree", "side_hopper", "ciser"],
                "color": NORFAIR_RED
            },
            AreaType.MARIDIA: {
                "bosses": ["draygon", "botwoon"],
                "unique_items": ["spring", "space", "plasma"],
                "consumables": ["missiles", "supers", "power_bombs", "energy_tank"],
                "enemies": ["geemer", "ciser"],
                "color": MARIDIA_BLUE
            },
            AreaType.TOURIAN: {
                "bosses": ["mother_brain_1"],  # Only Mother Brain 1 appears in game
                "unique_items": [],
                "consumables": ["missiles", "supers", "power_bombs", "energy_tank"],
                "enemies": ["side_hopper", "ciser"],
                "color": TOURIAN_YELLOW
            },
            AreaType.WRECKED_SHIP: {
                "bosses": ["phantoon"],
                "unique_items": ["gravity"],  # Gravity Suit found in Wrecked Ship
                "consumables": ["missiles", "supers", "power_bombs", "energy_tank"],
                "enemies": ["geemer", "skree"],
                "color": WRECKED_SHIP_PURPLE
            },
            AreaType.CERES: {
                "bosses": ["ceres_station"],
                "unique_items": [],
                "consumables": ["missiles", "supers", "power_bombs", "energy_tank"],
                "enemies": ["skree", "side_hopper"],
                "color": CERES_GRAY
            }
        }
        
        # Boss health values (increased for better balance)
        boss_health = {
            "bomb_torizo": 800,
            "spore_spawn": 1200,
            "kraid": 3000,
            "crocomire": 2000,
            "phantoon": 3500,
            "botwoon": 2500,
            "draygon": 4000,
            "gold_torizo": 3000,
            "ridley": 6000,
            "mother_brain_1": 8000,
            "mother_brain_2": 4000,
            "samus_ship": 0,  # Ship has no health - it's the starting point
            "ceres_station": 1000,
            "golden_four": 6000
        }
        
        # Enemy health values (minor enemies)
        enemy_health = {
            "geemer": 50,
            "skree": 75,
            "side_hopper": 100,
            "ciser": 125
        }
        
        # Enemy damage values (minor enemies)
        self.enemy_damage = {
            "geemer": 3,
            "skree": 4,
            "side_hopper": 5,
            "ciser": 6
        }
        
        # Create area map (hidden from player)
        self.area_map = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        
        # Step 1: Define all area types that MUST be placed
        all_area_types = list(areas.keys())
        
        # Step 2: Place each area type with guaranteed minimum size and connectivity
        for area_type in all_area_types:
            # Find a suitable starting position
            attempts = 0
            while attempts < 50:  # Prevent infinite loops
                if area_type == AreaType.CRATERIA:
                    # Crateria should start near top-left (ship location)
                    start_x, start_y = random.randint(0, 3), random.randint(0, 3)
                elif area_type == AreaType.TOURIAN:
                    # Tourian should be in a corner (Mother Brain's lair)
                    corner = random.choice([(0, 0), (9, 0), (0, 9), (9, 9)])
                    start_x, start_y = corner
                elif area_type == AreaType.WRECKED_SHIP:
                    # Wrecked ship should be smaller and isolated
                    start_x, start_y = random.randint(1, 8), random.randint(1, 8)
                else:
                    # Other areas can be anywhere
                    start_x, start_y = random.randint(1, 8), random.randint(1, 8)
                
                # Check if this position is available
                if self.area_map[start_y][start_x] is None:
                    break
                attempts += 1
            
            # If we couldn't find a spot, pick the first available None
            if attempts >= 50:
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if self.area_map[y][x] is None:
                            start_x, start_y = x, y
                            break
                    else:
                        continue
                    break
            
            # Determine area size based on type
            if area_type == AreaType.WRECKED_SHIP:
                area_size = random.randint(15, 25)  # Larger area to fit boss + gravity suit + items
            elif area_type == AreaType.CERES:
                area_size = random.randint(10, 18)  # Medium area (increased minimum for Ceres Station)
            else:
                area_size = random.randint(12, 25)  # Larger areas
            
            # Create the connected area
            self.flood_fill_area(start_x, start_y, area_type, area_size)
        
        # Step 3: Fill any remaining None areas with Crateria (default)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.area_map[y][x] is None:
                    self.area_map[y][x] = AreaType.CRATERIA
        
        # Step 4: Place bosses within their appropriate areas
        self.boss_placements = {}
        for area_type, area_data in areas.items():
            for boss_id in area_data["bosses"]:
                # Find suitable position within the area
                suitable_positions = []
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if self.area_map[y][x] == area_type:
                            # Check minimum distance from other bosses (except ship)
                            too_close = False
                            if boss_id != "samus_ship":
                                for (bx, by), _ in self.boss_placements.items():
                                    if abs(x - bx) + abs(y - by) < 3:
                                        too_close = True
                                        break
                            
                            if not too_close:
                                suitable_positions.append((x, y))
                
                # Place boss if suitable position found
                if suitable_positions:
                    x, y = random.choice(suitable_positions)
                    self.boss_placements[(x, y)] = (boss_id, area_type)
                else:
                    # If no suitable position found, place anyway (relaxed placement for small areas)
                    fallback_positions = []
                    for y in range(GRID_SIZE):
                        for x in range(GRID_SIZE):
                            if self.area_map[y][x] == area_type:
                                fallback_positions.append((x, y))
                    
                    if fallback_positions:
                        x, y = random.choice(fallback_positions)
                        self.boss_placements[(x, y)] = (boss_id, area_type)
                        print(f"Warning: {get_display_name(boss_id)} placed in small area without distance check")
                    else:
                        print(f"ERROR: Could not place {get_display_name(boss_id)} - no tiles in {area_type}")
        
        # Step 5: Place unique items, consumables, and enemies in correct areas
        self.place_items_in_areas(areas, boss_health, enemy_health)
        
    def flood_fill_area(self, start_x: int, start_y: int, area_type: AreaType, max_tiles: int):
        """Flood fill to create connected area with better connectivity"""
        if self.area_map[start_y][start_x] is not None:
            return
            
        # Use a more sophisticated flood fill that prioritizes connectivity
        stack = [(start_x, start_y)]
        placed = 0
        visited = set()
        
        while stack and placed < max_tiles:
            x, y = stack.pop(0)
            
            # Skip if already visited or out of bounds
            if (x, y) in visited or not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
                continue
                
            # Skip if already assigned
            if self.area_map[y][x] is not None:
                continue
                
            self.area_map[y][x] = area_type
            placed += 1
            visited.add((x, y))
            
            # Add neighbors with priority: cardinals first, then diagonals
            # This ensures better connectivity
            neighbors = [
                (x, y-1), (x, y+1), (x-1, y), (x+1, y),  # Cardinals first
                (x-1, y-1), (x+1, y-1), (x-1, y+1), (x+1, y+1)  # Diagonals second
            ]
            
            for nx, ny in neighbors:
                if ((nx, ny) not in visited and 
                    0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 
                    self.area_map[ny][nx] is None):
                    stack.append((nx, ny))
                    
    def find_nearest_area(self, x: int, y: int) -> AreaType:
        """Find the nearest area type"""
        min_dist = float('inf')
        nearest = None
        
        for ay in range(GRID_SIZE):
            for ax in range(GRID_SIZE):
                if self.area_map[ay][ax] is not None:
                    dist = abs(x - ax) + abs(y - ay)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = self.area_map[ay][ax]
                        
        return nearest
        
    def place_items_in_areas(self, areas: dict, boss_health: dict, enemy_health: dict):
        """Place items, bosses, and enemies in their correct areas"""
        # First place bosses
        for (x, y), (boss_id, area_type) in self.boss_placements.items():
            if boss_id == "samus_ship":
                tile = Tile(x, y, TileType.BOSS, boss_id, area_type)
                tile.state = TileState.FACE_UP
                tile.health = 0
                tile.max_health = 0
                self.revealed_tiles.append((x, y))
                self.log_combat("You've arrived at Zebes.")
                self.log_combat("destroy Mother Brain to save Samus.")
            else:
                tile = Tile(x, y, TileType.BOSS, boss_id, area_type)
                tile.health = boss_health[boss_id]
                tile.max_health = boss_health[boss_id]
            self.grid[y][x] = tile
            
        # Then place unique items (one per area)
        for area_type, area_data in areas.items():
            unique_items = area_data["unique_items"].copy()
            random.shuffle(unique_items)
            
            area_tiles = []
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.area_map[y][x] == area_type and self.grid[y][x] is None:
                        area_tiles.append((x, y))
            
            # Place one of each unique item
            for i, item_id in enumerate(unique_items):
                if i < len(area_tiles):
                    x, y = area_tiles[i]
                    tile = Tile(x, y, TileType.ITEM, item_id, area_type)
                    self.grid[y][x] = tile
                    
        # Fill remaining tiles with consumables, enemies, or empty
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] is None:
                    area_type = self.area_map[y][x]
                    area_data = areas[area_type]
                    
                    rand = random.random()
                    if rand < 0.20:  # 20% chance for consumable
                        item_id = random.choice(area_data["consumables"])
                        tile = Tile(x, y, TileType.ITEM, item_id, area_type)
                    elif rand < 0.40:  # 20% chance for enemy
                        enemy_id = random.choice(area_data["enemies"])
                        tile = Tile(x, y, TileType.ENEMY, enemy_id, area_type)
                        tile.health = enemy_health[enemy_id]
                        tile.max_health = enemy_health[enemy_id]
                    else:  # 60% empty
                        tile = Tile(x, y, TileType.EMPTY, "", area_type)
                    
                    self.grid[y][x] = tile
                
                    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)
                    
    def reset_game(self):
        """Reset the game to initial state - complete new game"""
        # Reset game state
        self.game_over = False
        self.victory = False
        self.score = 0
        
        # Reset player stats
        self.player_energy = 99
        self.max_energy = 99
        
        # Clear combat log
        self.combat_log = []
        
        # Reset boss defeats
        boss_list = [
            "bomb_torizo", "spore_spawn", "kraid", "crocomire",
            "phantoon", "botwoon", "draygon", "gold_torizo",
            "ridley", "mother_brain_1", "ceres_station"
        ]
        self.boss_defeats = {boss: 0 for boss in boss_list}
        
        # Reset inventory
        self.inventory = {
            "missiles": 0,      # Consumable
            "supers": 0,        # Consumable  
            "power_bombs": 0,   # Consumable
            "energy_tank": 0,   # Consumable
            "morph": False,     # Unique item
            "bomb": False,      # Unique item
            "hijump": False,    # Unique item
            "speed": False,     # Unique item
            "grapple": False,   # Unique item
            "xray": False,      # Unique item
            "spring": False,    # Unique item
            "space": False,     # Unique item
            "screw": False,     # Unique item
            "charge": False,    # Unique item (beam)
            "spazer": False,    # Unique item (beam)
            "wave": False,      # Unique item (beam)
            "ice": False,       # Unique item (beam)
            "plasma": False,    # Unique item (beam)
            "varia": False,     # Unique item (suit)
            "gravity": False,   # Unique item (suit)
        }
        
        # Clear revealed tiles
        self.revealed_tiles = []
        
        # Reset combat timers
        self.boss_turn_timer = 0
        self.player_attack_timer = 0
        
        # Regenerate the ENTIRE grid with new random layout
        self.initialize_game()
        
        # Log reset message
        self.log_combat("New game started! Press R to reset again.")
                    
    def is_fight_active(self) -> bool:
        """Check if any boss or enemy is currently active (face-up and alive)"""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = self.grid[y][x]
                if ((tile.tile_type == TileType.BOSS or tile.tile_type == TileType.ENEMY) and 
                    tile.state == TileState.FACE_UP and 
                    tile.health > 0):
                    return True
        return False
                    
    def handle_click(self, pos: Tuple[int, int]):
        """Handle mouse click on grid"""
        # Don't allow clicking during fights
        if self.is_fight_active():
            return
            
        x, y = pos
        
        # Check if click is within grid bounds
        if (GRID_START_X <= x < GRID_START_X + GRID_SIZE * TILE_SIZE and
            GRID_START_Y <= y < GRID_START_Y + GRID_SIZE * TILE_SIZE):
            
            # Convert to grid coordinates
            grid_x = (x - GRID_START_X) // TILE_SIZE
            grid_y = (y - GRID_START_Y) // TILE_SIZE
            
            tile = self.grid[grid_y][grid_x]
            
            # Check if tile can be clicked (adjacent to revealed tiles or first tile)
            if tile.state == TileState.FACE_DOWN and self.can_click_tile(grid_x, grid_y):
                # Check for Maridia movement restriction BEFORE processing tile
                if tile.area == AreaType.MARIDIA and not self.inventory.get("gravity", False):
                    self.log_combat("Cannot enter Maridia without Gravity Suit!")
                    return  # Exit early, don't process the tile
                
                tile.state = TileState.FACE_UP
                self.revealed_tiles.append((grid_x, grid_y))
                
                # Handle item collection
                if tile.tile_type == TileType.ITEM:
                    display_name = self.get_display_name(tile.item_id)
                    # Check if item already collected (for unique items)
                    if isinstance(self.inventory[tile.item_id], bool):
                        if self.inventory[tile.item_id]:
                            self.log_combat(f"Already have {display_name}!")
                            return
                        else:
                            self.inventory[tile.item_id] = True
                            self.log_combat(f"Collected {display_name}!")
                    else:
                        # Consumable item
                        self.inventory[tile.item_id] += 1
                        self.log_combat(f"Collected {display_name}! Total: {self.inventory[tile.item_id]}")
                    
                    # Add score for item collection
                    item_scores = {
                        "missiles": 10, "supers": 20, "power_bombs": 30, "energy_tank": 50,
                        "morph": 100, "bomb": 100, "hijump": 150, "speed": 150,
                        "grapple": 200, "xray": 200, "spring": 150, "space": 200,
                        "screw": 250, "charge": 150, "spazer": 200, "wave": 200,
                        "ice": 200, "plasma": 250, "varia": 300, "gravity": 400
                    }
                    self.score += item_scores.get(tile.item_id, 10)
                    
                    # Energy tanks increase max energy and heal fully
                    if tile.item_id == "energy_tank":
                        self.max_energy += 100  # Permanently increase max energy
                        self.player_energy = self.max_energy  # Fully heal
                        self.log_combat(f"Energy tank collected! Max energy: {self.max_energy}")
                    
                    # X-ray scope auto-grabs adjacent tiles if they are items
                    if self.inventory.get("xray", False):
                        self.auto_grab_adjacent_items(grid_x, grid_y)
                    
                elif tile.tile_type == TileType.BOSS:
                    display_name = self.get_display_name(tile.item_id)
                    self.log_combat(f"Revealed boss: {display_name} (HP: {tile.health})")
                    
                elif tile.tile_type == TileType.ENEMY:
                    display_name = self.get_display_name(tile.item_id)
                    self.log_combat(f"Revealed enemy: {display_name} (HP: {tile.health})")
                    
                # Check for Norfair damage (without Varia suit)
                if tile.area == AreaType.NORFAIR and not self.inventory.get("varia", False):
                    self.player_energy -= 25
                    self.log_combat("Norfair heat damage! -25 energy")
                    if self.player_energy <= 0:
                        self.game_over = True
                        self.log_combat("GAME OVER - Player defeated!")
                
                    
    def can_click_tile(self, x: int, y: int) -> bool:
        """Check if a tile can be clicked (adjacent to revealed tiles or first tile)"""
        # First tile can be anywhere
        if not self.revealed_tiles:
            return True
            
        # Check if adjacent to any revealed tile
        for rx, ry in self.revealed_tiles:
            if abs(x - rx) + abs(y - ry) == 1:  # Adjacent (manhattan distance = 1)
                return True
                
        return False
    
    def auto_grab_adjacent_items(self, x: int, y: int):
        """Auto-grab diagonal tiles if they are items (X-ray scope ability - forms an X!)"""
        # Check diagonal directions only (forms an "X" pattern)
        # Format: (x, y) where x=column, y=row
        diagonal_positions = [
            (x-1, y-1),   # top-left
            (x+1, y-1),   # top-right
            (x-1, y+1),   # bottom-left
            (x+1, y+1)    # bottom-right
        ]
        
        for diag_pos in diagonal_positions:
            diag_x, diag_y = diag_pos
            # Check bounds
            if not (0 <= diag_x < GRID_SIZE and 0 <= diag_y < GRID_SIZE):
                continue
            
            tile = self.grid[diag_y][diag_x]
            
            # Only auto-grab if it's face-down and is an item
            if tile.state == TileState.FACE_DOWN and tile.tile_type == TileType.ITEM:
                # Check for Maridia movement restriction
                if tile.area == AreaType.MARIDIA and not self.inventory.get("gravity", False):
                    continue  # Skip Maridia tiles without gravity suit
                
                tile.state = TileState.FACE_UP
                self.revealed_tiles.append((diag_x, diag_y))
                
                # Collect the item
                display_name = self.get_display_name(tile.item_id)
                if isinstance(self.inventory[tile.item_id], bool):
                    if not self.inventory[tile.item_id]:
                        self.inventory[tile.item_id] = True
                        self.log_combat(f"X-ray auto-collected {display_name}!")
                else:
                    # Consumable item
                    self.inventory[tile.item_id] += 1
                    self.log_combat(f"X-ray auto-collected {display_name}! Total: {self.inventory[tile.item_id]}")
                
                # Add score for item collection
                item_scores = {
                    "missiles": 10, "supers": 20, "power_bombs": 30, "energy_tank": 50,
                    "morph": 100, "bomb": 100, "hijump": 150, "speed": 150,
                    "grapple": 200, "xray": 200, "spring": 150, "space": 200,
                    "screw": 250, "charge": 150, "spazer": 200, "wave": 200,
                    "ice": 200, "plasma": 250, "varia": 300, "gravity": 400
                }
                self.score += item_scores.get(tile.item_id, 10)
                
                # Energy tanks increase max energy and heal fully
                if tile.item_id == "energy_tank":
                    self.max_energy += 100
                    self.player_energy = self.max_energy
                    self.log_combat(f"Energy tank collected! Max energy: {self.max_energy}")
                
                # Check for Norfair damage on auto-grabbed tiles
                if tile.area == AreaType.NORFAIR and not self.inventory.get("varia", False):
                    self.player_energy -= 25
                    self.log_combat("Norfair heat damage! -25 energy")
                    if self.player_energy <= 0:
                        self.game_over = True
                        self.log_combat("GAME OVER - Player defeated!")
        
    def get_area_color(self, area_type: AreaType) -> Tuple[int, int, int]:
        """Get the color for an area type"""
        area_colors = {
            AreaType.CRATERIA: CRATERIA_LIGHT_BLUE,
            AreaType.BRINSTAR: BRINSTAR_GREEN,
            AreaType.NORFAIR: NORFAIR_RED,
            AreaType.MARIDIA: MARIDIA_BLUE,
            AreaType.TOURIAN: TOURIAN_YELLOW,
            AreaType.WRECKED_SHIP: WRECKED_SHIP_PURPLE,
            AreaType.CERES: CERES_GRAY
        }
        return area_colors.get(area_type, DARK_GRAY)
        
    def get_display_name(self, entity_id: str) -> str:
        """Get a nice display name for enemies and bosses (wrapper for standalone function)"""
        return get_display_name(entity_id)
        
    def log_combat(self, message: str):
        """Add a message to the combat log"""
        self.combat_log.append(message)
        # Keep only last 20 messages
        if len(self.combat_log) > 28:
            self.combat_log.pop(0)
        print(message)  # Also print to console
        
    def get_attack_first_chance(self) -> float:
        """Calculate chance to attack first based on equipped items"""
        chance = 0.0
        
        # Movement items increase attack first chance by 25%
        if self.inventory.get("space", False):
            chance += 0.25
        if self.inventory.get("hijump", False):
            chance += 0.25
        if self.inventory.get("morph", False):
            chance += 0.25
        if self.inventory.get("spring", False):
            chance += 0.25
        
        # Speed booster increases by 50%
        if self.inventory.get("speed", False):
            chance += 0.50
        
        return min(chance, 1.0)  # Cap at 100%
    
    def update(self):
        """Update game state"""
        # Don't update combat if game over
        if self.game_over:
            return
            
        # Update energy based on energy tanks
        self.max_energy = 99 + (self.inventory.get("energy_tank", 0) * 100)
        
        # Update combat - determine attack order based on items
        self.boss_turn_timer += 1
        player_attacks_first = random.random() < self.get_attack_first_chance()
        
        if self.boss_turn_timer >= self.boss_turn_interval:
            self.boss_turn_timer = 0
            
            if player_attacks_first and self.is_fight_active():
                # Player attacks first
                self.process_player_attacks()
                self.process_enemy_turns()  # Then enemies
                self.process_boss_turns()    # Then bosses
            else:
                # Normal order: enemies first, then bosses
                self.process_enemy_turns()
                self.process_boss_turns()
            
        # Update player attacks on bosses (slower) - only if didn't attack first
        if not player_attacks_first:
            self.player_attack_timer += 1
            if self.player_attack_timer >= self.player_attack_interval:
                self.player_attack_timer = 0
                self.process_player_attacks()
            
    def process_enemy_turns(self):
        """Process enemy attacks on player"""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = self.grid[y][x]
                if (tile.tile_type == TileType.ENEMY and 
                    tile.state == TileState.FACE_UP and 
                    tile.health > 0):
                    
                    # Check if enemy is frozen
                    if tile.frozen:
                        display_name = self.get_display_name(tile.item_id)
                        self.log_combat(f"{display_name} is frozen and skips turn!")
                        tile.frozen = False  # Unfreeze after turn
                        continue
                    
                    # Enemy attacks player
                    damage = self.enemy_damage.get(tile.item_id, 3)
                    self.player_energy -= damage
                    display_name = self.get_display_name(tile.item_id)
                    self.log_combat(f"{display_name} attacks for {damage} damage!")
                    
                    if self.player_energy <= 0:
                        self.game_over = True
                        self.log_combat("GAME OVER - Player defeated!")
                        return
            
    def process_boss_turns(self):
        """Process boss attacks"""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = self.grid[y][x]
                if (tile.tile_type == TileType.BOSS and 
                    tile.state == TileState.FACE_UP and 
                    tile.health > 0):
                    
                    # Check if boss is frozen
                    if tile.frozen:
                        display_name = self.get_display_name(tile.item_id)
                        self.log_combat(f"{display_name} is frozen and skips turn!")
                        tile.frozen = False  # Unfreeze after turn
                        continue
                    
                    # Boss attacks player
                    damage = self.get_boss_damage(tile.item_id)
                    self.player_energy -= damage
                    display_name = self.get_display_name(tile.item_id)
                    self.log_combat(f"{display_name} attacks for {damage} damage!")
                    
                    if self.player_energy <= 0:
                        self.player_energy = 0
                        self.game_over = True
                        self.log_combat("GAME OVER - Player defeated!")
                        
    def process_player_attacks(self):
        """Process player attacks on bosses and enemies"""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = self.grid[y][x]
                if ((tile.tile_type == TileType.BOSS or tile.tile_type == TileType.ENEMY) and 
                    tile.state == TileState.FACE_UP and 
                    tile.health > 0):
                    
                    # Player attacks boss/enemy
                    damage = self.get_player_damage(tile.item_id)
                    tile.health -= damage
                    display_name = self.get_display_name(tile.item_id)
                    self.log_combat(f"Samus attacks {display_name} for {damage} dmg!")
                    
                    # Check for ice beam freeze (10% chance)
                    if (self.inventory.get("ice", False) and 
                        tile.health > 0 and 
                        random.random() < 0.10):
                        self.log_combat(f"{display_name} frozen! Extra turn!")
                        # Mark enemy as frozen (skip their next turn)
                        tile.frozen = True
                    
                    if tile.health <= 0:
                        tile.health = 0
                        tile.state = TileState.DESTROYED
                        
                        # Handle boss defeats
                        if tile.tile_type == TileType.BOSS:
                            self.boss_defeats[tile.item_id] += 1
                            
                            # Special Ceres Station handling
                            if tile.item_id == "ceres_station":
                                self.log_combat("You saved Ceres Station!")
                                self.log_combat("Ridley's life down by 1000!")
                                # Reduce Ridley's health if he exists
                                for y2 in range(GRID_SIZE):
                                    for x2 in range(GRID_SIZE):
                                        ridley_tile = self.grid[y2][x2]
                                        if (ridley_tile.tile_type == TileType.BOSS and 
                                            ridley_tile.item_id == "ridley" and 
                                            ridley_tile.health > 0):
                                            ridley_tile.health = max(0, ridley_tile.health - 1000)
                                            self.log_combat(f"Ridley's health reduced to {ridley_tile.health}!")
                                self.score += 600
                                continue
                            
                            # Check for Mother Brain victory
                            if tile.item_id == "mother_brain_1":
                                self.game_over = True
                                self.victory = True
                                self.log_combat("SAMUS WINS! Mother Brain defeated!")
                                return
                            
                            # Add score for boss defeat
                            boss_scores = {
                                "bomb_torizo": 500, "spore_spawn": 800, "kraid": 2000, "crocomire": 1200,
                                "phantoon": 1500, "botwoon": 1000, "draygon": 1800, "gold_torizo": 1600,
                                "ridley": 2500, "mother_brain_1": 5000, "mother_brain_2": 3000,
                                "samus_ship": 800, "golden_four": 4000
                            }
                            self.score += boss_scores.get(tile.item_id, 1000)
                            display_name = self.get_display_name(tile.item_id)
                            self.log_combat(f"{display_name} defeated! Score: +{boss_scores.get(tile.item_id, 1000)}")
                        
                        # Handle enemy defeats
                        elif tile.tile_type == TileType.ENEMY:
                            enemy_scores = {
                                "geemer": 25, "skree": 35, "side_hopper": 50, "ciser": 75
                            }
                            self.score += enemy_scores.get(tile.item_id, 25)
                            display_name = self.get_display_name(tile.item_id)
                            self.log_combat(f"{display_name} defeated! Score: +{enemy_scores.get(tile.item_id, 25)}")
                        
    def get_boss_damage(self, boss_id: str) -> int:
        """Get boss attack damage"""
        boss_damage = {
            "bomb_torizo": 5,
            "spore_spawn": 8,
            "kraid": 15,
            "crocomire": 10,
            "phantoon": 12,
            "botwoon": 6,
            "draygon": 20,
            "gold_torizo": 18,
            "ridley": 25,
            "mother_brain_1": 30,
            "mother_brain_2": 20,
            "samus_ship": 3,
            "ceres_station": 4,
            "golden_four": 35
        }
        return boss_damage.get(boss_id, 10)
        
    def get_player_damage(self, boss_id: str) -> int:
        """Get player damage against boss - beams, speed booster, and missiles add damage"""
        base_damage = 10
        
        # Beam weapons and speed booster add to damage
        if self.inventory.get("charge", False):
            base_damage += 20
        if self.inventory.get("ice", False):
            base_damage += 20
        if self.inventory.get("spazer", False):
            base_damage += 30
        if self.inventory.get("wave", False):
            base_damage += 20
        if self.inventory.get("plasma", False):
            base_damage += 25
        if self.inventory.get("screw", False):
            base_damage += 50  # Screw attack is powerful
        if self.inventory.get("speed", False):
            base_damage += 20  # Speed booster adds damage
        if self.inventory.get("bomb", False):
            base_damage += 50  # Bombs add significant attack damage
            
        # Missile bonuses with proper scaling
        missile_base = 10  # Base missile damage
        base_damage += self.inventory.get("missiles", 0) * missile_base
        base_damage += self.inventory.get("supers", 0) * (missile_base * 2)  # 2x missile damage
        base_damage += self.inventory.get("power_bombs", 0) * (missile_base * 3)  # 3x missile damage
        
        # Special boss interactions
        if boss_id == "draygon" and self.inventory.get("grapple", False):
            base_damage *= 3
            self.log_combat("Grappling beam bonus vs Draygon! 3x damage!")
            
        # Suit bonuses
        if self.inventory.get("varia", False):
            base_damage = int(base_damage * 1.25)  # 25% damage boost
        if self.inventory.get("gravity", False):
            base_damage = int(base_damage * 1.5)   # 50% damage boost
            
        return base_damage
        
    def render(self):
        """Render the game"""
        self.screen.fill(BLACK)
        
        # Draw energy display
        self.draw_energy_display()
        
        # Draw inventory
        self.draw_inventory()
        
        # Draw grid
        self.draw_grid()
        
        # Draw combat info
        self.draw_combat_info()
        
        # Draw boss tracker
        self.draw_boss_tracker()
        
        pygame.display.flip()
        
    def draw_grid(self):
        """Draw the game grid"""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = self.grid[y][x]
                screen_x, screen_y = tile.get_screen_position()
                
                if tile.state == TileState.FACE_DOWN:
                    # Draw face-down tile with area color
                    area_color = self.get_area_color(tile.area)
                    pygame.draw.rect(self.screen, area_color, 
                                   (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(self.screen, GRAY, 
                                   (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 2)
                elif tile.state == TileState.FACE_UP:
                    # Draw face-up tile with sprite - all tiles have black background
                    pygame.draw.rect(self.screen, BLACK, 
                                   (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(self.screen, GRAY, 
                                   (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 2)
                    
                    # Draw sprite
                    if tile.tile_type == TileType.ITEM:
                        self.sprite_manager.draw_item(self.screen, tile.item_id, 
                                                    screen_x, screen_y, TILE_SIZE)
                    elif tile.tile_type == TileType.BOSS:
                        self.sprite_manager.draw_boss(self.screen, tile.item_id, 
                                                    screen_x, screen_y, TILE_SIZE)
                        
                        # Draw boss health bar at bottom of tile (skip ship)
                        if tile.item_id != "samus_ship":
                            self.draw_health_bar(screen_x, screen_y + TILE_SIZE - 4, 
                                               tile.health, tile.max_health)
                                               
                    elif tile.tile_type == TileType.ENEMY:
                        self.sprite_manager.draw_enemy(self.screen, tile.item_id, 
                                                     screen_x, screen_y, TILE_SIZE)
                        
                        # Draw enemy health bar at bottom of tile (always show for enemies)
                        self.draw_health_bar(screen_x, screen_y + TILE_SIZE - 4, 
                                           tile.health, tile.max_health)
                elif tile.state == TileState.DESTROYED:
                    # Draw destroyed boss as grayscaled sprite
                    pygame.draw.rect(self.screen, BLACK, 
                                   (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(self.screen, GRAY, 
                                   (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 2)
                    
                    # Draw grayscaled boss/enemy sprite
                    if tile.tile_type == TileType.BOSS:
                        self.sprite_manager.draw_boss_grayed(self.screen, tile.item_id, 
                                                           screen_x, screen_y, TILE_SIZE)
                    elif tile.tile_type == TileType.ENEMY:
                        self.sprite_manager.draw_enemy_grayed(self.screen, tile.item_id, 
                                                            screen_x, screen_y, TILE_SIZE)
                                            
    def draw_health_bar(self, x: int, y: int, current: int, maximum: int):
        """Draw a health bar at bottom of tile"""
        bar_width = TILE_SIZE
        bar_height = 4  # Half height, on tile
        health_ratio = current / maximum if maximum > 0 else 0
        
        # Background (dark red)
        pygame.draw.rect(self.screen, (120, 0, 0), (x, y, bar_width, bar_height))
        # Border
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height), 1)
        # Health (bright green)
        if health_ratio > 0:
            health_width = int(bar_width * health_ratio)
            pygame.draw.rect(self.screen, (0, 255, 0), (x, y, health_width, bar_height))
        
    def draw_energy_display(self):
        """Draw energy display like Metroid (tanks + remainder)"""
        font = pygame.font.Font(None, 24)
        x = 10
        y = 10
        
        # Calculate total tanks based on max energy
        total_tanks = self.max_energy // 100
        remainder = self.player_energy % 100
        
        # Draw tanks in rows (7 per row like SM)
        tanks_per_row = 7
        tank_size = 16
        tank_spacing = 2
        
        for i in range(total_tanks):
            row = i // tanks_per_row
            col = i % tanks_per_row
            tank_x = x + col * (tank_size + tank_spacing)
            tank_y = y + row * (tank_size + tank_spacing)
            
            # Draw tank background
            pygame.draw.rect(self.screen, WHITE, (tank_x, tank_y, tank_size, tank_size), 1)
            
            # Determine if this tank is full or empty
            tank_start_energy = i * 100
            tank_end_energy = (i + 1) * 100
            
            if self.player_energy >= tank_end_energy:
                # Full tank
                pygame.draw.rect(self.screen, BRINSTAR_GREEN, (tank_x + 1, tank_y + 1, tank_size - 2, tank_size - 2))
            # Empty tank - no fill (shows as empty square)
            
        # Draw remainder number to the right of squares (always show)
        # Calculate position based on actual number of tanks drawn
        actual_tanks_this_row = min(total_tanks, tanks_per_row)
        number_x = x + (actual_tanks_this_row * (tank_size + tank_spacing)) + 15
        energy_text = font.render(str(remainder), True, WHITE)
        self.screen.blit(energy_text, (number_x, y))
        
    def draw_inventory(self):
        """Draw the two-row inventory bar to the right of energy display"""
        # Start inventory to the right of energy display
        start_x = 320  # Right of energy tanks
        y = INVENTORY_Y
        
        # Organize items into two rows
        items = list(self.inventory.keys())
        items_per_row = len(items) // 2
        item_size = 32
        item_spacing = 2  # Minimal spacing between icons
        
        # Row 1 (top)
        for i, item_id in enumerate(items[:items_per_row]):
            x = start_x + i * (item_size + item_spacing)
            
            # Draw item icon
            has_item = self.inventory[item_id] if isinstance(self.inventory[item_id], bool) else self.inventory[item_id] > 0
            if has_item:
                self.sprite_manager.draw_item(self.screen, item_id, x, y, item_size)
            else:
                self.sprite_manager.draw_item_grayed(self.screen, item_id, x, y, item_size)
                
            # Draw count on bottom-right of icon (only for consumables)
            if not isinstance(self.inventory[item_id], bool):
                count = self.inventory[item_id]
                if count > 0:
                    font = pygame.font.Font(None, 16)
                    text = font.render(str(count), True, WHITE)
                    self.screen.blit(text, (x + 20, y + 20))
                
        # Row 2 (bottom)
        for i, item_id in enumerate(items[items_per_row:]):
            x = start_x + i * (item_size + item_spacing)
            
            # Draw item icon
            has_item = self.inventory[item_id] if isinstance(self.inventory[item_id], bool) else self.inventory[item_id] > 0
            if has_item:
                self.sprite_manager.draw_item(self.screen, item_id, x, y + 35, item_size)
            else:
                self.sprite_manager.draw_item_grayed(self.screen, item_id, x, y + 35, item_size)
                
            # Draw count on bottom-right of icon (only for consumables)
            if not isinstance(self.inventory[item_id], bool):
                count = self.inventory[item_id]
                if count > 0:
                    font = pygame.font.Font(None, 16)
                    text = font.render(str(count), True, WHITE)
                    self.screen.blit(text, (x + 20, y + 55))
                
    def draw_combat_info(self):
        """Draw combat information to the right of grid"""
        x = COMBAT_INFO_X
        y = GRID_START_Y  # Same height as grid
        height = GRID_SIZE * TILE_SIZE  # Same height as grid
        
        # Background
        pygame.draw.rect(self.screen, BLACK, (x, y, HUD_WIDTH, height))
        pygame.draw.rect(self.screen, GRAY, (x, y, HUD_WIDTH, height), 2)
        
        # Title
        font = pygame.font.Font(None, 24)
        title = font.render("Log", True, WHITE)
        self.screen.blit(title, (x + 10, y + 10))
        
        # Combat log - calculate how many messages can actually fit
        font_small = pygame.font.Font(None, 20)  # Bigger text
        log_start_y = y + 35  # Start below title
        stats_start_y = y + height - 90  # Stats area starts here
        available_height = stats_start_y - log_start_y
        line_height = 16
        max_messages = available_height // line_height
        
        # Show as many messages as can fit
        messages_to_show = min(max_messages, len(self.combat_log))
        for i, message in enumerate(self.combat_log[-messages_to_show:]):
            text = font_small.render(message, True, WHITE)
            self.screen.blit(text, (x + 10, log_start_y + i * line_height))
            
        # Current stats at bottom (fixed position)
        y_stats = y + height - 90  # More space for additional messages
        stats_font = pygame.font.Font(None, 20)
        
        # Game over/victory message (fixed position, doesn't push stats)
        if self.game_over:
            game_over_font = pygame.font.Font(None, 32)
            if self.victory:
                message_text = game_over_font.render("SAMUS WINS", True, BRINSTAR_GREEN)
            else:
                message_text = game_over_font.render("GAME OVER", True, NORFAIR_RED)
            # Show message at fixed position above stats
            self.screen.blit(message_text, (x + 10, y_stats - 50))
        
        # Player damage
        damage = self.get_player_damage("")  # Get base damage
        damage_text = stats_font.render(f"Base Damage: {damage}", True, WHITE)
        self.screen.blit(damage_text, (x + 10, y_stats))
        
        # Score
        score_text = stats_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (x + 10, y_stats + 25))
        
        # Reset instruction
        reset_text = stats_font.render("Press R to Reset", True, GRAY)
        self.screen.blit(reset_text, (x + 10, y_stats + 50))
            
    def draw_boss_tracker(self):
        """Draw boss tracker in top right (like item HUD)"""
        x = BOSS_HUD_X
        y = INVENTORY_Y
        
        # Boss icons in two rows (no background, no title) - removed ship, ceres_station, and golden_four
        boss_list = [
            "bomb_torizo", "spore_spawn", "kraid", "crocomire",
            "phantoon", "botwoon", "draygon", "gold_torizo",
            "ridley", "mother_brain_1"
        ]
        
        icon_size = 32  # Match item HUD size
        icons_per_row = 5  # Even rows: 6 per row for 11 bosses
        spacing = 2
        
        # Calculate starting position to right-align
        total_width = icons_per_row * (icon_size + spacing) - spacing
        start_x = x + (BOSS_HUD_WIDTH - total_width)
        
        for i, boss_id in enumerate(boss_list):
            row = i // icons_per_row
            col = i % icons_per_row
            icon_x = start_x + col * (icon_size + spacing)
            icon_y = y + row * (icon_size + spacing)
            
            # Draw boss icon (no counters, just defeated/not defeated)
            if self.boss_defeats[boss_id] > 0:
                # Defeated - show normal sprite
                self.sprite_manager.draw_boss(self.screen, boss_id, icon_x, icon_y, icon_size)
            else:
                # Not defeated - show grayed out
                self.sprite_manager.draw_boss_grayed(self.screen, boss_id, icon_x, icon_y, icon_size)
                
        
    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

class SpriteManager:
    """Manages sprite loading and drawing"""
    def __init__(self):
        self.boss_sprites = {}
        self.item_sprites = {}
        self.enemy_sprites = {}
        self.load_sprites()
        
    def load_sprites(self):
        """Load all sprites from sprite sheets"""
        try:
            # Load boss sprites
            boss_sheet = pygame.image.load("boss_sprites.png").convert_alpha()
            self.boss_sprites = self.load_sprite_sheet(boss_sheet, 64, 64)
            
            # Load item sprites  
            item_sheet = pygame.image.load("item_sprites.png").convert_alpha()
            self.item_sprites = self.load_sprite_sheet(item_sheet, 16, 16)
            
            # Load enemy sprites (4 enemies in a row, 32x32 each)
            enemy_sheet = pygame.image.load("enemies.png").convert_alpha()
            self.enemy_sprites = self.load_enemy_sprites(enemy_sheet, 32, 32)
            
        except pygame.error as e:
            print(f"Error loading sprites: {e}")
            
    def load_sprite_sheet(self, sheet: pygame.Surface, sprite_width: int, sprite_height: int) -> Dict[str, pygame.Surface]:
        """Load individual sprites from a sprite sheet"""
        sprites = {}
        sheet_width, sheet_height = sheet.get_size()
        
        # Define sprite mappings
        if sprite_width == 64:  # Boss sprites
            mappings = {
                "bomb_torizo": (0, 0),
                "spore_spawn": (64, 0),
                "kraid": (128, 0),
                "crocomire": (192, 0),
                "phantoon": (256, 0),
                "botwoon": (320, 0),
                "draygon": (384, 0),
                "gold_torizo": (448, 0),
                "ridley": (512, 0),
                "mother_brain_1": (576, 0),
                "mother_brain_2": (640, 0),
                "samus_ship": (704, 0),
                "ceres_station": (768, 0),
                "golden_four": (832, 0),
            }
        else:  # Item sprites
            mappings = {
                "missiles": (0, 16),
                "supers": (32, 16),
                "power_bombs": (64, 16),
                "energy_tank": (64, 0),
                "morph": (0, 0),
                "bomb": (32, 0),
                "hijump": (0, 32),
                "speed": (32, 32),
                "grapple": (64, 32),
                "xray": (96, 32),
                "spring": (0, 48),
                "space": (32, 48),
                "screw": (64, 48),
                "charge": (96, 48),
                "spazer": (0, 64),
                "wave": (32, 64),
                "ice": (64, 64),
                "plasma": (96, 64),
                "varia": (0, 80),
                "gravity": (32, 80),
            }
            
        for name, (x, y) in mappings.items():
            sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
            sprite.blit(sheet, (0, 0), (x, y, sprite_width, sprite_height))
            sprites[name] = sprite
            
        return sprites
        
    def load_enemy_sprites(self, sheet: pygame.Surface, sprite_width: int, sprite_height: int) -> Dict[str, pygame.Surface]:
        """Load enemy sprites from a single row sheet"""
        sprites = {}
        enemy_names = ["geemer", "skree", "side_hopper", "ciser"]
        
        for i, name in enumerate(enemy_names):
            x = i * sprite_width
            y = 0
            sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
            sprite.blit(sheet, (0, 0), (x, y, sprite_width, sprite_height))
            sprites[name] = sprite
            
        return sprites
        
    def draw_boss(self, screen: pygame.Surface, boss_id: str, x: int, y: int, size: int):
        """Draw a boss sprite"""
        if boss_id in self.boss_sprites:
            sprite = self.boss_sprites[boss_id]
            scaled_sprite = pygame.transform.scale(sprite, (size, size))
            screen.blit(scaled_sprite, (x, y))
            
    def draw_item(self, screen: pygame.Surface, item_id: str, x: int, y: int, size: int):
        """Draw an item sprite"""
        if item_id in self.item_sprites:
            sprite = self.item_sprites[item_id]
            scaled_sprite = pygame.transform.scale(sprite, (size, size))
            screen.blit(scaled_sprite, (x, y))
            
    def draw_item_grayed(self, screen: pygame.Surface, item_id: str, x: int, y: int, size: int):
        """Draw a grayed out item sprite"""
        if item_id in self.item_sprites:
            sprite = self.item_sprites[item_id]
            scaled_sprite = pygame.transform.scale(sprite, (size, size))
            
            # Create a grayed out version
            grayed = scaled_sprite.copy()
            grayed.fill((128, 128, 128, 128), special_flags=pygame.BLEND_RGBA_MULT)
            
            screen.blit(grayed, (x, y))
            
    def draw_boss_grayed(self, screen: pygame.Surface, boss_id: str, x: int, y: int, size: int):
        """Draw a grayed out boss sprite"""
        if boss_id in self.boss_sprites:
            sprite = self.boss_sprites[boss_id]
            scaled_sprite = pygame.transform.scale(sprite, (size, size))
            
            # Create a grayed out version
            grayed = scaled_sprite.copy()
            grayed.fill((128, 128, 128, 128), special_flags=pygame.BLEND_RGBA_MULT)
            
            screen.blit(grayed, (x, y))
            
    def draw_enemy(self, screen: pygame.Surface, enemy_id: str, x: int, y: int, size: int):
        """Draw an enemy sprite (scaled up from 32x32 to match boss size)"""
        if enemy_id in self.enemy_sprites:
            sprite = self.enemy_sprites[enemy_id]
            scaled_sprite = pygame.transform.scale(sprite, (size, size))
            screen.blit(scaled_sprite, (x, y))
            
    def draw_enemy_grayed(self, screen: pygame.Surface, enemy_id: str, x: int, y: int, size: int):
        """Draw a grayscaled enemy sprite (scaled up from 32x32)"""
        if enemy_id in self.enemy_sprites:
            sprite = self.enemy_sprites[enemy_id]
            scaled_sprite = pygame.transform.scale(sprite, (size, size))
            
            # Create a grayed out version
            grayed = scaled_sprite.copy()
            grayed.fill((128, 128, 128, 128), special_flags=pygame.BLEND_RGBA_MULT)
            
            screen.blit(grayed, (x, y))

if __name__ == "__main__":
    game = Game()
    game.run()
