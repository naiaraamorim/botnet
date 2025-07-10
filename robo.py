import os
import time
import json
import requests
import threading as th
 
from concurrent.futures import ThreadPoolExecutor
 
# Configuration
token= "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cG4iOiI4MTA1NDU4NCIsImJpcnRoZGF0ZSI6IjEvMTQvMTk5NyAxMjowMDowMCBBTSIsInJvbGUiOiJWYWxlVXNlciIsImp0aSI6ImQ4YWJiZjEyLTgyOTMtNDhhNC04NzMyLTcyZThkNGM4ZDdkZSIsIm5iZiI6MTc1MjA4MzkzOCwiZXhwIjoxNzUyMDg3NTM4LCJpYXQiOjE3NTIwODM5MzgsImlzcyI6Imh0dHBzOi8vdmFsLWRldi1nYW1lZmxvcmVzdGFzLWFwaS5henVyZXdlYnNpdGVzLm5ldC8ifQ.nuMyqhSuBad8ldBoPoxr4-zrpkUOvffAeylo6Xk2NKM"
sleep_time = 0.1  # Time between thread batches
max_duration = 28 * 60  # 28 minutes
TARGET_EMAIL = "naiara.amorim@vale.com"  # Your email
DESIRED_RANK = 7  # The rank position you want to maintain
BATCH_SIZE = 30 # Number of requests per batch before re-checking rank
# --- End Configuration ---
 
