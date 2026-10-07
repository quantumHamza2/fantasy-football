import mysql.connector
from mysql.connector import Error
import os
import random
from datetime import datetime, timedelta
import time

# Database Configuration
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DB", "fantasy_football_db")
}

# Player position multipliers for stats generation
POSITION_STATS = {
    'GK': {'goals': (0, 0.01), 'assists': (0, 0.1), 'clean_sheets': (0.3, 0.7), 'saves': (3, 8)},
    'DEF': {'goals': (0, 0.3), 'assists': (0, 0.4), 'clean_sheets': (0.2, 0.6), 'saves': (0, 0)},
    'MID': {'goals': (0, 0.6), 'assists': (0, 0.8), 'clean_sheets': (0, 0.1), 'saves': (0, 0)},
    'FWD': {'goals': (0, 1.2), 'assists': (0, 0.5), 'clean_sheets': (0, 0), 'saves': (0, 0)}
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def create_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"🚨 Connection Error: {e}")
        print("TIP: Is MySQL running? Try 'brew services start mysql' on Mac")
        return None

def setup_database():
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()
        
        # Create database
        # Refuse to overwrite an existing database; never destroy user data.
        import re
        database = DB_CONFIG["database"]
        if not re.fullmatch(r"[A-Za-z0-9_]+", database):
            raise ValueError("MYSQL_DB must contain only letters, digits and underscores")
        cursor.execute(f"CREATE DATABASE `{database}`")
        conn.database = DB_CONFIG["database"]
        
        cursor.execute("""CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )""")
        # Enhanced tables with additional stats
        cursor.execute("""
        CREATE TABLE Teams (
            team_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            short_code VARCHAR(3),
            stadium VARCHAR(100),
            matches_played INT DEFAULT 0,
            wins INT DEFAULT 0,
            draws INT DEFAULT 0,
            losses INT DEFAULT 0,
            goals_for INT DEFAULT 0,
            goals_against INT DEFAULT 0
        )""")
        
        cursor.execute("""
        CREATE TABLE Players (
            player_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            position ENUM('GK', 'DEF', 'MID', 'FWD') NOT NULL,
            team_id INT,
            price DECIMAL(10, 2) NOT NULL,
            total_points INT DEFAULT 0,
            form DECIMAL(3, 1) DEFAULT 0.0,
            goals INT DEFAULT 0,
            assists INT DEFAULT 0,
            clean_sheets INT DEFAULT 0,
            yellow_cards INT DEFAULT 0,
            red_cards INT DEFAULT 0,
            minutes_played INT DEFAULT 0,
            FOREIGN KEY (team_id) REFERENCES Teams(team_id)
        )""")
        
        cursor.execute("""
        CREATE TABLE FantasyTeams (
            fantasy_team_id INT AUTO_INCREMENT PRIMARY KEY,
            team_name VARCHAR(100) NOT NULL,
            owner_name VARCHAR(100),
            budget DECIMAL(10, 2) DEFAULT 100.00,
            total_points INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        cursor.execute("""
        CREATE TABLE FantasyTeamPlayers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fantasy_team_id INT,
            player_id INT,
            is_captain BOOLEAN DEFAULT FALSE,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fantasy_team_id) REFERENCES FantasyTeams(fantasy_team_id),
            FOREIGN KEY (player_id) REFERENCES Players(player_id)
        )""")
        
        cursor.execute("""
        CREATE TABLE Matches (
            match_id INT AUTO_INCREMENT PRIMARY KEY,
            home_team_id INT,
            away_team_id INT,
            home_score INT,
            away_score INT,
            match_date DATE,
            FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
            FOREIGN KEY (away_team_id) REFERENCES Teams(team_id)
        )""")
        
        # Insert ALL 18 Premier League Teams with more realistic data
        teams = [
            ('Arsenal', 'ARS', 'Emirates Stadium'), ('Aston Villa', 'AVL', 'Villa Park'),
            ('Brentford', 'BRE', 'Gtech Community Stadium'), ('Brighton', 'BHA', 'Amex Stadium'),
            ('Chelsea', 'CHE', 'Stamford Bridge'), ('Crystal Palace', 'CRY', 'Selhurst Park'),
            ('Everton', 'EVE', 'Goodison Park'), ('Fulham', 'FUL', 'Craven Cottage'),
            ('Liverpool', 'LIV', 'Anfield'), ('Luton Town', 'LUT', 'Kenilworth Road'),
            ('Manchester City', 'MCI', 'Etihad Stadium'), ('Manchester United', 'MUN', 'Old Trafford'),
            ('Newcastle United', 'NEW', "St James' Park"), ('Nottingham Forest', 'NOT', 'City Ground'),
            ('Sheffield United', 'SHU', 'Bramall Lane'), ('Tottenham', 'TOT', 'Tottenham Hotspur Stadium'),
            ('West Ham', 'WHU', 'London Stadium'), ('Wolves', 'WOL', 'Molineux Stadium')
        ]
        cursor.executemany("INSERT INTO Teams (name, short_code, stadium) VALUES (%s, %s, %s)", teams)
        
        # Insert 100+ Real Players with realistic prices and positions
        players = []
        # Arsenal
        players.extend([
            ('Bukayo Saka', 'MID', 1, 8.5), ('Martin Ødegaard', 'MID', 1, 7.5),
            ('Declan Rice', 'MID', 1, 5.0), ('William Saliba', 'DEF', 1, 5.0)
        ])
        # Man City
        players.extend([
            ('Erling Haaland', 'FWD', 11, 14.0), ('Kevin De Bruyne', 'MID', 11, 10.5),
            ('Rodri', 'MID', 11, 5.5), ('Rúben Dias', 'DEF', 11, 5.5)
        ])
        # Liverpool
        players.extend([
            ('Mohamed Salah', 'FWD', 9, 12.5), ('Virgil van Dijk', 'DEF', 9, 6.0),
            ('Alisson', 'GK', 9, 5.5), ('Trent Alexander-Arnold', 'DEF', 9, 8.0)
        ])
        # Other teams...
        players.extend([
            ('Bruno Fernandes', 'MID', 12, 8.5), ('Marcus Rashford', 'FWD', 12, 9.0),
            ('Son Heung-min', 'FWD', 16, 9.5), ('James Maddison', 'MID', 16, 8.0),
            ('Ollie Watkins', 'FWD', 2, 8.0), ('Jarrod Bowen', 'MID', 17, 7.5)
        ])
        
        # Generate 80 more generic players
        positions = ['GK', 'DEF', 'MID', 'FWD']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        for team_id in range(1, 19):
            for _ in range(5):  # 5 generic players per team
                position = random.choice(positions)
                base_price = {'GK': 4.5, 'DEF': 4.0, 'MID': 5.0, 'FWD': 6.0}[position]
                price = base_price + random.uniform(-1.5, 3.0)
                price = max(4.0, min(price, 12.0))  # Keep prices realistic
                players.append((
                    f"{random.choice(['James', 'John', 'Robert', 'Michael'])} {random.choice(last_names)}",
                    position,
                    team_id,
                    round(price, 1)
                ))
        
        cursor.executemany(
            "INSERT INTO Players (name, position, team_id, price) VALUES (%s, %s, %s, %s)", 
            players
        )
        
        conn.commit()
        print("✅ Database initialized with:")
        print(f"- {len(teams)} Premier League teams")
        print(f"- {len(players)} players")
        print(f"- Fantasy team structure ready")
        
    except Error as e:
        print(f"🚨 Setup Error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def view_teams(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.*, 
               (wins * 3 + draws) AS points,
               (goals_for - goals_against) AS goal_diff
        FROM Teams t
        ORDER BY points DESC, goal_diff DESC
    """)
    print("\n🏆 Premier League Table:")
    print("{:<5} {:<20} {:<5} {:<5} {:<5} {:<5} {:<5} {:<5} {:<5}".format(
        "ID", "Team", "MP", "W", "D", "L", "GF", "GA", "Pts"))
    print("-"*70)
    for team in cursor:
        print("{:<5} {:<20} {:<5} {:<5} {:<5} {:<5} {:<5} {:<5} {:<5}".format(
            team['team_id'], team['name'], team['matches_played'], team['wins'],
            team['draws'], team['losses'], team['goals_for'], team['goals_against'],
            (team['wins'] * 3 + team['draws'])))
    cursor.close()

