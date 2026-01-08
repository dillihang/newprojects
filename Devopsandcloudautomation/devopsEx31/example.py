from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "my-api"
    })


if __name__=="__main__":

    app.run(debug=True)