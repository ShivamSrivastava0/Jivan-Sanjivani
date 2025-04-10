from fastapi import FastAPI, Query
import requests

app = FastAPI()

# OpenFDA Drug Interaction API Endpoint (Example Placeholder)
FDA_API_URL = "https://api.fda.gov/drug/label.json?search="

@app.get("/check-interactions/")
def check_interactions(drugs: list[str] = Query(...)):
    interactions = []
    
    for drug in drugs:
        response = requests.get(f"{FDA_API_URL}{drug}")
        if response.status_code == 200:
            data = response.json()
            try:
                interaction_info = data["results"][0]["drug_interactions"]
                interactions.append({"drug": drug, "interaction": interaction_info})
            except (KeyError, IndexError):
                interactions.append({"drug": drug, "interaction": "No interaction data found"})
        else:
            interactions.append({"drug": drug, "interaction": "Error fetching data"})
    
    return {"interactions": interactions}
