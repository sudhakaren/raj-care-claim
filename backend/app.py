# Author : Sudhakar Nagarajan
# email : sudhakr@ibm.com

from flask import Flask, jsonify, request
from flask_cors import CORS
import csv
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

CSV_FILE = '/app/data/claims.csv'
ACCESS_FILE = '/app/data/access.csv'
CSV_HEADERS = [
    'Claim Id', 'Claim Type', 'Policy Number', 'Service date',
    'Member Name', 'Relationship', 'Provider facility name',
    'Prescription name', 'Provider billed', 'Rx cost',
    'Plan paid', 'Your Share', 'Status'
]

def init_csv():
    if not os.path.exists(CSV_FILE):
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()

def init_access_csv():
    if not os.path.exists(ACCESS_FILE):
        os.makedirs(os.path.dirname(ACCESS_FILE), exist_ok=True)
        with open(ACCESS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Relationship', 'access'])
            writer.writeheader()
            writer.writerows([
                {'Relationship': 'self', 'access': 'yes'},
                {'Relationship': 'spouse', 'access': 'yes'},
                {'Relationship': 'child', 'access': 'no'}
            ])

def read_claims():
    init_csv()
    claims = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Claim Id', '').strip():
                claims.append(row)
    return claims

def write_claims(claims):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(claims)

def get_next_claim_id():
    claims = read_claims()
    if not claims:
        return "1"
    max_id = max([int(c.get('Claim Id', 0) or 0) for c in claims])
    return str(max_id + 1)

def read_access_rules():
    init_access_csv()
    access_rules = {}
    with open(ACCESS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            relationship = row.get('Relationship', '').strip().lower()
            access = row.get('access', '').strip().lower()
            if relationship:
                access_rules[relationship] = (access == 'yes')
    return access_rules

def filter_claims_by_access(claims):
    access_rules = read_access_rules()
    filtered_claims = []
    for claim in claims:
        relationship = claim.get('Relationship', '').strip().lower()
        if access_rules.get(relationship, True):
            filtered_claims.append(claim)
    return filtered_claims

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'raj-care-backend'}), 200

@app.route('/api/claims', methods=['GET'])
def get_claims():
    try:
        claims = read_claims()
        claim_id = request.args.get('claim_id')
        member_name = request.args.get('member_name')
        service_date = request.args.get('service_date')
        status = request.args.get('status')
        
        filtered_claims = claims
        if claim_id:
            filtered_claims = [c for c in filtered_claims if c.get('Claim Id', '').strip() == claim_id.strip()]
        if member_name:
            member_name_lower = member_name.lower()
            filtered_claims = [c for c in filtered_claims if member_name_lower in c.get('Member Name', '').lower()]
        if service_date:
            filtered_claims = [c for c in filtered_claims if c.get('Service date', '').strip() == service_date.strip()]
        if status:
            status_lower = status.lower()
            filtered_claims = [c for c in filtered_claims if c.get('Status', '').lower() == status_lower]
        
        return jsonify(filtered_claims), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/claims/<claim_id>', methods=['GET'])
