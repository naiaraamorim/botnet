import os
import time
import json
import requests
import threading as th

from concurrent.futures import ThreadPoolExecutor

# Configuration
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cG4iOiI4MTA1NDU4NCIsImJpcnRoZGF0ZSI6IjEvMTQvMTk5NyAxMjowMDowMCBBTSIsInJvbGUiOiJWYWxlVXNlciIsImp0aSI6ImQ4YWJiZjEyLTgyOTMtNDhhNC04NzMyLTcyZThkNGM4ZDdkZSIsIm5iZiI6MTc1MjA4MzkzOCwiZXhwIjoxNzUyMDg3NTM4LCJpYXQiOjE3NTIwODM5MzgsImlzcyI6Imh0dHBzOi8vdmFsLWRldi1nYW1lZmxvcmVzdGFzLWFwaS5henVyZXdlYnNpdGVzLm5ldC8ifQ.nuMyqhSuBad8ldBoPoxr4-zrpkUOvffAeylo6Xk2NKM"
sleep_time = 0.1  # Time between thread batches
max_duration = 28 * 60  # 28 minutes
TARGET_EMAIL = "naiara.amorim@vale.com"  # Your email
DESIRED_RANK = 7  # The rank position you want to maintain
BATCH_SIZE = 30   # Number of requests per batch before re-checking rank
# --- End Configuration ---

# (headers definitions permanecem inalterados)
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
        response = session.post(
            'https://val-dev-gameflorestas-api.azurewebsites.net/api/Social',
            json=json_data
        )
        print(f"Generate Status Code: {response.status_code}")
        if response.status_code == 200:
            js = response.json()
            if js.get('success') and js.get('data') and js['data'].get('id'):
                share_id = str(js['data']['id'])
                print(f"New share index generated: {share_id}")
                return share_id
            else:
                print("Error: No valid share ID in response")
                return None
        elif response.status_code == 403:
            print("CRITICAL ERROR: Access denied (403). Token may be expired or invalid.")
            return "STOP_EXECUTION"
        else:
            print(f"Error generating share index: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception generating share index: {type(e).__name__}: {e}")
        return None

def send_request(share_index, lock, request_id):
    try:
        response = requests.post(
            f'https://val-dev-gameflorestas-api.azurewebsites.net/api/Social/access/{share_index}',
            headers=submit_headers,
            timeout=10
        )
        if response.status_code == 200 and response.json().get('success'):
            with lock:
                print(f"Pontos adicionados com sucesso! (Request ID: {request_id})")
            return True
        else:
            with lock:
                code = response.status_code
                if code == 404:
                    print(f"Erro 404: Gere outro share_index. (Request ID: {request_id})")
                elif code in [403, 429]:
                    print(f"IP Block: {code}. Tente novamente mais tarde. (Request ID: {request_id})")
                else:
                    print(f"Erro {code}: {response.text} (Request ID: {request_id})")
            return False
    except Exception as e:
        with lock:
            print(f"Erro: {type(e).__name__} (Request ID: {request_id})")
        return False

def check_result_and_stop(future):
    try:
        if future.result() is False:
            stop_execution.set()
    except:
        stop_execution.set()

