import logging
from flask import Flask, render_template, request, jsonify
from rag.query import answer_question
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        history = data.get('history', [])
    
        if not user_message:
            logger.warning("Chat request received without message")
            return jsonify({'error': 'No message provided'}), 400

        logger.info(f"Processing chat message: {user_message[:50]}...")
        
        # Call the existing RAG logic
        result = answer_question(user_message, history=history)
        
        # result is expected to be a dict: {'answer': '...', 'sources': [...]}
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/contact', methods=['POST'])
def contact():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        message = data.get('message', '')
    
        if not name or not phone:
            logger.warning("Contact form submitted with missing fields")
            return jsonify({'error': 'Name and Phone are required'}), 400
        
        import csv
        import datetime
        
        file_exists = os.path.isfile('leads.csv')
        
        with open('leads.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp', 'Name', 'Email', 'Phone', 'Message'])
            
            writer.writerow([
                datetime.datetime.now().isoformat(),
                name,
                email,
                phone,
                message
            ])
            
        logger.info(f"Contact details saved for: {name}")
        return jsonify({'message': 'Details received successfully'})
    except Exception as e:
        logger.error(f"Error saving contact: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    # Use port 5000 or allow environment variable
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)