from flask import Flask, render_template, request, jsonify
import requests
import os

# =============================================
# Flask app setup — same as before.
# =============================================
app = Flask(__name__)

# GitHub's public API base URL
GITHUB_API = "https://api.github.com"


def get_user_data(username):
    """
    Hits the GitHub API and fetches:
    - User profile info
    - Their public repositories

    requests.get() is like opening a URL in 
    your browser, but in Python code.
    .json() converts the response into a 
    Python dictionary you can work with.
    """
    # Fetch user profile
    headers = {"User-Agent": "gitinsight-app",
               "Authorization":f"token {os.environ.get('GITHUB_TOKEN', '')}"
               }
    user_response = requests.get(f"{GITHUB_API}/users/{username}", headers=headers)

    # =============================================
    # status_code tells you if the request worked.
    # 200 = success
    # 404 = user not found
    # Anything else = something went wrong
    # =============================================
    if user_response.status_code == 404:
        return None, "User not found"

    if user_response.status_code != 200:
        return None, "GitHub API error. Try again later."

    user = user_response.json()

    # Fetch their repos (up to 100, sorted by most recently updated)
    repos_response = requests.get(
        f"{GITHUB_API}/users/{username}/repos",
        params={"per_page": 100, "sort": "updated"},
        headers=headers
    )
    repos = repos_response.json()

    # =============================================
    # COUNT LANGUAGES:
    # Loop through every repo and count how many
    # times each language appears.
    # This gives us: {"Python": 12, "JavaScript": 5}
    # =============================================
    language_counts = {}
    for repo in repos:
        lang = repo.get("language")  # could be None if repo has no code
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1

    # Sort languages by count, highest first
    # sorted() with key and reverse=True sorts descending
    sorted_languages = dict(
        sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
    )

    # =============================================
    # TOP REPOS BY STARS:
    # Sort repos by stargazers_count descending,
    # take the top 5.
    # =============================================
    top_repos = sorted(
        repos,
        key=lambda r: r.get("stargazers_count", 0),
        reverse=True
    )[:5]

    # Total stars across ALL repos
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)

    return {
        "name": user.get("name") or username,
        "username": username,
        "avatar": user.get("avatar_url"),
        "bio": user.get("bio") or "No bio provided.",
        "location": user.get("location") or "",
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "languages": sorted_languages,
        "top_repos": [
            {
                "name": r["name"],
                "description": r.get("description") or "No description.",
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "language": r.get("language") or "N/A",
                "url": r["html_url"]
            }
            for r in top_repos
        ],
        "github_url": f"https://github.com/{username}"
    }, None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Called when the user submits the form.
    Grabs the username, fetches data, returns JSON.
    """
    username = request.form.get("username", "").strip()

    if not username:
        return jsonify({"error": "Please enter a GitHub username."})

    data, error = get_user_data(username)

    if error:
        return jsonify({"error": error})

    return jsonify(data)


if __name__ == "__main__":
    port=int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)