from flask import Flask, render_template

app = Flask(__name__, template_folder="pages", static_folder="assets")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/billing")
def billing():
    return render_template("billing.html")

@app.route("/icons")
def icons():
    return render_template("icons.html")

@app.route("/landing")
def landing():
    return render_template("landing.html")

@app.route("/map")
def map_page():
    return render_template("map.html")

@app.route("/notifications")
def notifications():
    return render_template("notifications.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/rtl")
def rtl():
    return render_template("rtl.html")

@app.route("/sign-in")
def sign_in():
    return render_template("sign-in.html")

@app.route("/sign-up")
def sign_up():
    return render_template("sign-up.html")

@app.route("/tables")
def tables():
    return render_template("tables.html")

@app.route("/template")
def template():
    return render_template("template.html")

@app.route("/typography")
def typography():
    return render_template("typography.html")

@app.route("/virtual-reality")
def vr():
    return render_template("virtual-reality.html")

if __name__ == "__main__":
    app.run(debug=True)