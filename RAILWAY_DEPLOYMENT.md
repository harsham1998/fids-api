# Railway Deployment Guide for FIDS API

## 🚀 Quick Fix for Current Deployment

The error you're seeing is because Railway needs the Microsoft ODBC drivers to be installed. I've updated your files to fix this:

### ✅ Files Updated:
1. **Dockerfile** - Now installs ODBC Driver 18 for SQL Server
2. **main.py** - Added Railway environment detection and proper app export
3. **test_railway_db.py** - Test script to verify database connection

## 🔧 Deployment Steps

### 1. **Push Updated Code to GitHub**
```bash
git add .
git commit -m "Fix Railway deployment with ODBC drivers"
git push origin main
```

### 2. **Railway Environment Variables**
Set these in your Railway dashboard:
```
SQL_SERVER_HOST=sqlserverdb.cgt0oi2i2k3f.us-east-1.rds.amazonaws.com
SQL_SERVER_DATABASE=FIDS_DEV
SQL_SERVER_USERNAME=admin
SQL_SERVER_PASSWORD=Admin12345!
SECRET_KEY=ef6c5b4b31266d534b7069822ec1b4eee82d014cab206dbd1cc5e73693db7604
RAILWAY_ENVIRONMENT=production
```

### 3. **Redeploy**
Railway will automatically redeploy when you push to GitHub. The new Dockerfile will:
- Install Ubuntu base image
- Install Python 3 and required system packages
- Install Microsoft ODBC Driver 18 for SQL Server
- Install your Python dependencies
- Run your Flask app with gunicorn

## 🧪 Test Locally First (Optional)

Before deploying, you can test locally:
```bash
cd api
python3 test_railway_db.py
```

This will verify your database connection works.

## 🌐 After Deployment

### 1. **Get Your Railway API URL**
After successful deployment, Railway will give you a URL like:
`https://your-app-name.up.railway.app`

### 2. **Update Frontend Environment**
Update your frontend `.env.production`:
```
VITE_API_URL=https://your-railway-app.up.railway.app
```

### 3. **Test API Endpoints**
```bash
# Health check
curl https://your-railway-app.up.railway.app/api/health

# Get flights
curl https://your-railway-app.up.railway.app/api/flights?page=1&per_page=7
```

## 🔍 What Changed

### Dockerfile Changes:
- ✅ Uses Ubuntu 22.04 (better ODBC support)
- ✅ Installs Microsoft ODBC Driver 18
- ✅ Installs unixodbc-dev for pyodbc
- ✅ Keeps ADB tools for your existing functionality

### main.py Changes:
- ✅ Added `RAILWAY_ENVIRONMENT` detection
- ✅ Added proper `application = app` export for gunicorn
- ✅ Updated CORS to allow Railway domains
- ✅ Updated SocketIO CORS settings

## 🐛 If Still Having Issues

### Check Railway Logs:
1. Go to your Railway dashboard
2. Click on your service
3. Check "Deploy Logs" for any errors

### Common Issues:
1. **Environment variables not set** - Make sure all SQL Server credentials are set in Railway
2. **SQL Server not accessible** - Ensure your AWS RDS allows connections from Railway IPs
3. **Port issues** - Railway automatically handles port mapping

## 🎯 Expected Result

After this fix, your Railway deployment should:
- ✅ Start without ODBC driver errors
- ✅ Connect to your AWS SQL Server database
- ✅ Serve REST API endpoints
- ✅ Support WebSocket connections for real-time updates
- ✅ Handle CORS properly for your frontend

The deployment should show:
```
✅ Database connection successful
🚀 Starting FIDS API server...
```

Let me know if you need any clarification or if you encounter other issues!
