# How to Fix "Demo Mode" Banner

The "Demo Mode" banner appears when the frontend cannot connect to the backend API. Here's how to fix it:

## ✅ Solution

### Step 1: Ensure Backend is Running

Check if backend is running:
```bash
cd agentic-aws-nvidia-demo/services/orchestrator
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The backend should respond at: http://localhost:8080/health

### Step 2: Create Frontend .env File

A `.env` file has been created in `frontend/` directory. If it's missing, create it:

```bash
cd frontend
cat > .env << 'EOF'
VITE_API_URL=http://localhost:8080
EOF
```

### Step 3: Restart Frontend

**Important:** After creating/updating `.env`, you MUST restart the frontend dev server:

1. Stop the current frontend server (Ctrl+C)
2. Start it again:
```bash
cd frontend
npm run dev
```

Vite needs a restart to pick up new environment variables!

### Step 4: Verify Connection

1. Open browser console (F12)
2. Check for any API errors
3. The demo mode banner should disappear if API is accessible

## 🔍 Troubleshooting

### If banner still appears:

1. **Check backend is accessible:**
   ```bash
   curl http://localhost:8080/health
   ```
   Should return: `{"status":"healthy",...}`

2. **Check CORS:**
   - Backend should allow frontend origin
   - Check `app/main.py` CORS settings
   - Currently set to allow all origins (`allow_origins=["*"]`)

3. **Check API endpoint:**
   ```bash
   curl http://localhost:8080/stories
   ```
   Should return stories array (may be empty: `[]`)

4. **Clear browser cache:**
   - Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

5. **Check browser console:**
   - Look for network errors in DevTools > Network tab
   - Check Console for CORS errors

## 🎯 Quick Fix (Hide Banner Temporarily)

If you want to hide the demo mode banner for demonstration purposes while keeping demo data, you can modify the condition in the component files:

**Option 1:** Comment out the demo banner in:
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/StoriesList.tsx`
- `frontend/src/pages/StoryEditor.tsx`
- `frontend/src/pages/CharactersPage.tsx`

Look for:
```tsx
{usingDemo && (
  <div className="bg-warning/20...">
    ...
  </div>
)}
```

**Option 2:** Always show real API data by modifying the error handling to not fall back to demo data (not recommended for hackathon demo).

## 📝 Notes

- The `.env` file is gitignored and won't be committed
- Environment variables prefixed with `VITE_` are exposed to the frontend
- After changing `.env`, always restart the Vite dev server