def view_players(conn, filter_team=None, filter_position=None):
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT p.player_id, p.name, p.position, t.name as team, p.price, 
               p.total_points, p.goals, p.assists, p.clean_sheets
        FROM Players p JOIN Teams t ON p.team_id = t.team_id
    """
    params = []
    
    conditions = []
    if filter_team:
        conditions.append("t.team_id = %s")
        params.append(filter_team)
    if filter_position:
        conditions.append("p.position = %s")
        params.append(filter_position)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY p.total_points DESC"
    cursor.execute(query, params)
    
    print("\n👕 Players List:")
    print("{:<5} {:<25} {:<6} {:<20} {:<6} {:<6} {:<6} {:<6} {:<6}".format(
        "ID", "Name", "Pos", "Team", "Price", "Pts", "G", "A", "CS"))
    print("-"*90)
    for player in cursor:
        print("{:<5} {:<25} {:<6} {:<20} {:<6.1f} {:<6} {:<6} {:<6} {:<6}".format(
            player['player_id'], player['name'], player['position'], 
            player['team'], player['price'], player['total_points'],
            player['goals'], player['assists'], player['clean_sheets']))
    cursor.close()

def generate_player_stats(position):
    """Generate realistic stats based on player position"""
    stats = POSITION_STATS[position]
    goals = 1 if random.random() < stats['goals'][1] else 0
    assists = 1 if random.random() < stats['assists'][1] else 0
    clean_sheet = 1 if random.random() < stats['clean_sheets'][1] else 0
    saves = random.randint(stats['saves'][0], stats['saves'][1]) if position == 'GK' else 0
    yellow_card = 1 if random.random() < 0.15 else 0  # 15% chance
    red_card = 1 if random.random() < 0.02 else 0    # 2% chance
    
    return {
        'goals': goals,
        'assists': assists,
        'clean_sheet': clean_sheet,
        'saves': saves,
        'yellow_card': yellow_card,
        'red_card': red_card
    }

def simulate_match(conn, home_team_id, away_team_id):
    cursor = conn.cursor(dictionary=True)
    
    # Simulate match score (weighted by team strength)
    home_strength = random.uniform(0.7, 1.3)
    away_strength = random.uniform(0.7, 1.3)
    home_goals = max(0, int(random.gauss(1.5 * home_strength, 1)))
    away_goals = max(0, int(random.gauss(1.5 * away_strength, 1)))
    
    # Update team records
    cursor.execute("""
        UPDATE Teams 
        SET matches_played = matches_played + 1,
            goals_for = goals_for + %s,
            goals_against = goals_against + %s,
            wins = wins + CASE WHEN %s > %s THEN 1 ELSE 0 END,
            draws = draws + CASE WHEN %s = %s THEN 1 ELSE 0 END,
            losses = losses + CASE WHEN %s < %s THEN 1 ELSE 0 END
        WHERE team_id IN (%s, %s)
    """, (home_goals, away_goals, home_goals, away_goals, home_goals, away_goals, home_goals, away_goals, home_team_id, away_team_id))
    
    # Get players from both teams
    cursor.execute("SELECT player_id, position FROM Players WHERE team_id IN (%s, %s)", (home_team_id, away_team_id))
    players = cursor.fetchall()
    
    # Update player stats
    for player in players:
        stats = generate_player_stats(player['position'])
        
        # Calculate fantasy points
        points = (stats['goals'] * 4) + (stats['assists'] * 3)
        if player['position'] in ('GK', 'DEF'):
            points += stats['clean_sheet'] * 4
        if player['position'] == 'GK':
            points += stats['saves'] // 3  # 1 point per 3 saves
        points -= stats['yellow_card']
        points -= stats['red_card'] * 3
        
        # Update database
        cursor.execute("""
            UPDATE Players 
            SET total_points = total_points + %s,
                goals = goals + %s,
                assists = assists + %s,
                clean_sheets = clean_sheets + %s,
                yellow_cards = yellow_cards + %s,
                red_cards = red_cards + %s,
                minutes_played = minutes_played + 90
            WHERE player_id = %s
        """, (points, stats['goals'], stats['assists'], stats['clean_sheet'], 
              stats['yellow_card'], stats['red_card'], player['player_id']))
    
    # Record match
    cursor.execute("""
        INSERT INTO Matches (home_team_id, away_team_id, home_score, away_score, match_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (home_team_id, away_team_id, home_goals, away_goals, datetime.now().date()))
    
    conn.commit()
    
    # Get team names for display
    cursor.execute("SELECT name FROM Teams WHERE team_id IN (%s, %s)", (home_team_id, away_team_id))
    home_name, away_name = cursor.fetchall()
    
    print(f"\n⚽ {home_name[0]['name']} {home_goals}-{away_goals} {away_name[0]['name']}")
    cursor.close()

