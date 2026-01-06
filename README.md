# 🚀 Notion Life OS: Fully Automated Diary (Auto-Sync)

**A Fully Automated Notion Life OS Diary System**

[中文](https://www.google.com/search?q=README_CHINESE.md) | [English](README.md)

> A secondary development based on `duolingo2notion`. This is an automated "Life OS" daily diary management system.

## 🌟 Key Features

Most Notion automation scripts on the market offer only single functions. The goal of this project is **"A Fully Automated Day"**:

### 📅 Auto-Create Daily Diary

* **Automatic Generation**: Automatically generates the daily diary Page every morning.
* **Smart Relations**: Automatically calculates and links to the corresponding **Year**, **Month**, **Week**, and **All** databases. No manual maintenance required.
* **Dynamic Icons**: Supports calendar icons that change dynamically based on the current date.
* **Historical Data Support**: Supports importing old entries (Run the "Backfill Old Data" workflow in GitHub Actions manually after import).

### ✍️ Smart Word Count

* **Auto-Scan**: Scans the day's diary content every night.
* **Auto-Update**: Automatically counts words and fills the property, enabling monthly/yearly word count summaries via Notion Rollups.

### 🎨 Ultimate Gallery View Support

* **Formula 2.0**: Powered by Notion Formula 2.0, offering **Rainbow Progress Bars** and **Mood Spectrum** formulas.
* **Visual Stats**: Automatically displays entry progress, word count summaries, and mood distribution bars in Month/Week/Year Gallery views.

## 🛠️ Preview

* **Monthly Gallery**: Automatically visualizes monthly progress and mood distribution.
* **Daily Page**: Automatically links all hierarchy levels (Year/Month/Week).

## ⚙️ How to Use

### 1. Prepare Notion Databases

You need a "Life OS" system with the following hierarchy (It is recommended to duplicate the template directly):

* **Day**
* **Week**
* **Month**
* **Year**
* **All**

**The "Day" Database MUST contain the following properties (Case Sensitive):**

| Property Name | Type | Description |
| --- | --- | --- |
| `Name` | Title | The title of the page |
| `Date` | Date | The date of the entry |
| `Word Count` | Number | Stores the word count |
| `Mood` | Relation | Links to your Mood database |
| `Year` | Relation | Links to the Year database |
| `Month` | Relation | Links to the Month database |
| `Week` | Relation | Links to the Week database |
| `All` | Relation | Links to the All database |

### 2. Fork this Repository

Click the **Fork** button in the top-right corner to copy this repository to your GitHub account.

### 3. Configure GitHub Secrets

Go to your repository's **Settings** -> **Secrets and variables** -> **Actions**, and add the following secrets:

| Secret Name | Description |
| --- | --- |
| `NOTION_TOKEN` | Your Notion Integration Token |
| `NOTION_PAGE` | The Page ID of your Dashboard (32 alphanumeric characters) |

### 4. Automation Schedule

The project is configured with GitHub Actions:

* **Daily 00:05**: Automatically creates the diary page for the day.
* **Daily 23:45**: Automatically counts words for the day and updates the page.

## 🤝 Credits

This project is modified from `malinkang/duolingo2notion`.
