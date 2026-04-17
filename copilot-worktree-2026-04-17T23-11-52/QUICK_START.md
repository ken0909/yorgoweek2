# ⚡ Quick Start Guide

Get the Real Estate Agent running in **5 minutes**.

## Prerequisites

- Python 3.11+ installed
- Google Gemini API key (free from https://makersuite.google.com/app/apikeys)
- Ames Housing dataset (train.csv from Kaggle)

## Step 1: Setup Environment (2 minutes)

```bash
# Create .env file
cp .env.template .env

# Edit .env with your API key (open in any text editor)
# Find this line and add your key:
# GEMINI_API_KEY=your_gemini_api_key_here
```

**Windows users**: Use Notepad to edit `.env`

```bash
# Install dependencies
pip install -r requirements.txt
```

## Step 2: Train ML Model (5 minutes)

Download `train.csv` from Kaggle and place it in the project root.

```bash
# Open Jupyter notebook
jupyter notebook ml_pipeline.ipynb

# In Jupyter, run ALL cells in order:
# - Cell 1-8: Sections 1-8
# - Wait for output after each section
# - Section 7 generates model files: pipeline.joblib + train_stats.json
# - After Section 8, close notebook
```

**Expected**: Two files created:
- `app/model/pipeline.joblib` (10-50 MB)
- `app/model/train_stats.json` (~1 KB)

## Step 3: Start Backend (1 minute)

**Terminal 1**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Expected output**:
```
Uvicorn running on http://0.0.0.0:8000
```

## Step 4: Start Frontend (1 minute)

**Terminal 2**:
```bash
streamlit run streamlit_app.py
```

**Expected**: Browser opens to `http://localhost:8501`

## Step 5: Test It!

In Streamlit UI:

1. **Text input**: Type a house description
   ```
   Example: "3 bedroom house, 2 baths, good neighborhood, built in 2010"
   ```

2. **Click**: "Extract Features"
   - See extracted fields (green checkmarks)
   - See missing fields (input boxes)

3. **Fill in** missing fields (optional)

4. **Click**: "Predict Price"
   - See predicted price
   - See AI interpretation
   - See market context

Done! 🎉

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run: `pip install -r requirements.txt` |
| `.env` not working | Check `.env` is in project root (not in subdirectory) |
| `Pipeline not found` | Run ml_pipeline.ipynb Section 7 |
| `Cannot connect backend` | Check Terminal 1 is running `uvicorn` |
| `Port 8000 in use` | Kill process: `lsof -ti:8000` (macOS/Linux) or change port |
| `Port 8501 in use` | Run: `streamlit run streamlit_app.py --logger.level=debug --server.port=8502` |

---

## 📚 Next Steps

1. **Understand the system**: Read `README.md` for architecture overview
2. **Learn the code**: Read `IMPLEMENTATION_GUIDE.md` for deep dive
3. **Run examples**: See `PROJECT_SUMMARY.md` for test queries and results
4. **Verify deployment**: Use `CHECKLIST.md` for full testing

---

## 🚀 Docker Deployment (Optional)

```bash
# Build image
docker build -t real-estate-agent:v1 .

# Run container
docker run -p 8000:8000 --env-file .env real-estate-agent:v1

# Test
curl http://localhost:8000/health
```

---

## 💡 Tips

- **Keep both terminals open** (Terminal 1 = backend, Terminal 2 = frontend)
- **Logs visible in Terminal 1** help debug API issues
- **Reload Streamlit** if UI looks stuck (press R in Terminal 2)
- **Test with realistic queries** like: "4 bed, 2.5 bath, granite counters, 2020 build, excellent condition"

---

## 📖 Documentation

- `README.md` — Full guide and reference
- `FILE_MANIFEST.md` — Description of all files
- `CHECKLIST.md` — Pre-deployment verification
- `ARCHITECTURE_DIAGRAM.txt` — Visual system design
- `IMPLEMENTATION_GUIDE.md` — Deep technical dive
- `PROJECT_SUMMARY.md` — Examples and learning outcomes

---

## ❓ FAQ

**Q: What if Gemini API returns invalid JSON?**
A: The system catches the error, returns empty features, and UI asks you to fill them in manually.

**Q: What if the ML model isn't found?**
A: Make sure you ran `ml_pipeline.ipynb` Section 7 (generates `pipeline.joblib`).

**Q: Can I change the 10 features?**
A: No — they're locked to the Ames Housing dataset. To add features, you must retrain the model in the notebook.

**Q: How long does prediction take?**
A: 3-8 seconds (Gemini API + model inference + interpretation).

**Q: Can I use this in production?**
A: Not yet — it's single-threaded, no authentication, and no database. Add these before production.

---

## ✅ Verify Installation

Check this output:

```bash
# Terminal 1 should show:
Uvicorn running on http://0.0.0.0:8000

# Terminal 2 should show:
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501

# Browser should show:
[Text input] [Extract Features button]
```

If all three show up, you're ready! 🚀

---

## 📞 Help

If stuck, check:
1. **Requirements met?** Python 3.11+, pip working, API key valid
2. **Files generated?** Check `app/model/` has `.joblib` and `.json`
3. **Both terminals running?** Ctrl+C stops, `pip install -r requirements.txt` fixes missing packages
4. **Ports available?** 8000 and 8501 must be free

Still stuck? Read **TROUBLESHOOTING** in `README.md`

---

**You're all set! Start with Step 1 above.** ✨
