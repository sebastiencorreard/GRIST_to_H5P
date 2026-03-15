#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import json
import uuid
import requests
from io import StringIO

# Configuration Grist - Lien public
GRIST_DOC_ID = "fvUTCgKT6jMV"
TABLE_NAME = "Dispositifs"
GRIST_CSV_URL = f"https://grist.numerique.gouv.fr/o/docs/{GRIST_DOC_ID}/download/csv?tableId={TABLE_NAME}"

print(f"Téléchargement depuis : {GRIST_CSV_URL}")

# Récupérer les données CSV depuis Grist
response = requests.get(GRIST_CSV_URL)
response.raise_for_status()
response.encoding = 'utf-8'

# Parser le CSV
csv_data = StringIO(response.text)
reader = csv.DictReader(csv_data)
dispositifs = list(reader)

print(f"✓ {len(dispositifs)} dispositifs récupérés depuis Grist")
print(f"Colonnes disponibles : {list(dispositifs[0].keys())}")

def filtrer(public, type_disp, discipline=None):
    res = []
    for d in dispositifs:
        if public not in d['Public'] or type_disp not in d['Type dispositif']:
            continue
        if discipline and discipline not in d['Discipline']:
            continue
        res.append(d)
    return res

# Créer mapping unique des dispositifs
dispositif_to_end_id = {}
end_id = 1
for disp in dispositifs:
    nom = disp['Nom']
    if nom not in dispositif_to_end_id:
        dispositif_to_end_id[nom] = -end_id
        end_id += 1

h5p = {
    "branchingScenario": {
        "content": [],
        "endScreens": [
            {
                "endScreenTitle": "",
                "endScreenSubtitle": "",
                "contentId": -1,
                "endScreenScore": 0
            }
        ],
        "scoringOptionGroup": {
            "scoringOption": "no-score",
            "includeInteractionsScores": True
        },
        "startScreen": {
            "startScreenTitle": "<p>Trouver un dispositif CSTI</p>",
            "startScreenSubtitle": "<p>Répondez aux questions pour trouver une proposition qui vous correspond.</p>"
        },
        "behaviour": {
            "enableBackwardsNavigation": True,
            "forceContentFinished": False,
            "randomizeBranchingQuestions": False
        },
        "l10n": {
            "startScreenButtonText": "Commencer",
            "endScreenButtonText": "Recommencer au début",
            "backButtonText": "Revenir en arrière",
            "disableProceedButtonText": "Require to complete the current module",
            "replayButtonText": "Jouer la vidéo de nouveau",
            "scoreText": "Votre note:",
            "fullscreenAria": "Plein écran"
        }
    }
}

publics = [
    ("🏫 enseignant·e 1er degré", "1er degré"),
    ("🎒 enseignant·e en collège", "Collège"),
    ("📖 enseignant·e en lycée", "Lycée")
]

types_list = [
    ("🎓 à me former", "formation"),
    ("🏆 un concours pour mes élèves", "concours"),
    ("🌿 une opération de science participative pour mes élèves", "science participative"),
    ("🤝 à être accompagné·e pour mon projet", "accompagnement"),
    ("⚡ une action ponctuelle pour mes élèves", "action ponctuelle"),
    ("📅 un projet sur l'année pour mes élèves", "projet sur l'année"),
    ("📢 à m'informer et communiquer sur des projets", "communication")
]

disciplines = [
    "Interdisciplinaire",
    "Mathématiques", 
    "Physique chimie",
    "Sciences de la vie, de la Terre et de l'univers",
    "Technologie et robotique"
]

content = []
content_id = 0

# Q1: Public (contentId: 0)
q1 = {
    "type": {
        "library": "H5P.BranchingQuestion 1.0",
        "params": {
            "branchingQuestion": {
                "alternatives": [
                    {
                        "nextContentId": 1,
                        "feedback": {"title": "", "subtitle": ""},
                        "text": publics[0][0]
                    },
                    {
                        "nextContentId": 2,
                        "feedback": {"title": "", "subtitle": ""},
                        "text": publics[1][0]
                    },
                    {
                        "nextContentId": 3,
                        "feedback": {"title": "", "subtitle": ""},
                        "text": publics[2][0]
                    }
                ],
                "question": "<p>Je suis...</p>"
            },
            "proceedButtonText": "Proceed"
        },
        "subContentId": str(uuid.uuid4()),
        "metadata": {
            "contentType": "Branching Question",
            "license": "U",
            "title": "Choix public",
            "authors": [],
            "changes": [],
            "extraTitle": "Choix public"
        }
    },
    "showContentTitle": False,
    "proceedButtonText": "Proceed",
    "forceContentFinished": "useBehavioural",
    "feedback": {"title": "", "subtitle": ""},
    "contentBehaviour": "useBehavioural",
    "contentId": content_id
}
content.append(q1)
content_id += 1

# Pour chaque public, créer Q2
q2_ids = [1, 2, 3]
next_free_id = 4

