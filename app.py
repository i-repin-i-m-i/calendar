from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, date
from io import BytesIO
import base64
import math
import os

app = Flask(__name__)

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

YOUNG_END = 35 * 52
PRIME_END = 65 * 52

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
    
    top_margin = int(750 * scale)
    bottom_margin = int(400 * scale)
    
    available_height = height - top_margin - bottom_margin
    
    cols = 52
    rows = life_expectancy
    
    # Сначала вычисляем размер сетки исходя из доступного пространства
    # Оставляем место для подписей слева (50px) но центрируем саму сетку по экрану
    max_grid_width = width - int(120 * scale)  # Отступы по бокам
    max_grid_height = available_height
    
    cell_width = max_grid_width / cols
    cell_height = max_grid_height / rows
    cell_size = min(cell_width, cell_height)
    
    square_size = int(cell_size * 0.6)
    
    # Размер итоговой сетки
    grid_width = cols * cell_size
    grid_height = rows * cell_size
    
    # Центрируем сетку по горизонтали относительно ВСЕГО экрана
    grid_start_x = (width - grid_width) / 2
    grid_start_y = top_margin + (available_height - grid_height) / 2
    
    def get_cell_center(row, col):
        x = grid_start_x + col * cell_size + cell_size / 2
        y = grid_start_y + row * cell_size + cell_size / 2
        return x, y
    
    # Шрифт
    font_size = max(int(16 * scale), 10)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    label_color = '#48484A'
    
   # Подписи лет справа (после заполнения строки)
    for year in range(10, life_expectancy + 1, 10):
        row = year - 1
        cx, cy = get_cell_center(row, cols - 1)  # Последний столбец
        
        text = str(year)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_h = bbox[3] - bbox[1]
        
        draw.text(
            (grid_start_x + grid_width + int(8 * scale), cy - text_h / 2),
            text,
            fill=label_color,
            font=font
        )
    
    # Подписи недель сверху
    week_labels = [1, 13, 26, 39, 52]
    for week in week_labels:
        col = week - 1
        cx, cy = get_cell_center(0, col)
        
        text = str(week)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        draw.text(
            (cx - text_w / 2, grid_start_y - text_h - int(6 * scale)),
            text,
            fill=label_color,
            font=font
        )
    
    colors = {
        'lived': '#FFFFFF',
        'current': '#0A84FF',
        'future_young': '#48484A',
        'future_prime': '#2C2C2E',
        'future_late': '#1C1C1E',
    }
    
    for week in range(total_weeks):
        row = week // cols
        col = week % cols
        
        cx, cy = get_cell_center(row, col)
        
        x1 = cx - square_size / 2
        y1 = cy - square_size / 2
        x2 = cx + square_size / 2
        y2 = cy + square_size / 2
        
        if week < weeks_lived:
            color = colors['lived']
        elif week == weeks_lived:
            color = colors['current']
        elif week < YOUNG_END:
            color = colors['future_young']
        elif week < PRIME_END:
            color = colors['future_prime']
        else:
            color = colors['future_late']
        
        draw.rectangle([x1, y1, x2, y2], fill=color)
    
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
