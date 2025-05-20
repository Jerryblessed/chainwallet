import os
import json
import csv
import io
import requests
from flask import (
    Flask, render_template, render_template_string, request,
    redirect, url_for, session, flash, jsonify, send_file
)
from collections import Counter
from hdwithsteps import BitcoinTestnetHDWallet
from datetime import datetime

# env
import dotenv
dotenv.load_dotenv()

# Ethereum wallet dependencies
from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic
from hexbytes import HexBytes
from openai import AzureOpenAI

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', os.urandom(16))

# -----------------------------------------------------------------------------
# Rebar Shield / Data API configuration (for etchings & send_tx)
# -----------------------------------------------------------------------------
REBAR_SHIELD_KEY = os.getenv('REBAR_SHIELD_KEY')
REBAR_DATA_KEY   = os.getenv('REBAR_DATA_KEY')
REBAR_SHIELD_URL = 'https://shield.rebarlabs.io/v1/rpc'
REBAR_DATA_BASE  = 'https://data.rebarlabs.io/v1'

# -----------------------------------------------------------------------------
# Ethereum / ExSat Testnet configuration for wallet
# -----------------------------------------------------------------------------
EXSAT_RPC_URL = os.getenv('EXSAT_RPC_URL', 'https://evm-tst3.exsat.network')
CHAIN_ID      = int(os.getenv('EXSAT_CHAIN_ID', '839999'))

w3 = Web3(Web3.HTTPProvider(EXSAT_RPC_URL))
Account.enable_unaudited_hdwallet_features()

