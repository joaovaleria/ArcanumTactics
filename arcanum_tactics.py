import streamlit as st
import pandas as pd
import collections
import random

# --- GAME DATA & CONSTANTS ---

BOARD_COLS = [chr(ord('A') + i) for i in range(11)] # A-K
BOARD_ROWS = list(range(1, 14)) # 1-13
MYSTIC_ZONES = [('E', 7), ('G', 7), ('I', 7)] # As três zonas místicas

UNIT_DATA = {
    'Arcane Core': {'hp': 20, 'atk': 0, 'mv': 0, 'range': 0},
    'Sylvara': {'hp': 10, 'atk': 2, 'mv': 2, 'range': 1},
    'Guardião': {'hp': 5, 'atk': 2, 'mv': 2, 'range': 1},
    'Batedor': {'hp': 3, 'atk': 2, 'mv': 3, 'range': 1},
    'Adeptus': {'hp': 2, 'atk': 3, 'mv': 2, 'range': 3},
    'Brutamontes': {'hp': 6, 'atk': 3, 'mv': 1, 'range': 1},
    'Sentinela Arcana': {'hp': 4, 'atk': 1, 'mv': 2, 'range': 2},
}

CARD_DATA = {
    "Invocação: Adeptus": {"type": "invocation", "unit_type": "Adeptus", "cost": 2, "desc": "Invoca um Adeptus."},
    "Invocação: Batedor": {"type": "invocation", "unit_type": "Batedor", "cost": 2, "desc": "Invoca um Batedor."},
    "Invocação: Sentinela Arcana": {"type": "invocation", "unit_type": "Sentinela Arcana", "cost": 3, "desc": "Invoca uma Sentinela Arcana."},
    "Feitiço: Pulso Etéreo": {"type": "spell", "cost": 2, "desc": "Causa 2 de dano a uma unidade a até 4 casas."},
    "Feitiço: Escudo Etéreo": {"type": "spell", "cost": 2, "desc": "Aplica 3 de escudo a uma unidade aliada."},
    "Feitiço: Reflexo Estratégico": {"type": "spell", "cost": 4, "desc": "Compra 2 cartas."},
    "Feitiço: Translocação Rápida": {"type": "spell", "cost": 1, "desc": "Move um aliado 1 hexágono."},
}

# --- COORDINATE HELPER FUNCTIONS ---

def col_to_int(col_char):
    """Converts a column character ('A'-'K') to an integer (0-10)."""
    return ord(col_char.upper()) - ord('A')

def int_to_col(col_int):
    """Converts a column integer (0-10) to a character ('A'-'K')."""
    return chr(ord('A') + col_int)

def is_valid_coord(coords):
    """Checks if coordinates (col_char, row_int) are within the board."""
    col_char, row_int = coords
    return col_char in BOARD_COLS and row_int in BOARD_ROWS

def get_adjacent_hexes(coords):
    """
    Implements the hexagonal adjacency rule on the square grid.
    Returns a list of valid adjacent coordinates.
    """
    col_char, row = coords
    col = col_to_int(col_char)
    
    potential_neighbors = [
        (col, row - 1), (col, row + 1),
        (col - 1, row), (col + 1, row),
    ]
    
    if row % 2 != 0: # Odd rows
        potential_neighbors.extend([
            (col + 1, row - 1), (col + 1, row + 1)
        ])
    else: # Even rows
        potential_neighbors.extend([
            (col - 1, row - 1), (col - 1, row + 1)
        ])
        
    valid_neighbors = []
    for c, r in potential_neighbors:
        coord_tuple = (int_to_col(c), r)
        if is_valid_coord(coord_tuple):
            valid_neighbors.append(coord_tuple)
            
    return valid_neighbors

def calculate_distance(start_coords, end_coords):
    """Calculates hexagonal distance using Breadth-First Search."""
    if not is_valid_coord(start_coords) or not is_valid_coord(end_coords):
        return float('inf')
        
    q = collections.deque([(start_coords, 0)]) # (coords, distance)
    visited = {start_coords}
    
    while q:
        current_coords, dist = q.popleft()
        
        if current_coords == end_coords:
            return dist
            
        for neighbor in get_adjacent_hexes(current_coords):
            if neighbor not in visited:
                visited.add(neighbor)
                q.append((neighbor, dist + 1))
                
    return float('inf')

# --- SESSION STATE INITIALIZATION ---
if 'game_initialized' not in st.session_state:
    st.session_state.game_initialized = False

# Função para adicionar mensagens ao log
def add_event_message(message, is_critical=False):
    if 'event_log' not in st.session_state:
        st.session_state.event_log = collections.deque(maxlen=7) # Limite para 7 mensagens
    st.session_state.event_log.append(message)
    # Se for uma mensagem crítica (e.g., vitória/derrota), também a coloca como game_message
    if is_critical:
        st.session_state.game_message = message

