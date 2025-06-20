-- Création des tables pour l'historique CSPE
CREATE TABLE IF NOT EXISTS dossiers_cspe (
    id SERIAL PRIMARY KEY,
    numero_dossier VARCHAR(50) UNIQUE NOT NULL,
    demandeur VARCHAR(255) NOT NULL,
    activite VARCHAR(255),
    date_reclamation DATE,
    periode_debut INTEGER,
    periode_fin INTEGER,
    montant_reclame DECIMAL(12,2),
    statut VARCHAR(20) NOT NULL,
    motif_irrecevabilite TEXT,
    confiance_analyse DECIMAL(3,2),
    date_analyse TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyste VARCHAR(100),
    documents_joints TEXT[],
    commentaires TEXT
);
