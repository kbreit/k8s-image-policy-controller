from flask import Flask, jsonify, request

ALLOWED_REGISTRIES = ["docker.io"]

app = Flask(__name__)


def validate_request(request) -> bool:
    if request["apiVersion"] != "imagepolicy.k8s.io/v1alpha1":
        return False
    if request["kind"] != "ImageReview":
        return False
    return True


def verify_image(request) -> bool:
    try:
        if (
            request["spec"]["annotations"]["mycluster.image-policy.k8s.io/break-class"]
            == "true"
        ):
            return True
    except KeyError:
        pass
    for container in request["spec"]["containers"]:
        if container["image"].split("/")[0] not in ALLOWED_REGISTRIES:
            return False
    return True


def build_response(verdict, request) -> dict:
    request["status"] = {"allowed": verdict}
    if verdict is False:
        request["status"]["reason"] = "Image repo is blacklisted"
    return request


@app.route("/validate", methods=["POST"])
def validate_image():
    if request.method == "POST":
        payload = request.get_json(force=True)
        if not validate_request(payload):
            return jsonify({"error": "Invalid request"}), 400
        return jsonify(build_response(verify_image(payload), payload)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