if not st.session_state.game_initialized:
    st.session_state.units = {
        # Player 1 units (com atributos completos)
        '0': {'type': 'Arcane Core', 'player': 1, 'col': 'F', 'row': 13, 'hp': 20, 'max_hp': 20, 'mv_remaining': 0, 'ap_remaining': 1, 'max_mv': 0, 'atk': 0, 'range': 0},
        '1': {'type': 'Sylvara', 'player': 1, 'col': 'E', 'row': 12, 'hp': 10, 'max_hp': 10, 'mv_remaining': 2, 'ap_remaining': 1, 'max_mv': 2, 'atk': 2, 'range': 1},
        '2': {'type': 'Guardião', 'player': 1, 'col': 'D', 'row': 13, 'hp': 5, 'max_hp': 5, 'mv_remaining': 2, 'ap_remaining': 1, 'max_mv': 2, 'atk': 2, 'range': 1},
        '3': {'type': 'Batedor', 'player': 1, 'col': 'G', 'row': 12, 'hp': 3, 'max_hp': 3, 'mv_remaining': 3, 'ap_remaining': 1, 'max_mv': 3, 'atk': 2, 'range': 1},
        '4': {'type': 'Adeptus', 'player': 1, 'col': 'H', 'row': 13, 'hp': 2, 'max_hp': 2, 'mv_remaining': 2, 'ap_remaining': 1, 'max_mv': 2, 'atk': 3, 'range': 3},
        # Player 2 units (AI) - com atributos completos
        '5': {'type': 'Arcane Core', 'player': 2, 'col': 'F', 'row': 1, 'hp': 20, 'max_hp': 20, 'mv_remaining': 0, 'ap_remaining': 1, 'max_mv': 0, 'atk': 0, 'range': 0},
        '6': {'type': 'Guardião', 'player': 2, 'col': 'E', 'row': 2, 'hp': 5, 'max_hp': 5, 'mv_remaining': 2, 'ap_remaining': 1, 'max_mv': 2, 'atk': 2, 'range': 1}, # AI Champion placeholder
        '7': {'type': 'Adeptus', 'player': 2, 'col': 'D', 'row': 1, 'hp': 2, 'max_hp': 2, 'mv_remaining': 2, 'ap_remaining': 1, 'max_mv': 2, 'atk': 3, 'range': 3},
        '8': {'type': 'Batedor', 'player': 2, 'col': 'G', 'row': 2, 'hp': 3, 'max_hp': 3, 'mv_remaining': 3, 'ap_remaining': 1, 'max_mv': 3, 'atk': 2, 'range': 1},
        '9': {'type': 'Sentinela Arcana', 'player': 2, 'col': 'H', 'row': 1, 'hp': 4, 'max_hp': 4, 'mv_remaining': 2, 'ap_remaining': 1, 'max_mv': 2, 'atk': 1, 'range': 2},
    }
    st.session_state.selected_unit = None
    st.session_state.mana = {1: 3, 2: 3}
    st.session_state.hand = {
        1: ["Invocação: Adeptus", "Feitiço: Pulso Etéreo", "Invocação: Batedor"], # Cartas iniciais para o Jogador 1
        2: [], # AI não desenha cartas inicialmente nesta versão
    }
    st.session_state.current_turn = 1
    st.session_state.turn_number = 1
    st.session_state.game_message = "Bem-vindo ao Arcanum Tactics!"
    st.session_state.game_over = False
    st.session_state.next_unit_id = 10 # Próximo ID disponível para novas unidades
    st.session_state.valid_moves = set() # para guardar hexágonos de movimento válido
    st.session_state.valid_attacks = set() # para guardar hexágonos de ataque válido
    st.session_state.mystic_zone_control = { # Inicializa o controlo das zonas místicas
        (col, row): None for col, row in MYSTIC_ZONES
    }
    st.session_state.invocation_mode = False
    st.session_state.unit_type_to_invoke = None
    st.session_state.valid_invocations = set() # para guardar hexágonos de invocação válida
    # Inicializa o log de eventos
    st.session_state.event_log = collections.deque(maxlen=7) # Armazena as últimas 7 mensagens
    
    # INICIALIZAÇÃO DOS ESTADOS DE FEEDBACK VISUAL
    st.session_state.last_moved_unit = None
    st.session_state.last_move_from = None
    st.session_state.last_move_to = None
    st.session_state.last_attack_info = None

    add_event_message("Jogo iniciado! Que a tua estratégia te guie.")

    st.session_state.game_initialized = True


# --- GAME LOGIC FUNCTIONS ---

def get_unit_at_coords_streamlit(coords):
    for uid, unit in st.session_state.units.items():
        if (unit['col'], unit['row']) == coords:
            return uid, unit
    return None, None

def update_mystic_zone_control():
    for zone_col, zone_row in MYSTIC_ZONES:
        zone_coords = (zone_col, zone_row)
        
        unit_on_zone_id, unit_on_zone = get_unit_at_coords_streamlit(zone_coords)
        
        if unit_on_zone:
            current_unit_player = unit_on_zone['player']
            other_player_id = 1 if current_unit_player == 2 else 2
            
            enemy_on_zone = False
            for uid, unit in st.session_state.units.items():
                if unit['player'] == other_player_id and (unit['col'], unit['row']) == zone_coords:
                    enemy_on_zone = True
                    break
            
            if not enemy_on_zone:
                st.session_state.mystic_zone_control[zone_coords] = current_unit_player
            else:
                st.session_state.mystic_zone_control[zone_coords] = None # Contested
        else:
            st.session_state.mystic_zone_control[zone_coords] = None

def check_mystic_zone_victory(player_id):
    controlled_zones_count = 0
    for zone_coords, controller_id in st.session_state.mystic_zone_control.items():
        if controller_id == player_id:
            controlled_zones_count += 1
            
    if controlled_zones_count >= 3:
        add_event_message(f"🎉🎉🎉 Jogador {player_id} VENCEU! Controla 3 Zonas Místicas! 🎉🎉🎉", is_critical=True)
        st.session_state.game_over = True
        return True
    return False


def move_unit_streamlit(unit_id_str, target_coords):
    unit = st.session_state.units.get(unit_id_str)
    current_player_id = st.session_state.current_turn
    
    if not unit:
        add_event_message(f"Erro: Unidade com ID {unit_id_str} não encontrada.")
        return False
    if unit['player'] != current_player_id:
        add_event_message(f"Erro: Unidade {unit['type']} (ID: {unit_id_str}) não pertence ao Jogador {current_player_id}.")
        return False
    if unit['type'] == 'Arcane Core':
        add_event_message(f"Erro: Núcleo Arcano é imóvel.")
        return False

    if unit['mv_remaining'] <= 0:
        add_event_message(f"Erro: Unidade {unit['type']} (ID: {unit_id_str}) não tem pontos de movimento restantes.")
        return False

    if not is_valid_coord(target_coords):
        add_event_message(f"Erro: Coordenadas alvo {target_coords} são inválidas.")
        return False

    target_uid, target_occupant = get_unit_at_coords_streamlit(target_coords)
    
    if target_occupant: # Se há alguma unidade no alvo
        add_event_message(f"Erro: Hexágono {target_coords} já está ocupado por {target_occupant['type']}.")
        return False
    
    start_coords = (unit['col'], unit['row'])
    distance = calculate_distance(start_coords, target_coords) # A distância agora é o custo direto

    if distance == float('inf'):
        add_event_message(f"Erro: Não é possível alcançar {target_coords} a partir de {start_coords} (caminho inválido).")
        return False

    movement_cost = distance

    if movement_cost > unit['mv_remaining']:
        add_event_message(f"Erro: Unidade {unit['type']} (ID: {unit_id_str}) não tem movimento suficiente ({movement_cost} necessário, {unit['mv_remaining']} restante).")
        return False
    
    # Guarda as coordenadas antes de mover para o feedback visual
    st.session_state.last_moved_unit = unit_id_str
    st.session_state.last_move_from = start_coords
    st.session_state.last_move_to = target_coords

    unit['col'] = target_coords[0]
    unit['row'] = target_coords[1]
    unit['mv_remaining'] -= movement_cost
    
    add_event_message(f"{unit['type']} (ID: {unit_id_str}) moveu-se para {target_coords}. {unit['mv_remaining']} Mv restante.")
    update_mystic_zone_control() 
    return True

