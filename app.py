from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, date
from io import BytesIO
import base64
import math
import os

app = Flask(__name__)

# iPhone screen resolutions (width x height in pixels)
IPHONE_MODELS = {
    'se': {'name': 'iPhone SE / 8 / 7 / 6s', 'width': 750, 'height': 1334},
    '8plus': {'name': 'iPhone 8 Plus / 7 Plus / 6s Plus', 'width': 1242, 'height': 2208},
    'x': {'name': 'iPhone X / XS / 11 Pro', 'width': 1125, 'height': 2436},
    'xr': {'name': 'iPhone XR / 11', 'width': 828, 'height': 1792},
    'xsmax': {'name': 'iPhone XS Max / 11 Pro Max', 'width': 1242, 'height': 2688},
    '12mini': {'name': 'iPhone 12 mini / 13 mini', 'width': 1080, 'height': 2340},
    '12': {'name': 'iPhone 12 / 13 / 14', 'width': 1170, 'height': 2532},
    '12promax': {'name': 'iPhone 12 Pro Max / 13 Pro Max / 14 Plus', 'width': 1284, 'height': 2778},
    '14pro': {'name': 'iPhone 14 Pro / 15 / 15 Pro', 'width': 1179, 'height': 2556},
    '14promax': {'name': 'iPhone 14 Pro Max / 15 Plus / 15 Pro Max', 'width': 1290, 'height': 2796},
    '16pro': {'name': 'iPhone 16 Pro', 'width': 1206, 'height': 2622},
    '16promax': {'name': 'iPhone 16 Pro Max', 'width': 1320, 'height': 2868},
    '17': {'name': 'iPhone 17 / 17 Pro', 'width': 1206, 'height': 2622},
    '17air': {'name': 'iPhone Air', 'width': 1260, 'height': 2736},
    '17promax': {'name': 'iPhone 17 Pro Max', 'width': 1320, 'height': 2868},
}

def calculate_weeks_lived(birth_date):
    today = date.today()
    delta = today - birth_date
    return delta.days // 7

def calculate_total_weeks(life_expectancy):
    return life_expectancy * 52

def generate_life_image(birth_date, life_expectancy, model='12'):
    device = IPHONE_MODELS.get(model, IPHONE_MODELS['12'])
    width = device['width']
    height = device['height']
    
    weeks_lived = calculate_weeks_lived(birth_date)
    total_weeks = calculate_total_weeks(life_expectancy)
    
    img = Image.new('RGB', (width, height), color='#000000')
    draw = ImageDraw.Draw(img)
    
    scale = height / 2532
    
    top_margin = int(420 * scale)
    bottom_margin = int(580 * scale)
    side_margin = int(60 * scale)
    
    available_height = height - top_margin - bottom_margin
    available_width = width - (side_margin * 2)
    
    cols = 52
    rows = math.ceil(total_weeks / cols)
    
    dot_spacing_x = available_width / cols
    dot_spacing_y = available_height / rows
    
    spacing = min(dot_spacing_x, dot_spacing_y)
    dot_radius = spacing * 0.35
    
    grid_width = cols * spacing
    grid_height = rows * spacing
    
    start_x = (width - grid_width) / 2 + spacing / 2
    start_y = top_margin + (available_height - grid_height) / 2 + spacing / 2
    
    lived_color = '#FFFFFF'
    unlived_color = '#1C1C1E'
    current_week_color = '#007AFF'
    
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
    
    font_size_large = int(32 * scale)
    font_size_small = int(24 * scale)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size_large)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size_small)
    except:
        font = ImageFont.load_default()
        font_small = font
    
    percent_lived = (weeks_lived / total_weeks) * 100
    years_lived = weeks_lived / 52
    years_remaining = (total_weeks - weeks_lived) / 52
    
    stats_y = height - bottom_margin + int(100 * scale)
    
    main_text = f"{percent_lived:.1f}%"
    bbox = draw.textbbox((0, 0), main_text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, stats_y), main_text, fill='#FFFFFF', font=font)
    
    sub_text = f"{years_lived:.1f} лет прожито · {years_remaining:.1f} лет осталось"
    bbox = draw.textbbox((0, 0), sub_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, stats_y + int(50 * scale)), sub_text, fill='#8E8E93', font=font_small)
    
    week_text = f"Неделя {weeks_lived} из {total_weeks}"
    bbox = draw.textbbox((0, 0), week_text, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) / 2, stats_y + int(90 * scale)), week_text, fill='#48484A', font=font_small)
    
    return img

def encode_params(birth_date, life_expectancy, model='12'):
    data = f"{birth_date.isoformat()}|{life_expectancy}|{model}"
    return base64.urlsafe_b64encode(data.encode()).decode()

def decode_params(encoded):
    try:
        data = base64.urlsafe_b64decode(encoded.encode()).decode()
        parts = data.split('|')
        birth_date = date.fromisoformat(parts[0])
        life_expectancy = int(parts[1])
        model = parts[2] if len(parts) > 2 else '12'
        return birth_date, life_expectancy, model
    except:
        return None, None, None

@app.route('/')
def index():
    return render_template('index.html', models=IPHONE_MODELS)

@app.route('/generate', methods=['POST'])
def generate():
    birth_date_str = request.form.get('birth_date')
    life_expectancy = request.form.get('life_expectancy')
    model = request.form.get('model', '12')
    
    if not birth_date_str or not life_expectancy:
        return redirect(url_for('index'))
    
    try:
        birth_date = date.fromisoformat(birth_date_str)
        life_expectancy = int(life_expectancy)
    except ValueError:
        return redirect(url_for('index'))
    
    encoded = encode_params(birth_date, life_expectancy, model)
    device = IPHONE_MODELS.get(model, IPHONE_MODELS['12'])
    
    return render_template('result.html', 
                         encoded=encoded,
                         birth_date=birth_date,
                         life_expectancy=life_expectancy,
                         model=model,
                         device=device)

@app.route('/image/<encoded>.png')
def get_image(encoded):
    birth_date, life_expectancy, model = decode_params(encoded)
    
    if birth_date is None:
        return "Invalid parameters", 400
    
    img = generate_life_image(birth_date, life_expectancy, model)
    
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
    birth_date, life_expectancy, model = decode_params(encoded)
    
    if birth_date is None:
        return redirect(url_for('index'))
    
    device = IPHONE_MODELS.get(model, IPHONE_MODELS['12'])
    
    return render_template('result.html',
                         encoded=encoded,
                         birth_date=birth_date,
                         life_expectancy=life_expectancy,
                         model=model,
                         device=device)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
