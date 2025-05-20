from flask import Flask, request, render_template_string
import requests
import json

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ title }}</title>
  <style>
    body { font-family: sans-serif; background: #f4f4f4; padding: 2rem; }
    .container { max-width: 600px; margin: auto; background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
    h1 { text-align: center; margin-bottom: 1rem; }
    form { display: flex; gap: .5rem; margin-bottom: 1rem; }
    input[type=text] { flex: 1; padding: .5rem; font-size: 1rem; }
    button { padding: .5rem 1rem; font-size: 1rem; }
    .error { color: red; margin-top: 1rem; }
    .info { color: #555; margin-top: 1rem; }
    .pass { color: green; font-size: 1.2rem; margin-top: 1rem; }
    .fail { color: orange; font-size: 1.2rem; margin-top: 1rem; }
    pre { background: #eee; padding: 1rem; overflow-x: auto; margin-top: 1rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>{{ title }}</h1>
    <form id="txForm" method="POST">
      <input name="txhash" type="text" placeholder="Enter transaction hash…" required
             value="{{ txhash|default('') }}" />
      <button type="submit">Lookup</button>
    </form>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    {% if value is not none %}
      <div class="info">💰 Value Sent: {{ value }} BTC</div>
      {% if pot_pass %}
        <div class="pass">🎫 POT Pass Granted!</div>
      {% else %}
        <div class="fail">🔒 POT requires ≥ 0.001 BTC</div>
      {% endif %}
    {% endif %}

    {% if result %}
      <pre>{{ result }}</pre>
    {% endif %}
  </div>

  <script>
    document.getElementById('txForm').addEventListener('submit', e => {
      const v = e.target.txhash.value.trim();
      if (!v.startsWith('0x') || v.length < 10) {
        alert('Please enter a valid hash.');
        e.preventDefault();
      }
    });
  </script>
</body>
</html>
"""

RPC_URL = "https://evm-tst3.exsat.network"
THRESHOLD_ETH = 0.001

def fetch_tx(tx_hash):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getTransactionByHash",
        "params": [tx_hash],
        "id": 1
    }
    resp = requests.post(RPC_URL, json=payload, headers={"Content-Type":"application/json"}, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    if data.get("result") is None:
        raise ValueError("No such transaction")
    return data["result"]

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    result = None
    txhash = ""
    value = None
    pot_pass = False

    title = "ChainWallet POT Checker"

    if request.method == "POST":
        txhash = request.form.get("txhash", "").strip()
        try:
            tx = fetch_tx(txhash)
            # parse and convert hex wei to ETH
            wei = int(tx["value"], 16)
            value = round(wei / 1e18, 6)
            pot_pass = (value >= THRESHOLD_ETH)
            # adjust title for non-pass
            if not pot_pass:
                title = "POT for 0.001 BTC worth of book"
            # pretty-print JSON
            result = json.dumps(tx, indent=2)
        except ValueError:
            error = "❌ Transaction not found. Enter a valid hash."
        except Exception as e:
            error = f"❌ Error: {e}"

    return render_template_string(
        TEMPLATE,
        title=title,
        error=error,
        result=result,
        txhash=txhash,
        value=value,
        pot_pass=pot_pass
    )

if __name__ == "__main__":
    app.run(port=8080)