def get_claim(claim_id):
    try:
        claims = read_claims()
        claim = next((c for c in claims if c['Claim Id'] == claim_id), None)
        if claim:
            return jsonify(claim), 200
        else:
            return jsonify({'error': 'Claim not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/claims', methods=['POST'])
def create_claim():
    try:
        data = request.json
        required_fields = ['Claim Type', 'Policy Number', 'Member Name', 'Status']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        claims = read_claims()
        provider_billed = data.get('Provider billed', False)
        provider_billed_str = 'true' if (isinstance(provider_billed, bool) and provider_billed) or str(provider_billed).lower() == 'true' else 'false'
        
        new_claim = {
            'Claim Id': get_next_claim_id(),
            'Claim Type': str(data.get('Claim Type', '')),
            'Policy Number': str(data.get('Policy Number', '')),
            'Service date': str(data.get('Service date', '')),
            'Member Name': str(data.get('Member Name', '')),
            'Relationship': str(data.get('Relationship', '')),
            'Provider facility name': str(data.get('Provider facility name', '')),
            'Prescription name': str(data.get('Prescription name', '')),
            'Provider billed': provider_billed_str,
            'Rx cost': str(data.get('Rx cost', '0')),
            'Plan paid': str(data.get('Plan paid', '0')),
            'Your Share': str(data.get('Your Share', '0')),
            'Status': str(data.get('Status', 'Pending'))
        }
        
        claims.append(new_claim)
        write_claims(claims)
        return jsonify(new_claim), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/claims/<claim_id>', methods=['PUT'])
def update_claim(claim_id):
    try:
        data = request.json
        claims = read_claims()
        claim_index = next((i for i, c in enumerate(claims) if c['Claim Id'] == claim_id), None)
        if claim_index is None:
            return jsonify({'error': 'Claim not found'}), 404
        
        claim = claims[claim_index]
        for key in CSV_HEADERS:
            if key != 'Claim Id' and key in data:
                if key == 'Provider billed':
                    provider_billed = data[key]
                    claim[key] = 'true' if (isinstance(provider_billed, bool) and provider_billed) or str(provider_billed).lower() == 'true' else 'false'
                else:
                    claim[key] = str(data[key])
        
        claims[claim_index] = claim
        write_claims(claims)
        return jsonify(claim), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/claims/<claim_id>', methods=['DELETE'])
def delete_claim(claim_id):
    try:
        claims = read_claims()
        claim = next((c for c in claims if c['Claim Id'] == claim_id), None)
        if not claim:
            return jsonify({'error': 'Claim not found'}), 404
        
        claims = [c for c in claims if c['Claim Id'] != claim_id]
        write_claims(claims)
        return jsonify({'message': 'Claim deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        claims = read_claims()
        claim_id = request.args.get('claim_id')
        member_name = request.args.get('member_name')
        service_date = request.args.get('service_date')
        status = request.args.get('status')
        
        filtered_claims = claims
        if claim_id:
            filtered_claims = [c for c in filtered_claims if c.get('Claim Id', '').strip() == claim_id.strip()]
        if member_name:
            member_name_lower = member_name.lower()
            filtered_claims = [c for c in filtered_claims if member_name_lower in c.get('Member Name', '').lower()]
        if service_date:
            filtered_claims = [c for c in filtered_claims if c.get('Service date', '').strip() == service_date.strip()]
        if status:
            status_lower = status.lower()
            filtered_claims = [c for c in filtered_claims if c.get('Status', '').lower() == status_lower]
        
        total_claims = len(filtered_claims)
        total_rx_cost = sum(float(c.get('Rx cost', 0) or 0) for c in filtered_claims)
        total_plan_paid = sum(float(c.get('Plan paid', 0) or 0) for c in filtered_claims)
        total_your_share = sum(float(c.get('Your Share', 0) or 0) for c in filtered_claims)
        
        status_counts = {}
        for claim in filtered_claims:
            claim_status = claim.get('Status', 'Unknown')
            status_counts[claim_status] = status_counts.get(claim_status, 0) + 1
        
        unique_claim_ids = sorted(list(set(c.get('Claim Id', '') for c in claims if c.get('Claim Id', ''))))
        unique_member_names = sorted(list(set(c.get('Member Name', '') for c in claims if c.get('Member Name', ''))))
        unique_service_dates = sorted(list(set(c.get('Service date', '') for c in claims if c.get('Service date', ''))))
        unique_statuses = sorted(list(set(c.get('Status', '') for c in claims if c.get('Status', ''))))
        
        return jsonify({
            'total_claims': total_claims,
            'total_rx_cost': round(total_rx_cost, 2),
            'total_plan_paid': round(total_plan_paid, 2),
            'total_your_share': round(total_your_share, 2),
            'status_counts': status_counts,
            'filters_applied': {'claim_id': claim_id, 'member_name': member_name, 'service_date': service_date, 'status': status},
            'available_filters': {'claim_ids': unique_claim_ids, 'member_names': unique_member_names, 'service_dates': unique_service_dates, 'statuses': unique_statuses}
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/claims/filter-by-access', methods=['POST'])
def filter_claims_by_access_endpoint():
    try:
        data = request.json
        if not isinstance(data, list):
            return jsonify({'error': 'Input must be a JSON array of claims'}), 400
        filtered_claims = filter_claims_by_access(data)
        access_rules = read_access_rules()
        return jsonify({
            'original_count': len(data),
            'filtered_count': len(filtered_claims),
            'claims': filtered_claims,
            'access_rules': {k: ('yes' if v else 'no') for k, v in access_rules.items()}
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_csv()
    init_access_csv()
    app.run(host='0.0.0.0', port=5001, debug=True)
