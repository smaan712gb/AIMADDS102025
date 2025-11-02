# 🚀 AIMADDS Platform - Client Onboarding Guide

## Welcome to AIMADDS

Your AI-powered M&A due diligence platform is now live and ready for clients!

---

## 🌐 Access URLs

### Production Platform:
```
https://storage.googleapis.com/amadds102025-frontend/index.html
```

### API & Documentation:
```
Backend API:  https://aimadds-backend-zex5qoe5gq-uc.a.run.app
API Docs:     https://aimadds-backend-zex5qoe5gq-uc.a.run.app/docs
GitHub Code:  https://github.com/smaan712gb/AIMADDS102025
```

### Future Custom Domain URLs (After DNS Verification):
```
Platform:     https://app.aimadds.com
API:          https://api.aimadds.com
Email:        support@aimadds.com
```

---

## 🔐 Admin Access

**Your Admin Credentials:**
```
Email:    smaan2011@gmail.com
Password: admin123
```

⚠️ **CHANGE THIS PASSWORD IMMEDIATELY** after first login!

---

## 👥 Adding Users for Clients

### Method 1: Via API Documentation (Easiest)

1. **Go to API Docs:**
   ```
   https://aimadds-backend-zex5qoe5gq-uc.a.run.app/docs
   ```

2. **Login to Get Token:**
   - Find `POST /api/auth/login`
   - Click "Try it out"
   - Enter:
     ```json
     {
       "email": "smaan2011@gmail.com",
       "password": "admin123"
     }
     ```
   - Click "Execute"
   - **Copy the `access_token`** from response

3. **Authorize API:**
   - Click "Authorize" button (top right)
   - Paste token: `Bearer YOUR_TOKEN`
   - Click "Authorize"

4. **Add New User:**
   - Find `POST /api/auth/register`
   - Click "Try it out"
   - Enter:
     ```json
     {
       "email": "client@company.com",
       "password": "TempPassword123!",
       "role": "user"
     }
     ```
   - Click "Execute"

5. **Share Credentials with Client:**
   ```
   Platform: https://storage.googleapis.com/amadds102025-frontend/index.html
   Email: client@company.com
   Password: TempPassword123!
   ```

### Method 2: Via PowerShell/Curl

```powershell
# 1. Login as admin
$loginResponse = Invoke-RestMethod -Uri "https://aimadds-backend-zex5qoe5gq-uc.a.run.app/api/auth/login" -Method Post -Body (@{email="smaan2011@gmail.com"; password="admin123"} | ConvertTo-Json) -ContentType "application/json"

$token = $loginResponse.access_token

# 2. Add new user
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$newUser = @{
    email = "client@company.com"
    password = "TempPassword123!"
    role = "user"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://aimadds-backend-zex5qoe5gq-uc.a.run.app/api/auth/register" -Method Post -Headers $headers -Body $newUser

# 3. List all users
Invoke-RestMethod -Uri "https://aimadds-backend-zex5qoe5gq-uc.a.run.app/api/auth/users" -Headers $headers
```

---

## 📧 Email Template for Clients

```
Subject: Welcome to AIMADDS M&A Due Diligence Platform

Dear [Client Name],

Welcome to AIMADDS - your AI-powered M&A due diligence platform!

🔐 Your Access Credentials:
Platform: https://storage.googleapis.com/amadds102025-frontend/index.html
Email: [client email]
Password: [temporary password]

⚠️ Please change your password after first login!

📊 What You Can Do:
✅ Analyze M&A deals in 15-30 minutes
✅ Get investment committee-ready reports
✅ DCF valuation with Monte Carlo simulation
✅ 18 specialized AI agents working for you
✅ Download Excel, PowerPoint, and PDF reports

🎯 Getting Started:
1. Click the platform link
2. Login with credentials above
3. Click "New Analysis"
4. Enter target company ticker (e.g., NVDA, MSFT)
5. Watch AI agents work in real-time!

💡 Example Analysis:
Try analyzing NVIDIA (NVDA) or Microsoft (MSFT) to see the system in action.

📚 Need Help?
- View our technology: https://github.com/smaan712gb/AIMADDS102025
- Contact: smaan2011@gmail.com or support@aimadds.com

Best regards,
The AIMADDS Team
```

---

## 🎯 User Capabilities

### Regular Users Can:
- ✅ Login to platform
- ✅ Start M&A analyses
- ✅ View their own analyses
- ✅ Download reports (Excel, PowerPoint, PDF)
- ✅ Access real-time progress updates
- ✅ Use all 18 AI agents

### Regular Users CANNOT:
- ❌ See other users' analyses
- ❌ Add or delete users
- ❌ Access admin features
- ❌ View system-wide statistics

### Admins Can:
- ✅ Everything regular users can do
- ✅ Add new users
- ✅ Delete users
- ✅ View all analyses from all users
- ✅ List all users in system
- ✅ Change user roles

---

## 📊 Client Usage Example

### Scenario: Client Wants to Analyze NVIDIA Acquisition

1. **Client logs in**
2. **Clicks "New Analysis"**
3. **Enters:**
   - Project Name: "NVIDIA Acquisition Analysis"
   - Target Ticker: NVDA
   - Deal Type: Acquisition
   - (Optional) Acquirer Ticker: MSFT
   - (Optional) Deal Value: $50,000,000,000

4. **Clicks "Start Analysis"**
5. **Watches real-time progress:**
   - 18 AI agents execute sequentially
   - Each agent shows detailed progress
   - Takes 15-30 minutes total

6. **Gets Results:**
   - Executive summary with top findings
   - Valuation range (Bull/Base/Bear cases)
   - Top risks and opportunities
   - Go/no-go recommendation

7. **Downloads Reports:**
   - Glass Box Excel (6 tabs with formulas)
   - C-Suite PowerPoint (investment committee deck)
   - Diligence Bible PDF (complete narrative)

---

## 🔒 Security & Data Privacy

### Data Isolation:
- Each user only sees their own analyses
- User data stored in separate database records
- Admin can see all (for support purposes)

### Security Features:
- ✅ JWT token authentication
- ✅ HTTPS/SSL encryption
- ✅ Google Cloud security
- ✅ Role-based access control
- ✅ Secure password hashing (bcrypt)
- ✅ 8-hour session timeout

### What's Protected:
- User credentials encrypted
- API keys in Secret Manager
- Database credentials secured
- Reports stored in private Cloud Storage
- All traffic encrypted (HTTPS)

---