def simulate_matchday(conn):
    try:
        print("\n📅 Simulating Premier League Matchday...")
        
        # Get all teams and shuffle them
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT team_id FROM Teams")
        team_ids = [t['team_id'] for t in cursor.fetchall()]
        random.shuffle(team_ids)
        
        # Simulate matches (10 matches per matchday)
        for i in range(0, len(team_ids)-1, 2):
            home_id = team_ids[i]
            away_id = team_ids[i+1]
            simulate_match(conn, home_id, away_id)
            time.sleep(0.5)  # Pause for dramatic effect
        
        print("\n✅ Matchday simulation complete!")
        
    except Error as e:
        print(f"🚨 Simulation Error: {e}")

def create_fantasy_team(conn):
    try:
        cursor = conn.cursor()
        
        print("\n🛠️ Create Your Fantasy Team")
        team_name = input("Team Name: ")
        owner_name = input("Your Name: ")
        
        # Create team with £100m budget
        cursor.execute("""
            INSERT INTO FantasyTeams (team_name, owner_name)
            VALUES (%s, %s)
        """, (team_name, owner_name))
        team_id = cursor.lastrowid
        
        budget = 100.0
        selected_players = []
        positions_needed = {'GK': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}
        
        while sum(positions_needed.values()) > 0 and budget > 0:
            clear_screen()
            print(f"\n💰 Remaining Budget: £{budget:.1f}m")
            print("Positions needed:")
            for pos, count in positions_needed.items():
                if count > 0:
                    print(f"- {pos}: {count}")
            
            # Show players filtered by needed positions
            needed_positions = [pos for pos, count in positions_needed.items() if count > 0]
            view_players(conn, filter_position=random.choice(needed_positions))
            
            player_id = input("\nEnter Player ID to add (or 'done' to finish): ")
            if player_id.lower() == 'done':
                break
                
            # Get player details
            cursor.execute("""
                SELECT player_id, name, position, price 
                FROM Players 
                WHERE player_id = %s
            """, (player_id,))
            player = cursor.fetchone()
            
            if not player:
                print("❌ Invalid Player ID!")
                continue
                
            if positions_needed[player[2]] <= 0:
                print(f"❌ Already have enough {player[2]} players!")
                continue
                
            if player[3] > budget:
                print(f"❌ Need £{player[3] - budget:.1f}m more!")
                continue
                
            # Add player to team
            selected_players.append(player)
            budget -= float(player[3])
            positions_needed[player[2]] -= 1
            print(f"✔ Added {player[1]} (£{player[3]}m)! Remaining: £{budget:.1f}m")
            
            # Set first GK as captain
            if player[2] == 'GK' and positions_needed['GK'] == 1:
                is_captain = True
            else:
                is_captain = False
            
            cursor.execute("""
                INSERT INTO FantasyTeamPlayers (fantasy_team_id, player_id, is_captain)
                VALUES (%s, %s, %s)
            """, (team_id, player[0], is_captain))
            
            input("\nPress Enter to continue...")
        
        conn.commit()
        print(f"\n✅ Team '{team_name}' created with {len(selected_players)} players!")
        print(f"Remaining budget: £{budget:.1f}m")
        
    except Error as e:
        print(f"🚨 Team Creation Error: {e}")

