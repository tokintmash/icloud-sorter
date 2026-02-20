# iCloud Photo Downloader

Download your iCloud photos and videos locally, organized by album.

## Features

- 🔐 Secure iCloud authentication with 2FA support
- 📁 Browse and select albums to download
- 📊 Real-time download progress with speed and ETA
- ⏸️ Pause, resume, and cancel downloads
- 🔄 Incremental sync — only downloads new photos
- 💾 Atomic writes — no corrupted files from interrupted downloads

## Prerequisites

Before getting started, please read the [Prerequisites Guide](docs/PREREQUISITES.md) — you'll need to configure your iCloud account settings.

**Required software:** Python 3.10+, Node.js 18+

## Quick Start

```bash
# Clone the repository
git clone https://github.com/tokintmash/icloud-downloader.git
cd icloud-downloader

# Set up the backend
cd backend
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Build the frontend
cd ../frontend
npm install
npm run build

# Run the application
cd ../backend
python app.py
```

Then open `http://localhost:8000` in your browser.

## Development

See the [Development Guide](docs/DEVELOPMENT.md) for running the project in development mode with hot reloading.

## How It Works

1. **Login** with your Apple ID (2FA supported)
2. **Browse** your iCloud photo albums
3. **Select** albums to download
4. **Download** — photos are saved to your chosen directory, organized by album

## Disclaimer

This is an **unofficial project** not affiliated with Apple. See [DISCLAIMER.md](DISCLAIMER.md) for details.

## License

MIT — see [LICENSE](LICENSE) for details.
