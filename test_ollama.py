import requests

try:
    response = requests.get("http://localhost:11434/api/tags", timeout=5)
    print("Connexion réussie à Ollama !")
    print("Modèles disponibles :", response.json())
except requests.exceptions.RequestException as e:
    print("Erreur de connexion à Ollama :", e)
    print("\nVeuillez vérifier que :")
    print("1. Ollama est installé et en cours d'exécution")
    print("2. Le service est accessible à http://localhost:11434")
    print("3. Aucun pare-feu ne bloque la connexion")