def view_fantasy_team(conn, team_id):
    cursor = conn.cursor(dictionary=True)
    
    # Get team info
    cursor.execute("SELECT * FROM FantasyTeams WHERE fantasy_team_id = %s", (team_id,))
    team = cursor.fetchone()
    
    # Get players
    cursor.execute("""
        SELECT p.player_id, p.name, p.position, p.price, p.total_points, ftp.is_captain
        FROM FantasyTeamPlayers ftp
        JOIN Players p ON ftp.player_id = p.player_id
        WHERE ftp.fantasy_team_id = %s
        ORDER BY p.position, p.total_points DESC
    """, (team_id,))
    players = cursor.fetchall()
    
    print(f"\n🏆 {team['team_name']} (Managed by {team['owner_name']})")
    print(f"💰 Budget: £{team['budget']:.1f}m | 📊 Total Points: {team['total_points']}")
    print("\n👕 Squad:")
    print("{:<5} {:<25} {:<6} {:<6} {:<6} {:<10}".format(
        "ID", "Name", "Pos", "Price", "Pts", "Captain"))
    print("-"*65)
    
    total_value = 0
    total_points = 0
    for player in players:
        print("{:<5} {:<25} {:<6} {:<6.1f} {:<6} {:<10}".format(
            player['player_id'], player['name'], player['position'], 
            player['price'], player['total_points'],
            "⭐" if player['is_captain'] else ""))
        total_value += float(player['price'])
        total_points += player['total_points']
    
    print(f"\nTotal Squad Value: £{total_value:.1f}m")
    print(f"Total Points: {total_points}")
    cursor.close()

