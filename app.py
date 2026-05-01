from flask import Flask, render_template, request, jsonify
import os
import json
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Word to Project Mapping
WORD_PROJECT_MAP = {
    1: ['generator', 'system'],
    2: ['drone', 'fire'],
    3: ['rickshaw', 'alcohol'],
    4: ['water', 'management']
}

# Global state
class AppState:
    def __init__(self):
        self.ble_connected = False
        self.active_project = None
        self.project_mode_active = False

app_state = AppState()

# Try to import speech recognition library
try:
    import speech_recognition as sr
    import socket
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    
    # Set socket timeout for Google API calls (30 seconds)
    socket.setdefaulttimeout(30)
    
    SPEECH_RECOGNITION_AVAILABLE = True
    logger.info("Speech Recognition library loaded successfully")
except ImportError as e:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning(f"speech_recognition library not installed: {str(e)}")
except Exception as e:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning(f"Failed to initialize speech recognition: {str(e)}")

# Try to import BLE library
try:
    from bleak import BleakClient
    import asyncio
    BLE_AVAILABLE = True
    logger.info("BLE library (bleak) loaded successfully")
except ImportError:
    BLE_AVAILABLE = False
    logger.warning("bleak library not installed. Run: pip install bleak")

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html', 
                         speech_available=SPEECH_RECOGNITION_AVAILABLE,
                         ble_available=BLE_AVAILABLE)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current connection and project status"""
    return jsonify({
        'ble_connected': app_state.ble_connected,
        'active_project': app_state.active_project,
        'project_mode_active': app_state.project_mode_active,
        'speech_available': SPEECH_RECOGNITION_AVAILABLE,
        'ble_available': BLE_AVAILABLE
    })

@app.route('/api/diagnostics', methods=['GET'])
def diagnostics():
    """Check if all systems are ready"""
    diagnostics_data = {
        'speech_recognition': {
            'available': SPEECH_RECOGNITION_AVAILABLE,
            'library': 'SpeechRecognition',
            'api': 'Google Speech-to-Text'
        },
        'ble': {
            'available': BLE_AVAILABLE,
            'library': 'bleak',
            'note': 'BLE requires client-side Web Bluetooth API in browser'
        },
        'platform': os.name,
        'environment': 'Vercel' if 'VERCEL' in os.environ else 'Local Development'
    }
    return jsonify(diagnostics_data)

@app.route('/api/test-voice', methods=['POST'])
def test_voice():
    """Test voice recognition with a manual transcript"""
    data = request.json or {}
    test_transcript = data.get('transcript', 'fire test')
    
    logger.info(f"Testing voice recognition with: {test_transcript}")
    project_num, matched_keyword = process_voice_command(test_transcript)
    
    return jsonify({
        'success': True,
        'transcript': test_transcript,
        'project_detected': project_num,
        'matched_keyword': matched_keyword,
        'message': f'Project {project_num} detected' if project_num else 'No keywords matched'
    })

@app.route('/api/recognize-speech', methods=['POST'])
def recognize_speech():
    """Process audio file and recognize speech"""
    
    if not SPEECH_RECOGNITION_AVAILABLE:
        logger.error("Speech recognition not available")
        return jsonify({'error': 'Speech recognition not available on this server'}), 503
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    try:
        # Read audio file data
        audio_data = audio_file.read()
        
        if not audio_data:
            return jsonify({'error': 'Audio file is empty'}), 400
        
        logger.info(f"Received audio data: {len(audio_data)} bytes")
        
        # Parse WAV file to extract raw audio data
        import wave
        from io import BytesIO
        
        try:
            wav_buffer = BytesIO(audio_data)
            with wave.open(wav_buffer, 'rb') as wav_file:
                # Get audio parameters
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                logger.info(f"WAV: channels={n_channels}, sample_width={sample_width}, rate={frame_rate}, frames={n_frames}")
                
                # Read all frames
                frames = wav_file.readframes(n_frames)
        except Exception as wav_error:
            logger.error(f"WAV parsing error: {str(wav_error)}")
            return jsonify({'error': f'Invalid audio format: {str(wav_error)}'}), 400
        
        try:
            # Create AudioData object from raw frames
            audio = sr.AudioData(frames, frame_rate, sample_width)
            logger.info("Audio object created successfully")
            
            # Try Google Speech Recognition with timeout handling
            logger.info("Calling Google Speech API...")
            transcript = recognizer.recognize_google(audio, language='en-US')
            logger.info(f"Recognized: {transcript}")
            
            # Process voice command
            project_num, matched_keyword = process_voice_command(transcript)
            logger.info(f"Final project_detected: {project_num}, matched_keyword: {matched_keyword}")
            
            return jsonify({
                'success': True,
                'transcript': transcript,
                'project_detected': project_num if project_num else None,
                'matched_keyword': matched_keyword if matched_keyword else None
            })
            
        except socket.timeout:
            logger.error("Google API timeout - network too slow or API unreachable")
            return jsonify({
                'success': False,
                'error': 'Speech service timeout - please try again'
            }), 504
            
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return jsonify({
                'success': False,
                'error': 'Could not understand audio (speech too quiet or unclear)',
                'transcript': ''
            }), 400
            
        except sr.RequestError as api_error:
            error_msg = str(api_error)
            logger.error(f"Google API error: {error_msg}")
            
            # Check if it's a network issue
            if 'timed out' in error_msg.lower() or 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': 'Network error - speech service unreachable'
                }), 503
            else:
                return jsonify({
                    'success': False,
                    'error': f'Speech service error: {error_msg}'
                }), 503
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Server error: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/process-command', methods=['POST'])
def process_command():
    """Process a voice command by text"""
    
    data = request.json
    transcript = data.get('transcript', '').strip()
    
    if not transcript:
        return jsonify({'error': 'No transcript provided'}), 400
    
    # Process voice command
    project_num, matched_keyword = process_voice_command(transcript)
    
    if project_num:
        # Send command to Arduino
        success = send_project_command(project_num)
        return jsonify({
            'success': success,
            'project': project_num,
            'matched_keyword': matched_keyword,
            'message': f'Project {project_num} command sent' if success else 'Failed to send command'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No matching keywords found'
        })

def process_voice_command(transcript):
    """Extract project number from voice transcript"""
    
    if not transcript:
        logger.warning("Empty transcript received")
        return None, None
    
    transcript_lower = transcript.lower().strip()
    words = transcript_lower.split()
    
    logger.info(f"Processing transcript: '{transcript}'")
    logger.info(f"Lowercase: '{transcript_lower}'")
    logger.info(f"Words: {words}")
    logger.info(f"WORD_PROJECT_MAP: {WORD_PROJECT_MAP}")
    
    # Check against all project keywords
    for project_num in sorted(WORD_PROJECT_MAP.keys()):
        keywords = WORD_PROJECT_MAP[project_num]
        for keyword in keywords:
            # Check if keyword is a complete word (word boundary matching)
            if keyword in words:
                logger.info(f"✓ MATCH FOUND: '{keyword}' in {words} → Project {project_num}")
                return project_num, keyword
            # Also check as substring for robustness
            elif keyword in transcript_lower:
                logger.info(f"✓ SUBSTRING MATCH: '{keyword}' in '{transcript_lower}' → Project {project_num}")
                return project_num, keyword
    
    logger.warning(f"❌ NO KEYWORDS MATCHED for: '{transcript}' (words: {words})")
    return None, None

def send_project_command(project_num):
    """Send project command to Arduino via BLE"""
    
    if not BLE_AVAILABLE:
        logger.info(f"[SIMULATED] Project {project_num} command (BLE not available on this platform)")
        app_state.active_project = project_num
        app_state.project_mode_active = True
        return True
    
    # This would require actual BLE implementation
    # For now, just log it
    logger.info(f"Sending project {project_num} command to Arduino")
    app_state.active_project = project_num
    app_state.project_mode_active = True
    
    return True

@app.route('/api/ble/connect', methods=['POST'])
def ble_connect():
    """Notify backend of BLE connection (actual connection done in browser)"""
    app_state.ble_connected = True
    logger.info("Backend notified: BLE connected via browser")
    return jsonify({'success': True, 'message': 'Connection registered'})

@app.route('/api/ble/disconnect', methods=['POST'])
def ble_disconnect():
    """Notify backend of BLE disconnection"""
    app_state.ble_connected = False
    app_state.project_mode_active = False
    app_state.active_project = None
    logger.info("Backend notified: BLE disconnected")
    return jsonify({'success': True, 'message': 'Disconnection registered'})

@app.route('/api/project/<int:project_num>', methods=['POST'])
def send_project(project_num):
    """Send project command via button"""
    
    if project_num not in WORD_PROJECT_MAP:
        return jsonify({'error': 'Invalid project number'}), 400
    
    success = send_project_command(project_num)
    return jsonify({
        'success': success,
        'project': project_num,
        'message': f'Project {project_num} command sent' if success else 'Failed to send command'
    })

@app.route('/api/stop', methods=['POST'])
def stop_rover():
    """Stop the rover"""
    
    logger.info("Stop command received")
    app_state.project_mode_active = False
    app_state.active_project = None
    
    return jsonify({'success': True, 'message': 'Rover stopped'})

if __name__ == '__main__':
    # Get port from environment variable or default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Running on 0.0.0.0 allows other devices on your local Wi-Fi to access it
    app.run(host='0.0.0.0', port=port, debug=debug_mode)