def attack_unit_streamlit(attacker_id_str, target_id_str):
    attacker = st.session_state.units.get(attacker_id_str)
    target = st.session_state.units.get(target_id_str)
    current_player_id = st.session_state.current_turn

    if not attacker:
        add_event_message(f"Erro de Ataque: Unidade atacante com ID {attacker_id_str} não encontrada.")
        return False
    if not target:
        add_event_message(f"Erro de Ataque: Unidade alvo com ID {target_id_str} não encontrada.")
        return False

    if attacker['player'] != current_player_id:
        add_event_message(f"Erro de Ataque: Unidade {attacker['type']} (ID: {attacker_id_str}) não pertence ao Jogador {current_player_id}.")
        return False
    if attacker['type'] == 'Arcane Core':
        add_event_message(f"Erro de Ataque: Núcleo Arcano não pode atacar.")
        return False
    
    if target['player'] == current_player_id:
        add_event_message(f"Erro de Ataque: Não podes atacar uma unidade aliada (ID: {target_id_str}).")
        return False
    if attacker_id_str == target_id_str:
        add_event_message(f"Erro de Ataque: Não podes atacar a própria unidade (ID: {attacker_id_str}).")
        return False

    if attacker['ap_remaining'] <= 0:
        add_event_message(f"Erro de Ataque: Unidade {attacker['type']} (ID: {attacker_id_str}) não tem pontos de ação (AP) restantes.")
        return False

    attacker_coords = (attacker['col'], attacker['row'])
    target_coords = (target['col'], target['row'])
    distance = calculate_distance(attacker_coords, target_coords)

    if distance == float('inf') or distance > attacker['range']:
        add_event_message(f"Erro de Ataque: Alvo {target_id_str} fora do alcance de {attacker['type']} (Alcance: {attacker['range']}, Distância: {distance}).")
        return False

    damage = attacker['atk']
    target['hp'] -= damage
    attacker['ap_remaining'] -= 1

    # Guarda informação do ataque para feedback visual
    st.session_state.last_attack_info = {
        'attacker_coords': attacker_coords,
        'target_coords': target_coords,
        'target_id': target_id_str,
        'damage_dealt': damage
    }

    add_event_message(f"{attacker['type']} (ID: {attacker_id_str}) atacou {target['type']} (ID: {target_id_str}) causando {damage} de dano.")

    if target['hp'] <= 0:
        add_event_message(f"Unidade {target_id_str} ({target['type']}) foi destruída!")
        del st.session_state.units[target_id_str]

        if target['type'] == 'Arcane Core':
            add_event_message(f"🎉🎉🎉 Jogador {current_player_id} VENCEU! O Núcleo Arcano do inimigo foi destruído! 🎉🎉🎉", is_critical=True)
            st.session_state.game_over = True
            
    update_mystic_zone_control() 
    return True

# --- CARD LOGIC FUNCTIONS ---

def play_card_streamlit(card_name, target_coords=None, target_unit_id=None):
    current_player_id = st.session_state.current_turn
    card_info = CARD_DATA.get(card_name)
    
    if card_name not in st.session_state.hand[current_player_id]:
        add_event_message(f"Erro: Carta '{card_name}' não está na tua mão.")
        return False
    
    if not card_info:
        add_event_message(f"Erro: Informações da carta '{card_name}' não encontradas.")
        return False
    
    cost = card_info.get('cost', 0)
    if st.session_state.mana[current_player_id] < cost:
        add_event_message(f"Erro: Mana insuficiente para jogar '{card_name}' (Custo: {cost}, Mana: {st.session_state.mana[current_player_id]}).")
        return False

    success = False
    if card_info['type'] == 'invocation':
        if target_coords:
            success = invoke_unit_from_card(card_info['unit_type'], target_coords, current_player_id)
            if success:
                st.session_state.mana[current_player_id] -= cost
                st.session_state.hand[current_player_id].remove(card_name)
                add_event_message(f"Carta '{card_name}' jogada com sucesso! {cost} Mana deduzida.")
                st.session_state.invocation_mode = False
                st.session_state.unit_type_to_invoke = None
                st.session_state.valid_invocations = set()
        else:
            st.session_state.invocation_mode = True
            st.session_state.unit_type_to_invoke = card_info['unit_type']
            st.session_state.valid_invocations = get_valid_invocation_hexes(current_player_id, card_info['unit_type'])
            add_event_message(f"Selecione um hexágono verde no tabuleiro para invocar {card_info['unit_type']}.")
            st.session_state.selected_card_in_play = card_name
            success = True
            st.rerun()
            
    elif card_info['type'] == 'spell':
        success = cast_spell_from_card(card_name, target_coords, target_unit_id, current_player_id)
        if success:
            st.session_state.mana[current_player_id] -= cost
            st.session_state.hand[current_player_id].remove(card_name)
            add_event_message(f"Carta '{card_name}' jogada com sucesso! {cost} Mana deduzida.")
            
    return success

def invoke_unit_from_card(unit_type, target_coords, player_id):
    if not is_valid_coord(target_coords):
        add_event_message(f"Erro de Invocação: Coordenadas '{target_coords}' são inválidas.")
        return False
    
    uid_at_target, unit_at_target = get_unit_at_coords_streamlit(target_coords)
    if unit_at_target:
        add_event_message(f"Erro de Invocação: Hexágono {target_coords} já está ocupado por {unit_at_target['type']}.")
        return False
        
    unit_base_data = UNIT_DATA.get(unit_type)
    if not unit_base_data:
        add_event_message(f"Erro de Invocação: Tipo de unidade '{unit_type}' não encontrado nos dados.")
        return False

    player_core = None
    for uid, unit in st.session_state.units.items():
        if unit['player'] == player_id and unit['type'] == 'Arcane Core':
            player_core = unit
            break
    
    if not player_core:
        add_event_message("Erro de Invocação: Núcleo Arcano do jogador não encontrado.")
        return False

    core_coords = (player_core['col'], player_core['row'])
    distance_from_core = calculate_distance(core_coords, target_coords)

    if distance_from_core > 2 or distance_from_core == float('inf'): # Raio de 2 hexágonos
        add_event_message(f"Erro de Invocação: Unidade deve ser invocada a até 2 hexágonos do seu Núcleo Arcano. Distância: {distance_from_core}.")
        return False

    new_unit_id = str(st.session_state.next_unit_id)
    st.session_state.next_unit_id += 1

    new_unit = {
        'type': unit_type,
        'player': player_id,
        'col': target_coords[0],
        'row': target_coords[1],
        'hp': unit_base_data['hp'],
        'max_hp': unit_base_data['hp'], 
        'mv_remaining': 0, 
        'ap_remaining': 0, 
        'max_mv': unit_base_data['mv'], 
        'atk': unit_base_data['atk'],
        'range': unit_base_data['range'],
    }
    
    st.session_state.units[new_unit_id] = new_unit
    add_event_message(f"Unidade '{unit_type}' (ID: {new_unit_id}) invocada para {target_coords}. Ela estará pronta para agir no teu próximo turno.")
    update_mystic_zone_control() 
    return True