def transfer_market(conn):
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get user's team
        cursor.execute("SELECT * FROM FantasyTeams LIMIT 1")
        team = cursor.fetchone()
        
        if not team:
            print("❌ No teams found! Create one first.")
            return
        
        while True:
            clear_screen()
            view_fantasy_team(conn, team['fantasy_team_id'])
            
            print("\n🔄 Transfer Market Options:")
            print("1. Sell Player")
            print("2. Buy Player")
            print("3. Set Captain")
            print("4. Back to Menu")
            choice = input("\nChoose option: ")
            
            if choice == "1":
                # Sell player
                player_id = input("Enter Player ID to sell: ")
                cursor.execute("""
                    SELECT p.player_id, p.name, p.price, ftp.id
                    FROM FantasyTeamPlayers ftp
                    JOIN Players p ON ftp.player_id = p.player_id
                    WHERE ftp.fantasy_team_id = %s AND p.player_id = %s
                """, (team['fantasy_team_id'], player_id))
                player = cursor.fetchone()
                
                if player:
                    cursor.execute("""
                        DELETE FROM FantasyTeamPlayers 
                        WHERE id = %s
                    """, (player['id'],))
                    cursor.execute("""
                        UPDATE FantasyTeams 
                        SET budget = budget + %s
                        WHERE fantasy_team_id = %s
                    """, (player['price'], team['fantasy_team_id']))
                    conn.commit()
                    print(f"✔ Sold {player['name']} for £{player['price']}m!")
                else:
                    print("❌ Player not in your squad!")
                input("\nPress Enter to continue...")
                
            elif choice == "2":
                # Buy player
                view_players(conn)
                player_id = input("\nEnter Player ID to buy: ")
                
                # Check if player exists and get price
                cursor.execute("""
                    SELECT player_id, name, position, price 
                    FROM Players 
                    WHERE player_id = %s
                """, (player_id,))
                player = cursor.fetchone()
                
                if not player:
                    print("❌ Invalid Player ID!")
                    input("\nPress Enter to continue...")
                    continue
                
                # Check if already in team
                cursor.execute("""
                    SELECT 1 FROM FantasyTeamPlayers
                    WHERE fantasy_team_id = %s AND player_id = %s
                """, (team['fantasy_team_id'], player_id))
                if cursor.fetchone():
                    print("❌ Player already in your team!")
                    input("\nPress Enter to continue...")
                    continue
                
                # Check budget
                if float(player['price']) > team['budget']:
                    print(f"❌ Need £{player['price'] - team['budget']:.1f}m more!")
                    input("\nPress Enter to continue...")
                    continue
                
                # Add player
                cursor.execute("""
                    INSERT INTO FantasyTeamPlayers (fantasy_team_id, player_id)
                    VALUES (%s, %s)
                """, (team['fantasy_team_id'], player_id))
                
                # Update budget
                cursor.execute("""
                    UPDATE FantasyTeams 
                    SET budget = budget - %s
                    WHERE fantasy_team_id = %s
                """, (player['price'], team['fantasy_team_id']))
                
                conn.commit()
                print(f"✔ Bought {player['name']} for £{player['price']}m!")
                input("\nPress Enter to continue...")
                
            elif choice == "3":
                # Set captain
                player_id = input("Enter Player ID to make captain: ")
                
                # Clear current captain
                cursor.execute("""
                    UPDATE FantasyTeamPlayers
                    SET is_captain = FALSE
                    WHERE fantasy_team_id = %s
                """, (team['fantasy_team_id'],))
                
                # Set new captain
                cursor.execute("""
                    UPDATE FantasyTeamPlayers
                    SET is_captain = TRUE
                    WHERE fantasy_team_id = %s AND player_id = %s
                """, (team['fantasy_team_id'], player_id))
                
                conn.commit()
                print("✔ Captain changed!")
                input("\nPress Enter to continue...")
                
            elif choice == "4":
                break
                
    except Error as e:
        print(f"🚨 Transfer Error: {e}")
    finally:
        cursor.close()

