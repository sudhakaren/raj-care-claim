# Author : Sudhakar Nagarajan
# email : sudhakr@ibm.com

from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import os

app = Flask(__name__)
app.secret_key = 'raj-care-secret-key-2025'
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5001')

@app.route('/')
def index():
    try:
        response = requests.get(f'{BACKEND_URL}/api/claims')
        claims = response.json() if response.status_code == 200 else []
        stats_response = requests.get(f'{BACKEND_URL}/api/stats')
        stats = stats_response.json() if stats_response.status_code == 200 else {}
        return render_template('index.html', claims=claims, stats=stats)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return render_template('index.html', claims=[], stats={})

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        try:
            claim_data = {
                'Claim Type': request.form.get('claim_type'),
                'Policy Number': request.form.get('policy_number'),
                'Service date': request.form.get('service_date'),
                'Member Name': request.form.get('member_name'),
                'Relationship': request.form.get('relationship'),
                'Provider facility name': request.form.get('provider_facility'),
                'Prescription name': request.form.get('prescription_name'),
                'Provider billed': request.form.get('provider_billed') == 'true',
                'Rx cost': request.form.get('rx_cost'),
                'Plan paid': request.form.get('plan_paid'),
                'Your Share': request.form.get('your_share'),
                'Status': request.form.get('status', 'Pending')
            }
            response = requests.post(f'{BACKEND_URL}/api/claims', json=claim_data)
            if response.status_code == 201:
                flash('Claim created successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Error: {response.json().get("error", "Unknown error")}', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('create.html')

@app.route('/edit/<claim_id>', methods=['GET', 'POST'])
def edit(claim_id):
    if request.method == 'POST':
        try:
            claim_data = {
                'Claim Type': request.form.get('claim_type'),
                'Policy Number': request.form.get('policy_number'),
                'Service date': request.form.get('service_date'),
                'Member Name': request.form.get('member_name'),
                'Relationship': request.form.get('relationship'),
                'Provider facility name': request.form.get('provider_facility'),
                'Prescription name': request.form.get('prescription_name'),
                'Provider billed': request.form.get('provider_billed') == 'true',
                'Rx cost': request.form.get('rx_cost'),
                'Plan paid': request.form.get('plan_paid'),
                'Your Share': request.form.get('your_share'),
                'Status': request.form.get('status')
            }
            response = requests.put(f'{BACKEND_URL}/api/claims/{claim_id}', json=claim_data)
            if response.status_code == 200:
                flash('Claim updated successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Error: {response.json().get("error", "Unknown error")}', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    try:
        response = requests.get(f'{BACKEND_URL}/api/claims/{claim_id}')
        if response.status_code == 200:
            claim = response.json()
            return render_template('edit.html', claim=claim)
        else:
            flash('Claim not found', 'danger')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/delete/<claim_id>', methods=['POST'])
def delete(claim_id):
    try:
        response = requests.delete(f'{BACKEND_URL}/api/claims/{claim_id}')
        if response.status_code == 200:
            flash('Claim deleted successfully!', 'success')
        else:
            flash(f'Error: {response.json().get("error", "Unknown error")}', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
