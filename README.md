# STM Bus Delay Predictor

Predicting bus delays on the Montréal STM network using real-time GTFS data and machine learning.

> 🚧 **Work in progress** — this project is being built step by step as a hands-on way to learn machine learning, from data collection to deployment.

## Why this project?

I wanted to learn machine learning on real, messy, live data rather than a ready-made Kaggle dataset.
My local transit agency (RTC, Québec City) does not publish open real-time data, so I built this
project on the STM's GTFS-realtime feed instead.

The goal: given a bus line, a stop and a time, predict how late the bus will be.

## Roadmap

- [x] **Data access** — read and decode the STM GTFS-realtime feed (Protocol Buffers)
- [x] **Collector** — continuously record vehicle positions and trip updates
- [ ] **Static GTFS** — join real-time data with planned schedules to compute actual delays
- [ ] **Exploratory analysis** — which lines, hours and conditions cause the most delays?
- [ ] **Baseline model** — a naive "average delay at this hour" model to beat
- [ ] **ML model** — gradient boosting (LightGBM) with temporal and weather features
- [ ] **Evaluation** — error analysis and comparison against the baseline
- [ ] **API & demo** — FastAPI prediction service and an interactive Streamlit dashboard

## Tech stack

- **Python 3**
- **requests**, **gtfs-realtime-bindings** — data access and Protocol Buffers decoding
- More to come: pandas, LightGBM, FastAPI, Streamlit

## Getting started

### 1. Get an STM API key

1. Create a free account on the [STM developer portal](https://portail.developpeurs.stm.info/apihub).
2. Subscribe to the **GTFS-realtime** API (v2).
3. Generate an API key.

### 2. Install

```bash
git clone https://github.com/stephanebaribeau/stm-retards.git
cd stm-retards
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure

Create a `.env` file at the project root:

```
STM_API_KEY=your_api_key_here
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### 4. Run

```bash
python src/explorer_flux.py
```

This fetches the current vehicle positions and prints a summary of the feed.

## Project structure

```
stm-retards/
├── src/
│   └── explorer_flux.py   # Fetch and inspect the real-time feed
│   └── collecteur.py      # Continuously record vehicle positions and trip updates
├── requirements.txt
├── .gitignore
└── README.md
```

## Data source & license

Real-time data is provided by the [Société de transport de Montréal (STM)](https://www.stm.info/en/about/developers)
under the [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.
Data © Société de transport de Montréal.

This project is not affiliated with or endorsed by the STM.