def cast_spell_from_card(card_name, target_coords, target_unit_id, player_id):
    success = False
    
    if card_name == "Feitiço: Pulso Etéreo":
        if not target_unit_id:
            add_event_message("Erro: Pulso Etéreo requer um alvo.")
            return False
        
        target_unit = st.session_state.units.get(target_unit_id)
        if not target_unit:
            add_event_message(f"Erro: Alvo '{target_unit_id}' não encontrado para Pulso Etéreo.")
            return False
            
        attacker_core = next((unit for uid, unit in st.session_state.units.items() 
                              if unit['type'] == 'Arcane Core' and unit['player'] == player_id), None)
        if not attacker_core:
            add_event_message("Erro: Não foi possível encontrar o teu Núcleo Arcano para determinar o alcance do feitiço.")
            return False
            
        distance = calculate_distance((attacker_core['col'], attacker_core['row']), (target_unit['col'], target_unit['row']))
        
        if distance > 4 or distance == float('inf'): # Exemplo: Alcance de 4 para Pulso Etéreo
            add_event_message(f"Erro: Alvo '{target_unit_id}' fora do alcance de Pulso Etéreo (Max 4, Distância: {distance}).")
            return False

        if target_unit['player'] == player_id:
            add_event_message("Erro: Não podes usar Pulso Etéreo numa unidade aliada.")
            return False

        damage = 2
        target_unit['hp'] -= damage
        # Feedback visual para feitiços
        st.session_state.last_attack_info = {
            'attacker_coords': (attacker_core['col'], attacker_core['row']),
            'target_coords': (target_unit['col'], target_unit['row']),
            'target_id': target_unit_id,
            'damage_dealt': damage
        }
        add_event_message(f"Pulso Etéreo causa {damage} de dano a {target_unit['type']} (ID: {target_unit_id}).")
        
        if target_unit['hp'] <= 0:
            add_event_message(f"Unidade {target_unit_id} ({target_unit['type']}) foi destruída!")
            del st.session_state.units[target_unit_id]
            if target_unit['type'] == 'Arcane Core':
                add_event_message(f"🎉🎉🎉 Jogador {player_id} VENCEU! O Núcleo Arcano do inimigo foi destruído! 🎉🎉🎉", is_critical=True)
        success = True

    elif card_name == "Feitiço: Escudo Etéreo":
        if not target_unit_id:
            add_event_message("Erro: Escudo Etéreo requer um alvo.")
            return False

        target_unit = st.session_state.units.get(target_unit_id)
        if not target_unit:
            add_event_message(f"Erro: Alvo '{target_unit_id}' não encontrado para Escudo Etéreo.")
            return False
        
        if target_unit['player'] != player_id:
            add_event_message("Erro: Não podes usar Escudo Etéreo numa unidade inimiga.")
            return False

        shield_amount = 3
        target_unit['hp'] = min(target_unit['max_hp'], target_unit['hp'] + shield_amount) 
        add_event_message(f"Escudo Etéreo aplicado a {target_unit['type']} (ID: {target_unit_id}). Cura {shield_amount} HP.")
        success = True

    elif card_name == "Feitiço: Reflexo Estratégico":
        cards_drawn = 0
        for _ in range(2):
            if len(st.session_state.hand[player_id]) < 7: 
                new_card = random.choice(list(CARD_DATA.keys()))
                st.session_state.hand[player_id].append(new_card)
                cards_drawn += 1
            else:
                add_event_message("Mão cheia, não foi possível comprar mais cartas.")
                break
        add_event_message(f"Reflexo Estratégico jogado. Compraste {cards_drawn} cartas.")
        success = True

    elif card_name == "Feitiço: Translocação Rápida":
        if not target_unit_id or not target_coords:
            add_event_message("Erro: Translocação Rápida requer uma unidade alvo e uma posição alvo.")
            return False

        unit_to_move = st.session_state.units.get(target_unit_id)
        if not unit_to_move or unit_to_move['player'] != player_id:
            add_event_message(f"Erro: Unidade '{target_unit_id}' não encontrada ou não é aliada para Translocação Rápida.")
            return False

        uid_at_target, occupant_at_target = get_unit_at_coords_streamlit(target_coords)
        if occupant_at_target:
            add_event_message(f"Erro: Hexágono {target_coords} está ocupado para Translocação Rápida.")
            return False

        current_unit_coords = (unit_to_move['col'], unit_to_move['row'])
        distance = calculate_distance(current_unit_coords, target_coords)
        if distance != 1:
            add_event_message(f"Erro: Translocação Rápida move apenas 1 hexágono. Distância para {target_coords} é {distance}.")
            return False
        
        # Guarda as coordenadas antes de mover para o feedback visual do feitiço
        st.session_state.last_moved_unit = target_unit_id
        st.session_state.last_move_from = current_unit_coords
        st.session_state.last_move_to = target_coords

        unit_to_move['col'] = target_coords[0]
        unit_to_move['row'] = target_coords[1]
        add_event_message(f"Unidade {unit_to_move['type']} (ID: {target_unit_id}) translocada para {target_coords}.")
        success = True

    else:
        add_event_message(f"Erro: Feitiço '{card_name}' não implementado ou inválido.")
        return False
        
    update_mystic_zone_control() 
    return success

# --- AI LOGIC FUNCTIONS ---

def get_player_units(player_id):
    """Retorna um dicionário de unidades pertencentes a um jogador específico."""
    return {uid: unit for uid, unit in st.session_state.units.items() if unit['player'] == player_id}

