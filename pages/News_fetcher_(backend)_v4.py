import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import newspaper
from newspaper import Article
import os
import threading
from queue import Queue  # Import the Queue class

class NewsFetcherGUI:
    def __init__(self, master):
        self.master = master
        master.title("News Article Fetcher")

        # URL Input
        self.url_label = ttk.Label(master, text="Enter Article URL:")
        self.url_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_entry = ttk.Entry(master, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)

        # Fetch Button
        self.fetch_button = ttk.Button(master, text="Fetch Content", command=self.fetch_content)
        self.fetch_button.grid(row=1, column=0, columnspan=2, pady=10)

        # Content Display
        self.content_label = ttk.Label(master, text="Article Content:")
        self.content_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.content_text = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=80, height=20)
        self.content_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        self.content_text.config(state=tk.DISABLED)  # Make it read-only

        # Status Bar
        self.status_bar = ttk.Label(master, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E)

        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(3, weight=1)

    def fetch_content(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return

        self.status_bar.config(text="Fetching article...")
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete("1.0", tk.END)
        self.content_text.config(state=tk.DISABLED)

        threading.Thread(target=self.fetch_article_thread, args=(url,), daemon=True).start()

    def fetch_article_thread(self, url):
        try:
            # Create queues for thread communication
            status_queue = Queue()
            result_queue = Queue()
            error_queue = Queue()  # New queue for error reporting

            # Ensure the articles directory exists
            articles_dir = "articles"
            if not os.path.exists(articles_dir):
                os.makedirs(articles_dir)

            article = Article(url)
            status_queue.put("Downloading article...")
            article.download()
            article.parse()
            status_queue.put("Article downloaded and parsed.")

            status_queue.put("Performing NLP...")
            article.nlp()
            status_queue.put("NLP complete.")

            content = article.text
            title = article.title

            # Save the article content to a file
            filename = os.path.join(articles_dir, f"{title.replace(' ', '_')}.txt")
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                status_queue.put(f"Article saved to {filename}")
            except Exception as e:
                error_queue.put(f"Error saving article: {e}")

            result_queue.put(content)

        except newspaper.article.ArticleException as e:
            error_queue.put(f"Article download failed: {e}")
        except Exception as e:
            error_queue.put(f"An unexpected error occurred: {e}")
        finally:
            self.update_gui(status_queue, result_queue, error_queue)

    def update_gui(self, status_queue, result_queue, error_queue):
        while not status_queue.empty():
            status = status_queue.get()
            self.status_bar.config(text=status)

        while not result_queue.empty():
            content = result_queue.get()
            self.content_text.config(state=tk.NORMAL)
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert(tk.END, content)
            self.content_text.config(state=tk.DISABLED)

        while not error_queue.empty():
            error = error_queue.get()
            messagebox.showerror("Error", error)
            self.status_bar.config(text="Error")

if __name__ == "__main__":
    root = tk.Tk()
    gui = NewsFetcherGUI(root)
    root.mainloop()
