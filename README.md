# ChainWallet

![ChainWallet Logo](https://example.com/chainwallet-logo.png)

ChainWallet is a user-friendly, vendor-aware cryptocurrency wallet designed for seamless on-chain payments and Proof of Transaction (PoT) verification. Featuring AI-guided interactions, support for Bitcoin mainnet and testnet, Ethereum-compatible (EVM) wallet creation, UTXO tracking, Rune Etchings exploration, and integrated data insights via Rebar, ChainWallet empowers users and vendors alike with instant transaction proof and a frictionless experience.

---

## 🚀 Features

* **Seamless BTC Transactions** via Bitcore & Drivechain Thunder
* **Proof of Transaction (PoT)** passes for vendors when a payment meets a set threshold
* **Mnemonic + Password** wallet creation (no browser extensions required)
* **Raw TX Broadcast** using Rebar Shield API
* **UTXO Tracking** with xSat Wallet Tracker
* **Rune Etchings Explorer** integration for on-chain metadata
* **Testnet Address Generation** (P2PKH, P2SH, Bech32)
* **Live Market Data** (BTC, ETH, USD) via TradingView & Rebar Data Insights
* **AI Assistant** powered by Azure OpenAI for seamless UX guidance

---

## 🏗️ Architecture & Tech Stack

* **chainwallet app:** Flask
* **Drivechain redesign** React, Tailwind CSS, Bootstrap (fallback)
* **Blockchain Layers and data:**

  * Rebar  data
  * Rebar Shield on Alkanes
  * Bitcoin Mainnet & Testnet (native UTXO)
  * ExSat EVM & Drivechain Thunder (account-based sidechain)
* **APIs & Libraries:**

  * `bitcore-lib`, `bitcoinjs-lib` for TX construction
  * `get-port`, `electron` for dynamic port detection & desktop app
  * `TradingView` widget for live price tickers
  * `AzureOpenAI` for chat-based guidance

---

## 🚧 Installation & Setup

1. **Clone repository**

   ```bash
   git clone https://github.com/jerryblessed/chainwallet.git
   cd ChainWallet
   ```
2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Use sample environment variables**

   ```
   simply change .env.sample to .env and use for testing alone
   ```
   ### or

4. **Set environment variables** in `.env`:
  

   ```dotenv
   FLASK_SECRET=your_flask_secret
   REBAR_SHIELD_KEY=...
   REBAR_DATA_KEY=...
   EXSAT_RPC_URL=https://evm-tst3.exsat.network
   AZURE_OPENAI_KEY=...
   AZURE_OPENAI_ENDPOINT=...
   ```
5. **Start the wallet app**

   ```bash
   python app.py
   ```

---

## 🧱 Usage

* **Create/Login:** Generate or load wallets without extensions.
* **Send Funds:** Choose EVM or Bitcoin flows — use PoT checker for vendor passes.
* **Explore Data:** View UTXOs, Rune Etchings, and live market charts.
* **AI Chat:** Click 💬 to ask questions about addresses, TXs, or workflows.

---

## 🧩 Configuration & Customization

* **Threshold Settings:** Adjust PoT threshold in `config.py` (
  `POT_THRESHOLD_ETH = 0.001`).
* **Explorer URL:** Change block explorer links in `settings.js`.
* **UI Themes:** Switch light/dark modes via ThemeContext.

---

## 🎉 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please follow the code style and include tests for new features.

---

## 📄 License

MIT © Jeremiah & Contributors

---

## 🙏 Acknowledgments

* **Bitcoin community** for BIP standards
* **LayerTwo Labs** for Drivechain Thunder
* **Rebar Labs** for Shield & Data APIs
* **Azure OpenAI** for AI assistance