def find_targets_in_range(attacker_id_str):
    """Encontra unidades inimigas dentro do alcance do atacante."""
    attacker = st.session_state.units.get(attacker_id_str)
    if not attacker or attacker['ap_remaining'] <= 0 or attacker.get('atk', 0) <= 0:
        return []

    attacker_coords = (attacker['col'], attacker['row'])
    enemy_player_id = 1 if attacker['player'] == 2 else 2
    enemy_units = get_player_units(enemy_player_id)
    
    potential_targets = []
    for target_uid, target_unit in enemy_units.items():
        target_coords = (target_unit['col'], target_unit['row'])
        distance = calculate_distance(attacker_coords, target_coords)
        
        if distance <= attacker.get('range', 0) and distance != float('inf'):
            potential_targets.append(target_uid)
            
    return potential_targets

def find_closest_enemy_unit_coords(ai_unit_coords, enemy_player_id):
    """Encontra as coordenadas da unidade inimiga mais próxima."""
    enemy_units = get_player_units(enemy_player_id)
    
    if not enemy_units:
        return None, float('inf')

    min_distance = float('inf')
    closest_coords = None

    for enemy_uid, enemy_unit in enemy_units.items():
        enemy_coords = (enemy_unit['col'], enemy_unit['row'])
        distance = calculate_distance(ai_unit_coords, enemy_coords)
        if distance < min_distance:
            min_distance = distance
            closest_coords = enemy_coords
            
    return closest_coords, min_distance

def ai_turn_logic():
    ai_player_id = 2
    ai_units_copy = list(get_player_units(ai_player_id).keys())
    enemy_player_id = 1

    add_event_message("--- Turno da AI (Jogador 2) ---")

    update_mystic_zone_control() 

    random.shuffle(ai_units_copy) 

    for unit_id in ai_units_copy:
        if unit_id not in st.session_state.units:
            continue

        unit = st.session_state.units[unit_id]

        if unit['player'] != ai_player_id or unit['type'] == 'Arcane Core':
            continue

        # PRIORIDADE 1: Atacar se possível
        if unit['ap_remaining'] > 0 and unit.get('atk', 0) > 0:
            targets_in_range = find_targets_in_range(unit_id)
            if targets_in_range:
                target_to_attack_id = targets_in_range[0] 
                attack_unit_streamlit(unit_id, target_to_attack_id)
                unit['ap_remaining'] = 0 
                continue 

        # PRIORIDADE 2: Mover-se em direção ao inimigo mais próximo OU para uma zona mística livre/contestada
        if unit['mv_remaining'] > 0:
            current_coords = (unit['col'], unit['row'])
            
            target_move_coords = None
            min_dist_to_objective = float('inf')

            for zone_coords in MYSTIC_ZONES:
                controller = st.session_state.mystic_zone_control.get(zone_coords)
                if controller is None or controller == enemy_player_id: 
                    dist = calculate_distance(current_coords, zone_coords)
                    if dist < min_dist_to_objective:
                        min_dist_to_objective = dist
                        target_move_coords = zone_coords

            if target_move_coords and min_dist_to_objective <= unit['mv_remaining']:
                best_next_move = None
                smallest_remaining_dist = float('inf')

                for neighbor_coords in get_adjacent_hexes(current_coords):
                    occupant_uid, occupant_data = get_unit_at_coords_streamlit(neighbor_coords)
                    if occupant_data: 
                        continue
                    
                    dist_to_target_from_neighbor = calculate_distance(neighbor_coords, target_move_coords)
                    if dist_to_target_from_neighbor < smallest_remaining_dist:
                        if calculate_distance(current_coords, neighbor_coords) <= unit['mv_remaining']:
                             smallest_remaining_dist = dist_to_target_from_neighbor
                             best_next_move = neighbor_coords
                
                if best_next_move:
                    move_unit_streamlit(unit_id, best_next_move)
                    continue 
            
            else:
                closest_enemy_coords, min_dist_to_enemy = find_closest_enemy_unit_coords(current_coords, enemy_player_id)
                
                if closest_enemy_coords and min_dist_to_enemy > 0:
                    best_next_move = None
                    best_distance_reduction = -1

                    for neighbor_coords in get_adjacent_hexes(current_coords):
                        occupant_uid, occupant_data = get_unit_at_coords_streamlit(neighbor_coords)
                        if occupant_data: 
                            continue

                        dist_to_target_from_neighbor = calculate_distance(neighbor_coords, closest_enemy_coords)
                        current_dist = calculate_distance(current_coords, closest_enemy_coords)
                        reduction = current_dist - dist_to_target_from_neighbor

                        if reduction > best_distance_reduction and unit['mv_remaining'] >= 1:
                            best_distance_reduction = reduction
                            best_next_move = neighbor_coords
                    
                    if best_next_move:
                        move_unit_streamlit(unit_id, best_next_move)
                
    add_event_message("--- Fim do Turno da AI ---")

# --- TURN MANAGEMENT FUNCTIONS ---

def start_turn_streamlit():
    player_id = st.session_state.current_turn
    
    update_mystic_zone_control()

    player_to_check_for_victory = 1 if player_id == 2 else 2

    if check_mystic_zone_victory(player_to_check_for_victory):
        st.session_state.game_over = True 
        st.rerun() 
        return 

    st.session_state.mana[player_id] += 1
    add_event_message(f"--- Turno {st.session_state.turn_number} do Jogador {player_id} Começa ---")
    
    if player_id == 1 and len(st.session_state.hand[1]) < 7:
        new_card = random.choice(list(CARD_DATA.keys()))
        st.session_state.hand[1].append(new_card)
        add_event_message(f"Jogador {player_id} desenhou uma carta: {new_card}.")
    elif player_id == 1 and len(st.session_state.hand[1]) >= 7:
        add_event_message(f"Jogador {player_id} não desenhou carta (mão cheia).")
        
    add_event_message(f"Jogador {player_id} agora tem {st.session_state.mana[player_id]} Mana.")

    for uid, unit in st.session_state.units.items():
        if unit['player'] == player_id:
            unit['mv_remaining'] = unit['max_mv'] 
            unit['ap_remaining'] = 1

