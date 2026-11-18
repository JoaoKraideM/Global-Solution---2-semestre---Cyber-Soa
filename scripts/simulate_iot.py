"""Cliente virtual de sensor (somente dados sintéticos).
Exemplos:
python scripts/simulate_iot.py --station centro-demo --once
python scripts/simulate_iot.py --station verde-demo --count 3 --interval 3
"""
import argparse
import math
import os
import random
import sys
import time
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

parser = argparse.ArgumentParser()
parser.add_argument('--station', choices=['centro-demo','verde-demo'], default='centro-demo')
parser.add_argument('--url', default=os.getenv('API_URL','http://127.0.0.1:8000'))
parser.add_argument('--once', action='store_true')
parser.add_argument('--count', type=int, default=5)
parser.add_argument('--interval', type=float, default=2)
args = parser.parse_args()

key = os.getenv('SENSOR_A_KEY' if args.station=='centro-demo' else 'SENSOR_B_KEY','')
if not key or key.startswith('SUBSTITUA'):
    sys.exit('Configure SENSOR_A_KEY/SENSOR_B_KEY no arquivo .env')

for i in range(1 if args.once else max(1, args.count)):
    temp = 31 + 2*math.sin(i/3) + random.uniform(-0.4,0.4) - (1.5 if args.station=='verde-demo' else 0)
    payload = {'temperature_c':round(temp,1),'humidity_pct': round(61+random.uniform(-4,4),1)}
    try:
        with httpx.Client(timeout=5) as client:
            response = client.post(f'{args.url}/api/v1/stations/{args.station}/readings',json=payload,headers={'X-Device-Key':key})
        print(response.status_code, response.text, '[DADO SINTÉTICO]')
        response.raise_for_status()
    except httpx.HTTPError as exc:
        sys.exit(f'Falha no envio: {exc}')
    if i+1 < args.count and not args.once:
        time.sleep(args.interval)
