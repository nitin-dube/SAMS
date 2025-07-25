import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate('firebase_service_account.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def main():
    attendance_ref = db.collection('attendance').stream()
    print('Attendance Records:')
    for doc in attendance_ref:
        data = doc.to_dict()
        print(f"Doc ID: {doc.id}")
        print(f"  Course: {data.get('course')}")
        print(f"  Date: {data.get('date')}")
        print(f"  Students: {list(data.get('records', {}).keys())}")
        print('-' * 40)

if __name__ == '__main__':
    main() 