def end_turn_streamlit():
    add_event_message(f"--- Turno do Jogador {st.session_state.current_turn} Termina ---")
    
    player_id = st.session_state.current_turn
    
    update_mystic_zone_control()

    if len(st.session_state.hand[player_id]) > 7:
        add_event_message(f"Mão do Jogador {player_id} está cheia. Descartar cartas (lógica a implementar).")

    st.session_state.current_turn = 2 if st.session_state.current_turn == 1 else 1
    st.session_state.turn_number += 1
    st.session_state.selected_unit = None 
    st.session_state.valid_moves = set() 
    st.session_state.valid_attacks = set() 
    st.session_state.invocation_mode = False
    st.session_state.unit_type_to_invoke = None
    st.session_state.valid_invocations = set()
    # Limpar estados de feedback visual de turnos anteriores
    st.session_state.last_moved_unit = None
    st.session_state.last_move_from = None
    st.session_state.last_move_to = None
    st.session_state.last_attack_info = None

    if st.session_state.current_turn == 2 and not st.session_state.game_over:
        ai_turn_logic()
        st.session_state.current_turn = 1
        add_event_message("--- Turno da AI concluído. Turno do Jogador 1 começa ---")
        if not st.session_state.game_over:
            start_turn_streamlit() 
    elif not st.session_state.game_over: 
        start_turn_streamlit() 

def get_valid_moves_for_unit(unit_id):
    unit = st.session_state.units.get(unit_id)
    if not unit or unit['mv_remaining'] <= 0 or unit['type'] == 'Arcane Core':
        return set()

    start_coords = (unit['col'], unit['row'])
    max_mv = unit['mv_remaining']
    
    q = collections.deque([(start_coords, 0)])
    reachable_hexes = set()
    visited_with_cost = {start_coords: 0}

    while q:
        current_coords, current_cost = q.popleft()
        
        for neighbor in get_adjacent_hexes(current_coords):
            occupant_uid, occupant_data = get_unit_at_coords_streamlit(neighbor)
            if occupant_data: 
                continue 
            
            move_cost = 1 

            new_total_cost = current_cost + move_cost
            
            if neighbor in visited_with_cost and new_total_cost >= visited_with_cost[neighbor]:
                continue

            if new_total_cost <= max_mv:
                visited_with_cost[neighbor] = new_total_cost
                reachable_hexes.add(neighbor)
                q.append((neighbor, new_total_cost))
                
    return reachable_hexes

def get_valid_attack_targets_for_unit(unit_id):
    unit = st.session_state.units.get(unit_id)
    if not unit or unit['ap_remaining'] <= 0 or unit.get('atk', 0) <= 0 or unit['type'] == 'Arcane Core':
        return set()

    attacker_coords = (unit['col'], unit['row'])
    attack_range = unit['range']
    enemy_player_id = 1 if unit['player'] == 2 else 2
    
    valid_targets_coords = set()
    for target_uid, target_unit in st.session_state.units.items():
        if target_unit['player'] == enemy_player_id:
            target_coords = (target_unit['col'], target_unit['row'])
            distance = calculate_distance(attacker_coords, target_coords)
            if distance <= attack_range and distance != float('inf'):
                valid_targets_coords.add(target_coords)
                
    return valid_targets_coords

def get_valid_invocation_hexes(player_id, unit_type):
    valid_hexes = set()
    player_core = None
    for uid, unit in st.session_state.units.items():
        if unit['player'] == player_id and unit['type'] == 'Arcane Core':
            player_core = unit
            break
    
    if not player_core:
        return set()

    core_coords = (player_core['col'], player_core['row'])
    
    for col_char in BOARD_COLS:
        for row_int in BOARD_ROWS:
            current_coords = (col_char, row_int)
            
            uid_at_target, unit_at_target = get_unit_at_coords_streamlit(current_coords)
            if unit_at_target:
                continue

            distance_from_core = calculate_distance(core_coords, current_coords)
            if distance_from_core <= 2 and distance_from_core != float('inf'):
                valid_hexes.add(current_coords)
                
    return valid_hexes


# --- UI RENDERING ---

def create_empty_board():
    return { (c, r): "" for c in BOARD_COLS for r in BOARD_ROWS }

