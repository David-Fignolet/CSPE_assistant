import requests
import sys

def test_endpoint(base_url, endpoint):
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        print(f"\nTest de l'endpoint: {url}")
        
        # Test GET pour les endpoints de type API
        if endpoint != 'api/chat':
            response = requests.get(url, timeout=5)
            print(f"  - GET: {response.status_code}")
            if response.status_code == 200:
                print(f"  - Réponse: {response.json()}")
        
        # Test POST pour les endpoints de chat
        if 'chat' in endpoint or 'generate' in endpoint:
            response = requests.post(
                url,
                json={"model": "mistral:latest", "prompt": "Test"},
                timeout=5
            )
            print(f"  - POST: {response.status_code}")
            if response.status_code == 200:
                print(f"  - Réponse: {response.json()}")
                
    except Exception as e:
        print(f"  - Erreur: {str(e)}")

def main():
    base_url = "http://localhost:11434"
    endpoints = [
        "",
        "api/tags",
        "api/generate",
        "api/chat",
        "v1/chat/completions",
        "v1/models"
    ]
    
    print(f"Test des endpoints Ollama sur {base_url}")
    print("=" * 50)
    
    for endpoint in endpoints:
        test_endpoint(base_url, endpoint)

if __name__ == "__main__":
    main()