for pub_idx, (pub_label, pub_val) in enumerate(publics):
    alternatives = []
    
    for type_label, type_val in types_list:
        if type_val == "concours":
            # Question discipline
            disc_q_id = next_free_id
            next_free_id += 1
            
            disc_alternatives = []
            for disc in disciplines:
                resultats = filtrer(pub_val, type_val, disc)
                if resultats:
                    # Question choix dispositif
                    choice_q_id = next_free_id
                    next_free_id += 1
                    
                    disc_alternatives.append({
                        "nextContentId": choice_q_id,
                        "feedback": {"title": "", "subtitle": ""},
                        "text": disc
                    })
                    
                    # Créer question choix
                    disp_alternatives = []
                    for disp in resultats:
                        disp_alternatives.append({
                            "nextContentId": dispositif_to_end_id[disp['Nom']],
                            "feedback": {
                                "title": f"<p>{disp['Description']}</p><p><a target=\"_blank\" rel=\"noopener noreferrer\" href=\"{disp['URL']}\">→ En savoir plus</a></p>",
                                "subtitle": ""
                            },
                            "text": disp['Nom']
                        })
                    
                    content.append({
                        "type": {
                            "library": "H5P.BranchingQuestion 1.0",
                            "params": {
                                "branchingQuestion": {
                                    "alternatives": disp_alternatives,
                                    "question": f"<p>Choisissez un dispositif ({len(resultats)} disponible(s))</p>"
                                }
                            },
                            "subContentId": str(uuid.uuid4()),
                            "metadata": {
                                "contentType": "Branching Question",
                                "license": "U",
                                "title": f"Choix {type_val} {disc}",
                                "authors": [],
                                "changes": [],
                                "extraTitle": f"Choix {type_val} {disc}"
                            }
                        },
                        "showContentTitle": False,
                        "proceedButtonText": "Proceed",
                        "forceContentFinished": "useBehavioural",
                        "feedback": {"title": "", "subtitle": ""},
                        "contentBehaviour": "useBehavioural",
                        "contentId": choice_q_id
                    })
            
            if disc_alternatives:
                # Ajouter question discipline
                content.append({
                    "type": {
                        "library": "H5P.BranchingQuestion 1.0",
                        "params": {
                            "branchingQuestion": {
                                "alternatives": disc_alternatives,
                                "question": "<p>Dans quelle discipline ?</p>"
                            }
                        },
                        "subContentId": str(uuid.uuid4()),
                        "metadata": {
                            "contentType": "Branching Question",
                            "license": "U",
                            "title": f"Choix discipline {pub_val}",
                            "authors": [],
                            "changes": [],
                            "extraTitle": f"Choix discipline {pub_val}"
                        }
                    },
                    "showContentTitle": False,
                    "proceedButtonText": "Proceed",
                    "forceContentFinished": "useBehavioural",
                    "feedback": {"title": "", "subtitle": ""},
                    "contentBehaviour": "useBehavioural",
                    "contentId": disc_q_id
                })
                
                alternatives.append({
                    "nextContentId": disc_q_id,
                    "feedback": {"title": "", "subtitle": ""},
                    "text": type_label
                })
        else:
            resultats = filtrer(pub_val, type_val)
            if resultats:
                choice_q_id = next_free_id
                next_free_id += 1
                
                alternatives.append({
                    "nextContentId": choice_q_id,
                    "feedback": {"title": "", "subtitle": ""},
                    "text": type_label
                })
                
                disp_alternatives = []
                for disp in resultats:
                    disp_alternatives.append({
                        "nextContentId": dispositif_to_end_id[disp['Nom']],
                        "feedback": {
                            "title": f"<p>{disp['Description']}</p><p><a target=\"_blank\" rel=\"noopener noreferrer\" href=\"{disp['URL']}\">→ En savoir plus</a></p>",
                            "subtitle": ""
                        },
                        "text": disp['Nom']
                    })
                
                content.append({
                    "type": {
                        "library": "H5P.BranchingQuestion 1.0",
                        "params": {
                            "branchingQuestion": {
                                "alternatives": disp_alternatives,
                                "question": f"<p>Choisissez un dispositif ({len(resultats)} disponible(s))</p>"
                            }
                        },
                        "subContentId": str(uuid.uuid4()),
                        "metadata": {
                            "contentType": "Branching Question",
                            "license": "U",
                            "title": f"Choix {type_val} {pub_val}",
                            "authors": [],
                            "changes": [],
                            "extraTitle": f"Choix {type_val} {pub_val}"
                        }
                    },
                    "showContentTitle": False,
                    "proceedButtonText": "Proceed",
                    "forceContentFinished": "useBehavioural",
                    "feedback": {"title": "", "subtitle": ""},
                    "contentBehaviour": "useBehavioural",
                    "contentId": choice_q_id
                })
    
    # Q2 pour ce public
    q2 = {
        "type": {
            "library": "H5P.BranchingQuestion 1.0",
            "params": {
                "branchingQuestion": {
                    "alternatives": alternatives,
                    "question": "<p>Je cherche...</p>"
                }
            },
            "subContentId": str(uuid.uuid4()),
            "metadata": {
                "contentType": "Branching Question",
                "license": "U",
                "title": f"Choix type {pub_val}",
                "authors": [],
                "changes": [],
                "extraTitle": f"Choix type {pub_val}"
            }
        },
        "showContentTitle": False,
        "proceedButtonText": "Proceed",
        "forceContentFinished": "useBehavioural",
        "feedback": {"title": "", "subtitle": ""},
        "contentBehaviour": "useBehavioural",
        "contentId": q2_ids[pub_idx]
    }
    content.insert(q2_ids[pub_idx], q2)

# Trier par contentId
content.sort(key=lambda x: x['contentId'])

h5p["branchingScenario"]["content"] = content

with open('content.json', 'w', encoding='utf-8') as f:
    json.dump(h5p, f, indent=2, ensure_ascii=False)

print(f"✓ {len(content)} contenus créés dans content.json")