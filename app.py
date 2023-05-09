import json
import os
import subprocess

from flask import Flask, request
from flask_cors import CORS
from steiner import STP

app = Flask(__name__)
CORS(app) # TODO later do cors for only the domain

SCIP_JACK_PATH = os.getenv('SCIP_JACK_PATH')
if SCIP_JACK_PATH is None:
    raise Exception("SCIP_JACK_PATH environment variable must be set")

stp = STP()


@app.post('/api/stp/')
def solve_stp():
    # extract from the request body the list of terminal_ids
    terminal_ids = request.json['terminal_ids']

    stp_filepath = stp.create_stp_file(terminal_ids)
    sub = subprocess.run(
        [f"{SCIP_JACK_PATH}/scipstp", "-f", stp_filepath, "-s", os.path.join(os.getcwd(), "write.set")], cwd='out',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    solution_filepath = stp_filepath.replace(".stp",".stplog")
    travel_nodes = stp.read_stp_solution(solution_filepath)
    both = terminal_ids + travel_nodes

    # create a response object with both nodes
    response = app.response_class(response=json.dumps(both),
                                  status=200,
                                  mimetype='application/json')
    return response


if __name__ == '__main__':
    app.run()
