import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

file_path = r'C:\Users\ankit\OneDrive\Desktop\Library Management System\Data.xlsx'
data = pd.read_excel(file_path, sheet_name='in')


def authenticate_user(user_id):
    """Check if the entered User ID exists in the dataset."""
    return user_id in data['Borrower ID'].values


def search_books(query, search_by):
    """Search for books by Title, Author, or Book ID."""
    query = query.lower()
    if search_by == "Title":
        return data[data['Title'].str.lower().str.contains(query)]
    elif search_by == "Author":
        return data[data['Author'].str.lower().str.contains(query)]
    elif search_by == "Book ID":
        return data[data['Book ID'].str.lower().str.contains(query)]
    return pd.DataFrame()


def recommend_books(user_id):
    """Recommend books based on the genre of books issued by the user."""
    user_books = data[data['Borrower ID'] == user_id]
    if user_books.empty:
        return pd.DataFrame()

    genres = data['Genre']
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(genres)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    recommendations = pd.DataFrame()
    for index, row in user_books.iterrows():
        book_idx = data.index[data['Book ID'] == row['Book ID']].tolist()[0]
        similar_indices = cosine_sim[book_idx].argsort()[-6:-1][::-1]
        recommended_books = data.iloc[similar_indices]
        recommendations = pd.concat([recommendations, recommended_books])

    recommendations = recommendations[recommendations['Availability'] == "Available"]
    return recommendations.drop_duplicates().head(5)


def issue_book(book_id, user_id):
    """Issue a book and update the dataset."""
    global data
    book_index = data.index[data['Book ID'] == book_id].tolist()
    if not book_index:
        messagebox.showerror("Error", "Book ID not found.")
        return
    book_index = book_index[0]

    if data.loc[book_index, 'Availability'] == "Issued":
        messagebox.showerror("Error", "This book is already issued.")
        return

    data.loc[book_index, 'Availability'] = "Issued"
    data.loc[book_index, 'Borrower ID'] = user_id
    data.loc[book_index, 'Last Issued Date'] = datetime.now().strftime("%Y-%m-%d")
    data.loc[book_index, 'Issued Times'] += 1
    data.to_excel(file_path, index=False, sheet_name='in')
    messagebox.showinfo("Success", f"Book '{data.loc[book_index, 'Title']}' issued successfully!")


def return_book(book_id, user_id):
    """Return a book and update the dataset."""
    global data
    book_index = data.index[(data['Book ID'] == book_id) & (data['Borrower ID'] == user_id)].tolist()
    if not book_index:
        messagebox.showerror("Error", "You cannot return this book.")
        return
    book_index = book_index[0]

    data.loc[book_index, 'Availability'] = "Available"
    data.loc[book_index, 'Borrower ID'] = None
    data.to_excel(file_path, index=False, sheet_name='in')
    messagebox.showinfo("Success", f"Book '{data.loc[book_index, 'Title']}' returned successfully!")


# Tkinter GUI
def login_screen():
    """Create the login screen."""
    def login():
        user_id = entry_user_id.get()
        if authenticate_user(user_id):
            messagebox.showinfo("Login Successful", "Welcome to the Library Management System!")
            login_window.destroy()
            search_screen(user_id)
        else:
            messagebox.showerror("Login Failed", "Invalid User ID. Please try again.")

    login_window = tk.Tk()
    login_window.title("Library Management System - Login")

    tk.Label(login_window, text="User ID:").pack(pady=10)
    entry_user_id = tk.Entry(login_window)
    entry_user_id.pack(pady=10)

    tk.Button(login_window, text="Login", command=login).pack(pady=10)
    login_window.mainloop()


def search_screen(user_id):
    """Create the search screen."""
    def search():
        query = entry_search.get()
        search_by = combo_search_by.get()
        results = search_books(query, search_by)

        for row in tree.get_children():
            tree.delete(row)

        for _, book in results.iterrows():
            tree.insert("", tk.END, values=(book['Book ID'], book['Title'], book['Author'], book['Genre'], book['Availability']))

    def recommend():
        recommendations = recommend_books(user_id)

        for row in tree.get_children():
            tree.delete(row)

        for _, book in recommendations.iterrows():
            tree.insert("", tk.END, values=(book['Book ID'], book['Title'], book['Author'], book['Genre'], book['Availability']))

    def view_issued_books():
        """Show books issued to the current user."""
        issued_books = data[data['Borrower ID'] == user_id]

        for row in tree.get_children():
            tree.delete(row)

        for _, book in issued_books.iterrows():
            tree.insert("", tk.END, values=(book['Book ID'], book['Title'], book['Author'], book['Genre'], book['Availability']))

    def issue_selected_book():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No book selected.")
            return
        book_id = tree.item(selected_item, 'values')[0]
        issue_book(book_id, user_id)
        search()

    def return_selected_book():
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No book selected.")
            return
        book_id = tree.item(selected_item, 'values')[0]
        return_book(book_id, user_id)
        search()

    search_window = tk.Tk()
    search_window.title("Library Management System - Search")

    tk.Label(search_window, text="Search:").grid(row=0, column=0, padx=10, pady=10)
    entry_search = tk.Entry(search_window)
    entry_search.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(search_window, text="Search By:").grid(row=0, column=2, padx=10, pady=10)
    combo_search_by = ttk.Combobox(search_window, values=["Title", "Author", "Book ID"], state="readonly")
    combo_search_by.grid(row=0, column=3, padx=10, pady=10)
    combo_search_by.current(0)

    tk.Button(search_window, text="Search", command=search).grid(row=0, column=4, padx=10, pady=10)
    tk.Button(search_window, text="Recommend", command=recommend).grid(row=0, column=5, padx=10, pady=10)
    tk.Button(search_window, text="Issue", command=issue_selected_book).grid(row=0, column=6, padx=10, pady=10)
    tk.Button(search_window, text="Return", command=return_selected_book).grid(row=0, column=7, padx=10, pady=10)
    tk.Button(search_window, text="View My Issued Books", command=view_issued_books).grid(row=0, column=8, padx=10, pady=10)

    columns = ("Book ID", "Title", "Author", "Genre", "Availability")
    tree = ttk.Treeview(search_window, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.grid(row=1, column=0, columnspan=9, padx=10, pady=10)

    search_window.mainloop()


login_screen()