def get_ranking_data():
    """Fetch current ranking data from the API"""
    try:
        response = requests.get(
            'https://val-dev-gameflorestas-api.azurewebsites.net/api/ranking',
            params={'limit': '100'},
            headers=ranking_headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()['data']['rankings']
        else:
            print(f"Error fetching ranking: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception fetching ranking: {type(e).__name__}: {e}")
        return None

def analyze_ranking(rankings):
    """Analyze ranking to find target user position and competitors"""
    if not rankings:
        return None
    positions = []
    target_position = None
    target_points = None
    for idx, user_data in enumerate(rankings):
        email = user_data['user']['email']
        pts = user_data['totalPoints']
        rank = idx + 1
        positions.append((rank, email, pts))
        if email == TARGET_EMAIL:
            target_position = rank
            target_points = pts
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
    curr_rank = analysis['target_position']
    curr_pts = analysis['target_points']
    if curr_rank == DESIRED_RANK:
        return {'points_needed': 0, 'action': 'MAINTAIN',
                'message': f"Already at desired rank {DESIRED_RANK}!"}
    if curr_rank < DESIRED_RANK:
        return {'points_needed': 0, 'action': 'WAIT',
                'message': f"Currently at rank {curr_rank}, higher than desired rank {DESIRED_RANK}. Monitoring..."}
    # needs to climb
    target_pts = analysis['positions'][DESIRED_RANK - 1][2] \
                if DESIRED_RANK <= len(analysis['positions']) else curr_pts
    needed = target_pts - curr_pts + 10
    return {'points_needed': max(needed, 1), 'action': 'GENERATE',
            'message': f"Need ~{needed} points to reach rank {DESIRED_RANK} from current rank {curr_rank}"}

def display_ranking_status(analysis):
    """Display current ranking status"""
    if not analysis:
        print("Could not fetch ranking data")
        return
    print("\nRANKING STATUS:")
    print(f"   Target Email: {TARGET_EMAIL}")
    print(f"   Desired Rank: {DESIRED_RANK}")
    if analysis['target_position']:
        print(f"   Current Rank: {analysis['target_position']}")
        print(f"   Current Points: {analysis['target_points']}")
        print(f"   Status: {calculate_points_needed(analysis)['message']}")
    else:
        print(f"   {TARGET_EMAIL} not found in top 100 rankings!")
    print()

if __name__ == "__main__":
    print("="*70)
    print("ADVANCED FLORESTA RANKING SYSTEM")
    print("="*70)
    print(f"Target Email: {TARGET_EMAIL}")
    print(f"Desired Rank: {DESIRED_RANK}")
    print(f"Batch Size: {BATCH_SIZE}")
    print("="*70)

    lock = th.Lock()
    stop_execution = th.Event()
    ncpu = os.cpu_count() or 1
    cycle_count = 1

    # <<< NOVO: Guarda a última posição conhecida (None até primeiro fetch bem-sucedido) >>>
    last_known_rank = None

    try:
        while True:
            print(f"\n{'='*50}")
            print(f"RANKING CHECK {cycle_count}")
            print(f"{'='*50}")

            # 1) Tenta buscar o ranking
            rankings = get_ranking_data()
            analysis = analyze_ranking(rankings)

            if analysis and analysis['target_position']:
                current_rank = analysis['target_position']
                # <<< NOVO: atualiza última posição conhecida apenas em caso de sucesso >>>
                last_known_rank = current_rank

                print(f"Current rank: {current_rank} | Target: {DESIRED_RANK}")
                if current_rank <= DESIRED_RANK:
                    print(f"Already at or above target rank {DESIRED_RANK}. Monitoring...")
                    cycle_count += 1
                    time.sleep(sleep_time)
                    continue
            else:
                # <<< NOVO: se falhar e na última vez você já estava no alvo, continua monitoramento >>>
                if last_known_rank is not None and last_known_rank <= DESIRED_RANK:
                    print("WARNING: Could not fetch ranking, but you were already at target rank. Continuing monitoring...")
                    cycle_count += 1
                    time.sleep(sleep_time)
                    continue
                print("Not found in ranking or error fetching ranking. Will try to generate points.")

            # 2) Gerar novo share_index
            share_index = generate_share_index()
            if share_index == "STOP_EXECUTION":
                print("Script terminated due to authentication error (403).")
                break
            if not share_index:
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
                while not stop_execution.is_set() and (time.time() - start_time) < max_duration:
                    futures = []
                    for _ in range(ncpu):
                        if stop_execution.is_set():
                            break
                        fut = executor.submit(send_request, share_index, lock, request_id)
                        fut.add_done_callback(check_result_and_stop)
                        futures.append(fut)
                        request_id += 1
                        total_requests += 1
                        batch_counter += 1

                        if batch_counter >= BATCH_SIZE:
                            for f in futures:
                                if f.done() and f.result():
                                    successful_requests += 1
                            # Recheca o ranking em batch
                            print(f"[Batch] Checking rank after {BATCH_SIZE} requests...")
                            new_ranks = analyze_ranking(get_ranking_data() or [])
                            if new_ranks and new_ranks['target_position'] <= DESIRED_RANK:
                                print(f"[Batch] Target rank reached ({new_ranks['target_position']}). Stopping generation.")
                                stop_execution.set()
                                break
                            batch_counter = 0
                            futures.clear()
                    # coleta requests finais do batch
                    for f in futures:
                        if f.done() and f.result():
                            successful_requests += 1
                    time.sleep(sleep_time)

            elapsed = (time.time() - start_time) / 60
            print(f"\nCYCLE {cycle_count} SUMMARY:")
            print(f"   Duration: {elapsed:.1f} minutes")
            print(f"   Successful Requests: {successful_requests}/{total_requests}")
            if stop_execution.is_set():
                final_analysis = analyze_ranking(get_ranking_data())
                if final_analysis and final_analysis['target_position'] <= DESIRED_RANK:
                    print(f"   Status: TARGET RANK ACHIEVED! Currently at rank {final_analysis['target_position']}")
                else:
                    print("   Status: Stopped due to error (will retry next cycle)")
            else:
                print("   Status: Completed cycle without hitting target; will retry.")
            cycle_count += 1
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nScript stopped by user.")
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {e}")
        print("The system will attempt to restart...")
