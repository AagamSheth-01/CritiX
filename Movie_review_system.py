import sys
import requests
import mysql.connector
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QFrame, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

class MovieDatabase:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="A@gams18105",
                database="movie_reviews"
            )
            self.cursor = self.conn.cursor()
        except mysql.connector.Error as e:
            self.conn = None
            self.cursor = None
            print(f"[DB ERROR] Could not connect to MySQL: {e}")

    def get_movie(self, title):
        try:
            if not self.cursor:
                return None
            self.cursor.execute(
                "SELECT title, description, rating, poster_url FROM movies WHERE title = %s",
                (title,)
            )
            return self.cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"[DB ERROR] {e}")
            return None

    def add_movie(self, title, desc, rating, poster):
        try:
            if not self.cursor:
                return
            self.cursor.execute(
                "INSERT INTO movies (title, description, rating, poster_url) VALUES (%s, %s, %s, %s)",
                (title, desc, rating, poster)
            )
            self.conn.commit()
        except mysql.connector.errors.IntegrityError:
            pass
        except mysql.connector.Error as e:
            print(f"[DB ERROR] {e}")

    def get_reviews(self, title):
        try:
            if not self.cursor:
                return []
            self.cursor.execute(
                "SELECT user_name, review FROM reviews WHERE movie_title = %s",
                (title,)
            )
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            print(f"[DB ERROR] {e}")
            return []

    def add_review(self, movie_title, username, review):
        try:
            if not self.cursor:
                return
            self.cursor.execute(
                "INSERT INTO reviews (movie_title, user_name, review) VALUES (%s, %s, %s)",
                (movie_title, username, review)
            )
            self.conn.commit()
        except mysql.connector.Error as e:
            print(f"[DB ERROR] {e}")


class MovieReviewGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 Movie Review System")
        self.setGeometry(100, 100, 1100, 800)
        self.setStyleSheet("background-color: #121212; color: white;")
        self.db = MovieDatabase()

        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 15px;")
        self.main_frame.setFixedSize(1000, 750)
        self.main_layout = QVBoxLayout(self.main_frame)

        self.title_label = QLabel("🎥 Enter Movie Name:")
        self.title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #f39c12;")
        self.main_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        search_layout = QHBoxLayout()
        self.movie_input = QLineEdit()
        self.movie_input.setStyleSheet("background-color: #333; color: white; padding: 12px; border-radius: 8px; font-size: 16px;")
        self.movie_input.setPlaceholderText("🔍 Type movie name...")
        self.movie_input.setFixedHeight(40)
        search_layout.addWidget(self.movie_input)

        self.search_button = QPushButton("Search")
        self.search_button.setStyleSheet("background-color: #c0392b; color: white; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 16px;")
        self.search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_button.setFixedHeight(40)
        search_layout.addWidget(self.search_button)
        self.main_layout.addLayout(search_layout)

        self.poster_label = QLabel()
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.poster_label)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setStyleSheet("background-color: #1a1a1a; color: white; padding: 15px; border-radius: 8px; font-size: 18px;")
        self.result_area.setFixedHeight(350)
        self.main_layout.addWidget(self.result_area)

        self.review_button = QPushButton("📝 Add Your Review")
        self.review_button.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; border-radius: 8px; font-size: 16px;")
        self.review_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.review_button.clicked.connect(self.add_review)
        self.main_layout.addWidget(self.review_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.search_button.clicked.connect(self.search_movie)
        self.current_movie = None

        main_window_layout = QVBoxLayout(self)
        main_window_layout.addWidget(self.main_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_window_layout)

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def search_movie(self):
        movie_name = self.movie_input.text().strip()
        if not movie_name:
            return

        try:
            movie_data = self.db.get_movie(movie_name)
            if movie_data:
                title, desc, rating, poster = movie_data
            else:
                title, desc, rating, poster = self.fetch_movie_data(movie_name)
                if title:
                    self.db.add_movie(title, desc, rating, poster)

            if title:
                self.display_movie(title, desc, rating)
                self.load_poster(poster)
            else:
                self.show_error("Movie not found.")
        except Exception as e:
            self.show_error(f"Unexpected error: {e}")

    def fetch_movie_data(self, movie_name):
        api_key = "YOUR_TMDB_API_KEY"
        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_name}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("results"):
                movie = data["results"][0]
                return (
                    movie["title"],
                    movie.get("overview", "No description available."),
                    movie.get("vote_average", "N/A"),
                    f"https://image.tmdb.org/t/p/w500{movie.get('poster_path', '')}"
                )
        except requests.exceptions.RequestException as e:
            self.show_error(f"API error: {e}")
        return None, None, None, None

    def display_movie(self, title, desc, rating):
        if title:
            self.current_movie = title
            self.result_area.setText(f"<b>🎬 {title}</b>\n\n⭐ Rating: {rating}\n\n📖 {desc}\n\n📝 Reviews:\n")
            reviews = self.db.get_reviews(title)
            for user, review in reviews:
                self.result_area.append(f"<b>🎤 {user}:</b> {review}\n")

    def load_poster(self, url):
        if not url:
            return
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            self.poster_label.setPixmap(pixmap.scaled(400, 600, Qt.AspectRatioMode.KeepAspectRatio))
        except requests.exceptions.RequestException:
            self.show_error("Failed to load movie poster.")

    def add_review(self):
        if not self.current_movie:
            return
        user_name, ok1 = QInputDialog.getText(self, "User Name", "Enter your name:")
        if not ok1 or not user_name.strip():
            return
        review, ok2 = QInputDialog.getText(self, "Add Review", "Write your review:")
        if ok2 and review.strip():
            try:
                self.db.add_review(self.current_movie, user_name, review)
                self.result_area.append(f"<b>🎤 {user_name}:</b> {review}\n")
            except Exception as e:
                self.show_error(f"Could not save review: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MovieReviewGUI()
    window.show()
    sys.exit(app.exec())