def render_board():
    board_display = create_empty_board()
    
    # Adicionar Zonas Místicas e seu controlo
    for (col, row) in MYSTIC_ZONES:
        zone_coords = (col, row)
        controller = st.session_state.mystic_zone_control.get(zone_coords)
        if controller == 1:
            board_display[zone_coords] = "🔵" 
        elif controller == 2:
            board_display[zone_coords] = "🟠" 
        else:
            board_display[zone_coords] = "🟪" 

    # Preencher com unidades
    for uid, unit in st.session_state.units.items():
        pos = (unit['col'], unit['row'])
        
        symbol = unit['type'][0] 
        if unit['type'] == "Arcane Core": symbol = "N"
        elif unit['type'] == "Sentinela Arcana": symbol = "S"
        elif unit['type'] == "Guardião": symbol = "G"
        elif unit['type'] == "Brutamontes": symbol = "T"
        elif unit['type'] == "Batedor": symbol = "B"
        elif unit['type'] == "Adeptus": symbol = "A"

        hp_indicator = f"({unit['hp']})"
        
        if pos in MYSTIC_ZONES:
            zone_symbol = board_display[pos] 
            board_display[pos] = f"{zone_symbol}{unit['player']}{symbol}{hp_indicator}"
        else:
            board_display[pos] = f"{unit['player']}{symbol}{hp_indicator}"
    
    for r in reversed(BOARD_ROWS): 
        cols_for_row = st.columns(len(BOARD_COLS))
        for i, col_char in enumerate(BOARD_COLS):
            coords = (col_char, r)
            cell_content = board_display[coords] 
            
            button_label = ""
            button_help_text = f"Coordenadas: {col_char}{r}"

            if coords in MYSTIC_ZONES:
                controller = st.session_state.mystic_zone_control.get(coords)
                if controller == 1:
                    button_label_prefix = "🔵"
                    button_help_text += " (Zona Mística - Controlada pelo Jogador 1)"
                elif controller == 2:
                    button_label_prefix = "🟠"
                    button_help_text += " (Zona Mística - Controlada pelo Jogador 2)"
                else:
                    button_label_prefix = "🟪"
                    button_help_text += " (Zona Mística - Contestada/Livre)"
                
                if cell_content.startswith(("🔵", "🟠", "🟪")):
                    button_label = cell_content 
                else:
                    button_label = button_label_prefix 
            elif cell_content: 
                button_label = cell_content
                unit_id_at_coords, unit_obj_at_coords = get_unit_at_coords_streamlit(coords)
                if unit_obj_at_coords:
                    button_help_text += (
                        f"\nUnidade: {unit_obj_at_coords['type']} (ID: {unit_id_at_coords})"
                        f"\nHP: {unit_obj_at_coords['hp']}/{unit_obj_at_coords['max_hp']}"
                        f"\nMV: {unit_obj_at_coords['mv_remaining']}/{unit_obj_at_coords['max_mv']}"
                        f"\nAP: {unit_obj_at_coords['ap_remaining']}"
                    )
            else: 
                button_label = f"{col_char}{r}" 
            
            # --- Lógica de feedback visual para movimentos/ataques/invocações ---
            # PRIORIDADE 1: Unidade Selecionada
            if st.session_state.selected_unit:
                selected_unit_obj = st.session_state.units.get(st.session_state.selected_unit)
                if selected_unit_obj and (selected_unit_obj['col'], selected_unit_obj['row']) == coords:
                    button_label = f"⭐ {button_label}" # Adiciona um ícone à unidade selecionada
                    button_help_text += " (Unidade Selecionada)"
                # PRIORIDADE 2: Invocação Válida (se não for a unidade selecionada)
                elif st.session_state.invocation_mode and coords in st.session_state.valid_invocations:
                    button_label = f"✨ {button_label}" 
                    button_help_text += " (Invocação Válida)"
                # PRIORIDADE 3: Movimento/Ataque Válido (se não for a unidade selecionada ou modo invocação)
                elif selected_unit_obj and selected_unit_obj['player'] == st.session_state.current_turn: 
                    if coords in st.session_state.valid_moves:
                        button_label = f"🟢 {button_label}" 
                        button_help_text += " (Movimento Válido)"
                    elif coords in st.session_state.valid_attacks:
                        button_label = f"🔴 {button_label}" 
                        button_help_text += " (Alvo de Ataque Válido)"
            # PRIORIDADE 4: Modo Invocação (se nenhuma unidade estiver selecionada)
            elif st.session_state.invocation_mode and coords in st.session_state.valid_invocations:
                button_label = f"✨ {button_label}" 
                button_help_text += " (Invocação Válida)"

            # Feedback visual para a última ação (aplicado por cima de tudo, mas pode ser ajustado)
            if st.session_state.last_moved_unit:
                if coords == st.session_state.last_move_from:
                    button_label = f"⚪ {button_label}" # Hexágono de origem
                if coords == st.session_state.last_move_to:
                    button_label = f"✨ {button_label}" # Hexágono de destino
            
            if st.session_state.last_attack_info:
                if coords == st.session_state.last_attack_info['attacker_coords']:
                    button_label = f"💥 {button_label}" # Atacante
                if coords == st.session_state.last_attack_info['target_coords']:
                    # Só aplica se a unidade ainda existir, caso contrário já foi removida
                    if st.session_state.last_attack_info['target_id'] in st.session_state.units:
                        button_label = f"💔 {button_label}" # Alvo que levou dano
                    else: # Unidade destruída
                        button_label = f"💀 {button_label}" # Alvo destruído
            
            with cols_for_row[i]:
                if st.button(button_label, key=f"hex_{col_char}{r}", help=button_help_text, use_container_width=True):
                    # Limpa o feedback visual das últimas ações antes de processar um novo clique
                    st.session_state.last_moved_unit = None
                    st.session_state.last_move_from = None
                    st.session_state.last_move_to = None
                    st.session_state.last_attack_info = None

                    if st.session_state.game_over:
                        add_event_message("O jogo terminou!")
                        st.rerun()
                    elif st.session_state.invocation_mode:
                        if coords in st.session_state.valid_invocations:
                            if play_card_streamlit(st.session_state.selected_card_in_play, target_coords=coords):
                                st.rerun()
                        else:
                            add_event_message("Não podes invocar aqui. Seleciona um hexágono verde válido ou clica 'Cancelar Invocação'.")
                            st.rerun()
                    elif st.session_state.selected_unit:
                        selected_unit_id = st.session_state.selected_unit
                        selected_unit_obj = st.session_state.units.get(selected_unit_id)

                        if selected_unit_obj and selected_unit_obj['player'] == st.session_state.current_turn:
                            if coords in st.session_state.valid_moves:
                                move_unit_streamlit(selected_unit_id, coords)
                                st.session_state.selected_unit = None
                                st.session_state.valid_moves = set()
                                st.session_state.valid_attacks = set()
                                st.rerun()
                            elif coords in st.session_state.valid_attacks:
                                target_uid, _ = get_unit_at_coords_streamlit(coords)
                                if target_uid:
                                    attack_unit_streamlit(selected_unit_id, target_uid)
                                    st.session_state.selected_unit = None
                                    st.session_state.valid_moves = set()
                                    st.session_state.valid_attacks = set()
                                    st.rerun()
                                else:
                                    add_event_message("Erro: Nenhuma unidade inimiga para atacar no hexágono selecionado.")
                                    st.rerun()
                            else:
                                add_event_message(f"Movimento ou ataque inválido para {coords}. Clica na unidade selecionada novamente para cancelar.")
                                st.rerun()
                        else: # Clique em algo que não a própria unidade selecionada mas no modo de unidade selecionada
                            add_event_message("Clica numa posição válida para mover/atacar, ou clica na unidade selecionada para desmarcar.")
                            st.rerun()
                    else: # Nenhuma unidade selecionada, tenta selecionar uma
                        clicked_unit_id, clicked_unit_obj = get_unit_at_coords_streamlit(coords)
                        if clicked_unit_id and clicked_unit_obj['player'] == st.session_state.current_turn:
                            st.session_state.selected_unit = clicked_unit_id
                            st.session_state.valid_moves = get_valid_moves_for_unit(clicked_unit_id)
                            st.session_state.valid_attacks = get_valid_attack_targets_for_unit(clicked_unit_id)
                            add_event_message(f"Unidade {clicked_unit_obj['type']} (ID: {clicked_unit_id}) selecionada.")
                            st.rerun()
                        elif clicked_unit_id and clicked_unit_obj['player'] != st.session_state.current_turn:
                            add_event_message("Não podes selecionar unidades inimigas.")
                            st.rerun()
                        else:
                            add_event_message("Nenhuma unidade para selecionar neste hexágono.")
                            st.rerun()

# Streamlit page configuration
st.set_page_config(layout="wide")
st.title("🎲 Arcanum Tactics - Protótipo Jogável")

