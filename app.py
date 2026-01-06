from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, date
from io import BytesIO
import base64
import math
import os

app = Flask(__name__)

def calculate_weeks_lived(birth_date):
    """Calculate total weeks lived from birth date to today."""
    today = date.today()
    delta = today - birth_date
    return delta.days // 7

def calculate_total_weeks(life_expectancy):
    """Calculate total weeks in expected lifespan."""
    return life_expectancy * 52

def generate_life_image(birth_date, life_expectancy, width=1170, height=2532):
    """Generate life visualization image for iPhone lock screen."""
    
    weeks_lived = calculate_weeks_lived(birth_date)
    total_weeks = calculate_total_weeks(life_expectancy)
    
    # iPhone 14 Pro / 15 Pro lock screen dimensions
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)
    
    # Calculate grid parameters
    # We want to show total_weeks dots in a grid
    # Leave space for clock area at top and widgets at bottom
    top_margin = 450
    bottom_margin = 600
    side_margin = 80
    
    available_height = height - top_margin - bottom_margin
    available_width = width - (side_margin * 2)
    
    # Calculate optimal grid
    # Target: fit all weeks in available space with good spacing
    cols = 52  # 52 weeks per year
    rows = math.ceil(total_weeks / cols)
    
    # Calculate dot size and spacing
    dot_spacing_x = available_width / cols
    dot_spacing_y = available_height / rows
    
    # Use smaller of the two to keep dots circular
    spacing = min(dot_spacing_x, dot_spacing_y)
    dot_radius = spacing * 0.35
    
    # Recenter based on actual grid size
    grid_width = cols * spacing
    grid_height = rows * spacing
    
    start_x = (width - grid_width) / 2 + spacing / 2
    start_y = top_margin + (available_height - grid_height) / 2 + spacing / 2
    
    # Colors
    lived_color = '#FFFFFF'
    unlived_color = '#1C1C1E'
    current_week_color = '#007AFF'  # Apple blue
    
    # Draw dots
    for week in range(total_weeks):
        row = week // cols
        col = week % cols
        
        x = start_x + col * spacing
        y = start_y + row * spacing
        
        if week < weeks_lived:
            color = lived_color
        elif week == weeks_lived:
            color = current_week_color
        else:
            color = unlived_color
        
        draw.ellipse(
            [x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius],
            fill=color
        )
    
    # Add subtle stats at bottom
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
        font_small = font
    
    # Calculate percentages and years
    percent_lived = (weeks_lived / total_weeks) * 100
    years_lived = weeks_lived / 52
    years_remaining = (total_weeks - weeks_lived) / 52
    
    # Stats text
    stats_y = height - bottom_margin + 100
    
    # Main stat
    main_text = f"{percent_lived:.1f}%"
    bbox = draw.textbbox((0, 0), main_text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, stats_y), main_text, fill='#FFFFFF', font=font)
    
    # Secondary stats
    sub_text = f"{years_lived:.1f} лет прожито · {years_remaining:.1f} лет осталось"
    bbox = draw.textbbox((0, 0), sub_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, stats_y + 50), sub_text, fill='#8E8E93', font=font_small)
    
    # Week counter
    week_text = f"Неделя {weeks_lived} из {total_weeks}"
    bbox = draw.textbbox((0, 0), week_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, stats_y + 90), week_text, fill='#48484A', font=font_small)
    
    return img

def encode_params(birth_date, life_expectancy):
    """Encode parameters for URL."""
    data = f"{birth_date.isoformat()}|{life_expectancy}"
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_params(encoded):
    """Decode parameters from URL."""
    try:
        data = base64.urlsafe_b64decode(encoded.encode()).decode()
        parts = data.split('|')
        birth_date = date.fromisoformat(parts[0])
        life_expectancy = int(parts[1])
        return birth_date, life_expectancy
    except:
        return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    birth_date_str = request.form.get('birth_date')
    life_expectancy = request.form.get('life_expectancy')
    
    if not birth_date_str or not life_expectancy:
        return redirect(url_for('index'))
    
    try:
        birth_date = date.fromisoformat(birth_date_str)
        life_expectancy = int(life_expectancy)
    except ValueError:
        return redirect(url_for('index'))
    
    encoded = encode_params(birth_date, life_expectancy)
    return render_template('result.html', 
                         encoded=encoded,
                         birth_date=birth_date,
                         life_expectancy=life_expectancy)

@app.route('/image/<encoded>.png')
def get_image(encoded):
    birth_date, life_expectancy = decode_params(encoded)
    
    if birth_date is None:
        return "Invalid parameters", 400
    
    img = generate_life_image(birth_date, life_expectancy)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='image/png',
        download_name='life-weeks.png'
    )

@app.route('/preview/<encoded>')
def preview(encoded):
    birth_date, life_expectancy = decode_params(encoded)
    
    if birth_date is None:
        return redirect(url_for('index'))
    
    return render_template('result.html',
                         encoded=encoded,
                         birth_date=birth_date,
                         life_expectancy=life_expectancy)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
