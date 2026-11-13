# Privacy Policy for InstaReciprocal

**Last updated:** November 13, 2026

InstaReciprocal is built on a **local-first, privacy-by-design** architecture. Your Instagram data belongs solely to you and remains entirely on your local machine.

---

### 1. No Login Credentials or Session Tokens
- InstaReciprocal **never** requests, collects, stores, or transmits your Instagram username, password, two-factor authentication codes, session cookies, or API access tokens.
- You do not log in to Instagram within the application. The application works exclusively with the data export files you manually download from Instagram via Meta's "Download your information" feature.

### 2. Complete Local Processing
- All parsing, normalization, comparison, filtering, and report generation occur strictly on your local computer.
- No analytics, tracking pixels, crash telemetry, or third-party monitoring services are embedded in the software.

### 3. Local Data Storage & User Ownership
- All application data is stored in standard local files within your application folder:
  - `data/whitelist.json`: Your locally designated protected accounts.
  - `data/instareciprocal.db`: Your local SQLite database containing manual review statuses and scan history.
  - `exports/`: Locally generated CSV and JSON reports.
- None of this data is ever synced or uploaded to external servers or cloud services.
- You can delete your database, reports, or history at any time by clearing the `data` and `exports` folders.

### 4. Outbound Connections
- InstaReciprocal does not make automated outbound network requests to Instagram or any other server.
- The only network-related feature is the optional "Open profile" button, which opens the public Instagram profile (`https://www.instagram.com/{username}/`) in your default web browser via your operating system's standard URL handler.

### 5. Safety & No Automated Actions
- InstaReciprocal **never** performs automated follows, unfollows, likes, comments, or direct messages.
- Any decision to unfollow an account must be carried out manually by you in your browser or mobile app. The application merely records your personal manual review confirmation.

---

### 6. Contact & Open Source
InstaReciprocal is open source under the MIT License. You can inspect the complete source code and build process at:  
https://github.com/saurabhkr1825-svg/instareciprocal