# Headers for ranking API
ranking_headers = {
    'Accept': 'application/json, text/plain, /',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Authorization': f'Bearer {token}',
    'Connection': 'keep-alive',
    'Origin': 'https://parceirosdafloresta.vale.com',
    'Referer': 'https://parceirosdafloresta.vale.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
 
# Headers for share index generation
gen_headers = {
    'Accept': 'application/json, text/plain, /',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Authorization': f'Bearer {token}',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://parceirosdafloresta.vale.com',
    'Referer': 'https://parceirosdafloresta.vale.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
 
# Headers for point submission
submit_headers = {
    'Accept': 'application/json, text/plain, /',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://parceirosdafloresta.vale.com',
    'Referer': 'https://parceirosdafloresta.vale.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}
 
def generate_share_index():
    """Generate a new share index for point submission"""
   
    json_data = {
        'socialPlataform': 6,
        'challengeId': 8,
    }
 
    try:
        session = requests.Session()
        session.headers.update(gen_headers)
       
        response = session.post('https://val-dev-gameflorestas-api.azurewebsites.net/api/Social', json=json_data)
       
        print(f"Generate Status Code: {response.status_code}")
 
        if response.status_code == 200:
            js = response.json()
            print(json.dumps(js, indent=4, ensure_ascii=False))
           
            if js.get('success') and js.get('data') and js['data'].get('id'):
                share_id = str(js['data']['id'])
                print(f"New share index generated: {share_id}")
                return share_id
            else:
                print("Error: No valid share ID in response")
                return None
        elif response.status_code == 403:
            print(f"CRITICAL ERROR: Access denied (403). Token may be expired or invalid.")
            print("Script will terminate to prevent further unauthorized requests.")
            return "STOP_EXECUTION"
        else:
            print(f"Error generating share index: {response.status_code}")
            return None
           
    except Exception as e:
        print(f"Exception generating share index: {type(e)._name_}: {e}")
        return None
 
def send_request(share_index, lock, request_id):
 
    #with lock:
        #print(f"Adicionando pontos... (Request ID: {request_id})")
 
    try:
 
        response = requests.post(
            'https://val-dev-gameflorestas-api.azurewebsites.net/api/Social/access/{}'.format(share_index),
            headers=submit_headers,
            timeout=10
        )
 
        if response.status_code == 200:
            js = response.json()
 
            if js.get('success'):
 
                with lock:
                    print(f"Pontos adicionados com sucesso! (Request ID: {request_id})")
 
                return True
 
        else:
 
            if response.status_code == 404:
 
                with lock:
                    print(f"Erro {response.status_code}: Gere outro share_index. (Request ID: {request_id})")
                    return False
 
            elif response.status_code in [403, 429]:
 
                with lock:
                    print(f"IP Block: {response.status_code}. Tente novamente mais tarde. (Request ID: {request_id})")
                    return False
 
            else:
               
                with lock:
                    print(f"Erro {response.status_code}: {response.text} (Request ID: {request_id})")
                    return False
 
            return False
 
    except Exception as e:
 
        with lock:
            print(f"Erro: {type(e)._name_} (Request ID: {request_id})")
 
        return False
 
def check_result_and_stop(future):
 
    try:
        result = future.result()
 
        if result is False:
            stop_execution.set()
 
    except Exception:
        stop_execution.set()
 
def get_ranking_data():
    """Fetch current ranking data from the API"""
    params = {
        'limit': '100',
    }
 
    try:
        response = requests.get(
            'https://val-dev-gameflorestas-api.azurewebsites.net/api/ranking',
            params=params,
            headers=ranking_headers,
            timeout=30
        )
 
        if response.status_code == 200:
            js = response.json()
            return js['data']['rankings']
        else:
            print(f"Error fetching ranking: {response.status_code}")
            return None
           
    except Exception as e:
        print(f"Exception fetching ranking: {type(e)._name_}: {e}")
        return None
 
def analyze_ranking(rankings):
    """Analyze ranking to find target user position and competitors"""
    if not rankings:
        return None
   
    positions = []
    target_position = None
    target_points = None
   
    for idx, user_data in enumerate(rankings):
        name = user_data['user']['email']
        points = user_data['totalPoints']
        current_rank = idx + 1
       
        positions.append((current_rank, name, points))
       
        # Check if this is our target user
        if name == TARGET_EMAIL:
            target_position = current_rank
            target_points = points
   
    return {
        'positions': positions,
        'target_position': target_position,
        'target_points': target_points,
        'total_users': len(positions)
    }
 
def calculate_points_needed(analysis):
    """Calculate how many points are needed to reach desired rank"""
    if not analysis or not analysis['target_position']:
        return None
   
    current_rank = analysis['target_position']
    current_points = analysis['target_points']
    desired_rank = DESIRED_RANK
   
    if current_rank == desired_rank:
        return {
            'points_needed': 0,
            'action': 'MAINTAIN',
            'message': f"Already at desired rank {desired_rank}!"
        }
    elif current_rank < desired_rank:
        # We're ranked higher than desired, need to let others catch up
        return {
            'points_needed': 0,
            'action': 'WAIT',
            'message': f"Currently at rank {current_rank}, higher than desired rank {desired_rank}. Monitoring..."
        }
    else:
        # We need to gain points to improve rank
        positions = analysis['positions']
       
        if desired_rank <= len(positions):
            # Get points of person currently in desired rank
            target_user_points = positions[desired_rank - 1][2]  # -1 because list is 0-indexed
            points_needed = target_user_points - current_points + 10  # +10 buffer to surpass them
        else:
            points_needed = 10  # Minimum points to start climbing
       
        return {
            'points_needed': max(points_needed, 1),
            'action': 'GENERATE',
            'message': f"Need ~{points_needed} points to reach rank {desired_rank} from current rank {current_rank}"
        }
 
def display_ranking_status(analysis):
    """Display current ranking status"""
    if not analysis:
        print("Could not fetch ranking data")
        return
   
    print(f"\nRANKING STATUS:")
    print(f"   Target Email: {TARGET_EMAIL}")
    print(f"   Desired Rank: {DESIRED_RANK}")
   
    if analysis['target_position']:
        print(f"   Current Rank: {analysis['target_position']}")
        print(f"   Current Points: {analysis['target_points']}")
       
        action_info = calculate_points_needed(analysis)
        if action_info:
            print(f"   Status: {action_info['message']}")
    else:
        print(f"   {TARGET_EMAIL} not found in top 100 rankings!")
   
    print()
 
def should_generate_points():
    """Check if we need to generate points based on current ranking"""
    print(f"[{time.strftime('%H:%M:%S')}] Checking current ranking position...")
   
    rankings = get_ranking_data()
    analysis = analyze_ranking(rankings)
   
    display_ranking_status(analysis)
   
    if not analysis or not analysis['target_position']:
        print(f"WARNING: {TARGET_EMAIL} not found in rankings. Will generate points to enter leaderboard.")
        return True, "ENTER_LEADERBOARD"
   
    action_info = calculate_points_needed(analysis)
   
    if not action_info:
        print("Error calculating required action. Will generate points as safety measure.")
        return True, "ERROR_SAFETY"
   
    if action_info['action'] == 'GENERATE':
        print(f"Point generation needed: {action_info['message']}")
        return True, action_info['points_needed']
    elif action_info['action'] == 'MAINTAIN':
        print(f"Position maintained! {action_info['message']}")
        return False, 0
    else:  # WAIT
        print(f"No action needed: {action_info['message']}")
        return False, 0
 
if __name__ == "__main__":
 
    print("="*70)
    print("ADVANCED FLORESTA RANKING SYSTEM")
    print("="*70)
    print(f"Target Email: {TARGET_EMAIL}")
    print(f"Desired Rank: {DESIRED_RANK}")
    print(f"Batch Size: {BATCH_SIZE} (requests before rank check)")
    print("="*70)
    print("This system will:")
    print("1. Monitor your ranking position")
    print("2. Generate points only when needed to reach/maintain your desired rank")
    print("3. Check ranking every 15 seconds during point generation to avoid overshooting")
    print("4. Stop point generation immediately when you reach your target rank")
    print("5. Continuously monitor for competitors who might overtake you")
    print("="*70)
 
    if TARGET_EMAIL == "your_email@example.com":
        print("WARNING: Please update TARGET_EMAIL in the configuration!")
        print("Current value is the default placeholder.")
        print("="*70)
 
    lock = th.Lock()
    stop_execution = th.Event()
    ncpu = os.cpu_count() or 1
    cycle_count = 1
 
    try:
        while True:
            print(f"\n{'='*50}")
            print(f"RANKING CHECK {cycle_count}")
            print(f"{'='*50}")
 
            # Check current ranking
            rankings = get_ranking_data()
            analysis = analyze_ranking(rankings)
            if analysis and analysis['target_position']:
                current_rank = analysis['target_position']
                print(f"Current rank: {current_rank} | Target: {DESIRED_RANK}")
                if current_rank <= DESIRED_RANK:
                    print(f"Already at or above target rank {DESIRED_RANK}. Monitoring...")
                    cycle_count += 1
                    time.sleep(0.1)
                    continue
            else:
                print("Not found in ranking or error fetching ranking. Will try to generate points.")
 
            # Generate new share index
            share_index = generate_share_index()
            if share_index == "STOP_EXECUTION":
                print("Script terminated due to authentication error (403).")
                break
            elif not share_index:
                print("Failed to generate share index. Retrying in 30 seconds...")
                time.sleep(30)
                continue
 
            print(f"Starting point generation with share index: {share_index}")
 
            stop_execution.clear()
            start_time = time.time()
            successful_requests = 0
            total_requests = 0
 
            with ThreadPoolExecutor(max_workers=ncpu) as executor:
                request_id = 1
                batch_counter = 0
                while (not stop_execution.is_set() and (time.time() - start_time) < max_duration):
                    futures = []
                    for i in range(ncpu):
                        if stop_execution.is_set():
                            break
                        future = executor.submit(send_request, share_index, lock, request_id)
                        future.add_done_callback(check_result_and_stop)
                        futures.append(future)
                        request_id += 1
                        total_requests += 1
                        batch_counter += 1
                        if batch_counter >= BATCH_SIZE:
                            for f in futures:
                                try:
                                    if f.done() and f.result():
                                        successful_requests += 1
                                except:
                                    pass
                            print(f"[Batch] Checking rank after {BATCH_SIZE} requests...")
                            rankings = get_ranking_data()
                            analysis = analyze_ranking(rankings)
                            if analysis and analysis['target_position']:
                                current_rank = analysis['target_position']
                                print(f"   [Batch] Current Rank: {current_rank} | Target Rank: {DESIRED_RANK}")
                                if current_rank <= DESIRED_RANK:
                                    print(f"   [Batch] Target rank reached or surpassed. Stopping point generation.")
                                    stop_execution.set()
                                    break
                            else:
                                print("   [Batch] Could not fetch ranking data during batch check")
                            batch_counter = 0
                            futures = []
                    for future in futures:
                        if future.done():
                            try:
                                if future.result():
                                    successful_requests += 1
                            except:
                                pass
                    time.sleep(sleep_time)
 
            elapsed_time = time.time() - start_time
            print(f"\nCYCLE {cycle_count} SUMMARY:")
            print(f"   Duration: {elapsed_time/60:.1f} minutes")
            print(f"   Successful Requests: {successful_requests}/{total_requests}")
            if stop_execution.is_set():
                rankings = get_ranking_data()
                analysis = analyze_ranking(rankings)
                if analysis and analysis['target_position']:
                    current_rank = analysis['target_position']
                    if current_rank <= DESIRED_RANK:
                        print(f"   Status: TARGET RANK ACHIEVED! Currently at rank {current_rank}")
                        if current_rank < DESIRED_RANK:
                            print(f"   WARNING: You've overshot! You're at rank {current_rank}, better than target rank {DESIRED_RANK}")
                        print(f"   Switching to monitoring mode...")
                    else:
                        print("   Status: Stopped due to error (will retry with new cycle)")
                else:
                    print("   Status: Stopped due to error (will retry with new cycle)")
            else:
                print("   Status: Completed successfully")
            cycle_count += 1
            time.sleep(2)
 
    except KeyboardInterrupt:
        print("\n\nScript stopped by user.")
        print("Thank you for using the Advanced Floresta Ranking System!")
    except Exception as e:
        print(f"\nUnexpected error: {type(e)._name_}: {e}")
        print("The system will attempt to restart...")