def view_league_standings(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT ft.team_name, ft.owner_name, SUM(p.total_points) as total_points,
               COUNT(ftp.player_id) as players, ft.budget
        FROM FantasyTeams ft
        LEFT JOIN FantasyTeamPlayers ftp ON ft.fantasy_team_id = ftp.fantasy_team_id
        LEFT JOIN Players p ON ftp.player_id = p.player_id
        GROUP BY ft.fantasy_team_id
        ORDER BY total_points DESC
    """)
    
    print("\n🏆 Fantasy League Standings:")
    print("{:<5} {:<20} {:<20} {:<10} {:<10} {:<10}".format(
        "Pos", "Team", "Manager", "Points", "Players", "Budget"))
    print("-"*85)
    for idx, team in enumerate(cursor.fetchall(), 1):
        print("{:<5} {:<20} {:<20} {:<10} {:<10} {:<10.1f}".format(
            idx, team['team_name'], team['owner_name'], 
            team['total_points'] or 0, team['players'], float(team['budget'])))
    cursor.close()

def main_menu():
    conn = create_connection()
    if not conn:
        return
    
    try:
        while True:
            clear_screen()
            print("""
            ╔══════════════════════════════════════════╗
            ║       FANTASY FOOTBALL MANAGER 2024       ║
            ╚══════════════════════════════════════════╝
            1. View Premier League Table
            2. View All Players
            3. Create Fantasy Team
            4. Manage My Team
            5. Simulate Matchday
            6. View Fantasy League
            7. Exit
            """)
            
            choice = input("\nChoose option: ")
            
            if choice == "1":
                view_teams(conn)
            elif choice == "2":
                view_players(conn)
            elif choice == "3":
                create_fantasy_team(conn)
            elif choice == "4":
                transfer_market(conn)
            elif choice == "5":
                simulate_matchday(conn)
            elif choice == "6":
                view_league_standings(conn)
            elif choice == "7":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice!")
            
            input("\nPress Enter to continue...")
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    print("⚽ Fantasy Football Manager 2024 ⚽")
    print("1. Initialize Database")
    print("2. Run Program")
    choice = input("Choose option: ")
    
    if choice == "1":
        setup_database()
    elif choice == "2":
        main_menu()