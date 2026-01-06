# 🚀 Notion Life OS: Fully Automated Diary (Auto-Sync)

**A Fully Automated Life OS Diary System for Notion**

> A powerful variant based on [duolingo2notion](https://github.com/malinkang/duolingo2notion). This is not just a Duolingo syncer, but a complete "Life OS" daily management automation.

![License](https://img.shields.io/badge/license-MIT-green) ![Python](https://img.shields.io/badge/python-3.9-blue) ![Notion](https://img.shields.io/badge/Notion-API-black)

## 🌟 Key Features

Most Notion automations only do one thing. This project aims for **"A Fully Automated Day"**:

1.  **📅 Auto-Create Daily Log**:
    * Automatically generates a diary page every morning at 00:05.
    * **Smart Relations**: Automatically links the day to the correct **Year**, **Month**, **Week**, and **All** databases. No manual linking required.
    * Supports dynamic icons (Calendar icon matches the current date).

2.  **🦉 Duolingo Integration**:
    * Seamlessly fetches your daily Duolingo learning stats (XP, Study Time, Lessons).
    * Inserts a beautiful "Callout Block" into your diary page.

3.  **✍️ Auto Word Count**:
    * Scans your diary page content every night at 23:45.
    * Counts your words automatically and fills the `Word Count` property.
    * Enables monthly/yearly word count stats via Notion Rollups.

4.  **🎨 Ultimate Gallery View Support**:
    * Designed for Notion Formula 2.0.
    * Provides **Rainbow Progress Bars** and **Mood Spectrum Bars**.
    * Visualizes your monthly progress, word counts, and mood distribution in the Gallery View.

---

## 🛠️ Preview

### 📊 Monthly Gallery
_Visualize your month with progress bars and mood spectrums._
![Monthly View](https://via.placeholder.com/800x400?text=Place+Your+Screenshot+Here)

### 📝 Daily Page
_Auto-generated page with Duolingo stats and auto-relations._
![Daily Page](https://via.placeholder.com/800x400?text=Place+Your+Screenshot+Here)

---

## ⚙️ Setup Guide

### 1. Notion Database Setup
You need a "Life OS" system with the following databases. (It is recommended to duplicate a compatible template).

Databases required: **Day**, **Week**, **Month**, **Year**, **All**.

**Required Properties in "Day" Database:**
*(Case Sensitive)*

| Property Name | Type | Description |
| :--- | :--- | :--- |
| `Name` | Title | The title of the page |
| `Date` | Date | The date of the entry |
| `Word Count` | Number | Stores the word count |
| `Mood` | Relation | Links to your Mood database |
| `Year` | Relation | Links to the Year database |
| `Month` | Relation | Links to the Month database |
| `Week` | Relation | Links to the Week database |
| `All` | Relation | Links to the All database |

### 2. Fork this Repository
Click the **Fork** button at the top right of this page to copy this code to your GitHub account.

### 3. Configure GitHub Secrets
Go to your repository **Settings** -> **Secrets and variables** -> **Actions**, and add the following secrets:

| Secret Name | Description |
| :--- | :--- |
| `NOTION_TOKEN` | Your Notion Integration Token |
| `NOTION_PAGE` | Link to your Life OS dashboard page |
| `JWT` | Duolingo JWT Token (Find it in browser cookies) |
| `USER_NAME` | Duolingo Username |

### 4. Automation Schedule
The workflow is handled by GitHub Actions:
* **00:05 (UTC+8)**: Creates the daily page & syncs Duolingo.
* **23:45 (UTC+8)**: Counts words and updates the page.

---

## 🧠 Advanced: Notion Formulas

This project works best with my custom Notion Formulas 2.0 for Gallery Views.

**Example Code for Mood Spectrum Bar:**

```javascript
/* Paste the formula code here or link to your blog/gist */
