#!/bin/bash
# Arka planda API'yi başlat
uvicorn main:app --host 0.0.0.0 --port 8000 &
# Ön planda Streamlit'i başlat
streamlit run ui.py --server.port $PORT --server.address 0.0.0.0