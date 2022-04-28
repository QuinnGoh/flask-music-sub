class User:
    username: str
    email = str
    password = str

    def __init__(self, username: str, email: str, password: str) -> None:
        self.username = username
        self.email = email
        self.password = password


class Song:
    title: str
    artist: str
    year: int
    web_url: str
    img_url: str

    def __init__(self, title: str, artist: str, year: int, web_url: str, img_url: str) -> None:
        self.title = title
        self.artist = artist
        self.year = year
        self.web_url = web_url
        self.img_url = img_url