# Azure OpenAI config for AI assistant
AZURE_OPENAI_KEY      = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_MODEL    = os.getenv('AZURE_OPENAI_MODEL', 'gpt-4o')
AZURE_OPENAI_API_VER  = os.getenv('AZURE_OPENAI_API_VER', '2023-06-01-preview')
client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VER,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# -----------------------------------------------------------------------------
# Helper: fetch a page of rune etchings
# -----------------------------------------------------------------------------
def fetch_etchings(offset=0, limit=60):
    resp = requests.get(
        "https://api.rebarlabs.io/runes/v1/etchings",
        params={"offset": offset, "limit": limit},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()

# Helper: generic JSON RPC call to Rebar Shield
# -----------------------------------------------------------------------------
def call_shield(method, params):
    payload = {"jsonrpc":"1.0","id":"1","method":method,"params":params}
    headers = {
        "Content-Type":"application/json",
        "Authorization": f"Bearer {REBAR_SHIELD_KEY}"
    }
    r = requests.post(REBAR_SHIELD_URL, json=payload, headers=headers, timeout=10)
    return r.json()

# Helper: fetch ExSat UTXOs (for tracker)
# -----------------------------------------------------------------------------
def get_exsat_utxos(contract, scope, table, lower_bound=None, limit=50):
    payload = {
        "json": True,
        "code": contract,
        "scope": scope,
        "table": table,
        "limit": limit,
        "reverse": True
    }
    if lower_bound:
        payload['lower_bound'] = lower_bound
    r = requests.post(
        'https://rpc-sg.exsat.network/v1/chain/get_table_rows',
        headers={'Content-Type':'application/json'},
        data=json.dumps(payload), timeout=10
    )
    return r.json().get('rows', []) if r.ok else []

# -----------------------------------------------------------------------------
# Utility to manage active tab in session
# -----------------------------------------------------------------------------
def set_active(tab):
    session['active_tab'] = tab

# -----------------------------------------------------------------------------
# Routes: UTXO Tracker and Data Insights
# -----------------------------------------------------------------------------
@app.route('/tracker')
def tracker():
    rows = get_exsat_utxos('utxomng.xsat','utxomng.xsat','utxos')
    utxos, total = [], 0
    for u in rows:
        sats = int(u.get('value',0)); total += sats
        utxos.append({
            'txid': u['txid'], 'index': u['index'],
            'value_xsat': sats/1e8, 'scriptpubkey': u['scriptpubkey'],
            'id': u['id']
        })
    return render_template('tracker.html', utxos=utxos, total=total/1e8)

@app.route('/data')
def data_insights():
    url = f"{REBAR_DATA_BASE}/bitcoin/blocks/latest"
    headers = {'Authorization': f"Bearer {REBAR_DATA_KEY}", 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, timeout=10)
    stats = r.json() if r.ok else {'error': r.text}
    return render_template('data.html', stats=stats)

# -----------------------------------------------------------------------------
# Routes: Bitcoin HD Wallet (login, addresses)
# -----------------------------------------------------------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        pwd = request.form['password']; action = request.form['action']
        wallet = BitcoinTestnetHDWallet()
        try:
            if action == 'load':
                wallet.load_existing_wallet(pwd)
            else:
                mnemonic = wallet.create_new_wallet()
                flash(f'🔑 Save this mnemonic: {mnemonic}', 'info')
                wallet.save_wallet(pwd)
            session['pwd'] = pwd; session['has_wallet'] = True
            return redirect(url_for('addresses'))
        except FileNotFoundError:
            flash('No wallet found.', 'warning')
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('login.html')

@app.route('/addresses', methods=['GET','POST'])
def addresses():
    if not session.get('has_wallet'): return redirect(url_for('login'))
    if request.method == 'POST':
        cnt = int(request.form['count']); typ = int(request.form['address_type'])
        wallet = BitcoinTestnetHDWallet(); wallet.load_existing_wallet(session['pwd'])
        addrs = wallet.generate_addresses(cnt, typ)
        info = wallet.get_wallet_info()
        return render_template('addresses.html', addresses=addrs, wallet_info=info)
    return render_template('addresses.html', addresses=None, wallet_info=None)

# -----------------------------------------------------------------------------
# Routes: Rune Etchings Explorer
# -----------------------------------------------------------------------------
@app.route('/etchings', methods=['GET'])
def etchings():
    offset       = int(request.args.get('offset', 0))
    limit        = int(request.args.get('limit', 20))
    min_div      = int(request.args.get('min_div', 0))
    symbol_filt  = request.args.get('symbol', None)
    txid_filt    = request.args.get('txid', '').strip()

    page   = fetch_etchings(offset, limit)
    raw    = page.get('results', [])
    filtered = [
        e for e in raw
        if e['divisibility'] >= min_div
        and (symbol_filt is None or e['symbol'] == symbol_filt)
        and (not txid_filt or txid_filt in e['location']['tx_id'])
    ]

    # Reputation and stats
    creator_counts = Counter(e['location']['tx_id'] for e in filtered)
    reputation     = dict(creator_counts)
    top_runes      = Counter(e['name'] for e in filtered).most_common(5)
    top_creators   = creator_counts.most_common(5)
    blocks         = sorted(Counter(e['location']['block_height'] for e in filtered).items())

    # CSV export
    if request.args.get('export') == 'csv':
        si = io.StringIO(); cw = csv.writer(si)
        cw.writerow(['name','symbol','div','txid','block','timestamp'])
        for e in filtered:
            cw.writerow([
                e['name'], e['symbol'], e['divisibility'],
                e['location']['tx_id'], e['location']['block_height'],
                e['location']['timestamp']
            ])
        output = io.BytesIO(si.getvalue().encode())
        return send_file(output, as_attachment=True, mimetype='text/csv', attachment_filename='etchings.csv')

    return render_template(
        'etchings.html', raw=raw, filtered=filtered, page=page,
        top_runes=top_runes, top_creators=top_creators,
        reputation=reputation, offset=offset, blocks=blocks,
        filters={'min_div': min_div, 'symbol': symbol_filt, 'txid': txid_filt}
    )

# -----------------------------------------------------------------------------
# Route: Shield sendrawtransaction
# -----------------------------------------------------------------------------
@app.route('/send', methods=['GET','POST'])
def send_tx():
    txid, error = None, None
    if request.method == 'POST':
        raw_tx = request.form['raw_tx'].strip().lower().removeprefix('0x')
        resp   = call_shield('sendrawtransaction', [raw_tx])
        if resp.get('error'): error = resp['error']
        else:                   txid  = resp.get('result')
    return render_template('send.html', txid=txid, error=error)

# -----------------------------------------------------------------------------
# Routes: ExSat Wallet (EVM) with AI chat
# -----------------------------------------------------------------------------
@app.route('/')
def wallet_index():
    active = session.pop('active_tab', 'create')
    address = session.get('address'); priv = session.get('private_key')
    balance = None
    if address:
        try:
            balance = float(w3.from_wei(w3.eth.get_balance(address), 'ether'))
        except:
            balance = 0
    return render_template(
        'index.html', mnemonic=session.pop('mnemonic', None),
        priv=priv, addr=address, address=address, balance=balance,
        private_key=priv, tx_hash=session.pop('tx_hash', None),
        lookup_result=session.pop('lookup_result', None),
        lookup_error=session.pop('lookup_error', None), active_tab=active
    )

@app.route('/register', methods=['POST'])
def wallet_register():
    pwd = request.form['password']
    m   = Mnemonic('english')
    mnemonic = m.generate(128)
    seed     = m.to_seed(mnemonic, passphrase=pwd)
    acct     = Account.from_key('0x' + seed.hex()[:64])
    session['private_key'] = acct.key.hex()
    session['address']     = acct.address
    session['mnemonic']    = mnemonic
    set_active('send')
    return redirect(url_for('wallet_index'))

@app.route('/login_priv', methods=['POST'])
def wallet_login_priv():
    key  = request.form['privkey'].strip()
    acct = Account.from_key(key)
    session['private_key'] = acct.key.hex()
    session['address']     = acct.address
    set_active('send')
    return redirect(url_for('wallet_index'))

@app.route('/login_mnemonic', methods=['POST'])
def wallet_login_mnemonic():
    data = request.form
    m     = Mnemonic('english')
    seed  = m.to_seed(data['mnemonic'], passphrase=data.get('passphrase', ''))
    acct  = Account.from_key('0x' + seed.hex()[:64])
    session['private_key'] = acct.key.hex()
    session['address']     = acct.address
    set_active('send')
    return redirect(url_for('wallet_index'))

@app.route('/logout')
def wallet_logout():
    session.clear()
    set_active('create')
    return redirect(url_for('wallet_index'))

@app.route('/send_eth', methods=['POST'])
def wallet_send():
    pk   = request.form['private_key']
    acct = Account.from_key(pk)
    nonce = w3.eth.get_transaction_count(acct.address)
    tx = {
        'nonce': nonce,
        'to': request.form['to_address'],
        'value': w3.to_wei(float(request.form['amount']), 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'chainId': CHAIN_ID
    }
    signed = w3.eth.account.sign_transaction(tx, pk)
    txh    = w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    session['tx_hash'] = txh
    set_active('send')
    return redirect(url_for('wallet_index'))

@app.route('/txlookup', methods=['POST'])
def wallet_txlookup():
    h = request.form['txhash'].strip()
    try:
        tx      = w3.eth.get_transaction(h)
        receipt = w3.eth.get_transaction_receipt(h)
        info    = {k: (v.hex() if isinstance(v, HexBytes) else v) for k,v in dict(tx).items()}
        info['status'] = receipt.status
        session['lookup_result'] = json.dumps(info, indent=2)
    except Exception as e:
        session['lookup_error']  = str(e)
    set_active('lookup')
    return redirect(url_for('wallet_index'))

@app.route('/ai', methods=['POST'])
def wallet_ai():
    data = request.get_json()
    resp = client.chat.completions.create(
        model=AZURE_OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are an ExSat wallet assistant."},
            {"role": "user",   "content": data.get('msg', '')}
        ]
    )
    return jsonify(response=resp.choices[0].message.content.strip())

# -----------------------------------------------------------------------------
# Main entrypoint
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv('PORT', '5000')))
