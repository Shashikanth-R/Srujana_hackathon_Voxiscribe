import requests
import json
from config import AZURE_FACE_ENDPOINT, AZURE_FACE_KEY
import time

HEADERS = {
    'Ocp-Apim-Subscription-Key': AZURE_FACE_KEY,
    'Content-Type': 'application/octet-stream'
}

PERSON_GROUP_ID = 'voxiscribe-group-v1'

def ensure_person_group():
    url = AZURE_FACE_ENDPOINT.rstrip('/') + '/face/v1.0/persongroups/' + PERSON_GROUP_ID
    r = requests.get(url, headers={'Ocp-Apim-Subscription-Key': AZURE_FACE_KEY})
    if r.status_code == 200:
        return True
    # create
    create_url = AZURE_FACE_ENDPOINT.rstrip('/') + '/face/v1.0/persongroups/' + PERSON_GROUP_ID
    body = {"name": PERSON_GROUP_ID, "recognitionModel": "recognition_04"}
    r2 = requests.put(create_url, headers={'Ocp-Apim-Subscription-Key': AZURE_FACE_KEY, 'Content-Type': 'application/json'}, json=body)
    return r2.status_code in (200, 204)

def register_face(user_id, image_bytes):
    ensure_person_group()
    # create person
    create_person_url = AZURE_FACE_ENDPOINT.rstrip('/') + f'/face/v1.0/persongroups/{PERSON_GROUP_ID}/persons'
    r = requests.post(create_person_url, headers={'Ocp-Apim-Subscription-Key': AZURE_FACE_KEY, 'Content-Type': 'application/json'}, json={"name": f"user_{user_id}"})
    r.raise_for_status()
    person_id = r.json()['personId']
    # add face
    add_face_url = AZURE_FACE_ENDPOINT.rstrip('/') + f'/face/v1.0/persongroups/{PERSON_GROUP_ID}/persons/{person_id}/persistedFaces'
    r2 = requests.post(add_face_url, headers=HEADERS, data=image_bytes)
    r2.raise_for_status()
    # train
    train_url = AZURE_FACE_ENDPOINT.rstrip('/') + f'/face/v1.0/persongroups/{PERSON_GROUP_ID}/train'
    requests.post(train_url, headers={'Ocp-Apim-Subscription-Key': AZURE_FACE_KEY})
    return person_id

def verify_face(person_id, image_bytes, threshold=0.6):
    # detect
    detect_url = AZURE_FACE_ENDPOINT.rstrip('/') + '/face/v1.0/detect?returnFaceId=true'
    r = requests.post(detect_url, headers=HEADERS, data=image_bytes)
    if r.status_code != 200:
        return {"success": False, "error": r.text}
    detected = r.json()
    if not detected:
        return {"success": False, "message": "No face detected"}
    face_id = detected[0]['faceId']
    # identify
    identify_url = AZURE_FACE_ENDPOINT.rstrip('/') + '/face/v1.0/identify'
    body = {
        "personGroupId": PERSON_GROUP_ID,
        "faceIds": [face_id],
        "maxNumOfCandidatesReturned": 1,
        "confidenceThreshold": threshold
    }
    r2 = requests.post(identify_url, headers={'Ocp-Apim-Subscription-Key': AZURE_FACE_KEY, 'Content-Type': 'application/json'}, json=body)
    if r2.status_code != 200:
        return {"success": False, "error": r2.text}
    results = r2.json()
    if results and results[0].get('candidates'):
        candidate = results[0]['candidates'][0]
        return {"success": True, "personId": candidate['personId'], "confidence": candidate['confidence']}
    return {"success": False, "message": "No matching person"}