st.sidebar.title("📖 Índice do Jogo")
st.sidebar.markdown("""
- **Objetivo**: Destruir o Arcane Core inimigo ou **controlar 3 Zonas Místicas no início do turno do adversário**.
- **Zonas Místicas**: Controladas ao ter uma unidade no hexágono sem inimigos. Se ambos tiverem, está contestada.
- **Movimento**: Cada unidade tem alcance de movimento (MV). Um hexágono **não pode ser ocupado por mais de uma unidade.**
- **Ataque**: Unidades atacam usando AP e alcance (Range).
- **Cartas**: Usam mana. Incluem invocações e feitiços.
- **Invocação**: Unidades podem ser invocadas **apenas num raio de 2 hexágonos do teu Núcleo Arcano** e em hexágonos vazios.
- **Fadiga de Invocação**: Unidades invocadas **não podem mover-se ou atacar no turno em que são invocadas**. Elas estarão prontas para agir no próximo turno do jogador.
- **Turno**: 1. Repor mana e carta · 2. Mover/Atacar/Usar Cartas · 3. Fim
""")

with st.expander("📊 Estatísticas das Unidades", expanded=False):
    st.dataframe(pd.DataFrame(UNIT_DATA).T)

with st.expander("🃏 Cartas Disponíveis", expanded=False):
    st.dataframe(pd.DataFrame(CARD_DATA).T)

st.subheader(f"Turno {st.session_state.turn_number} - Jogador {st.session_state.current_turn}")

if st.session_state.game_over:
    st.success(st.session_state.game_message)
    if st.button("Reiniciar Jogo"):
        st.session_state.game_initialized = False
        st.rerun()
    st.stop()
else:
    update_mystic_zone_control() 
    # st.info(st.session_state.game_message) # Esta mensagem será agora exibida no log, mas mantida para mensagens críticas

col1, col2 = st.columns([2, 1])

with col1:
    render_board() 
    
    st.markdown("---")
    st.subheader("Informação das Unidades no Tabuleiro:")
    for uid in sorted(st.session_state.units.keys(), key=lambda x: int(x)):
        unit = st.session_state.units[uid]
        player_tag = "Tu" if unit['player'] == 1 else "AI"
        st.write(f"**ID: {uid}** | {unit['type']} ({player_tag}) | Pos: {unit['col']}{unit['row']} | HP: {unit['hp']}/{unit['max_hp']} | MV: {unit['mv_remaining']}/{unit['max_mv']} | AP: {unit['ap_remaining']}")


with col2:
    st.subheader("👑 As tuas unidades (Jogador 1)")
    st.markdown("**(Seleciona as tuas unidades clicando no tabuleiro)**")

    if st.session_state.invocation_mode:
        st.markdown(f"**Modo de Invocação Ativo:** Clica num hexágono `✨ VERDE` para invocar **{st.session_state.unit_type_to_invoke}**.")
        if st.button("Cancelar Invocação", key="cancel_invocation_button"):
            st.session_state.invocation_mode = False
            st.session_state.unit_type_to_invoke = None
            st.session_state.valid_invocations = set()
            add_event_message("Invocação cancelada.")
            st.rerun()

    elif st.session_state.selected_unit:
        selected = st.session_state.units[st.session_state.selected_unit]
        st.markdown(f"**Unidade selecionada:** {selected['type']} (ID: {st.session_state.selected_unit}, {selected['col']}{selected['row']})")
        st.markdown(f"HP: {selected['hp']}/{selected['max_hp']}, MV: {selected['mv_remaining']}/{selected['max_mv']}, AP: {selected['ap_remaining']}")
        
        st.markdown("---")
        st.markdown("**(Clica num hexágono `🟢 VERDE` para mover, ou num `🔴 VERMELHO` para atacar)**")
        
        if st.button("Cancelar Seleção", key="cancel_selection_button"):
            st.session_state.selected_unit = None
            st.session_state.valid_moves = set()
            st.session_state.valid_attacks = set()
            add_event_message("Seleção de unidade cancelada.")
            st.rerun()

    st.markdown("---")
    st.subheader("🃏 Cartas na mão")
    current_player_hand = st.session_state.hand.get(st.session_state.current_turn, [])
    
    st.markdown(f"**Mana:** {st.session_state.mana[st.session_state.current_turn]}")

    selected_card_to_play = st.selectbox(
        "Seleciona uma carta para jogar:",
        ["Selecione uma carta"] + current_player_hand,
        key="card_selector",
        disabled=st.session_state.invocation_mode 
    )

    if selected_card_to_play != "Selecione uma carta":
        card_details = CARD_DATA.get(selected_card_to_play, {})
        st.write(f"**{selected_card_to_play}** (Custo: {card_details.get('cost', '?')} Mana)")
        st.write(f"Descrição: {card_details.get('desc', '')}")
        
        card_type = card_details.get('type')

        if card_type == "invocation":
            if st.button(f"Ativar Invocação: {card_details.get('unit_type')}", key="activate_invocation_mode"):
                play_card_streamlit(selected_card_to_play) 

        elif card_type == "spell":
            # Campos de entrada para alvo de feitiço
            target_col_spell = st.text_input("Coluna alvo (ex: F):", key="spell_col_input", max_chars=1)
            target_row_spell = st.number_input("Linha alvo (ex: 7):", min_value=BOARD_ROWS[0], max_value=BOARD_ROWS[-1], step=1, key="spell_row_input")
            target_unit_id_spell = st.text_input("ID de unidade alvo (opcional, ex: 5):", key="spell_unit_id_input", value="")

            if st.button(f"Lançar Feitiço: {selected_card_to_play}", key="play_spell_button"):
                coords_to_pass = None
                unit_id_to_pass = None

                if target_col_spell and target_row_spell:
                    coords_to_pass = (target_col_spell.upper(), target_row_spell)
                
                if target_unit_id_spell:
                    unit_id_to_pass = target_unit_id_spell

                if play_card_streamlit(selected_card_to_play, target_coords=coords_to_pass, target_unit_id=unit_id_to_pass):
                    st.rerun()
    else:
        st.markdown("Nenhuma carta selecionada.")

    if st.button("Terminar turno", key="end_turn_button_bottom"):
        end_turn_streamlit()
        st.rerun()

    # Seção para o Log de Eventos
    st.markdown("---")
    st.subheader("📝 Log de Eventos")
    for event in reversed(list(st.session_state.event_log)): # Mostra as mais recentes primeiro
        st.text(event)