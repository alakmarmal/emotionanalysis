import tkinter as tk
from ttkbootstrap import Style
from tkinter import messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from googleapiclient.discovery import build
from textblob import TextBlob
import nltk
import string
import os
import threading

nltk.download('punkt')

# --------- CONFIG ---------
API_KEY = "AIzaSyC3H0rk8432nCj4ghxH07qOxqe3gfXQExE"

# --------- YOUTUBE COMMENT FETCH ---------
def fetch_comments(video_id):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    comments = []
    request = youtube.commentThreads().list(
        part="snippet", videoId=video_id, textFormat="plainText", maxResults=100
    )

    while request:
        response = request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            if comment not in comments:
                comments.append(comment)
        request = youtube.commentThreads().list_next(request, response)

    return comments

# --------- SENTIMENT ANALYSIS ---------
def preprocess_comment(comment):
    comment = comment.lower()
    return comment.translate(str.maketrans('', '', string.punctuation))

def analyze_sentiment(comment):
    blob = TextBlob(comment)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "Positive"
    elif polarity < -0.2:
        return "Negative"
    else:
        return "Neutral"

# --------- GUI LOGIC ---------
def perform_analysis():
    def run_analysis():
        url = url_entry.get()
        if "v=" not in url:
            messagebox.showerror("Invalid Input", "Please enter a valid YouTube URL.")
            return

        video_id = url.split("v=")[-1].split("&")[0]
        log_label.config(text="📡 Fetching comments...")

        try:
            comments = fetch_comments(video_id)
        except Exception as e:
            messagebox.showerror("API Error", str(e))
            log_label.config(text="❌ Failed to fetch comments.")
            return

        if not comments:
            messagebox.showinfo("No Comments", "No comments found.")
            return

        log_label.config(text="🔍 Analyzing sentiments...")

        data = []
        for c in comments:
            clean = preprocess_comment(c)
            sentiment = analyze_sentiment(clean)
            data.append({"Comment": c, "Sentiment": sentiment})

        df = pd.DataFrame(data)
        df.to_csv("youtube_comments_analysis.csv", index=False)

        sentiments = df["Sentiment"].value_counts()

        for widget in chart_frame.winfo_children():
            widget.destroy()

        # ---------- Chart Drawing ----------
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = ['Positive', 'Negative', 'Neutral']
        colors = ['#5cb85c', '#d9534f', '#6c757d']
        counts = [sentiments.get(label, 0) for label in labels]

        if chart_type.get() == "Bar":
            bars = ax.bar(labels, counts, color=colors, edgecolor='black')
            ax.set_ylabel("Number of Comments", fontsize=10)
            ax.set_xlabel("Sentiment", fontsize=10)
            ax.set_title("Sentiment Distribution", fontsize=12, fontweight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.5)

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 2, str(height),
                        ha='center', va='bottom', fontsize=9)
        else:
            ax.pie(counts, labels=labels, autopct='%1.1f%%', colors=colors, shadow=True)
            ax.set_title("Sentiment Distribution", fontsize=12, fontweight='bold')

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=5)

        log_label.config(text=f"✅ {len(df)} comments analyzed. CSV saved!")

    threading.Thread(target=run_analysis).start()

# --------- GUI SETUP ---------
app = tk.Tk()
app.title("YouTube Comment Sentiment Analyzer")
app.geometry("800x600")
app.resizable(False, False)
style = Style(theme="minty")

# --------- MAIN FRAME ---------
frame = tk.Frame(app, padx=20, pady=20)
frame.pack(fill="x")

tk.Label(frame, text="🎥 YouTube Video URL", font=("Segoe UI", 13, "bold")).pack(anchor="w")
url_entry = tk.Entry(frame, font=("Segoe UI", 12), width=60)
url_entry.pack(pady=10)

tk.Label(frame, text="📊 Chart Type", font=("Segoe UI", 11)).pack(anchor="w")
chart_type = tk.StringVar(value="Bar")
tk.OptionMenu(frame, chart_type, "Bar", "Pie").pack(pady=5)

analyze_btn = tk.Button(frame, text="Analyze Comments", command=perform_analysis,
                        bg="#20c997", fg="white", font=("Segoe UI", 12, "bold"), padx=16, pady=8)
analyze_btn.pack(pady=10)

log_label = tk.Label(frame, text="", font=("Segoe UI", 11, "italic"), fg="gray")
log_label.pack()

# --------- CHART FRAME ---------
chart_frame = tk.Frame(app, padx=20, pady=20)
chart_frame.pack(fill="both", expand=True)

app.mainloop()
 